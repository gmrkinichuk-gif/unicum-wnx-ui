"""The settings page, written out twice for two UI backends.

`template` builds the page izeberg's modsSettingsApi draws, and `native_page`
the same page for the client's own settings tab. Two renderings of one page,
which is why they sit together: a row added to one and forgotten in the other
is the mistake this arrangement is meant to make obvious.
"""
from __future__ import absolute_import

import logging

from unicum.settings import EXTRAS, MAX_FLAGS, METRICS, MODES, WINDOWS
from unicum.settings_window.labels import (_ALT_SCREENS, _CHOICE_WIDTH,
                                           _CONNECT_TOOLTIP, _EXTRA_LABELS,
                                           _LINK_TOOLTIPS, _MENU_KEYS,
                                           _MODES_TOOLTIP, _RESET_TOOLTIP,
                                           _RULE, _SURFACE_LABELS,
                                           _TAB_TOOLTIP, _WINDOW_LABELS,
                                           HIDE_BATTLES_LABEL, BATTLE_CHAT_LABEL,
                                           BATTLE_CHAT_LABELS, CARD_LABEL,
                                           CARD_VAR, CONNECT_VAR,
                                           DISCORD_VAR, HIDE_BATTLES_VAR,
                                           HIDE_VAR, LINKS,
                                           MEASURE_LABEL, MINIMAP_NAME_LABELS,
                                           RELOAD_LABELS, REPLAYS_LABEL,
                                           RESET_BUTTON, RESET_LABEL,
                                           FIGURE_LABELS, FIGURES_LABEL,
                                           RESULTS_FIGURES_LABEL,
                                           _FIGURES_TOOLTIP,
                                           _RESULTS_FIGURES_TOOLTIP,
                                           RESET_VAR, SHOW_CHOICES,
                                           SOURCE_VAR, SUPPORT_VAR,
                                           TEAM_CHOICES, WHEN_CHOICES,
                                           _GARAGE_SURFACES, _MODE_LABELS,
                                           _SPACER, HIDE_BATTLES_TOOLTIP,
                                           GARAGE_CHAT_LABEL, HIDE_LABEL,
                                           PANEL_TEXT_LABEL, BATTLE_TEXT_LABEL,
                                           TEXT_SIZE_LABELS, REPLAYS_TOOLTIP,
                                           COLOR_NAMES_LABEL, COLOR_CLAN_TAGS_LABEL,
                                           COLOR_VEHICLES_LABEL, SHOW_WNX_BADGES_LABEL,
                                           _COLOR_NAMES_TOOLTIP, _COLOR_CLAN_TAGS_TOOLTIP,
                                           _COLOR_VEHICLES_TOOLTIP, _SHOW_WNX_BADGES_TOOLTIP)
from unicum.settings_window.codec import (_alt_key, _figures_key, _menu_key,
                                          _mode_key, _show_key, to_window)
from unicum.settings_window import preview
from unicum.settings_window import wnx
from unicum.settings_window import localize

# Whether the modsSettingsApi page carries the preview too. Its label is
# izeberg's component, not ours, and whether it draws markup or prints the
# tags is not written down anywhere: this says so out loud instead of
# pretending it was checked. The client's own settings tab draws it either
# way, because that one is ours.
_API_PREVIEW = True

_logger = logging.getLogger('unicum.settings_window.page')

def _joined(rows, prefix=u''):
    """(drawn row, ...): each row as one field, its caption in front of it.

    A tab character would be read as the end of a field in the native page,
    so it never appears in one. Captions are this module's own words and a
    surface's own label, so there is nothing to escape, and the badges that
    follow are the mod's own markup.
    """
    out = []
    for caption, markup in rows:
        if not markup:
            continue
        said = u', '.join(part for part in (prefix, caption) if part)
        out.append(u'%s   %s' % (said, markup) if said else markup)
    return tuple(out)


def garage_preview_lines(drawing):
    """The sample garage row, named by the screen it is a row of.

    Named because the Garage tab shows five screens and the Stats group
    above the preview feeds all of them: without the name a reader cannot
    tell which one they are being shown, and would read the row as being
    about whichever dropdown they last touched.
    """
    if not drawing:
        return ()
    badges, textures, settings = drawing
    surface = preview.garage_surface(settings)
    if surface is None:
        return ()
    return _joined(preview.lines(badges, textures, settings, surface),
                   _SURFACE_LABELS[surface])


