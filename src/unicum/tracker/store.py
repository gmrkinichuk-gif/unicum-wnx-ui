"""Small fsynced journal; a torn final line never destroys earlier battles."""
import copy
import json
import logging
import os
import time

from unicum.tracker.formula import finite

_logger = logging.getLogger('unicum.tracker.store')
ROOT = os.path.join('mods', 'configs', 'unicum', 'wnx_tracker')
LIMIT = 200


def replace(source, target):
    """Use built-in file operations available in the shipped WoT Python.

    Windows Python 2 cannot rename over a file. Keep the last committed copy
    recoverable if the process dies between the two renames.
    """
    if os.name != 'nt' or not os.path.exists(target):
        os.rename(source, target)
        return
    previous = target + '.previous'
    if os.path.exists(previous):
        os.unlink(previous)
    os.rename(target, previous)
    try:
        os.rename(source, target)
    except OSError:
        os.rename(previous, target)
        raise


def recover(path):
    previous = path + '.previous'
    if not os.path.exists(path) and os.path.exists(previous):
        os.rename(previous, path)


class History(object):
    def __init__(self, region, account_id, root=ROOT):
        if region not in ('eu', 'na', 'asia') or not str(account_id).isdigit():
            raise ValueError('invalid tracker identity')
        self.region, self.account = region, str(account_id)
        self.path = os.path.join(root, region, self.account, 'history.jsonl')
        self.rows, self.epoch, self.deleted = [], 0, set()
        self.error, self.readonly, self._events = None, False, 0
        self.pending, self._retry_at = [], 0
        self._load()

    def _valid(self, row):
        return (isinstance(row, dict) and row.get('schemaVersion') == 1
                and row.get('region') == self.region and row.get('accountId') == self.account
                and isinstance(row.get('arenaUniqueId'), basestring)
                and row['arenaUniqueId'].isdigit() and int(row['arenaUniqueId']) > 0
                and all(finite(row.get(key)) and row[key] >= 0 for key in
                        ('startedAt', 'tankId', 'battleType', 'damageDealt',
                         'damageAssistedRadio', 'damageAssistedTrack', 'frags', 'spotted'))
                and row['startedAt'] > 0 and row['tankId'] > 0)

    def _put(self, row):
        if (not self._valid(row) or row['startedAt'] <= self.epoch
                or row['arenaUniqueId'] in self.deleted
                or any(r['arenaUniqueId'] == row['arenaUniqueId'] for r in self.rows)):
            return False
        if len(self.rows) == LIMIT and row['startedAt'] <= self.rows[0]['startedAt']:
            return False
        self.rows.append(copy.deepcopy(row))
        self.rows.sort(key=lambda r: (r['startedAt'], int(r['arenaUniqueId'])))
        self.rows = self.rows[-LIMIT:]
        return True

    def _load(self):
        try:
            recover(self.path)
        except OSError:
            self.error, self.readonly = 'storage_error', True
            _logger.exception('could not recover committed tracker journal')
            return
        if not os.path.exists(self.path):
            return
        broken = False
        try:
            with open(self.path, 'rb') as handle:
                for line in handle:
                    try:
                        item = json.loads(line)
                        if not isinstance(item, dict) or item.get('schemaVersion') != 1:
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
                        _logger.warning('invalid tracker journal record')
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
            _logger.exception('could not load local tracker history')

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
        return {'schemaVersion': 1, 'kind': 'snapshot', 'resetEpoch': self.epoch,
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
            self._append({'schemaVersion': 1, 'kind': 'battle', 'row': row})
        except (IOError, OSError):
            self.rows = before
            self.error = 'storage_error'
            if not any(r['arenaUniqueId'] == row['arenaUniqueId'] for r in self.pending):
                self.pending = (self.pending + [copy.deepcopy(row)])[-LIMIT:]
            if not self._retry_at:
                self._retry_at = time.time() + 5
            raise
        if self._events > 400:
            try:
                self._compact()
            except (IOError, OSError):
                _logger.exception('tracker compaction deferred; journal is intact')
        return True

    def retry(self):
        if not self.pending or self.readonly or time.time() < self._retry_at:
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
            self._compact({'schemaVersion': 1, 'kind': 'snapshot', 'rows': [],
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
                _logger.warning('tracker reset committed but previous journal could not be removed')
