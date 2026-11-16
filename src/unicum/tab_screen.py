"""WNX ratings on the battle Tab screen, drawn in its page.

The Tab screen ("Team composition") is Coherent Gameface. Its python side,
`gui.impl.battle.battle_page.tab_view.TabView`, fills a model the page binds
with `data-bind-for="index, item:{{model.playerList.allies}}"`, and three
separate attempts to put a rating in that model have now been written,
confirmed present in the model by a probe, and NOT drawn on screen:

    tab probe:  name=u'szucsmester'  clan=u'BOBHU 1491'
    tab probe:  name=u'V0MIT0'       clan=u'HVZ 1226'

Both `userName` and `clanAbbrev`, two unrelated string properties, were in
the native model and neither appeared. Whatever the reason, that model is not
the road to this screen, so this module takes the other one: it runs a script
inside the page and writes into the DOM.

WHY THIS IS NOT THE SAME GRAFT AS THE RESULTS SCREEN

`battle_results.py` patches `_getChildComponents`, which is defined on
`ViewComponent`. `TabView` extends `ViewImpl`, which has no such method and
never calls one, so the same patch here would create a method nobody
invokes: a silent no-op, and exactly the kind of failure that has already
cost hours on this screen.

The road that works is `View.setChildView`, which `ViewImpl` does inherit,
and it is not a deduction. `gravity.scheduled_personal_reserves`, installed
in this game, does it on this view, and the client's own log says so on
every battle:

    [Glow] Parent view loaded: TabView.
    [Glow] Child attached to TabView with layout ID 19.
    [Glow][Gameface] Reconcile: ... cards=5, matched=0

`cards=5` is a `document.querySelectorAll` running in the battle Tab's page.

Everything else is borrowed: the `UnicumTankButton` layout, its loader and
the model shape are the ones the hangar and the results screen already use,
so there is no new resource to declare and no client restart to ask for.
"""
import functools
import json
import logging
import weakref
import zlib

from frameworks.wulf import ViewModel
from gui.impl.pub.view_component import ViewComponent

from unicum import extended_info, figures, resources
from unicum.api.entry import PLAYERS
from unicum.layouts import layout_id
from unicum.tank_button import FEATURE, LAYOUT, compose

_logger = logging.getLogger('unicum.tab_screen')

# The settings surface this screen reads for visibility and team averages.
# Player text always uses WNX and its site-served scale. Flags are deliberately
# not published on the Tab screen.
SURFACE = 'battle'
SCREEN = 'tab'

_MODULE = 'coui://gui/gameface/mods/unicum/TankButton/TankButton.js'
_SCRIPT = 'web/battle/tab_screen.js'
_STYLE = 'web/battle/tab_screen.css'
_CHECK_SECONDS = 1.0

# Where live models are kept across reloads of this package: on the host
# class, so a reimport finds the screens already open.
_REGISTRY = '_unicumTabModels'

# Property indexes; gf_mod_inject takes 0 with ModInjectModel.
_REVISION = 2
_SCRIPT_TEXT = 3
_STYLE_TEXT = 4
_DATA = 5


def _report(args):
    """Where the page's `api.report` lands.

    Reached through an eval of an import, never as a bound function: a view
    outlives a reload of this package, so a handler holding today's function
    would keep running yesterday's code. `tank_button` explains the same
    trick at length.
    """
    logging.getLogger('unicum.tab_screen').info('page: %s', args)


_ON_ITEM = functools.partial(
    eval, "__import__('unicum.tab_screen', None, None, ['_report'])._report(locals())", {})


# Keep these imports for callers of the previous Tab formatting helpers.
from unicum.roster import (wnx_data as _wnx_data,
                           battle_stats as _battle_stats)


class TabModel(ViewModel):
    __slots__ = ('onItemClick', )

    def __init__(self, properties=6, commands=1):
        super(TabModel, self).__init__(properties=properties, commands=commands)

    def _initialize(self):
        super(TabModel, self)._initialize()
        from openwg_gameface import gf_mod_inject
        gf_mod_inject(self, FEATURE, modules=[_MODULE])
        self._addBoolProperty('enabled', True)
        self._addNumberProperty('revision', 0)
        self._addStringProperty('script', '')
        self._addStringProperty('style', '')
        self._addStringProperty('data', '')
        self.onItemClick = self._addCommand('onItemClick')


