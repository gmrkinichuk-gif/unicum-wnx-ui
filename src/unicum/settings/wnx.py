"""Validated, backwards-compatible controls for the redesigned battle surfaces."""
import copy

OPACITIES = tuple(range(0, 101, 10))
DURATIONS = (50, 100, 150, 200, 250, 300)
ALT_STATS = ('adaptive', 'wnx', 'winrate', 'battles', 'all')
MISSING = ('neutral', 'hidden')
TEXT_COLORS = ('light', 'native', 'wnx')

DEFAULTS = {
    'loading': {'background': True, 'stripe': True, 'opacity': 50,
                'wnx': True, 'winrate': True, 'battles': True},
    'panel': {'background': True, 'stripe': True, 'opacity': 40,
              'altStats': 'adaptive', 'animation': True, 'duration': 150},
    'tab': {'background': True, 'opacity': 40, 'wnx': True,
            'winrate': True, 'battles': True,
            'names': 'light', 'clans': 'light', 'vehicles': 'light'},
    'markers': {'stripe': True, 'missing': 'neutral'},
}


def validate(raw):
    values = copy.deepcopy(DEFAULTS)
    if not isinstance(raw, dict):
        return values
    choices = {'opacity': OPACITIES, 'duration': DURATIONS, 'altStats': ALT_STATS,
               'missing': MISSING, 'names': TEXT_COLORS, 'clans': TEXT_COLORS,
               'vehicles': TEXT_COLORS}
    for surface, defaults in DEFAULTS.items():
        given = raw.get(surface, {})
        if not isinstance(given, dict):
            continue
        for key, default in defaults.items():
            value = given.get(key)
            if isinstance(default, bool):
                if isinstance(value, bool):
                    values[surface][key] = value
            elif not isinstance(value, bool) and value in choices[key]:
                values[surface][key] = value
    return values


def options(settings):
    # Small fake/older settings providers need the same defaults as a legacy file.
    try:
        values = settings['wnxUI']
        return values if isinstance(values, dict) else copy.deepcopy(DEFAULTS)
    except (KeyError, TypeError):
        return copy.deepcopy(DEFAULTS)


def flash_options(settings):
    values = options(settings)
    loading, panel = values['loading'], values['panel']
    fields = [loading[k] for k in ('background', 'stripe', 'opacity', 'wnx', 'winrate', 'battles')]
    fields += [panel[k] for k in ('background', 'stripe', 'opacity')]
    fields += [ALT_STATS.index(panel['altStats']), panel['animation'], panel['duration']]
    return ','.join(str(int(value)) for value in fields)
