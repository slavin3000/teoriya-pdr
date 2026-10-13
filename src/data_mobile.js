  // ---------- progress file: export / import / reset (data lives only on this phone) ----------
  const EXPORT_APP = "teoriya-pdr";
  function dataSectionHtml() {
    return `
      <section>
        <h2 class="sec">Дані</h2>
        <div class="panel data-panel">
          <p class="empty">Прогрес зберігається лише на цьому телефоні. Щоб перенести його на інший пристрій, збережіть файл і відкрийте його там.</p>
          <div class="row-actions">
            <button class="btn soft" id="exp">Зберегти прогрес у файл</button>
            <button class="btn soft" id="imp">Відновити з файлу</button>
            <button class="btn soft" id="wipe">Скинути прогрес</button>
          </div>
          <input type="file" id="imp-file" accept="application/json,.json" hidden>
          <p class="data-msg" id="data-msg" role="status"></p>
        </div>
      </section>
      <section>
        <h2 class="sec">Про застосунок</h2>
        <div class="panel about">
          <p><b>Теорія ПДР: тести</b> — неофіційний тренажер для підготовки до теоретичного іспиту на категорії B1, B. Застосунок не пов’язаний із Головним сервісним центром МВС.</p>
          <p>Питання — з переліку тестових питань до екзаменаційних білетів; правильні відповіді — за таблицею, затвердженою наказом ГСЦ МВС від 29.10.2025 № 225; цитати — з Правил дорожнього руху (редакція від 09.04.2026).</p>
          <p>Першоджерела: <a href="https://hsc.gov.ua/poslugi/avtoshkoli/pitannya-ta-ispit-z-pdr/">питання та іспит з ПДР на сайті ГСЦ МВС</a> · <a href="https://zakon.rada.gov.ua/laws/show/1306-2001-%D0%BF">Правила дорожнього руху на сайті Верховної Ради</a>.</p>
          <p>Застосунок працює без інтернету, не збирає й нікуди не передає ваших даних.</p>
          <p class="ver">Версія __VERSION__</p>
        </div>
      </section>`;
  }
  function setDataMsg(t) { const m = $("#data-msg"); if (m) m.textContent = t; }
  async function exportProgress() {
    const payload = JSON.stringify({ app: EXPORT_APP, v: 1, exportedAt: Date.now(), stats, session: readLocalSnap() });
    const name = "teoriya-pdr-progres-" + today() + ".json";
    const N = window.__native, FS = N && N.plug("Filesystem"), Share = N && N.plug("Share");
    if (FS && Share) {
      const r = await FS.writeFile({ path: name, data: payload, directory: "CACHE", encoding: "utf8" });
      await Share.share({ title: "Прогрес «Теорія ПДР: тести»", url: r.uri, dialogTitle: "Куди зберегти файл прогресу" });
      return "Файл готовий — оберіть, куди його зберегти або надіслати.";
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([payload], { type: "application/json" })); a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    return "Файл збережено.";
  }
  // merge, never overwrite: per question the most recent record wins, exams are united, daily counters keep the larger value
  function importProgress(obj) {
    if (!obj || obj.app !== EXPORT_APP || !obj.stats || typeof obj.stats.q !== "object") throw new Error("not ours");
    let n = 0;
    for (const [k, v] of Object.entries(obj.stats.q || {})) {
      if (!BY.has(k) || !v || typeof v !== "object") continue;
      if (!stats.q[k] || (v.t || 0) > (stats.q[k].t || 0)) { stats.q[k] = { n: +v.n || 0, w: +v.w || 0, f: +v.f || 0, lo: v.lo ? 1 : 0, t: +v.t || 0 }; n++; }
    }
    for (const [d, v] of Object.entries(obj.stats.d || {})) {
      const cur = stats.d[d]; if (!cur || (v.n || 0) > (cur.n || 0)) stats.d[d] = { n: +v.n || 0, ok: +v.ok || 0 };
    }
    for (const ex of (obj.stats.exams || [])) if (ex && ex.id && !stats.exams.some(x => x.id === ex.id)) stats.exams.push(ex);
    stats.exams.sort((a, b) => (b.startedAt || 0) - (a.startedAt || 0));
    saveLocal();
    if (!saved && validSnap(obj.session)) { lsSet(SS_KEY, JSON.stringify(obj.session)); saved = obj.session; }
    fcCache = null;
    return n;
  }
  function bindData() {
    const exp = $("#exp"), imp = $("#imp"), file = $("#imp-file"), wipe = $("#wipe");
    if (!exp) return;
    exp.onclick = async () => { exp.disabled = true; try { setDataMsg(await exportProgress()); } catch (e) { setDataMsg("Не вдалося зберегти файл."); } finally { exp.disabled = false; } };
    imp.onclick = () => file.click();
    file.onchange = async () => {
      const f = file.files && file.files[0]; if (!f) return;
      try { const n = importProgress(JSON.parse(await f.text())); renderProgress(); renderHome(); setDataMsg(`Прогрес відновлено з файлу: оновлено ${n} ${plural(n, "питання", "питання", "питань")}.`); }
      catch (e) { setDataMsg("Це не файл прогресу цього застосунку."); }
      file.value = "";
    };
    wipe.onclick = () => {
      if (!wipe.dataset.armed) {
        wipe.dataset.armed = "1"; wipe.textContent = "Точно скинути весь прогрес?"; wipe.classList.add("danger");
        setTimeout(() => { if (wipe.isConnected) { delete wipe.dataset.armed; wipe.textContent = "Скинути прогрес"; wipe.classList.remove("danger"); } }, 4000);
        return;
      }
      stats.q = {}; stats.d = {}; stats.exams = []; saveLocal(); saveSession(null); fcCache = null;
      renderProgress(); renderHome(); setDataMsg("Прогрес скинуто.");
    };
  }

  // ---------- Android: back button and leaving the app ----------
  (function nativeHooks() {
    const App = window.__native && window.__native.plug("App"); if (!App) return;
    App.addListener("backButton", () => {
      hideTip();
      if (session && !session.done) { if (!session.paused) return pauseSession(); session = null; return renderHome(); }
      if (!view.querySelector(".modes")) { session = null; return renderHome(); }
      App.exitApp();
    });
    App.addListener("pause", () => pauseSession());
  })();
