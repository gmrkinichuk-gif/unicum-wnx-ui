# WGMods submission assessment

Scope: Unicum WNX UI 0.9.20, WoT EU 2.4.1.1 #993. Checked 2026-11-22
against the [WGMods Mod Hub terms](https://wgmods.net/pages/terms_of_use_portal_en/),
[WoT Fair Play prohibited mods](https://worldoftanks.eu/en/content/guide/fair-play/prohibited-mods/),
[Wargaming Player Content Policy](https://legal.wargaming.net/en/user-documents/content-policies/player-content-policy/view),
[Wargaming EULA](https://legal.wargaming.net/en/user-documents/eula/end-user-license-agreement/view)
and [Wargaming Privacy Policy](https://legal.wargaming.net/en/user-documents/privacy/privacy-policy/view/).

| Area | Evidence and remaining check |
| --- | --- |
| Gameplay and fairness | Retained code displays external historical ratings and client-visible UI data, and computes the account's past-battle WNX locally. The packaged features contain no aim, fire, vehicle control, reload timers, map spotting or visibility automation. The overhead marker integration extends the game's own marker movie. A live check should confirm that client visibility, marker removal, and replay behavior are preserved. Fair Play and the portal's moderation decision still apply. |
| Privacy | The three HTTPS paths, exact identifier fields, local records and deletion steps are listed in [PRIVACY.md](../PRIVACY.md). Release checks reject credential-bearing, upload and non-core requests. Identifier queries to Unicum.gg are still transfers. This mod does not call the Wargaming Public API directly; the privacy policy's discussion of community apps is not a blanket authorization. The [WG API Terms](https://developers.wargaming.net/documentation/rules/agreement/) set separate conditions on use and onward handling of API data. Provider rights, server retention and the treatment of indirect API-derived data require provider or moderator confirmation. |
| Copyright and attribution | Upstream AGPL source and notices and OpenWG Gameface MIT terms are retained. Provide matching corresponding source with the binary. The installer includes a modified copy of the client's `battleVehicleMarkersApp.swf`. The Player Content Policy permits creating and sharing mods subject to the EULA. That general permission does not settle whether this complete patched client file can be redistributed in this form. Obtain Wargaming's confirmation for this payload, or generate the patch on the user's own client without redistributing the original movie. |
| Listing content | Use screenshots with fictional or redacted names/identifiers and a truthful compatibility and data-use description. Keep the source attribution and Wargaming non-endorsement notice. The portal forbids prohibited mods, malware, unauthorized copyrighted material, disclosure of personal data, unreleased client assets and unrelated content. |
| Submission mechanics | WGMods pre-reviews submissions and requires a signed-in Wargaming account. Its public terms §4.1 call for an accessible Russian translation when posting materials in other languages. §4.2 refers to file-type and size limits without stating the actual limits. Confirm those limits in the signed-in form for the chosen listing and upload. |
| Release license | The root AGPLv3 and third-party notices are present. The new [release license notice](../RELEASE_LICENSE.md) explains the existing rights, Wargaming attribution, provider transfers and limits; release build and tests enforce its inclusion in both distribution archives. It does not create an AGPL-incompatible click-through EULA, legal consent or retroactively change published assets. |
| Consent and provider data | The current release discloses HTTPS account-ID queries but does not provide a separately gated, affirmative first-run choice before third-party requests begin. In particular, it can send other players' numeric account IDs. Disclosure alone is not consent, and legality/provider terms should be confirmed with moderators. Implement a real opt-in only after agreeing to the required UX and default-disabled network behavior; do not label a static notice as opt-in. |
| API-policy presentation | The Wargaming API policy includes copyright attribution, official-game and support links and anti-advertising requirements for covered API applications. This client mod does not directly invoke WG API; whether the same obligations apply to indirect Unicum.gg-derived data needs confirmation. The documentation now includes Wargaming attribution and official links; an in-game support button has not been added. |
| Release listing | A copy-ready [English and Russian listing](WGMODS_LISTING.md) covers compatible build, features, dependency, outbound account identifiers, local history, AGPL and source links. Confirm portal field limits and provide real sanitized screenshots. |

**Status:** documentation / release-builder update proposed; not a new WGMods submission.
The published v0.9.20 assets have not been rebuilt or replaced. This is a
source and package review, not Wargaming approval or confirmation that all
portal criteria are met. Resolve the patched-client-file rights and the
third-party identifier transfer question before resubmitting.
