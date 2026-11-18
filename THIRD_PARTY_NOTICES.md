# Third-party notices

The main project retains upstream GNU AGPL v3. Dependency licenses below were
checked against the supplied license files and exact npm lockfile versions on
2026-11-16. Do not infer that external client files inherit the mod's license.

| Component | Version / license | Use and provenance |
| --- | --- | --- |
| openwg_gameface | 1.2.2 / MIT | Bundled runtime; original binary and Andrii Andruschyshyn notice in `vendor/openwg/` |
| react-flagpack | 2.0.6 / MIT | Yummygum flag artwork rasterized by tools/flags; `licenses/react-flagpack.txt` |
| Phosphor Icons Core | 2.1.1 / MIT | Hangar icon artwork; `licenses/phosphor-icons.txt` |
| Roboto Condensed | @fontsource 5.3.0 / OFL-1.1 | Google font used to generate badge masks; `licenses/roboto-condensed.txt` |
| opentype.js | 2.0.0 / MIT | Font parser used only by glyph tooling; `licenses/opentype.txt` |
| sharp | 0.34.5 / Apache-2.0 | Build-time rasterizer; `licenses/sharp.txt` |
| libvips and sharp native packages | Lockfile platform variants / LGPL-3.0-or-later and other bundled terms | Build tools only; not shipped in game packages; preserve their installed notices if redistributing tools |
| Apache Royale | 0.9.12 / Apache-2.0 plus distribution notices | Downloaded compiler only; `licenses/royale-NOTICE.txt`; complete distribution terms remain with the SDK |
| Python, Node.js, Java | External interpreters and build tools | Not vendored or shipped; retain their distribution licenses when redistributing them |
| playerglobal and WoT SWCs | External SDK/client terms | Compilation inputs linked externally; not included in this Git repository |
| WoT battleVehicleMarkersApp.swf | External Wargaming client terms | Read from a matching client and patched only in ignored build output |
| Unicum.gg WNX implementation | AGPL-3.0, Antoine Kingue | Python port and numerical test oracle from [ratings.ts at 65f19c0](https://github.com/unicum-gg/unicum.gg/blob/65f19c009bf434bb2c0c9061183b12c743f856fd/packages/shared/src/wot/ratings.ts) |

The Tracker requests the public Tomato.gg expected values endpoint used by
Unicum.gg and keeps the response in the client's local cache. The candidate
does not redistribute a copy of the table.

Full npm dependency inventory, including transitive and optional platform
packages, is in [docs/DEPENDENCIES.json](docs/DEPENDENCIES.json). MIT, ISC, 0BSD,
Apache-2.0 and LGPL tooling declarations do not replace those packages' full
license conditions. No npm runtime or native library is embedded in the mod.
Roboto raster masks retain the accompanying font notice; the font itself is
not bundled. The upstream integration logos retain their owners' trademarks.

Release packaging includes these notices and license texts in the `.wotmod`
and a top-level `licenses/` directory in the installation ZIP. The openwg MIT
notice is also placed beside its bundled binary.
