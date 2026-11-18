"""Reorganize the complete native control catalog, without duplicating its schema."""
from unicum.settings_window.codec import to_window
from unicum.tracker import options
from unicum.tracker.localize import translate

CATEGORIES = ('General', 'WNX Tracker', 'Battle', 'Garage', 'Integrations')
GENERAL = set(('enabled', 'settingsLanguage', 'metric', 'window', 'winrate',
               'battles', 'winrateDecimal', 'maxFlags', 'measurePerformance', 'resetDefaults'))


def category(var):
    if var.startswith('tracker_'):
        return 'WNX Tracker'
    if var in GENERAL:
        return 'General'
    if (var.startswith(('twitch', 'hide', 'send', 'account', 'link'))
            or var in ('support', 'discord', 'source')):
        return 'Integrations'
    if (var.startswith(('wnx_', 'mode', 'color')) or var in ('showWnxBadges', 'autoReload', 'minimapNames')
            or var.startswith('battle') and not var.startswith('battleResults')
            or var in ('altOnlyMarkers', 'altOnlyPanel', 'altOnlyTab', 'altOnlyLoading', 'altOnlyMinimap')):
        return 'Battle'
    return 'Garage'


def build(native, values, expected):
    language = values.get('settingsLanguage', 'en')
    output = dict((key, []) for key in CATEGORIES)
    group = ''
    for line in native.split(u'\n'):
        parts = line.split(u'\t')
        kind = parts[0]
        if kind == 'group':
            group = parts[2]
        if kind not in ('checkbox', 'dropdown', 'button', 'input'):
            continue
        var = parts[1]
        row = {'kind': kind, 'var': var, 'label': parts[2], 'group': group}
        if kind == 'dropdown':
            row.update(value=int(parts[3]) + int(parts[4]), offset=int(parts[4]), options=parts[5].split('|'))
        elif kind == 'checkbox':
            row['value'] = parts[3] == '1'
        else:
            row['value' if kind == 'input' else 'word'] = parts[3] if len(parts) > 3 else ''
        # The reset action is deliberately separate from tracker history reset.
        if var == 'resetSettings':
            target = 'General'
        else:
            target = category(var)
        output[target].append(row)
    window = to_window(values)
    for key, label, choices in (
            ('mode', 'Display mode', options.MODES),
            ('count', 'Random battles in window', options.COUNTS),
            ('opacity', 'Background opacity', options.OPACITIES)):
        output['WNX Tracker'].append({'kind': 'dropdown', 'var': 'tracker_' + key,
            'label': translate(label, language), 'value': window['tracker_' + key],
            'offset': 0, 'options': [str(v) + ('%' if key == 'opacity' else '') for v in choices], 'group': ''})
    for var, label in (('tracker_reset', 'Reset statistics...'), ('tracker_position', 'Reset position')):
        output['WNX Tracker'].append({'kind': 'button', 'var': var, 'label': translate(label, language),
                                     'word': translate('Reset', language), 'danger': var == 'tracker_reset', 'group': ''})
    status = translate('Expected values', language) + ': ' + (expected.updated or translate('Unavailable', language))
    output['WNX Tracker'].append({'kind': 'text', 'label': status, 'group': ''})
    return [{'id': key, 'title': translate(key, language), 'rows': output[key]} for key in CATEGORIES]
