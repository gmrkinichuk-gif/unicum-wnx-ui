"""The window itself: registering it, drawing it, and reading it back.

The only part here that touches the client. Everything the page says is in
`labels`, everything it looks like is in `page`, and everything it means is
in `codec`.
"""
from __future__ import absolute_import

import json
import logging

from unicum.settings_window.codec import apply_window, read_native, to_window
from unicum.settings_window.labels import (linked_notice, CONNECT_VAR,
                                           DISCORD_URL, DISCORD_VAR, LINKAGE,
                                           LINKS, RESET_VAR, SOURCE_URL,
                                           SOURCE_VAR, SUPPORT_VAR)
from unicum.settings_window.page import (channel_label, garage_preview_lines,
                                         native_page, preview_lines, template)
from unicum.settings_window.localize import text as translated

_logger = logging.getLogger('unicum.settings_window.window')


def api_instance(api):
    """1.7.1 exports the internal API directly; older builds wrapped it."""
    if hasattr(api, 'onSettingsChanged') and hasattr(api, 'onButtonClicked'):
        return api
    return getattr(api, '_ModsSettingsApi__instance', None)

def reset_defaults(settings):
    """Every setting back to its default, and a system message saying so."""
    from unicum.settings import DEFAULTS
    language = settings['settingsLanguage']
    settings.update(json.loads(json.dumps(DEFAULTS)))
    _logger.info('the settings were put back to their defaults')
    try:
        from gui import SystemMessages
        from gui.shared.notifications import NotificationPriorityLevel
        SystemMessages.pushMessage(translated('unicum.gg: the settings are back to their defaults.', language),
                                   type=SystemMessages.SM_TYPE.Information,
                                   priority=NotificationPriorityLevel.MEDIUM)
    except Exception:
        _logger.debug('could not say that the settings were reset', exc_info=True)

def handle_button(var, settings, content, session=None):
    """What a button of either page does, apart from Twitch's Connect."""
    if var == RESET_VAR:
        confirm_reset(settings, session)
        return True
    return False


def confirm_reset(settings, session):
    """Use the client's confirmation dialog; never reset after teardown."""
    try:
        from gui import DialogsInterface
        from gui.Scaleform.daapi.view.dialogs import SimpleDialogMeta, ConfirmDialogButtons

        def answered(confirmed):
            if confirmed and session is not None and session.alive:
                reset_defaults(settings)

        language = settings['settingsLanguage']
        DialogsInterface.showDialog(SimpleDialogMeta(
            translated('Reset unicum.gg settings?', language),
            translated('Restore all unicum.gg options to their defaults and save them?', language),
            ConfirmDialogButtons(translated('Reset', language), translated('Cancel', language))), answered)
    except Exception:
        _logger.exception('could not show the reset confirmation; settings unchanged')

