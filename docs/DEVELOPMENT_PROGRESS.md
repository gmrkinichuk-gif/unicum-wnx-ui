# Package identity migration progress

Date: 2026-11-18. Repository: `gmrkinichuk-gif/unicum-wnx-ui`.

## Scope and workspace

- Change the release Package ID from `gg.unicum` to `gg.unicum.wnxui`, without
  changing mod versions, runtime code, UI, WNX algorithms or published assets.
- The checkout is `in-game-settings/` inside the larger local workspace.
- Pre-existing uncommitted Tracker, settings and test changes are present.
  Preserve them and exclude them from this task's commit. Tests of the working
  tree may include those changes; distinguish this from validation of the commit.
- Current published version is 0.9.18. Existing local candidates reach
  0.9.19-dev.6. Reuse versions for validation; do not increment or publish.

## Completed investigation

- `tools/build_release.py` derives both `meta.xml` and the output `.wotmod`
  filename from `MOD_ID`. `bundle()` uses the generated package filename.
- Both `build.yml` and `candidate.yml` hard-code the old release filename.
- `tools/install_dev.py` has a separate upstream dev Package ID.
- Runtime `gg.unicum.menu` and settings linkage `gg.unicum` are integration IDs,
  not package metadata. Shared Python modules, resources, configuration and
  Gameface registrations prevent safe coexistence with upstream even after
  changing the Package ID. Document these without renaming runtime namespaces.
- Historical release links, `downloads/`, checksums and audit evidence must stay
  unchanged.

## Completed implementation and changed files

- `tools/build_release.py`: `MOD_ID = 'gg.unicum.wnxui'`. Metadata and output
  filename derive from that constant; the installer uses the new filename.
- `tools/install_dev.py`: separate dev ID `gg.unicum.wnxui.dev`, preserving
  dev version `0.1.0` and entry/resource paths.
- `tools/release_check.py`: check metadata ID, matching filename/version,
  stored/nonduplicate/noncorrupt ZIP members. Optional second argument checks
  the installation ZIP's version, client directory, exactly one mod and one
  Gameface package, exact embedded mod bytes and required license notices.
  Game-only imports are deferred so packaging checks can also run on Python 3.
- `tools/test_build_release.py`: 11 packaging tests, including rejection of
  the old ID/filename, mismatched version, compression, wrong client folder,
  an extra legacy package, changed embedded bytes and missing license notice.
- `.github/workflows/build.yml`, `.github/workflows/candidate.yml`: run those
  tests and pass the new package filename plus the installer to release_check.
  Publication behavior and permissions are unchanged.
- `AGENTS.md`, `README.md`, `docs/DEVELOPMENT.md`, `docs/RELEASING.md`,
  `docs/BETA_VALIDATION.md`, `docs/SESSION_TRACKER_QA_UK.md`: current build,
  install, removal, rollback and QA instructions. Historical links retained.
- `docs/PACKAGE_IDENTITY.md`: shared-namespace audit and safe migration plan.
- `CHANGELOG.md`: dated maintenance note without a version heading or bump.
- `docs/DEVELOPMENT_PROGRESS.md`: this handoff record.

No runtime Python, AS3, web resources or algorithms were edited by this task.
No game files changed. No release, tag or push performed. Published downloads,
release links, checksums and historical audit evidence were not modified.

## Automated verification (2026-11-18)

Two scopes were checked: the existing working tree, and an isolated snapshot
of `HEAD` plus only the 15 files listed above. The latter excludes all
pre-existing uncommitted Tracker/settings/test changes. Its source is under
ignored `build/package-id-validation/commit-source/`.

| Check | Working tree | Isolated commit source |
| --- | --- | --- |
| Python 3.12 packaging unittest | 11 passed | 11 passed |
| Python 2.7.18 selftest | 1,145 checks passed before and after migration | 1,096 checks passed |
| Python 2.7 compiled release + installer check | 34 checks passed | 34 checks passed |
| Roster geometry fixtures | 8 layouts passed | 8 layouts passed |
| Battle UI / marker fixtures | Passed | Passed |
| Settings UI fixtures | Passed | Passed |
| Tracker UI fixtures | 1,300 assertions passed | 1,287 assertions passed |

No explicit API skips or failed checks were reported. These are local runs;
GitHub Actions itself has not been dispatched. `git diff --check` passed.

Both builds reused local compiled SWFs, flags and icons; they were not rebuilt
from client inputs for this packaging-only task. Snapshot builds therefore
verify package/source behavior with existing assets, not an independently
recompiled AS3 deliverable. None of these artifacts is authorized for release.

The existing candidate version **0.9.19-dev.6** and client folder **2.4.1.1**
were reused without altering version declarations or old candidate outputs:

