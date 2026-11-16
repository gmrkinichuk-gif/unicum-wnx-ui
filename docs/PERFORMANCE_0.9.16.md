# Performance update 0.9.16

Date: 2026-11-16. Target: World of Tanks EU, resource directory `2.4.1.1`.
This update preserves the existing Unicum.gg rating API, WNX thresholds, RGB
bands, cache/network behavior and supported roster features.

## What changed and why

- Tab now remembers both requested and browser-canonicalized inline CSS values.
  Comparing `#RRGGBB` or a source gradient with a normalized browser value had
  caused 120 unchanged property writes every 200 ms (about 600 writes/second).
  The new code also repairs a subsequent native overwrite and restores original
  styles when stopped. Native Live Tags geometry reads run after all row writes.
- Overhead marker badge geometry is cached until its native field, text or
  layout changes. Stripe geometry no longer serializes complete `htmlText` on
  every frame. Display properties are assigned only when needed. The marker
  addon reuses its layout function and checks anchor replacement every six
  frames; layout itself continues every frame.
- Retained hidden, fully transparent or detached Scaleform roster branches skip
  row processing. Visible branches retain the existing 20 Hz refresh.
- Python marker payloads are prepared once per account and reused while the API
  Entry and scale timestamp are unchanged. Settings changes clear this cache.
  Alt, team selection and disabled/missing-rating sentinels are evaluated on
  every sync, independently of the prepared payload.

## Local replay comparison

The same saved replay and installed modpack were used. The client was restarted
between versions. Native debug-panel arguments provided smoothed current FPS
and the FPS recorded in the replay. `BattleReplay.currentTime` aligned samples.
Graphics settings were not edited for the experiment. The final candidate and
0.9.15 were compared over replay seconds 20 through 150, excluding loading and
countdown. The original first CSV was lost after a client restart; a fresh
0.9.15 control was captured instead. No missing samples were reconstructed.

| Metric | 0.9.15 | 0.9.16 final |
|---|---:|---:|
| Native samples | 601 | 621 |
| Mean sampled FPS | 69.58 | 70.42 |
| Median sampled FPS | 70 | 71 |
| P10 sampled FPS | 66 | 69 |
| Minimum individual sample | 52 | 45 |

Across 130 shared one-second replay bins, mean FPS difference was +0.87 and
median difference +0.50. Mean absolute difference in the recorded-replay FPS
control was 0.23 FPS. Typical FPS improved slightly in this run, but the lower
isolated minimum shows that this does not establish elimination of all stalls.
Only one control and one final run were captured; foreground/camera constancy
was not independently recorded throughout every sample. These results should
be treated as a local observation, not a statistically established FPS gain.

The existing Python game-thread profiler reported these means during the
corresponding replay intervals (13 reporting windows per run):

| Python metric | 0.9.15 | 0.9.16 final |
|---|---:|---:|
| Total mod game-thread time | 2.40% | 0.96% |
| `NameMarkers._sync` | 13.19 ms/s | 2.56 ms/s |
| `TabScreen._check` | 1.37 ms/s | 0.91 ms/s |

This profiler does not measure AS3/Gameface CPU. In browser fixtures, an
unchanged poll fell from 120 inline property writes to zero. Total style writes
in the late-update/death/Live Tags scenario fell from 1994 to 312.

PresentMon could not start its ETW trace without additional Windows rights.
No permissions were changed. These native samples are smoothed FPS readings
at about 5 Hz, not per-frame timing or 1% lows. Whole-process CPU was not stable
between launches and is not used to claim an engine/GPU improvement.

## Validation and limits

- AS3 compilation against eight SWCs from the installed client passed.
- Python 2.7 compiled-package `release_check.py` passed. The tested workspace
  archive held 400 uncompressed entries with current SWF/JS/CSS/Python resources.
- Battle UI fixtures passed: panel bounds/cache, normal/Alt marker text,
  simultaneous labels, HP/type obstacles, missing/late WNX and disposal.
- Browser Tab fixtures passed at 1280, 1366, 1920 and 2560 widths: native
  Live Tags and tooltips, both teams, long names, late model data, killed/revived
  rows, icon identity, no duplicate statistics and teardown.
- The original sandboxed Python run stopped at the online `clan resolved`
  assertion after `resolve HTTP 0`. Before this GitHub update, the integrated
  source was checked again with network access: all 869 Python 2.7 assertions
  passed, including the live API checks, with zero explicit skips.
- The final replay loaded the marker classes/view, Tab's 30 rows with 26 WNX
  matches, and native Live Tag updates. Every Alt/panel mode was not manually
  exercised again in the final replay; fixtures and the previously accepted
  0.9.15 functionality remain the evidence for those modes.

Static inspection of 39 installed `.wotmod` packages found no overlapping
Python/SWF/JS/CSS resource paths. Both Unicum and the installed sixth-sense mod
reference `createMarker`; this is a possible shared hook, not proof of a conflict.
Three `BattleStatisticsDataController` restoration warnings occur during
shutdown in both versions. Their runtime replacement owner remains unresolved;
this update does not claim to repair that existing teardown interaction.

## Tested workspace artifact and rollback

The installed local `.wotmod` was version 0.9.16 with SHA-256:

`7c0de94138363ce44d2c94468c3f7676277fd21a3c583d5ca4d808e997c6c896`

This identifies the tested workspace build. A build using the repository's
additional license/packaging preparation can have a different digest; it must
be checked and tested independently before being offered as a binary Release.
No compiled client-derived movie, personal replay, raw game log, account file
or temporary FPS probe is included in this source update. Existing license
notices and release procedures remain in place.

The previous installed 0.9.15 was retained locally. To roll back an installation,
close WoT, replace only the Unicum package with the backed-up version, and keep
shared dependencies needed by other mods. After measurements, the temporary
probe was removed and `measurePerformance` was restored to `false`.
