# Unicum WNX UI

WNX battle overlays and a local hangar session tracker for **World of Tanks EU
2.4.1.1**. This is an independent derivative of the
[Unicum.gg client mod](https://github.com/unicum-gg/unicum.gg-mod).

## What it adds

- WNX statistics, colour accents and configurable figures for the loading
  screen, battle panels and Tab scoreboard. The Alt behavior and displayed
  metrics can be configured per surface.
- WNX accents on vehicle markers displayed by the game. These require the
  matching markers component from the build.
- A hangar Tracker with Mini, Compact, Trend and Battles views, a 10/20/30-battle
  window, and damage and assist statistics for your own random battles.
- English and Ukrainian settings through the Tracker's gear in the hangar.
  A compatible external Mod Menu may also show the settings page when
  modsSettingsApi is installed.

## Download and install

1. Open [GitHub Releases](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/releases)
   and choose the installer ZIP matching your EU client's mod folder.
2. Close the game and move any previous Unicum WNX UI or upstream Unicum.gg
   package out of the active mod folder. The current package is
   `gg.unicum.wnxui_<version>.wotmod`. The original package and some older
   releases use `gg.unicum_*.wotmod`; both versions can load the same runtime
   modules, so install only one of them.
3. Extract the ZIP into the World of Tanks root. The archive includes
   OpenWG Gameface 1.2.2 for the Tab overlay. Keep one compatible copy of that
   shared dependency.
4. In the hangar, use the gear on the WNX Tracker to change settings.
   **Apply** saves changes, **OK** saves and closes, and **Cancel** discards
   the draft. In 0.9.20 this replaces the tab previously added to the
   game's own settings window.

For a rollback, close WoT, remove just the active WNX UI package and restore
the backed-up version for the matching client. To uninstall, remove the WNX
UI package. Other mods may still use Gameface. Local data locations and
history removal are listed in [Privacy and data use](PRIVACY.md).

The [original v0.9.18 release](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/releases/tag/v0.9.18)
and its [original installer ZIP](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/releases/download/v0.9.18/unicum.gg_0.9.18_wot_2.4.1.1.zip)
remain available with their historical package names and behavior.

## Privacy and compatibility

The current mod makes HTTPS requests to Unicum.gg for WNX ratings and colour
scales, and to Tomato.gg for a public table of expected vehicle values. Rating
queries include numeric account IDs and, for vehicle-specific statistics,
vehicle IDs and a mode code. The session journal stays on the player's
computer. See [Privacy and data use](PRIVACY.md) for the full inventory.

The [WGMods assessment](docs/WGMODS_REVIEW.md) records which checks were
completed and which require moderation or live client evidence.

## Build

Use Python 3, Java 17 and Python 2.7 with a matching installed EU client.
The build uses that client's Scaleform libraries and its markers movie.

```powershell
python tools/build_as3.py --game "F:/Games/World_of_Tanks_EU"
python tools/build_release.py --version 0.9.20 --python27 "C:/Python27/python.exe" --game "F:/Games/World_of_Tanks_EU"
python -B -m unittest discover -s tools -p test_build_release.py
& "C:/Python27/python.exe" -B tools/release_check.py dist/gg.unicum.wnxui_0.9.20.wotmod dist/unicum.gg_0.9.20_wot_2.4.1.1.zip
node tools/check_roster_grid.mjs
node tools/check_battle_ui.mjs
node tools/check_settings_ui.mjs
node tools/check_tracker_ui.mjs
```

See [release procedure](docs/RELEASING.md), [package identity](docs/PACKAGE_IDENTITY.md)
and [changelog](CHANGELOG.md). Report issues without including your settings,
battle-history file, credentials or unredacted game logs.

## License and attribution

The mod source is licensed under [GNU AGPL v3](LICENSE). The [NOTICE](NOTICE)
and [third-party notices](THIRD_PARTY_NOTICES.md) identify the upstream work
and separate dependencies. Wargaming owns its trademarks and client material
used by this project. Wargaming does not endorse this work.
