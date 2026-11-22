# -*- coding: utf-8 -*-
"""Full settings parity, offline expected cache and account-bound consumer checks."""
import copy
import json
import logging
import os
import sys
import threading
import time
import types

from checks.common import check


def run(workdir):
    from unicum.settings import Settings
    from unicum.runtime.session import Session
    from unicum.settings_window import codec, page
    from unicum.tracker.page import build, CATEGORIES
    from unicum.tracker.expected import Expected, parse, ORIGIN
    import helpers

    session = Session(0)
    settings = Settings(session, os.path.join(workdir, 'tracker-settings.json'))
    settings.update({'externalMod': {'value': 17}, 'wnxTracker': {'futureField': 'preserved'}})
    expected = Expected(session, os.path.join(workdir, 'tracker-expected.json'))
    for language in ('en', 'uk'):
        settings.update({'settingsLanguage': language})
        for supporter in (False, True):
            native = page.native_page(settings.values(), channel='Some_Channel', linked=True,
                                      supporter=supporter, battles_hidden=False)
            original = [line.split('\t')[1] for line in native.split('\n')
                        if line.split('\t')[0] in ('checkbox', 'dropdown', 'button', 'input')]
            categories = build(native, settings.values(), expected)
            flat = [row for group in categories for row in group['rows'] if 'var' in row]
            names = [row['var'] for row in flat]
            check('%s full existing control/action parity (supporter=%s)' % (language, supporter),
                  len(names) == len(set(names)) and set(original).issubset(set(names))
                  and [group['id'] for group in categories] == list(CATEGORIES))
            check('%s no visibility or alternative-battle switch introduced' % language,
                  set(name for name in names if name.startswith('tracker_')) ==
                  set(('tracker_mode', 'tracker_count', 'tracker_opacity', 'tracker_reset', 'tracker_position')))
    for count in range(3):
        codec.apply_window({'tracker_count': count, 'tracker_mode': count, 'tracker_opacity': count}, settings, None)
        check('tracker codec round trip %d' % count,
              codec.to_window(settings.values())['tracker_count'] == count)
    settings.update({'wnxTracker': {'position': [0.2, 0.8]}})
    reloaded = Settings(session, settings._store)
    check('new fields persist with unknown nested keys and existing settings',
          reloaded['wnxTracker']['position'] == [0.2, 0.8]
          and reloaded['wnxTracker']['futureField'] == 'preserved' and reloaded['externalMod']['value'] == 17)

    class Fetch(object):
        def __init__(self): self.calls = []
        def fetch(self, *args, **kwargs): self.calls.append(args)
    class Response(object):
        responseCode = 200
        body = json.dumps({'meta': {'updated': '2026-11-17T21:54:15.243Z'}, 'data': [{
            'tank_id': 6209, 'expected_damage': 1200, 'expected_frags': 0.8,
            'expected_spots': 1.1, 'expected_assistance': 500, 'is_fallback': False}]})
    fetch = Fetch()
    expected = Expected(fetch, os.path.join(workdir, 'expected-cache.json'))
    original_account = getattr(helpers, 'isPlayerAccount', None)
    try:
        helpers.isPlayerAccount = lambda: True
        expected.refresh()
        expected.refresh()
        check('only verified origin requested; concurrent requests coalesced', len(fetch.calls) == 1 and fetch.calls[0][0] == ORIGIN)
        expected._received(Response())
        table = copy.deepcopy(expected.table)
        expected.refresh()
        check('daily request cap with usable expected table', len(fetch.calls) == 1)
        offline = Expected(fetch, expected.store)
        check('offline cache preserves source/hash/date and intCD lookup',
              offline.table == table and 6209 in offline.table and offline.version == expected.version)
        broken = Response()
        broken.body = '{"data":[]}'
        expected._received(broken)
        check('malformed origin never replaces previous usable expectations', expected.table == table)
        broken.responseCode = 503
        expected._received(broken)
        check('server failure never caches unknown expected values', expected.table == table)
        helpers.isPlayerAccount = lambda: False
        expected._received(Response())
        check('response arriving in battle defers parsing and disk write to garage', expected._pending is not None)
        helpers.isPlayerAccount = lambda: True
        expected.refresh()
        check('deferred expected response applied in garage', expected._pending is None and expected.table == table)
        with open(expected.store, 'rb') as handle: cache = json.load(handle)
        cache['payload']['data'][0]['expected_damage'] = 999
        with open(expected.store, 'wb') as handle: json.dump(cache, handle)
        check('invalid content hash rejected instead of silently changing WNX', not Expected(fetch, expected.store).table)
    finally:
        if original_account is None:
            del helpers.isPlayerAccount
        else:
            helpers.isPlayerAccount = original_account

    check_history_messages(session, settings)
    session.close()
    check_history_delivery()


