/* Today — the home screen (Phase 3, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).
   One screen that answers "what next?": the next Volumes step, debates with replies still owed, loose ends,
   study, today's plan, recent files, and the health of the system (Antigravity backup age, stale server, indexes).
   Every card loads on its own, so a slow source never holds up the others. Numbers come straight from the tab
   each card links to. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

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
  function get(url) { return fetch(url).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); }); }
  function link(text, fn, title) { return el("a", { href: "#", title: title || null, on: { click: function (e) { e.preventDefault(); fn(); } } }, [text]); }
  function go(tab, detail) { window.JarvisOpen(tab, detail || {}); }
  function card(id, title, tab) {
    var placeholder = (window.JarvisUI && window.JarvisUI.loading)
      ? window.JarvisUI.loading() : el("div", { class: "fx-muted", text: "Loading\u2026" });
    var body = el("div", { class: "td-body" }, [placeholder]);
    var head = el("div", { class: "td-head" }, [el("h3", { text: title }), tab ? link("open \u203a", function () { go(tab); }) : null]);
    return { el: el("section", { class: "td-card", id: "td-" + id }, [head, body]), body: body };
  }
  function fill(c, kids) { c.body.textContent = ""; kids.forEach(function (k) { if (k) c.body.appendChild(k); }); }
  function fail(c, e) { fill(c, [el("div", { class: "fx-muted", text: "Couldn't load: " + e.message })]); }
  function row(main, sub, onClick, badge) {
    return el("div", { class: "td-row" + (onClick ? " td-click" : ""), on: onClick ? { click: onClick } : null }, [
      el("div", { class: "td-main" }, [main, badge ? el("span", { class: "dx-badge", text: badge }) : null]),
      sub ? el("div", { class: "fx-muted", text: sub }) : null]);
  }
  function hoursAgo(ts) { return (Date.now() - Date.parse(ts)) / 3600000; }

  function load(root) {
    root.textContent = "";
    root.classList.add("td-root");
    var d = new Date();
    root.appendChild(el("div", { class: "td-top" }, [
      el("h2", { class: "td-date", text: d.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" }) }),
      el("span", { class: "fx-muted", text: "What to do next, from everything in the suite." })]));
    var grid = el("div", { class: "td-grid" });
    root.appendChild(grid);
    var C = {
      next: card("next", "Next in the books", "books"),
      debate: card("debate", "Debates", "threads"),
      loose: card("loose", "Loose ends", "loose"),
      plan: card("plan", "Today's plan", "cockpit"),
      study: card("study", "Study", "anki"),
      recent: card("recent", "Recent files", "files"),
      system: card("system", "System", null)
    };
    Object.keys(C).forEach(function (k) { grid.appendChild(C[k].el); });

    get("/api/books/next?n=3").then(function (d) {
      if (!d.items || !d.items.length) return fill(C.next, [el("div", { class: "fx-muted", text: "Nothing waiting in Volumes." })]);
      fill(C.next, d.items.map(function (x) {
        return row(x.action.charAt(0).toUpperCase() + x.action.slice(1) + ": " + x.title,
          x.volume + " \u00b7 " + x.sources + " source" + (x.sources === 1 ? "" : "s") + " \u00b7 " + Math.round(x.words / 1000) + "k words",
          function () { go("books", { chapter: x.chapter }); });
      }));
    }).catch(function (e) { fail(C.next, e); });

    get("/api/debate/threads").then(function (d) {
      var ts = d.threads || [];
      var owed = ts.filter(function (t) { return t.unsent_points; });
      var totalOwed = owed.reduce(function (n, t) { return n + t.unsent_points; }, 0);
      var recent = ts.filter(function (t) { return hoursAgo(t.last_ts) <= 72; }).slice(0, 4);
      var kids = [el("div", { class: "td-stat" }, [el("strong", { text: String(totalOwed) }), " drafted repl" + (totalOwed === 1 ? "y" : "ies") + " not seen posted, in " + owed.length + " debate" + (owed.length === 1 ? "" : "s")])];
      (recent.length ? recent : ts.slice(0, 3)).forEach(function (t) {
        kids.push(row(t.title, t.participants.slice(0, 2).map(function (p) { return p.name; }).join(", ") + " \u00b7 " + t.last_ts.slice(0, 16).replace("T", " "),
          function () { go("threads", { id: t.id }); }, t.unsent_points || null));
      });
      fill(C.debate, kids);
    }).catch(function (e) { fail(C.debate, e); });

    Promise.all([get("/api/loose/threads?limit=3"), get("/api/ledger/questions?missed=true&limit=3")]).then(function (r) {
      var th = r[0], q = r[1];
      var kids = [];
      (th.threads || []).forEach(function (t) {
        kids.push(row(t.label.join(" \u00b7 "), t.n_docs + " documents, " + t.n_integrated + " in a book" + (t.n_open_items ? ", " + t.n_open_items + " open items" : ""),
          function () { go("loose"); }));
      });
      kids.push(el("div", { class: "td-stat" }, [el("strong", { text: String(q.total) }), " question" + (q.total === 1 ? "" : "s") + " you asked that may never have been answered"]));
      (q.items || []).slice(0, 2).forEach(function (x) {
        kids.push(row("\u201c" + x.text.slice(0, 90) + (x.text.length > 90 ? "\u2026" : "") + "\u201d", x.date + " \u00b7 " + (x.surface === "AG" ? "Antigravity" : "Claude"),
          function () { go("ledger"); }));
      });
      fill(C.loose, kids);
    }).catch(function (e) { fail(C.loose, e); });

    get("/api/schedule").then(function (s) {
      var done = Object.keys(s.habits || {}).filter(function (k) { return s.habits[k]; }).length;
      var all = Object.keys(s.habits || {}).length;
      var kids = [];
      if (s.daily_breakthrough) kids.push(el("div", { class: "td-quote", text: s.daily_breakthrough }));
      kids.push(el("div", { class: "td-stat" }, [el("strong", { text: done + " / " + all }), " habits done today"]));
      var list = el("div", { class: "td-habits" });
      Object.keys(s.habits || {}).forEach(function (k) {
        list.appendChild(el("span", { class: "td-habit" + (s.habits[k] ? " on" : ""), text: (s.habits[k] ? "\u2713 " : "") + k.replace(/_/g, " ") }));
      });
      kids.push(list);
      fill(C.plan, kids);
    }).catch(function (e) { fail(C.plan, e); });

    get("/api/health").then(function (h) {
      var scrip = "C:\\Users\\Elation\\Scholar_Decade_Plan\\The_Ten_Year_Scriptorium.md";
      fill(C.study, [
        el("div", { class: "td-stat" }, [el("strong", { text: String(h.anki_due_today) }), " Anki card" + (h.anki_due_today === 1 ? "" : "s") + " due (of " + h.anki_total_cards + ")"]),
        row("Review now", null, function () { go("anki"); }),
        row("The Ten-Year Scriptorium", "your self-study plan", function () { go("files", { path: scrip }); })
      ]);
    }).catch(function (e) { fail(C.study, e); });

    get("/api/files/state").then(function (s) {
      var r = (s.recent || []).slice(0, 6);
      if (!r.length) return fill(C.recent, [el("div", { class: "fx-muted", text: "Files you open in Library \u203a Files show up here." })]);
      fill(C.recent, r.map(function (x) { return row(x.name, x.at, function () { go("files", { path: x.path }); }); }));
    }).catch(function (e) { fail(C.recent, e); });

    renderSystem(C.system);
  }

  function renderSystem(c) {
    Promise.all([get("/api/today/backup"), get("/api/build_info").catch(function () { return null; }),
                 get("/api/recall/status").catch(function () { return null; }), get("/api/files/links/status").catch(function () { return null; })])
      .then(function (r) {
        var b = r[0], info = r[1], rec = r[2], links = r[3];
        var kids = [];
        var running = b.run && b.run.state === "running";
        var bkRow = el("div", { class: "td-sys " + (b.state === "ok" ? "ok" : "warn") }, [
          el("div", { class: "td-main", text: (b.state === "ok" ? "\u2713 " : "\u26a0 ") + "Antigravity history: " + b.message }),
          el("div", { class: "fx-muted", text: b.state === "ok" ? b.sessions_in_backup + " conversations kept (" + b.sessions_live + " still live in Antigravity)"
            : "Antigravity deletes its oldest conversations past about 515. Back up before they go." }),
          el("button", { class: "j-btn" + (b.state === "ok" ? " ghost" : " primary"), disabled: running ? true : null, on: { click: function () {
            fetch("/api/today/backup/run", { method: "POST" }).then(function () { pollBackup(c); }); } } }, [running ? "Backing up\u2026" : "Back up now"])
        ]);
        kids.push(bkRow);
        if (b.run && b.run.state === "done" && b.run.code !== null) {
          kids.push(el("div", { class: "fx-muted", text: (b.run.code === 0 ? "Last run: " : "Last run failed: ") + (b.run.output || "").split("\n").filter(Boolean).slice(-2, -1).join("") }));
        }
        if (info) kids.push(el("div", { class: "td-sys " + (info.stale && info.stale.length ? "warn" : "ok"), text:
          (info.stale && info.stale.length ? "\u26a0 This server is running older code \u2014 restart it (" + info.stale.length + " file(s) changed)" : "\u2713 Server is running the latest code") }));
        if (rec && rec.exists) kids.push(el("div", { class: "td-sys ok", text: "\u2713 Recall index " + Math.round(rec.db_bytes / 1048576) + " MB, built " + (rec.built_at || "").slice(0, 10) }));
        if (links) kids.push(el("div", { class: "td-sys " + (links.state === "done" ? "ok" : "warn"), text:
          links.state === "done" ? "\u2713 Backlink index: " + (links.n_files || 0).toLocaleString() + " notes, built " + (links.built_at || "").slice(0, 10)
          : links.state === "running" ? "Backlink index building\u2026 " + links.done + " / " + links.total : "Backlink index not built yet (Files \u203a any note \u203a Backlinks)" }));
        fill(c, kids);
      }).catch(function (e) { fail(c, e); });
  }
  function pollBackup(c) {
    renderSystem(c);
    var t = setInterval(function () {
      get("/api/today/backup").then(function (b) {
        if (!b.run || b.run.state !== "running") { clearInterval(t); renderSystem(c); }
      });
    }, 3000);
  }

  window.JarvisModules.today = { load: load, onShow: load };
})();
