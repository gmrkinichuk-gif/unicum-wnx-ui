"""Putting a rating and a flag on each name, on every battle surface.

The measuring is here as much as the drawing. Scaleform gives no way to ask
what a string will be once its inline images have loaded, so the width is
computed from the markup, and `markup_width` is the one place that knows how.
A width guessed wrong is a column that overlaps the next one.

A mixin, for the reason the battles package gives: the entries, the session
and the settings are read by both halves.
"""
from __future__ import absolute_import

import logging

from unicum import modes, views
from unicum.battle.markup import icon_markers, markup_width
from unicum.battle.teams import TeamNames
from unicum.battle.presentation import BattleVisibility
from unicum.api.entry import PLAYERS
from unicum.roster import marker_text, native_name_fields

_logger = logging.getLogger('unicum.battle.drawing')

# The battle view's surfaces, in panelHidden/tabHidden/loadingHidden order.
_ALT_SURFACES = ('panel', 'tab', 'loading')

# The client's own method for "resend the arena's description", which is where
# a team name lives. Private, so it carries the mangled name of its class,
# `BattleStatisticsDataController`.
_ARENA_DESCRIPTION = '_BattleStatisticsDataController__setArenaDescription'

# The statistics controller's methods whose data can carry each team's order:
# every exchange it adds sort ids to (stats_ctrl.py). Frags re-sort the teams
# too, in the Tab of a mode that orders by them.
_ORDERED = ('as_setVehiclesDataS', 'as_addVehiclesInfoS', 'as_updateVehiclesInfoS',
            'as_updateVehicleStatusS', 'as_setFragsS', 'as_updateVehiclesStatsS')

# "Not looked up yet", which None cannot say: None is the answer for a mode
# with no per-vehicle record at all, and asking the client again every pass
# because the honest answer was None would be a read per row per second.
_UNASKED = object()


def tank_of(vInfo):
    """The vehicle id Wargaming keys its own per-vehicle statistics on, or None.

    `compactDescr` is that id: the same number the site stores a tank
    snapshot under, so a pair asked for here and a row stored there are the
    same tank without a translation table in between.
    """
    return getattr(getattr(vInfo, 'vehicleType', None), 'compactDescr', None)


def _arena():
    """The battle's arena data provider, or None outside a battle."""
    from helpers import dependency
    from skeletons.gui.battle_session import IBattleSessionProvider
    return dependency.instance(IBattleSessionProvider).getArenaDP()

def _default_order(arena):
    """Each team's vehicle ids as the client sorts them for its screens.

    What TeamsSortedIDsComposer sends: sorted by VehicleInfoSortKey, without
    observers. Stands in until the client sends its own, which a mode may
    sort its own way.
    """
    from gui.battle_control.arena_info import vos_collections

    def ids(collection):
        return [vehicle_id for vehicle_id in collection(sortKey=vos_collections.VehicleInfoSortKey).ids(arena)
                if not arena.getVehicleInfo(vehicle_id).vehicleType.isObserver]

    return {'leftItemsIDs': ids(vos_collections.AllyItemsCollection),
            'rightItemsIDs': ids(vos_collections.EnemyItemsCollection)}