def check_history_messages(session, settings):
    from unicum.tracker.controller import Controller
    from unicum.tracker.writer import HistoryView
    from unicum.tracker.extract import extract
    from checks.battles import RESULTS

    account = '531280131'
    constants = type('Bonus', (), {'REGULAR': 1})
    row = extract(RESULTS, 'eu', account, constants)
    rows = [dict(row, arenaUniqueId=str(i + 1)) for i in range(10)]
    tracker = type('Tracker', (), {'account': account, 'revision': 0})()
    lookup = type('Lookup', (), {'get': lambda *args: None})()
    scales = type('Scales', (), {'color': lambda *args: None})()
    tab = type('Tab', (), {'_page': lambda self: ''})()
    controller = Controller(session, settings, tracker, lookup, scales)
    controller._tank = lambda tank_id: ('Fixture tank', 10)
    controller.expected.table = {6209: {'damage': 1200, 'frags': 0.8, 'spots': 1.1, 'assist': 500}}
    settings.update({'wnxTracker': {'count': 10}})
    for language, play_more, incomplete, unknown, missing in (
            ('en', 'Play 1 more random battles', 'Incomplete battle results', 'Unknown tank',
             'Missing WNX expectations for some tanks'),
            ('uk', u'Зіграйте ще 1 випадкових боїв', u'Неповні результати боїв', u'Невідомий танк',
             u'Для деяких танків бракує очікуваних значень WNX')):
        settings.update({'settingsLanguage': language})
        tracker.history = HistoryView(rows[:-1], None, False, False)
        tracker.revision += 1
        state = controller._model()
        check('%s genuine shortfall gets the battle-count message' % language,
              state['progress'] == 9 and state['message'] == play_more)

        tracker.history = HistoryView(rows[:-1] + [dict(rows[-1], tankId=None, schemaVersion=2)],
                                      None, False, False)
        tracker.revision += 1
        state = controller._model()
        check('%s widget and graph tooltips explain the unavailable rating' % language,
              state['progress'] == 10 and state['wnx'] is None and state['message'] == incomplete
              and state['bars'][-1]['message'] == state['points'][-1]['message'] == incomplete
              and state['bars'][-1]['tankName'] == unknown and state['bars'][0]['tankName'] == 'Fixture tank')
        tracker.history = HistoryView(rows[:-1] + [dict(rows[-1], tankId=123)], None, False, False)
        tracker.revision += 1
        state = controller._model()
        check('%s missing tank expectations have their own widget and tooltip text' % language,
              state['progress'] == 10 and state['message'] == state['bars'][-1]['message'] == missing)


