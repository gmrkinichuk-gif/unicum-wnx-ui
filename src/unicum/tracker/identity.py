"""Local own-account identity, with no web token or linked-account storage."""
def current_account_id():
    try:
        import BigWorld
        value = getattr(BigWorld.player(), 'databaseID', None)
        if value:
            return str(value)
        import BattleReplay
        if BattleReplay.g_replayCtrl.isPlaying:
            return None
        from helpers import dependency
        from skeletons.gui.battle_session import IBattleSessionProvider
        value = dependency.instance(IBattleSessionProvider).getArenaDP().getVehicleInfo().player.accountDBID
        return str(value) if value else None
    except Exception:
        return None