- Working-tree outputs: `build/package-id-validation/after/`.
- Isolated outputs: `build/package-id-validation/commit-source/dist/`.
- Package: `gg.unicum.wnxui_0.9.19-dev.6.wotmod`.
- Installer: `unicum.gg_0.9.19-dev.6_wot_2.4.1.1.zip`.
- Confirmed installer paths:
  `mods/2.4.1.1/gg.unicum.wnxui_0.9.19-dev.6.wotmod`,
  `mods/2.4.1.1/net.openwg/net.openwg.gameface_1.2.2.wotmod`,
  shared dependency license and `licenses/unicum/` notices.

For a direct before/after comparison, the builder from original `HEAD` and
the modified builder packaged the same working-tree sources/assets at the
same version into separate ignored directories. All 428 member paths match:
metadata differs only in `<id>`, 115 Python bytecode modules have equal code
objects (recursively ignoring temporary compiler source filenames and `.pyc`
timestamps), and all 312 remaining members are byte-identical. Installer paths
differ only in the mod filename; dependency and license bytes are unchanged.
This comparison isolates the package migration from unrelated local edits.

Reproduction commands from the repository root (adjust interpreter paths):

```powershell
python -B -m unittest discover -s tools -p test_build_release.py
& ../source_modified/build/tools/python27/python.exe -B tools/selftest.py
& ../source_modified/build/tools/python27/python.exe -B tools/release_check.py build/package-id-validation/after/gg.unicum.wnxui_0.9.19-dev.6.wotmod build/package-id-validation/after/unicum.gg_0.9.19-dev.6_wot_2.4.1.1.zip
node tools/check_roster_grid.mjs
node tools/check_battle_ui.mjs
node tools/check_settings_ui.mjs
node tools/check_tracker_ui.mjs
```

Ignored evidence: `build/package-id-{baseline-selftest,selftest,build,release-check,payload-comparison,roster-grid,battle-ui,settings-ui,tracker-ui}.log`
and `build/package-id-validation/commit-{selftest,build,release-check}.log`.

## Problems, limitations and remaining work

- Original and derivative retain shared `unicum.*` modules, bootstraps, SWFs,
  Gameface registrations, menu/settings linkage and configuration directories.
  The new Package ID does **not** enable simultaneous installation. Remove old
  packages from all scanned folders and back up settings before switching.
  Full namespace isolation and a configuration migration would be separate work.
- The release check's fake client cannot perform the first-run restart:
  `FakeBigWorld.savePreferences` is absent. It logs that fixture limitation;
  startup/resource/teardown checks still pass. Validate actual restart in WoT.
- Live WoT startup, first-run resource indexing, loading, panels, Tab, markers,
  WNX display, settings/language persistence, Tracker and optional API/modpack
  combinations remain **not tested in this task**. Follow BETA_VALIDATION.md
  and PACKAGE_IDENTITY.md, then inspect `game.log` for duplicate/resource errors.
- Before distributing any candidate, recompile assets against the intended
  client from the final source, run package checks, and complete in-game QA.
- Publication requires explicit maintainer confirmation. Do not replace
  historical assets or create a release as part of this task.

Implementation and automated verification are complete. Commit title:
`Give Unicum WNX UI a distinct package identity`. The commit contains only
the 15 task files; unrelated pre-existing changes remain in the working tree.
Use `git log -1 --oneline` to obtain its identifier after committing.

## Manual-test preparation after 7b7a9b9 (2026-11-18)

The earlier automatic-install request was interrupted before any game mutation.
The current instruction supersedes it: prepare artifacts and instructions only.
Do not install into the game, remove user files, change versions, publish or push.

- HEAD is `7b7a9b9`. There are 18 pre-existing modified files and four untracked
  source/test files; the index is empty. These changes are preserved.
- Use the existing local candidate version `0.9.19-dev.6`, without a bump.
- Actual installed client: `F:/Games/World_of_Tanks_EU`, EU
  `v.2.4.1.1 #993`; `paths.xml` scans `mods/2.4.1.1` recursively and
  `res_mods/2.4.1.1`. This matches the documented supported target.
- All seven required client SWCs and `battleVehicleMarkersApp.swf` were found
  in the installed client's `gui-part*.pkg`. No mirror/fallback is required.
- New isolated working directory:
  `build/manual-test-20261118-151922Z/`. Its `source/` contains 300 files:
  tracked working-tree files plus the four existing untracked source/test
  files. This candidate includes local uncommitted improvements; it is not a
  pristine-commit build. `BUILD_MANIFEST.json` records source hashes and status.
- Compile AS3 freshly against the installed client in the isolated directory.
  Cached compiler/playerglobal and local npm modules are copied into that
  directory; existing outputs and user files are not overwritten.
- Fresh selftest passed (Python 2.7), 11 packaging tests passed, and all four UI
  fixtures passed (Tracker: 1,300 assertions). Full build/archive checks are
  complete; detailed results follow below.
- Existing `build/test-install/` contains `gg.unicum_0.9.17.wotmod` and
  `settings-before-test.json`; leave both unchanged and use a new staging tree.
