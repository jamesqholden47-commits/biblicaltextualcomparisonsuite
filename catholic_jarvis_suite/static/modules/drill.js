/* Drill — real objections as flashcards (Phase 4, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).
   Front: something an opponent actually wrote in one of your debates (no name shown). Think of your answer.
   Back: what you actually replied in that debate (if you did), and a link to the exact message.
   Grade it Again / Hard / Good / Easy (keys 1-4, Space to show the answer); SM-2 brings it back when due. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};
  var S = { topic: "", q: null, i: 0, shown: false, packs: [] };

  window.addEventListener("jarvis:open-drill", function (ev) {
    var d = (ev && ev.detail) || {};
    S.topic = d.topic || "";
    if (S.ui) { S.ui.sel.value = S.topic; next(); }
  });

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "text") e.textContent = v;
      else if (k === "on") Object.keys(v).forEach(function (ev) { e.addEventListener(ev, v[ev]); });
      else e.setAttribute(k, v === true ? "" : v);
    });
    (kids || []).forEach(function (c) { if (c !== null && c !== undefined) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function get(u, body) {
    var o = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
    return fetch(u, o).then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.detail || r.status); return j; }); });
  }

  function load(root) {
    root.textContent = "";
    root.classList.add("dr-root");
    var sel = el("select", { class: "fx-select", on: { change: function () { S.topic = sel.value; next(); } } }, [el("option", { value: "", text: "All topics" })]);
    var stats = el("span", { class: "fx-muted" });
    var stage = el("div", { class: "dr-stage" }, [(window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading objections from your debates…") : el("div", { class: "j-empty", text: "Loading objections from your debates…" })]);
    root.appendChild(el("div", { class: "dr-top" }, [el("h2", { class: "dx-h", text: "Objection drill" }), sel, stats]));
    root.appendChild(el("div", { class: "fx-muted", style: "margin-bottom:12px", text:
      "Real objections from your debates. Answer it in your head (or out loud), then show what you actually said. Space shows the answer; 1–4 grades it." }));
    root.appendChild(stage);
    S.ui = { sel: sel, stats: stats, stage: stage };
    get("/api/packs").then(function (d) {
      d.packs.filter(function (p) { return p.n_cards; }).forEach(function (p) { sel.appendChild(el("option", { value: p.id, text: p.title + " (" + p.n_cards + ")" })); });
      sel.value = S.topic;
      next();
    });
    document.addEventListener("keydown", onKey);
  }

  function onKey(e) {
    var pane = document.getElementById("tab-drill");
    if (!pane || !pane.classList.contains("active") || !S.q || ["INPUT", "TEXTAREA", "SELECT"].indexOf(document.activeElement.tagName) >= 0) return;
    if (e.code === "Space" && !S.shown) { e.preventDefault(); show(); }
    else if (S.shown && ["1", "2", "3", "4"].indexOf(e.key) >= 0) { e.preventDefault(); grade(+e.key); }
  }

  function next() {
    get("/api/drill/queue?limit=30" + (S.topic ? "&topic=" + encodeURIComponent(S.topic) : "")).then(function (q) {
      S.q = q; S.i = 0; S.shown = false;
      S.ui.stats.textContent = q.due + " due · " + q.new_left_today + " new left today · " + q.total + " cards on this topic";
      render();
    }).catch(function (e) { S.ui.stage.textContent = e.message; });
  }

  function cur() { return S.q && S.q.queue[S.i]; }

  function render() {
    var st = S.ui.stage, c = cur();
    st.textContent = "";
    if (!c) {
      st.appendChild(el("div", { class: "j-empty", text: S.q && S.q.total ? "Done for today on this topic. Come back tomorrow, or pick another topic." : "No objections on this topic yet." }));
      return;
    }
    var badge = c.schedule ? "review · seen " + c.schedule.reps + "×" : "new";
    st.appendChild(el("div", { class: "dr-card" }, [
      el("div", { class: "dr-meta" }, [el("span", { class: "dx-state", text: badge }), el("span", { class: "fx-muted", text: "  " + c.thread_title + " · " + c.date + "  ·  " + (S.i + 1) + " of " + S.q.queue.length })]),
      el("div", { class: "dr-label", text: "An opponent wrote:" }),
      el("div", { class: "dr-front", text: c.front }),
      S.shown ? backEl(c) : el("button", { class: "j-btn primary dr-show", on: { click: show } }, ["Show what you said (Space)"])
    ]));
  }

  function backEl(c) {
    var kids = [el("div", { class: "dr-label", text: c.answer ? "You replied:" : "You never answered this in the logs." })];
    if (c.answer) kids.push(el("div", { class: "dr-back", text: c.answer }));
    else kids.push(el("div", { class: "fx-muted", text: "Use it as practice: how would you answer now? The topic's pack has your cards, earlier posts and dossiers." }));
    kids.push(el("div", { class: "dx-pactions" }, [
      el("button", { class: "j-btn ghost", on: { click: function () { window.JarvisOpen("threads", { id: c.thread, msg: c.msg }); } } }, ["Show in the debate"]),
      el("button", { class: "j-btn ghost", on: { click: function () { window.JarvisOpen("packs", {}); } } }, ["Open the packs"])
    ]));
    kids.push(el("div", { class: "dr-grades" }, [[1, "Again"], [2, "Hard"], [3, "Good"], [4, "Easy"]].map(function (g) {
      return el("button", { class: "j-btn" + (g[0] === 3 ? " primary" : ""), on: { click: function () { grade(g[0]); } } }, [g[0] + " · " + g[1]]);
    })));
    return el("div", { class: "dr-answer" }, kids);
  }

  function show() { S.shown = true; render(); }

  function grade(g) {
    var c = cur();
    if (!c) return;
    get("/api/drill/grade", { id: c.id, grade: g }).then(function (s) {
      if (window.showToast) window.showToast("Next review " + s.due, "info");
      S.i += 1; S.shown = false;
      if (S.i >= S.q.queue.length) next(); else render();
    });
  }

  window.JarvisModules.drill = { load: load };
})();
