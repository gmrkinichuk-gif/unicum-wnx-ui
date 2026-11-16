"""Regression checks for cached roster formatting and the immediate Alt path.

These use the real Python presentation, dispatch and lifecycle code. A fake
client supplies only scheduling/input; no network or game launch is needed.
"""
from checks.common import check


class _Settings(object):
    def __init__(self):
        self.window = 'recent'
        self.decimal = True
        self.visible = True
        self.waiting = set()

    def window_of(self, metric):
        return self.window

    def extra(self, metric, surface):
        return 'total'

    def winrate_decimal(self):
        return self.decimal

    def shows(self, surface):
        return self.visible

    def alt_only(self, surface):
        return surface in self.waiting


class _Scales(object):
    def __init__(self):
        self.band = '#4a92b7'

    def color(self, metric, value):
        return self.band

    def text_color(self, metric, value):
        return self.band


def check_roster_cache():
    from unicum.api.entry import Entry
    from unicum.battle.presentation import RosterPresentations
    from unicum.roster import row_data

    settings, scales, cache = _Settings(), _Scales(), RosterPresentations()
    entries = dict((i, Entry(ratings={'recent': {'wnx': 1000 + i},
                                    'total': {'winrate': 52.34, 'battles': 1500}}))
                   for i in range(1, 31))
    built = []

    def long_builder(entry):
        built.append(entry)
        return 'pill:%s' % entry.rating('wnx', settings.window)

    expected = dict((i, row_data(entry, settings, scales)) for i, entry in entries.items())
    for unused in range(20):
        for account, entry in entries.items():
            row, long_badge = cache.get(account, entry, settings, scales, True, long_builder)
            assert row == expected[account] and long_badge.startswith('pill:')
    check('30 unchanged accounts over 20 passes format once each',
          cache.formats == 30 and cache.hits == 570 and len(built) == 30)

    entries[1].ratings['recent']['wnx'] = 2300
    row, unused = cache.get(1, entries[1], settings, scales, True, long_builder)
    check('an API refresh changing an existing entry updates only that account',
          row['wnx'] == 2300 and cache.formats == 31 and len(built) == 31)
    entries[1].ratings['total']['battles'] = 2500
    row, unused = cache.get(1, entries[1], settings, scales)
    check('battle count updates invalidate the cached text', row['battles'] == '2.5k')
    settings.decimal = False
    row, unused = cache.get(1, entries[1], settings, scales)
    check('a win-rate display setting invalidates the cached text',
          row == row_data(entries[1], settings, scales))
    scales.band = '#7a4fb2'
    row, unused = cache.get(1, entries[1], settings, scales)
    check('a refreshed original colour scale invalidates the cached colours',
          row['bandColor'] == '#7a4fb2' and row['color'] == '#7a4fb2')
    settings.visible = False
    row, unused = cache.get(1, entries[1], settings, scales)
    check('hiding statistics removes extras on the next presentation',
          'battles' not in row and 'winrate' not in row)
    missing, pill = cache.get(99, None, settings, scales, True, long_builder)
    check('missing statistics retain absence rather than fabricated zeroes',
          missing == {'wnxAvailable': False} and pill == '')
    invalid = Entry(ratings={'recent': {'wnx': float('nan')}})
    cache.get(100, invalid, settings, scales, True, long_builder)
    before = cache.formats
    invalid_row, pill = cache.get(100, invalid, settings, scales, True, long_builder)
    check('non-finite WNX is missing, and remains cacheable',
          invalid_row == {'wnxAvailable': False} and pill == '' and cache.formats == before)
    cache.clear()
    cache.get(1, entries[1], settings, scales)
    check('a new arena discards the old account presentation', cache.formats == before + 1)


