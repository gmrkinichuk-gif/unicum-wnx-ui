"""Build the released mod: what a player unzips into the game, with nothing else to install.

    python tools/build_release.py --version 1.0.0

Writes dist/gg.unicum.wnxui_<version>.wotmod, and dist/unicum.gg_<version>_wot_<game version>.zip laid
out as the game folder, which is what is published:

  mods/<game version>/gg.unicum.wnxui_<version>.wotmod
  mods/<game version>/net.openwg/net.openwg.gameface_<its version>.wotmod

openwg_gameface is what the garage features need. It is bundled from
vendor/openwg/ (MIT, its license beside it) under net.openwg/, the folder every
mod that ships it uses, so a copy from another mod is overwritten rather than
loaded twice. Update it by replacing that file.

The package contains the compiled WNX runtime, AS3 views, the battle Tab
Gameface loader and its resource mappings, and notices. Build the AS3 inputs
with tools/build_as3.py --game before packaging. The inner package uses
ZIP_STORED for the game loader and needs the real Python 2.7 interpreter.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from install_dev import AS3_BUILD, PYTHON27_CANDIDATES, RES

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'src' / 'unicum'
ENTRY = REPO / 'dev' / 'mod_unicum.py.in'
DIST = REPO / 'dist'

MOD_ID = 'gg.unicum.wnxui'

# Where the client's own paths.xml is published, to read the folder it looks in.
#
# unicum-gg/wot.src mirrors the client's game root off the update CDN, so this
# names the folder the live client will actually read, rather than a constant
# somebody has to remember to bump. It is the package's whole dependence on a
# client version: nothing inside the .wotmod names one (see `bundle`).
PATHS_XML = 'https://raw.githubusercontent.com/unicum-gg/wot.src/EU/sources/paths.xml'
PATHS_MODS = re.compile(r'\./mods/([0-9][0-9.]*)')
GAMEFACE = REPO / 'vendor' / 'openwg'
NAME = 'unicum.gg'
DESCRIPTION = 'Battle WNX ratings, local session tracker and settings.'

# Never shipped: a developer's own settings, compiled leftovers.
EXCLUDED = {'local_settings.py'}

VERSION = re.compile(r'^\d+\.\d+\.\d+(?:-dev\.\d+)?$')


def game_version(given: str | None, game: Path | None = None) -> str:
    """The client version the zip puts the mod under.

    The installed client first, when one is to hand: its own paths.xml names
    the folder it will read, and it is right the moment the update lands.

    The mirror is the fallback, and only ever a fallback, because it is copied
    off the CDN some time after a release: on the day 2.4.1.0 shipped it still
    read 2.4.0.2, which would have put the mod in the folder the client had
    just stopped looking at -- a package that installs and does nothing, which
    is the one failure a release must not ship.
    """
    if given:
        return given
    if game is not None:
        local = Path(game) / 'paths.xml'
        if local.is_file():
            found = PATHS_MODS.search(local.read_text(encoding='utf-8', errors='replace'))
            if found:
                return found.group(1)
    try:
        with urllib.request.urlopen(PATHS_XML, timeout=30) as response:
            text = response.read().decode('utf-8', 'replace')
    except urllib.error.URLError as error:
        raise SystemExit(f'{PATHS_XML}: {error.reason}; pass --game-version')
    found = PATHS_MODS.search(text)
    if not found:
        raise SystemExit(f'no mods folder in {PATHS_XML}; pass --game-version')
    return found.group(1)


def python27(given: str | None) -> list[str]:
    candidates = [Path(given)] if given else PYTHON27_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return [str(candidate)]
    raise SystemExit('Python 2.7 not found; pass --python27')


CORE_PACKAGES = {'api', 'battle', 'runtime', 'settings', 'settings_window', 'tracker', 'web'}
CORE_MODULES = {'__init__', 'badge_png', 'badge_text', 'badges', 'config', 'extended_info',
                'figures', 'first_run', 'layouts', 'minimap_names', 'modes', 'name_markers',
                'profile', 'resources', 'roster', 'tab_screen', 'textures', 'views'}


def ignore_noncore(folder, names):
    path = Path(folder)
    ignored = set(shutil.ignore_patterns('*.pyc', '*.pyo', '__pycache__', *EXCLUDED)(folder, names))
    if path == SRC:
        ignored.update(name for name in names if name not in CORE_PACKAGES
                       and name != 'badge_glyphs.json'
                       and not (name.endswith('.py') and Path(name).stem in CORE_MODULES))
    elif path == SRC / 'web':
        ignored.update(set(names) - {'battle'})
    return ignored


def stage_package(stage: Path, version: str) -> Path:
    """The package's sources in a scratch tree, with the release's version in it."""
    package = stage / 'unicum'
    shutil.copytree(SRC, package, ignore=ignore_noncore)

    init = package / '__init__.py'
    text = init.read_text(encoding='utf-8')
    text, count = re.subn(r"^VERSION = '[^']*'$", f"VERSION = '{version}'", text, flags=re.M)
    if count != 1:
        raise SystemExit('VERSION not found in src/unicum/__init__.py')
    init.write_text(text, encoding='utf-8')
    entry = stage / 'mod_unicum.py'
    shutil.copy2(ENTRY, entry)
    text, count = re.subn(r"^__version__ = '[^']*'$", f"__version__ = '{version}'",
                          entry.read_text(encoding='utf-8'), flags=re.M)
    if count != 1:
        raise SystemExit('__version__ not found in dev/mod_unicum.py.in')
    entry.write_text(text, encoding='utf-8')
    return package


def compile_all(py27: list[str], stage: Path) -> None:
    """Every .py to .pyc with the client's Python, so the magic matches; the sources are not shipped."""
    result = subprocess.run(
        py27 + ['-c',
                'import compileall, sys; sys.exit(0 if compileall.compile_dir(sys.argv[1], quiet=1, force=1) '
                'else 1)', str(stage)],
        capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f'compiling failed:\n{result.stdout}\n{result.stderr}')