class SettingsWindow(object):


    def __init__(self, session, settings, link=None):
        self._session = session
        self._settings = settings
        self._link = link
        self._chat = None
        # (channel followed, Twitch chat writable, game linked, account name,
        # card shown, supports the site, loadouts hidden, battles hidden,
        # the drawn battle rows, the drawn garage row) as the page shows them. It has to match what `_register` unpacks and
        # what `_check_state` builds: `install` registers off this one, before
        # the link has answered anything. A field added to two of the three
        # and not to the seed took the whole mod down at every start.
        self._state = (u'', False, False, None, True, False, False, None, (), ())
        self._alive = True
        self._api = None
        # (badges, flag textures, settings) once the mod has built them.
        self._drawing = None

    def install(self):
        try:
            from gui.modsSettingsApi import g_modsSettingsApi
        except ImportError:
            _logger.info('modsSettingsApi not installed; use the native unicum.gg settings tab')
            return
        self._api = g_modsSettingsApi
        self._session.on_close(self._remove)
        self._register()
        self._settings.on_change(self._on_settings)
        _logger.info('registered in modsSettingsApi as %s', LINKAGE)

    def follow_badges(self, badges, textures):
        """Hand over what the preview draws with, once the mod has built it.

        Separate from the constructor because the window is installed before
        the badges exist: it is one of the first things up, so that a client
        that fails later still has somewhere to turn the mod off.

        Guarded like `follow_twitch`: without modsSettingsApi there is no
        page to put a preview on, and `_check_state` would reach for an API
        that was never found.
        """
        self._drawing = (badges, textures, self._settings)
        if self._api is not None:
            self._check_state()

    def follow_twitch(self, chat):
        """Show the channel `chat` follows, and the account link, as they change."""
        self._chat = chat
        if self._api is not None:
            self._session.repeat(2.0, self._check_state)

    def _check_state(self):
        link = self._link
        linked = bool(link is not None and link.secret)
        state = (self._chat.channel if self._chat is not None else u'',
                 linked and link.twitch == 'ready', linked, link.name if linked else None,
                 self._card_shown(), self._supporter(), self._hidden(),
                 self._battles_hidden(), tuple(preview_lines(self._drawing)),
                 tuple(garage_preview_lines(self._drawing)))
        if state == self._state:
            return
        self._state = state
        # A new template replaces the page; its callbacks are added again, so
        # the ones already on the API's events come off first.
        self._unregister()
        self._register()

    def _card_shown(self):
        return not (self._link is not None and self._link.card_hidden)

    def _supporter(self):
        return bool(self._link is not None and self._link.supporter)

    def _hidden(self):
        return bool(self._link is not None and self._link.loadouts_hidden)

    def _battles_hidden(self):
        """None when no account is linked, the one case the box is left out."""
        if self._link is None or not self._link.secret:
            return None
        return bool(self._link.battles_hidden)

    def _register(self):
        (channel, writable, linked, name, card_shown, supporter, hidden,
         battles_hidden, _drawn, _garage_drawn) = self._state
        self._language = self._settings['settingsLanguage']
        described = template(self._settings.values(), channel, writable, card_shown,
                                                   supporter, hidden, battles_hidden,
                                                   drawing=self._drawing)
        from unicum import profile
        described = profile.api_page(described)
        values = profile.window_values(to_window(self._settings.values(), card_shown, hidden, battles_hidden))
        fields = [row['varName'] for column in ('column1', 'column2')
                  for row in described.get(column, []) if 'varName' in row]
        missing = sorted(set(fields) - set(values))
        if missing:
            raise ValueError('settings template has no value for: %s' % ', '.join(missing))
        self._api.setModTemplate(LINKAGE, described,
                                 self._on_window, self._on_button)
        # The API keeps its own copy of every value and sends it back as the
        # player's choice. For the card that copy can be stale (the card's
        # cross changes the truth without going through the window), and an
        # old "shown" coming back would undo the cross: so it is set to the
        # truth first.
        self._api.updateModSettings(LINKAGE, values)

    def _on_window(self, linkage, raw):
        if not self._alive or linkage != LINKAGE or not isinstance(raw, dict):
            return
        apply_window(raw, self._settings, self._link)

    def _on_button(self, linkage, var_name, value=None):
        if not self._alive or linkage != LINKAGE:
            return
        if handle_button(var_name, self._settings, 'mods-list', self._session):
            return


    def _on_settings(self):
        """Keep the window in step with a hand edit of settings.json."""
        # The API answers with onSettingsChanged, which lands in _on_window
        # and is read back as the player's choice, so every site-owned box
        # goes out at its truth. Left to their defaults, the two hiding boxes
        # went out unticked and that answer read as a player asking for what
        # they had hidden to be shown again.
        if not self._alive:
            return
        if self._language != self._settings['settingsLanguage']:
            self._unregister()
            self._register()
            return
        from unicum.profile import window_values
        self._api.updateModSettings(LINKAGE, window_values(to_window(self._settings.values(), self._card_shown(),
                                                       self._hidden(), self._battles_hidden())))

    def _remove(self):
        self._alive = False
        self._unregister()
        instance = api_instance(self._api)
        if instance is not None:
            instance.activeMods.discard(LINKAGE)
            instance.state.get('templates', {}).pop(LINKAGE, None)

    def _unregister(self):
        instance = api_instance(self._api)
        for name, handler in (('onSettingsChanged', self._on_window), ('onButtonClicked', self._on_button)):
            event = getattr(instance, name, None)
            try:
                event -= handler
            except Exception:
                _logger.debug('could not unregister %s', name, exc_info=True)
