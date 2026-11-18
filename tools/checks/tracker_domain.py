"""Numerical, durable-history and result-consumer integration checks."""
import copy
import json
import os

from checks.common import check, REPO


def run(workdir):
    from unicum.tracker import formula, options
    from unicum.tracker.extract import extract
    from unicum.tracker.state import snapshot, geometry
    from unicum.tracker.store import History
    from checks.battles import RESULTS
    from unicum.battles.reporter import Reporter
    from unicum.runtime.session import Session

    with open(os.path.join(REPO, 'tools', 'fixtures', 'wnx_parity.json')) as handle:
        fixtures = json.load(handle)
    for case in fixtures['cases']:
        value = formula.compute(case['tanks'], dict((int(k), v) for k, v in case['expected'].items()))
        check('upstream WNX parity ' + case['name'],
              value is None if case['value'] is None else abs(value - case['value']) < fixtures['tolerance'])

    class Constants(object):
        REGULAR, RANDOM_NP2, EPIC_RANDOM, TRAINING, COMP7 = 1, 100, 24, 2, 43

    row = extract(RESULTS, 'eu', 531280131, Constants)
    check('real fixture: own account, 64-bit arena id and tank intCD',
          row['tankId'] == 6209 and row['arenaUniqueId'] == '19011738950705142'
          and row['damageDealt'] == 4374 and row['winnerResult'] == 'win')
    check('other account never aliases own results', extract(RESULTS, 'eu', 123, Constants) is None)
    other = copy.deepcopy(RESULTS)
    other['common']['bonusType'] = 2
    check('training excluded even with random-shaped results', extract(other, 'eu', 531280131, Constants) is None)
    for metric in ('damageDealt', 'kills', 'damageAssistedRadio'):
        other = copy.deepcopy(RESULTS)
        other['vehicles']['13089208'][0].pop(metric)
        check('missing metric never becomes zero: ' + metric, extract(other, 'eu', 531280131, Constants) is None)

    root = os.path.join(workdir, 'tracker-history')
    history = History('eu', 531280131, root)
    check('first battle durable; repeated result ignored', history.add(row) and not history.add(row))
    check('journal survives restart', History('eu', 531280131, root).rows == [row])
    with open(history.path, 'ab') as handle:
        handle.write('{"torn":')
    history = History('eu', 531280131, root)
    check('partial tail recovered without losing last full battle', history.rows == [row] and history.error == 'history_recovered')
    for i in range(1, 241):
        history.add(dict(row, arenaUniqueId=str(90000000000000000 + i), startedAt=row['startedAt'] + i))
    check('200 retained battles and compaction survive restart', len(history.rows) == 200 and
          History('eu', 531280131, root).rows == history.rows and not history.add(row))
    alternate = History('eu', 2, root)
    alternate.add(dict(row, accountId='2'))
    history.reset(row['startedAt'] + 300)
    history = History('eu', 531280131, root)
    check('reset blocks old callbacks across restarts', not history.rows and not history.add(row))
    check('reset never affects other accounts or regions', len(History('eu', 2, root).rows) == 1
          and not History('na', 531280131, root).rows)
    check('post-reset battle accepted', history.add(dict(row, startedAt=row['startedAt'] + 301, arenaUniqueId='99999999999999999')))
    original_append = history._append
    def disk_full(item):
        with open(history.path, 'ab') as handle:
            handle.write('{"partial":')
        raise IOError('simulated disk full')
    history._append = disk_full
    failed = dict(row, arenaUniqueId='99999999999999998', startedAt=row['startedAt'] + 302)
    try:
        history.add(failed)
    except IOError:
        pass
    check('failed append retains raw metrics for bounded retry', history.pending == [failed] and history.error == 'storage_error')
    history._append, history._retry_at = original_append, 0
    check('retry repairs partial append and durably saves the battle once',
          history.retry() and not history.pending and History('eu', 531280131, root).rows == history.rows)

    expected = {6209: {'damage': 1200, 'frags': 0.8, 'spots': 1.1, 'assist': 500}}
    rows = [dict(row, arenaUniqueId=str(i+1), startedAt=row['startedAt']+i, damageDealt=i*87) for i in range(60)]
    for count in (10, 20, 30):
        check('%d waits for a complete window' % count, snapshot(rows[:count-1], count, expected)['reason'] == 'more_battles')
        missing = snapshot(rows[:count], count, {})
        check('%d missing expectations distinct from progress' % count,
              missing['reason'] == 'missing_expected' and missing['progress'] == count and missing['wnx'] is None)
        check('%d has no premature delta' % count, snapshot(rows[:2*count-1], count, expected)['delta'] is None)
        state = snapshot(rows[:2*count], count, expected)
        check('%d disjoint delta and rolling graph' % count,
              state['delta'] == formula.aggregate(rows[count:2*count], expected)-formula.aggregate(rows[:count], expected)
              and len(state['points']) == count and len(state['bars']) == count)
        check('%d first rolling point needs N real battles' % count,
              len(snapshot(rows[:count], count, expected)['points']) == 1)
        g = geometry(count)
        check('%d bars have separate hit zones and positive gaps' % count,
              all(w < hit and x >= left and x+w <= left+hit for x,w,left,hit in g)
              and all(g[i][2]+g[i][3] <= g[i+1][2]+1e-9 for i in range(count-1)))
    check('bad tracker options use safe defaults; legacy keys survive parent validator',
          options.validate({'count': 50, 'mode': 'hidden'}) == options.DEFAULTS)

    class Sink(object):
        def __init__(self):
            self.seen = []
        def record(self, result):
            self.seen.append(result)
    class Settings(object):
        def sends_battles(self):
            return False
    sink, session = Sink(), Session(0)
    reporter = Reporter(session, Settings(), None, tracker=sink)
    reporter._record(RESULTS)
    check('local consumer runs when server sending is disabled', sink.seen == [RESULTS] and not reporter._queue)
    def broken(result):
        raise RuntimeError('deliberate tracker failure')
    sink.record = broken
    original = lambda service, result, needToShowUI: 'original-result'
    check('tracker exception cannot break original postResult', reporter._wrap_post(original)(None, RESULTS) == 'original-result')
    session.close()
