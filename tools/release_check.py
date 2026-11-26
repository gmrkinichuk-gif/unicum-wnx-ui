"""Load a built .wotmod the way the client does, outside the game.

    python2.7 tools/release_check.py dist/gg.unicum.wnxui_1.0.0.wotmod [installation.zip]

The selftest drives the mod from its sources. A release is something else:
compiled modules only, imported from scripts/client/, and resources that exist
nowhere on disk, only in the client's virtual tree. This extracts the package,
imports it from its .pyc files with the fake client of tools/checks, answers
ResMgr from the package's res/ tree, and checks that the entry point starts
the mod and that every resource the mod reads through resources.py is there.

Python 2.7, same as the client.
"""
import logging
import os
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

from checks.common import check


def check_archives(package, bundle=None):
    """Check identity and the optional installer before loading any game code."""
    with zipfile.ZipFile(package) as archive:
        check('the package has no corrupt ZIP members', archive.testzip() is None)
        names = archive.namelist()
        check('the package has no duplicate members', len(names) == len(set(names)))
        metadata = ET.fromstring(archive.read('meta.xml'))
        check('the package ID belongs to Unicum WNX UI',
              metadata.findtext('id') == 'gg.unicum.wnxui')
        version = metadata.findtext('version')
        filename = 'gg.unicum.wnxui_%s.wotmod' % version
        check('the package filename matches its ID and version',
              os.path.basename(package) == filename)
        check('the package uses client-compatible stored members',
              all(info.compress_type == zipfile.ZIP_STORED for info in archive.infolist()))
    if bundle is None:
        return
    with zipfile.ZipFile(bundle) as archive:
        check('the installer has no corrupt ZIP members', archive.testzip() is None)
        names = archive.namelist()
        check('the installer has no duplicate members', len(names) == len(set(names)))
        prefix = 'unicum.gg_%s_wot_' % version
        basename = os.path.basename(bundle)
        check('the installer filename matches the package version',
              basename.startswith(prefix) and basename.endswith('.zip'))
        client = basename[len(prefix):-4]
        folder = 'mods/%s/' % client
        packaged = folder + filename
        dependencies = [name for name in names
                        if name.startswith(folder + 'net.openwg/net.openwg.gameface_')
                        and name.endswith('.wotmod')]
        check('the installer contains one mod and one Gameface in the client folder',
              len(dependencies) == 1 and
              set(n for n in names if n.endswith('.wotmod')) == set([packaged] + dependencies))
        with open(package, 'rb') as handle:
            check('the installer embeds the exact checked package',
                  archive.read(packaged) == handle.read())
        check('the installer includes the required license notices',
              all(name in names for name in
                  (folder + 'net.openwg/LICENSE-gameface', 'licenses/unicum/LICENSE',
                   'licenses/unicum/NOTICE', 'licenses/unicum/THIRD_PARTY_NOTICES.md',
                   'licenses/unicum/RELEASE_LICENSE.md')))
        check('the installer includes the privacy disclosure', 'licenses/unicum/PRIVACY.md' in names)


class Section(object):

    def __init__(self, path):
        self._path = path

    @property
    def asBinary(self):
        with open(self._path, 'rb') as handle:
            return handle.read()

    def keys(self):
        return os.listdir(self._path)


class FakeEventBus(object):
    """The selftest never needs one: its client has no SWFs, so views.py never installs."""

    def addListener(self, *args, **kwargs):
        pass

    def removeListener(self, *args, **kwargs):
        pass


class PackageResMgr(object):
    """ResMgr answering from the package's res/ tree, as the client merges it."""

    root = None
    # Paths answered as absent: the SWFs, as in the selftest, whose fake client
    # cannot host views.py; they are checked for in the package on their own.
    hidden = ('gui/flash/',)

    @classmethod
    def _path(cls, path):
        return os.path.join(cls.root, *path.split('/'))

    @classmethod
    def isFile(cls, path):
        return not path.startswith(cls.hidden) and os.path.isfile(cls._path(path))

    @classmethod
    def openSection(cls, path):
        full = cls._path(path)
        return Section(full) if os.path.exists(full) else None


