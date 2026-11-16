# Beta validation checklist — 0.9.16

**Status:** pre-release testing plan, not evidence that all tests passed. No binary GitHub Release is authorized by this checklist.

**Target:** World of Tanks EU client resource directory `2.4.1.1`. Other client versions and modpacks have not been certified. Use an isolated test setup when possible.

## 1. Identify the candidate

- [ ] Confirm the commit SHA, mod version (`0.9.16`), target client version and candidate build source.
- [ ] Confirm GitHub Actions `build` checks passed. **Never distribute its mirror-built output**: that workflow is a compile regression test only.
- [ ] Run the manually dispatched `candidate` workflow or build with the matching installed EU client. A `candidate` Actions artifact is *not* a GitHub Release.
- [ ] Record SHA-256 hashes for the candidate `.wotmod`, installation ZIP and client manifest. Confirm the ZIP contains the expected `mods/<client version>/` layout and required license notices.
- [ ] Run Python 2.7 `selftest.py`, `release_check.py` on the candidate package, and relevant UI checks. Record any skipped network-dependent checks explicitly.
- [ ] Treat `docs/ARTIFACTS.json` and `docs/PUBLICATION_CHECK.json` as **historical 0.9.15 initial-import reports**; their hashes and version do not certify the 0.9.16 candidate.

## 2. Install cleanly

- [ ] Close WoT; back up Unicum settings and the previous working mod package.
- [ ] Install **one** Unicum version. Do not run the dev bootstrap or another `gg.unicum_*.wotmod` alongside the candidate.
- [ ] Check compatibility with the installed modpack, especially any mod changing `battleVehicleMarkersApp.swf`.
- [ ] Launch the game and inspect `game.log` for Unicum startup failures, AS3/Scaleform errors and leaked hooks. Keep private game logs out of Git.

## 3. Visual checks inside the game

Test **both teams**, short and long names, clan tags, late-arriving ratings and missing WNX. Use screenshots from the actual game rather than mockups.

### Loading screen

- [ ] Each player's tinted background has consistent height and width within its team, independent of name length.
- [ ] Clan emblems and vehicle icons remain inside their intended row boundaries.
- [ ] Nicknames use available space without aggressive double-sided truncation.
- [ ] WNX accent is on the **left for allies**, **right for enemies**.
- [ ] Unknown WNX uses a neutral readable treatment, not a fabricated zero or a misleading rating colour.

### Battle team panels (“ears”)

- [ ] Check all **four native panel modes**; the icon-only mode remains functional.
- [ ] In the three text modes, normal-state content matches the chosen mode; the WNX accent is on the **right for allies**, **left for enemies**.
- [ ] Check the documented Alt text substitution (Medium/Long: WNX; Full: WNX, WR and battles). In Full, verify the **tank name remains visible while the nickname slot changes**.
- [ ] Holding Alt changes the intended text slot; releasing Alt restores it. There is no overlap, layout jump, duplicate overlay or unnecessary network request.
- [ ] Exercise quick Alt presses, mode switches while Alt is held, Alt+Tab, loss of focus, battle exit and re-entry.
- [ ] Tints and accents have consistent dimensions across all player rows.

### Tab scoreboard

- [ ] The new layout actually appears, populated with WNX, win rate and battles for both sides where available.
- [ ] Nicknames, clan tags, tank names, ranks and vehicle contours do not overlap or disappear.
- [ ] Allied/enemy row geometry and WNX accents are mirrored correctly, with native icons and medals inside the row.
- [ ] Native allied Live Tags, leader updates and tooltips work and are not obscured.
- [ ] Current-player and destroyed-player styles remain readable; unknown WNX stays neutral.

### Overhead vehicle markers

- [ ] WNX accent follows the correct vehicle/Alt nickname label and does not cover HP, vehicle/type information or other native markers.
- [ ] Late-arriving and missing WNX, friendly/enemy filtering, destroyed vehicles and marker teardown behave correctly.

## 4. Stability and performance

- [ ] Compare the same replay scenario with the last known-good version, with comparable settings; note FPS distribution and visible stutters, not just a single average.
- [ ] Review `game.log` after an entire battle and after returning to the hangar.
- [ ] Verify no accumulating UI instances, callbacks, animations or duplicated network requests across repeated battles.
- [ ] Do not treat fixture checks, mirror compilation or one replay run as proof of general FPS improvement.

## 5. Release gate and evidence

Record: commit SHA, candidate SHA-256, EU client version, installed modpack, test date, exact panel modes, screenshots, relevant log errors and **pass / fail / not tested** for each section above.

**Do not publish a binary Release** until the candidate has been tested in-game and explicitly approved, and redistribution of patched client-derived components and matching AGPL Corresponding Source has been reviewed. Tag and upload only the exact approved candidate; never substitute a mirror-built package.

If testing fails, open an issue with reproduction steps and sanitized evidence, fix it in a separate branch, then rebuild and retest a new candidate.
