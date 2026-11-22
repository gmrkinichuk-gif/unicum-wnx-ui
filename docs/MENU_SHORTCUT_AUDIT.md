# Standalone settings shortcut: findings and temporary policy

Date: 2026-11-18. Baseline: `7b7a9b9`; inspected the current working tree,
the installed candidate and the local WoT EU 2.4.1.1 log. Pre-existing local
Tracker/settings changes are not part of this fix's commit.

The maintainer reports successful startup and correct battle UI after package
migration and removal of conflicting packages. Those are reports about the
previous candidate; the modified shortcut behavior still needs live testing.

## Agreed scope

The maintainer clarified: **disable only `gg.unicum.menu`; keep the existing
Tracker gear and modsSettingsApi page**. The native `unicum.gg` tab stays the
standard route. A future consolidated panel is deferred. No UI design,
statistics algorithm, configuration schema, version or Package ID changes.

## Distinct identities

| Identity | Owner and purpose |
| --- | --- |
| `gg.unicum.wnxui` | `tools/build_release.py`: package metadata and `.wotmod` filename. |
| `gg.unicum.menu` | `src/unicum/mods_list.py`: our optional modsListApi shortcut registration. |
| `gg.unicum` | `settings_window/labels.py` `LINKAGE`: settings template/callback namespace in modsSettingsApi, also used when selecting the Aslain page. |
| `unicum.SettingsTab` | AS3 `SettingsTab.LINKAGE`: view class used by the game's own settings tabs. |
| `unicum.gg` | Display label of the native tab and other UI. |

`mods_list.py` imports `labels.LINKAGE` to select the settings page, not to
name its menu entry. Changing Package ID neither renames nor isolates these
runtime identities. The `7b7a9b9` diff contains no runtime registration changes.

## Verified call chains before the fix

Registration:

```text
unicum.start()
  -> settings_window.install(session, settings, link)  [optional API page]
  -> settings_tab.install(session, settings, link)    [native bridge]
  -> mods_list.install(session)
       -> ModsListEntry.install()
            -> session.on_close(_remove)
            -> g_modsListApi.addModification(id='gg.unicum.menu', callback=_CALLBACK)
```

Clicking the shortcut uses a builtin/import-based callback, then
`open_settings()` applies a two-second reopen guard and schedules `_OPEN_NOW`
through `Session.callback(0.5, ...)`. `open_now()` tries Aslain, izeberg,
the existing modsSettingsApi menu callback, then the native fallback. These
routes also serve the account-card action in `twitch_panel.py` and remain.

Native Apply:

```text
SettingsTabView.hookWindow(): listeners on applyBtn / submitBtn
  -> onCommit(): send pending var/type/value lines, clear draft, shell.hold()
  -> SettingsTab.send() / out queue
  -> LobbyView.takeSettingsTabOut() or TeamNamesHtml equivalent
  -> Python SettingsTab._tick() -> _take()
  -> codec.read_native() -> codec.apply_window()
  -> Settings.update(from_window(raw))
       -> merge + validate + write -> _notify() when values differ
       -> registered surfaces refresh their own state
```

The current working-tree store writes before notification; on local write
failure it retains the old runtime state. Account-owned choices are delegated
separately to GameLink. No part of this save path calls `unicum.start()` or
`stop()`, or directly calls `removeModification('gg.unicum.menu')`.

UI updates are more specific than a whole-mod restart:

- The game's Apply can rebuild its tabs list. `SettingsTabs.addTab()` checks
  each frame, re-adds the native tab if absent, and restores its selection.
  `SettingsTab.holding` bridges the game's own settings-response cycle.
- Native Python `_tick()` republishes changed page text; the AS3 settings
  view can rebuild its controls. That is separate from the lobby menu item.
- Optional `SettingsWindow._on_settings()` updates API values. A language
  change, or `_check_state()` detecting link/preview changes, unregisters its
  two callbacks and registers a new template. `_unregister()` detaches
  `onSettingsChanged` and `onButtonClicked`; it does not remove our menu item.
  Full `_remove()` drops the optional page only on Session close.

Two explicit menu-removal routes exist in our old source:

```text
Session.close() -> ModsListEntry._remove() -> API.removeModification(MOD_ID)

TrackerRoot.openSettings() -> send({kind:'opened'})
  -> Controller._tick() -> _action()
  -> settings.reload() + menu.retire()
  -> ModsListEntry._remove() -> API.removeModification(MOD_ID)
```

The second route intentionally retired the duplicate shortcut once the custom
Tracker window acknowledged opening. It is a concrete removal path, but
native `SettingsTabView.onCommit()` does not send this Tracker `opened` event.
It therefore does **not** establish the cause of the reported native-Apply bug.

## Diagnostic limit and focused next investigation

The local log confirms Aslain Mod Menu 2.1.15, including:
`flash mods-list absent - gui.modsListApi is served by the menu API now`.
The session starting at 16:45:42 registers the menu item; later it opens the
Aslain route and shows native settings views. There is no logged removal
reason, call stack, callback identity or before/after entry snapshot.
The installed vendor Python implementation is obfuscated; it was only read,
never executed outside the client or modified during this investigation.