class TabScreen(object):

    def __init__(self, session, lookup, flags, badges, scales, settings, alt):
        self._session = session
        self._lookup = lookup
        self._badges = badges
        self._scales = scales
        self._settings = settings
        self._alt = alt
        self._host = None
        self._layout = None
        self._stamps = None
        self._script = self._style = u''
        self._revision = 0
        self._last_probe = None
        self._published = weakref.WeakKeyDictionary()

    # ------------------------------------------------------------- installing

    def install(self):
        try:
            import openwg_gameface  # noqa: F401 -- the injector the model needs
        except ImportError:
            _logger.info('openwg_gameface not installed, no ratings on the Tab screen')
            return
        try:
            from gui.impl.battle.battle_page.tab_view import TabView
        except ImportError:
            _logger.info('no Tab view in this client, no ratings on that screen')
            return
        self._layout = layout_id(LAYOUT, FEATURE)
        if self._layout is None:
            _logger.info('%s not in the resource map yet, no ratings on the Tab screen', FEATURE)
            return
        self._host = TabView
        self._session.patch(TabView, '_onLoaded', self._wrap_loaded)
        self._check()
        self._session.repeat(_CHECK_SECONDS, self._check)
        self._settings.on_change(self._publish_all)
        if self._alt is not None:
            self._alt.on_change(self._publish_all)
        _logger.info('installed on TabView, layout %s', self._layout)

    def _wrap_loaded(self, original):

        def _onLoaded(view, *args, **kwargs):
            result = original(view, *args, **kwargs)
            try:
                self._attach(view)
            except Exception:
                # A Tab screen without ratings beats a Tab screen that fails.
                _logger.exception('could not attach to the Tab screen')
            return result

        return _onLoaded

    def _attach(self, view):
        """Graft our page onto this screen, once.

        `getChildView` first: `_onLoaded` can run more than once over the life
        of a view, and `setSubView` refuses a child that already has a parent
        with 'child %r can not be added', which would be the only sign.
        """
        if view.getChildView(self._layout) is not None:
            _logger.info('the Tab screen already carries our page')
            return
        child = ViewComponent(layoutID=self._layout, model=TabModel)
        model = child.getViewModel()
        model.onItemClick += _ON_ITEM
        view.setChildView(self._layout, child)
        self._models()[model] = True
        self._load_code(model)
        self._publish(model)
        _logger.info('attached our page to the Tab screen')

    def _models(self):
        models = getattr(self._host, _REGISTRY, None)
        if models is None:
            models = weakref.WeakKeyDictionary()
            setattr(self._host, _REGISTRY, models)
        return models

    # --------------------------------------------------------------- the code

    def _check(self):
        """New code when a source changes, and the data again: a rating may have landed."""
        stamps = tuple(resources.stamp(path) for path in (_SCRIPT, _STYLE))
        if stamps != self._stamps:
            self._stamps = stamps
            self._script = compose([('tab screen', resources.read(_SCRIPT).decode('utf-8'))])
            self._style = resources.read(_STYLE).decode('utf-8')
            self._revision = zlib.crc32((self._script + self._style).encode('utf-8')) & 0x3fffffff
            for model in list(self._models().keys()):
                self._load_code(model)
        self._publish_all()

    def _load_code(self, model):
        try:
            model._setString(_SCRIPT_TEXT, self._script)
            model._setString(_STYLE_TEXT, self._style)
            model._setNumber(_REVISION, self._revision)
            _logger.info('Tab code published: revision=%s script=%s css=%s',
                         self._revision, len(self._script), len(self._style))
        except Exception:
            _logger.exception('could not give the Tab screen its code')

    # --------------------------------------------------------------- the data

    def _roster(self):
        """[(the names a row may show, account id, on our team)] for this arena.

        The arena data PROVIDER, not the Tab view's own vehicle dict. That
        dict carries `accountDBID` 0 for a third of the rows -- measured,
        `tab: sources model=0L vehicle=4177952L panel=None` -- while the
        provider the players panel reads has a real id for the same vehicle.

        Both names are listed, the real one and an anonymised player's
        made-up one, so whichever the row shows finds the right account. The
        page keys on the name it draws and nothing else: the rows carry no
        identifier at all, no `data-test-id` and no materialised vehicle id.
        """
        found = []
        try:
            from helpers import dependency
            from skeletons.gui.battle_session import IBattleSessionProvider
            arena_dp = dependency.instance(IBattleSessionProvider).getArenaDP()
            if arena_dp is None:
                return found
            for info in arena_dp.getVehiclesInfoIterator():
                player = getattr(info, 'player', None)
                account_id = getattr(player, 'accountDBID', 0)
                if not account_id:
                    continue
                names = [name for name in (getattr(player, 'name', None),
                                           getattr(player, 'fakeName', None)) if name]
                if not names:
                    continue
                found.append((names, account_id, bool(arena_dp.isAllyTeam(info.team))))
        except Exception:
            _logger.debug('could not read the arena roster', exc_info=True)
        return found

    def _publish_all(self):
        for model in list(self._models().keys()):
            self._publish(model)

    def _publish(self, model):
        color_enabled = (self._settings['enabled'] and
                         (self._settings['colorNamesByWnx'] or
                          self._settings['colorClanTagsByWnx'] or
                          self._settings['colorVehiclesByWnx']))
        data = {'players': {}, 'averages': {'allies': None, 'enemies': None},
                'shown': False,
                'indicatorEnabled': False,
                'redesignEnabled': self._settings['enabled'],
                'colorNamesByWnx': self._settings['colorNamesByWnx'],
                'colorClanTagsByWnx': self._settings['colorClanTagsByWnx'],
                'colorVehiclesByWnx': self._settings['colorVehiclesByWnx']}
        # The same wait the players panel honours: a player who asked for
        # these numbers only while the extended info key is held gets them
        # only then, on this screen too.
        waiting = extended_info.waits(self._alt, self._settings, SCREEN)
        show_stats = self._settings.metric(SURFACE) is not None and not waiting
        data['shown'] = show_stats
        data['indicatorEnabled'] = show_stats or color_enabled
        if self._settings['enabled']:
            wanted = []
            values = {'allies': [], 'enemies': []}
            window = self._settings.window_of('wnx')
            for names, account_id, ally in self._roster():
                if self._lookup.needs_fetch(PLAYERS, account_id):
                    wanted.append(account_id)
                    for name in names:
                        data['players'][name] = {'wnxAvailable': False}
                entry = self._lookup.get(PLAYERS, account_id)
                value, rating_data = _wnx_data(entry, window, self._badges)
                color = rating_data.get('color') if rating_data is not None else None
                if value is not None:
                    values['allies' if ally else 'enemies'].append(value)
                player_data = dict(rating_data or {'wnxAvailable': False})
                if color is not None:
                    player_data['color'] = color
                    player_data['bandColor'] = rating_data.get('bandColor')
                if show_stats:
                    if value is not None:
                        player_data['wnx'] = int(round(value))
                    player_data.update(_battle_stats(entry, self._settings))
                for name in names:
                    data['players'][name] = player_data
            if show_stats and self._settings.shows_average(SURFACE):
                for side in ('allies', 'enemies'):
                    found = values[side]
                    if not found:
                        continue
                    mean = int(round(sum(found) / float(len(found))))
                    data['averages'][side] = figures.rating_pill(
                        self._badges, self._scales, 'wnx', mean)
            # Two requests, not one, and the reason is what each costs. The
            # roster answers in milliseconds off indexed player rows; the
            if wanted:
                self._lookup.prefetch(players=sorted(set(wanted)),
                                      on_ready=self._publish_all)
        probe = (len(data['players']), sum(1 for p in data['players'].values()
                  if p.get('wnxAvailable')), data['shown'])
        if probe != self._last_probe:
            self._last_probe = probe
            _logger.info('Tab data: aliases=%d WNX=%d shown=%s', *probe)
        text = json.dumps(data, sort_keys=True)
        if self._published.get(model) == text:
            return
        try:
            model._setString(_DATA, text)
            self._published[model] = text
        except Exception:
            _logger.debug('a Tab model gone', exc_info=True)


def install(session, lookup, flags, badges, scales, settings, alt):
    TabScreen(session, lookup, flags, badges, scales, settings, alt).install()
