# Package identity and upstream conflicts

Reviewed 2026-11-18 against this checkout and the supplied original mod source.

New release builds use Package ID `gg.unicum.wnxui` and filename
`gg.unicum.wnxui_<version>.wotmod`. `tools/build_release.py` writes `meta.xml`
from `MOD_ID` and uses that same value for the output filename. `bundle()`
embeds that file at `mods/<client version>/<filename>`. The installation ZIP
retains `unicum.gg_<version>_wot_<client version>.zip`; its name is not a client
Package ID. `build.yml` and `candidate.yml` validate the new package and ZIP.

Dev builds use `gg.unicum.wnxui.dev` instead of upstream `gg.unicum.dev`.
The dev version and bootstrap filename are unchanged. Published release links,
`downloads/`, archived checksums and historical audit reports retain old names.
The migration creates no new release and changes no mod version.

## Remaining shared namespaces

Changing a package ID resolves the metadata collision, not the resource and
module collisions below. **Run only one Unicum variant at a time.** These are
shared paths/identifiers in both source trees, not claims of a live-tested
failure with a particular load order.

| Area | Shared path or identifier | Potential conflict |
| --- | --- | --- |
| Release entry | `res/scripts/client/gui/mods/mod_unicum.pyc` from `dev/mod_unicum.py.in` | One module path; the client's merged resource tree cannot isolate implementations by Package ID. |
| Python | `res/scripts/client/unicum/`, imports `unicum.*` | Modules may shadow or mix; independent hooks and teardown cannot be assumed. |
| Dev entry | `mod_unicum_dev.py` / `.pyc`, `dev/mod_unicum_dev.py.in` | A second bootstrap watches/reloads the same module namespace. |
| Scaleform | `res/gui/flash/unicum.*.swf`, AS3 package `unicum`, `battleVehicleMarkersApp.swf` | Shared views/classes; the patched client movie can also collide with other mods. |
| Images and cache | `gui/maps/icons/unicum/`, rating/Twitch badges under `res_mods/` | Shared virtual paths and generated files can overwrite each other. |
| Gameface | `gui/gameface/mods/unicum/`, `gui/gen_resources/unicum.json`, `mods/configs/res_map/unicum.json` | Same resource declarations, `UnicumTankButton` / `UnicumTwitchWindow` entrances and `R.mods.unicum.*` IDs. |
| Optional integrations | `src/unicum/mods_list.py`: `gg.unicum.menu`; `settings_window/labels.py`: `gg.unicum` linkage | Shared menu/settings registration keys. These are runtime integration IDs, not package metadata. |
| Persistent data | `mods/configs/unicum/` including `settings.json`, `account.json`, `resolve.json`, `scales.json` | Settings, account state and caches are shared between variants. The derivative also keeps tracker data here. |
| Embedded web UI | `window.__unicum*` globals and `unicum-*` DOM identifiers in `src/unicum/web/` | Content scripts in a common view can overwrite or reuse the same state. |

`net.openwg.gameface` is a deliberate shared dependency, bundled unchanged under
`mods/<client version>/net.openwg/`. Do not rename its ID, files or license.
`https://unicum.gg` is the data service, not a package identifier. API URLs,
logger names, UI labels and inherited copyright notices are retained.

## Safe migration

1. Close WoT and back up the installed mod files and `mods/configs/unicum/`,
   including tracker history and account state. Keep personal data private.
2. Move older Unicum packages outside all client-scanned folders. Check both
   `gg.unicum_*.wotmod` and `gg.unicum.wnxui_*.wotmod`, plus
   `gg.unicum.dev_*.wotmod` / `gg.unicum.wnxui.dev_*.wotmod` and loose dev
   bootstraps. A new ID will not replace an old filename during extraction.
3. Install one new package, keeping a single compatible shared Gameface copy.
   Existing settings need no migration for this change. When switching back to
   upstream, restore its own backed-up settings if schemas differ.
4. Validate startup, hangar, panels, Tab, markers, WNX, settings persistence,
   language and Tracker in the client; inspect `game.log` for duplicate loads
   and resource errors. Restore the backed-up files to roll back.

If simultaneous installation becomes a requirement, treat full runtime
isolation as a separate project: coordinate entry/module names, AS3 symbols,
resource maps, web IDs, integration keys and configuration migration together.
Two independent replacements of `battleVehicleMarkersApp.swf` would still need
an explicit compatibility design. Partial resource renaming cannot establish
safe coexistence. This task therefore changes package identities only.
