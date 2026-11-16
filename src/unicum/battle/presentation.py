"""Cached roster presentation and the battle's immediate, cache-only Alt path."""
import logging
import math

from unicum import views
from unicum.roster import row_data

_logger = logging.getLogger('unicum.battle.presentation')
_SURFACES = ('panel', 'tab', 'loading')


def _finite(value):
    return value if value is not None and not (math.isnan(value) or math.isinf(value)) else None


class RosterPresentations(object):
    """One formatted career presentation per account for the current arena.

    Values rather than entry identity catch settings changes, in-place cache
    updates and refreshed colour scales. Reading them never starts a fetch.
    """

    def __init__(self):
        self._values = {}
        self.hits = 0
        self.formats = 0

    def clear(self):
        self._values.clear()

    def get(self, account_id, entry, settings, badges, want_long=False, long_builder=None):
        window = settings.window_of('wnx')
        winrate = settings.extra('winrate', 'battle')
        battles = settings.extra('battles', 'battle')
        value = _finite(entry.rating('wnx', window)) if entry is not None else None
        wr = _finite(entry.stat('winrate', winrate)) if entry is not None and winrate else None
        count = _finite(entry.stat('battles', battles)) if entry is not None and battles else None
        band = badges.color('wnx', value) if value is not None else None
        signature = (value, wr, count, window, winrate, battles,
                     settings.winrate_decimal(), settings.shows('battle'), band)
        kept = self._values.get(account_id)
        if kept is None or kept['signature'] != signature:
            kept = {'signature': signature, 'row': row_data(entry, settings, badges), 'long': None}
            self._values[account_id] = kept
            self.formats += 1
        else:
            self.hits += 1
        if want_long and kept['long'] is None:
            kept['long'] = long_builder(entry) if long_builder is not None and value is not None else ''
        return kept['row'], kept['long'] or ''


class BattleVisibility(object):
    """Alt changes existing fields immediately without rebuilding the roster."""

    def _on_alt(self):
        view = views.battle_view()
        if view is None:
            return
        held = self.alt is not None and self.alt.down
        hidden = tuple(self._settings.alt_only(surface) and not held for surface in _SURFACES)
        previous = self._published
        current = previous[1] if previous is not None and previous[0] is view else None
        if current is not None and current[3:6] == hidden and current[10] == held:
            return
        if not held and current is not None and current[10]:
            self._panel_metrics(view)
        try:
            view.panelWnxBadgesVisible = held
            view.panelHidden, view.tabHidden, view.loadingHidden = hidden
        except Exception:
            _logger.debug('the battle view cannot update Alt visibility yet', exc_info=True)
            return
        if current is not None:
            state = current[:3] + hidden + current[6:10] + (held,) + current[11:]
            self._published = (view, state)
            if hidden != current[3:6]:
                # Team averages use the arena-description path. It can read
                # cached entries here, but a keypress cannot queue fetches.
                self._alt_dispatch = True
                try:
                    self._redraw()
                finally:
                    self._alt_dispatch = False

    def _panel_metrics(self, view):
        """Read the existing AS3 counters on release only when measuring."""
        try:
            enabled = getattr(self._settings, 'measures_performance', None)
            if enabled is None or not enabled():
                return
            _logger.info('Alt release panel metrics: %s', view.takePanelMetrics())
        except Exception:
            _logger.debug('the battle view cannot provide panel metrics yet', exc_info=True)

    def _settings_changed(self):
        self._presentations.clear()
        self._redraw()
        self._publish()
