"""Small fsynced journal; a torn final line never destroys earlier battles."""
import copy
import json
import logging
import os
import time

from unicum.runtime.files import recover, replace
from unicum.tracker.formula import finite
from unicum.tracker.records import (COMPLETE_SCHEMA, PARTIAL_SCHEMA, RATING_FIELDS,
                                    complete, identifier, valid_start)

_logger = logging.getLogger('unicum.tracker.store')
ROOT = os.path.join('mods', 'configs', 'unicum', 'wnx_tracker')
LIMIT = 60


def _existing_index(rows, row):
    arena = row['arenaUniqueId']
    return next((i for i, current in enumerate(rows) if current['arenaUniqueId'] == arena), None)


class History(object):
    def __init__(self, region, account_id, root=ROOT, logger=_logger):
        if region not in ('eu', 'na', 'asia') or not str(account_id).isdigit():
            raise ValueError('invalid tracker identity')
        self.region, self.account = region, str(account_id)
        self._logger = logger
        self.path = os.path.join(root, region, self.account, 'history.jsonl')
        self.rows, self.epoch, self.deleted = [], 0, set()
        self.error, self.readonly, self._events = None, False, 0
        self.pending, self._retry_at = [], 0
        self._load()

    def _valid(self, row):
        if not isinstance(row, dict) or (row.get('region'), row.get('accountId')) != (self.region, self.account):
            return False
        arena = row.get('arenaUniqueId')
        if not isinstance(arena, basestring) or identifier(arena) != arena:
            return False
        if not valid_start(row.get('startedAt')) or not finite(row.get('battleType')) or row['battleType'] < 0:
            return False
        schema = row.get('schemaVersion')
        if schema != (COMPLETE_SCHEMA if complete(row) else PARTIAL_SCHEMA):
            return False
        tank = row.get('tankId')
        return ((tank is None or (finite(tank) and int(tank) == tank and tank > 0))
                and all(key in row and (row[key] is None or (finite(row[key]) and row[key] >= 0))
                        for key in RATING_FIELDS))

    def _put(self, row):
        if (not self._valid(row) or row['startedAt'] <= self.epoch
                or row['arenaUniqueId'] in self.deleted):
            return False
        known = _existing_index(self.rows, row)
        if known is None:
            if len(self.rows) == LIMIT and row['startedAt'] <= self.rows[0]['startedAt']:
                return False
            self.rows.append(copy.deepcopy(row))
        else:
            if complete(self.rows[known]) or not complete(row):
                return False
            self.rows[known] = copy.deepcopy(row)
        self.rows.sort(key=lambda r: (r['startedAt'], int(r['arenaUniqueId'])))
        self.rows = self.rows[-LIMIT:]
        return True

    def _load(self):
        try:
            recover(self.path)
        except OSError:
            self.error, self.readonly = 'storage_error', True
            self._logger.exception('could not recover committed tracker journal')
            return
        if not os.path.exists(self.path):
            return
        broken = False
        try:
            with open(self.path, 'rb') as handle:
                for line in handle:
                    try:
                        item = json.loads(line)
                        if (not isinstance(item, dict)
                                or item.get('schemaVersion') not in (COMPLETE_SCHEMA, PARTIAL_SCHEMA)):
                            self.readonly = True
                            raise ValueError('unsupported journal schema')
                        if item.get('kind') in ('snapshot', 'reset'):
                            epoch = item.get('resetEpoch', 0)
                            deleted = item.get('deleted', [])
                            if not finite(epoch) or epoch < 0 or not isinstance(deleted, list):
                                raise ValueError('invalid reset watermark')
                            self.epoch = max(self.epoch, epoch)
                            self.deleted.update(str(v) for v in deleted)
                            self.rows = []
                            for row in item.get('rows', []):
                                self._put(row)
                        elif item.get('kind') == 'battle':
                            row = item.get('row')
                            if not self._valid(row):
                                raise ValueError('invalid battle record')
                            self._put(row)
                        else:
                            raise ValueError('unknown journal event')
                        self._events += 1
                    except (ValueError, TypeError, KeyError):
                        broken = True
                        self._logger.warning('invalid tracker journal record')
            if broken:
                self.error = 'history_recovered'
                if not self.readonly:
                    # Preserve the evidence before repairing, including partial tails.
                    import shutil
                    shutil.copy2(self.path, self.path + '.corrupt-%d' % time.time())
                    self._compact()
        except (IOError, OSError):
            self.error = 'storage_error'
            self.readonly = True
            self._logger.exception('could not load local tracker history')

    def _append(self, item):
        if self.readonly:
            raise IOError('tracker history is read-only')
        folder = os.path.dirname(self.path)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        with open(self.path, 'ab') as handle:
            handle.write(json.dumps(item, separators=(',', ':'), allow_nan=False) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        self._events += 1

    def _snapshot(self):
        # An earlier candidate treats a newer envelope as read-only and
        # leaves the partial results intact for the current reader.
        version = PARTIAL_SCHEMA if any(not complete(row) for row in self.rows) else COMPLETE_SCHEMA
        return {'schemaVersion': version, 'kind': 'snapshot', 'resetEpoch': self.epoch,
                'deleted': sorted(self.deleted), 'rows': self.rows}

    def _compact(self, snapshot=None):
        if self.readonly:
            raise IOError('tracker history is read-only')
        folder = os.path.dirname(self.path)
        if not os.path.isdir(folder):
            os.makedirs(folder)
        temporary = self.path + '.tmp'
        with open(temporary, 'wb') as handle:
            handle.write(json.dumps(snapshot or self._snapshot(), separators=(',', ':')) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        replace(temporary, self.path)
        self._events = 1

    def add(self, row):
        before = self.rows[:]
        if not self._put(row):
            return False
        try:
            if self.pending:
                raise IOError('tracker history is awaiting journal repair')
            self._append({'schemaVersion': row['schemaVersion'], 'kind': 'battle', 'row': row})
        except (IOError, OSError):
            self.rows = before
            self.error = 'storage_error'
            queued = _existing_index(self.pending, row)
            if queued is None:
                self.pending = (self.pending + [copy.deepcopy(row)])[-LIMIT:]
            elif not complete(self.pending[queued]) and complete(row):
                self.pending[queued] = copy.deepcopy(row)
            if not self._retry_at:
                self._retry_at = time.time() + 5
            raise
        if self._events > LIMIT or (len(before) == LIMIT and before[0] != self.rows[0]):
            try:
                self._compact()
            except (IOError, OSError):
                self._logger.exception('tracker compaction deferred; journal is intact')
        return True

    def retry(self, force=False):
        if not self.pending or self.readonly or (not force and time.time() < self._retry_at):
            return False
        self._retry_at = time.time() + 5
        before = self.rows[:]
        try:
            for row in self.pending:
                self._put(row)
            # Repair any partial failed append as well as persisting the retry.
            self._compact()
            self.pending, self.error = [], None
            self._retry_at = 0
            return True
        except (IOError, OSError):
            self.rows = before
            return False

    def reset(self, now=None):
        epoch = time.time() if now is None else now
        deleted = set(self.deleted) | set(row['arenaUniqueId'] for row in self.rows + self.pending)
        try:
            self._compact({'schemaVersion': COMPLETE_SCHEMA, 'kind': 'snapshot', 'rows': [],
                           'resetEpoch': epoch, 'deleted': sorted(deleted)})
        except (IOError, OSError):
            self.error = 'storage_error'
            raise
        self.epoch, self.deleted, self.rows, self.pending = epoch, deleted, [], []
        self.error, self._retry_at = None, 0
        previous = self.path + '.previous'
        if os.path.exists(previous):
            try:
                os.unlink(previous)
            except OSError:
                self._logger.warning('tracker reset committed but previous journal could not be removed')