def preview_lines(drawing):
    """The sample battle rows as markup, captions included; () without the badges.

    `drawing` is (badges, textures, settings) or None. None until the mod has
    built them, which is the first moment of a session and any session where
    the badge files could not be drawn: the window opens with one line fewer
    rather than not at all.

    The settings come through here rather than from the `values` the rest of
    the page is built from because the preview asks them questions -- what is
    shown, which figures, which metric -- that only the store answers. They
    are the same values either way: the page is built from `store.values()`.

    A tab character would be read as the end of the field, so the caption is
    joined to its row with spaces. Captions are this module's own words, so
    there is nothing to escape.
    """
    if not drawing:
        return ()
    badges, textures, settings = drawing
    return _joined(preview.lines(badges, textures, settings))


def _heading(templates, text):
    return templates.createLabel(u'%s  %s' % (text.upper(), _RULE))

def channel_label(channel, linked):
    """The Twitch section's channel line."""
    if not channel:
        return u'Channel: not linked'
    return u'Channel: %s' % channel if linked else u'Channel: %s (Connect to write in it)' % channel

def _button_line(templates, text, var, button, tooltip=None):
    # 1.7.1's Label factory ignores buttons entirely. An empty radio group
    # draws its heading and dynamic button without a dummy editable control.
    return templates.createRadioButtonGroup(
        text, var, [], -1, tooltip=tooltip,
        button=templates.createButton(width=90, height=24, text=button))

