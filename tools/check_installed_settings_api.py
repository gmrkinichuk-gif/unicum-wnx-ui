"""Run the installed API's actual Python 2.7 template/generation methods offline.

No game modules are imported and no API state or player settings are written.
Pass the locally installed izeberg.modssettingsapi .wotmod as the only argument.
"""
import copy
import json
import logging
import marshal
import os
import re
import sys
import types
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
package = types.ModuleType('unicum')
package.__path__ = [os.path.join(ROOT, 'src', 'unicum')]
sys.modules['unicum'] = package
gui = types.ModuleType('gui')
gui.__path__ = []
sys.modules['gui'] = gui
api_module = types.ModuleType('gui.modsSettingsApi')
sys.modules['gui.modsSettingsApi'] = api_module

archive = zipfile.ZipFile(sys.argv[1])


def code(name):
    return marshal.loads(archive.read('res/scripts/client/gui/modsSettingsApi/' + name + '.pyc')[8:])


def child(parent, name):
    return next(value for value in parent.co_consts
                if isinstance(value, types.CodeType) and value.co_name == name)


constants = types.ModuleType('_constants')
enum = types.FunctionType(child(code('_constants'), 'COMPONENT_TYPE'), {'__name__': '_constants'})()
constants.COMPONENT_TYPE = type('COMPONENT_TYPE', (object,), enum)
sys.modules['_constants'] = constants
sys.modules['gui.modsSettingsApi._constants'] = constants
api_module.__path__ = []
templates = types.ModuleType('gui.modsSettingsApi.templates')
exec code('templates') in templates.__dict__
api_module.templates = templates
namespace = {'__name__': 'offline_api', 'copy': copy, 'COLUMNS': ('column1', 'column2'),
             '__builtins__': __builtins__, '_logger': logging.getLogger('offline_api'),
             'jsonDump': lambda value, pretty=False: json.dumps(value, sort_keys=True),
             'deprecated': lambda *args, **kwargs: lambda method: method}
methods = types.FunctionType(child(code('api'), 'ModsSettingsApi'), namespace)()
Api = type('OfflineApi', (object,), methods)
api = Api.__new__(Api)
api.activeMods = set()
api.state = {'templates': {}, 'settings': {}}
api.saveState = lambda: None


class Event(object):
    def __init__(self):
        self.handlers = []

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.handlers.remove(handler)
        return self

    def __call__(self, *args):
        for handler in list(self.handlers):
            handler(*args)


api.onSettingsChanged, api.onButtonClicked = Event(), Event()
from unicum.settings import validate
from unicum.settings_window.codec import to_window
from unicum.settings_window.page import template
from unicum.settings_window.labels import CONNECT_VAR, LINKAGE

for linked, language in ((False, 'en'), (True, 'en'), (False, 'uk'), (True, 'uk')):
    values = validate({'settingsLanguage': language})
    page = template(values, linked=linked)
    for column in ('column1', 'column2'):
        for row in page[column]:
            if 'button' in row:
                assert row['type'] == 'RadioButtonGroup' and row['options'] == []
    api.setModTemplate(LINKAGE, page, lambda *args: None, lambda *args: None)
    replacement = to_window(values)
    api.updateModSettings(LINKAGE, replacement)
    assert len(api.generateSettingsData()) == 1
    # Reproduce the original screenshot failure using the exact installed method.
    if not linked:
        replacement.pop(CONNECT_VAR)
        try:
            api.generateSettingsData()
            raise AssertionError('missing button key must reproduce the original bug')
        except KeyError as error:
            assert error.args == (CONNECT_VAR,)
        replacement[CONNECT_VAR] = -1
        assert len(api.generateSettingsData()) == 1
print('PASS: installed API generates linked/unlinked pages; missing twitchConnect reproduces KeyError')

from unicum.settings_window.window import SettingsWindow, api_instance
assert api_instance(api) is api, 'installed API exports its instance directly'
api.onSettingsChanged, api.onButtonClicked = Event(), Event()


class Settings(object):
    current = validate({})

    def __getitem__(self, key):
        return self.current[key]

    def values(self):
        return copy.deepcopy(self.current)

    def update(self, changes):
        pass


settings = Settings()
controller = SettingsWindow(None, settings)
controller._api = api
controller._register()
for language in ('uk', 'en', 'uk'):
    settings.current['settingsLanguage'] = language
    controller._on_settings()
    controller._check_state()
    assert len(api.onSettingsChanged.handlers) == len(api.onButtonClicked.handlers) == 1
    assert len(api.generateSettingsData()) == 1
controller._remove()
assert not api.onSettingsChanged.handlers and not api.onButtonClicked.handlers
assert LINKAGE not in api.activeMods and LINKAGE not in api.state['templates']
print('PASS: direct API instance, language rebuilds and repeated registration/teardown keep exactly one callback pair')

from unicum.settings_window import localize
from unicum.settings_window.page import native_page
captions = set()


def collect(value):
    if isinstance(value, list):
        for item in value:
            collect(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in ('text', 'label', 'tooltip') and isinstance(item, basestring):
                captions.add(item)
            else:
                collect(item)


values = validate({})
collect(template(values, supporter=True, battles_hidden=False))
for line in native_page(values, supporter=True, battles_hidden=False).split('\n'):
    fields = line.split('\t')
    for index in {'tab': (1,), 'group': (2,), 'checkbox': (2,), 'dropdown': (2,),
                  'input': (2,), 'button': (2, 3), 'text': (1,)}.get(fields[0], ()):
        captions.add(fields[index])
    if fields[0] == 'dropdown':
        captions.update(fields[5].split('|'))
proper_names = set(('WN7', 'WN8', 'WNX', 'PR', 'WTR', 'Twitch', 'GitHub', 'Discord', 'unicum.gg', 'English'))
missing = sorted(caption for caption in captions if re.search('[a-zA-Z]', caption)
                 and caption not in proper_names and localize.text(caption, 'uk') == caption)
assert not missing, missing
print('PASS: all native/API captions, choices and tooltips have Ukrainian translations')
