"""Native Scaleform page, using the shared schema and preview formatters."""
from __future__ import absolute_import

from unicum.settings import EXTRAS, MAX_FLAGS, METRICS, MODES, WINDOWS
from unicum.settings_window.labels import (
    _ALT_SCREENS, _EXTRA_LABELS, _GARAGE_SURFACES, _MENU_KEYS, _MODE_LABELS,
    _SURFACE_LABELS, _WINDOW_LABELS, BATTLE_CHAT_LABEL, BATTLE_CHAT_LABELS,
    BATTLE_TEXT_LABEL, CARD_LABEL, CARD_VAR, COLOR_CLAN_TAGS_LABEL,
    COLOR_NAMES_LABEL, COLOR_VEHICLES_LABEL, CONNECT_VAR, FIGURE_LABELS,
    FIGURES_LABEL, GARAGE_CHAT_LABEL, HIDE_BATTLES_LABEL, HIDE_BATTLES_VAR,
    HIDE_LABEL, HIDE_VAR, LINKS, MEASURE_LABEL, MINIMAP_NAME_LABELS,
    PANEL_TEXT_LABEL, RELOAD_LABELS, REPLAYS_LABEL, RESET_BUTTON, RESET_LABEL,
    RESET_VAR, RESULTS_FIGURES_LABEL, SHOW_CHOICES, SHOW_WNX_BADGES_LABEL,
    TEAM_CHOICES, TEXT_SIZE_LABELS, WHEN_CHOICES)
from unicum.settings_window.codec import (_alt_key, _figures_key, _menu_key,
                                          _mode_key, _show_key, to_window)
from unicum.settings_window import localize, wnx

