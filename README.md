# Теорія ПДР: тести — Android

Офлайн-тренажёр теоретического экзамена ПДР (категории B1, B): 1762 вопроса, режимы «Навчання» и «Реальний іспит», прогресс только на телефоне. Веб-тренажёр, упакованный в Android-приложение через Capacitor 8.

**Как выложить в Google Play — пошагово в [PUBLISH.md](PUBLISH.md).**

## Структура

| Путь | Что это |
|---|---|
| `web/` | исходники тренажёра: `template.html` (общий с веб-версией), `data.json` (вопросы), `pdr.json` (текст ПДР), `packs/` (картинки WebP в JSON-пачках) |
| `src/` | вставки для мобильной версии: `why_mobile.js` (кнопка «Чому?» с готовыми пояснениями), `data_mobile.js` (сохранение/восстановление прогресса, «Про застосунок», кнопка «Назад») |
| `scripts/build_www.py` | собирает офлайн-бандл `www/`: перевод интерфейса на украинский, локальные шрифты, отступы под вырезы экрана, мост к нативным плагинам |
| `android/` | нативный проект Android (Capacitor), иконки, экран запуска, подпись |
| `resources/` | генераторы иконок (`make_icons.py`) и картинок для магазина (`make_store_graphics.py`), шрифты для них |
| `store/` | материалы для Google Play: тексты, иконка 512, баннер, скриншоты |
| `docs/privacy.html` | политика конфиденциальности (для GitHub Pages) |
| `.github/workflows/android.yml` | сборка APK/AAB в GitHub Actions |

## Сборка

Обычно — в GitHub Actions (см. PUBLISH.md). Локально нужны Node 22+, JDK 21, Android SDK (API 36) и Python 3:

```bash
npm ci
npm run sync                 # web/ + src/ → www/ → android/
cd android
./gradlew assembleDebug      # app/build/outputs/apk/debug/app-debug.apk
./gradlew bundleRelease      # нужен ключ: android/keystore.properties или переменные ANDROID_KEYSTORE_*
```

`android/keystore.properties` для локальной подписи (файл в .gitignore):

```
storeFile=/полный/путь/upload-key.jks
storePassword=...
keyAlias=upload
keyPassword=...
```

Проверить бандл в браузере без Android: `python3 -m http.server -d www 8000` → http://localhost:8000.

## Версия

Единственное место — `"version"` в `package.json`. Из неё берутся `versionName` (1.2.3) и `versionCode` (10203), а также строка «Версія» в приложении. Перед каждой загрузкой в Google Play увеличивайте версию.

## Пояснения «Чому?» (на будущее)

Кнопка появляется под ответом, если в `src/explain.json` есть запись для этого вопроса. Формат:

```json
{
  "15-12": {
    "law": ["15.9", "15.10"],
    "signs": ["3.34"],
    "marks": ["1.4"],
    "text": "Пояснення українською…"
  }
}
```

* ключ — id вопроса `раздел-номер`, как в `web/data.json` (`15-12`, `8.1-34`);
* `law` — пункты ПДР, их текст подставится дословно из `pdr.json`;
* `signs` / `marks` — знаки и разметка на картинке (карточки с названием и значением);
* `text` — само пояснение.

Пока файла нет, сборка кладёт пустой `{}` и кнопка скрыта.

## Иконки и графика

```bash
npm run icons                              # android/app/src/main/res/mipmap-* , splash, store/icon-512.png
python3 resources/make_store_graphics.py   # store/screenshots/*.png и баннер из store/screenshots/raw/
```