- Read-only game audit found three old packages in the active client folder:
  `gg.unicum_0.9.19-dev.2.wotmod`, `gg.unicum_0.9.19-dev.4.wotmod`, and
  `gg.unicum_0.9.19-dev.6.wotmod`. No loose `mod_unicum*` bootstrap was found.
  These packages remain untouched; manual installation must first move them
  outside every scanned directory. Do not restore all three together on rollback.

### Completed build and verification

- Recompiled all six AS3 compilation targets and patched a fresh copy of the
  actual client's markers movie. All seven required SWCs match bytes
  re-extracted from the installed client's packages. Original marker DoABC
  payloads remain intact alongside the added boot code. No cached mod SWF or
  mirror-built client input was used.
- Rebuilt 252 flags and the original icon generator's outputs in the isolated
  source tree. Its generated web PNGs are recorded separately in the manifest;
  the original working-tree images were not overwritten.
- Used Python 2.7.18 for bytecode and checks, Python 3.12 for packaging,
  Java Temurin 17.0.21, Node 24.21.0 and the existing locked npm dependencies.
- Built `gg.unicum.wnxui_0.9.19-dev.6.wotmod`: 1,782,178 bytes, 428 members,
  `meta.xml` ID `gg.unicum.wnxui`, version `0.9.19-dev.6`. Members are stored,
  nonduplicate and CRC-valid; all `.pyc` magic matches Python 2.7. No source
  `.py`, local_settings, bytecode cache directories or personal config ships.
- Built `unicum.gg_0.9.19-dev.6_wot_2.4.1.1.zip`: 736,321 bytes. Reused the
  version and read the target client folder from the installed `paths.xml`.
- Ran Python 2.7 selftest: **1,145 checks passed**, no explicit API skips.
- Ran packaging unittest: **11 tests passed**.
- Ran compiled package + ZIP release_check: **34 checks passed**. The known
  fake-client first-run restart limitation remains; real restart needs WoT.
- Roster geometry: **8 layouts passed**; battle UI and settings UI fixtures
  passed; Tracker UI: **1,300 assertions passed**. No live WoT test performed.
- Extracted ZIP into newly created empty
  `build/manual-test-20261118-151922Z/test-install/`. Exactly one new Unicum
  package and one Gameface dependency are present; no old IDs/bootstrap,
  wrong-version folders or personal configurations. ZIP members stay within
  the staging root, and the embedded mod is byte-identical to the standalone.
- Bundled Gameface ID/version: `net.openwg.gameface` / `1.2.2`; SHA-256
  `2bb65f28663e3ab34b5a1102a1bbd1f6e17a65e1f6a898a8645c4ab732b50184`.
  It is identical to both the vendored dependency and the single installed
  game copy. Required license notices exist in both package and installer.
- Read-only overlap audit found no other installed package resource collision
  beyond the three old Unicum packages; no loose resource overrides. This
  does not certify dynamic compatibility with the installed modpack.
- Confirmed release/dev IDs and both CI filename consumers. Remaining old
  strings are migration instructions, historical evidence, negative tests or
  deliberately unchanged runtime integration IDs.

### Deliverables

Exact ready ZIP path:

```text
F:\Games\WoT_mod_project\in-game-settings\build\manual-test-20261118-151922Z\dist\unicum.gg_0.9.19-dev.6_wot_2.4.1.1.zip
```

ZIP SHA-256:
`d39fecac2daa1dfb6ae2fc6005b908c6264905aae3c91db14c4daf9183e63278`.

Standalone package is beside it; SHA-256:
`2cbc42b0c016a46e5bddc0d4f72f5e1f48bf8036f7ebcc40f62206757e6158c4`.

`dist/SHA256SUMS.txt` records both hashes. The build root also contains
`BUILD_MANIFEST.json`, `INSTALL_AUDIT.json`, build/test logs and the preserved
`source/` snapshot. All generated outputs are ignored by Git.

[MANUAL_TESTING_UK.md](MANUAL_TESTING_UK.md) provides exact paths, backup and
manual install/rollback instructions, the three pre-existing packages to move,
the instruction to reuse existing identical Gameface, and a 13-row in-game
checklist covering startup, restart, hangar, Tracker, loading, panels, Alt, Tab,
markers, WNX, settings, persistence and exit/logs. A copy is included beside
the candidate artifacts. This follow-up changes only that guide and this
progress record in the repository; existing source/test changes stay intact.

### Outstanding manual steps

1. The user must close WoT, back up configuration and move the three old
   packages out of scanned folders before installing the single new package.
   Nothing in the actual game installation has been changed by this task.
2. Complete every in-game checklist row; all remain untested. Review only the
   new session's log for duplicate loads, resource errors and regressions.
3. Restore only one previous Unicum package on rollback; do not reinstate the
   pre-existing three-package collision. Preserve before/after configuration.
4. If the client changes from EU 2.4.1.1 #993, stop and rebuild against its
   actual files. No missing-input substitute was needed for this candidate.

