# Contributing

Read [AGENTS.md](AGENTS.md) and [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
Keep Python game code compatible with 2.7 and preserve Session ownership and
teardown. Use small commits describing the actual change. Existing upstream
history uses gitmoji; it is not required for this derivative. Do not add
generated-by notices or co-author footers.

Run the Python 2.7 selftest before committing; for release packages run
`release_check.py` as well. Run the relevant UI checks after interface changes.
Some API checks depend on the service and explicitly skip when unreachable;
report skips as such. Review `game.log` after actual client changes locally,
but never commit the log. Document the client version and unverified behavior.

Retain upstream notices and describe modifications and dates in CHANGELOG.md.
Never commit credentials, personal configuration, replay data, build outputs,
SDKs, node_modules or client binaries. Review `git diff --cached` and
`git status --short --untracked-files=all` before pushing. Release publication
requires a separate explicit decision after in-game validation.
