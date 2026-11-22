# Unicum WNX UI — release license and user notice

This notice accompanies the installable World of Tanks mod. It **explains the existing license**; it is not a separate restrictive end-user license agreement, a click-through contract, or a substitute for the complete license. It does not reduce any rights granted by the GNU Affero General Public License version 3 (AGPLv3).

## 1. License and source code

The Unicum WNX UI program is a derivative of [Unicum.gg's client mod](https://github.com/unicum-gg/unicum.gg-mod) and is distributed under the **GNU AGPL version 3**. You may run, study, share and modify the AGPL-covered code under the conditions of the full [LICENSE](LICENSE). This includes the conditions for distributing modified versions, making matching Corresponding Source available to binary recipients, and preserving copyright and license notices.

For a published binary, obtain the corresponding version's source from the [GitHub Releases page](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/releases) or the matching Git tag. Check that the source corresponds to the exact binary you received. The license and source obligations apply to the `.wotmod` as well as to the installable ZIP; an archive's filename does not change the license.

Copyright and third-party credits are documented in [NOTICE](NOTICE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). OpenWG Gameface is an MIT-licensed, separately credited component. The AGPL does **not** grant rights to Wargaming's game assets or any third party's trademarks.

## 2. What the installed mod does with data

When active, the mod sends HTTPS GET requests to **Unicum.gg** to display WNX ratings. Queries can include numeric account IDs for **other players in a battle**, not only your own account, and numeric account/vehicle identifiers and game-mode codes. It also downloads public WNX colour scales from Unicum.gg and public expected-vehicle-value data from **Tomato.gg**. Those services receive normal network metadata, including your IP address, and manage their own server logs and retention.

The current release does **not** upload chat, replays, battle-result files, loadouts, your Wargaming password or Wargaming authentication token. It does **not** call the Wargaming Public API directly. Your own Tracker history is stored locally, with a rolling limit, and is not uploaded by this mod.

These requests can occur when the mod is running; **installing the mod does not provide a separate opt-in consent control**. Disabling an on-screen overlay does not necessarily stop background rating requests. To prevent the mod's network requests, remove the mod before launching the game. See [PRIVACY.md](PRIVACY.md) for the exact endpoints, local file locations, reset options, deletion instructions and limits of what the maintainer can know about external providers.

## 3. No Wargaming affiliation or approval

World of Tanks and Wargaming names, trademarks, game assets and related rights belong to their respective owners.

**© Wargaming.net. All rights reserved.**

This work includes trademarks and/or copyrighted works that are the exclusive property of Wargaming. All rights reserved by Wargaming. This work is unofficial and is not endorsed by Wargaming.

Official game website: https://worldoftanks.eu/

Official Wargaming support: https://eu.wargaming.net/support/

Neither a public GitHub release nor this document constitutes WGMods approval or permission to redistribute game-client assets. Use and distribution of modifications remain subject to Wargaming's applicable rules, the game's EULA, and fair-play requirements.

## 4. No warranty

The AGPL-covered program is provided **without warranty** to the extent permitted by applicable law; see sections 15–17 of the full AGPLv3. This notice does not limit rights or remedies that cannot lawfully be excluded. Third-party components remain subject to their own license terms.

For project issues, use the [GitHub issue tracker](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/issues). Do not post account IDs, settings files, tokens or raw game logs publicly.