Thus the **exact cause of disappearance after native Apply is unconfirmed**.
The following are possibilities to distinguish, not proven causes:

- Tracker's independent retirement action arrived near the user's Apply.
- The shim rebuilt its entry collection after an API/template update, or
  changed API instance; our entry previously registered only once per start.
- A menu model still held a prior callback after a reload. The old code
  explicitly guards against that history with builtin/import-based callbacks.
- Optional API template replacement/event reentrancy affected the shim's
  view of registrations. Our unregister/register pair is designed to avoid
  duplicate callbacks, but vendor behavior is not established by source tests.

For a separate diagnostic candidate with registration deliberately restored,
log only IDs, generation, instance identities and counts at:

1. `ModsListEntry.install`, `_remove`, `retire`, `Session.close`: reason and
   a short removal stack; distinguish teardown from Tracker retirement.
2. `SettingsTab._take` before/after committed messages, `Settings.update`
   success/failure/notification, `Controller._action` event kind.
3. `SettingsWindow._on_settings`, `_check_state`, `_register`, `_unregister`:
   whether the language/template changed, handler counts and API identity.
4. Read-only menu-entry presence and callback identity before/after Apply,
   then again on the next UI update. Correlate one session and timestamps.

Do not log values, account credentials or private keys, remove foreign
entries, patch the vendor implementation, or enable this instrumentation in
the normal workaround. No diagnostic runtime data sufficient to decide among
these possibilities was available in this task.

## Implemented temporary solution

`mods_list.install(session)` no longer instantiates the legacy registration
class, imports the menu API, or calls add/removeModification. It returns
`None` so Tracker has no duplicate entry to retire. The legacy implementation
is retained, dormant, for a later deliberate registration decision.

The existing account-card action still needs `_session` for its delayed
settings open. The installer therefore keeps that navigation context with
one guarded close hook, no polling, subscriptions, patches or queued timer.
Repeated installation in the same Session is idempotent. An older Session's
teardown cannot clear a newer context; actual delayed opens remain gated and
cancelled by Session. There is no cosmetic hiding and no global menu reset.

The native tab, optional API registration, Tracker gear and configuration
paths remain unchanged. A full client restart is recommended for testing a
new packaged build; normal reload first closes the old owning Session.

## Configuration boundaries and future panel proposal

Current separation is substantial but incomplete:

- `settings/defaults.py`, `validating.py`, `wnx.py`: defaults and validation.
  `settings/store.py`: one shared Settings instance, persistence, external-file
  reload and `on_change` notifications; it does not depend on an AS3 window.
- `settings_window/codec.py`: flat UI variables/indices versus nested values;
  `apply_window` coordinates local settings with GameLink/account operations.
- `page.py`, `native.py`, `labels.py`, `localize.py`, `preview.py`, shared WNX
  field catalog: presentation schema, translations, previews and serialization.
- `settings_tab.py`: native message bridge; `SettingsWindow`: optional API
  adapter; `tracker/controller.py` plus AS3 TrackerSettings: custom adapter.
- `tracker/page.py` currently parses the native page into its categories and
  adds Tracker-only options. The future UI is therefore coupled to another
  UI's serialized format. It should not become the configuration authority.
- Account linking/privacy controls use GameLink/account storage and network
  acknowledgments; tracker history/reset has separate persistence and identity
  guards. Neither should be folded into settings.json or a render component.

Proposed future work, **not implemented here**:

1. Define one typed field/action catalog independent of native page strings,
   with stable keys, validation, labels and availability conditions.
2. Keep one configuration service for validated local updates and change
   notifications; expose explicit account/history commands with asynchronous
   success/failure. Reuse existing storage and algorithms.
3. Have native, optional API and future panel adapters render that catalog and
   maintain their own drafts. Apply uses the shared service; Cancel discards
   only the draft. Avoid subscriptions or configuration copies per render.
4. Preserve forward/unknown keys, account/region isolation, reset confirmation,
   atomic file behavior and offline use. Test migration and all adapters before
   retiring any old route or deciding the panel/menu ownership policy.

No panel migration or large refactor was performed.

## Validation and manual gate

The new checks cover disabled registration, unchanged foreign entries,
idempotency, no registration-side timers/hooks, native Apply/notifications/file
write/new-instance persistence, retained routes, Tracker-open navigation,
delayed callback cancellation and safe Session replacement. Native AS3 fixtures
execute actual SettingsTabs methods for registration, Apply list recovery,
duplicate prevention and preservation of game tabs/selection.

Required in WoT: start with one new package, confirm no standalone Unicum menu
item before/after Apply, verify other menu entries, native Apply/Cancel/OK and
restart persistence, Tracker gear and optional API, then battle/Alt/Tab/markers
and WNX. Source/fake-client tests cannot certify live vendor UI behavior.