def template(values, channel=u'', linked=False, card_shown=True,
             supporter=False, loadouts_hidden=False, battles_hidden=None,
             drawing=None):
    """The API's page for these settings, showing `values` and the Twitch channel followed.

    `linked` is whether the Twitch chat can be written to, `card_shown` whether
    the account card shows for the account logged in. `supporter` decides
    whether the hiding box is drawn at all, and `loadouts_hidden` where it sits.
    `battles_hidden` is None when the game is linked to no account, which is
    the one case the battle-hiding box is left out: the site keys it there.
    """
    from gui.modsSettingsApi import templates
    window = to_window(values, card_shown, loadouts_hidden, battles_hidden)

    def checkbox(label, var, tooltip=None):
        return templates.createCheckbox(label, var, window[var], tooltip=tooltip)

    def choice(label, var, options, tooltip=None):
        return templates.createDropdown(label, var, list(options), window[var], tooltip=tooltip, width=_CHOICE_WIDTH)

    def show(surface):
        return choice(_SURFACE_LABELS[surface], _show_key(surface), [c[0] for c in SHOW_CHOICES])

    garage = [
        _heading(templates, 'Garage'),
        choice('Settings language', 'settingsLanguage', localize.LANGUAGE_NAMES),
        choice('Rating', 'metric', [metric.upper() for metric in METRICS],
               tooltip='{HEADER}Rating{/HEADER}{BODY}WN7, WN8 and WNX are unicum.gg\'s own, computed '
                       'from a player\'s per-vehicle records. PR and WTR are Wargaming\'s own: one '
                       'figure for a whole career, the second being the rating the client itself '
                       'shows.{/BODY}'),
        choice('Period', 'window', [_WINDOW_LABELS[w] for w in WINDOWS],
               tooltip='{HEADER}Rating period{/HEADER}{BODY}Last 30 days falls back to overall while the '
                       '30-day value is not computed yet. PR and WTR have no 30-day value at all, so '
                       'they stay career figures whatever is chosen here.{/BODY}'),
        choice('Win rate', 'winrate', [_EXTRA_LABELS[e] for e in EXTRAS],
               tooltip='{HEADER}Win rate{/HEADER}{BODY}Drawn beside the rating, wherever the rating is '
                       'drawn, in grey so the badge stays what you read first. Its period is its own: a '
                       'rating reads as form, a win rate is usually wanted over a whole career.{/BODY}'),
        checkbox('Win rate to a tenth', 'winrateDecimal',
                 tooltip='{HEADER}Win rate to a tenth{/HEADER}{BODY}Draws 58.7% instead of 59%. Off by '
                         'default: the rating badge beside it is a whole number too, and a tenth of a '
                         'point is not something you read at a glance.{/BODY}'),
        choice('Battles', 'battles', [_EXTRA_LABELS[e] for e in EXTRAS],
               tooltip='{HEADER}Battles{/HEADER}{BODY}How many battles the player has, beside the rating. '
                       'Shortened past ten thousand everywhere it is drawn: 23k rather than 23 184. The '
                       'badge is an image and each distinct number is a file, so counting to the unit '
                       'past ten thousand would write thousands of them into your game folder.{/BODY}'),
        templates.createNumericStepper('Flags per player or clan', 'maxFlags', window['maxFlags'], 1, MAX_FLAGS, 1),
    ]
    if _API_PREVIEW:
        garage.extend(templates.createLabel(row) for row in garage_preview_lines(drawing))
    garage.append(templates.createEmpty(_SPACER))
    garage.extend(show(surface) for surface in _GARAGE_SURFACES)
    garage.extend(checkbox(_SURFACE_LABELS[surface] + ' average', surface + 'Average')
                  for surface in ('skirmishRoom', 'battleResults'))
    garage.append(choice(RESULTS_FIGURES_LABEL, _figures_key('battleResults'),
                         list(FIGURE_LABELS), tooltip=_RESULTS_FIGURES_TOOLTIP))
    garage.extend([
        choice('Skirmish room: when', _alt_key('skirmishRoom'), WHEN_CHOICES,
               tooltip='{HEADER}Skirmish room{/HEADER}{BODY}While Alt is held, the members ratings and '
                       'flags show, and the average of the detachment with them. The order they are '
                       'sorted in stays whatever you chose.{/BODY}'),
        choice('Stronghold: when', _alt_key('stronghold'), WHEN_CHOICES),
        choice('Battle results: when', _alt_key('results'), WHEN_CHOICES),
        templates.createEmpty(_SPACER),
        checkbox('Tank menu button', 'tankButton',
                 tooltip='{HEADER}Tank menu button{/HEADER}{BODY}A unicum.gg button beside the vehicle menu, '
                         'with links for the selected tank: its unicum.gg tabs, AI assistants and its '
                         'build.{/BODY}'),
        checkbox('Right-click a player', _menu_key('players'),
                 tooltip='{HEADER}Right-click a player{/HEADER}{BODY}Adds unicum.gg entries to the menu the '
                         'game opens on a player: their page, and the AI assistants. In battle, in the battle '
                         'results, in your contacts and in a skirmish room.{/BODY}'),
        checkbox('Right-click a tank', _menu_key('vehicles'),
                 tooltip='{HEADER}Right-click a tank{/HEADER}{BODY}The same on the menu the game opens on a '
                         'vehicle: the carousel, the tech tree, the shop and the comparison.{/BODY}'),
        checkbox('Share my loadouts', 'sendLoadouts',
                 tooltip='{HEADER}Share my loadouts{/HEADER}{BODY}Sends how you have set your tanks up, so your own unicum.gg page shows them: equipment, crew skills, field modifications, ammunition. Nothing about anyone else, and Wargaming publishes none of it, so a page is only as complete as the players who share. Untick it to stop, and to have everything already sent deleted.{/BODY}'),
    ])
    # Only for the accounts that may use it. A box drawn greyed out for
    # everybody else would be advertising the subscription rather than
    # describing a setting, and this list is a list of settings.
    if supporter:
        garage.append(checkbox(
            HIDE_LABEL, HIDE_VAR,
            tooltip='{HEADER}' + HIDE_LABEL + '{/HEADER}{BODY}Keeps sending your loadouts, so they still count '
                    'towards what the site can say about a tank, but takes them off your own public page. To '
                    'stop sending them altogether, and delete the ones already sent, untick Share my loadouts '
                    'instead.{/BODY}'))
    if battles_hidden is not None:
        garage.append(checkbox(HIDE_BATTLES_LABEL, HIDE_BATTLES_VAR, tooltip=HIDE_BATTLES_TOOLTIP))
    garage.extend([
        checkbox(REPLAYS_LABEL, 'sendReplays', tooltip=REPLAYS_TOOLTIP),
        checkbox(CARD_LABEL, CARD_VAR,
                 tooltip='{HEADER}' + CARD_LABEL + '{/HEADER}{BODY}The card under the mission cards that '
                         'links this game to your unicum.gg account, or says which one it is linked to. Its '
                         'cross hides it for the account logged in; tick this to bring it back.{/BODY}'),
        checkbox(MEASURE_LABEL, 'measurePerformance',
                 tooltip='{HEADER}' + MEASURE_LABEL + '{/HEADER}{BODY}Times everything this mod does on the '
                         'thread that draws the game and writes a table to python.log every ten seconds, '
                         'worst first. Turn it on only to answer a question about frame rate, and send the '
                         'table with the report. It measures this mod alone, not the game and not the other '
                         'mods installed.{/BODY}'),
        checkbox(GARAGE_CHAT_LABEL, 'twitchGarage'),
        choice(PANEL_TEXT_LABEL, 'twitchPanelText', TEXT_SIZE_LABELS,
               tooltip="{HEADER}" + PANEL_TEXT_LABEL + "{/HEADER}{BODY}How big the chat lines are "
                       "drawn in the panel, in the garage and in the window over a battle, which are "
                       "the same panel. The panel keeps the size you gave it, so a larger text shows "
                       "fewer lines at once: drag the panel's corner for more room.{/BODY}"),
        # Connect only while it has something to do: once the chat can be
        # written to, the line only says which channel it is.
        (templates.createLabel(channel_label(channel, linked), tooltip=_CONNECT_TOOLTIP) if linked else
         _button_line(templates, channel_label(channel, linked), CONNECT_VAR, 'Connect', _CONNECT_TOOLTIP)),
        templates.createEmpty(_SPACER),
    ])
    garage.extend(_button_line(templates, text, var, word, _LINK_TOOLTIPS[var]) for var, text, word in LINKS)
    garage.append(_button_line(templates, RESET_LABEL, RESET_VAR, RESET_BUTTON, _RESET_TOOLTIP))

    battle = [
        _heading(templates, 'Battle'),
        checkbox('Show battle ratings', 'battleRating'),
        checkbox('Team average', 'battleAverage'),
        choice(FIGURES_LABEL, _figures_key('battle'), list(FIGURE_LABELS),
               tooltip=_FIGURES_TOOLTIP),
        checkbox(COLOR_NAMES_LABEL, 'colorNamesByWnx', tooltip=_COLOR_NAMES_TOOLTIP),
        checkbox(COLOR_CLAN_TAGS_LABEL, 'colorClanTagsByWnx', tooltip=_COLOR_CLAN_TAGS_TOOLTIP),
        checkbox(COLOR_VEHICLES_LABEL, 'colorVehiclesByWnx', tooltip=_COLOR_VEHICLES_TOOLTIP),
        checkbox(SHOW_WNX_BADGES_LABEL, 'showWnxBadges', tooltip=_SHOW_WNX_BADGES_TOOLTIP),
    ]
    if _API_PREVIEW:
        battle.extend(templates.createLabel(row) for row in preview_lines(drawing))
    battle.append(templates.createEmpty(_SPACER))
    battle.extend(choice(_MODE_LABELS[mode], _mode_key(mode), [c[0] for c in TEAM_CHOICES],
                         tooltip=_MODES_TOOLTIP if mode == MODES[0] else None) for mode in MODES)
    battle.append(templates.createEmpty(_SPACER))
    battle.extend(choice(label, _alt_key(key), WHEN_CHOICES, tooltip=_TAB_TOOLTIP if key == 'tab' else None)
                  for key, label in _ALT_SCREENS)
    battle.extend([
        templates.createEmpty(_SPACER),
        choice(BATTLE_CHAT_LABEL, 'twitchBattle', BATTLE_CHAT_LABELS,
               tooltip='{HEADER}' + BATTLE_CHAT_LABEL + '{/HEADER}{BODY}Where your Twitch chat shows once the battle has started. In the battle chat puts each message in the game\'s own chat, which is what this setting did when it was a tick box. In a window keeps the chat window of the queue screen up over the battle, drawn like the panel in the garage and draggable to a place of its own, which is remembered apart from the garage\'s. While you are aiming the game keeps the mouse to itself, so that window is there to read, not to type in.{/BODY}'),
        choice(BATTLE_TEXT_LABEL, 'twitchBattleText', TEXT_SIZE_LABELS,
               tooltip="{HEADER}" + BATTLE_TEXT_LABEL + "{/HEADER}{BODY}How big the Twitch lines are "
                       "drawn in the game's own battle chat. Asked as a step up or down from the size "
                       "the game draws with, so it follows your interface scale instead of fighting "
                       "it. The Glitch and the viewer badges are images and keep their own size."
                       "{/BODY}"),
        choice('Announce reloading', 'autoReload', RELOAD_LABELS,
               tooltip='{HEADER}Announce reloading{/HEADER}{BODY}Sends the "Reloading!" message to your team '
                       'by itself, as F8 does. Every gun announces after each shot; autoloaders only, once a '
                       'magazine is empty, which is far less talking. Reloads shorter than the 5-second limit '
                       'of the chat are never announced.{/BODY}'),
        choice('Minimap labels', 'minimapNames', MINIMAP_NAME_LABELS,
               tooltip='{HEADER}Minimap labels{/HEADER}{BODY}What is written beside a vehicle on the minimap. '
                       'The game writes the vehicle; calling out a flank usually wants the player. This only '
                       'changes a label the game was already going to write, so it stays off entirely while '
                       'the game\'s own minimap names are turned off.{/BODY}'),
    ])
    battle.extend(wnx.api_rows(templates, window))
    return localize.template({'modDisplayName': 'unicum.gg', 'enabled': values['enabled'],
                              'column1': garage, 'column2': battle}, values)

from unicum.settings_window.native import native_page
