# Release procedure

No release is published automatically. The initial import creates only a Git
commit. There are no tag-triggered publishers, scheduled release PRs or calls
to the upstream wgmods service. Removed upstream tools targeted its repository
or mod-hub ID and must not be reused for this derivative without adaptation.

1. Use the version at the top of the CHANGELOG (currently 0.9.20); bump it
   only for a deliberately versioned change.
2. Build from a matching installed EU client with README's commands, or run
   the manual `candidate` workflow with the current version. It reads the live
   client through the inherited client-files action. A candidate is an Actions
   artifact, never a Release. Record the client manifest and SHA-256 digests.
3. Run the packaging unit tests, compiled-package release_check and UI checks. Pass both
   `dist/gg.unicum.wnxui_<version>.wotmod` and
   `dist/unicum.gg_<version>_wot_<client version>.zip` to release_check so it
   verifies the new Package ID, filenames and installer content. Review skips.
   Confirm the versioned `.wotmod` contains `res/licenses/unicum/RELEASE_LICENSE.md`
   and the installer contains `licenses/unicum/RELEASE_LICENSE.md`, alongside the
   full AGPL, upstream notices, third-party licenses and privacy disclosure.
4. Test the candidate in WoT using [BETA_VALIDATION.md](BETA_VALIDATION.md):
   both teams, panel modes, loading, Tab, native Live Tags and tooltips, Alt
   changes, own/dead/hidden players, missing and late ratings, overhead markers
   and the installed modpack. Record pass/fail/not-tested evidence.
5. Record the game validation evidence and maintainer's publication decision.
   Review the data-use notice and license obligations for the patched client
   movie and bundled components. See the [WGMods assessment](WGMODS_REVIEW.md).
   Check the [WGMods listing draft](WGMODS_LISTING.md) and do not imply this
   written disclosure substitutes for runtime opt-in or game-asset permission.
6. Only then create a tag and GitHub Release manually, attach the verified ZIP,
   `.wotmod`, manifest and checksums, and provide matching Corresponding Source
   to every recipient. Do not replace verified assets with mirror-built output.

Repository visibility is a separate maintainer decision. On 2026-11-16 the
maintainer explicitly requested public source access together with the 0.9.16
update. A public repository provides source access; publishing a binary Release
still follows the validation and license steps above.

The CI `build` workflow uses mirrored client files solely as a compiler and
packaging regression check. Its temporary game version is a CI sentinel, not
a supported client or mod version. No CI package from that workflow is uploaded.
The candidate workflow uses the actual CHANGELOG version and live client files.
Both workflows use read-only repository permissions.

Package identity is `gg.unicum.wnxui`, and the installer embeds
`mods/<client version>/gg.unicum.wnxui_<version>.wotmod`. The installer ZIP's
existing `unicum.gg_...zip` name and shared `net.openwg/` dependency stay the
same. A different Package ID does not allow coexistence with upstream:
follow [PACKAGE_IDENTITY.md](PACKAGE_IDENTITY.md) and remove old release/dev
packages before client testing. Keep published release URLs, archived binaries,
checksums and historical validation reports unchanged. Rebuilding an existing
version is a local check, not authorization to replace its published assets.
