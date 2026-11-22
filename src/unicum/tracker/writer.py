"""Serialize tracker journal operations outside the game thread."""
from collections import namedtuple
import logging
from Queue import Empty, Queue
from threading import Thread

from unicum.tracker.store import History

_logger = logging.getLogger('unicum.tracker.store')
HistoryView = namedtuple('HistoryView', 'rows error pending readonly')


class _LogQueue(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
        self._records = Queue()

    def emit(self, record):
        self._records.put_nowait(record)

    def flush_on_game_thread(self):
        # The host's log handlers and the optional mod error reporter may
        # call client APIs. Dispatch their records only from the game thread.
        while True:
            try:
                record = self._records.get_nowait()
            except Empty:
                return
            if _logger.isEnabledFor(record.levelno):
                _logger.handle(record)


class HistoryWriter(object):
    def __init__(self, session, region):
        self._region = region
        self._jobs, self._updates = Queue(), Queue()
        self._histories = {}
        self._retrying = set()
        self._log_queue = _LogQueue()
        self._log = logging.Logger(_logger.name, logging.WARNING)
        self._log.addHandler(self._log_queue)
        self._thread = Thread(target=self._run, name='Unicum WNX history')
        self._thread.daemon = True
        self._thread.start()
        session.on_close(self._close)

    def submit(self, account, operation, value=None):
        self._jobs.put_nowait((account, operation, value))

    def updates(self):
        self._log_queue.flush_on_game_thread()
        while True:
            try:
                yield self._updates.get_nowait()
            except Empty:
                return

    def _close(self):
        # A normal shutdown or reload drains the queue before another session
        # can open these journals. The game never waits for a write in play.
        self._jobs.put_nowait(None)
        self._thread.join()
        self._log_queue.flush_on_game_thread()

    def _run(self):
        while True:
            try:
                job = self._jobs.get(timeout=5) if self._retrying else self._jobs.get()
            except Empty:
                self._retry()
                continue
            if job is None:
                self._retry(force=True)
                return
            self._apply(*job)
            self._retry()

    def _publish(self, account, history):
        self._updates.put_nowait((account, HistoryView(
            tuple(row.copy() for row in history.rows), history.error,
            bool(history.pending), history.readonly)))

    def _apply(self, account, operation, value):
        history = self._histories.get(account)
        opened = history is None
        try:
            if opened:
                # A result can arrive before the first garage poll.
                history = self._histories[account] = History(self._region, account, logger=self._log)
            if operation == 'add' and not history.add(value) and not opened:
                return
            if operation == 'reset':
                history.reset(now=value)
        except Exception:
            self._log.exception('tracker history %s failed', operation)
            if history is None:
                self._updates.put_nowait((account, HistoryView((), 'storage_error', False, True)))
                return
            history.error = 'storage_error'
        if history.pending and not history.readonly:
            self._retrying.add(account)
        else:
            self._retrying.discard(account)
        self._publish(account, history)

    def _retry(self, force=False):
        for account in tuple(self._retrying):
            history = self._histories[account]
            if history.retry(force=force):
                self._retrying.discard(account)
                self._publish(account, history)
