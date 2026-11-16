# Development

`src/unicum/` is Python 2.7 game code and embedded Gameface/CEF resources.
`as3/src/` contains Scaleform views and marker subclasses; `as3/stubs/` contains
compile-time stand-ins. `dev/` holds release and hot-reload bootstraps.
`res/` supplies resource maps and Gameface entry HTML. `assets/` holds source
artwork. `tools/` contains Python 3 build tools and Python 2.7 checks.
`vendor/openwg/` is the one required vendored runtime binary and its MIT notice.

Use README's build commands from the root. `npm ci` consumes committed locks;
never copy node_modules or old build output into a fresh checkout. Royale is
downloaded on demand; existing SDK caches may be reused locally but are never
versioned. Game inputs must match the client being tested. The build never
needs the original source archive, private logs or the old workspace layout.

For hot reload, build assets and SWFs, then run:

```powershell
python tools/install_dev.py --game "C:/Games/World_of_Tanks_EU" --python27 "C:/Python27/python.exe"
```

This command intentionally installs into the game. Do not run it alongside a
release `.wotmod`. Read AGENTS.md for Session teardown, shared services, API
backoff and native-client integration constraints.

## Checks

- `python2.7 -B tools/selftest.py`: fake-client regression suite with live API
  checks where reachable; inspect output for explicit skips.
- `python2.7 -B tools/release_check.py dist/gg.unicum_0.9.15.wotmod`: compiled
  package and virtual-resource check outside the game.
- `node tools/check_roster_grid.mjs`: mirrored AS3 layout fixtures.
- `node tools/check_battle_ui.mjs`: actual AS3 method bodies with display fixtures.
- `node tools/check_panel_flip.mjs --client-dump PATH`: optional check using a
  developer-supplied `_gui_battle_abc.txt` dump of the matching client library.
- `python tools/check_roster_layout.py --client-css PATH --game GAME --browser BROWSER`:
  optional real CSS/native-icon browser geometry check. Supply extracted
  `TabView.css` and a Chromium executable; client files are deliberately excluded.

Optional checks write only to ignored `build/checks/`. They are fixtures, not
evidence of in-game rendering or performance. No client installation, private
logs or screenshots are part of the repository.

Regenerate badge masks only deliberately with `npm --prefix tools/badges run
glyphs`: this writes tracked `src/unicum/badge_glyphs.json`. Icon generation
also updates small tracked panel PNGs; review any resulting diff.