def main():
    import imp
    from checks.client import install_fake_client
    from checks.engine import FakeBigWorld, FakeResponse

    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    logging.basicConfig(level=logging.INFO, format='       %(name)s: %(message)s')
    check_archives(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
    workdir = tempfile.mkdtemp(prefix='unicum-release-')
    try:
        with zipfile.ZipFile(sys.argv[1]) as archive:
            names = archive.namelist()
            archive.extractall(workdir)
        res = os.path.join(workdir, 'res')
        check('no source file ships', not [n for n in names if n.endswith('.py')])
        prefix = 'res/scripts/client/unicum/'
        removed = ('battles/', 'replays/', 'loadouts/', 'twitch', 'game_link/',
                   'tank_button/', 'reporting.pyc', 'motion.pyc', 'mods_list.pyc', 'settings_tab.pyc',
                   'web/hangar/', 'web/results/', 'web/stronghold/')
        check('removed integrations cannot be imported from the package',
              not any(n.startswith(prefix) and n[len(prefix):].startswith(removed) for n in names))
        check('the entry point is where the client loads mods from',
              'res/scripts/client/gui/mods/mod_unicum.pyc' in names)
        check('the native settings tab library is absent', 'res/gui/flash/unicum.settings.swf' not in names)
        check('the package includes release license information',
              'res/licenses/unicum/RELEASE_LICENSE.md' in names)
        check('the package includes the privacy disclosure', 'res/licenses/unicum/PRIVACY.md' in names)
        check('the views and the patched markers app ship',
              all('res/gui/flash/%s' % swf in names for swf in
                  ('unicum.lobby.swf', 'unicum.battle.swf', 'unicum.markers.swf', 'unicum.markers.classes.swf',
                   'battleVehicleMarkersApp.swf')))

        game = os.path.join(workdir, 'game')
        os.makedirs(os.path.join(game, 'res_mods', '2.4.0.0'))
        os.chdir(game)
        class OfflineBigWorld(FakeBigWorld):
            def fetchURL(self, url, callback, headers, timeout, method, postData):
                self.fetched.append((url, method))
                return self.callback(0, lambda: callback(FakeResponse(503, '')))

        engine = OfflineBigWorld()
        install_fake_client(engine)
        sys.modules['gui.shared'].g_eventBus = FakeEventBus()
        PackageResMgr.root = res
        sys.modules['ResMgr'] = PackageResMgr
        sys.path.insert(0, os.path.join(res, 'scripts', 'client'))

        entry = imp.load_compiled('mod_unicum', os.path.join(res, 'scripts', 'client', 'gui', 'mods', 'mod_unicum.pyc'))
        entry.init()
        import unicum
        check('the package is the compiled one from the package',
              os.path.dirname(unicum.__file__) == os.path.join(res, 'scripts', 'client', 'unicum'))
        check('the entry point started the mod', entry._loaded is unicum and unicum._session is not None)
        check('startup requests only public colour scales',
              engine.fetched == [('https://unicum.gg/api/ratings/scales', 'GET')])

        from unicum import badge_png, resources
        # As in the client, where the package is no directory on disk.
        resources._ROOT = os.path.join(workdir, 'nowhere')
        del badge_png._masks[:]
        for rel in ('web/battle/tab_screen.js', 'web/battle/tab_screen.css', 'badge_glyphs.json'):
            check('the package holds %s, read through ResMgr' % rel, bool(resources.read(rel)))
        check('a badge is drawn from the packaged masks', badge_png.png(3323, '#7A4FB2')[1:4] == b'PNG')
        check('only the battle Tab Gameface loader ships',
              PackageResMgr.isFile('gui/gameface/mods/unicum/WnxTab/WnxTab.js')
              and PackageResMgr.isFile('mods/configs/res_map/unicum_wnx_tab.json')
              and PackageResMgr.isFile('gui/gen_resources/unicum_wnx_tab.json')
              and not PackageResMgr.isFile('gui/gameface/mods/unicum/TankButton/TankButton.js'))
        from checks.privacy_core import run
        run(workdir)

        entry.fini()
        check('the entry point stops the mod', entry._loaded is None)
    finally:
        os.chdir(TOOLS)
        shutil.rmtree(workdir, ignore_errors=True)
    # check() exits on the first failure.
    print('\nrelease check passed')


if __name__ == '__main__':
    main()
