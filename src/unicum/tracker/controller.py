"""Garage-only bridge to the existing lobby movie; no battle polling/rendering."""
import json
import logging
import time

from unicum import config, views
from unicum.tracker import visibility
from unicum.api.entry import PLAYERS
from unicum.settings_window import codec, labels, window
from unicum.tracker.expected import Expected
from unicum.tracker.formula import finite
from unicum.tracker.localize import labels as words, rating_message, translate
from unicum.tracker.options import MODES
from unicum.tracker.page import for_settings
from unicum.tracker.service import playing_replay
from unicum.tracker.state import snapshot

_logger = logging.getLogger('unicum.tracker.ui')


class Controller(object):
    def __init__(self, session, settings, tracker, lookup, scales, menu=None):
        self.session, self.settings, self.tracker = session, settings, tracker
        self.lookup, self.scales, self.menu = lookup, scales, menu
        self.expected = Expected(session)
        self._scheduled, self._published, self._flash = False, None, None
        self._reset_identity = None
        self._names = {}
        self._statistics_key, self._statistics = None, None
        self._error_at = 0
        self._escape_held = False
        self._save_pending, self._save_result = None, None

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
        visibility.subscribe(self.session, self._visibility_changed)
        self.start()

    def _visibility_changed(self, *args):
        if not visibility.unobstructed():
            self.hide()
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
        self._schedule(0.2)

    def _schedule(self, delay):
        if not self._scheduled:
            self._scheduled = True
            self.session.callback(delay, self._tick)

    def hide(self, *args):
        if self._flash is not None:
            try:
                self._flash.hideTracker()
            except Exception:
                _logger.debug('lobby tracker already gone', exc_info=True)
        self._published, self._flash, self._reset_identity = None, None, None
        self._escape_held = False
        self._save_pending, self._save_result = None, None

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
            self._statistics = snapshot(history.rows if history else (), options['count'], self.expected.table)
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
        state['loading'] = history is None
        if state['loading']:
            state['message'] = translate('Loading battle history...', language)
        elif state['reason'] == 'more_battles':
            label = ('Play {remaining} random battles to build statistics' if not state['progress']
                     else 'Play {remaining} more random battles')
            state['message'] = translate(label, language).format(remaining=state['count'] - state['progress'])
        else:
            state['message'] = rating_message(state['reason'], language)
        state['error'] = ''
        if history and history.error:
            state['error'] = translate('History recovered from a damaged file' if history.error == 'history_recovered'
                                       else 'History could not be saved', language)
            if history.pending or history.readonly:
                state['message'] = state['error']
        for row in state['bars']:
            tank = row['tankId']
            name, tier = self._tank(tank) if tank is not None else (translate('Unknown tank', language), None)
            row['tankName'] = name or '%s #%s' % (translate('Tank', language), tank)
            row['tier'] = tier
            row['color'] = self.scales.color('wnx', row['wnx']) or '#65717e'
        for row in state['bars'] + state['points']:
            row['message'] = rating_message(row['reason'], language)
            row['time'] = time.strftime('%d.%m %H:%M', time.localtime(row['startedAt']))
        state['categories'] = for_settings(self.settings.values(), self.expected)
        state['saveResult'] = self._save_result
        return state

    def _tick(self):
        self._scheduled = False
        try:
            from helpers import isPlayerAccount
        except ImportError:
            self.hide()
            return
        if playing_replay():
            self.hide()
            return
        if not isPlayerAccount():
            self.hide()
            self._schedule(1.0)
            return
        if not visibility.unobstructed():
            self.hide()
            self.start()
            return
        try:
            account = self.tracker.identify()
            if not account:
                self.hide()
            else:
                self.expected.refresh()
                if self.lookup.needs_fetch(PLAYERS, int(account)):
                    self.lookup.prefetch(players=[int(account)])
                flash = views.lobby_view()
                if flash is not None:
                    if flash is not self._flash:
                        self._published, self._flash = None, flash
                        self._save_pending, self._save_result = None, None
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
                _logger.exception('tracker UI update failed')
        self.start()

    def _action(self, action, flash):
        if action.get('account') is not None and (action.get('account') != self.tracker.account
                                                  or action.get('region') != config.REGION):
            return
        kind = action.get('kind')
        if kind == 'mode':
            mode = action.get('value')
            if mode in MODES:
                self.settings.update({'wnxTracker': {'mode': mode}})
        elif kind == 'position':
            self.settings.update({'wnxTracker': {'position': action.get('value')}})
        elif kind == 'apply':
            self._save_settings(action, flash)
        elif kind == 'opened':
            self._reset_identity = (config.REGION, self.tracker.account)
            self.settings.reload()
            if self.menu is not None:
                self.menu.retire()
        elif kind == 'button':
            var = action.get('var')
            if var == 'tracker_position':
                self.settings.update({'wnxTracker': {'position': None}})
                flash.resetTrackerPosition()
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

    def _save_settings(self, action, flash):
        request = action.get('request')
        if not isinstance(request, (int, long)) or isinstance(request, bool) or request <= 0:
            return
        account = self.tracker.account
        pending = (flash, account, request)
        self._save_pending = pending
        self._save_result = None

        def done(error, retry):
            if self._save_pending is pending and self.tracker.account == account:
                self._save_pending = None
                # Send this with the saved model so Apply never redraws
                # cleared draft fields against stale values.
                self._save_result = {'request': request, 'error': error, 'retry': retry}

        raw = action.get('values')
        if not isinstance(raw, dict):
            done('local', [])
            return
        try:
            codec.apply_window(raw, self.settings, None, done)
        except Exception:
            _logger.exception('could not apply tracker settings')
            done('local', [])


def install(session, settings, tracker, lookup, scales, menu=None):
    controller = Controller(session, settings, tracker, lookup, scales, menu)
    controller.install()
    return controller
