  // ---------- "Чому?": ready-made explanations shipped with the app (www/explain.json) ----------
  // explain.json: { "<question id>": { "law": ["15.9"], "signs": ["3.36"], "marks": ["1.1"], "text": "…" } }
  // The button stays hidden until that file exists and has an entry for the question.
  let pdrPromise = null;
  function loadPdr() {
    if (!pdrPromise) {
      pdrPromise = fetch("pdr.json").then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(P => {
        const chunks = P.chunks.map(([k, sec, label, text]) => ({ k, sec, label, text }));
        return { edition: P.edition, chunks, byKey: new Map(chunks.map(c => [c.k, c])), alias: P.alias || {}, names: P.names || {}, notes: P.notes || {} };
      });
      pdrPromise.catch(() => { pdrPromise = null; });
    }
    return pdrPromise;
  }
  function pdrGet(I, key) { return I.byKey.get(key) || I.byKey.get(I.alias[key]) || null; }
  let explPromise = null;
  function loadExpl() {
    if (!explPromise) explPromise = fetch("explain.json").then(r => r.ok ? r.json() : null).catch(() => null);
    return explPromise;
  }
  // one card per sign / marking seen in the picture: number, name, meaning from ПДР and the general provisions that name it
  function objCards(I, objs) {
    if (!objs.length) return "";
    const signs = objs.filter(o => o.ns === "33"), marks = objs.filter(o => o.ns === "34");
    const card = (o, i) => {
      const long = o.def.length > 600;
      const notes = o.notes.slice(0, 3), more = o.notes.length - notes.length;
      return `<figure class="sign-item"><figcaption><span class="sign-num">${o.ns === "33" ? "знак" : "розмітка"} ${esc(o.num)}</span>${o.name ? ` <span class="sign-name">«${esc(o.name)}»</span>` : ""}</figcaption>
        <blockquote lang="uk" class="${long ? "clamp" : ""}" id="obj-${i}">${esc(o.def)}</blockquote>${long ? `<button class="law-more" data-t="obj-${i}">Показати повністю</button>` : ""}
        ${notes.length ? `<ul class="sign-notes" lang="uk">${notes.map(n => `<li>${esc(n)}</li>`).join("")}</ul>${more > 0 ? `<button class="law-more sign-more" data-more="${i}">Ще ${more} ${plural(more, "положення", "положення", "положень")}</button>` : ""}` : ""}
      </figure>`;
    };
    let i = 0;
    return (signs.length ? `<div class="law-src">Знаки на зображенні</div>${signs.map(o => card(o, i++)).join("")}` : "")
      + (marks.length ? `<div class="law-src">Розмітка на зображенні</div>${marks.map(o => card(o, i++)).join("")}` : "");
  }
  function objInfo(I, ns, num) {
    const key = ns + ":" + num, c = pdrGet(I, key); if (!c) return null;
    return { ns, num, key, chunkKey: c.k, name: I.names[key] || "", def: c.text, notes: I.notes[key] || [] };
  }
  function lawHtml(I, cs) {
    if (!cs.length) return "";
    return `<div class="law-src">Правила дорожнього руху України · ${esc(I.edition.split(" (")[0].toLowerCase())}</div>` + cs.map((c, i) => {
      const long = c.text.length > 700;
      return `<figure class="law-item"><figcaption>${esc(c.label)}</figcaption><blockquote lang="uk" class="${long ? "clamp" : ""}" id="law-${i}">${esc(c.text)}</blockquote>${long ? `<button class="law-more" data-i="${i}">Показати повністю</button>` : ""}</figure>`;
    }).join("");
  }
  function renderWhy(box, I, cs, text, done, objs) {
    objs = objs || [];
    const shown = new Set(objs.map(o => o.chunkKey));
    const law = cs.filter(c => !shown.has(c.k));
    box.innerHTML = `${I && objs.length ? `<div class="law">${objCards(I, objs)}</div>` : ""}${I && law.length ? `<div class="law">${lawHtml(I, law)}</div>` : ""}<div class="why-text">${esc(text)}</div>${done ? note() : ""}`;
    box.querySelectorAll(".law-more").forEach(b => b.onclick = () => {
      if (b.dataset.more != null) { const o = objs[+b.dataset.more]; const ul = b.previousElementSibling; ul.innerHTML = o.notes.map(n => `<li>${esc(n)}</li>`).join(""); b.remove(); return; }
      const bq = box.querySelector("#" + (b.dataset.t || "law-" + b.dataset.i)); if (bq) bq.classList.remove("clamp"); b.remove();
    });
  }
  async function setupWhy(q, chosen) {
    const btn = $("#why"); if (!btn) return;
    const E = await loadExpl(); const e = E && E[q.id];
    if (!e || !btn.isConnected) return;
    btn.hidden = false;
    btn.onclick = async () => {
      const box = $("#explain"); box.hidden = false; btn.hidden = true;
      let I = null; try { I = await loadPdr(); } catch (err) { I = null; }
      const cs = I ? (e.law || []).map(k => pdrGet(I, String(k))).filter(Boolean) : [];
      const objs = I ? [...(e.signs || []).map(n => objInfo(I, "33", String(n))), ...(e.marks || []).map(n => objInfo(I, "34", String(n)))].filter(Boolean) : [];
      if (box.isConnected) renderWhy(box, I, cs, e.text || "", true, objs);
    };
  }
  const note = () => `<span class="note">Цитати — дослівно з офіційного тексту ПДР. Пояснення підготовлене штучним інтелектом і може містити неточності.</span>`;
