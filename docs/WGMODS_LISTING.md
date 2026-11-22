# WGMods listing draft — Unicum WNX UI

**Draft only; do not submit until the items in [WGMODS_REVIEW.md](WGMODS_REVIEW.md) are cleared.** Adapt the version and client build to the exact submitted ZIP. Do not reuse the declined v0.9.18 listing/download unchanged.

## English — short description

Unicum WNX UI adds historical WNX ratings to World of Tanks EU battle screens and a locally stored personal battle-session Tracker. Independent, free and open-source mod (GNU AGPLv3).

## English — full description

**Compatibility:** World of Tanks EU 2.4.1.1 (release v0.9.20 only). Check compatibility again before publishing another version.

**Features:** WNX rating overlays on the loading screen, battle team panels, Tab scoreboard and vehicle markers; Alt display options; a personal Tracker with Mini, Compact, Trend and Battles modes and 10/20/30-battle views; English and Ukrainian settings.

**Installation:** Close the game. Remove older Unicum or Unicum WNX UI packages from active mod folders. Extract the matching installation ZIP into the World of Tanks folder. The installer includes the separately licensed OpenWG Gameface 1.2.2 dependency. Do not install two versions simultaneously.

**Network and privacy:** When active, the mod automatically sends HTTPS GET requests to Unicum.gg for WNX ratings, including numeric account identifiers of players shown in a battle and vehicle identifiers. It downloads public rating colour scales from Unicum.gg and public expected-value tables from Tomato.gg. Providers can see network metadata such as your IP address. The mod keeps your own Tracker history locally; it does not upload chat, replays, battle files, loadouts, passwords or Wargaming authentication tokens. There is no separate in-game opt-in for third-party requests in this release; simply disabling the visible overlay does not turn every request off. To stop requests, uninstall the mod before playing. See the [privacy disclosure](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/blob/main/PRIVACY.md).

**Licensing and attribution:** GNU AGPLv3 for the derivative code; matching source is available with the GitHub release. Third-party components retain their own licenses. See [release license information](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/blob/main/RELEASE_LICENSE.md), [NOTICE](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/blob/main/NOTICE) and [third-party credits](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/blob/main/THIRD_PARTY_NOTICES.md).

**Official status:** Unofficial independent community modification, not affiliated with or endorsed by Wargaming. © Wargaming.net. All rights reserved. Official game: https://worldoftanks.eu/ . Official support: https://eu.wargaming.net/support/ .

**Download and source:** https://github.com/gmrkinichuk-gif/unicum-wnx-ui/releases

## Русский — краткое описание

Unicum WNX UI отображает исторический рейтинг WNX в боевом интерфейсе World of Tanks EU и локальную статистику личной игровой сессии в ангаре. Независимая бесплатная модификация с открытым кодом (GNU AGPLv3).

## Русский — полное описание

**Совместимость:** World of Tanks EU 2.4.1.1 (только релиз v0.9.20). Для следующей версии игры требуется отдельная проверка.

**Возможности:** рейтинг WNX на экране загрузки, в командных панелях, таблице Tab и маркерах техники; настройки отображения при нажатии Alt; личный Tracker с режимами Mini, Compact, Trend и Battles и интервалами 10/20/30 боёв. Настройки на английском и украинском языках.

**Установка:** Закройте игру. Удалите из активных папок старые пакеты Unicum и Unicum WNX UI. Распакуйте ZIP-архив для соответствующей версии клиента в папку World of Tanks. В архив входит компонент OpenWG Gameface 1.2.2 со своей лицензией. Не устанавливайте две версии одновременно.

**Сеть и конфиденциальность:** Во время работы мод автоматически отправляет HTTPS GET-запросы сервису Unicum.gg для получения рейтингов WNX. В параметрах запросов могут передаваться числовые идентификаторы аккаунтов участников боя, а также идентификаторы техники. Общедоступные шкалы цветов загружаются с Unicum.gg, ожидаемые значения — с Tomato.gg. Сторонние сервисы видят сетевые данные, включая IP-адрес. История личных боёв Tracker хранится локально. Мод не загружает на сервер чаты, реплеи, файлы результатов боёв, комплектацию техники, пароли или токены Wargaming. Отдельного согласия на сторонние запросы внутри игры в этой версии нет. Отключение отображения рейтинга не гарантирует отключения сетевых запросов; для полного прекращения запросов удалите мод до запуска игры. Подробности: [политика данных](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/blob/main/PRIVACY.md).

**Лицензия:** GNU AGPLv3 для производного кода; исходники соответствующей версии доступны вместе с релизом. У сторонних компонентов собственные лицензии. См. [информацию о лицензии](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/blob/main/RELEASE_LICENSE.md), [NOTICE](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/blob/main/NOTICE) и [сведения о компонентах](https://github.com/gmrkinichuk-gif/unicum-wnx-ui/blob/main/THIRD_PARTY_NOTICES.md).

**Статус:** Неофициальная независимая модификация, не связанная с Wargaming и не одобренная ею. © Wargaming.net. All rights reserved. Официальный сайт игры: https://worldoftanks.eu/ . Поддержка: https://eu.wargaming.net/support/ .

**Загрузка и исходный код:** https://github.com/gmrkinichuk-gif/unicum-wnx-ui/releases

## Before publishing on WGMods

- Confirm current portal requirements in the signed-in submission UI, including accepted archive extensions, size limits, language requirements and any disclosure fields. The public terms URL cannot currently be fully inspected through a text-only browser.
- Resolve the right to redistribute the patched client-owned `battleVehicleMarkersApp.swf`, or change packaging so a legally compliant transformation is performed from the user's own installed client without shipping the original artwork/code.
- Seek moderation guidance on sending other players' numeric identifiers to Unicum.gg by default. This draft accurately **discloses** the transfers; it does not replace opt-in or establish a lawful basis for them.
- Confirm external providers' rights and applicable WG API data onward-use restrictions, even though this mod does not itself directly call the WG Public API.
- Provide real, privacy-safe screenshots and live-client evidence. Verify the matching source and third-party licenses are included in the binary archives.
- Make and test a **new** versioned package, update release descriptions, and upload that actual ZIP to WGMods. Repository documentation changes alone do not update existing v0.9.20 assets or a declined WGMods submission.
