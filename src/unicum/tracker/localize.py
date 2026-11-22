# -*- coding: utf-8 -*-
"""New tracker/window text; existing controls retain the shared translations."""
from unicum.settings_window.localize import text

WORDS = {
    'Mini': u'Міні', 'Compact': u'Компакт', 'Trend': u'Тренд', 'Battles': u'Бої',
    'General': u'Загальні', 'WNX Tracker': u'WNX Tracker', 'Battle': u'Бій',
    'Garage': u'Ангар', 'Integrations': u'Інтеграції',
    'Apply': u'Застосувати', 'OK': u'OK', 'Cancel': u'Скасувати',
    'Saving settings...': u'Збереження налаштувань…',
    'Could not save settings. Try again.': u'Не вдалося зберегти налаштування. Спробуйте ще раз.',
    'Could not save some account settings. Try again.':
        u'Не вдалося зберегти деякі налаштування акаунта. Спробуйте ще раз.',
    'Settings': u'Налаштування', 'Display mode': u'Режим відображення',
    'Random battles in window': u'Випадкових боїв у вибірці',
    'Background opacity': u'Непрозорість фону',
    'Reset statistics...': u'Скинути статистику…', 'Reset position': u'Відновити розташування',
    'Reset statistics?': u'Скинути статистику?', 'Reset': u'Скинути', 'Restore': u'Відновити',
    'This action cannot be undone.': u'Цю дію неможливо скасувати.',
    'All local random-battle history for the current account will be deleted. Graphs and session WNX will start again.':
        u'Уся локальна історія випадкових боїв для поточного акаунта буде видалена. Графіки та сесійний WNX почнуть формуватися заново.',
    'Total WNX on Unicum.gg, replays and mod settings remain unchanged.':
        u'Загальний WNX на Unicum.gg, реплеї та налаштування мода залишаться без змін.',
    'Reset mod settings?': u'Скинути налаштування мода?',
    'Restore mod defaults? Tracker history and account link remain unchanged.':
        u'Відновити типові налаштування? Історія Tracker і зв’язок акаунта залишаться без змін.',
    'Play {remaining} more random battles': u'Зіграйте ще {remaining} випадкових боїв',
    'Play {remaining} random battles to build statistics': u'Зіграйте ще {remaining} випадкових боїв для формування статистики',
    'Incomplete battle results': u'Неповні результати боїв',
    'Expected WNX values are unavailable': u'Очікувані значення WNX недоступні',
    'Missing WNX expectations for some tanks': u'Для деяких танків бракує очікуваних значень WNX',
    'WNX temporarily unavailable': u'WNX тимчасово недоступний',
    'Average damage': u'Середня шкода', 'Average assist': u'Середній асист',
    'win': u'Перемога', 'loss': u'Поразка', 'draw': u'Нічия',
    'No data': u'Немає даних', 'Tank': u'Танк', 'Unknown tank': u'Невідомий танк', 'Battle': u'Бій',
    'Loading battle history...': u'Завантаження історії боїв…',
    'History could not be saved': u'Не вдалося зберегти історію',
    'History recovered from a damaged file': u'Історію відновлено з пошкодженого файлу',
    'Expected values': u'Очікувані значення', 'Unavailable': u'Недоступно',
    'Cached': u'Кешовано', 'Updated': u'Оновлено', 'Pending changes': u'Незбережені зміни',
}


def translate(value, language):
    return WORDS.get(value, text(value, language)) if language == 'uk' else value


RATING_MESSAGES = {
    'incomplete_results': 'Incomplete battle results',
    'expected_unavailable': 'Expected WNX values are unavailable',
    'missing_expected': 'Missing WNX expectations for some tanks',
    'wnx_unavailable': 'WNX temporarily unavailable',
}


def rating_message(reason, language):
    return translate(RATING_MESSAGES[reason], language) if reason else ''


def labels(language):
    return dict((key, translate(key, language)) for key in WORDS)