No new commit, game installation, deletion of user files, version change,
release, tag or push was performed during this preparation.

## Standalone settings shortcut investigation (2026-11-18)

Scope clarified by the maintainer during this task: **disable only
`gg.unicum.menu`; leave Tracker's gear and the modsSettingsApi page intact**.
This clarification limits the earlier native-only wording. Do not migrate
settings or remove other entry points in this change.

Baseline HEAD: `7b7a9b9`. The pre-existing modified/untracked source and test
files, the previous uncommitted progress record and manual-testing guide are
preserved. An ignored checkpoint under `build/menu-shortcut-analysis/` records
the original Git status, file hashes and the original progress document.

Investigation so far:

- `start()` calls `mods_list.install()`; the old installer constructed
  `ModsListEntry`, whose `install()` called `g_modsListApi.addModification`
  with `gg.unicum.menu`. Its callback delayed the settings-window route.
- `labels.LINKAGE = 'gg.unicum'` identifies the optional API page; it is
  independent from menu ID `gg.unicum.menu`, native AS3 linkage
  `unicum.SettingsTab`, and Package ID `gg.unicum.wnxui`.
- Native Apply travels through AS3 `SettingsTabView.onCommit`, the shell's
  output queue, `SettingsTab._take`, `codec.apply_window`, `Settings.update`
  and readers' notifications. That path contains no direct menu removal.
- A confirmed separate removal path is TrackerSettings opening:
  `TrackerRoot.openSettings` -> `kind: opened` -> `Controller._action` ->
  `menu.retire` -> `ModsListEntry._remove` -> `removeModification`. This does
  not prove that native Apply caused the reported disappearance.
- The actual client log confirms Aslain Mod Menu 2.1.15 serves modsListApi
  through its compatibility shim. The relevant vendor implementation is
  obfuscated, and the log has no menu-removal call stack/entry-state snapshots.
  The exact cause of the native-Apply disappearance remains unconfirmed.
- Commit `7b7a9b9` changed packaging/CI/documentation, not these runtime
  registrations. There is no source-level dependency from Apply/menu lifetime
  to the new Package ID.

Completed temporary implementation:

- `src/unicum/mods_list.py`: public installer no longer constructs/registers
  a menu entry and returns `None`. Retain only the session context needed by
  existing account-card actions, with idempotent setup and guarded teardown.
- `tools/checks/menu_entry.py` and `tools/checks/settings_ui.py`: exercise
  absent registration, unchanged foreign menu items, native Apply/live
  notification/persistence, existing routes, callback cancellation and session
  replacement. All 13 new checks pass in the working tree.
- `tools/check_settings_ui.mjs`: execute actual SettingsTabs methods against
  fixtures; verify one native tab, recovery after the game's Apply rebuild,
  preserved game tabs and selected-tab behavior.
- Baseline selftest: 1,145 checks passed. Updated working-tree selftest:
  1,158 checks passed, no explicit skips. Native AS3 fixture check passed.

Detailed call chains, evidence limits, a focused runtime diagnostic plan and
the deferred panel architecture are in
[MENU_SHORTCUT_AUDIT.md](MENU_SHORTCUT_AUDIT.md). No diagnostic hooks were
enabled in the live client; vendor files were read only.

Final automated results:

| Check | Current working tree | HEAD + only this task's changes |
| --- | --- | --- |
| Python 2.7 selftest | 1,158 passed | 1,109 passed |
| Packaging unittest | 11 passed | 11 passed |
| Roster fixtures | 8 layouts passed | 8 layouts passed |
| Battle UI fixtures | Passed | Passed |
| Settings UI/native tab fixtures | Passed | Passed |
| Tracker UI fixtures | 1,300 assertions passed | 1,287 assertions passed |

No failed checks or explicit API skips. `git diff --check` passed. The isolated
copy at `build/menu-shortcut-analysis/commit-source/` excludes the earlier
uncommitted Tracker/store/codec work and previous documentation additions.
Source hashes confirm all unrelated pre-existing files are unchanged, including
WNX formulas, Tracker code, battle code, AS3, packaging/version declarations,
configuration persistence code and `docs/MANUAL_TESTING_UK.md`.

Files belonging to this commit:

- `src/unicum/mods_list.py`: pause only standalone registration, retain
  navigation and guarded session cleanup; no live menu API mutation.
- `tools/checks/menu_entry.py`: 13 lifecycle/save/menu regression checks.
- `tools/checks/settings_ui.py`: invoke the new checks in the existing selftest.
- `tools/check_settings_ui.mjs`: execute native registration and Apply-recovery
  methods against fixtures, preserving game tabs and selection.
- `README.md`, `CHANGELOG.md`: describe the temporary policy without a bump.
- `docs/MENU_SHORTCUT_AUDIT.md`: investigation, uncertainty, diagnostics and
  future configuration/UI boundaries.
