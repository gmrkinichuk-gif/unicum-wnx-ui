"""Receive only own confirmed results for the local tracker; never upload."""
import logging

_logger = logging.getLogger('unicum.tracker.results')


def install(session, tracker):
    try:
        from gui.battle_results.service import BattleResultsService
    except ImportError:
        _logger.warning('local tracker results service unavailable')
        return

    def wrap(original):
        def postResult(service, result, needToShowUI=True):
            try:
                tracker.record(result)
            except Exception:
                _logger.exception('could not process own local battle result')
            return original(service, result, needToShowUI)
        return postResult

    session.patch(BattleResultsService, 'postResult', wrap)
