"""Garage-only bridge to the existing lobby movie; no battle polling/rendering."""
import json
import logging
import time

from unicum import config, views
from unicum.api.entry import PLAYERS
from unicum.settings_window import codec, labels, window
from unicum.tracker.expected import Expected
from unicum.tracker.formula import finite
from unicum.tracker.localize import labels as words, translate
from unicum.tracker.options import MODES
from unicum.tracker.page import build
from unicum.tracker.service import playing_replay
from unicum.tracker.state import snapshot

_logger = logging.getLogger('unicum.tracker.ui')


class Controller(object):
    def __init__(self, session, settings, tracker, lookup, scales, tab, menu=None):
        self.session, self.settings, self.tracker = session, settings, tracker
        self.lookup, self.scales, self.tab, self.menu = lookup, scales, tab, menu
        self.expected = Expected(session)
        self._scheduled, self._published, self._flash = False, None, None
        self._reset_identity = None
        self._names = {}
        self._statistics_key, self._statistics = None, None
        self._error_at = 0
        self._escape_held = False

    def install(self):
        from PlayerEvents import g_playerEvents
        self.session.subscribe(g_playerEvents.onAccountShowGUI, self.start)
        self.session.subscribe(g_playerEvents.onAvatarBecomePlayer, self.hide)
        # A logoff must close the draft before the next account can use it.
        event = getattr(g_playerEvents, 'onAccountBecomeNonPlayer', None)
        if event is not None:
            self.session.subscribe(event, self.hide)
        self.session.on_close(self.hide)
        try:
            import game
            self.session.patch(game, 'handleKeyEvent', self._wrap_key)
        except (ImportError, AttributeError):
            _logger.debug('game key dispatcher unavailable')
        self.start()

    def _wrap_key(self, original):
        def handleKeyEvent(event):
            try:
                if self._take_escape(event):
                    return True
            except Exception:
                _logger.debug('tracker could not handle Escape', exc_info=True)
            return original(event)
        return handleKeyEvent

    def _take_escape(self, event):
        # InputHandler only emits an Event. Returning from its listener does
        # not prevent game.handleKeyEvent from handing Escape on to GUI.
        if not self.session.alive or (self._flash is None and not self._escape_held):
            return False
        import Keys
        from helpers import isPlayerAccount
        if event.key != Keys.KEY_ESCAPE or not isPlayerAccount():
            return False
        if not event.isKeyDown():
            consumed, self._escape_held = self._escape_held, False
            return consumed
        if event.isRepeatedEvent():
            return self._escape_held
        self._escape_held = self._flash is not None and bool(self._flash.escapeTrackerSettings())
        return self._escape_held

    def start(self, *args):
        if not self._scheduled:
            self._scheduled = True
            self.session.callback(0.2, self._tick)

    def hide(self, *args):
        if self._flash is not None:
            try:
                self._flash.hideTracker()
            except Exception:
                _logger.debug('lobby tracker already gone', exc_info=True)
        self._published, self._flash, self._reset_identity = None, None, None
        self._escape_held = False

    def _tank(self, tank_id):
        if tank_id not in self._names:
            try:
                from items import vehicles
                vehicle = vehicles.getVehicleType(tank_id)
                self._names[tank_id] = (vehicle.userString, vehicle.level)
            except Exception:
                return None, None
        return self._names[tank_id]

    def _model(self):
        account = self.tracker.account
        options = self.settings['wnxTracker']
        language = self.settings['settingsLanguage']
        history = self.tracker.history
        key = (account, self.tracker.revision, options['count'], self.expected.version)
        if key != self._statistics_key:
            self._statistics = snapshot(history.rows, options['count'], self.expected.table)
            self._statistics_key = key
        state = dict(self._statistics)
        entry = self.lookup.get(PLAYERS, int(account))
        total = entry.rating('wnx', 'total') if entry is not None else None
        total = total if finite(total) else None
        score = total if options['mode'] == 'Mini' else state['wnx']
        color = self.scales.color('wnx', score if score is not None else total) or '#65717e'
        state.update(mode=options['mode'], opacity=options['opacity'], position=options['position'],
                     total=total, color=color, labels=words(language), account=account,
                     region=config.REGION, language=language)
        if state['reason'] == 'more_battles':
            label = ('Play {remaining} random battles to build statistics' if not state['progress']
                     else 'Play {remaining} more random battles')
            state['message'] = translate(label, language).format(remaining=state['count'] - state['progress'])
        else:
            state['message'] = translate('WNX data is unavailable for some battles', language)
        state['error'] = ''
        if history.error:
            state['error'] = translate('History recovered from a damaged file' if history.error == 'history_recovered'
                                       else 'History could not be saved', language)
            if history.pending or history.readonly:
                state['message'] = state['error']
        for row in state['bars']:
            name, tier = self._tank(row['tankId'])
            row['tankName'] = name or '%s #%s' % (translate('Tank', language), row['tankId'])
            row['tier'] = tier
            row['color'] = self.scales.color('wnx', row['wnx']) or '#65717e'
            row['time'] = time.strftime('%d.%m %H:%M', time.localtime(row['startedAt']))
        for row in state['points']:
            row['time'] = time.strftime('%d.%m %H:%M', time.localtime(row['startedAt']))
        state['categories'] = build(self.tab._page(), self.settings.values(), self.expected)
        return state

    def _tick(self):
        self._scheduled = False
        try:
            from helpers import isPlayerAccount
        except ImportError:
            self.hide()
            return
        if not isPlayerAccount() or playing_replay():
            self.hide()
            return
        try:
            account = self.tracker.identify()
            if account:
                self.expected.refresh()
                if self.lookup.needs_fetch(PLAYERS, int(account)):
                    self.lookup.prefetch(players=[int(account)])
                flash = views.lobby_view()
                if flash is not None:
                    if flash is not self._flash:
                        self._published, self._flash = None, flash
                    # Actions are drained before publishing a new saved-settings model.
                    text = flash.takeTrackerOut()
                    for line in (text or '').split('\n'):
                        if line:
                            self._action(json.loads(line), flash)
                    model = json.dumps(self._model(), ensure_ascii=True, allow_nan=False, separators=(',', ':'))
                    if model != self._published:
                        flash.setTrackerState(model)
                        self._published = model
        except Exception:
            if time.time() >= self._error_at:
                self._error_at = time.time() + 60
                _logger.exception('tracker UI update failed; native settings remain available')
        self.start()

    def _action(self, action, flash):
        if action.get('account') is not None and (action.get('account') != self.tracker.account
                                                  or action.get('region') != config.REGION):
            return
        kind = action.get('kind')
        if kind == 'mode':
            current = self.settings['wnxTracker']['mode']
            step = -1 if action.get('step') == -1 else 1
            self.settings.update({'wnxTracker': {'mode': MODES[(MODES.index(current) + step) % len(MODES)]}})
        elif kind == 'position':
            self.settings.update({'wnxTracker': {'position': action.get('value')}})
        elif kind == 'apply':
            raw = action.get('values')
            if isinstance(raw, dict):
                codec.apply_window(raw, self.settings, self.tab._link)
        elif kind == 'opened':
            self._reset_identity = (config.REGION, self.tracker.account)
            if self.menu is not None:
                self.menu.retire()
        elif kind == 'button':
            var = action.get('var')
            if var == 'tracker_position':
                self.settings.update({'wnxTracker': {'position': None}})
                flash.resetTrackerPosition()
            elif var == labels.CONNECT_VAR and self.tab._link is not None:
                self.tab._link.connect(labels.linked_notice)
            elif var not in ('tracker_reset', labels.RESET_VAR):
                window.handle_button(var, self.settings, 'session-tracker', self.session)
        elif kind == 'confirmed':
            if action.get('var') == 'tracker_reset' and self._reset_identity:
                self.tracker.reset(self._reset_identity)
            elif action.get('var') == labels.RESET_VAR:
                window.reset_defaults(self.settings)
                flash.discardTrackerDraft()
        elif kind == 'log':
            _logger.info('Scaleform tracker: %s', action.get('message', '')[:400])


def install(session, settings, tracker, lookup, scales, tab, menu=None):
    controller = Controller(session, settings, tracker, lookup, scales, tab, menu)
    controller.install()
    return controller
