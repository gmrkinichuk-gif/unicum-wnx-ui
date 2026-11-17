# Update 0.9.17 — 2026-11-17

Target: World of Tanks EU 2.4.1.1. Original mod: unicum-gg/unicum.gg-mod.

## Changes

- Guard unchanged Scaleform roster x/width, text wrapping, multiline, autoSize,
  alpha and statistics x/y assignments. Real native changes are still repaired.
- Extend the existing opt-in performance meter with timestamps for calls >=16 ms.
  Retain at most 64 primitive records and batch at most eight log entries on the
  existing report interval. No stack/frame/engine objects are retained.
- Add bounded-record/disabled-meter and stable-geometry regression checks.
- Keep WNX thresholds, colour bands, requests and caches unchanged.

## Validation

The local candidate passed the Python 2.7 suite (874 assertions), AS3 build
against eight installed-client SWCs, battle UI checks and release structure
checks. The package contains 400 stored entries; 213 original Python modules
were verified unchanged. These checks do not establish visual correctness.\nA publication-time rerun passed the UI fixture and release check, but the full\nselftest stopped at the live-service assertion `FAIL clan resolved`. The\nprevious 874-assertion pass is historical; a fresh full pass is not claimed.\nThe changed geometry and bounded-meter assertions passed before this failure.

One 180-second live-battle PresentMon capture contained 11,885 frames. The
largest Present interval was 1238.99 ms during hangar-to-battle initialization;
four intervals exceeded 500 ms. After the first 60 seconds of the recording,
8,613 frames had P99 23.49 ms, maximum 48.08 ms and no interval >=50 ms.
This is one observation, not an FPS comparison or proof that freezes are fixed.
Measured Python hooks did not explain the largest interval; engine/UI/native
waits are outside this profiler. Exact root cause remains unresolved.
Further tracing was deferred at the maintainer's request. No replay FPS
comparison was used for 0.9.17. Raw logs, player identities and traces are private.

Performance measurement defaults to false and was disabled again after testing.
Previous installed 0.9.16 and settings were backed up locally before installation.
Complete in-client UI regression validation remains outstanding.

## Distribution

See downloads/0.9.17 for the tested binary, install ZIP, matching source archive
and SHA256SUMS.txt. Existing source/CI publication improvements remain in main.
The source archive preserves the exact local build inputs, including their
historical build scripts; it contains no personal configuration or game logs.
