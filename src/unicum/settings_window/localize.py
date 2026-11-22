# -*- coding: utf-8 -*-
"""Settings-only English/Ukrainian translation; protocol keys never change."""
import re

LANGUAGES = ('en', 'uk')
LANGUAGE_NAMES = (u'English', u'Українська')

UK = {
    'Settings language': u'Мова налаштувань',
    'Skirmish room average': u'Середній рейтинг загону',
    'Battle results average': u'Середній рейтинг у результатах', 'Team average': u'Середній рейтинг команди',
    'Garage': u'Ангар', 'Battle': u'Бій', 'General': u'Загальне',
    'Statistics': u'Статистика', 'Stats': u'Статистика', 'Screens': u'Екрани',
    'Loading Screen': u'Завантаження', 'Battle Panels': u'Бойові панелі',
    'Tab Scoreboard': u'Таблиця Tab', 'Vehicle Markers': u'Маркери техніки',
    'Enable unicum.gg': u'Увімкнути unicum.gg',
    'Rating': u'Рейтинг', 'Period': u'Період', 'Rating period': u'Період рейтингу',
    'Last 30 days': u'Останні 30 днів', 'Overall': u'Загальна', 'Off': u'Вимкнено',
    'Win rate': u'Відсоток перемог', 'Win rate to a tenth': u'Перемоги: один знак після коми',
    'Battles': u'Кількість боїв', 'Flags per player or clan': u'Прапорців гравця або клану',
    'Contacts list': u'Список контактів', 'Profile': u'Профіль', 'Skirmish room': u'Передбойова кімната',
    'Stronghold': u'Укріпрайон', 'Battle results': u'Результати бою', 'In battle': u'У бою',
    'Ratings and flags': u'Рейтинг і прапорці', 'Ratings only': u'Лише рейтинг',
    'Flags only': u'Лише прапорці', 'Nothing': u'Нічого',
    'Skirmish room: when': u'Передбойова кімната: коли', 'Stronghold: when': u'Укріпрайон: коли',
    'Battle results: when': u'Результати бою: коли', 'Battle results: figures': u'Результати бою: статистика',
    'Figures shown': u'Яку статистику показувати', 'Career': u'За весь акаунт',
    'On the tank': u'На цій техніці', 'Both': u'Обидва варіанти',
    'Always': u'Завжди', 'While Alt is held': u'Під час утримання Alt',
    'Tank menu button': u'Кнопка в меню техніки', 'Right-click a player': u'Контекстне меню гравця',
    'Right-click a tank': u'Контекстне меню техніки', 'Share my loadouts': u'Надсилати мої комплектації',
    'Hide my loadouts from my page': u'Приховати мої комплектації на сайті',
    'Hide my battles from my page': u'Приховати мої бої на сайті',
    'Share the replay file too': u'Також надсилати файл реплею',
    'unicum.gg account card': u'Картка акаунта unicum.gg',
    'Measure what this mod costs': u'Вимірювати навантаження мода',
    'Chat panel in the garage': u'Панель чату в ангарі',
    'Chat text size in the panel': u'Розмір тексту в панелі чату',
    'Chat text size in the battle chat': u'Розмір тексту в бойовому чаті',
    'Twitch chat in battle': u'Чат Twitch у бою', 'Small': u'Малий', 'Normal': u'Звичайний',
    'Large': u'Великий', 'Larger': u'Дуже великий', 'In the battle chat': u'У бойовому чаті',
    'In a window': u'В окремому вікні', 'In both': u'В обох місцях',
    'Connect': u'Підключити', 'Channel: not linked': u'Канал: не підключено',
    'Twitch channel (empty: linked account)': u'Канал Twitch (порожньо: з акаунта)',
    'unicum.gg is free and has no ads': u'unicum.gg безкоштовний і без реклами',
    'Questions, ideas and bug reports': u'Питання, ідеї та повідомлення про помилки',
    "The mod's source and its issues": u'Вихідний код і помилки мода',
    'Support': u'Підтримати', 'Support unicum.gg': u'Підтримати unicum.gg',
    'Every setting back to its default': u'Відновити типові налаштування', 'Reset': u'Скинути',
    'Cancel': u'Скасувати', 'Reset unicum.gg settings?': u'Скинути налаштування unicum.gg?',
    'Restore all unicum.gg options to their defaults and save them?': u'Відновити всі типові налаштування unicum.gg та зберегти їх?',
    'unicum.gg: the settings are back to their defaults.': u'unicum.gg: відновлено типові налаштування.',
    'What and when': u'Що і коли показувати', 'WNX in battle': u'WNX у бою', 'Tools': u'Інструменти',
    'Color player names by WNX': u'Кольорові нікнейми в бойових списках',
    'Color clan tags by WNX': u'Кольорові теги кланів у списках',
    'Color vehicle names by WNX': u'Кольорові назви техніки у списках',
    'Show battle ratings': u'Показувати рейтинг у бою',
    'Show WNX badges': u'Показувати значки WNX', 'Above tanks': u'Над технікою',
    'Players list': u'Панелі гравців', 'Tab screen': u'Екран Tab',
    'Loading screen': u'Екран завантаження', 'Minimap': u'Мінікарта',
    'Announce reloading': u'Повідомляти про перезаряджання', 'Never': u'Ніколи',
    'Every gun': u'Для всіх гармат', 'Autoloaders only': u'Лише для барабанів',
    'Minimap labels': u'Підписи на мінікарті', 'Vehicle': u'Техніка', 'Player': u'Гравець',
    'Vehicle and player': u'Техніка та гравець', 'Whose stats, per mode': u'Чию статистику показувати',
    'Random battles': u'Випадкові бої', 'Ranked battles': u'Рангові бої', 'Onslaught': u'Натиск',
    'Frontline': u'Лінія фронту', 'Training rooms': u'Тренувальні кімнати', 'Other modes': u'Інші режими',
    'Both teams': u'Обидві команди', 'Allies only': u'Лише союзників', 'Enemies only': u'Лише противників',
    'Nobody': u'Нічию', 'WNX row background': u'Фон рядків за WNX', 'WNX colour stripe': u'Кольорова смуга WNX',
    'Background opacity': u'Непрозорість фону', 'Show WNX': u'Показувати WNX',
    'Show win rate': u'Показувати відсоток перемог', 'Show battles': u'Показувати кількість боїв',
    'Statistics while holding Alt': u'Статистика під час утримання Alt',
    'Adaptive (WNX in narrow modes)': u'Адаптивно (WNX у вузьких панелях)',
    'WNX / WR / battles': u'WNX / перемоги / бої', 'Animate Alt transition': u'Анімація переходу Alt',
    'Transition duration (ms)': u'Тривалість переходу (мс)', 'Nickname colour': u'Колір нікнеймів',
    'Clan tag colour': u'Колір тегів кланів', 'Vehicle name colour': u'Колір назв техніки',
    'Light': u'Світлий', 'Game default': u'Штатний', 'Players without WNX': u'Гравці без WNX',
    'Neutral grey stripe': u'Нейтральна сіра смуга', 'Hide stripe': u'Приховати смугу',
    'Behaviour': u'Пояснення', 'Changes apply with Apply or OK. Cancel discards edits.': u'Apply / OK — зберегти. Cancel — відкинути зміни.',
    'Full mode keeps the vehicle name visible during Alt.': u'У повній панелі Alt зберігає назву техніки.',
    'The stripe follows the native label and avoids HP and icons.': u'Смуга біля підпису не перекриває HP та іконки.',
    'at rest': u'звичайно', 'with Alt': u'з Alt',
}

