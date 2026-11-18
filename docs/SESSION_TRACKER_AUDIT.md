# Session Tracker audit — 2026-11-17

Base: origin/main `2b4269d6da9cd77d1931af9b10b4978e61f02c0a`, release 0.9.18.
The implementation branch was later rebased onto `1f3a482`, which only adds
0.9.18 documentation and screenshots.
Branch: feature/wnx-session-tracker. The supplied TECHNICAL_SPEC_UK.md takes
precedence over the English-only convention and conceptual reference controls.
Both approved PNGs were inspected; the in-client width budget is 320 logical px.

## Confirmed architecture

* Reporter wraps BattleResultsService.postResult and also receives claimed/cache
  results in _record. Its upload gate precedes extraction. A guarded local
  consumer must run first in _record, independently of settled/upload queues.
* The real replay-derived RESULTS fixture identifies participants with
  vehicles[].accountDBID, tank with typeCompDescr, time with arenaCreateTime.
  Account.databaseID is already used by game_link/proof.py. Names are not identity.
* modes.py maps named client constants, including REGULAR/RANDOM_NP2/EPIC_RANDOM.
  Tracker follows that random mapping and rejects replay playback.
* Shared Lookup/Entry provides total.wnx; RatingScales supplies the only colour
  thresholds. Existing recent ratings cannot represent a local N-battle window.
* Settings validates and recursively preserves unknown keys; native_page and
  codec already cover the original controls, account actions and WNX surfaces.
* LobbyView is the single service-layer view. Add child sprites there, not a
  competing view. Python/Flash communication uses callable drain methods because
  GFx caches getter results. Session owns callbacks/patches/subscriptions.
* Native settings tab remains the emergency recovery path. Remove the tray entry
  only after the custom window acknowledges opening; never remove the fallback.

## Formula and expected values

Upstream checked at `65f19c009bf434bb2c0c9061183b12c743f856fd`:
[ratings.ts](https://github.com/unicum-gg/unicum.gg/blob/65f19c009bf434bb2c0c9061183b12c743f856fd/packages/shared/src/wot/ratings.ts),
[wn-expected.ts](https://github.com/unicum-gg/unicum.gg/blob/65f19c009bf434bb2c0c9061183b12c743f856fd/packages/core/src/wargaming/wot/wn-expected.ts).
Both repositories are AGPL-3.0. Port and fixtures retain attribution.

Unicum.gg uses https://api.tomato.gg/api/wnx/wnx-expected-values.json directly.
HTTP GET succeeded; response is {meta:{status,updated},data:[{tank_id,
expected_damage,expected_frags,expected_spots,expected_assistance,is_fallback}]}.
The same numeric tank ID domain is used by the upstream per-battle rating path
and this client's typeCompDescr (e.g. fixture tank 6209). Validate individual
mapping against the game's vehicle encyclopedia during live acceptance.
Do not derive alternative expectations or exclude origin rows upstream uses.
No public client endpoint SLA or separate redistribution licence was confirmed.
Therefore do not bundle a third-party snapshot: fetch the verified public origin
in the garage at most daily, cache validated rows with source date and content
hash, retain stale cache offline, show unavailable without a usable table.
No local history is transmitted to this origin.

## Implementation order / dependencies

1. Pure formula + upstream numerical fixtures; strict own-result extraction.
2. Per-region/account versioned durable journal (200 retained records), dedupe,
   reset watermark and corruption recovery; consumer before uploader gate.
3. N/2N readiness, aggregate rolling points, individual bars and tooltip model.
4. Existing LobbyView child widget; bounded geometry, hover, drag and lifecycle.
5. Five-category custom glass window using the complete existing field catalog;
   separate draft, Apply/OK/Cancel, shared theme, localized reset confirmation.
6. Regression suite, actual AS3 compilation, package checks, candidate and live
   checklist. No merge, public release, WGMods upload or automatic installation.

Dependencies already available: Python 2.7 runtime, Python 3 build tools, Java,
Royale compiler, client SWCs and installed WoT EU. New code needs no optional
modsSettingsApi/modsListApi and no additional runtime libraries.

## Risks and verification limits

Replay-derived fixture is real data, but a current live postResult capture is
still needed for account switch/anonymous-player cases. Missing identity or
metrics must never silently become zero. In-flight reset uses battle start time,
so a battle started before reset is deliberately excluded even if received later.
Journal append is small and fsynced; storage failures remain visible and retriable.
Flash rendering, native focus, hover placement, UI scaling, optional-mod matrix,
real battles and sustained performance require live-client acceptance. Compilation
and simulated fixtures alone are not evidence that those live cases passed.
