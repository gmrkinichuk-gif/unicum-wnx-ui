"""Strict own-account extraction from confirmed results, with no name matching."""
from unicum.tracker.formula import finite

METRICS = ('damageDealt', 'damageAssistedRadio', 'damageAssistedTrack', 'spotted')


def extract(results, region, account_id, constants=None):
    from unicum.modes import mode_of
    if not isinstance(results, dict) or not account_id:
        return None
    common = results.get('common') or {}
    if mode_of(common.get('bonusType'), constants) != 'random':
        return None
    arena = results.get('arenaUniqueID')
    started = common.get('arenaCreateTime')
    if (not isinstance(arena, (int, long, basestring)) or isinstance(arena, bool)
            or not str(arena).isdigit() or int(arena) <= 0
            or not finite(started) or started <= 0):
        return None
    matches = []
    vehicles = results.get('vehicles')
    if not isinstance(vehicles, dict):
        return None
    for value in vehicles.values():
        for row in value if isinstance(value, (list, tuple)) else [value]:
            if isinstance(row, dict) and str(row.get('accountDBID')) == str(account_id):
                matches.append(row)
    if len(matches) != 1:
        return None
    own = matches[0]
    tank = own.get('typeCompDescr')
    if not finite(tank) or tank <= 0 or int(tank) != tank:
        return None
    metrics = dict((key, own.get(key)) for key in METRICS)
    metrics['frags'] = own.get('kills')
    if any(not finite(v) or v < 0 for v in metrics.values()):
        return None
    team, winner = own.get('team'), common.get('winnerTeam')
    outcome = None
    if team in (1, 2) and winner in (0, 1, 2):
        outcome = 'draw' if winner == 0 else ('win' if winner == team else 'loss')
    metrics.update(schemaVersion=1, region=region, accountId=str(account_id),
                   arenaUniqueId=str(arena), startedAt=int(started),
                   battleType=common['bonusType'], tankId=int(tank), winnerResult=outcome)
    return metrics
