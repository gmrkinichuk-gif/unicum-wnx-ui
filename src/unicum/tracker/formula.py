"""AGPL-3.0 port of Unicum.gg ratings.ts (65f19c009bf4), Antoine Kingue.

Keep IEEE-754 division/NaN behaviour: zero frag/spot expectations are allowed
by upstream, and must not become a Python ZeroDivisionError or a fake zero.
"""
import math

from unicum.tracker.records import complete

KEYS = ('wExpDmg', 'wExpSpot', 'wExpFrag', 'wExpAssist',
        'wDmg', 'wSpot', 'wFrag', 'wAssist')


def finite(value):
    if not isinstance(value, (int, long, float)) or isinstance(value, bool):
        return False
    try:
        return not math.isnan(value) and not math.isinf(value)
    except OverflowError:
        return False


def divide(a, b):
    return a / float(b) if b else (float('nan') if not a else float('inf'))


def corrected(value, cap):
    return float('nan') if math.isnan(value) else max(0, min(cap, value))


def zero():
    return dict((key, 0.0) for key in KEYS)


def add(acc, tank, expected):
    exp = expected.get(tank['tank_id'])
    stats = tank.get('all') or {}
    battles = stats.get('battles', 0)
    if exp is None or battles <= 0:
        return
    for target, source in (('wExpDmg', 'damage'), ('wExpSpot', 'spots'),
                           ('wExpFrag', 'frags'), ('wExpAssist', 'assist')):
        acc[target] += battles * exp[source]
    for target, source in (('wDmg', 'damage_dealt'), ('wSpot', 'spotted'),
                           ('wFrag', 'frags')):
        acc[target] += stats[source]
    acc['wAssist'] += stats.get('radio_assisted_damage', 0) + stats.get('track_assisted_damage', 0)


def finalize(acc):
    if acc['wExpDmg'] <= 0:
        return None
    ratio = divide(acc['wDmg'] + acc['wAssist'] * 0.67,
                   acc['wExpDmg'] + acc['wExpAssist'] * 0.67)
    damage = corrected((ratio - 0.22) / (1 - 0.22), ratio - 0.22)
    frags = corrected((divide(acc['wFrag'], acc['wExpFrag']) - 0.12) / (1 - 0.12), damage + 0.4)
    spots = corrected((divide(acc['wSpot'], acc['wExpSpot']) - 0.38) / (1 - 0.38), damage + 0.2)
    raw = 750 * damage + 200 * frags + 50 * spots
    result = raw * (raw / 1000) ** 0.45 * 1.65
    return result if finite(result) else None


def compute(tanks, expected):
    acc = zero()
    for tank in tanks:
        add(acc, tank, expected)
    return finalize(acc)


def battle_tank(row):
    return {'tank_id': row['tankId'], 'all': {
        'battles': 1, 'damage_dealt': row['damageDealt'],
        'spotted': row['spotted'], 'frags': row['frags'],
        'radio_assisted_damage': row['damageAssistedRadio'],
        'track_assisted_damage': row['damageAssistedTrack']}}


def aggregate(rows, expected):
    # A partial window is not the requested window. Never skip missing tanks.
    if not rows or any(not complete(row) or row['tankId'] not in expected for row in rows):
        return None
    return compute([battle_tank(row) for row in rows], expected)
