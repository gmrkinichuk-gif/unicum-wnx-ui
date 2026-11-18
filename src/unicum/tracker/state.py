"""Pure window mathematics; graphs retain holes instead of inventing zeroes."""
from unicum.tracker.formula import aggregate


def snapshot(rows, count, expected):
    current = rows[-count:]
    ready = len(current) == count
    score = aggregate(current, expected) if ready else None
    previous = aggregate(rows[-2 * count:-count], expected) if len(rows) >= 2 * count else None
    bars = [dict(row, wnx=aggregate([row], expected)) for row in current] if ready else []
    points = []
    if ready:
        for end in range(max(count, len(rows) - count + 1), len(rows) + 1):
            points.append({'wnx': aggregate(rows[end - count:end], expected),
                           'startedAt': rows[end - 1]['startedAt'],
                           'arenaUniqueId': rows[end - 1]['arenaUniqueId']})
    damage = sum(r['damageDealt'] for r in current) / float(count) if ready else None
    assist = (sum(r['damageAssistedRadio'] + r['damageAssistedTrack'] for r in current)
              / float(count)) if ready else None
    return {'count': count, 'progress': len(current), 'wnx': score,
            'delta': score - previous if score is not None and previous is not None else None,
            'reason': 'more_battles' if not ready else ('missing_expected' if score is None else ''),
            'damage': damage, 'assist': assist,
            'combined': damage + assist if ready else None, 'bars': bars, 'points': points}


def geometry(count, width=300.0):
    step = width / count
    return [(i * step + step * 0.17, step * 0.66, i * step, step) for i in range(count)]