def check_history_delivery():
    from unicum.game_link import proof
    from unicum.runtime.session import Session
    from unicum.tracker import service
    from unicum.tracker.store import History
    from checks.battles import RESULTS

    class LogThreads(logging.Handler):
        def __init__(self):
            logging.Handler.__init__(self)
            self.threads = []

        def emit(self, record):
            self.threads.append(threading.current_thread())

    def wait_for(tracker, predicate):
        deadline = time.time() + 5
        while time.time() < deadline:
            tracker.identify()
            if tracker.history is not None and predicate(tracker.history):
                return tracker.history
            time.sleep(0.01)
        return None

    original_identity, original_replay = proof.current_account_id, service.playing_replay
    original_constants = sys.modules.get('constants')
    original_append = History._append
    first, second = '531280131', '595280968'
    result = dict(RESULTS, personal={'avatar': {'accountDBID': int(first)}})
    partial = copy.deepcopy(result)
    partial['vehicles']['13089208'][0].pop('damageAssistedTrack')
    started, release = threading.Event(), threading.Event()
    main_thread = threading.current_thread()
    log, captured = logging.getLogger('unicum.tracker.store'), LogThreads()
    log.addHandler(captured)
    session = Session(0)
    try:
        constants = types.ModuleType('constants')
        constants.ARENA_BONUS_TYPE = type('Bonus', (), {'REGULAR': 1})
        sys.modules['constants'] = constants
        identity = [None]
        proof.current_account_id = lambda: identity[0]
        service.playing_replay = lambda: False
        tracker = service.Tracker(session)
        tracker.record(dict(RESULTS, arenaUniqueID=987654320))
        tracker.record(partial)
        tracker.record(partial)
        service.playing_replay = lambda: True
        tracker.record(dict(result, arenaUniqueID=987654321))
        session.close()

        session = Session(1)
        tracker = service.Tracker(session)
        service.playing_replay = lambda: False
        identity[0] = second
        state = wait_for(tracker, lambda view: True)
        check('anonymous receipt survives close and does not follow the next login',
              state is not None and not state.rows)
        tracker.record(RESULTS)  # Older results can still use the client account.
        state = wait_for(tracker, lambda view: len(view.rows) == 1)
        check('signed-in account extracts only its own tank and damage', state is not None
              and state.rows[0]['tankId'] == 8545 and state.rows[0]['damageDealt'] == 872)
        rejected = False
        try:
            tracker.reset(('eu', first))
        except ValueError:
            rejected = True
        check('reset confirmation cannot cross account switch', rejected)

        identity[0] = first
        state = wait_for(tracker, lambda view: True)
        check('restart retains one verified partial result and excludes replay and unowned results',
              state is not None and [row['arenaUniqueId'] for row in state.rows] ==
              [str(RESULTS['arenaUniqueID'])] and state.rows[0]['damageAssistedTrack'] is None)
        tracker.record(result)
        state = wait_for(tracker, lambda view: view.rows[0]['damageAssistedTrack'] is not None)
        check('normal consumer upgrades a partial result in place on complete redelivery',
              state is not None and len(state.rows) == 1 and state.rows[0]['damageAssistedTrack'] == 59)

        def slow_append(history, item):
            started.set()
            if not release.wait(5):
                raise IOError('test did not release worker')
            return original_append(history, item)

        History._append = slow_append
        older = dict(result, arenaUniqueID=987654322)
        later = dict(result, arenaUniqueID=987654323,
                     common=dict(result['common'], arenaCreateTime=int(time.time()) + 10))
        tracker.record(older)
        check('write is pending while the game can keep reading the current view',
              started.wait(2) and tracker.identify() == first and tracker.history is state)
        tracker.reset(('eu', first))
        tracker.record(older)
        tracker.record(later)
        check('reset and a result can enqueue without waiting on slow disk',
              not release.is_set() and tracker.history is state)
        release.set()
        state = wait_for(tracker, lambda view: [row['arenaUniqueId'] for row in view.rows] == ['987654323'])
        check('FIFO reset drops old callbacks and retains only the post-reset battle', state is not None)

        failure = dict(later, arenaUniqueID=987654324)
        def failed_append(history, item):
            raise IOError('deliberate write failure')
        History._append = failed_append
        tracker.record(failure)
        state = wait_for(tracker, lambda view: view.pending)
        check('worker exposes write error without counting the uncommitted result',
              state is not None and state.error == 'storage_error' and len(state.rows) == 1)
        tracker.identify()
        check('storage errors reach client log handlers on the game thread', captured.threads == [main_thread])
        History._append = original_append
        session.close()
        check('normal teardown retries a failed write and preserves both accounts on disk',
              [row['arenaUniqueId'] for row in History('eu', first).rows] == ['987654323', '987654324']
              and len(History('eu', second).rows) == 1)
    finally:
        release.set()
        History._append = original_append
        session.close()
        log.removeHandler(captured)
        proof.current_account_id, service.playing_replay = original_identity, original_replay
        if original_constants is None:
            sys.modules.pop('constants', None)
        else:
            sys.modules['constants'] = original_constants


def check_escape():
    from unicum.runtime.session import Session
    from unicum.tracker.controller import Controller
    import helpers

    class Event(object):
        def __init__(self, key, down=True, repeated=False):
            self.key, self.down, self.repeated = key, down, repeated

        def isKeyDown(self): return self.down
        def isRepeatedEvent(self): return self.repeated

    class Flash(object):
        settings = False
        actions = 0

        def escapeTrackerSettings(self):
            if not self.settings:
                return False
            self.settings = False
            self.actions += 1
            return True

    original_keys = sys.modules.get('Keys')
    original_account = getattr(helpers, 'isPlayerAccount', None)
    session = Session(0)
    try:
        keys = sys.modules['Keys'] = types.ModuleType('Keys')
        keys.KEY_ESCAPE = 1
        helpers.isPlayerAccount = lambda: True
        controller = Controller.__new__(Controller)
        controller.session, controller._escape_held, controller._flash = session, False, Flash()
        wrapped = controller._wrap_key(lambda event: 'native')
        check('closed custom window passes Escape to the system menu', wrapped(Event(1)) == 'native')
        controller._flash.settings = True
        check('non-Escape key retains original behaviour', wrapped(Event(2)) == 'native')
        check('custom-window Escape consumed without native menu', wrapped(Event(1)) is True)
        check('Escape repeat and key-up consumed once without re-closing',
              wrapped(Event(1, repeated=True)) is True and wrapped(Event(1, down=False)) is True
              and controller._flash.actions == 1)
        check('subsequent fresh Escape reaches native menu', wrapped(Event(1)) == 'native')
        controller._flash.settings = True
        helpers.isPlayerAccount = lambda: False
        check('input ownership never consumes battle Escape', wrapped(Event(1)) == 'native')
    finally:
        if original_keys is None:
            sys.modules.pop('Keys', None)
        else:
            sys.modules['Keys'] = original_keys
        if original_account is None:
            del helpers.isPlayerAccount
        else:
            helpers.isPlayerAccount = original_account
        session.close()
