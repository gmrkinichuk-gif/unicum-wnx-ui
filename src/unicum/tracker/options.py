"""Additive tracker settings; normalized coordinates survive viewport changes."""
import copy
from unicum.tracker.formula import finite

MODES = ('Mini', 'Compact', 'Trend', 'Battles')
COUNTS = (10, 20, 30)
OPACITIES = (40, 50, 60, 70, 80, 90)
DEFAULTS = {'mode': 'Compact', 'count': 20, 'opacity': 60, 'position': None}


def validate(raw):
    result = copy.deepcopy(DEFAULTS)
    if not isinstance(raw, dict):
        return result
    for key, choices in (('mode', MODES), ('count', COUNTS), ('opacity', OPACITIES)):
        if not isinstance(raw.get(key), bool) and raw.get(key) in choices:
            result[key] = raw[key]
    position = raw.get('position')
    if (isinstance(position, list) and len(position) == 2
            and all(finite(v) for v in position)):
        result['position'] = [max(0.0, min(1.0, float(v))) for v in position]
    return result
