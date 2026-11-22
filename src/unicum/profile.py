"""The shipped WNX-only feature, data and network boundary."""
from __future__ import absolute_import

import copy
import re
import urlparse

KEYS = ('enabled', 'settingsLanguage', 'metric', 'window', 'battles', 'winrate',
        'winrateDecimal', 'colorNamesByWnx', 'colorClanTagsByWnx',
        'colorVehiclesByWnx', 'showWnxBadges', 'wnxUI', 'wnxTracker',
        'battle', 'altOnly', 'modes')
VARS = set(('enabled', 'settingsLanguage', 'window', 'battles', 'winrate',
            'winrateDecimal', 'colorNamesByWnx', 'colorClanTagsByWnx',
            'colorVehiclesByWnx', 'showWnxBadges', 'battleAverage', 'battleRating',
            'battleFigures', 'resetSettings', 'resetDefaults'))
SCREENS = ('panel', 'tab', 'loading', 'markers')


def settings(values):
    """Persist only parameters needed by the retained surfaces."""
    from unicum.settings.wnx import DEFAULTS as WNX_DEFAULTS
    values = values if isinstance(values, dict) else {}
    result = dict((k, copy.deepcopy(values[k])) for k in KEYS if k in values)
    result['metric'] = 'wnx'
    for key, keys in (('wnxTracker', ('mode', 'count', 'opacity', 'position')),
                      ('battle', ('rating', 'average', 'figures')),
                      ('altOnly', SCREENS),
                      ('modes', ('random', 'ranked', 'onslaught', 'stronghold',
                                 'frontline', 'training', 'other'))):
        raw = result.get(key)
        if isinstance(raw, dict):
            result[key] = dict((k, raw[k]) for k in keys if k in raw)
    if isinstance(result.get('modes'), dict):
        result['modes'] = dict((k, dict((s, v[s]) for s in ('allies', 'enemies') if s in v))
                               for k, v in result['modes'].items() if isinstance(v, dict))
    raw = result.get('wnxUI')
    if isinstance(raw, dict):
        result['wnxUI'] = dict((s, dict((k, raw[s][k]) for k in defaults if k in raw[s]))
                               for s, defaults in WNX_DEFAULTS.items() if isinstance(raw.get(s), dict))
    return result


def runtime(values):
    """Compatibility values for shared renderers, with all legacy features off."""
    values['metric'] = 'wnx'
    for surface in ('contacts', 'profile', 'skirmishRoom', 'stronghold', 'battleResults'):
        values[surface].update(flags=False, rating=False, average=False)
    values['battle']['flags'] = False
    values.update(sendReplays=False, sendLoadouts=False, tankButton=False,
                  autoReload='off', measurePerformance=False)
    values['contextMenu'] = {'players': False, 'vehicles': False}
    values['twitch'].update(channel='', battle='off', garage=False)
    return values


def allowed_var(name):
    return (name in VARS or name.startswith(('wnx_', 'tracker_', 'mode'))
            or name in ('altOnlyPanel', 'altOnlyTab', 'altOnlyLoading', 'altOnlyMarkers'))


def window_values(values):
    return dict((k, v) for k, v in values.items() if allowed_var(k))


def native_page(text):
    output, tab, group, emitted_tab = [], None, None, None
    for line in text.split(u'\n'):
        parts = line.split(u'\t')
        if parts[0] == 'tab':
            tab, group = line, None
        elif parts[0] == 'group':
            group = line
        elif parts[0] in ('checkbox', 'dropdown', 'input', 'button') and allowed_var(parts[1]):
            if tab != emitted_tab:
                output.append(tab)
                emitted_tab = tab
            if group is not None:
                output.append(group)
                group = None
            output.append(line)
    return u'\n'.join(output)


def api_page(page):
    page = copy.deepcopy(page)
    for column in ('column1', 'column2'):
        page[column] = [row for row in page.get(column, [])
                        if allowed_var(row.get('varName', ''))]
    return page


def permits(url, headers=None, post_data=None):
    """Only public read requests required for WNX; no authentication or uploads."""
    parsed = urlparse.urlsplit(url)
    if parsed.scheme != 'https' or headers or post_data is not None or parsed.fragment:
        return False
    if parsed.netloc == 'api.tomato.gg':
        return parsed.path == '/api/wnx/wnx-expected-values.json' and not parsed.query
    if parsed.netloc != 'unicum.gg':
        return False
    if parsed.path == '/api/ratings/scales':
        return not parsed.query
    if not re.match(r'^/api/(eu|na|asia)/resolve$', parsed.path):
        return False
    query = urlparse.parse_qs(parsed.query, keep_blank_values=True)
    if not query or set(query) - set(('players', 'vehicles', 'mode')):
        return False
    for key in ('players', 'vehicles'):
        if key in query:
            if len(query[key]) != 1 or len(query[key][0].split(',')) > 100:
                return False
            pattern = r'^\d+(,\d+)*$' if key == 'players' else r'^\d+:\d+(,\d+:\d+)*$'
            if not re.match(pattern, query[key][0]):
                return False
    return ('players' in query or 'vehicles' in query) and (
        'mode' not in query or len(query['mode']) == 1 and
        query['mode'][0] in ('random', 'epic', 'stronghold_skirmish', 'stronghold_defense', 'globalmap'))
