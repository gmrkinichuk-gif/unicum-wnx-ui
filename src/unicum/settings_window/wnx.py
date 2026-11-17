"""One field catalog shared by the API page, native tabs and settings codec."""
from unicum.settings import wnx

FIELDS = (
    ('loading', 'background', 'WNX row background', None),
    ('loading', 'stripe', 'WNX colour stripe', None),
    ('loading', 'opacity', 'Background opacity', wnx.OPACITIES),
    ('loading', 'wnx', 'Show WNX', None),
    ('loading', 'winrate', 'Show win rate', None),
    ('loading', 'battles', 'Show battles', None),
    ('panel', 'background', 'WNX row background', None),
    ('panel', 'stripe', 'WNX colour stripe', None),
    ('panel', 'opacity', 'Background opacity', wnx.OPACITIES),
    ('panel', 'altStats', 'Statistics while holding Alt', wnx.ALT_STATS),
    ('panel', 'animation', 'Animate Alt transition', None),
    ('panel', 'duration', 'Transition duration (ms)', wnx.DURATIONS),
    ('tab', 'background', 'WNX row background', None),
    ('tab', 'opacity', 'Background opacity', wnx.OPACITIES),
    ('tab', 'wnx', 'Show WNX', None),
    ('tab', 'winrate', 'Show win rate', None),
    ('tab', 'battles', 'Show battles', None),
    ('tab', 'names', 'Nickname colour', wnx.TEXT_COLORS),
    ('tab', 'clans', 'Clan tag colour', wnx.TEXT_COLORS),
    ('tab', 'vehicles', 'Vehicle name colour', wnx.TEXT_COLORS),
    ('markers', 'stripe', 'WNX colour stripe', None),
    ('markers', 'missing', 'Players without WNX', wnx.MISSING),
)
TITLES = (('loading', 'Loading Screen'), ('panel', 'Battle Panels'),
          ('tab', 'Tab Scoreboard'), ('markers', 'Vehicle Markers'))
LABELS = {'adaptive': 'Adaptive (WNX in narrow modes)', 'wnx': 'WNX',
          'winrate': 'Win rate', 'battles': 'Battles', 'all': 'WNX / WR / battles',
          'neutral': 'Neutral grey stripe', 'hidden': 'Hide stripe',
          'light': 'Light', 'native': 'Game default'}


def var(surface, key):
    return 'wnx_' + surface + '_' + key


def labels(choices, key):
    return [str(value) + ('%' if key == 'opacity' else '') if isinstance(value, int)
            else LABELS[value] for value in choices]


def to_window(values):
    values = values.get('wnxUI', wnx.DEFAULTS)
    return dict((var(surface, key), choices.index(values[surface][key]) if choices
                 else values[surface][key]) for surface, key, _, choices in FIELDS)


def from_window(raw):
    changes = {}
    for surface, key, _, choices in FIELDS:
        value = raw.get(var(surface, key))
        if choices:
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < len(choices):
                continue
            value = choices[value]
        elif not isinstance(value, bool):
            continue
        changes.setdefault(surface, {})[key] = value
    return {'wnxUI': changes} if changes else {}


def api_rows(templates, window):
    rows = []
    for surface, title in TITLES:
        rows.append(templates.createLabel(title.upper()))
        for screen, key, label, choices in FIELDS:
            if screen != surface:
                continue
            name = var(screen, key)
            if choices:
                rows.append(templates.createDropdown(label, name, labels(choices, key), window[name], width=220))
            else:
                rows.append(templates.createCheckbox(label, name, window[name]))
    return rows


def native_rows(window):
    rows = []
    for surface, title in TITLES:
        rows += [u'tab\t' + title, u'group\t0\t' + title]
        for screen, key, label, choices in FIELDS:
            if screen != surface:
                continue
            name = var(screen, key)
            if choices:
                rows.append(u'dropdown\t%s\t%s\t%d\t0\t%s' %
                            (name, label, window[name], u'|'.join(labels(choices, key))))
            else:
                rows.append(u'checkbox\t%s\t%s\t%d' % (name, label, window[name]))
        rows += [u'group\t1\tBehaviour',
                 u'text\tChanges apply with Apply or OK. Cancel discards edits.']
        if surface == 'panel':
            rows.append(u'text\tFull mode keeps the vehicle name visible during Alt.')
        if surface == 'markers':
            rows.append(u'text\tThe stripe follows the native label and avoids HP and icons.')
    return rows