def members(stage: Path) -> list[tuple[Path, str]]:
    """(file on disk, path inside the .wotmod), in a stable order."""
    out: list[tuple[Path, str]] = []
    out.append((stage / 'mod_unicum.pyc', 'res/scripts/client/gui/mods/mod_unicum.pyc'))
    package = stage / 'unicum'
    for path in sorted(package.rglob('*')):
        if not path.is_file() or path.suffix == '.py':
            continue
        out.append((path, 'res/scripts/client/unicum/' + path.relative_to(package).as_posix()))

    swfs = [swf for swf in AS3_BUILD.glob('unicum.*.swf')
            if not swf.name.endswith('.boot.swf') and swf.name != 'unicum.settings.swf']
    swfs += list(AS3_BUILD.glob('battleVehicleMarkersApp.swf'))
    if not swfs:
        raise SystemExit('no SWFs in build/as3: run tools/build_as3.py first')
    out += [(swf, f'res/gui/flash/{swf.name}') for swf in sorted(swfs)]

    for name in ('gui/gen_resources/unicum_wnx_tab.json', 'mods/configs/res_map/unicum_wnx_tab.json',
                 'gui/gameface/mods/unicum/WnxTab/WnxTab.html', 'gui/gameface/mods/unicum/WnxTab/WnxTab.js'):
        out.append((RES / name, 'res/' + name))
    for name in ('LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'PRIVACY.md', 'RELEASE_LICENSE.md'):
        out.append((REPO / name, 'res/licenses/unicum/' + name))
    out += [(path, 'res/licenses/unicum/' + path.relative_to(REPO).as_posix())
            for path in sorted((REPO / 'licenses').rglob('*')) if path.is_file()]
    out.append((GAMEFACE / 'LICENSE-gameface', 'res/licenses/unicum/LICENSE-gameface'))
    return out


def meta(version: str) -> str:
    return ('<root>\n'
            f'    <id>{MOD_ID}</id>\n'
            f'    <version>{version}</version>\n'
            f'    <name>{NAME}</name>\n'
            f'    <description>{DESCRIPTION}</description>\n'
            '</root>\n')


def main() -> None:
    parser = argparse.ArgumentParser(description='Build the released unicum.gg .wotmod.')
    parser.add_argument('--version', required=True, help='x.y.z')
    parser.add_argument('--python27', help='path to Python 2.7 (the client\'s version)')
    parser.add_argument('--game-version',
                        help='the client the zip targets, e.g. 2.4.1.0; read off --game, then the mirror')
    parser.add_argument('--game', default=r'C:/Games/World_of_Tanks_EU',
                        help="an installed client, whose paths.xml names the folder it reads")
    args = parser.parse_args()
    if not VERSION.match(args.version):
        raise SystemExit('--version must be x.y.z or x.y.z-dev.N')

    py27 = python27(args.python27)
    folder_version = game_version(args.game_version, Path(args.game) if args.game else None)
    print(f'client   {folder_version}')
    DIST.mkdir(exist_ok=True)
    target = DIST / f'{MOD_ID}_{args.version}.wotmod'
    with tempfile.TemporaryDirectory() as scratch:
        stage = Path(scratch)
        stage_package(stage, args.version)
        compile_all(py27, stage)
        files = members(stage)
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as archive:
            archive.writestr('meta.xml', meta(args.version))
            for path, inside in files:
                archive.write(path, inside)
    size = target.stat().st_size
    print(f'wrote {target} ({len(files)} files, {size / 1024:.0f} KB)')
    bundle(target, args.version, folder_version)


def bundle(package: Path, version: str, client: str) -> None:
    """The zip a player unzips into the game folder: the mod and openwg_gameface."""
    gameface = sorted(GAMEFACE.glob('net.openwg.gameface_*.wotmod'))
    if len(gameface) != 1:
        raise SystemExit(f'expected one net.openwg.gameface_*.wotmod in {GAMEFACE}, found {len(gameface)}')
    # A rebuild for another client must not leave two archives for this version.
    for stale in DIST.glob(f'{NAME}_{version}_wot_*.zip'):
        stale.unlink()
    target = DIST / f'{NAME}_{version}_wot_{client}.zip'
    folder = f'mods/{client}'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.write(package, f'{folder}/{package.name}')
        archive.write(gameface[0], f'{folder}/net.openwg/{gameface[0].name}')
        archive.write(GAMEFACE / 'LICENSE-gameface', f'{folder}/net.openwg/LICENSE-gameface')
        for name in ('LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md', 'PRIVACY.md', 'RELEASE_LICENSE.md'):
            archive.write(REPO / name, 'licenses/unicum/' + name)
        for path in sorted((REPO / 'licenses').rglob('*')):
            if path.is_file():
                archive.write(path, 'licenses/unicum/' + path.relative_to(REPO).as_posix())
    print(f'wrote {target} ({target.stat().st_size / 1024:.0f} KB, with {gameface[0].name})')


if __name__ == '__main__':
    main()
