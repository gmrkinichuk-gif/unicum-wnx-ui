"""Strict own-account extraction from confirmed results, with no name matching."""
from unicum.tracker.formula import finite
from unicum.tracker.records import (COMPLETE_SCHEMA, METRICS, PARTIAL_SCHEMA,
                                    complete, identifier, valid_start)


def result_account(results):
    """The private avatar block that WoT uses for its own post-battle view."""
    personal = results.get('personal') if isinstance(results, dict) else None
    avatar = personal.get('avatar') if isinstance(personal, dict) else None
    return identifier(avatar.get('accountDBID')) if isinstance(avatar, dict) else None


def extract(results, region, account_id, constants=None):
    from unicum.modes import mode_of
    account = identifier(account_id)
    if not isinstance(results, dict) or not account:
        return None
    owner = result_account(results)
    if owner and owner != account:
        return None
    common = results.get('common')
    if not isinstance(common, dict):
        return None
    bonus = common.get('bonusType')
    if (not isinstance(bonus, (int, long)) or isinstance(bonus, bool)
            or mode_of(bonus, constants) != 'random'):
        return None
    arena = identifier(results.get('arenaUniqueID'))
    started = common.get('arenaCreateTime')
    if not arena or not valid_start(started):
        return None
    matches = []
    vehicles = results.get('vehicles')
    if isinstance(vehicles, dict):
        for value in vehicles.values():
            for row in value if isinstance(value, (list, tuple)) else [value]:
                if isinstance(row, dict) and identifier(row.get('accountDBID')) == account:
                    matches.append(row)
    if not matches and owner != account:
        return None
    # The private avatar or a participant match establishes the battle. An
    # absent or ambiguous vehicle still leaves a hole at its chronological slot.
    own = matches[0] if len(matches) == 1 else {}
    tank = own.get('typeCompDescr')
    row = {'tankId': int(tank) if finite(tank) and tank > 0 and int(tank) == tank else None}
    for key in METRICS:
        value = own.get('kills' if key == 'frags' else key)
        row[key] = value if finite(value) and value >= 0 else None
    team, winner = own.get('team'), common.get('winnerTeam')
    outcome = None
    if team in (1, 2) and winner in (0, 1, 2):
        outcome = 'draw' if winner == 0 else ('win' if winner == team else 'loss')
    row.update(schemaVersion=COMPLETE_SCHEMA if complete(row) else PARTIAL_SCHEMA,
               region=region, accountId=account,
               arenaUniqueId=arena, startedAt=int(started), battleType=bonus, winnerResult=outcome)
    return row