def native_page(values, channel=u'', linked=False, card_shown=True,
                supporter=False, loadouts_hidden=False, battles_hidden=None,
                drawing=None):
    """The same settings for the unicum.gg tab of the game's settings window (settings_tab.py).

    The same variables and the same choices as template(), laid out for a
    window this mod draws itself: sub-tabs, framed groups in two columns, a
    line a setting. As text the AS3 side reads without a JSON parser, a line
    an item, its fields apart by tabs:

      tab       label
      group     column (0 or 1), title
      dropdown  var, label, selected index, offset, options apart by "|"
      checkbox  var, label, 1 or 0
      text      label, drawn as plain text with its markup escaped
      preview   markup, drawn as markup: the mod's own badges, nothing else
      button    var, label, button text

    A dropdown sends back its index plus its offset: maxFlags counts from 1.
    """
    from unicum.settings_window.page import channel_label, garage_preview_lines, preview_lines
    window = to_window(values, card_shown, loadouts_hidden, battles_hidden)
    lines = []

    def tab(label):
        lines.append(u'tab\t' + label)

    def group(column, title):
        lines.append(u'group\t%d\t%s' % (column, title))

    def dropdown(label, var, options, offset=0):
        lines.append(u'dropdown\t%s\t%s\t%d\t%d\t%s' % (var, label, window[var] - offset, offset,
                                                         u'|'.join(options)))

    def show(surface):
        dropdown(_SURFACE_LABELS[surface], _show_key(surface), [c[0] for c in SHOW_CHOICES])

    def checkbox(label, var):
        lines.append(u'checkbox\t%s\t%s\t%d' % (var, label, 1 if window[var] else 0))

    def preview_rows(rows):
        for row in rows:
            lines.append(u'preview\t' + row)

    tab(u'Garage')
    group(0, u'General')
    checkbox(u'Enable unicum.gg', 'enabled')
    dropdown(u'Settings language', 'settingsLanguage', localize.LANGUAGE_NAMES)
    group(0, u'Stats')
    dropdown(u'Rating', 'metric', [metric.upper() for metric in METRICS])
    dropdown(u'Period', 'window', [_WINDOW_LABELS[w] for w in WINDOWS])
    dropdown(u'Win rate', 'winrate', [_EXTRA_LABELS[e] for e in EXTRAS])
    checkbox(u'Win rate to a tenth', 'winrateDecimal')
    dropdown(u'Battles', 'battles', [_EXTRA_LABELS[e] for e in EXTRAS])
    dropdown(u'Flags per player or clan', 'maxFlags', [str(n) for n in range(1, MAX_FLAGS + 1)], offset=1)
    preview_rows(garage_preview_lines(drawing))
    group(0, u'Garage')
    checkbox(u'Tank menu button', 'tankButton')
    checkbox(u'Right-click a player', _menu_key('players'))
    checkbox(u'Right-click a tank', _menu_key('vehicles'))
    checkbox(u'Share my loadouts', 'sendLoadouts')
    if supporter:
        checkbox(HIDE_LABEL, HIDE_VAR)
    if battles_hidden is not None:
        checkbox(HIDE_BATTLES_LABEL, HIDE_BATTLES_VAR)
    checkbox(REPLAYS_LABEL, 'sendReplays')
    checkbox(CARD_LABEL, CARD_VAR)
    checkbox(MEASURE_LABEL, 'measurePerformance')
    group(1, u'Screens')
    for surface in _GARAGE_SURFACES:
        show(surface)
        if surface in ('skirmishRoom', 'battleResults'):
            checkbox(_SURFACE_LABELS[surface] + ' average', surface + 'Average')
    dropdown(u'Skirmish room: when', _alt_key('skirmishRoom'), WHEN_CHOICES)
    dropdown(u'Stronghold: when', _alt_key('stronghold'), WHEN_CHOICES)
    dropdown(u'Battle results: when', _alt_key('results'), WHEN_CHOICES)
    dropdown(RESULTS_FIGURES_LABEL, _figures_key('battleResults'), list(FIGURE_LABELS))
    group(1, u'unicum.gg')
    for var, text, word in LINKS:
        lines.append(u'button	%s	%s	%s' % (var, text, word))
    lines.append(u'button	%s	%s	%s' % (RESET_VAR, RESET_LABEL, RESET_BUTTON))

    tab(u'Battle')
    group(0, u'What and when')
    show('battle')
    checkbox(u'Team average', 'battleAverage')
    dropdown(FIGURES_LABEL, _figures_key('battle'), list(FIGURE_LABELS))
    group(0, u'WNX in battle')
    checkbox(COLOR_NAMES_LABEL, 'colorNamesByWnx')
    checkbox(COLOR_CLAN_TAGS_LABEL, 'colorClanTagsByWnx')
    checkbox(COLOR_VEHICLES_LABEL, 'colorVehiclesByWnx')
    checkbox(SHOW_WNX_BADGES_LABEL, 'showWnxBadges')
    preview_rows(preview_lines(drawing))
    for key, label in _ALT_SCREENS:
        dropdown(label, _alt_key(key), WHEN_CHOICES)
    group(0, u'Tools')
    dropdown(u'Announce reloading', 'autoReload', RELOAD_LABELS)
    dropdown(u'Minimap labels', 'minimapNames', MINIMAP_NAME_LABELS)
    group(1, u'Whose stats, per mode')
    for mode in MODES:
        dropdown(_MODE_LABELS[mode], _mode_key(mode), [c[0] for c in TEAM_CHOICES])

    lines.extend(wnx.native_rows(window))
    tab(u'Twitch')
    group(0, u'Twitch')
    lines.append(u'input\ttwitchChannel\tTwitch channel (empty: linked account)\t' + values['twitch']['channel'])
    if linked:
        lines.append(u'text\t' + channel_label(channel, linked))
    else:
        lines.append(u'button\t%s\t%s\tConnect' % (CONNECT_VAR, channel_label(channel, linked)))
    checkbox(GARAGE_CHAT_LABEL, 'twitchGarage')
    dropdown(PANEL_TEXT_LABEL, 'twitchPanelText', TEXT_SIZE_LABELS)
    dropdown(BATTLE_CHAT_LABEL, 'twitchBattle', BATTLE_CHAT_LABELS)
    dropdown(BATTLE_TEXT_LABEL, 'twitchBattleText', TEXT_SIZE_LABELS)
    return localize.native(u'\n'.join(line.replace(u'\n', u' ') for line in lines), values)
