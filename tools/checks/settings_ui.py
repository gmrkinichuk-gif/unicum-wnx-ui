"""Exercise the editable page/codec/store boundary and every WNX control."""
import json
import os
import sys
import types

from checks.common import check


def run(workdir):
    check_menu_fallback()
    from checks.menu_entry import run as check_menu_entry
    check_menu_entry(workdir)
    from unicum.runtime.session import Session
    from unicum.settings import Settings
    from unicum.settings import wnx
    from unicum.settings_window import codec, page
    from unicum.settings_window import localize
    from unicum.settings_window.wnx import FIELDS, var
    from unicum.settings_tab import SettingsTab

    session = Session(generation=0)
    path = os.path.join(workdir, 'settings-ui.json')
    settings = Settings(session, store=path)
    for surface in ('battle', 'battleResults', 'skirmishRoom'):
        settings.update({surface: {'average': False}})
    check('all independent team averages survive a full API round trip',
          all(codec.from_window(codec.to_window(settings.values()))[surface]['average'] is False
              for surface in ('battle', 'battleResults', 'skirmishRoom')))
    settings.update(codec.from_window({'settingsLanguage': 1}))
    ukrainian = page.native_page(settings.values())
    check('language changes are validated, saved and rendered in Ukrainian',
          settings['settingsLanguage'] == 'uk' and u'\u041c\u043e\u0432\u0430 \u043d\u0430\u043b\u0430\u0448\u0442\u0443\u0432\u0430\u043d\u044c' in ukrainian
          and 'WNX row background' not in ukrainian)
    check('language selection never changes protocol keys or numeric indices',
          'wnx_panel_duration' in ukrainian and codec.to_window(settings.values())['settingsLanguage'] == 1)
    check('language persists across a store restart and rejects invalid values',
          Settings(session, store=path)['settingsLanguage'] == 'uk'
          and __import__('unicum.settings', fromlist=['validate']).validate({'settingsLanguage': 'xx'})['settingsLanguage'] == 'en')
    check('English is unchanged and dynamic channel names are not translated',
          localize.text('Rating', 'en') == 'Rating'
          and localize.text('Channel: Some_Channel', 'uk').endswith('Some_Channel'))
    check('Ukrainian tooltips retain the native header/body protocol',
          localize.text('{HEADER}Reset{/HEADER}{BODY}Reset everything{/BODY}', 'uk').startswith('{HEADER}')
          and 'Reset everything' not in localize.text('{HEADER}Reset{/HEADER}{BODY}Reset everything{/BODY}', 'uk'))
    settings.update(codec.from_window({'settingsLanguage': 0}))
    native = [line.split('\t') for line in page.native_page(settings.values()).split('\n')]
    check('the native page exposes the master switch and Twitch channel input',
          any(row[:3] == ['checkbox', 'enabled', 'Enable unicum.gg'] for row in native)
          and any(row[:2] == ['input', 'twitchChannel'] for row in native))
    check('every WNX field is rendered exactly once in the native page',
          all(sum(1 for row in native if row[1] == var(surface, key)) == 1
              for surface, key, _, _ in FIELDS))
    for surface, key, _, choices in FIELDS:
        name = var(surface, key)
        for index, expected in enumerate(choices or (False, True)):
            raw = {name: index if choices else expected}
            settings.update(codec.from_window(raw))
            check('%s=%s is validated, saved and returned by the page' % (name, expected),
                  settings['wnxUI'][surface][key] == expected
                  and codec.to_window(settings.values())[name] == raw[name])
        settings.update({'wnxUI': {surface: {key: 'invalid'}}})
        check('%s rejects invalid stored values' % name,
              settings['wnxUI'][surface][key] == wnx.DEFAULTS[surface][key])
    check('malformed WNX subtrees and boolean numeric choices are rejected',
          wnx.validate({'panel': {'duration': True}, 'loading': []}) == wnx.DEFAULTS)
    check('invalid dropdown indices do not write settings',
          codec.from_window({'wnx_panel_duration': -1, 'wnx_tab_opacity': 99}) == {})
    settings.update({'unknown': {'future': 7}, 'battle': {'extension': 'keep'},
                     'wnxUI': {'panel': {'extension': 9}}})
    settings.update({'metric': 'wn8'})
    reopened = Settings(session, store=path)
    check('unknown keys survive validation, saving and restart at every level',
          reopened['unknown']['future'] == 7 and reopened['battle']['extension'] == 'keep'
          and reopened['wnxUI']['panel']['extension'] == 9)
    check('stored WNX options survive restart without changing the original metrics',
          reopened['wnxUI'] == settings['wnxUI'] and reopened['metric'] == 'wn8')
    check('Scaleform receives all loading/panel options as primitive fields',
          len(wnx.flash_options(settings).split(',')) == 12)

    class Flash(object):
        output = ''

        def takeSettingsTabOut(self):
            value, self.output = self.output, ''
            return value

    flash = Flash()
    tab = SettingsTab(session, settings)
    before = settings.values()
    flash.output = u'peek\twnx_panel_stripe\tc\t0'
    tab._take(flash)
    check('editing a native checkbox is only a draft', settings.values() == before and bool(tab._peek))
    flash.output = u'peek\t\t\t'
    tab._take(flash)
    check('Cancel clears drafts without saving', settings.values() == before and tab._peek == {})
    flash.output = u'wnx_panel_stripe\tc\t0\ntwitchChannel\ts\tSome_Channel\npeek\t\t\t'
    tab._take(flash)
    check('Apply/OK commit the real settings and normalize the channel',
          settings['wnxUI']['panel']['stripe'] is False and settings['twitch']['channel'] == 'some_channel')
    with open(path, 'rb') as handle:
        check('the committed changes are on disk', json.load(handle)['wnxUI']['panel']['stripe'] is False)
    from unicum.settings_window import window
    from unicum.settings_window.labels import RESET_VAR
    dialogs_name = 'gui.Scaleform.daapi.view.dialogs'
    held = sys.modules.get(dialogs_name)
    gui = sys.modules['gui']
    previous = getattr(gui, 'DialogsInterface', None)
    dialogs = types.ModuleType(dialogs_name)
    dialogs.SimpleDialogMeta = lambda *args: args
    dialogs.ConfirmDialogButtons = lambda submit, close: (submit, close)
    callbacks = []
    gui.DialogsInterface = type('Dialogs', (object,), {'showDialog': staticmethod(
        lambda meta, callback: callbacks.append(callback))})
    sys.modules[dialogs_name] = dialogs
    try:
        before = settings.values()
        window.handle_button(RESET_VAR, settings, 'test', session)
        check('Reset opens confirmation before writing', settings.values() == before and len(callbacks) == 1)
        callbacks.pop()(False)
        check('a cancelled Reset leaves all values intact', settings.values() == before)
        window.handle_button(RESET_VAR, settings, 'test', session)
        callbacks.pop()(True)
        check('confirmed Reset restores defaults and retains unknown extension keys',
              settings['wnxUI']['panel']['stripe'] is True and settings['unknown']['future'] == 7)
        settings.update({'enabled': False})
        window.handle_button(RESET_VAR, settings, 'test', session)
        session.close()
        callbacks.pop()(True)
        check('a delayed confirmation cannot write after teardown', settings['enabled'] is False)
    finally:
        if held is None:
            sys.modules.pop(dialogs_name, None)
        else:
            sys.modules[dialogs_name] = held
        if previous is None:
            delattr(gui, 'DialogsInterface')
        else:
            gui.DialogsInterface = previous


