"""Pure window mathematics; graphs retain holes instead of inventing zeroes."""
from unicum.tracker.formula import aggregate
from unicum.tracker.records import complete


def _rating(rows, expected):
    score = aggregate(rows, expected)
    if score is not None:
        return {'wnx': score, 'reason': ''}
    if any(not complete(row) for row in rows):
        reason = 'incomplete_results'
    elif not expected:
        reason = 'expected_unavailable'
    elif any(row['tankId'] not in expected for row in rows):
        reason = 'missing_expected'
    else:
        reason = 'wnx_unavailable'
    return {'wnx': None, 'reason': reason}


def _average(rows, count, fields):
    if len(rows) != count or any(row.get(field) is None for row in rows for field in fields):
        return None
    return sum(row[field] for row in rows for field in fields) / float(count)


def snapshot(rows, count, expected):
    current = rows[-count:]
    ready = len(current) == count
    rating = _rating(current, expected) if ready else {'wnx': None, 'reason': 'more_battles'}
    score = rating['wnx']
    previous = aggregate(rows[-2 * count:-count], expected) if len(rows) >= 2 * count else None
    bars = [dict(row, **_rating([row], expected)) for row in current] if ready else []
    points = []
    if ready:
        for end in range(max(count, len(rows) - count + 1), len(rows) + 1):
            points.append(dict(_rating(rows[end - count:end], expected),
                               startedAt=rows[end - 1]['startedAt'],
                               arenaUniqueId=rows[end - 1]['arenaUniqueId']))
    damage = _average(current, count, ('damageDealt',))
    assist = _average(current, count, ('damageAssistedRadio', 'damageAssistedTrack'))
    return dict(rating, count=count, progress=len(current),
                delta=score - previous if score is not None and previous is not None else None,
                damage=damage, assist=assist,
                bars=bars, points=points)


def geometry(count, width=300.0):
    step = width / count
    return [(i * step + step * 0.17, step * 0.66, i * step, step) for i in range(count)]
