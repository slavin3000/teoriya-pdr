#!/usr/bin/env python3
"""Builds the offline Android web bundle (www/) from the web trainer template.

Inputs : web/template.html, web/data.json, web/pdr.json, web/packs/*.json, src/*.js
Output : www/index.html, www/fonts/*, www/packs/*, www/pdr.json  www/explain.json (src/explain.json or {})
"""
import json, os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'web')
WWW = os.path.join(ROOT, 'www')
VERSION = json.load(open(os.path.join(ROOT, 'package.json')))['version']

src = open(os.path.join(APP, 'template.html'), encoding='utf-8').read()

def rep(old, new, count=None):
    """exact replacement that must match (count = expected number of matches, None = at least one)"""
    global src
    n = src.count(old)
    if n == 0 or (count is not None and n != count):
        sys.exit(f'pattern matched {n} times (expected {count or ">=1"}): {old[:120]!r}')
    src = src.replace(old, new)

# ---------------------------------------------------------------- structure
# drop Google Fonts (offline app ships its own font files)
src = re.sub(r'<link rel="preconnect"[^>]*>\n', '', src)
src = re.sub(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>\n', '', src)
rep('<title>ПДР-тренажёр</title>\n', '')

# storage: mirror to native Preferences, wait for restore, re-read paused session
rep('  function saveLocal() { try { localStorage.setItem(LS_KEY, JSON.stringify(stats)); } catch (e) {} }',
    '  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} if (window.__native) window.__native.mirror(k, v); }\n'
    '  function saveLocal() { lsSet(LS_KEY, JSON.stringify(stats)); }', 1)
rep('    try { localStorage.setItem(SS_KEY, JSON.stringify(snap)); } catch (e) {}', '    lsSet(SS_KEY, JSON.stringify(snap));', 1)
rep('  async function initStore() {\n    let db = null;',
    '  async function initStore() {\n    try { if (window.__native) await window.__native.ready; } catch (e) {}\n    let db = null;', 1)
rep("      try { const s = JSON.parse(localStorage.getItem(LS_KEY) || \"null\"); if (s) { Object.assign(stats.q, s.q || {}); Object.assign(stats.d, s.d || {}); stats.exams = s.exams || []; } } catch (e) {}\n      setSaveState(); rerenderHome(); return;",
    "      try { const s = JSON.parse(localStorage.getItem(LS_KEY) || \"null\"); if (s) { Object.assign(stats.q, s.q || {}); Object.assign(stats.d, s.d || {}); stats.exams = s.exams || []; } } catch (e) {}\n      if (!session) { const loc = readLocalSnap(); saved = validSnap(loc) ? loc : null; }\n      setSaveState(); rerenderHome(); return;", 1)
rep('el.className = "save-state" + (store.mode === "db" && !store.err ? " on" : store.mode === "local" || store.err ? " warn" : "");',
    'el.className = "save-state" + (store.err ? " warn" : store.mode !== "loading" ? " on" : "");', 1)

# «Чому?»: replace the live-Claude block with ready-made explanations
a = src.index('  // ---------- ПДР text (loaded on first "Почему?") ----------')
b = src.index('  const note = () =>'); b = src.index('\n', b) + 1
src = src[:a] + open(os.path.join(ROOT, 'src', 'why_mobile.js'), encoding='utf-8').read() \
    + open(os.path.join(ROOT, 'src', 'data_mobile.js'), encoding='utf-8').read().replace('__VERSION__', VERSION) + src[b:]

# home: data + about sections
rep("""      </section>`;
    armStart($("#go-exam"), startExam);""", """      </section>${dataSectionHtml()}`;
    bindData();
    armStart($("#go-exam"), startExam);""", 1)

# safe areas (Capacitor SystemBars injects --safe-area-inset-*), sticky bar under the status bar
rep('.qbar { display: flex; align-items: center; gap: 12px; justify-content: space-between; position: sticky; top: env(safe-area-inset-top, 0px);',
    '.qbar { display: flex; align-items: center; gap: 12px; justify-content: space-between; position: sticky; top: var(--sat);', 1)
rep('.app { max-width: 760px; margin: 0 auto; padding-inline: 16px; padding-block: 20px 48px;',
    '.app { max-width: 760px; margin: 0 auto; padding-inline: 16px; padding-block: calc(16px + var(--sat)) calc(40px + var(--sab));', 1)

# ---------------------------------------------------------------- Ukrainian UI
UK = [
    # header / footer
    ('<h1>ПДР-тренажёр</h1>', '<h1>Теорія ПДР: тести</h1>'),
    ('Разделы 1–39 и дополнительные для категорий B1, B · 1762 вопроса', 'Розділи 1–39 і додаткові для категорій B1, B · 1762 питання'),
    ('Подключаю статистику…', 'Завантажую прогрес…'),
    ('"Статистика не сохраняется"', '"Не вдалося зберегти прогрес"'),
    ('"Статистика сохраняется"', '"Прогрес зберігається"'),
    ('"Статистика только в этом браузере"', '"Прогрес зберігається на цьому телефоні"'),
    ('Прогресс подготовки', 'Прогрес підготовки'),
    ('<p class="foot">Ответы — по таблице правильных ответов, утверждённой приказом ГСЦ МВС от 29.10.2025 № 225.</p>',
     '<p class="foot">Неофіційний навчальний застосунок, не пов’язаний із ГСЦ МВС. Відповіді — за таблицею правильних відповідей (наказ ГСЦ МВС від 29.10.2025 № 225).</p>'),
    ('"ru-RU"', '"uk-UA"'),
    # progress + forecast
    ('<span>освоено из ${total', '<span>опановано з ${total'),
    ('<span>осталось</span>', '<span>залишилось</span>'),
    ('Освоено ${mastered} из ${total}, ждут пересдачи ${waiting}', 'Опановано ${mastered} з ${total}, чекають на повторення ${waiting}'),
    ('ждут пересдачи', 'чекають на повторення'),
    ('все вопросы освоены', 'усі питання опановано'),
    ('прогноз экзаменов появится после первого экзамена', 'прогноз з’явиться після першого іспиту'),
    ('считаю прогноз', 'рахую прогноз'),
    ('Оценка по вашей точности: с первого раза ', 'Оцінка за вашою точністю: з першого разу '),
    ('%, на пересдаче ', '%, під час повторення '),
    ('%. Считается для режима «Обучение»: ошибки и новые вопросы идут в билет первыми.', '%. Рахується для режиму «Навчання»: помилки й нові питання потрапляють у білет першими.'),
    ('экзаменов до 100%', 'іспитів до 100%'),
    # resume card
    ('aria-label="Незаконченный подход"', 'aria-label="Незавершений підхід"'),
    ('"Обучение на паузе"', '"Навчання на паузі"'),
    ('"Реальный экзамен на паузе"', '"Реальний іспит на паузі"'),
    ('"Работа над ошибками на паузе"', '"Робота над помилками на паузі"'),
    ('Сохранено ${fmtDate(sv.savedAt)}. Таймер стоит, пока экзамен на паузе.', 'Збережено ${fmtDate(sv.savedAt)}. Поки іспит на паузі, таймер стоїть.'),
    ('Точно сбросить?', 'Точно скинути?'),
    ('Продолжить', 'Продовжити'),
    ('"Сбросить"', '"Скинути"'),
    ('>Сбросить<', '>Скинути<'),
    # mode cards
    ('Билет на 20 вопросов', 'Білет на 20 питань'),
    ('Сначала ваши ошибки, потом новые вопросы, освоенные — только когда раздел пройден. Идёт в статистику и прогресс.',
     'Спершу ваші помилки, потім нові питання, опановані — лише коли розділ пройдено. Враховується у статистиці й прогресі.'),
    ('Начать новый подход →', 'Почати новий підхід →'),
    ('Начать новый →', 'Почати новий →'),
    ('Учиться →', 'Вчитися →'),
    ('Как в сервисном центре', 'Як у сервісному центрі'),
    ('20 случайных вопросов, 20 минут, можно пропускать. Третья ошибка — экзамен прекращается. На статистику не влияет.',
     '20 випадкових питань, 20 хвилин, можна пропускати. Третя помилка — іспит припиняється. На статистику не впливає.'),
    ('Проверить себя →', 'Перевірити себе →'),
    ('Ошибок пока нет', 'Помилок поки немає'),
    ('Вопрос уходит из очереди после двух верных ответов подряд (по одному за подход).',
     'Питання виходить із черги після двох правильних відповідей поспіль (по одній за підхід).'),
    ('Сюда попадут вопросы, на которые вы ответите неправильно в режиме «Обучение».',
     'Сюди потраплять питання, на які ви відповісте неправильно в режимі «Навчання».'),
    ('Повторить ошибки →', 'Повторити помилки →'),
    ('" в очереди"', '" у черзі"'),
    ('"вопрос", "вопроса", "вопросов"', '"питання", "питання", "питань"'),
    # stats
    ('ответов всего', 'відповідей усього'),
    ('верных ответов', 'правильних відповідей'),
    ('вопросов встречалось', 'питань траплялося'),
    ('реальных экзаменов сдано', 'реальних іспитів складено'),
    ('Слабые разделы', 'Слабкі розділи'),
    ('Появятся, когда в разделе наберётся хотя бы 5 ответов.', 'З’являться, коли в розділі набереться щонайменше 5 відповідей.'),
    ('Последние экзамены', 'Останні іспити'),
    ('"реальный" : "обучение"', '"реальний" : "навчання"'),
    ('"сдан" : x.timeUp ? "время вышло" : x.stopped ? "прекращён" : "не сдан"', '"складено" : x.timeUp ? "час вийшов" : x.stopped ? "припинено" : "не складено"'),
    ('Загружаю…', 'Завантажую…'),
    ('Ещё не было ни одного экзамена.', 'Ще не було жодного іспиту.'),
    ('Незаконченный подход будет сброшен — нажмите ещё раз', 'Незавершений підхід буде скинуто — натисніть ще раз'),
    # pause screen
    ('"Обучение остановлено"', '"Навчання зупинено"'),
    ('"Экзамен остановлен"', '"Іспит зупинено"'),
    ('"Подход остановлен"', '"Підхід зупинено"'),
    ('. Таймер стоит.', '. Таймер стоїть.'),
    ('Прогресс сохранён — можно закрыть страницу и продолжить позже, в том числе с другого устройства.', 'Прогрес збережено — можна закрити застосунок і продовжити пізніше.'),
    ('На главную', 'На головну'),
    # question screen
    ('Реальный экзамен · вопрос ${vi + 1}', 'Реальний іспит · питання ${vi + 1}'),
    (' · ответов ${answeredN}', ' · відповідей ${answeredN}'),
    ('ошибок: ${errs}', 'помилок: ${errs}'),
    ('`Обучение · ', '`Навчання · '),
    ('" · просмотр"', '" · перегляд"'),
    ('`Ошибки · ', '`Помилки · '),
    ('aria-label="Вопросы экзамена"', 'aria-label="Питання іспиту"'),
    ('", ошибка"', '", помилка"'),
    ('", текущий"', '", поточне"'),
    ('", без ответа"', '", без відповіді"'),
    ('", ещё впереди"', '", ще попереду"'),
    ('", верно"', '", правильно"'),
    ('"Точно завершить?"', '"Точно завершити?"'),
    ('Завершить', 'Завершити'),
    ('Просмотр вопроса ${vi + 1}. Ответ уже засчитан, изменить его нельзя.', 'Перегляд питання ${vi + 1}. Відповідь уже зараховано, змінити її не можна.'),
    ('Варианты ответа', 'Варіанти відповіді'),
    ('"ваш ответ ✓" : "правильный"', '"ваша відповідь ✓" : "правильна"'),
    ('mark = "ваш ответ"', 'mark = "ваша відповідь"'),
    ('Правильный ответ — ', 'Правильна відповідь — '),
    ('>Пропустить<', '>Пропустити<'),
    ('Почему?', 'Чому?'),
    ('Предыдущий вопрос', 'Попереднє питання'),
    ('Следующий вопрос', 'Наступне питання'),
    ('К вопросу ${S.idx + 1} →', 'До питання ${S.idx + 1} →'),
    ('Enter — дальше', 'Enter — далі'),
    ('← → — листать', '← → — гортати'),
    ('Клавиши 1–', 'Клавіші 1–'),
    ('" — ответ', '" — відповідь'),
    ('Enter — к текущему вопросу', 'Enter — до поточного питання'),
    (' · ← — предыдущий', ' · ← — попереднє'),
    ('Иллюстрация к вопросу', 'Ілюстрація до питання'),
    ('Картинка не загрузилась — проверьте соединение.', 'Не вдалося завантажити зображення.'),
    ('"Следующий без ответа →"', '"Наступне без відповіді →"'),
    ('"Далее →"', '"Далі →"'),
    ('"Итог →"', '"Підсумок →"'),
    ('<span class="t-ok">верно</span>', '<span class="t-ok">правильно</span>'),
    ('<span class="t-bad">ошибка</span>', '<span class="t-bad">помилка</span>'),
    ('<span class="t-cur">текущий</span>', '<span class="t-cur">поточне</span>'),
    ('<p>Ещё впереди</p>', '<p>Ще попереду</p>'),
    # results
    ('Реальный экзамен · на статистику не влияет', 'Реальний іспит · на статистику не впливає'),
    ('"Экзамен сдан"', '"Іспит складено"'),
    ('"Экзамен прекращён"', '"Іспит припинено"'),
    ('"Экзамен не сдан"', '"Іспит не складено"'),
    ('`Третья ошибка после ${ex.answered} ${plural(ex.answered, "ответа", "ответов", "ответов")} из ${S.ids.length} — в сервисном центре на этом тест прекращается.`',
     '`Третя помилка після ${ex.answered} ${plural(ex.answered, "відповіді", "відповідей", "відповідей")} з ${S.ids.length} — у сервісному центрі на цьому тест припиняється.`'),
    ('(допустимо не больше ${EXAM_MAX_ERR})', '(допустимо не більше ${EXAM_MAX_ERR})'),
    (', из них без ответа: ', ', з них без відповіді: '),
    ('Время ${fmtTime(ex.durationSec)}', 'Час ${fmtTime(ex.durationSec)}'),
    ('" · время вышло"', '" · час вийшов"'),
    ('"Ещё реальный экзамен" : "Новый билет"', '"Ще реальний іспит" : "Новий білет"'),
    ('Разбор ошибок', 'Розбір помилок'),
    ('"Ваш ответ — "', '"Ваша відповідь — "'),
    ('"Без ответа"', '"Без відповіді"'),
    ('Правильный — ', 'Правильна — '),
    ('right + " из " + done.length + " верно"', 'right + " з " + done.length + " правильно"'),
    ('"Подход завершён"', '"Підхід завершено"'),
    ('В очереди ошибок осталось ${left} ${plural(left, "питання", "питання", "питань")}. Верно отвеченные вернутся ещё раз, чтобы закрепить — после второго верного ответа подряд они уходят из очереди.',
     'У черзі помилок залишилося ${left} ${plural(left, "питання", "питання", "питань")}. Питання з правильною відповіддю повернуться ще раз для закріплення — після другої правильної відповіді поспіль вони виходять із черги.'),
    ('>Ещё подход<', '>Ще підхід<'),
    ('id="exam">Экзамен<', 'id="exam">Іспит<'),
    # generic leftovers (must run last)
    ('"Обучение на паузе"', '"Навчання на паузі"'),
    ('Работа над ошибками', 'Робота над помилками'),
    ('Реальный экзамен', 'Реальний іспит'),
    ('>Обучение<', '>Навчання<'),
    ('"ошибка", "ошибки", "ошибок"', '"помилка", "помилки", "помилок"'),
    ('Вопрос ${', 'Питання ${'),
    ('<b>Вопрос ${', '<b>Питання ${'),
    (' · верно ${answered - errs} из ${answered}', ' · правильно ${answered - errs} з ${answered}'),
    ('осталось ${fmtTime', 'залишилось ${fmtTime'),
    (' из ${', ' з ${'),
]
for ru, uk in UK:
    if ru in src:
        src = src.replace(ru, uk)
    elif uk not in src and ru not in ('"Обучение на паузе"', '<b>Вопрос ${'):
        sys.exit(f'translation key not found: {ru[:100]!r}')

# safety net: any Russian-only letters left in user-facing text?
code = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
code = '\n'.join(l for l in code.split('\n') if not l.strip().startswith('//'))
left = sorted(set(re.findall(r'[^\n]{0,40}[ыэъёЫЭЪЁ][^\n]{0,40}', code)))
if left:
    sys.exit('Russian text left:\n' + '\n'.join(left[:40]))

# ---------------------------------------------------------------- fonts (cyrillic + latin subsets, woff2)
fonts_dir = os.path.join(WWW, 'fonts'); shutil.rmtree(fonts_dir, ignore_errors=True); os.makedirs(fonts_dir)
css = []
for pkg, weights in (('onest', (400, 500, 600, 700)), ('unbounded', (500, 700)), ('jetbrains-mono', (500, 600))):
    base = os.path.join(ROOT, 'node_modules', '@fontsource', pkg)
    shutil.copy(os.path.join(base, 'LICENSE'), os.path.join(fonts_dir, f'LICENSE-{pkg}.txt'))   # SIL OFL 1.1
    for w in weights:
        txt = open(os.path.join(base, f'{w}.css'), encoding='utf-8').read()
        for block in re.findall(r'@font-face \{.*?\}', txt, re.S):
            m = re.search(r'url\(\./files/([^)]+?-(cyrillic|latin)-\d+-normal\.woff2)\)', block)
            if not m: continue
            shutil.copy(os.path.join(base, 'files', m.group(1)), fonts_dir)
            block = re.sub(r'src: [^;]+;', f"src: url(fonts/{m.group(1)}) format('woff2');", block)
            css.append(block)

HEAD = """<!doctype html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<title>Теорія ПДР: тести</title>
<style>
%s
:root { --sat: var(--safe-area-inset-top, env(safe-area-inset-top, 0px)); --sab: var(--safe-area-inset-bottom, env(safe-area-inset-bottom, 0px)); }
html { -webkit-text-size-adjust: 100%%; }
body { margin: 0; -webkit-tap-highlight-color: transparent; }
body::before { content: ""; position: fixed; inset: 0 0 auto 0; height: var(--sat); background: var(--bg); z-index: 30; }
img { max-width: 100%%; }
[hidden] { display: none !important; }
@media (hover: none) { .kbd { display: none; } }
.data-panel { display: grid; gap: 12px; }
.data-panel .empty { margin: 0; }
.data-msg { margin: 0; font-size: 14px; color: var(--ink-2); min-height: 1.2em; }
.about p { margin: 0 0 8px; font-size: 14px; color: var(--ink-2); }
.about p b { color: var(--ink); }
.about a { color: var(--accent); overflow-wrap: anywhere; }
.about .ver { margin: 0; font-size: 12.5px; color: var(--ink-3); }
/* phone, during a ticket: hide the header and squeeze the progress strip so the question fits on screen */
@media (max-width: 540px) {
  .app:has(.qbar) .top, .app:has(.qbar) .lane { display: none; }
  .app:has(.qbar) .progress { gap: 5px; }
  .app:has(.qbar) .pg-nums { gap: 2px 14px; }
  .app:has(.qbar) .pg-nums b { font-size: 14px; }
  .app:has(.qbar) .pg-nums .pg-main b { font-size: 16px; }
  .app:has(.qbar) .pg-nums span { font-size: 12px; }
  .app:has(.qbar) .pg-fc { display: none !important; }
  .app:has(.qbar) .pg-bar { height: 6px; }
}
</style>
<script src="capacitor.js"></script>
<script>
// Capacitor bridge helpers: native plugins when running inside the Android app, nothing in a plain browser
window.__native = (() => {
  const cap = window.Capacitor;
  const native = !!(cap && typeof cap.isNativePlatform === "function" && cap.isNativePlatform());
  const cache = {};
  const plug = name => {
    if (!native) return null;
    if (!(name in cache)) { let p = null; try { p = (typeof cap.registerPlugin === "function" ? cap.registerPlugin(name) : null) || (cap.Plugins && cap.Plugins[name]) || null; } catch (e) {} cache[name] = p; }
    return cache[name];
  };
  const Prefs = plug("Preferences");
  const KEYS = ["pdr-trainer-stats-v1", "pdr-trainer-session-v1"];
  // localStorage is the working copy; Preferences is a durable backup restored on start if the WebView storage was cleared
  const ready = (async () => { if (!Prefs) return; for (const k of KEYS) { try { if (!localStorage.getItem(k)) { const r = await Prefs.get({ key: k }); if (r && r.value) localStorage.setItem(k, r.value); } } catch (e) {} } })();
  return { native, plug, ready, mirror(k, v) { if (Prefs) Prefs.set({ key: k, value: v }).catch(() => {}); } };
})();
</script>
</head>
<body>
""" % '\n'.join(css)

data = open(os.path.join(APP, 'data.json'), encoding='utf-8').read()
page = HEAD + src.replace('__DATA__', data) + '\n</body>\n</html>\n'

# ---------------------------------------------------------------- assets
os.makedirs(WWW, exist_ok=True)
open(os.path.join(WWW, 'index.html'), 'w', encoding='utf-8').write(page)
shutil.copy(os.path.join(APP, 'pdr.json'), WWW)
shutil.copy(os.path.join(ROOT, 'node_modules', '@capacitor', 'core', 'dist', 'capacitor.js'), WWW)  # registerPlugin() for native plugins (no bundler)
packs = os.path.join(WWW, 'packs'); shutil.rmtree(packs, ignore_errors=True); shutil.copytree(os.path.join(APP, 'packs'), packs)
expl = os.path.join(ROOT, 'src', 'explain.json')
if os.path.exists(expl): shutil.copy(expl, WWW)
else: open(os.path.join(WWW, 'explain.json'), 'w', encoding='utf-8').write('{}')  # empty: «Чому?» stays hidden, no 404
print('www built:', round(os.path.getsize(os.path.join(WWW, 'index.html')) / 1e6, 2), 'MB index,', len(os.listdir(packs)), 'packs,', len(os.listdir(fonts_dir)), 'font files, version', VERSION)