- `docs/DEVELOPMENT_PROGRESS.md`: only this investigation section is staged;
  previous uncommitted manual-test progress remains in the working tree.

Deferred work: define a UI-independent typed field/action catalog, keep one
configuration authority and separate account/history commands, then adapt a
future panel without duplicating algorithms or persistence. The current
Tracker panel derives its catalog from native page strings; this coupling is
documented, not refactored. Other settings entry points remain by the explicit
maintainer clarification.

Still required in WoT after rebuilding a candidate: confirm absence of our
standalone entry before/after Apply; native tab Apply/Cancel/OK, live updates
and full-restart persistence; preserved Tracker gear and optional API page;
other mods/menu items; battle panels/Alt/Tab/markers/WNX. The new code has not
been installed or live-tested. Prior test ZIPs do not contain this change.

Commit title: `Pause standalone Unicum settings menu registration`. Only the
eight task files above belong to this commit. No game files, user configuration
or third-party modification were changed; no version/Package ID change,
release, tag or push is part of this task.

## Fresh menu-disabled test build after fe23da0 (2026-11-18)

Requested outcome: a new isolated `.wotmod` and installation ZIP containing
the paused `gg.unicum.menu` registration, without installing into the game.
Keep `gg.unicum.wnxui` and the existing DEV version `0.9.19-dev.6`.

- HEAD: `fe23da0`; index empty. All pre-existing uncommitted files are retained.
- Isolated directory: `build/menu-disabled-test-20261118-161700Z/`.
- `source/` contains 303 tracked/untracked working-tree files, including the
  current local Tracker/settings changes. This is deliberately a working-tree
  candidate, not a pristine HEAD build. `BUILD_MANIFEST.json` records original
  source hashes and Git status.
- The snapshot's `src/unicum/mods_list.py` matches HEAD exactly; SHA-256
  `a0d1a593467f5b3dc54752ec5ac4891cc6b062f3d7902be21b487a0c704eace0`.
- Installed client checked: EU `v.2.4.1.1 #993`, active mods folder `2.4.1.1`.
- Started clean AS3 compilation using the installed client's own packages,
  fresh Python compilation and resource generation. No mirror client inputs
  or precompiled mod SWFs are used. Cached compiler/npm libraries are build
  tools only and copied into the isolated tree.
- Fresh Python 2.7 selftest passed. Flags (252) and icons generated.
- Completed all applicable checks, the compiled package identity/menu smoke
  test, ZIP integrity/dependency/staging verification and replacement guide.

Nothing has been copied to the game, and no release or push is authorized.

### Completed outputs and provenance

Recompiled six AS3 targets, patched the installed client's own markers movie,
generated flags/icons, and compiled every packaged Python module with Python
2.7.18 in a fresh temporary staging tree. The seven required client SWCs were
re-extracted and their hashes matched the build inputs. Original marker DoABC
payloads remain intact alongside the added boot code. Source, tool/client and
output hashes are recorded in `BUILD_MANIFEST.json`.

New standalone package:

```text
F:\Games\WoT_mod_project\in-game-settings\build\menu-disabled-test-20261118-161700Z\dist\gg.unicum.wnxui_0.9.19-dev.6.wotmod
```

Size: 1,782,478 bytes. SHA-256:
`941e2dc9f23bc2cb270e7a3eadf986d4cc215a84f1c7f369578241fefd795e6e`.

New installation ZIP:

```text
F:\Games\WoT_mod_project\in-game-settings\build\menu-disabled-test-20261118-161700Z\dist\unicum.gg_0.9.19-dev.6_wot_2.4.1.1.zip
```

Size: 736,319 bytes. SHA-256:
`925a2a1aea691baf866dece4a16a20fa134b2f5046348e5d4c3671112f2884af`.

Package metadata remains `gg.unicum.wnxui` / `0.9.19-dev.6`. The package has
428 nonduplicate stored members, valid CRCs and Python 2.7 bytecode. No Python
source, local_settings, old bootstrap or private configuration is included.
The ZIP embeds the exact checked package under `mods/2.4.1.1/`, the unchanged
Gameface 1.2.2 under `net.openwg/`, and required license notices.

Fresh extraction into `build/menu-disabled-test-20261118-161700Z/test-install/`
contains exactly one Unicum package and one Gameface dependency, with no old
packages. This staging directory is outside the actual game installation.

### Automated checks for this build

| Check | Result |
| --- | --- |
| Python 2.7 selftest, including menu lifecycle/native Apply/persistence and optional API registration | 1,158 checks passed; no explicit API skips |
| Packaging unittest | 11 tests passed |
| Compiled package + installer release_check | 34 checks passed |
| Additional compiled-menu smoke test | Packaged install code matches source; no menu API add/remove calls on startup/teardown; navigation retained and foreign entries preserved |
| Roster layouts | 8 layouts passed |
| Battle UI/markers | Passed |
| Settings UI + native tab Apply/recovery | Passed |
| Tracker AS3 fixtures | 1,300 assertions passed |
| Panel animation against a freshly extracted/dumped client library | 24,636 assertions passed |
| Browser Tab geometry with actual client CSS and icon resources | 1280, 1366, 1920, 2560: zero geometry errors |
| Replay backfill selfcheck | 4 checks passed; no replay sending |
| Pinned upstream WNX fixture regeneration | 26 fixtures match existing fixture data |

