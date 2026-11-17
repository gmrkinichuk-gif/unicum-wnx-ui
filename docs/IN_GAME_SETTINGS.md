# In-game settings development candidate

`0.9.18-dev.1`, branch `feature/in-game-settings`, based on current `main`
(`7435e3b`, rebased after 0.9.17 reached main during development). The verified
0.9.16 base, upstream 0.9.17 optimizations/downloads and existing releases are
unchanged. Local experimental archives were not used as the implementation base.

## Why the window was empty

The supplied client's `game.log` records the failure at 2026-11-17 15:40:12
immediately after `unicum.gg` opens `ModsSettingsApiWindow`:
`view.requestModsData -> api.generateSettingsData`, `KeyError: 'twitchConnect'`.
The API window itself loads; its central data request fails before rendering.
This is independent of the native `unicum.settings.swf` loader.

The installed `izeberg.modssettingsapi_1.7.1.wotmod` replaces its complete
settings dictionary in `updateModSettings()`, then indexes every template
`varName` in `generateSettingsData()`. Unicum's replacement dictionary omitted
the Connect, Reset and link-button variables. All are now present, ignored as
settings on readback, and checked against the template before registration.
The offline installed-bytecode check reproduces the original KeyError when
Connect's key is removed and successfully generates both account states in
both languages with the fix.

Two additional integration errors were found:

- That API's SWF ignores `button` on a `Label`. Action rows now use its supported
  radio-group heading/dynamic-button component with zero radio choices, so
  there is no dummy switch. This needs the final live acceptance check below.
- That package exports the internal API directly, rather than through the
  older wrapper's private attribute. Both shapes are handled for opening and
  detaching callbacks. Repeated registration/language changes retain exactly
  one settings/button callback pair; teardown removes them and the live page.

Live testing also caught the current client's two required arguments to
`ConfirmDialogButtons`. Reset now supplies explicit translated button labels,
and a late answer is ignored after Session teardown.

## Configuration

The existing `mods/configs/unicum/settings.json` remains the only settings file.
Known fields are validated; unknown and legacy keys survive nested saves.
No player configuration or account secrets are shipped in the repository.
The pre-test personal configuration and installed Unicum package were backed
up locally under ignored `build/test-install/`.

`settingsLanguage` is `en` (default) or `uk`. Choose **Settings language** in
the API page or the native tab's General group. Apply/OK saves the selection;
Cancel discards it. The selection translates labels, choices, explanatory text,
tooltips and Reset confirmation in both backends. Channel names, rating codes,
HTML, protocol variable names and saved enum values are never translated.
The game's own bottom buttons follow the game's language.

All original ratings (WN7/WN8/WNX/PR/WTR), rating/WR/battle periods, WR precision,
flags, supported modes/surfaces, Alt visibility, minimap, account/Twitch,
context-menu, replay/loadout and performance options are retained. The native
page also exposes the previously missing master switch and Twitch channel.
Team averages have independent controls and survive a complete API round trip.
Existing upstream battle-reporting behavior is unchanged; hiding a public battle
list does not stop uploads. The Ukrainian tooltip preserves this distinction.

New display fields live under `wnxUI`:

| Object | Fields and defaults | Consumer |
|---|---|---|
| `loading` | `background: true`, `stripe: true`, `opacity: 50`, `wnx: true`, `winrate: true`, `battles: true` | `RosterRows` loading backgrounds/columns |
| `panel` | `background: true`, `stripe: true`, `opacity: 40`, `altStats: "adaptive"`, `animation: true`, `duration: 150` | `RosterRows`, `PanelModes`, `PanelTextSwap` |
| `tab` | `background: true`, `opacity: 40`, `wnx: true`, `winrate: true`, `battles: true`, `names: "light"`, `clans: "light"`, `vehicles: "light"` | Gameface `tab_screen.js` |
| `markers` | `stripe: true`, `missing: "neutral"` | `name_markers.py`, existing `NameMarkerStripe` |

