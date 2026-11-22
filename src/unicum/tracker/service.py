"""Account-bound local consumer; never enables or invokes server uploading."""
import logging
import time

from unicum import config
from unicum.tracker.extract import extract, result_account
from unicum.tracker.writer import HistoryWriter

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
        self._views = {}
        self._requested = set()
        self._writer = HistoryWriter(session, config.REGION)

    def identify(self):
        if playing_replay():
            return None
        from unicum.tracker.identity import current_account_id
        account = current_account_id()
        if account and account not in self._requested:
            self._writer.submit(account, 'load')
            self._requested.add(account)
        for owner, view in self._writer.updates():
            self._views[owner] = view
        view = self._views.get(account)
        if account != self.account or view is not self.history:
            self.account, self.history = account, view
            self.revision += 1
        return account

    def record(self, results):
        if not self.session.alive or playing_replay():
            return
        from unicum.tracker.identity import current_account_id
        # A result's own avatar still names its owner during login transitions,
        # including when a callback for the previous account arrives late.
        current = current_account_id()
        owner = result_account(results)
        if owner and current and owner != current:
            return
        account = owner or current
        if not account:
            _logger.warning('tracker result has no verified account; waiting for a confirmed result')
            return
        row = extract(results, config.REGION, account)
        if row is not None:
            self._writer.submit(account, 'add', row)
            self._requested.add(account)

    def reset(self, identity):
        account = self.identify()
        if not account or (config.REGION, account) != identity:
            raise ValueError('tracker account changed during confirmation')
        self._writer.submit(account, 'reset', time.time())
