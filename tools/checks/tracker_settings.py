"""Exercise saved settings through the same request/model cycle as GFx."""
import json
import os

from checks.common import check


def run(workdir):
    from unicum import config, views
    from unicum.game_link import GameLink
    from unicum.runtime import files
    from unicum.runtime.session import Session
    from unicum.settings import Settings
    from unicum.settings_tab import SettingsTab
    from unicum.settings_window.labels import CARD_VAR, HIDE_BATTLES_VAR, HIDE_VAR
    from unicum.tracker.controller import Controller
    from unicum.tracker.writer import HistoryView
    import helpers

    class Flash(object):
        def __init__(self):
            self.actions = []
            self.models = []

        def takeTrackerOut(self):
            text = '\n'.join(json.dumps(action) for action in self.actions)
            del self.actions[:]
            return text

        def setTrackerState(self, text):
            self.models.append(json.loads(text))

        def hideTracker(self):
            pass

    class Tracker(object):
        account, revision = '42', 0
        history = HistoryView((), None, False, False)

        def identify(self):
            return self.account

    class Lookup(object):
        def needs_fetch(self, *args): return False
        def get(self, *args): return None

    class Scales(object):
        def color(self, *args): return None

    class Site(object):
        def __init__(self):
            self.requests = {}

        def fetch(self, url, done, post_data, **kwargs):
            for key, value in json.loads(post_data).items():
                self.requests[key] = (value, done)

        def answer(self, key, code):
            _, done = self.requests.pop(key)
            done(type('Response', (), {'responseCode': code})())

    def state_value(model, var):
        return next(row['value'] for tab in model['categories'] for row in tab['rows']
                    if row.get('var') == var)

    session, site, flash = Session(0), Site(), Flash()
    settings_path = os.path.join(workdir, 'tracker-save-settings.json')
    card_path = os.path.join(workdir, 'tracker-save-account.json')
    settings = Settings(session, settings_path)
    link = GameLink(site, store=card_path)
    link._account = '42'
    link._links['42'] = 'a' * 64
    link.twitch, link.supporter = 'ready', True
    tab = SettingsTab(session, settings, link)
    controller = Controller(session, settings, Tracker(), Lookup(), Scales())
    controller.expected.refresh = lambda: None
    original_view, original_rename = views.lobby_view, files.os.rename
    original_helper = getattr(helpers, 'isPlayerAccount', None)
    views.lobby_view = lambda: flash
    helpers.isPlayerAccount = lambda: True
    notified = []
    settings.on_change(lambda: notified.append(settings.values()))

    def press(**action):
        flash.actions.append(dict(action, account='42', region=config.REGION))
        controller._tick()
        return flash.models[-1]

    def disk(path):
        with open(path, 'rb') as handle:
            return json.load(handle)

    def fail_config(source, target):
        if target == settings_path and source.endswith('.tmp'):
            raise OSError('simulated settings replacement failure')
        original_rename(source, target)

    try:
        previous_stamp = os.stat(settings_path).st_mtime
        edited = settings.values()
        edited['wnxTracker'].update(count=20, futureOption='keep')
        edited['unknownSetting'] = {'external': True}
        with open(settings_path, 'wb') as handle:
            json.dump(edited, handle)
        os.utime(settings_path, (previous_stamp, previous_stamp))
        model = press(kind='opened')
        check('opening the window reads the current file even before the periodic watcher',
              state_value(model, 'tracker_count') == 1 and len(notified) == 1)

        values = {'tracker_count': 2, 'twitchChannel': 'https://twitch.tv/PlayerName/'}
        files.os.rename = fail_config
        model = press(kind='apply', request=1, values=dict(values, **{HIDE_VAR: True}))
        check('disk failure acknowledges failure, keeps runtime/file and skips account writes',
              model['saveResult'] == {'request': 1, 'error': 'local', 'retry': []}
              and state_value(model, 'tracker_count') == 1 and disk(settings_path) == edited
              and settings['wnxTracker']['count'] == 20 and len(notified) == 1 and not site.requests)
        check('failed atomic write cleans up its staging file',
              not any(name.endswith('.tmp') for name in os.listdir(workdir)))

        files.os.rename = original_rename
        model = press(kind='apply', request=2, values=values)
        check('save replies with the committed canonical model, preserving external and unknown settings',
              model['saveResult'] == {'request': 2, 'error': '', 'retry': []}
              and state_value(model, 'tracker_count') == 2
              and state_value(model, 'twitchChannel') == 'playername'
              and disk(settings_path) == settings.values() and len(notified) == 2
              and settings['unknownSetting'] == {'external': True}
              and settings['wnxTracker']['futureOption'] == 'keep')
        model = press(kind='apply', request=3, values=values)
        check('canonical no-op gets its own acknowledgment without another settings notification',
              model['saveResult']['request'] == 3 and not model['saveResult']['error'] and len(notified) == 2)

        model = press(kind='apply', request=4,
                      values={'tracker_count': 0, HIDE_VAR: True, HIDE_BATTLES_VAR: True, CARD_VAR: False})
        check('mixed save waits for outstanding privacy responses after committing local settings',
              model['saveResult'] is None and state_value(model, 'tracker_count') == 0
              and set(site.requests) == {'loadoutsHidden', 'battlesHidden'}
              and disk(card_path)['cardHidden'] == ['42'])
        site.answer('loadoutsHidden', 200)
        check('reply to one of two privacy changes leaves the request pending',
              press()['saveResult'] is None)
        site.answer('battlesHidden', 503)
        model = press()
        check('mixed privacy failure identifies only the field that needs retrying',
              model['saveResult'] == {'request': 4, 'error': 'account', 'retry': [HIDE_BATTLES_VAR]}
              and state_value(model, HIDE_VAR) and not state_value(model, HIDE_BATTLES_VAR))
        press(kind='apply', request=5, values={HIDE_BATTLES_VAR: True})
        site.answer('battlesHidden', 200)
        model = press()
        check('retry receives confirmed privacy value and account links survive',
              model['saveResult'] == {'request': 5, 'error': '', 'retry': []}
              and state_value(model, HIDE_BATTLES_VAR) and disk(card_path)['links'] == {'42': 'a' * 64})

        def fail_card(source, target):
            if target == card_path and source.endswith('.tmp'):
                raise OSError('simulated card replacement failure')
            original_rename(source, target)
        files.os.rename = fail_card
        model = press(kind='apply', request=6, values={CARD_VAR: True})
        check('card preference remains unchanged on a failed write',
              model['saveResult'] == {'request': 6, 'error': 'account', 'retry': [CARD_VAR]}
              and link.card_hidden and disk(card_path)['cardHidden'] == ['42'])
        files.os.rename = original_rename
        press(kind='apply', request=7, values={HIDE_BATTLES_VAR: False})
        link._account = controller.tracker.account = '43'
        controller.hide()
        site.answer('battlesHidden', 200)
        controller._tick()
        check('a late account preference reply does not update the new account or its window',
              flash.models[-1]['account'] == '43' and flash.models[-1]['saveResult'] is None
              and link.battles_hidden is True)
        os.rename(settings_path, settings_path + '.previous')
        reloaded = Settings(session, settings_path)
        check('startup restores a settings file interrupted between the Windows renames',
              reloaded.values() == settings.values() and disk(settings_path) == reloaded.values())
    finally:
        files.os.rename, views.lobby_view = original_rename, original_view
        if original_helper is None:
            del helpers.isPlayerAccount
        else:
            helpers.isPlayerAccount = original_helper
        session.close()