The first headless Edge run could not initialize its Windows AppContainer
inside the sandbox, producing no geometry results. The same check was retried
outside the sandbox and all four widths passed. This was an environment
failure, not a recorded layout assertion failure. Both logs are retained.

The optional `check_installed_settings_api.py` contract runner is specifically
for izeberg modsSettingsApi 1.7.1. That implementation is not installed here;
Aslain Mod Menu 2.1.15 uses a different obfuscated API. This optional check is
not applicable and was not run against an incompatible substitute. Fake API
registration/save tests passed; real Aslain page behavior remains manual.
The known fake-client first-run restart limitation also remains: a real game
restart cannot be validated by FakeBigWorld.

### Replacement and manual test gate

`dist/TESTING_UK.md` beside the new files gives exact paths, checksums,
replacement/rollback instructions and the requested behavior checklist.
`dist/SHA256SUMS.txt` identifies both artifacts. Do not confuse this directory
with earlier same-version candidates; their filenames are identical but their
hashes differ and they do not contain the new menu fix.

Close WoT, back up the previous package and `mods/configs/unicum/` outside all
scanned game folders, move old Unicum release/dev packages out, then copy only
the new `.wotmod` into `F:/Games/World_of_Tanks_EU/mods/2.4.1.1/`. Reuse the
single existing identical Gameface 1.2.2; preserve user configuration. Check
the installed file's SHA-256 before starting. Roll back by restoring one
previous package; retain both before/after configuration backups if needed.

Still untested in the real client: no standalone hangar item before/after
Apply; the native tab; the Mod Menu settings page; Tracker gear; saving and
full-restart persistence; other menus and battle/loading/Alt/Tab/markers/WNX.
The compiled smoke test establishes our registration behavior in a fake
client, not the behavior of every installed mod or the live vendor UI.

This follow-up changes only this progress document in the working checkout;
builds, the source copy, logs and the new guide are under ignored `build/`.
Pre-existing source/test/documentation files are preserved. No installation,
new commit, release, version/Package ID change, third-party edit or push.

## WNX-only candidate 0.9.19-dev.7 (2026-11-22)

The maintainer chose to keep battle WNX, Session Tracker and their settings.
The local candidate targets the installed WoT EU 2.4.1.1 #993. It uses Package
ID `gg.unicum.wnxui` and keeps `gg.unicum.menu` paused. The working tree includes
earlier Tracker improvements and a pre-change snapshot under
`build/privacy-core-20261122-010338/before/`.

- `src/unicum/__init__.py` and `tracker/results.py` now use a local results hook.
  Runtime startup omits battle reporting, uploads, movement sampling, account
  linking, Twitch, the error reporter and unrelated lobby features. The release
  allowlist excludes those modules and their resources. Historical source and
  older artifacts remain available for reference.
- `src/unicum/profile.py`, `runtime/session.py`, `api/entry.py` and
  `api/resolve.py` constrain active data handling. HTTPS GET requests can query
  ratings using relevant account/vehicle identifiers at Unicum.gg and fetch
  public colour and expected values tables. There are no request bodies or
  authorization headers. Other players' lookup data stays in memory. Settings,
  public tables, generated badges and a rolling journal of the account's own
  results are local. The journal retains the latest 60 valid own random battles
  for the current and comparison windows. The candidate does not open or purge
  old upload queues/account files or the old on-disk player lookup cache.
- The settings bridge and templates expose the retained WNX settings and
  Tracker controls. Settings JSON is normalized to retained fields. Keep a
  backup before switching versions if you need the former integrations' options.
- `tracker/visibility.py` checks the client's foreground hangar state and
  window layers/modality. The AS3 tracker also hides on native windows and
  closes its draft when leaving the unobstructed hangar. The card is hidden
  while its own settings are open. The native settings tab remains separate.
- `Widget.as` and `Graph.as` reduce Mini from 210×66 to 176×54, Compact from
  320×100 to 272×76 and graph mode from 320×202 to 272×158. The styling keeps
  the dark glass, colour accent, chart, arrows and gear from the reference,
  with concise labels and less explanatory text.
- The Tab scoreboard uses `WnxTab` resources dedicated to battle, with the
  existing bundled Gameface 1.2.2 dependency. The builder and CI checks now
  focus on shipped features. The historical full upstream selftest expects
  retired features and is superseded for the candidate by `release_check.py`
  and its compiled-package privacy and Tracker checks.

