"""The exact public origin used by Unicum.gg, cached without a bundled snapshot."""
import hashlib
import json
import logging
import os
import time

from unicum.tracker.formula import finite
from unicum.runtime.files import recover, replace

ORIGIN = 'https://api.tomato.gg/api/wnx/wnx-expected-values.json'
STORE = os.path.join('mods', 'configs', 'unicum', 'wnx_tracker', 'expected.json')
_logger = logging.getLogger('unicum.tracker.expected')


def parse(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
        raise ValueError('invalid expected table')
    table = {}
    for row in payload['data']:
        tank = row.get('tank_id') if isinstance(row, dict) else None
        if not finite(tank) or tank <= 0 or int(tank) != tank or int(tank) in table:
            raise ValueError('invalid/duplicate expected tank id')
        values = dict((key, row.get(source)) for key, source in (
            ('damage', 'expected_damage'), ('frags', 'expected_frags'),
            ('spots', 'expected_spots'), ('assist', 'expected_assistance')))
        if any(not finite(v) or v < 0 for v in values.values()) or values['damage'] <= 0:
            raise ValueError('invalid expected metrics')
        table[int(tank)] = values
    if not table:
        raise ValueError('empty expected table')
    return table


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()


class Expected(object):
    def __init__(self, session, store=STORE):
        self.session, self.store = session, store
        self.table, self.version, self.updated = {}, None, None
        self.fetched, self.retry, self.busy = 0, 0, False
        self._pending = None
        self._load()

    def _load(self):
        try:
            recover(self.store)
            with open(self.store, 'rb') as handle:
                cache = json.load(handle)
            payload = cache['payload']
            if (cache.get('schemaVersion') != 1 or cache.get('source') != ORIGIN
                    or digest(payload) != cache['sha256'] or not finite(cache.get('fetchedAt'))):
                raise ValueError('invalid expected cache')
            self.table = parse(payload)
            self.version, self.fetched = cache['sha256'], cache['fetchedAt']
            self.updated = (payload.get('meta') or {}).get('updated')
        except (IOError, OSError, ValueError, TypeError, KeyError):
            if os.path.exists(self.store):
                _logger.warning('expected cache unusable; raw history is retained')

    def refresh(self):
        if self._pending is not None:
            response, self._pending = self._pending, None
            self._received(response)
        now = time.time()
        if self.busy or now < self.retry or now - self.fetched < 86400:
            return
        self.busy = True
        self.retry = now + 300
        try:
            self.session.fetch(ORIGIN, self._received, timeout=15.0)
        except Exception:
            self.busy = False
            _logger.exception('expected fetch could not start; retry is bounded')

    def _received(self, response):
        self.busy = False
        from helpers import isPlayerAccount
        if not isPlayerAccount():
            self._pending = response
            return
        try:
            if response.responseCode != 200:
                return
            payload = json.loads(response.body)
            table = parse(payload)
            version = digest(payload)
            self.table, self.version = table, version
            self.fetched = time.time()
            self.updated = (payload.get('meta') or {}).get('updated')
            folder = os.path.dirname(self.store)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            temporary = self.store + '.tmp'
            with open(temporary, 'wb') as handle:
                json.dump({'schemaVersion': 1, 'source': ORIGIN, 'sha256': version,
                           'fetchedAt': self.fetched, 'payload': payload}, handle)
                handle.flush()
                os.fsync(handle.fileno())
            replace(temporary, self.store)
        except (IOError, OSError, ValueError, TypeError):
            _logger.exception('expected refresh failed; keeping previous usable table')
