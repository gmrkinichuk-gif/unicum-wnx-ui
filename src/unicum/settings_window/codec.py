"""Settings to window values and back, with nothing in between.

Text and dicts in, values out. The round trip is what the checks hold this
to: anything the page can show has to read back to the setting it came from,
because a value that does not survive the trip is a setting that silently
resets itself the next time the window opens.
"""
from __future__ import absolute_import

import logging

from unicum.settings import (AVERAGED, BATTLE_CHAT_CHOICES, EXTRAS,
                             METRICS, MINIMAP_NAME_CHOICES, MODES,
                             RELOAD_CHOICES, SURFACES,
                             TEXT_SIZE_CHOICES, WINDOWS)
from unicum.settings_window.labels import (_ALT_KEYS, _ALT_SCREENS,
                                           _MENU_KEYS, _SURFACE_LABELS,
                                           CARD_VAR, HIDE_BATTLES_VAR,
                                           HIDE_VAR,
                                           MINIMAP_NAME_LABELS,
                                           RELOAD_LABELS, SHOW_CHOICES,
                                           TEAM_CHOICES, WHEN_CHOICES)
from unicum.settings import FIGURE_CHOICES, FIGURED
from unicum.settings_window import wnx
from unicum.settings_window.localize import LANGUAGES

_logger = logging.getLogger('unicum.settings_window.codec')

def read_native(text):
    """What the settings tab sends back ("var\tkind\tvalue" a line), as the window's raw values.

    Kinds: d a dropdown's index (offset added), c a checkbox, b a button.
    Returns (raw values, buttons clicked).
    """
    raw, buttons = {}, []
    for line in (text or u'').split(u'\n'):
        parts = line.split(u'\t')
        if len(parts) != 3:
            continue
        var, kind, value = parts
        if kind == u'd':
            try:
                raw[str(var)] = int(value)
            except ValueError:
                continue
        elif kind == u'c':
            raw[str(var)] = value == u'1'
        elif kind == u's':
            raw[str(var)] = value
        elif kind == u'b':
            buttons.append(str(var))
    return raw, buttons

def read_peek(text):
    """The tab's peeked values: a choice made but not yet applied.

    Sent on every change, so the preview can show what the choice would
    look like before it is saved. An empty dict means nothing is pending,
    which is also what the tab sends when Apply, OK or Cancel settles it.

    Its lines carry a field more than a change does ("peek\tvar\tkind\t
    value"), which is what keeps `read_native` from reading them as changes
    and saving them: that one counts fields and skips anything that is not
    three.
    """
    peek = {}
    for line in (text or u'').split(u'\n'):
        parts = line.split(u'\t')
        if len(parts) != 4 or parts[0] != u'peek':
            continue
        _, var, kind, value = parts
        if not var:
            # The settling line: everything pending is gone.
            return {}
        if kind == u'd':
            try:
                peek[str(var)] = int(value)
            except ValueError:
                continue
        elif kind == u'c':
            peek[str(var)] = value == u'1'
    return peek


def apply_window(raw, settings, link, done=None):
    """Commit supported local WNX settings and acknowledge the save."""
    from unicum.profile import window_values
    raw = window_values(raw)
    if not settings.update(from_window(raw)):
        if done is not None:
            done('local', [])
        return
    if done is not None:
        done('', [])


def to_window(values, card_shown=True, loadouts_hidden=False, battles_hidden=False):
    """What the window stores for these settings: flat, choices by index."""
    window = {CARD_VAR: card_shown, HIDE_VAR: loadouts_hidden,
              HIDE_BATTLES_VAR: bool(battles_hidden),
              'enabled': values['enabled'], 'maxFlags': values['maxFlags'], 'tankButton': values['tankButton'],
              'colorNamesByWnx': values['colorNamesByWnx'],
              'colorClanTagsByWnx': values['colorClanTagsByWnx'],
              'colorVehiclesByWnx': values['colorVehiclesByWnx'],
              'showWnxBadges': values['showWnxBadges'],
              'sendLoadouts': values['sendLoadouts'],
              'sendReplays': values['sendReplays'],
              'measurePerformance': values['measurePerformance'],
              'autoReload': RELOAD_CHOICES.index(values['autoReload']),
              'minimapNames': MINIMAP_NAME_CHOICES.index(values['minimapNames']),
              'twitchChannel': values['twitch']['channel'],
              'twitchBattle': BATTLE_CHAT_CHOICES.index(values['twitch']['battle']),
              'twitchPanelText': TEXT_SIZE_CHOICES.index(values['twitch']['panelText']),
              'twitchBattleText': TEXT_SIZE_CHOICES.index(values['twitch']['battleText']),
              'twitchGarage': values['twitch']['garage'],
              'metric': METRICS.index(values['metric']), 'window': WINDOWS.index(values['window']),
              'winrate': EXTRAS.index(values['winrate']), 'battles': EXTRAS.index(values['battles']),
              'winrateDecimal': values['winrateDecimal']}
    for key in _ALT_KEYS:
        window[_alt_key(key)] = 1 if values['altOnly'][key] else 0
    for key in _MENU_KEYS:
        window[_menu_key(key)] = values['contextMenu'][key]
    for mode in MODES:
        teams = values['modes'][mode]
        window[_mode_key(mode)] = _choice_of(TEAM_CHOICES, teams['allies'], teams['enemies'])
    for surface in SURFACES:
        window[_show_key(surface)] = _choice_of(SHOW_CHOICES, values[surface]['rating'], values[surface]['flags'])
    for surface in FIGURED:
        window[_figures_key(surface)] = FIGURE_CHOICES.index(values[surface]['figures'])
    for surface in AVERAGED:
        window[surface + 'Average'] = values[surface]['average']
    window['battleRating'] = values['battle']['rating']
    window.update(wnx.to_window(values))
    from unicum.tracker import options as tracker
    tracked = tracker.validate(values.get('wnxTracker'))
    for key, choices in (('mode', tracker.MODES), ('count', tracker.COUNTS), ('opacity', tracker.OPACITIES)):
        window['tracker_' + key] = choices.index(tracked[key])
    window['settingsLanguage'] = LANGUAGES.index(values.get('settingsLanguage', 'en'))
    # updateModSettings replaces the API's entire dictionary. It indexes every
    # varName, including labels with buttons, when generating the window.
    from unicum.settings_window.labels import CONNECT_VAR, RESET_VAR, LINKS
    window.update((var, -1) for var in [CONNECT_VAR, RESET_VAR] + [item[0] for item in LINKS])
    return window