def check_menu_fallback():
    from unicum import mods_list, views
    from unicum.runtime.session import Session
    shared = sys.modules['gui.shared']
    name = 'gui.shared.event_dispatcher'
    held_module = sys.modules.get(name)
    held_attribute = getattr(shared, 'event_dispatcher', None)
    held_view, held_session = views.lobby_view, mods_list._session
    held_time = mods_list._last_open
    held_openers = [mods_list._open_aslain, mods_list._open_izeberg, mods_list._open_settings_entry]
    opened = []
    dispatcher = types.ModuleType(name)
    dispatcher.showSettingsWindow = lambda: opened.append('window')
    shared.event_dispatcher = dispatcher
    sys.modules[name] = dispatcher
    flash = type('Flash', (object,), {'openSettingsTab': lambda self: opened.append('tab')})()
    views.lobby_view = lambda: flash
    session = Session(generation=0)
    try:
        mods_list._session, mods_list._last_open = session, [0]
        mods_list._open_aslain = mods_list._open_izeberg = mods_list._open_settings_entry = lambda: False
        mods_list.open_now()
        check('without optional settings APIs the menu requests the native tab and one window',
              opened == ['tab', 'window'])
        mods_list.open_settings()
        mods_list.open_settings()
        check('repeated menu activation queues only one Session-owned callback', len(session._callbacks) == 1)
        session.close()
        check('teardown cancels the delayed menu open', not session._callbacks)
    finally:
        session.close()
        views.lobby_view, mods_list._session = held_view, held_session
        mods_list._last_open = held_time
        mods_list._open_aslain, mods_list._open_izeberg, mods_list._open_settings_entry = held_openers
        if held_module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = held_module
        if held_attribute is None:
            delattr(shared, 'event_dispatcher')
        else:
            shared.event_dispatcher = held_attribute
