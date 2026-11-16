"""Exercise the real marker WNX bridge with a cached entry and fake canvas."""
import sys
import types

from checks.common import check


class Record(object):
    def __init__(self, **values):
        self.__dict__.update(values)


def run():
    base = 'gui.Scaleform.daapi.view.battle.shared.markers2d'
    missing = object()
    previous = dict((key, sys.modules.get(key, missing))
                    for key in (base, base + '.manager', 'unicum.name_markers'))
    package = types.ModuleType(base)
    package.__path__ = []
    manager_module = types.ModuleType(base + '.manager')
    manager_module.MarkersManager = type('MarkersManager', (object,), {})
    sys.modules[base], sys.modules[base + '.manager'] = package, manager_module
    import unicum
    from unicum import modes
    old_attribute = getattr(unicum, 'name_markers', missing)
    from unicum.battle import drawing
    old_arena, old_filter = drawing._arena, modes.team_filter
    try:
        from unicum.api.entry import Entry
        from unicum.name_markers import NameMarkers
        entry = Entry(ratings={'recent': {'wnx': 2180}, 'total': {'wnx': 1800}})
        entries = {1: entry, 2: entry}
        requested_metrics = []

        class Settings(object):
            enabled = True
            only_alt = False

            def window_of(self, metric):
                check('marker stripe asks for the configured WNX window', metric == 'wnx')
                return 'recent'

            def shows(self, surface):
                return self.enabled

            def alt_only(self, surface):
                return self.only_alt

        class Scales(object):
            def color(self, metric, value):
                requested_metrics.append(metric)
                return '#4a92b7'

            def text_color(self, metric, value):
                return self.color(metric, value)

        flags = Record(_settings=Settings(), _badges=Scales(), alt=None,
                       _lookup=Record(get=lambda kind, account: entries[account]))
        controller = NameMarkers.__new__(NameMarkers)
        controller._flags = flags
        controller._payloads = {}
        controller._reload_view_if_changed = lambda manager, ours: None
        formatted = []
        controller._text = lambda item: formatted.append(('text', item)) or 'existing badge text'
        controller._images = lambda item: formatted.append(('images', item)) or 'existing.png|20|10|4'
        vehicles = dict((i, Record(team=i, player=Record(accountDBID=i))) for i in (1, 2))
        drawing._arena = lambda: Record(getVehicleInfo=lambda vehicle: vehicles[vehicle])
        modes.team_filter = lambda settings: lambda team: True
        markers = dict((i, Record(getMarkerID=lambda i=i: i + 10)) for i in (1, 2))
        calls = []
        manager = Record(getPlugin=lambda name: Record(_markers=markers),
                         invokeMarker=lambda *args: calls.append(args))
        manager._unicumNameMarkerIds = set((11, 12))
        controller._draw(manager)
        check('both teams receive the exact original WNX band RGB',
              len(calls) == 2 and all(call[-1] == 0x4a92b7 for call in calls))
        check('the existing text and image payloads remain unchanged',
              all(call[1:-1] == ('setUnicumData', 'existing badge text', 0xffffff,
                                'existing.png|20|10|4') for call in calls))
        controller._draw(manager)
        check('unchanged marker data causes no second canvas update', len(calls) == 2)
        check('unchanged marker entries reuse their prepared payload', len(formatted) == 4)
        entries[1] = entries[2] = Entry(ratings={})
        controller._draw(manager)
        controller._draw(manager)
        check('unknown WNX sends one stable absent-colour sentinel, never zero or NaN',
              len(calls) == 4 and all(call[-1] == -1 for call in calls[2:]))
        check('replacement API entries invalidate only the prepared account payloads', len(formatted) == 8)
        modes.team_filter = lambda settings: lambda team: team == 1
        controller._draw(manager)
        check('team-filtered marker sends disabled sentinel instead of neutral grey',
              len(calls) == 5 and calls[-1][0] == 12 and calls[-1][-1] == -2)
        flags._settings.only_alt = True
        controller._draw(manager)
        check('Alt-only markers stay disabled while Alt is released',
              len(calls) == 6 and calls[-1][0] == 11 and calls[-1][-1] == -2)
        flags.alt = Record(down=True)
        controller._draw(manager)
        check('Alt enables the unknown-WNX marker only for the selected team',
              len(calls) == 7 and calls[-1][0] == 11 and calls[-1][-1] == -1)
        flags._settings.enabled = False
        controller._draw(manager)
        controller._draw(manager)
        check('disabled battle statistics do not leave neutral accents or repeated updates',
              len(calls) == 8 and calls[-1][-1] == -2)
        flags._settings.enabled = True
        entries[1] = entry
        controller._draw(manager)
        check('late available WNX replaces the unknown colour without affecting the filtered team',
              len(calls) == 9 and calls[-1][0] == 11 and calls[-1][-1] == 0x4a92b7)
        check('the new stripe never requests another rating metric',
              requested_metrics and set(requested_metrics) == set(('wnx',)))
    finally:
        drawing._arena, modes.team_filter = old_arena, old_filter
        for key, value in previous.items():
            if value is missing:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value
        if old_attribute is missing:
            if hasattr(unicum, 'name_markers'):
                delattr(unicum, 'name_markers')
        else:
            unicum.name_markers = old_attribute