def from_window(raw):
    """settings.json changes from what the window sends back."""
    changes = wnx.from_window(raw)
    if isinstance(raw.get('battleRating'), bool):
        changes.setdefault('battle', {})['rating'] = raw['battleRating']
    from unicum.tracker import options as tracker
    for key, choices in (('mode', tracker.MODES), ('count', tracker.COUNTS), ('opacity', tracker.OPACITIES)):
        index = _index(raw.get('tracker_' + key), choices)
        if index is not None:
            changes.setdefault('wnxTracker', {})[key] = choices[index]
    language = _index(raw.get('settingsLanguage'), LANGUAGES)
    if language is not None:
        changes['settingsLanguage'] = LANGUAGES[language]
    for key in ('enabled', 'tankButton', 'sendLoadouts', 'sendReplays',
                'measurePerformance', 'winrateDecimal', 'colorNamesByWnx',
                'colorClanTagsByWnx', 'colorVehiclesByWnx', 'showWnxBadges'):
        if isinstance(raw.get(key), bool):
            changes[key] = raw[key]
    announced = _index(raw.get('autoReload'), RELOAD_CHOICES)
    if announced is not None:
        changes['autoReload'] = RELOAD_CHOICES[announced]
    labelled = _index(raw.get('minimapNames'), MINIMAP_NAME_CHOICES)
    if labelled is not None:
        changes['minimapNames'] = MINIMAP_NAME_CHOICES[labelled]
    context_menu = dict((key, bool(raw[_menu_key(key)])) for key in _MENU_KEYS
                        if isinstance(raw.get(_menu_key(key)), bool))
    if context_menu:
        changes['contextMenu'] = context_menu
    alt_only = dict((key, bool(raw[_alt_key(key)])) for key in _ALT_KEYS
                    if _index(raw.get(_alt_key(key)), WHEN_CHOICES) is not None)
    if alt_only:
        changes['altOnly'] = alt_only
    twitch = {}
    if isinstance(raw.get('twitchChannel'), basestring):
        twitch['channel'] = raw['twitchChannel']
    battle = _index(raw.get('twitchBattle'), BATTLE_CHAT_CHOICES)
    if battle is not None:
        twitch['battle'] = BATTLE_CHAT_CHOICES[battle]
    if isinstance(raw.get('twitchGarage'), bool):
        twitch['garage'] = raw['twitchGarage']
    for var, key in (('twitchPanelText', 'panelText'), ('twitchBattleText', 'battleText')):
        step = _index(raw.get(var), TEXT_SIZE_CHOICES)
        if step is not None:
            twitch[key] = TEXT_SIZE_CHOICES[step]
    if twitch:
        changes['twitch'] = twitch
    if _index(raw.get('metric'), METRICS) is not None:
        changes['metric'] = METRICS[raw['metric']]
    if _index(raw.get('window'), WINDOWS) is not None:
        changes['window'] = WINDOWS[raw['window']]
    for key in ('winrate', 'battles'):
        if _index(raw.get(key), EXTRAS) is not None:
            changes[key] = EXTRAS[raw[key]]
    if isinstance(raw.get('maxFlags'), (int, float)) and not isinstance(raw.get('maxFlags'), bool):
        changes['maxFlags'] = int(raw['maxFlags'])
    for surface in SURFACES:
        index = _index(raw.get(_show_key(surface)), SHOW_CHOICES)
        if index is not None:
            _, rating, flags = SHOW_CHOICES[index]
            changes[surface] = {'rating': rating, 'flags': flags}
    for surface in AVERAGED:
        value = raw.get(surface + 'Average')
        if isinstance(value, bool):
            changes.setdefault(surface, {})['average'] = value
    for surface in FIGURED:
        index = _index(raw.get(_figures_key(surface)), FIGURE_CHOICES)
        if index is not None:
            # Into whatever this surface already has in `changes`, not over
            # it: the show dropdown above writes its own dict for the same
            # surface, and the last one to assign would win.
            changes.setdefault(surface, {})['figures'] = FIGURE_CHOICES[index]
    modes = {}
    for mode in MODES:
        index = _index(raw.get(_mode_key(mode)), TEAM_CHOICES)
        if index is not None:
            _, allies, enemies = TEAM_CHOICES[index]
            modes[mode] = {'allies': allies, 'enemies': enemies}
    if modes:
        changes['modes'] = modes
    return changes

def _show_key(surface):
    return surface + 'Show'


def _figures_key(surface):
    return surface + 'Figures'

def _mode_key(mode):
    return 'mode%s' % (mode[0].upper() + mode[1:])

def _alt_key(key):
    return 'altOnly' + key.capitalize()

def _menu_key(key):
    return 'contextMenu' + key.capitalize()

def _choice_of(choices, first, second):
    """The index of the (label, first, second) option in `choices` matching two switches."""
    for index, (_, a, b) in enumerate(choices):
        if a == first and b == second:
            return index
    return 0

def _index(value, options):
    if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value < len(options):
        return int(value)
    return None