Six AS3 targets were compiled against the installed client and the markers
movie was patched from that client. Python bytecode was compiled from a new
staging tree with Python 2.7. 66 compiled-package checks, 11 packaging tests
and all four Node UI fixture scripts passed, including 1,300 Tracker assertions
and 26 WNX formula cases in the compiled suite. The fake engine did not make
network requests. The game client was not launched, so actual window stacking,
Gameface rendering and compatibility with the installed Mod Menu remain open.

Outputs are under `build/privacy-core-20261122-010338/dist/`:

- `gg.unicum.wnxui_0.9.19-dev.7.wotmod` (968,279 bytes)
- `unicum.gg_0.9.19-dev.7_wot_2.4.1.1.zip` (425,189 bytes)
- `SHA256SUMS.txt` and `REPORT_UK.md`

`BUILD_MANIFEST.json` and `release-check.log` are in the build root. The ZIP
contains the WNX package, Gameface and notices. No installation, release or
push was performed.

## Tracker visibility and mode tabs, 0.9.19-dev.8 (2026-11-22)

The previous package loaded successfully. Its client log shows the normal
`GeneratedDefaultHangarState` after login and after navigation, as well as
ordinary hangar views and the `_GFMoEBlWindow` hangar indicator on layer 7.
There was no diagnostic recording the precise suppressor. Code inspection
found several ways to keep the card hidden, including treating every AS3
class containing `Window` as blocking and applying the general window filter
to the persistent MoE indicator.

The Tracker now checks the actual default or legacy foreground hangar state,
ignores regular hangar components and the exact undecorated nonmodal MoE
indicator, and continues to hide for visible overlay windows and native menus.
Window visibility events and a short retry handle transitions and the account
becoming ready after login. Four localized tabs replace the arrows. Selection
is direct, highlighted and persisted. Mini measures 248×54 to fit the tabs.

Recompiled six AS3 targets against the actual WoT EU 2.4.1.1 #993 libraries.
Passed 75 compiled-package checks, 11 packaging tests and all four UI fixture
suites, including 1,304 Tracker assertions. Live placement and recovery after
opening each modal still require a client check.

Artifacts and SHA-256 sums are under `build/tracker-tabs-dev8/dist/`. No game
files were installed, no release was created, and no changes were pushed.

## Tracker glass card, 0.9.19-dev.9 (2026-11-22)

Compared screenshots 117–120 with `references/approved_tracker_glass.png`
and rendered both iterations of the proposed layout offline. The reference
informed the continuous tinted card, subtle separators and shared controls.
The second pass increased the stat icons to their native 24 px and added a
separator between the two metrics.

- `Widget.as`, `Card.as` and `Graph.as` center the WNX and delta fields,
  use 272×76 px for both Mini and Compact, and keep the full chart and footer
  inside a 272×200 px card. The header uses single-line text measured against
  its available space. Rating tint, trend ink and per-battle bar colors
  still use the existing rating data.
- `TrackerIcons.as` reuses the game's Scaleform resources for damage, assist
  and settings. `TrackerRoot.as` clamps the single card and keeps the per-point
  tooltip for battle details. `tracker/state.py` and `tracker/localize.py`
  remove the unused combined summary value and labels. The calculations for
  the other metrics and local configuration storage use the existing code.
- `tools/check_tracker_ui.mjs` verifies tab bounds, modes, colors, footer,
  refresh behavior and chart interaction. `tools/checks/tracker_domain.py`
  verifies that incomplete data still preserves available metrics with the
  reduced payload.

Six AS3 targets compiled against WoT EU 2.4.1.1 #993. All 75
compiled-package checks, 11 packaging tests and four UI fixture suites passed,
including 1,116 Tracker assertions. A local render from the AS3 fixture used
the client Warhelios font and native PNGs. The Ukrainian labels fit in the
tested width, including `Компакт` at 41 px of 56 px and `Тренд` at 29.5 px
of 41 px. The font in the live GFx movie may differ.

The offline preview is `build/tracker-card-dev9/TRACKER_PREVIEW.png`.
`build/tracker-card-dev9/dist/` contains
`gg.unicum.wnxui_0.9.19-dev.9.wotmod`,
`unicum.gg_0.9.19-dev.9_wot_2.4.1.1.zip` and `SHA256SUMS.txt`.
Verified both ZIP CRC tables, the package manifest, the newly compiled lobby
SWF and the exact nested package bytes. The ZIP targets `mods/2.4.1.1/`
and includes Gameface 1.2.2 and notices.

In-game QA is pending. Check GFx resource loading, tab labels and scale,
gear click, plot hovering and mode persistence. The game was not launched
or modified. No release or push was performed.

## Tracker settings glass window, 0.9.20 (2026-11-22)

`TrackerSettings.as` and `SettingsControls.as` now use the same
rating-tinted button palette, dividers, native gear and fitted captions
as the Tracker card via `Card.as` and `Glass.as`. The window puts the
four display modes, three battle counts and six opacity steps in
visible rows of buttons. They retain the existing draft indices and
Apply, OK and Cancel flow. Other setting groups still scroll and use
their existing controls. A red confirmation remains for resetting
statistics. `tracker/page.py` and `tracker/localize.py` provide both
English and Ukrainian labels for the mode choices and position action.

