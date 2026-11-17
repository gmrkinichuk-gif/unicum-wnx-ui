# Changelog

## 0.9.17

- Avoid repeated assignments to unchanged Scaleform roster text geometry and formatting properties
- Add bounded, opt-in slow-call timestamps to the existing performance meter for correlation with live frame-time traces
- Keep only the latest 64 primitive slow-call records and batch log output on the existing reporting interval

- Publish versioned 0.9.17 downloads, matching sources and checksums; document live-capture limitations and ChatGPT assistance.


## 0.9.16

- Stop unchanged Tab rows from rewriting canonicalised inline colours every 200 ms; batch native Live Tags layout reads after row updates
- Cache unchanged overhead-marker geometry and reduce dynamic marker-field lookups without changing Alt, HP or vehicle-icon placement
- Reuse each account's prepared overhead-marker payload until its API entry, colour scale or display settings change
- Skip retained hidden Scaleform loading and legacy Tab branches while keeping visible players panels and loading rows on the existing 20 Hz refresh
- Add steady-state CSS-write, hidden-branch and marker-cache regression checks

- Document the 20–150 s replay comparison: mean FPS 69.58 to 70.42, median 70 to 71, P10 sampled FPS 66 to 69, and Python game-thread time 2.40% to 0.96%; retain the lower isolated minimum (52 to 45 FPS) and measurement limitations
- Record validation results and existing teardown/API-check limitations in docs/PERFORMANCE_0.9.16.md

## Publication preparation - 2026-11-16

- Prepare the independent Unicum WNX UI source repository without changing the
  current mod version, 0.9.15, or publishing a Release.
- Add developer, provenance, dependency and audit documentation.
- Include required license notices in built packages and make local UI checks
  accept external client fixtures instead of the old workspace paths.
- Replace upstream release and hub publishing automation with read-only CI and
  a manually requested candidate build that only uploads an Actions artifact.

Versions 0.9.1 through 0.9.15 below describe the supplied local modification;
0.9.0 and earlier are inherited upstream history.


## 0.9.15

- Keep the native allied Live Tags in a normal-flow Tab column, including before their client bindings first reveal a leader
- Give the native Live Tags tooltip wrapper its full row height so damage, assistance and blocking icons remain centred and clickable
- Preserve native visibility, icon resources, leader updates and tooltip bindings; add late-binding and clipping regression checks using the actual client icons

## 0.9.14

- Show the existing neutral grey roster accent beside overhead labels when WNX is unavailable
- Keep disabled, team-filtered and Alt-only markers hidden separately from missing ratings
- Preserve the vertical accent geometry and replace grey with the original WNX band when cached statistics arrive

## 0.9.13

- Replace the overhead horizontal WNX underline with a three-pixel vertical accent to the right of the visible vehicle label or Alt nickname
- Keep the accent within the text line and move it sideways around native labels, HP and type indicators
- Reserve separate space for the existing Unicum marker badge beside the vertical accent

## 0.9.12

- Extend native current-player highlighting to clan tags, vehicle names and all roster statistics
- Keep overhead underlines below both visible labels; use space below the HP bar when the gap above it is insufficient
- Retain the WNX background of destroyed Tab rows and add a translucent red inset wash for both teams
- Slightly reduce Tab tint intensity while preserving the stronger loading and players-panel underlays

## 0.9.11

- Preserve the native current-player nickname colour in Scaleform and the client gold/colourblind colours in Tab
- Increase WNX underlines to four pixels with a solid dark outline; cache marker geometry while unchanged
- Increase row underlay opacity and WNX tint visibility in Tab, loading and players panels without changing any source rating colour or threshold
- Show an em dash during Alt when the selected text mode has no available statistic, restoring the native name on release
- Release marker anchors and pending image waiters explicitly when the marker view is removed

## 0.9.10

### Fixed

- Measure players-panel underlays from visible content, excluding atlas backgrounds and interaction hit areas; refresh the cache on mode changes and preserve the active Alt text slot
- Place Tab statistics beside the nickname inside the native user-info area, reduce excess table margins and cap each team at 700 rem
- Keep native Live Tags and their tooltips inside a reserved row slot instead of the clipped negative-offset gutter
- Preserve native vehicle contours, levels, prestige, status, voice and platoon controls in the compact layout

### Added

- Draw an exact WNX-band vector underline under the native overhead vehicle label, following the nickname when the client switches to extended information; omit it when WNX is unavailable

