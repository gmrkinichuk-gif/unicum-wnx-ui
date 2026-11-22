# Privacy and data use

Applies to Unicum WNX UI 0.9.20. This document describes the mod itself and
the two services it contacts. Wargaming publishes its own
[Privacy Policy](https://legal.wargaming.net/en/user-documents/privacy/privacy-policy/view/).

## Data sent by the mod

| Recipient and endpoint | Data sent and purpose |
| --- | --- |
| Unicum.gg — `GET /api/{region}/resolve` | Region code in the path. The query can contain numeric WoT account IDs in `players`, including your own and other players shown in the battle roster, and numeric account ID/vehicle descriptor pairs in `vehicles`. Vehicle queries can carry a battle-mode code in `mode`. These fields are used to retrieve the WNX ratings and game statistics used by the UI. |
| Unicum.gg — `GET /api/ratings/scales` | Public colour-scale request with no query parameters. |
| Tomato.gg — `GET /api/wnx/wnx-expected-values.json` | Public expected-vehicle-values request with no query parameters. The Tracker uses the returned table to calculate session WNX locally. |

The destinations can receive your IP address and ordinary connection
metadata as part of serving requests. Numeric account IDs are identifiers,
even without player nicknames. The mod uses HTTPS GET requests without
request bodies or custom authorization headers. It does not transmit
passwords, Wargaming tokens, nicknames, clan IDs or tags, chat, replays,
vehicle loadouts, the local battle journal or crash reports. No in-game
account linking or Twitch integration is shipped. Each provider controls its
own server logs and retention. This project cannot verify or promise either
provider's deletion schedules.

## Data held on your computer

- Ratings and returned statistics indexed by other players' account and
  vehicle IDs are kept in memory for the current client session. Version
  0.9.20 does not persist that lookup cache. The game resource cache may
  contain generated badge PNGs with displayed numeric values and colours.
- `mods/configs/unicum/settings.json` stores mod preferences.
  `mods/configs/unicum/scales.json` and
  `mods/configs/unicum/wnx_tracker/expected.json` cache public tables.
- `mods/configs/unicum/wnx_tracker/<region>/<account-id>/history.jsonl`
  retains up to 60 valid random battles for your own account. The journal
  uses region, account ID, arena ID, battle type, start time, vehicle
  descriptor, result, damage, radio and tracking assist, kills and spotted
  count. Reset bookkeeping and recovery copies may also exist in that
  account directory. The mod does not record other players' results in it.
- Normal diagnostics may appear in the local client log. Older builds can
  leave separate files on disk; 0.9.20 does not erase those automatically.

Use the Tracker gear and **Reset statistics** to reset the active account's
Tracker. To clear its journal, reset bookkeeping and recovery copies entirely,
close the game and remove that account's directory shown above. The game does
not need these files. To stop all of this mod's requests, close the game and
remove its active `gg.unicum.wnxui_*.wotmod` package. Display switches alone
do not stop the Tracker's hangar rating lookup or public data refreshes.

For questions about the mod, contact its maintainer through the repository's
support channel. Use the relevant provider for questions about data it
received. Avoid posting account identifiers, raw battle history or unredacted
client logs in public discussions.