Opacity is 0–100% in steps of 10. Duration choices are 50/100/150/200/250/300 ms.
Alt choices are adaptive, WNX, WR, battles, or all three. Adaptive preserves the
baseline's narrower WNX-only slots. Explicit multi-value selections fit inside
the native text rectangle. Short stays native; Medium/Long/Full use their
existing target fields, and Full retains the vehicle name while Alt is held.
Tab text choices are light/native/WNX; the current player's native highlight,
native contours, Live Tags and tooltip bindings remain. Missing marker WNX is
neutral grey or hidden; disabled/team-filtered markers stay distinct from missing
statistics. The existing label/HP/type-icon collision geometry is unchanged.

## Lifecycle and persistence

The native tab uses the existing Scaleform shell/library, native controls and
scrolling viewport. It shares settings with the optional API; it does not create
a second service-layer view. Seven subtabs group the existing features plus the
four WNX surfaces. There is no HTML settings replacement.

Apply commits and saves; OK commits and closes; Cancel/close discards pending
native edits. Reset asks for confirmation, restores defaults, saves, and clears
stale native drafts. Reset retains unknown extension keys and the account link.
Language changes rebuild the optional API template once without stacking handlers.
Menu delays are Session-owned and cancelled on close. No network requests,
recurring timers or ENTER_FRAME listeners were added for the new controls.
Options only invalidate existing cached row drawing when changed.

Without modsSettingsApi, the mod-menu entry opens the native settings tab.
Without modsListApi, the normal WoT settings tab remains available. Native SWF
load/start failures report through the existing bounded AS3-to-Python log bridge.

## Validation on 2026-11-17

Automated checks on the final candidate:

- Python 2.7 `tools/selftest.py`, including every new display choice, language
  validation/persistence, draft/commit/Cancel/Reset, unknown keys and teardown.
- `tools/check_installed_settings_api.py` against the installed optional API's
  actual bytecode, both account states/languages and direct-instance lifecycle.
- Actual AS3-body fixtures: `check_settings_ui.mjs`, `check_panel_flip.mjs`
  (matching client constants; 24,636 assertions), `check_battle_ui.mjs`,
  and `check_roster_grid.mjs`.
- Headless Edge with the matching client's Tab CSS and native icon assets at
  1280/1366/1920/2560 widths: no errors, including option toggles, opacity,
  native/WNX text colours, Live Tags, death/revival and unchanged-style caching.
- AS3 compilation against installed client 2.4.1.1 and compiled-package
  `tools/release_check.py`. These are fixtures/package checks, not live combat.

Live client observations, on the earlier English candidate before localization:

- `0.9.18-dev.1` started and registered successfully with the optional API.
- The previously empty API window displayed standard settings and WNX controls.
- The native WoT tab loaded its SWF, displayed all seven sections, and scrolled
  without covering the bottom buttons at 1920×1080.
- A changed panel-stripe checkbox followed by Cancel left the file unchanged;
  reopening restored the saved checkbox. Apply wrote `stripe: false` to disk.
- A subsequent startup without the optional API logged the supported native-tab
  fallback. The user then stopped Computer Use with physical Escape before the
  fallback UI/persistence check could complete. The optional API and original
  stripe value were restored. Other mods were not changed.

Still required before merging/releasing:

- Live acceptance of the final dynamic API buttons, Reset confirmation/positive
  Reset, language switching/translated layout, OK and post-restart UI persistence.
- Complete the no-API menu-opening check and test a client without modsListApi.
- Live combat/replay checks for all panel modes, Alt selections/transitions,
  loading/Tab options and marker placement; UI-scale checks beyond the observed
  1920×1080 native layout; sustained reopen/resource-leak measurement.

The final bilingual artifact is in `dist/`; the running game may still have the
earlier test package loaded. Close the client before installing the final file.
No Release or merge is authorized by this candidate.