## 0.9.9

### Changed

- Replace the native nickname (Medium/Full) or vehicle text (Long) while Alt is held: WNX only in the narrow Medium/Long slots, WNX/WR/battles in Full; preserve the vehicle name in Full and leave Short unchanged
- Add a reversible 150 ms text-only compression/fade transition inside the native text rectangle, with reusable fields and focus/mode/teardown cancellation
- Prepare per-account roster presentations only when ratings, settings or colour scales change; Alt changes visibility without roster scans or network requests
- Bound Scaleform roster refreshes to 20 Hz while advancing only active transitions every frame; preserve native text, icons, hit targets and panel geometry
- Reconcile missed extended-info key releases with one Session-owned callback while held
- Replace unsupported Gameface CSS negation selectors with reversible positive classes, preserving native icon containers

## 0.9.8

### Fixed

- Remove mandatory CSS getPropertyPriority and isConnected dependencies from Tab for Coherent 2.4.1.1 compatibility
- Add bounded Tab startup, model and rendering diagnostics
- Measure loading and players-panel backgrounds from one team grid with fixed row height
- Place loading medals and squad icons in dedicated mirrored zones inside the row
- Re-run the native name formatter after assigning the loading text width, using the client's original real/fake names and tags
- Mirror loading stripes outward, player-panel stripes inward and Tab stripes outward
- Extend regressions to missing DOM features, delayed data, teardown, native-name transport and actual AS3 geometry bodies


## 0.9.7

### Changed

- Reflow the native Tab rows into distinct player, WNX, WR, battles, contour and vehicle zones, within the viewport width
- Present roster text in light colours on dark row underlays with exact Unicum.gg WNX band accents
- Give Scaleform loading rows separate aligned statistics fields and expand the name area into available outer space
- Apply a softer version of the same style to the players panel, preserving Alt-only pills and Long-mode WNX-only markup

### Fixed

- Remove statistics from the nested 127rem nickname container
- Preserve cached Tab statistics while a background refresh is in flight
- Use explicit neutral rows and missing-value placeholders without fabricating ratings
- Share roster WNX/WR/count formatting between Gameface and Scaleform


## 0.9.6

### Improved

- Keep the Tab nickname text intact and use one-sided CSS ellipsis only when its actual layout box cannot fit it
- Show WNX badges in the ordinary battle players panel only while the native extended-info key is held; keep Tab and loading-screen behavior separate

### Fixed

- Stop rewriting the bound Tab nickname string during layout, preserving full names for roster matching and preventing repeated truncation
- Keep WNX badge visibility changes in the existing Scaleform rows without rebuilding them or affecting name colours and flags

## 0.9.5

### Improved

- Keep Tab nicknames and WNX statistics on one line, shortening names with three dots to preserve the stats area
- Show a crossed-eye indicator when a Tab row has no available WNX or the client hides its nickname
- Show only the WNX rating badge in the native Long players-panel mode when battle ratings are enabled

### Fixed

- Preserve the original Tab row grid and native tank icon containers while laying out names, clan tags and statistics
- Publish explicit WNX availability for player aliases while cached statistics resolve

## 0.9.4

### Improved

- Increase WNX text saturation without changing the Unicum.gg scale or its rating bands
- Show Tab statistics as one WNX-coloured block in the order WNX, win rate and battles
- Format Tab battle counts to tenths of a thousand, such as 0.3k and 1.5k

### Fixed

- Keep Tab statistics inside the existing player-name cell so native tank icon cells retain their row positions

## 0.9.3

### Improved

- Color player names, clan tags and vehicle names with the same WNX scale in the battle Tab, players panel and loading table
- Show battles, WNX and win rate as text after the vehicle name in the Tab table, following the project reference image

### Changed

- Hide per-player WNX rating badges by default, with a setting to show them again
- Add independent settings for player names, clan tags and vehicle names

## 0.9.2

### Improved

- Show each player's WNX beside their name in the battle Tab table, with the Unicum.gg WNX colour on the nickname and vehicle name

### Fixed

- Keep Unicum.gg flag icons out of the battle Tab table

## 0.9.1

### Added

- Colour the battle roster's player names and vehicle names with Unicum.gg's WNX scale, with separate settings for each

## 0.9.0

### Added

- Offering a replay whose battle the table cannot hold
- Personal rating and wtr to the ratings a player can read

### Fixed

- Ask the server which months it holds instead of mirroring the rule

