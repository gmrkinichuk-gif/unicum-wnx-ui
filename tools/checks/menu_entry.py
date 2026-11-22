"""The paused menu registration must not affect settings or other mods."""
import json
import os
import sys
import types

from checks.common import check


def run(workdir):
    from unicum import mods_list
    from unicum.runtime.session import Session
    from unicum.settings import Settings
    from unicum.settings_tab import SettingsTab
    from unicum.tracker.controller import Controller

    class MenuApi(object):
        def __init__(self):
            self.items = {'third.party': object(), 'modsSettingsApi': object()}
            self.calls = []

        def addModification(self, **kwargs):
            self.calls.append(('add', kwargs))

        def removeModification(self, key):
            self.calls.append(('remove', key))

    name = 'gui.modsListApi'
    api = MenuApi()
    module = types.ModuleType(name)
    module.g_modsListApi = api
    held_module = sys.modules.get(name)
    held_session, held_time = mods_list._session, mods_list._last_open
    held_openers = (mods_list._open_aslain, mods_list._open_izeberg,
                    mods_list._open_settings_entry, mods_list._open_native)
    session, next_session = Session(41), Session(42)
    original_items = dict(api.items)
    sys.modules[name] = module
    try:
        menu = mods_list.install(session)
        mods_list.install(session)
        check('the public installer registers no standalone menu entry',
              menu is None and not api.calls and api.items == original_items)
        check('pausing registration adds no timer, patch or subscription',
              not session._callbacks and not session._patches and not session._subscriptions)
        check('repeated navigation installation owns exactly one teardown', len(session._closers) == 1)

        store = os.path.join(workdir, 'menu-disabled-settings.json')
        settings = Settings(session, store=store)
        notifications = []
        settings.on_change(lambda: notifications.append(settings['wnxUI']['panel']['stripe']))
        tab = SettingsTab(session, settings)

        class Flash(object):
            output = u'wnx_panel_stripe\tc\t0'

            def takeSettingsTabOut(self):
                value, self.output = self.output, ''
                return value

        tab._take(Flash())
        check('native Apply immediately notifies live readers with the menu disabled',
              settings['wnxUI']['panel']['stripe'] is False and notifications == [False])
        with open(store, 'rb') as handle:
            check('native Apply still writes the configuration',
                  json.load(handle)['wnxUI']['panel']['stripe'] is False)
        check('saved native settings survive a new Settings instance',
              Settings(next_session, store=store)['wnxUI']['panel']['stripe'] is False)
        check('native Apply does not register or remove any other menu item',
              not api.calls and api.items == original_items)

        controller = Controller.__new__(Controller)
        controller.menu, controller.settings = menu, settings
        controller.tracker = type('Tracker', (object,), {'account': '42'})()
        controller._action({'kind': 'opened'}, None)
        check('Tracker opening retains account-card settings navigation', mods_list._session is session)

        opened = []
        mods_list._last_open = [0]
        mods_list._open_aslain = lambda: opened.append('aslain') or True
        mods_list._open_izeberg = lambda: opened.append('izeberg') or True
        mods_list._open_settings_entry = lambda: opened.append('api-entry') or True
        mods_list._open_native = lambda: opened.append('native') or True
        mods_list.open_now()
        check('existing optional window routing retains its original priority', opened == ['aslain'])
        mods_list.open_settings()
        mods_list.open_settings()
        check('existing quick actions keep one gated Session-owned callback', len(session._callbacks) == 1)

        mods_list.install(next_session)
        session.close()
        check('old teardown cannot erase the newer navigation session', mods_list._session is next_session)
        check('teardown cancels delayed navigation without touching other mods',
              not session._callbacks and not api.calls and api.items == original_items)
        next_session.close()
        check('final teardown releases navigation without menu API mutations',
              mods_list._session is None and not api.calls and api.items == original_items)
    finally:
        session.close()
        next_session.close()
        mods_list._session, mods_list._last_open = held_session, held_time
        (mods_list._open_aslain, mods_list._open_izeberg,
         mods_list._open_settings_entry, mods_list._open_native) = held_openers
        if held_module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = held_module