class Drawing(TeamNames, BattleVisibility):
    """Putting ratings and flags on the battle surfaces."""

    def _publish(self):
        # Take back inline markers that were drawn before the view was ready.
        if views.html_team_names():
            self._take_back()
        """Give the battle view the markers and the teams' order, when changed.

        Read the current roster so hot reload works, keeping the client's
        latest order. Unchanged presentations stay cached by account id.
        """
        view = views.battle_view()
        arena = _arena() if view is not None or self._roster_props else None
        if view is None and arena is not None: return
        if arena is None:
            self._presentations.clear()
            self._presentation_arena = None
            self._order = {'leftItemsIDs': [], 'rightItemsIDs': []}
            self._received = set()
            self._roster_props = {}
            self._published = None
            self._wg_mode = _UNASKED
            self._said_tanks = False
            return
        if self._presentation_arena is not arena:
            self._presentations.clear()
            self._presentation_arena = arena
        self._markers = {}
        self._drew_tank = 0
        shows = modes.team_filter(self._settings)
        color_names = (self._settings['enabled'] and
                       self._settings['colorNamesByWnx'])
        color_clan_tags = (self._settings['enabled'] and
                           self._settings['colorClanTagsByWnx'])
        color_vehicles = (self._settings['enabled'] and
                          self._settings['colorVehiclesByWnx'])
        show_badges = (self._settings['enabled'] and self._settings['showWnxBadges'])
        show_long_rating = (self._settings['enabled'] and self._settings.shows('battle'))
        for vInfo in arena.getVehiclesInfoIterator():
            if vInfo.isObserver():
                continue
            player = getattr(vInfo, 'player', None)
            account_id = getattr(player, 'accountDBID', None)
            flags, badge, color, clan_tag, name, fake_name = self._marker(
                account_id, tank_of(vInfo),
                getattr(player, 'clanAbbrev', None),
                getattr(player, 'name', None), getattr(player, 'fakeName', None),
                team_shown=shows(vInfo.team))
            row, long_badge = ({}, '')
            if account_id and shows(vInfo.team):
                row, long_badge = self._presentations.get(account_id,
                    self._lookup.get(PLAYERS, account_id), self._settings, self._badges,
                    show_long_rating, self._long_wnx_badge)
            if flags or badge or color or long_badge or self._settings['enabled']:
                marker = icon_markers(flags, badge)
                marker.extend([color or '', clan_tag if color else '',
                               name if color else '', fake_name if color else ''])
                marker.extend([long_badge, markup_width(long_badge)])
                marker.extend([row.get('bandColor') or '',
                               str(row['wnx']) if row.get('wnxAvailable') else '',
                               row.get('winrate') or '', row.get('battles') or ''])
                marker.extend(self._roster_props.get(vInfo.vehicleID, [''] * 6))
                self._markers[vInfo.vehicleID] = marker
        if len(self._received) < len(self._order):
            for key, ids in _default_order(arena).items():
                if key not in self._received:
                    self._order[key] = ids
        state = (marker_text(self._markers),
                 ','.join(str(i) for i in self._order['leftItemsIDs']),
                 ','.join(str(i) for i in self._order['rightItemsIDs']))
        held = self.alt is not None and self.alt.down
        panel_badges_visible = held
        hidden = tuple(self._settings.alt_only(surface) and not held for surface in _ALT_SURFACES)
        state = state + hidden + (color_names, color_clan_tags, color_vehicles, show_badges,
                                  panel_badges_visible, self._settings['enabled'], self._settings.shows('battle'))
        from unicum.settings.wnx import flash_options
        state += (flash_options(self._settings),)
        if self._published is not None and self._published[0] is view and self._published[1] == state:
            return
        first = self._published is None
        count = len(self._markers)
        if count != getattr(self, '_probed', None):
            self._probed = count
            first = True
        if self._drew_tank and not self._said_tanks:
            self._said_tanks = True
            _logger.info('Alt: %d row(s) on the tank they brought', self._drew_tank)
        if first:
            # One line per battle, saying what actually left Python. Without it
            # a Tab screen that draws nothing is indistinguishable from a Tab
            # screen that was never sent anything, and both look like silence
            # in the log. Cheap: it runs once per view, not per frame.
            # `ready` is the one that matters: a view whose window never
            # reaches LOADED never runs configUI, so it never searches the
            # display tree and never draws anything -- no error, no drawing.
            _logger.info('battle view: %d marker(s), %d left, %d right, '
                         'hidden panel/tab/loading=%s, ready=%s, status=%s',
                         len(self._markers),
                         len(self._order['leftItemsIDs']),
                         len(self._order['rightItemsIDs']),
                         '/'.join('1' if h else '0' for h in hidden),
                         views.BATTLE.ready(),
                         [getattr(w, 'windowStatus', '?') for w in views.BATTLE.windows()])
        before = self._published[1][3:6] if not first else None
        self._published = (view, state)
        try:
            view.markersText, view.leftIds, view.rightIds = state[:3]
        except Exception:
            _logger.exception('could not give the battle view its markers')
            return
        try:
            view.panelHidden, view.tabHidden, view.loadingHidden = hidden
        except Exception:
            # A view whose class predates the properties, until the next battle.
            _logger.debug('the battle view has no hidden surfaces yet', exc_info=True)
        try:
            view.colorNamesByWnx = color_names
            view.colorClanTagsByWnx = color_clan_tags
            view.colorVehiclesByWnx = color_vehicles
            view.showWnxBadges = show_badges
            view.panelWnxBadgesVisible = panel_badges_visible
            view.rosterRedesignEnabled = self._settings['enabled']
            view.rosterStatsEnabled = self._settings.shows('battle')
            view.rosterOptions = state[-1]
        except Exception:
            _logger.debug('the battle view has no WNX text colour settings yet', exc_info=True)
        if first or hidden != before:
            # Names drawn before the view loaded carry the markers after them,
            # and a team average only exists in the name, so Alt changing what
            # a screen shows is what asks for one to be put there or dropped
            # (see _mark_teams).
            self._redraw()

    def _mark(self, component, vInfoVO):
        data = component.get()
        player = getattr(vInfoVO, 'player', None)
        team_shown = modes.team_filter(self._settings)(getattr(vInfoVO, 'team', None))
        flags, badge, color, clan_tag, name, fake_name = self._marker(
            getattr(player, 'accountDBID', None), tank_of(vInfoVO),
            getattr(player, 'clanAbbrev', None),
            getattr(player, 'name', None), getattr(player, 'fakeName', None),
            team_shown=team_shown)
        if not getattr(self, '_probed_mark', False):
            self._probed_mark = True
            _logger.info('vehicle data: drawing=%s, flags=%d chars, badge=%d chars, '
                         'data is dict=%s, region before=%r',
                         views.html_team_names(), len(flags or ''), len(badge or ''),
                         isinstance(data, dict),
                         (data.get('region') if isinstance(data, dict) else None))
        vehicle_id = getattr(vInfoVO, 'vehicleID', None)
        if vehicle_id:
            self._roster_props[vehicle_id] = native_name_fields(data)
        # Beside the vehicle icon instead, drawn by the battle view.
        if views.html_team_names():
            self._inline.discard(vehicle_id)
            self._take_back()
            return
        # Left untouched without a marker, so a None stays None.
        if (flags or badge) and team_shown and isinstance(data, dict):
            data['region'] = (data.get('region') or '') + flags + badge
            if vehicle_id:
                self._inline.add(vehicle_id)

    def _tank_mode(self):
        """The mode a tank's record is read over in this battle, or None.

        None where Wargaming publishes nothing per vehicle -- Frontline,
        Onslaught, Steel Hunter -- in which case no pair is ever asked for and
        no row ever changes.

        Held for the battle rather than read per row: it cannot change inside
        one, and this is asked once per player per pass. `_publish` clears it
        with the rest of the between-battles state.
        """
        if self._wg_mode is _UNASKED:
            self._wg_mode = modes.current_wg_mode()
        return self._wg_mode

    def _on_tank(self):
        """Whether the battle rows are showing the tank rather than the career.

        The surface's `figures` choice says which of the two a row rests on
        and Alt shows the other, so the key is a glance at the figure not
        currently drawn rather than the only road to one of them. Holding a
        key to read a number is fine for a second opinion and no way to read
        the number you came for. Under 'career' the key swaps nothing, which
        is the choice that also asks the site for nothing.

        One answer for the three surfaces, because they are drawn from one
        string of markers: the panel, the Tab screen and the loading screen
        are shown and hidden apart but read the same figures. Alt can swap
        only where at least one of them shows without it; where all three
        wait, the key is spent on revealing and the rows arrive as they rest.
        """
        at_rest = self._settings.rests_on_tank('battle')
        if self.alt is None or not self.alt.down:
            return at_rest
        if not self._settings.swaps_figures('battle'):
            return at_rest
        if not any(not self._settings.alt_only(surface) for surface in _ALT_SURFACES):
            return at_rest
        return not at_rest

    def _marker(self, account_id, tank_id=None, clan_tag=None, player_name=None,
                fake_name=None, team_shown=True):
        """(flags markup, rating badge markup, WNX colour, clan tag) for one player.

        Holding Alt puts the row on the tank this player brought, in this
        mode, instead of their career. A swap rather than a second group of
        pills: the players panel column is the narrowest place these numbers
        have to fit, and two ratings side by side in it read as one number
        measured twice rather than two tanks' worth of truth.
        """
        if not account_id:
            return '', '', None, clan_tag, player_name, fake_name
        colors_enabled = (self._settings['enabled'] and
                          (self._settings['colorNamesByWnx'] or
                           self._settings['colorClanTagsByWnx'] or
                           self._settings['colorVehiclesByWnx']))
        show_badges = (team_shown and self._settings.shows('battle') and
                       self._settings['showWnxBadges'])
        show_flags = team_shown and self._settings.shows_flags('battle')
        show_long_rating = (team_shown and self._settings['enabled'] and
                            self._settings.shows('battle'))
        if not show_badges and not show_flags and not colors_enabled and not show_long_rating:
            return '', '', None, clan_tag, player_name, fake_name
        # An old answer is still drawn while a fresh one is fetched.
        if self._lookup.needs_fetch(PLAYERS, account_id):
            self._request(account_id)
        entry = self._lookup.get(PLAYERS, account_id)
        color = self._wnx_color(entry) if colors_enabled else None
        if not clan_tag and entry is not None and isinstance(entry.clan, dict):
            clan_tag = entry.clan.get('tag')
        if entry is not None and not player_name:
            player_name = entry.name
        if not team_shown or not self._settings.shows('battle'):
            return '', '', color, clan_tag, player_name, fake_name
        flags = ''
        if show_flags:
            flags = self._textures.markup(entry, self._settings['maxFlags'])
        if not show_badges:
            return flags, '', color, clan_tag, player_name, fake_name
        mode = (self._tank_mode()
                if tank_id and self._settings.wants_vehicle('battle') else None)
        if mode is not None:
            # Asked for as the battle loads, beside the roster, and not on the
            # first press. Waiting for the press was the cheaper of the two and
            # it put the whole wait where it hurts: a site answering in twenty
            # or thirty seconds -- measured, and timing out at the client's
            # thirty more often than not -- turns a key held for a moment into
            # a key held for nothing.
            if self._lookup.needs_vehicle(account_id, tank_id, mode):
                self._request_vehicle(account_id, tank_id, mode)
            if self._on_tank():
                record = self._lookup.vehicle(account_id, tank_id, mode)
                drawn = self._badges.vehicle(record, self._settings, 'battle')
                if drawn:
                    self._drew_tank += 1
                # Nothing in hand, or nothing stored about this tank: the
                # career rating in plain grey instead of an empty column. A
                # blank row answers the question with silence, and silence is
                # indistinguishable from the mod being broken -- which is
                # exactly how the first evening of this read.
                return (flags, drawn or self._badges.plain(entry, self._settings, 'battle'),
                        color, clan_tag, player_name, fake_name)
        # Compact: this one dict feeds the players panel, whose column is the
        # narrowest place any of these numbers has to fit.
        return (flags, (self._badges.rating(entry, self._settings, 'battle')
                        + self._badges.extras(entry, self._settings, 'battle', compact=True)),
                color, clan_tag, player_name, fake_name)

    def _wnx_color(self, entry):
        """Use the cached career WNX and the scale's vivid text colour."""
        if entry is None:
            return None
        value = entry.rating('wnx', self._settings.window_of('wnx'))
        return self._badges.text_color('wnx', value)

    def _long_wnx_badge(self, entry):
        """The long panel's single pill, using the original WNX scale."""
        if entry is None:
            return ''
        value = entry.rating('wnx', self._settings.window_of('wnx'))
        if value is None:
            return ''
        return self._badges.markup('wnx', value) or '%d' % round(value)

    def _redraw(self):
        """Resend the arena description, which is what carries a team average.

        **Deliberately NOT `invalidateArenaInfo`.** That one resends the arena
        description AND the whole vehicles collection, and the second half is
        destructive to other mods: `invalidateVehiclesInfo` / `-Stats` push a
        new data provider into the players panel's lists, which re-binds every
        item renderer. Mods that graft their own Flash fields onto those
        renderers -- a spotted indicator, a hit-point label -- lose them, and
        since they build those once and never listen for an invalidation, they
        never come back. Holding Alt once showed everything, letting go took
        their labels away for the rest of the battle.

        Nothing we draw needs the vehicles resent. The players' notes are
        hidden by the view itself through `panelHidden` and friends; only a
        team average has to be written into the client's own team name field,
        and `__setArenaDescription` is exactly the half that resends it. It
        calls `as_setArenaInfoS`, which this mod already wraps, so the average
        is put back by the same path as always.

        Falls back to the whole invalidation on a client that has renamed the
        method: a team average that costs another mod its labels is still
        better than one that never appears, and the fallback is visible in the
        log rather than silent.
        """
        for controller in list(self._controllers):
            try:
                describe = getattr(controller, _ARENA_DESCRIPTION, None)
                if describe is not None:
                    describe()
                else:
                    _logger.info('no %s on this client, falling back to the '
                                 'full invalidation', _ARENA_DESCRIPTION)
                    controller.invalidateArenaInfo()
            except Exception:
                _logger.exception('could not redraw the battle statistics')
