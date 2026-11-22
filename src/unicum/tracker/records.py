"""Fields required for an exact local WNX calculation."""
import time

METRICS = ('damageDealt', 'damageAssistedRadio', 'damageAssistedTrack', 'spotted', 'frags')
RATING_FIELDS = ('tankId',) + METRICS
COMPLETE_SCHEMA = 1
PARTIAL_SCHEMA = 2


def complete(row):
    return all(row.get(key) is not None for key in RATING_FIELDS)


def identifier(value):
    if isinstance(value, (int, long)) and not isinstance(value, bool) and value > 0:
        return str(value)
    if isinstance(value, basestring) and value and not value.strip('0123456789') and int(value) > 0:
        return str(int(value))
    return None


def valid_start(value):
    if not isinstance(value, (int, long, float)) or isinstance(value, bool) or not value >= 1:
        return False
    try:
        time.localtime(value)
    except (OverflowError, ValueError, OSError):
        return False
    return True
