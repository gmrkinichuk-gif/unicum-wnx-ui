# Unicum WNX UI

A modified [Unicum.gg World of Tanks client mod](https://github.com/unicum-gg/unicum.gg-mod),
focused on WNX presentation in battle. This is an independent derivative,
not an official Unicum.gg or Wargaming release.

The current local modification is **0.9.16**, derived from the **0.9.0** source
snapshot. These numbers come from the supplied changelogs, not the development
bootstrap placeholders. The release builder injects the requested version into
the compiled package. See [CHANGELOG.md](CHANGELOG.md) and [NOTICE](NOTICE).

## Features

- Players panels and loading screen: readable text with WNX band accents and
  dark row underlays. Alt displays statistics in supported panel modes:
  WNX in Medium/Long, and WNX, win rate and battle count in Full.
- Tab scoreboard: compact player/clan statistics, native vehicle contours,
  current-player highlighting, destroyed-row treatment, and native allied
  Live Tags with leader updates and tooltips.
- Overhead markers: vertical WNX accent beside the vehicle label or Alt
  nickname. Unavailable WNX uses the existing neutral accent; disabled and
  team-filtered markers stay hidden.
- Inherited Unicum.gg features include flags and ratings on supported lobby
  surfaces, stronghold sorting, the hangar tank menu, settings integration,
  Twitch chat, account linking, and battle/replay and loadout integration.

WNX values and colour bands come from Unicum.gg. The modification does not
define replacement rating thresholds. The current UI uses row/marker accents;
the legacy `colorNamesByWnx`, `colorClanTagsByWnx` and `colorVehiclesByWnx`
settings are high-contrast text overrides in the redesigned rosters.

## Performance update 0.9.16

Unchanged Tab rows no longer repeat inline colour writes. Overhead markers cache
geometry and per-account payloads, and hidden Scaleform tables skip row work.
In a single matched replay window, mean sampled FPS changed from 69.58 to 70.42
and Python game-thread time from 2.40% to 0.96%. These are local measurements,
not a guarantee for every system; [the report](docs/PERFORMANCE_0.9.16.md) includes
P10, the lower isolated minimum, checks and known limitations.

## Compatibility and status

The supplied packages and installed client target **World of Tanks EU 2.4.1.1**.
Upstream originally documented 2.4.0.0. Other client versions and other modpacks
are not certified. A successful build or fixture test does not establish
correctness inside the game; client validation remains required before a release.
Mods replacing `battleVehicleMarkersApp.swf` can conflict with this mod.
Never load another Unicum.gg version or the development bootstrap alongside it.

## Installation and removal

Version 0.9.16 was built from the installed compatible EU client and replay-tested.
See [performance and validation notes](docs/PERFORMANCE_0.9.16.md) for results and
remaining limitations. No GitHub Release has been published; build the installation
ZIP as described below, then use `dist/unicum.gg_0.9.16_wot_2.4.1.1.zip`.

1. Close the client and back up existing Unicum settings and mod files.
2. Remove the previous `gg.unicum_*.wotmod` and any Unicum dev bootstrap.
3. Extract the ZIP into the game directory, preserving `mods/<client version>/`.
   It contains the mod and MIT-licensed openwg_gameface 1.2.2 under `net.openwg/`.
4. Start the client. A first-start resource-map update may restart it once.

Settings are created in `mods/configs/unicum/settings.json`; the default metric
is `wnx`. modsSettingsApi and modsListApi are optional integrations.
To remove the mod, close the client and remove its `gg.unicum_*.wotmod`.
Keep shared openwg_gameface if another installed mod uses it. Restore the backed
up mod to roll back. Account links, settings and caches live outside this repo.

## Building

Requirements: Python **3.10+** for tools (3.12 recommended), actual Python
**2.7.18** for game bytecode/checks, Node.js **22+**, Java **11+** (17 recommended),
and an installed compatible WoT EU client. Python 2.7 is legacy: use it only
for this game's tooling. SDKs, npm packages and compilers are not vendored.

Run from the repository root, adjusting interpreter and game paths:

```powershell
npm --prefix tools/flags ci --no-audit --no-fund
npm --prefix tools/flags run build
npm --prefix tools/badges ci --no-audit --no-fund
npm --prefix tools/badges run icon
python tools/build_as3.py --game "C:/Games/World_of_Tanks_EU"
python tools/build_release.py --version 0.9.16 --python27 "C:/Python27/python.exe" --game "C:/Games/World_of_Tanks_EU"
& "C:/Python27/python.exe" -B tools/selftest.py
& "C:/Python27/python.exe" -B tools/release_check.py dist/gg.unicum_0.9.16.wotmod
node tools/check_roster_grid.mjs
node tools/check_battle_ui.mjs
```

The builder writes the `.wotmod` and installation ZIP under ignored `dist/`.
`build_as3.py` downloads Apache Royale and playerglobal, extracts client SWCs
read-only and patches a build-local copy of the markers movie. It does not
install anything unless `--install` is explicitly supplied. `--from-mirror`
is for compilation checks only: its output must never be distributed to players.

See [CONTRIBUTING.md](CONTRIBUTING.md), [developer guide](docs/DEVELOPMENT.md),
[release procedure](docs/RELEASING.md), [audit](docs/AUDIT.md) and
[third-party notices](THIRD_PARTY_NOTICES.md).

## Network and privacy

Inherited features communicate with `https://unicum.gg`, and Twitch when used.
The mod includes battle/replay and vehicle-loadout integration; review settings
before use. Account linking stores a private key in
`mods/configs/unicum/account.json`. Never commit this file, game logs, replay
files, cookies or personal settings. An optional separately installed error
reporter may submit exceptions; see `src/unicum/reporting.py`.

## License

The derivative retains upstream **GNU AGPL version 3**: [LICENSE](LICENSE).
Original copyright notices and separate dependency terms remain in force.
When distributing binaries, provide recipients the matching Corresponding
Source and required notices. A private development repository does not waive
those obligations. Wargaming client files and third-party trademarks are not
relicensed by this project. See [NOTICE](NOTICE).