Set the source and package version to `0.9.20` and added the changelog
entry. The package targets WoT EU 2.4.1.1 #993 with ID `gg.unicum.wnxui`.
The local artifacts are `build/tracker-settings-0.9.20/dist/` and the
offline Warhelios preview is `build/tracker-settings-0.9.20/SETTINGS_PREVIEW.png`.

Recompiled six AS3 targets and all shipped Python modules. Passed 78
compiled-package checks, 11 packaging tests and four UI fixture suites,
including 1,141 Tracker assertions. The checks run with a fake client.
Live GFx font metrics, control focus, popup placement and persistence
after a client restart still need an in-game pass. No installation,
release publication or push was performed.

## Tracker glass depth, 0.9.20 (2026-11-22)

`Glass.as` adds a vertical WNX-tinted gradient, a brighter top edge,
a darker bottom edge and a soft downward shadow. `Widget.as` and
`TrackerSettings.as` put the painted surface below their interactive
controls and keep the existing hit area. Selected tabs and primary
buttons get a softly highlighted top edge through `Card.as`.
The Tracker gradient follows all six existing opacity settings.

Recompiled six AS3 targets against WoT EU 2.4.1.1 #993. Passed 78
compiled-package checks, 11 packaging tests and all four UI fixture suites,
including 1,150 Tracker assertions. The new checks cover gradient direction,
opacity endpoints, rating colors and separation of the shadow from hit
testing. Offline previews on dark and light backdrops are
`build/tracker-glass-depth-0.9.20/TRACKER_DEPTH.png` and
`build/tracker-glass-depth-0.9.20/SETTINGS_DEPTH.png`.

The revised local build uses version `0.9.20` and Package ID
`gg.unicum.wnxui`. Its ZIP, .wotmod and SHA-256 manifest are in
`build/tracker-glass-depth-0.9.20/dist/`. Verified both archives and
compared their package contents with the earlier 0.9.20 build. After
normalizing Python staging paths and timestamps, the only difference
is `unicum.lobby.swf`. In-game QA still needs to confirm how Scaleform
renders the shadow and text at the player's opacity and UI scale.

## Tracker tooltips and settings sliders, 0.9.20 (2026-11-22)

`TrackerRoot.as` uses the glass panel for Trend and Battles hover tooltips.
Their content, hover targets and viewport clamping follow the existing
behavior. `TrackerSettings.as` and `Card.as` match the dropdowns to the
window with shaded surfaces, accent-colored choices and chevrons. Long
menus show a scroll thumb and can open above their field.

`SettingsControls.as` uses `OpacitySlider.as` for all four opacity rows
in the Tracker gear window. Tracker keeps its original 40–90% choices.
The loading screen, battle panel and Tab keep their 0–100% choices.
Both ranges use ten-percentage-point steps, with a percentage readout,
pointer dragging, arrow keys, Home and End. Apply and OK use the existing
settings draft and saved values. The native WoT tab uses its existing controls.

Recompiled six AS3 targets against WoT EU 2.4.1.1 #993. Passed 79
compiled-package checks, 11 packaging tests and four UI fixture suites,
including 1,167 Tracker assertions. The checks cover tooltip visibility,
dropdown bounds and scrolling, slider focus, drag cleanup, and persisted
values for all opacity settings. Offline previews are in
`build/tracker-popups-0.9.20/`. The revised ZIP, package and SHA-256 manifest
are in its `dist/` folder, using `gg.unicum.wnxui` and version `0.9.20`.

In-game QA is pending for live tooltip rendering and mouse capture during
dragging. No client launch, installation, release publication or push
was performed.

## 0.9.20 release preparation (2026-11-22)

- Removed the native Unicum tab from the lobby and battle views. The
  packaged `settings_tab.pyc` and `unicum.settings.swf` are absent. The
  hangar Tracker reads the same preference catalog directly and continues
  to save through the existing settings codec. Optional Mod Menu support
  still registers independently.
- Rewrote the user-facing README and settings guide for the WNX-only
  feature set. `PRIVACY.md` describes all outbound query fields, recipients,
  local data and removal. It ships in the package and ZIP.
- `docs/WGMODS_REVIEW.md` compares the package to official Fair Play,
  Privacy, EULA, Player Content and portal terms. Wargaming moderation,
  the full patched markers movie's redistribution permission and provider
  handling of indirect API-derived data require confirmation.
- Five AS3 targets and Python 2.7 bytecode built using WoT EU 2.4.1.1 #993.
  Ran 82 compiled-package checks, 11 packaging tests and all four UI
  suites, including 1,167 Tracker assertions. Current binary artifacts are
  under `build/final-0.9.20-audit/dist/`. Live acceptance checks for the
  removed tab and native marker visibility remain open.
