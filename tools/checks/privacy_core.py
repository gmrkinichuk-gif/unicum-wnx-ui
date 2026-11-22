# -*- coding: utf-8 -*-
"""Exercise the shipped WNX features against fake client interfaces."""
import json
import os
import sys
import types

from checks.common import REPO, check


def run(workdir):
    from unicum import profile, views
    from unicum.api.entry import Entry, PLAYERS
    from unicum.api.resolve import Lookup
    from unicum.runtime.session import Session
    from unicum.settings import Settings
    from unicum.settings_window.codec import apply_window
    from unicum.tracker import formula, results, visibility
    from unicum.tracker.extract import extract
    from unicum.tracker.page import for_settings
    from unicum.tracker.store import History, LIMIT

    path = os.path.join(workdir, 'privacy-settings.json')
    with open(path, 'w') as handle:
        json.dump({'sendReplays': True, 'sendLoadouts': True, 'twitch': {'channel': 'private'},
                   'metric': 'wn8', 'battle': {'flags': True}, 'wnxTracker': {'count': 30}}, handle)
    session = Session(77)
    settings = Settings(session, store=path)
    check('legacy upload and flag settings cannot activate', settings['metric'] == 'wnx'
          and not settings.sends_replays() and not settings.sends_loadouts()
          and not settings.sends_battles() and not settings.shows_flags('battle'))
    apply_window({'wnx_panel_stripe': False, 'twitchChannel': 'ignore', 'sendReplays': True}, settings, None)
    with open(path) as handle:
        stored = json.load(handle)
    check('only core settings are saved', set(stored) <= set(profile.KEYS)
          and 'flags' not in stored['battle'] and stored['wnxTracker']['count'] == 30)
    check('Apply persists supported options across reopen',
          Settings(session, store=path)['wnxUI']['panel']['stripe'] is False)
    expected = type('Expected', (object,), {'updated': ''})()
    controls = set(row['var'] for tab in for_settings(settings.values(), expected)
                   for row in tab['rows'] if 'var' in row)
    check('Tracker settings expose core controls without inherited integrations',
          {'wnx_panel_stripe', 'battleRating', 'tracker_opacity'} <= controls
          and not {'sendReplays', 'twitchConnect', 'tankButton'} & controls)
    apply_window({'battleRating': False}, settings, None)
    check('battle ratings can be disabled without enabling flags or uploads',
          settings.metric('battle') is None and not settings.shows_flags('battle'))
    from unicum.tracker.controller import Controller
    controller = Controller.__new__(Controller)
    controller.settings = settings
    for mode in ('Mini', 'Battles', 'Trend', 'Compact'):
        controller._action({'kind': 'mode', 'value': mode}, None)
        check('tab selection persists ' + mode, Settings(session, store=path)['wnxTracker']['mode'] == mode)
    controller._action({'kind': 'mode', 'value': 'unknown'}, None)
    check('invalid tab selection is ignored', settings['wnxTracker']['mode'] == 'Compact')
    for language, modes in (('en', ['Mini', 'Compact', 'Trend', 'Battles']),
                            ('uk', [u'Міні', u'Компакт', u'Тренд', u'Бої'])):
        settings.update({'settingsLanguage': language})
        rows = dict((row['var'], row) for tab in for_settings(settings.values(), expected)
                    for row in tab['rows'] if row.get('kind') == 'dropdown')
        check('settings choices retain canonical order in ' + language,
              rows['tracker_mode']['options'] == modes
              and rows['tracker_count']['options'] == ['10', '20', '30']
              and rows['tracker_opacity']['options'] == ['40%', '50%', '60%', '70%', '80%', '90%'])
    apply_window({'tracker_mode': 2, 'tracker_count': 0, 'tracker_opacity': 5}, settings, None)
    window = Settings(session, store=path)['wnxTracker']
    check('direct settings choices persist mode, count and opacity',
          (window['mode'], window['count'], window['opacity']) == ('Trend', 10, 90))
    apply_window({'wnx_loading_opacity': 0, 'wnx_panel_opacity': 5, 'wnx_tab_opacity': 10}, settings, None)
    battle_ui = Settings(session, store=path)['wnxUI']
    check('opacity slider indices persist through settings storage',
          [battle_ui[surface]['opacity'] for surface in ('loading', 'panel', 'tab')] == [0, 50, 100])

    good = 'https://unicum.gg/api/eu/resolve?players=123&vehicles=123:57&mode=random'
    check('public WNX queries are allowed', profile.permits(good)
          and profile.permits('https://unicum.gg/api/ratings/scales')
          and profile.permits('https://api.tomato.gg/api/wnx/wnx-expected-values.json'))
    for url, options in ((good, {'method': 'POST'}), (good, {'post_data': 'payload'}),
                         (good, {'headers': {'Authorization': 'Bearer private'}}),
                         (good + '&clans=1', {}), (good + '&players=456', {}),
                         (good.replace('unicum.gg', 'example.com'), {}),
                         ('https://unicum.gg/api/game/me', {})):
        try:
            session.fetch(url, lambda response: None, **options)
        except ValueError:
            continue
        check('non-core request refused before engine dispatch', False)
    check('uploads, credentials and non-WNX destinations rejected', True)
    lookup = Lookup(session, 'eu', store=False)
    lookup._absorb({'players': [123], 'clans': [], 'tags': [], 'vehicles': []},
                   {'players': {'123': {'nickname': 'private', 'countries': ['FR'],
                                        'ratings': {'total': {'wnx': 987, 'wn8': 42}}}}})
    cached = lookup.get(PLAYERS, 123)
    check('lookup accepts only rendered ratings and schedules no disk save',
          isinstance(cached, Entry) and cached.name is None and not cached.countries
          and cached.ratings == {'total': {'wnx': 987}} and not session._callbacks)

    name = 'gui.battle_results.service'
    previous = sys.modules.get(name)
    parent_name = 'gui.battle_results'
    previous_parent = sys.modules.get(parent_name)
    parent = types.ModuleType(parent_name)
    parent.__path__ = []
    sys.modules[parent_name] = parent
    service = types.ModuleType(name)
    received = []

    class Service(object):
        def postResult(self, result, needToShowUI=True):
            return result, needToShowUI

    service.BattleResultsService = Service
    parent.service = service
    sys.modules[name] = service
    try:
        original = Service.postResult.im_func
        tracker = type('Tracker', (object,), {'record': lambda self, row: received.append(row)})()
        results.install(session, tracker)
        marker = {'arenaUniqueID': 1}
        check('local result hook forwards native result and invokes own tracker',
              Service().postResult(marker, False) == (marker, False) and received == [marker])
        session.close()
        check('local result hook restores the client handler', Service.postResult.im_func is original)
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        if previous_parent is None:
            sys.modules.pop(parent_name, None)
        else:
            sys.modules[parent_name] = previous_parent

    raw = {'arenaUniqueID': 12, 'personal': {'avatar': {'accountDBID': 123}},
           'common': {'bonusType': 1, 'arenaCreateTime': 1700000000, 'winnerTeam': 1},
           'vehicles': {'1': {'accountDBID': 123, 'typeCompDescr': 57, 'team': 1,
                              'damageDealt': 900, 'damageAssistedRadio': 80,
                              'damageAssistedTrack': 20, 'spotted': 1, 'kills': 1},
                        '2': {'accountDBID': 987, 'name': 'foreign-name', 'damageDealt': 9000}}}
    constants = type('Bonus', (object,), {'REGULAR': 1})
    row = extract(raw, 'eu', '123', constants)
    check('own result extraction excludes other accounts and accepts only the owner',
          row is not None and row['damageDealt'] == 900 and
          extract(raw, 'eu', '987', constants) is None and 'foreign-name' not in repr(row))
    directory = os.path.join(workdir, 'privacy-tracker')
    history = History('eu', '123', root=directory)
    for index in range(LIMIT + 2):
        history.add(dict(row, arenaUniqueId=str(index + 1), startedAt=row['startedAt'] + index))
    reopened = History('eu', '123', root=directory)
    check('own history survives reopening with a 60-battle cap',
          LIMIT == 60 and len(reopened.rows) == LIMIT and reopened.rows[0]['arenaUniqueId'] == '3')
    with open(history.path) as handle:
        raw_log = handle.read()
    check('rolling journal compacts away expired records and excludes other players',
          'foreign-name' not in raw_log and '"arenaUniqueId":"1"' not in raw_log)

    # Exercise the same visibility predicate against the client's shapes.
    from frameworks.wulf import WindowLayer, WindowStatus
    held = getattr(WindowLayer, 'WINDOW', None)
    hangar_check, original_dependency = visibility.in_hangar, views.dependency.instance
    windows = []
    visible = [True]
    manager = type('Manager', (object,), {'findWindows': lambda self, pred: list(filter(pred, windows))})()
    loader = type('Loader', (object,), {'windowsManager': manager})()
    WindowLayer.WINDOW = 'window'
    visibility.in_hangar = lambda: visible[0]
    views.dependency.instance = lambda interface: loader
    try:
        check('unobstructed hangar can show the tracker', visibility.unobstructed())
        modal = type('Modal', (object,), {'layer': WindowLayer.WINDOW, 'windowStatus': 'loaded',
                                          'isHidden': lambda self: False, 'isModal': lambda self: True})()
        windows.append(modal)
        check('foreground modal hides tracker on the hangar route', not visibility.unobstructed())
        modal.isHidden = lambda: True
        check('hidden window no longer covers the hangar', visibility.unobstructed())
        # Hangar and world-marker surfaces are not overlay windows; even their
        # proxy methods may be unavailable while they initialize.
        windows[:] = [type('HangarWindow', (object,), {'layer': 'sub-view'})()]
        check('ordinary hangar components never count as blocking windows', visibility.unobstructed())
        indicator = type('_GFMoEBlWindow', (object,), {'layer': WindowLayer.WINDOW,
                         'windowStatus': 'loaded', 'isHidden': lambda self: False,
                         'isModal': lambda self: False})()
        windows.append(indicator)
        check('the MoE hangar badge does not cover the tracker', visibility.unobstructed())
        indicator.isModal = lambda: True
        check('a modal MoE window still hides the tracker', not visibility.unobstructed())
        visible[0] = False
        check('non-hangar foreground route hides tracker', not visibility.unobstructed())
    finally:
        views.dependency.instance = original_dependency
        visibility.in_hangar = hangar_check
        if held is None:
            del WindowLayer.WINDOW
        else:
            WindowLayer.WINDOW = held

    with open(os.path.join(REPO, 'tools', 'fixtures', 'wnx_parity.json')) as handle:
        parity = json.load(handle)
    for case in parity['cases']:
        expected = dict((int(k), v) for k, v in case['expected'].items())
        actual = formula.compute(case['tanks'], expected)
        value = case['value']
        check('WNX formula parity: ' + case['name'], actual == value or
              (actual is not None and value is not None and abs(actual - value) <= parity['tolerance']))
