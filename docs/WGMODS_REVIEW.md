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

**Status:** not submitted. This is a source and package review. It is not a
Wargaming approval or a confirmation that all portal criteria are met.