TOOLTIPS = {
    'Rating': u'WN7, WN8 та WNX — рейтинги unicum.gg. PR і WTR — загальні рейтинги акаунта від Wargaming.',
    'Rating period': u'Останні 30 днів або весь час. Якщо свіжих даних немає, використовуються загальні. PR і WTR завжди загальні.',
    'Win rate': u'Відсоток перемог поруч із рейтингом. Його період обирається незалежно від періоду рейтингу.',
    'Win rate to a tenth': u'Показувати 58,7% замість округлених 59%.',
    'Battles': u'Кількість боїв поруч із рейтингом. Великі значення скорочуються, наприклад 23k.',
    'Skirmish room': u'За вибором рейтинг, прапорці та середній рейтинг загону показуються лише під час утримання Alt. Порядок гравців не змінюється.',
    'Tank menu button': u'Кнопка unicum.gg у меню техніки: сторінки вибраного танка, ШІ-помічники та посилання на комплектацію.',
    'Right-click a player': u'Додає сторінку гравця на unicum.gg та ШІ-помічників до його контекстного меню.',
    'Right-click a tank': u'Додає посилання unicum.gg до контекстного меню техніки в каруселі, дереві досліджень, магазині та порівнянні.',
    'Share my loadouts': u'Надсилає на unicum.gg вашу комплектацію: обладнання, навички екіпажу, польову модернізацію та боєприпаси. Вимкнення припиняє надсилання й видаляє вже надіслані комплектації.',
    'Hide my loadouts from my page': u'Комплектації надалі надсилаються для статистики сайту, але не показуються на вашій публічній сторінці. Щоб припинити надсилання, вимкніть відповідний параметр.',
    'Hide my battles from my page': u'Приховує список ваших боїв на публічній сторінці. Бої все одно надсилаються й враховуються у статистиці сайту, навіть коли мод вимкнений.',
    'Share the replay file too': u'Додатково надсилає на unicum.gg файл .wotreplay, який уже записує клієнт. Він містить усе побачене клієнтом, зокрема бойовий чат. Вимкнення припиняє нові надсилання; уже надіслані файли залишаються.',
    'unicum.gg account card': u'Показує картку під завданнями в ангарі для підключення акаунта unicum.gg. Цей параметр повертає картку після закриття хрестиком.',
    'Measure what this mod costs': u'Вимірює час роботи цього мода й періодично пише підсумки в game.log. Вмикайте для діагностики навантаження.',
    'Chat text size in the panel': u'Розмір тексту в панелі Twitch в ангарі та окремому вікні в бою. Більший шрифт вміщує менше рядків.',
    'Chat text size in the battle chat': u'Розмір повідомлень Twitch у штатному бойовому чаті відносно масштабу інтерфейсу гри.',
    'Twitch': u'Підключіть гру до акаунта unicum.gg через браузер, щоб писати у свій Twitch-чат. Після підключення доступний одержувач TO TWITCH та команда !t.',
    'Twitch chat in battle': u'Показувати Twitch у бойовому чаті, окремому вікні або в обох місцях. Окреме вікно під час прицілювання призначене для читання.',
    'Support unicum.gg': u'Відкриває сторінку добровільної підтримки unicum.gg у браузері. Сайт і мод безкоштовні та без реклами.',
    'Discord': u'Відкриває Discord unicum.gg у браузері: питання, пропозиції та повідомлення про помилки.',
    'GitHub': u'Відкриває репозиторій мода з вихідним кодом і повідомленнями про помилки.',
    'Reset': u'Після підтвердження відновлює та зберігає типові налаштування мода. Підключення акаунта зберігається.',
    'Figures shown': u'Статистика всього акаунта, вибраної техніки або обидві. У варіанті «Обидва» Alt показує техніку; якщо даних немає, використовується статистика акаунта. У режимах без WN-рейтингу техніки показується відсоток перемог.',
    'Battle results: figures': u'У результатах бою можна показувати статистику всього акаунта, техніки з цього бою або обидві поруч. Використовується режим саме цього бою.',
    'Color player names by WNX': u'Керування оформленням нікнеймів у бойових списках. У перероблених панелях текст світлий, а WNX передає фон і смуга. Колір тексту Tab налаштовується окремо.',
    'Color clan tags by WNX': u'Оформлення тегів кланів у бойових списках. У Scaleform тег може бути частиною поля нікнейма.',
    'Color vehicle names by WNX': u'Оформлення назв техніки у бойових списках. Штатні іконки та інші елементи рядка зберігаються.',
    'Show battle ratings': u'Показувати рейтинг у бою',
    'Show WNX badges': u'Показує старі значки рейтингу біля бойових рядків. Перероблені панелі та Tab використовують текстову статистику.',
    'Whose stats, per mode': u'Окремо для кожного режиму: союзники, противники, обидві команди або ніхто. Впливає на підтримувані бойові екрани.',
    'Tab screen': u'Статистика в таблиці Tab. WNX, відсоток перемог, кількість боїв і кольори налаштовуються в підрозділі «Таблиця Tab». Прапорці тут не показуються.',
    'Announce reloading': u'Автоматично надсилає команді повідомлення про перезаряджання, як F8. Для барабанів можна повідомляти лише після їх спорожнення. Короткі перезаряджання до 5 секунд пропускаються.',
    'Minimap labels': u'Назва техніки, нікнейм гравця або обидва на мінікарті. Працює лише коли штатні підписи мінікарти ввімкнені.',
}


