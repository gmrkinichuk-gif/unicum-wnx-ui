"""Packaging regressions; no game installation, compiler or network required.

    python -B -m unittest discover -s tools -p 'test_build_release.py'
"""
import contextlib
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from unittest.mock import patch

import build_release
import install_dev
from release_check import check_archives


class PackageIdentityTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.version = '0.9.19-dev.6'
        self.client = '2.4.1.1'
        self.folder = 'mods/' + self.client + '/'
        self.package = self.root / ('gg.unicum.wnxui_' + self.version + '.wotmod')
        self.write_package()
        gameface = self.root / 'vendor'
        gameface.mkdir()
        (gameface / 'net.openwg.gameface_1.2.2.wotmod').write_bytes(b'dependency')
        (gameface / 'LICENSE-gameface').write_text('Gameface license')
        for name in ('LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'PRIVACY.md', 'RELEASE_LICENSE.md'):
            (self.root / name).write_text(name)
        (self.root / 'licenses').mkdir()
        (self.root / 'licenses' / 'component.txt').write_text('component license')
        with patch.multiple(build_release, REPO=self.root, DIST=self.root, GAMEFACE=gameface):
            with contextlib.redirect_stdout(io.StringIO()):
                build_release.bundle(self.package, self.version, self.client)
        self.bundle = self.root / ('unicum.gg_' + self.version + '_wot_' + self.client + '.zip')

    def write_package(self, metadata=None, compression=zipfile.ZIP_STORED):
        with zipfile.ZipFile(self.package, 'w', compression) as archive:
            archive.writestr('meta.xml', metadata or build_release.meta(self.version))
            archive.writestr('res/scripts/client/gui/mods/mod_unicum.pyc', b'bytecode')

    def verify(self, package=None):
        with contextlib.redirect_stdout(io.StringIO()):
            check_archives(str(package or self.package), str(self.bundle))

    def rewrite_bundle(self, transform):
        with zipfile.ZipFile(self.bundle) as archive:
            entries = [(n, archive.read(n)) for n in archive.namelist()]
        with zipfile.ZipFile(self.bundle, 'w') as archive:
            for name, data in entries:
                for target, payload in transform(name, data):
                    archive.writestr(target, payload)

    def test_release_metadata_has_independent_id_and_unchanged_version(self):
        for version in ('0.9.18', self.version):
            metadata = ET.fromstring(build_release.meta(version))
            self.assertEqual(metadata.findtext('id'), 'gg.unicum.wnxui')
            self.assertEqual(metadata.findtext('version'), version)

    def test_bundle_layout_payload_dependency_and_licenses(self):
        self.verify()
        with zipfile.ZipFile(self.bundle) as archive:
            self.assertEqual(archive.read(self.folder + self.package.name), self.package.read_bytes())
            self.assertEqual(archive.read(self.folder + 'net.openwg/net.openwg.gameface_1.2.2.wotmod'),
                             b'dependency')
            self.assertIn('licenses/unicum/licenses/component.txt', archive.namelist())
            self.assertIn('licenses/unicum/PRIVACY.md', archive.namelist())
            self.assertIn('licenses/unicum/RELEASE_LICENSE.md', archive.namelist())

    def test_old_package_id_is_rejected(self):
        self.write_package(build_release.meta(self.version).replace('gg.unicum.wnxui', 'gg.unicum'))
        with self.assertRaises(SystemExit):
            self.verify()

    def test_old_filename_is_rejected(self):
        legacy = self.root / ('gg.unicum_' + self.version + '.wotmod')
        legacy.write_bytes(self.package.read_bytes())
        with self.assertRaises(SystemExit):
            self.verify(legacy)

    def test_filename_version_mismatch_is_rejected(self):
        self.write_package(build_release.meta('0.9.18'))
        with self.assertRaises(SystemExit):
            self.verify()

    def test_deflated_wotmod_is_rejected(self):
        self.write_package(compression=zipfile.ZIP_DEFLATED)
        with self.assertRaises(SystemExit):
            self.verify()

    def test_wrong_client_folder_is_rejected(self):
        self.rewrite_bundle(lambda n, d: [(n.replace(self.folder, 'mods/0.0.0.0/'), d)])
        with self.assertRaises(SystemExit):
            self.verify()

    def test_additional_legacy_package_is_rejected(self):
        with zipfile.ZipFile(self.bundle, 'a') as archive:
            archive.writestr(self.folder + 'gg.unicum_0.9.18.wotmod', b'legacy')
        with self.assertRaises(SystemExit):
            self.verify()

    def test_different_embedded_package_is_rejected(self):
        self.rewrite_bundle(lambda n, d: [(n, b'wrong' if n.endswith(self.package.name) else d)])
        with self.assertRaises(SystemExit):
            self.verify()

    def test_missing_license_is_rejected(self):
        self.rewrite_bundle(lambda n, d: [] if n == 'licenses/unicum/NOTICE' else [(n, d)])
        with self.assertRaises(SystemExit):
            self.verify()

    def test_missing_release_license_is_rejected(self):
        self.rewrite_bundle(lambda n, d: [] if n == 'licenses/unicum/RELEASE_LICENSE.md' else [(n, d)])
        with self.assertRaises(SystemExit):
            self.verify()

    def test_dev_package_has_independent_id_and_preserves_version(self):
        bytecode = self.root / 'mod_unicum_dev.pyc'
        bytecode.write_bytes(b'dev bytecode')
        package = self.root / ('gg.unicum.wnxui.dev_' + install_dev.MOD_VERSION + '.wotmod')
        with patch.object(install_dev, 'FLAGS_BUILD', self.root / 'no-flags'):
            install_dev.build_wotmod(bytecode, package)
        with zipfile.ZipFile(package) as archive:
            metadata = ET.fromstring(archive.read('meta.xml'))
            self.assertEqual(metadata.findtext('id'), 'gg.unicum.wnxui.dev')
            self.assertEqual(metadata.findtext('version'), install_dev.MOD_VERSION)
            self.assertEqual(archive.read('res/scripts/client/gui/mods/mod_unicum_dev.pyc'),
                             bytecode.read_bytes())


if __name__ == '__main__':
    unittest.main()