<!-- 3 commit(s) not shown, being invisible to a player:
     Merge remote-tracking branch 'origin/main'
     the release zip's name to carry the game version
     Merge remote-tracking branch 'origin/main'
-->

## 0.8.0

### Added

- State the garage as a list, not only as loadouts
- Open the player's own page from the account card
- Choose where the Twitch chat shows in battle
- Replace the battle-sharing box with one that hides the battle list
- The platoons the client numbers to each battle sent
- A size for the chat text, in the panel and in the battle chat

### Improved

- Drop the fill the hangar's own cards do not have
- Wear the hangar's own card decor instead of copying it
- Draw the panel and the card as the hangar draws its own
- Soften the panel's borrowed noise to the hangar's own read strength
- Give the chat window the garage's own edge
- Build for the game client 2.4.1.1

### Fixed

- Announce the reload the C key starts
- Point the deferred imports the package split left behind
- Stop one refused battle from holding up every battle behind it
- Match the hangar's own hover on the account card
- The hover layer was three times too strong
- Give the panel's borrowed noise a widget's strength
- Let the panel's border take the card's own strength
- Give the chat panel an edge that survives a render and a battle
- Keep the window's place over a battle the client started in
- Read the account from the arena in a battle with no lobby behind it
- The master switch stopping the battle uploads (#10)
- Frontline battles naming only the first tank and earning for only one
- Frontline replays never being sent because their results ran past the header window
- The settings window taking the mod down at every start
- Reading an order into the lives of a vehicle that respawned

<!-- 16 commit(s) not shown, being invisible to a player:
     hold the file size convention with a ratchet
     split battles.py into a package
     split loadouts.py into a package
     split replays.py into a package
     split settings_window.py into a package
     split twitch_window.py into a package
     split twitch.py into a package
     split settings.py into a package
     split game_link.py into a package
     split tank_button.py into a package
     split battle.py into a package
     split lobby.py into a package, the last one over the limit
     check every name the mod takes from itself
     the import check failing on the gitignored local settings (#11)
     a release pull request that publishes the mod when merged
     the hand-off of each release to the wgmods publisher
-->

## 0.7.1

### Fixed

- Read the client's battle result types, not our own module
- Stop a recovered battle closing the player's results screen

## 0.7.0

### Added

- Sending a replay in pieces when it is too long for one request
- Ask for a battle's results as soon as it is announced

### Improved

- Set the sort dropdown as far from its edge as the title is from its
- Ask the disk once whether a badge is drawn, not once per draw
- Pick the newest replays by name instead of statting the folder
- Let the battle tab screen rest while it is not on screen
- Announce a reload as its report lands, not half a second later

### Fixed

- Keep the wanted replays through a rate limit
- Let the queue past a replay the server keeps refusing
- Stop offering replays the game will never put on the wire
- Stop freezing the game thread for a second to save the lookup cache
- Announce the reload a change of shell starts

### Removed

- The stack sampler, which broke the game it was measuring

## 0.6.0

### Added

- The ratings to the battle Tab screen, drawn in its page

### Fixed

- Send the ammunition and supplies cost the client reports as tuples
- Stop asking for battle results from inside a battle, and keep the try
- Sample a battle with one timer instead of one per battle
- Count a claim before it is sent, so a synchronous answer cannot break it
- Rebuild the whole receiver list, so the chat keeps its caret
- Take back the panel marker written before the view drew
- Answer whether the battle view draws, instead of always no

## 0.5.2

### Fixed

- The tank page button, the Twitch window and the ratings on the battle
  results screen, none of which appeared on game client 2.4.1.0. That client
  registers a mod's own views itself, and answers the older request with "not
  registered", which reads exactly like a missing file. The mod now declares
  those views the way the client asks for, and still the old way for an
  earlier client.

## 0.5.1

### Fixed

- The mod not loading at all on game client 2.4.1.0. The client moved the
  registry a Scaleform view declares itself in, and the mod read it by name at
  import time, so that one name took everything down with it: no ratings, no
  flags, no panel, nothing. It is now read through the GUI loader, and a
  client that moves it again costs the views that need it rather than the
  whole mod.

## 0.5.0

For game client 2.4.1.0.

### Added

- Report the battles this client played, with everything the game's own
  detailed report shows.
- Sampling where everybody was, while the battle runs, so a battle can be
  watched back on its map at unicum.gg.
- Sending the battle's own replay file, when the client kept one, under a
  setting of its own.
- Report the mark of excellence a battle left the gun at, and send the whole
  fleet's mark progress from the garage, for every tank ever played rather
  than only those still owned.
- A minimap label choice: the vehicle, the player, or both, which can wait for
  Alt like the other battle readings and takes effect without leaving battle.
- A replay tab on the battle results screen.

### Improved

- openwg_gameface 1.2.2, the build this client runs.
- Share battles by default.
- Ask whether the garage is loaded instead of waiting it out.
- Name the Alt row after its screen, not after the other setting.

### Fixed

- Resend only the arena description, so another mod's own labels on the
  players panel survive a rating landing.
- The hangar card offering Connect for a Twitch already linked.

<!-- Not shown, being invisible to a player: thirteen fixes to the battle
     reporting, the replay collection, the mark reading, the minimap labels
     and the results tab, all of them to work added in this same version; one
     code comment; and the release build reading the client version off the
     installed client rather than a mirror that lags a game update.
-->

## 0.4.1

### Fixed

- In the battle players list, the language flags no longer sit a couple of pixels above the badges beside them.
- On the loading screen, an image tag no longer shows for a moment next to the team names while the ratings are waiting for Alt.

## 0.4.0

### Added

- Your tank setups on your own unicum.gg page: equipment, directives, crew skills, field modifications, ammunition and consumables, for every vehicle in your garage. Sent when they change and when you take a tank into battle. On by default; untick Share my loadouts in the settings to stop, and everything already sent is deleted. Supporters can keep theirs off their public page while still contributing to the figures.
- Every rating now carries the player's win rate and battle count beside it, as badges in the same style. Each has its own switch and its own period, and the win rate can be shown to a tenth of a point.
- The Twitch chat a battle opens on carries what was said before it started, instead of opening empty.
- A Measure what this mod costs switch: it times what the mod does on the game's own thread, and samples which mod that thread is actually in, writing a table to python.log every ten seconds. For answering a frame rate question with a number instead of a guess.

### Improved

- The mod no longer lists a folder nine times a second in battle. That one call was 3.5% of all the Python the game's own thread ran.

### Fixed

- The contacts list no longer draws flags and badges over the player's name while its images are still loading.

## 0.3.0

### Added

- Right-click a player, anywhere in the game, and open their unicum.gg page or hand it to ChatGPT, Claude or Scira. In battle, in the battle results, in your contacts and in a skirmish room.
- The same on any tank: the carousel, the tech tree, the shop and the comparison.
- Two switches in the settings turn each of them off.

### Changed

- Installing is only the two files in the archive now. The mod makes what it needs on its first run and restarts the game once, so ratings are coloured badges from your very first battle instead of bare numbers.

## 0.2.0

### Added

- A settings box that brings back the unicum.gg account card once closed
- A notice saying where the account card went when it is closed
- The garage twitch panel to the battle queue screen, in a window of its own
- The twitch panel to the battle loading screen
- A unicum.gg tab to the game's own settings window
- A support button to both settings pages
- Discord and github links beside the support button
- The alt only choice to the skirmish room
- The stronghold alt choice, a reset button and a scrolling page
- Announcing reloads for autoloaders only
- One command that cuts a release from the commits

### Improved

- The hot reload note to say a changed AS3 class waits for its app to be rebuilt
- The settings page into a garage and a battle column, one dropdown per screen, mode and alt choice
- The tank menu button icon to the hangar's own brushed silver
- The battle markers to place themselves only when something moved
- The vehicle markers to draw their shadow without a filter
- The ai entries to name the build instead of encoding it
- The written build to read as a list
- The chatgpt entry to open the page carrying the build

### Fixed

- The twitch panel notice naming a settings box that does not exist
- The team average showing its image markup as text while the battle view is still loading
- The skirmish room's member list jumping as it refreshes
- The settings tab's ground to start under its sub-tabs, with no frame
- The settings tab's buttons never reaching python
- The settings tab reaching python, and its dropdowns' row count
- The skirmish sort order not coming back from the view
- A team losing its average on the tab screen
- The skirmish sort menu showing five rows whatever it holds
- The markers covering what appears beside a row
- The claude and chatgpt entries handing a link they refuse to open
- The scroll bar running to the very bottom of the page
- The page missing the fade at its edges and its scroll bar sitting too far right
- Settings tab fade and scroll bar to match the General tab
- The release finding the client's python, not a name no PATH holds
