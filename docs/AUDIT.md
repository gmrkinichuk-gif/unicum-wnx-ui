# Initial publication audit - 2026-11-16

## Scope and provenance

Prepared from `source_modified` in a separate clone of
`gmrkinichuk-gif/unicum-wnx-ui`, confirmed private with default branch `main`.
The original source snapshot and working source were only read; no compiler,
installer or packager was run against them. Preparation scripts and local
audit logs are outside the publication source set.

The supplied baseline CHANGELOG starts at 0.9.0; the modified CHANGELOG and
existing package names establish 0.9.15. Runtime sources deliberately contain
development placeholders; build_release.py injects the actual version in its
temporary staging tree. The installed client's paths.xml specifies 2.4.1.1.
No upstream Git commit ID was supplied. UPSTREAM_DELTA.json records the
source delta without copying source_original.

## Publication contents

Includes Python runtime and embedded web resources, AS3 sources and stubs,
bootstraps, resource maps, source artwork, build/install tools, regression
checks, npm lockfiles, original MIT openwg_gameface 1.2.2 and its license,
English documentation, provenance, licenses and two GitHub Actions workflows.

Excludes original source copies, old release archives, compiled mod outputs,
SDKs, bundled Python installers, node_modules, bytecode, caches, private logs,
game dumps, personal settings, account links, replay files and screenshots.
The one intentional vendored binary is MIT-licensed openwg_gameface, required
by the upstream installation ZIP builder. It is not a temporary mod build.

Upstream release PR, automatic Release and wgmods publishing scripts were
omitted because they target the upstream repository or listing. CI has only
read access and publishes no releases. The manual candidate workflow stores
an Actions artifact for client testing. Repository privacy is unchanged.

## License review

The complete local LICENSE matches the live upstream main LICENSE after
normalizing line endings, including Antoine Kingue's copyright notice.
It remains unchanged. NOTICE identifies the derivative and preparation date.
Direct dependency license texts, exact npm lock versions and transitive
license declarations are retained in licenses/, THIRD_PARTY_NOTICES.md and
DEPENDENCIES.json. Required notices now also travel with generated packages.
No incompatible license declaration was found in the included source set.

External Wargaming client files and playerglobal are build inputs under their
own terms, not source relicensed by this repository. Client-derived binaries
remain local; their distribution terms and matching AGPL Corresponding Source
access must be addressed before distributing to recipients. This source import
does not authorize or create a public Release.

## Local verification from the new clone

| Check | Result |
| --- | --- |
| npm ci, tools/flags and tools/badges | Passed with committed lockfiles |
| Flag generation | Passed: 252 PNGs |
| Icon generation | Passed |
| Apache Royale / Java 17 AS3 build | Passed; actual installed client's SWCs and markers movie |
| Python 2.7 selftest | Passed: 873 assertions; no explicit API skips |
| Python 2.7 compiled-package release_check | Passed: 23 assertions |
| Mirrored loading grid fixtures | Passed: 8 layouts |
| Battle UI method/geometry checks | Passed |
| Alt panel animation/native mode fixtures | Passed: 24,636 assertions |
| Browser Tab / Live Tags check | Passed: no errors at 1280, 1366, 1920 and 2560 widths |
| actionlint 1.7.12 | Passed |

Optional browser and panel-mode checks read developer-provided client CSS,
icons and a library dump externally. None of these fixtures is committed.
The SDK cache was reused, but all mod SWFs and Python bytecode were rebuilt.
The build did not use --install, did not launch the game and did not alter the
installed client's files. Successful fixtures are not in-game validation.

Local ignored outputs: `dist/gg.unicum_0.9.15.wotmod` and
`dist/unicum.gg_0.9.15_wot_2.4.1.1.zip`. License presence, Python 2.7 magic,
archive integrity and resource layout were checked. Digests are recorded in
ARTIFACTS.json for this local audit; these are not published release assets.

## Security and Git review

The exact index export passed Gitleaks 8.30.1 with zero findings using its default rules,
with redacted output. Common credential assignments and sensitive filenames
were also inspected manually. Source occurrences of token/secret/password
refer to runtime credential handling, environment variable names or explicit
test fixtures; no personal credential stores or local settings are included.
The vendored openwg archive was enumerated and scanned after extraction too.
The final scanner outcome and staged-file totals are in PUBLICATION_CHECK.json.
This is a point-in-time scan, not a guarantee against every possible secret.

git diff --cached --check and the full staged path list were reviewed before
commit. No forced push, tag creation, Release creation, mod-hub upload or
repository visibility change is part of this publication.