def text(value, language='en'):
    if language != 'uk' or not isinstance(value, basestring):
        return value
    value = value.decode('utf-8') if isinstance(value, str) else value
    if value in UK:
        return UK[value]
    tooltip = re.match(r'^\{HEADER\}(.*?)\{/HEADER\}\{BODY\}', value, re.S)
    if tooltip and tooltip.group(1) in TOOLTIPS:
        title = tooltip.group(1)
        return u'{HEADER}%s{/HEADER}{BODY}%s{/BODY}' % (text(title, language), TOOLTIPS[title])
    if value.startswith(u'Channel: '):
        return u'Канал: ' + value[9:].replace(u' (Connect to write in it)', u' (підключіть, щоб писати)')
    for source in sorted(UK, key=len, reverse=True):
        # Preview prefixes and decorative API headings contain markup; only
        # known captions are translated, never player/channel names or HTML.
        for prefix in (unicode(source), unicode(source).upper()):
            if value == prefix:
                return UK[source]
            if value.startswith(prefix + u'  '):
                return UK[source] + value[len(prefix):]
    return value


def template(page, values):
    language = values.get('settingsLanguage', 'en')
    if language == 'en':
        return page
    def visit(value):
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, dict):
            return dict((key, text(item, language) if key in ('text', 'label', 'tooltip')
                         else visit(item)) for key, item in value.items())
        return value
    return visit(page)


def native(page, values):
    language = values.get('settingsLanguage', 'en')
    if language == 'en':
        return page
    out = []
    for line in page.split(u'\n'):
        fields = line.split(u'\t')
        kind = fields[0]
        indices = {'tab': (1,), 'group': (2,), 'dropdown': (2,), 'checkbox': (2,),
                   'input': (2,), 'text': (1,), 'preview': (1,), 'button': (2, 3)}.get(kind, ())
        for index in indices:
            fields[index] = text(fields[index], language)
        if kind == 'dropdown':
            fields[5] = u'|'.join(text(option, language) for option in fields[5].split(u'|'))
        out.append(u'\t'.join(fields))
    return u'\n'.join(out)
