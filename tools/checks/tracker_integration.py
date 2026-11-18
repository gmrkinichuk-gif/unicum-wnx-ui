"""Full settings parity, offline expected cache and account-bound consumer checks."""
import copy
import json
import os
import sys
import types

from checks.common import check


def run(workdir):
    from unicum.settings import Settings
    from unicum.runtime.session import Session
    from unicum.settings_window import codec, page
    from unicum.tracker.page import build, CATEGORIES
    from unicum.tracker.expected import Expected, parse, ORIGIN
    from unicum.tracker import service
    from unicum.game_link import proof
    from checks.battles import RESULTS
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

    original_identity, original_replay = proof.current_account_id, service.playing_replay
    original_constants = sys.modules.get('constants')
    try:
        constants = types.ModuleType('constants')
        constants.ARENA_BONUS_TYPE = type('Bonus', (), {'REGULAR': 1})
        sys.modules['constants'] = constants
        identity = [None]
        proof.current_account_id = lambda: identity[0]
        service.playing_replay = lambda: False
        tracker = service.Tracker(session)
        tracker.record(RESULTS)
        check('unknown identity retains delayed raw result in memory', len(tracker._pending) == 1)
        identity[0] = '531280131'
        tracker.identify()
        check('garage identity resolves delayed result once', len(tracker.history.rows) == 1 and not tracker._pending)
        tracker.record(RESULTS)
        check('consumer deduplicates repeated confirmed results', len(tracker.history.rows) == 1)
        service.playing_replay = lambda: True
        tracker.record(dict(RESULTS, arenaUniqueID=987654321))
        check('replay playback never enters history', len(tracker.history.rows) == 1)
        service.playing_replay = lambda: False
        identity[0] = '595280968'
        tracker.identify()
        check('account switching isolates local history', not tracker.history.rows)
        tracker.record(RESULTS)
        check('other account extracts only its own tank and damage', tracker.history.rows[0]['tankId'] == 8545
              and tracker.history.rows[0]['damageDealt'] == 872)
        try:
            tracker.reset(('eu', '531280131'))
        except ValueError:
            pass
        check('reset confirmation cannot cross account switch', len(tracker.history.rows) == 1)
    finally:
        proof.current_account_id, service.playing_replay = original_identity, original_replay
        if original_constants is None:
            sys.modules.pop('constants', None)
        else:
            sys.modules['constants'] = original_constants
    session.close()


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
