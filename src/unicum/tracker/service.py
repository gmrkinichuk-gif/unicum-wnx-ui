"""Account-bound local consumer; never enables or invokes server uploading."""
import logging

from unicum import config
from unicum.tracker.extract import extract
from unicum.tracker.store import History

_logger = logging.getLogger('unicum.tracker')


def playing_replay():
    try:
        import BattleReplay
        return bool(BattleReplay.g_replayCtrl.isPlaying)
    except ImportError:
        return False


class Tracker(object):
    def __init__(self, session):
        self.session, self.history, self.account = session, None, None
        self.revision = 0
        self._pending = []
        self._histories = {}

    def identify(self):
        if playing_replay():
            return None
        from unicum.game_link.proof import current_account_id
        account = current_account_id()
        if account and account != self.account:
            if account not in self._histories:
                self._histories[account] = History(config.REGION, account)
            self.history = self._histories[account]
            self.account = account
            self.revision += 1
        if account and self.history.retry():
            self.revision += 1
        if account and self._pending:
            pending, self._pending = self._pending, []
            for result in pending:
                self.record(result)
        return account

    def record(self, results):
        if not self.session.alive or playing_replay():
            return
        account = self.identify()
        if not account:
            if results not in self._pending:
                self._pending = (self._pending + [results])[-20:]
            _logger.warning('tracker result deferred: own account identity unavailable')
            return
        row = extract(results, config.REGION, account)
        if row is not None and self.history.add(row):
            self.revision += 1

    def reset(self, identity):
        account = self.identify()
        if not account or (config.REGION, account) != identity:
            raise ValueError('tracker account changed during confirmation')
        self.history.reset()
        self.revision += 1