def check_alt_dispatch():
    from unicum import views
    from unicum.battle.flags import BattleFlags

    class NoWork(object):
        def __getattr__(self, name):
            raise AssertionError('Alt attempted expensive work: ' + name)

    class View(object):
        def __init__(self):
            self.markersText = 'existing roster bytes'
            self.leftIds, self.rightIds = '1,2', '3,4'

    class Alt(object):
        down = False

    settings, view = _Settings(), View()
    flags = BattleFlags(NoWork(), NoWork(), NoWork(), NoWork(), settings)
    flags.alt = Alt()
    flags._published = (view, ('payload', '1,2', '3,4', False, False, False,
                              True, True, True, False, False, True, True))
    original = views.battle_view
    views.battle_view = lambda: view
    redraws = []

    def redraw():
        redraws.append(flags._alt_dispatch)
        # The existing average callback can still ask for missing entries.
        # On a key edge, these calls may never enqueue network work.
        flags._request(123)
        flags._request_vehicle(123, 456, 'random')

    flags._redraw = redraw
    flags._publish = NoWork()
    try:
        for held in [True, False] * 50:
            flags.alt.down = held
            flags._on_alt()
            assert view.panelWnxBadgesVisible == held
        check('100 Alt edges change existing visibility without reading the roster',
              view.markersText == 'existing roster bytes' and redraws == [])
        check('Alt dispatch keeps the full published state in sync',
              flags._published[1][10] is False and len(flags._published[1]) == 13)
        metrics = []
        settings.measures_performance = lambda: True
        view.takePanelMetrics = lambda: metrics.append('existing AS3 counters') or metrics[-1]
        flags.alt.down = True
        flags._on_alt()
        check('panel metrics do not query AS3 during the press', metrics == [])
        flags.alt.down = False
        flags._on_alt()
        flags._on_alt()
        check('performance mode reads cached AS3 counters on the release edge once',
              metrics == ['existing AS3 counters'])
        settings.measures_performance = lambda: False
        flags.alt.down = True
        flags._on_alt()
        flags.alt.down = False
        flags._on_alt()
        check('with performance mode off, releasing Alt never calls the metrics proxy', len(metrics) == 1)

        def unavailable():
            raise RuntimeError('view has already been disposed')

        view.takePanelMetrics = unavailable
        settings.measures_performance = lambda: True
        flags.alt.down = True
        flags._on_alt()
        flags.alt.down = False
        flags._on_alt()
        check('an unavailable metrics proxy cannot interrupt the native key release',
              not view.panelWnxBadgesVisible and flags._published[1][10] is False)
        settings.measures_performance = lambda: False
        settings.waiting = set(('tab', 'loading'))
        flags._on_alt()
        check('Alt-only Tab and loading use their independent visibility slots',
              view.tabHidden and view.loadingHidden and not view.panelHidden)
        flags.alt.down = True
        flags._on_alt()
        check('team averages redraw only after a surface visibility change',
              redraws == [True, True] and not view.tabHidden and not view.loadingHidden)
        check('an Alt-only redraw cannot enqueue account or tank requests',
              not flags._pending and not flags._pending_pairs and not flags._alt_dispatch)
        views.battle_view = lambda: None
        flags.alt.down = False
        flags._on_alt()
        check('a disposed or not-yet-created battle view receives no writes',
              flags._published[1][10] is True)
    finally:
        views.battle_view = original


def check_alt_release():
    import sys
    import types
    import BigWorld
    import helpers
    from unicum import extended_info
    from unicum.runtime.session import Session

    class Event(object):
        key = 56

        def __init__(self, down):
            self.ctx = {'isDown': down}
            self.pressed = down

        def isKeyDown(self):
            return self.pressed

    absent = object()
    old_key = getattr(BigWorld, 'isKeyDown', absent)
    old_avatar = getattr(helpers, 'isPlayerAvatar', absent)
    old_mapping = sys.modules.get('CommandMapping', absent)
    physically_down = [True]
    mapping = types.ModuleType('CommandMapping')
    mapping.CMD_VEHICLE_MARKERS_SHOW_INFO = 'showInfo'

    class Commands(object):
        def isFired(self, command, key):
            return command == 'showInfo' and key == 56

        def get(self, name):
            assert name == 'CMD_VEHICLE_MARKERS_SHOW_INFO'
            return 56

    mapping.g_instance = Commands()
    sys.modules['CommandMapping'] = mapping
    BigWorld.isKeyDown = lambda key: key == 56 and physically_down[0]
    helpers.isPlayerAvatar = lambda: True
    session = Session(generation=0)
    alt = extended_info.ExtendedInfo(session)
    changes = []
    alt.on_change(lambda: changes.append(alt.down))
    baseline = set(BigWorld.pending)
    try:
        alt._on_event(Event(True))
        alt._on_key(Event(True))
        check('native event and input report one shared press edge', changes == [True])
        alt._on_key(Event(False))
        check('a native key-up clears a paired event whose release was missed',
              not alt.down and changes == [True, False])
        alt._on_key(Event(True))
        alt._on_event(Event(True))
        alt._on_event(Event(False))
        check('a native event-up also clears a paired input latch', not alt.down)
        for unused in range(100):
            alt._on_key(Event(True))
        added = set(BigWorld.pending) - baseline
        check('rapid repeated presses share a single physical-key reconciliation', len(added) == 1)
        physically_down[0] = False
        for handle in added:
            BigWorld.pending.pop(handle)()
        check('a physically released key clears a missed up after focus loss',
              not alt.down and not alt._key_check_pending)
        physically_down[0] = True
        alt._on_key(Event(True))
        check('a new held key schedules reconciliation again', len(set(BigWorld.pending) - baseline) == 1)
        session.close()
        check('session teardown cancels every pending reconciliation callback',
              set(BigWorld.pending) == baseline)
    finally:
        session.close()
        for module, name, previous in ((BigWorld, 'isKeyDown', old_key),
                                       (helpers, 'isPlayerAvatar', old_avatar)):
            if previous is absent:
                delattr(module, name)
            else:
                setattr(module, name, previous)
        if old_mapping is absent:
            del sys.modules['CommandMapping']
        else:
            sys.modules['CommandMapping'] = old_mapping


def run():
    check_roster_cache()
    check_alt_dispatch()
    check_alt_release()
