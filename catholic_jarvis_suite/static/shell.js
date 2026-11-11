/* shell.js — workspace shell for the CatholicJarvis suite (Phase 0 of SUITE_OVERHAUL_PLAN_2026-10-07,
   Claude GUI, Opus 5.5). Loaded after index.html's own scripts.

   What it does, without touching any tab's internals:
   - groups the 21 existing tabs into workspaces (left sidebar) and sub-tabs (top bar); the old strip is hidden
     but kept in the DOM because index.html code looks buttons up by id;
   - deep links: #<workspace>/<tab>[?path=...] survives reload and back/forward;
   - Ctrl+K command palette over tabs, Volumes chapters, Loose Ends documents and Recall;
   - a side-panel reader ("peek"): JarvisOpen("reader", {path}) now opens beside the current tab, with a button
     to expand into the full Reader tab;
   - a banner when the server is running older code than is on disk (/api/build_info).
   A tab id that does not exist on the page (a later phase's tab) is simply not shown. */
(function () {
  "use strict";

  var WORKSPACES = [
    { id: "today",   label: "Today",          ico: "☀", tabs: [["today", "Today"], ["cockpit", "Horarium"]] },
    { id: "library", label: "Library",        ico: "\u{1F4DA}", tabs: [["files", "Files"], ["organizer", "Organizer"], ["navigator", "Genealogy & Treemap"], ["verbum", "Verbum Suite"], ["plenary_suite", "Plenary Logos Suite"], ["manuscripts", "Manuscripts"], ["reader", "Reader"], ["recall", "Search"],
                                                                  ["studio", "PDFs"], ["dossiers", "Corpus"]] },
    { id: "books",   label: "Books",          ico: "\u{1F4D6}", tabs: [["books", "Volumes"], ["loose", "Loose Ends"], ["episodes", "Episodes"],
                                                                  ["podcast", "Podcast"]] },
    { id: "debate",  label: "Debate",         ico: "⚔", tabs: [["threads", "Threads"], ["desk", "Compose"], ["packs", "Packs"],
                                                                  ["drill", "Drill"]] },
    { id: "patristics", label: "Patristic Arsenal", ico: "📜", tabs: [["manuscript_diff", "Manuscript Diff"], ["patristic_map", "Patristic Map"], ["defeater_tree", "Debate Cockpit"], ["deuterocanon", "Deuterocanon"], ["contributors", "Contributors"], ["omitted_verses", "Omitted Verses"], ["translation_lab", "Translation Lab"]] },
    { id: "study",   label: "Study",          ico: "\u{1F393}", tabs: [["anki", "Anki"], ["languages", "Languages"], ["career", "Career"]] },
    { id: "church",  label: "Church & Life",  ico: "✝", tabs: [["pope_leo", "Pope Leo"], ["vatican_culture", "Vatican"]] },
    { id: "system",  label: "System",         ico: "⚙", sep: true,
                                              tabs: [["sessions", "Sessions"], ["ledger", "Questions"], ["vaults", "Vault Dedup"],
                                                     ["audit", "Audit"], ["health", "Health"]] }
  ];
  // Retired tabs (Phase 5): their cards live in Packs, every field included; data files untouched.
  // Old links and older code that still open them land on the new home.
  var RETIRED = { debates: "packs", pope: "packs" };
  var TAB_TO_WS = {};
  WORKSPACES.forEach(function (w) { w.tabs.forEach(function (t) { TAB_TO_WS[t[0]] = w.id; }); });

  var lastTabOf = {};          // workspace -> last sub-tab used there
  var current = { ws: null, tab: null };
  var origSwitch = window.switchTab;

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === "text") e.textContent = attrs[k];
      else if (k === "on") Object.keys(attrs.on).forEach(function (ev) { e.addEventListener(ev, attrs.on[ev]); });
      else e.setAttribute(k, attrs[k]);
    });
    (kids || []).forEach(function (c) { if (c) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function paneExists(id) { return !!document.getElementById("tab-" + id); }
  function wsTabs(ws) { return ws.tabs.filter(function (t) { return paneExists(t[0]); }); }
  function wsById(id) { for (var i = 0; i < WORKSPACES.length; i++) if (WORKSPACES[i].id === id) return WORKSPACES[i]; return null; }

  // ── layout ────────────────────────────────────────────────────────────────────
  function buildFrame() {
    document.body.classList.add("j-shell");
    var header = document.querySelector("header");
    var content = document.querySelector(".content-area");
    var frame = el("div", { id: "j-frame" });
    var side = el("aside", { id: "j-sidebar" });
    var main = el("div", { id: "j-main" });
    var banner = el("div", { id: "j-banner" });
    var sub = el("div", { id: "j-subtabs" });
    var peek = buildPeek();
    header.parentNode.insertBefore(frame, header.nextSibling);
    frame.appendChild(side); frame.appendChild(main); frame.appendChild(peek);
    main.appendChild(banner); main.appendChild(sub); main.appendChild(content);
  }

  function renderSidebar() {
    var side = document.getElementById("j-sidebar");
    side.textContent = "";
    WORKSPACES.forEach(function (w) {
      var tabs = wsTabs(w);
      if (!tabs.length) return;
      if (w.sep) side.appendChild(el("div", { class: "j-side-sep" }));
      side.appendChild(el("button", {
        class: "j-ws" + (current.ws === w.id ? " active" : ""), id: "j-ws-" + w.id, title: w.label,
        on: { click: function () { goWorkspace(w.id); } }
      }, [el("span", { class: "j-ico", text: w.ico }), el("span", { class: "j-label", text: w.label }),
          el("span", { class: "j-count", id: "j-wscount-" + w.id })]));
    });
    side.appendChild(el("div", { class: "j-side-foot" }, [
      el("span", { class: "j-kbd", text: "Ctrl" }), " ", el("span", { class: "j-kbd", text: "K" }), " search everything", el("br"),
      el("span", { class: "j-kbd", text: "?" }), " shortcuts"
    ]));
    updateCounts();
  }

  function renderSubtabs() {
    var bar = document.getElementById("j-subtabs");
    bar.textContent = "";
    var w = wsById(current.ws);
    if (!w) return;
    bar.appendChild(el("span", { class: "j-ws-title", text: w.label }));
    wsTabs(w).forEach(function (t) {
      var b = el("button", { class: "j-sub" + (current.tab === t[0] ? " active" : ""), "data-tab": t[0],
                             on: { click: function () { go(t[0]); } } }, [t[1]]);
      if (t[0] === "anki") b.appendChild(el("span", { class: "j-count", id: "j-anki-due" }));
      bar.appendChild(b);
    });
    bar.appendChild(el("span", { class: "j-spacer" }));
    bar.appendChild(el("button", { class: "j-search-btn", title: "Search everything (Ctrl+K)", on: { click: openPalette } },
      ["\u{1F50D} Search", el("span", { class: "j-kbd", text: "Ctrl K" })]));
    updateCounts();
  }

  function updateCounts() {
    var due = document.getElementById("due-badge");
    var n = due ? due.textContent.trim() : "";
    var a = document.getElementById("j-anki-due");
    if (a) a.textContent = n && n !== "0" ? n : "";
    var s = document.getElementById("j-wscount-study");
    if (s) s.textContent = n && n !== "0" ? n : "";
  }

  // ── navigation ────────────────────────────────────────────────────────────────
  function go(tabId, opts) {
    opts = opts || {};
    if (RETIRED[tabId]) tabId = RETIRED[tabId];
    if (!paneExists(tabId)) return false;
    var pane = document.getElementById("tab-" + tabId);
    var wasLoaded = pane && pane.dataset.loaded;
    origSwitch(tabId);
    // a deep link can switch to a module tab before its script has arrived; then nothing loads it. Wait for it.
    if (pane && !pane.dataset.loaded && pane.parentNode && pane.parentNode.id === "module-panes" &&
        !(window.JarvisModules && window.JarvisModules[tabId])) waitForModule(tabId);
    // a module may refresh itself each time it is shown again (Today does); first showing is its load()
    var M = window.JarvisModules && window.JarvisModules[tabId];
    if (wasLoaded && M && typeof M.onShow === "function") {
      try { M.onShow(pane.querySelector(".module-root") || pane); } catch (e) { console.warn(tabId + ".onShow failed", e); }
    }
    var ws = TAB_TO_WS[tabId] || current.ws || "today";
    var changedWs = ws !== current.ws;
    current.ws = ws; current.tab = tabId; lastTabOf[ws] = tabId;
    if (changedWs) renderSidebar();
    else document.querySelectorAll(".j-ws").forEach(function (b) { b.classList.toggle("active", b.id === "j-ws-" + ws); });
    renderSubtabs();
    if (!opts.noHash) {
      var h = "#" + ws + "/" + tabId + (opts.query ? "?" + opts.query : "");
      if (location.hash !== h) history.pushState(null, "", h);
    }
    try { localStorage.setItem("jarvis.lastHash", "#" + ws + "/" + tabId); } catch (e) { /* storage may be blocked */ }
    return true;
  }
  function waitForModule(tabId) {
    var tries = 0;
    var t = setInterval(function () {
      tries++;
      var pane = document.getElementById("tab-" + tabId);
      var ready = window.JarvisModules && window.JarvisModules[tabId];
      if (ready || tries > 200) {
        clearInterval(t);
        if (ready && pane && !pane.dataset.loaded && current.tab === tabId) origSwitch(tabId);   // loads it now
      }
    }, 50);
  }
  function goWorkspace(wsId) {
    var w = wsById(wsId);
    if (!w) return;
    var tabs = wsTabs(w);
    var t = lastTabOf[wsId] && paneExists(lastTabOf[wsId]) ? lastTabOf[wsId] : (tabs[0] && tabs[0][0]);
    if (t) go(t);
  }

  function parseHash(h) {
    var m = /^#([a-z_]+)\/([a-z0-9_-]+)(?:\?(.*))?$/.exec(h || "");
    if (!m) return null;
    var q = {};
    (m[3] || "").split("&").forEach(function (kv) { if (!kv) return; var i = kv.indexOf("="); q[decodeURIComponent(kv.slice(0, i))] = decodeURIComponent(kv.slice(i + 1)); });
    return { ws: m[1], tab: m[2], q: q };
  }
  function applyHash(h) {
    var r = parseHash(h);
    if (!r || !paneExists(r.tab)) return false;
    go(r.tab, { noHash: true });
    if (r.q.path && (r.tab === "reader" || r.tab === "files")) fireOpen(r.tab, { path: r.q.path, part: r.q.part ? +r.q.part : 0 });
    else if (r.q.q && r.tab === "recall") fireOpen("recall", { q: r.q.q });
    return true;
  }
  function fireOpen(tabId, detail) {
    // the module's listener exists only once its script has run; until then the event would be lost
    var tries = 0;
    var t = setInterval(function () {
      tries++;
      var isModule = !!(window.JarvisModules && window.JarvisModules[tabId]);
      var builtIn = !document.querySelector("#module-panes > #tab-" + tabId);
      if ((isModule || builtIn) && tries >= 7 || tries > 200) {     // >= 350 ms as before, and the module is there
        clearInterval(t);
        window.dispatchEvent(new CustomEvent("jarvis:open-" + tabId, { detail: detail || {} }));
      }
    }, 50);
  }

  // switchTab is called by older code (and by modules); keep the shell in step with it
  window.switchTab = function (tabId) {
    if (!go(tabId)) origSwitch(tabId);
  };
  // JarvisOpen: "reader" opens in the side panel; everything else switches tab as before
  window.JarvisOpen = function (tabId, detail) {
    detail = detail || {};
    if (tabId === "reader" && detail.path && !detail.full) { openPeek(detail.path, detail.part || 0); return; }
    var q = (tabId === "reader" || tabId === "files") && detail.path ? "path=" + encodeURIComponent(detail.path) : "";
    go(tabId, { query: q });
    fireOpen(tabId, detail);
  };
  window.JarvisGo = go;

  // ── side-panel reader ─────────────────────────────────────────────────────────
  var peekState = { path: null, part: 0, parts: 1 };
  function buildPeek() {
    var body = el("div", { id: "j-peek-body", class: "fx-md" });
    return el("aside", { id: "j-peek", "aria-label": "Side reader" }, [
      el("div", { id: "j-peek-head" }, [
        el("div", { id: "j-peek-title", text: "" }),
        el("button", { class: "j-btn ghost", title: "Open in the full Reader", on: { click: function () {
          var p = peekState.path, part = peekState.part; closePeek();
          window.JarvisOpen("reader", { path: p, part: part, full: true }); } } }, ["⤢ Expand"]),
        el("button", { class: "j-btn ghost", title: "Close (Esc)", on: { click: closePeek } }, ["✕"])
      ]),
      el("div", { id: "j-peek-meta" }),
      body,
      el("div", { id: "j-peek-parts" })
    ]);
  }
  function openPeek(path, part) {
    peekState.path = path; peekState.part = part || 0;
    document.getElementById("j-peek").classList.add("open");
    document.getElementById("j-peek-title").textContent = path.split(/[\\/]/).pop();
    document.getElementById("j-peek-meta").textContent = path;
    var body = document.getElementById("j-peek-body");
    body.textContent = "Loading…";
    var get = function (url) { return fetch(url).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, status: r.status, j: j }; }); }); };
    var qs = "?path=" + encodeURIComponent(path) + "&part=" + (part || 0);
    // the Reader serves its own document set; anything else inside the Files roots comes from the Files API
    get("/api/reader/doc" + qs)
      .then(function (res) { return res.status === 403 ? get("/api/files/view" + qs).then(function (f) {
        if (f.ok) { f.j.title = f.j.title || f.j.name; f.j.filename = f.j.name; f.j.html = f.j.html || ""; } return f; }) : res; })
      .then(function (res) {
        if (!res.ok) { body.textContent = "Could not open: " + (res.j.detail || "error"); return; }
        var d = res.j;
        document.getElementById("j-peek-title").textContent = d.title || d.filename;
        document.getElementById("j-peek-meta").textContent = path + "  ·  " + Math.round((d.bytes || 0) / 1024) + " KB";
        body.innerHTML = d.html;          // server-rendered from escaped markdown (reader_core.render_markdown)
        body.scrollTop = 0;
        peekState.parts = d.part_count || 1;
        var pb = document.getElementById("j-peek-parts");
        pb.textContent = "";
        if (peekState.parts > 1) {
          pb.appendChild(el("button", { class: "j-btn", on: { click: function () { if (peekState.part > 0) openPeek(path, peekState.part - 1); } } }, ["‹ Prev"]));
          pb.appendChild(el("span", { text: "Part " + (peekState.part + 1) + " of " + peekState.parts }));
          pb.appendChild(el("button", { class: "j-btn", on: { click: function () { if (peekState.part < peekState.parts - 1) openPeek(path, peekState.part + 1); } } }, ["Next ›"]));
        }
      })
      .catch(function (e) { body.textContent = "Could not open: " + e; });
  }
  function closePeek() { document.getElementById("j-peek").classList.remove("open"); }
  window.JarvisPeek = openPeek;

  // ── command palette ───────────────────────────────────────────────────────────
  var pal = { items: [], sel: 0, seq: 0, timer: null };
  function buildPalette() {
    var input = el("input", { id: "j-palette-input", placeholder: "Search tabs, chapters, documents, conversations…", autocomplete: "off" });
    var results = el("div", { id: "j-palette-results" });
    var box = el("div", { id: "j-palette" }, [input, results,
      el("div", { class: "j-pal-foot" }, ["↑↓ move", "Enter open", "Shift+Enter open beside", "Esc close"])]);
    var bd = el("div", { id: "j-palette-backdrop", on: { mousedown: function (e) { if (e.target.id === "j-palette-backdrop") closePalette(); } } }, [box]);
    document.body.appendChild(bd);
    input.addEventListener("input", function () { clearTimeout(pal.timer); pal.timer = setTimeout(runQuery, 140); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { pal.sel = Math.min(pal.sel + 1, pal.items.length - 1); paintSel(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { pal.sel = Math.max(pal.sel - 1, 0); paintSel(); e.preventDefault(); }
      else if (e.key === "Enter") { var it = pal.items[pal.sel]; if (it) { closePalette(); it.run(e.shiftKey); } e.preventDefault(); }
      else if (e.key === "Escape") { closePalette(); e.preventDefault(); }
    });
  }
  function openPalette() {
    document.getElementById("j-palette-backdrop").classList.add("show");
    var i = document.getElementById("j-palette-input");
    i.value = ""; i.focus(); runQuery();
  }
  function closePalette() { document.getElementById("j-palette-backdrop").classList.remove("show"); }

  function tabItems(q) {
    var out = [];
    WORKSPACES.forEach(function (w) {
      wsTabs(w).forEach(function (t) {
        var hay = (t[1] + " " + w.label + " " + t[0]).toLowerCase();
        if (!q || q.split(/\s+/).every(function (x) { return hay.indexOf(x) >= 0; }))
          out.push({ group: "Go to", title: t[1], sub: w.label, run: function () { go(t[0]); } });
      });
    });
    return out;
  }
  function openDoc(path, beside) {
    if (beside) openPeek(path, 0); else window.JarvisOpen("reader", { path: path, full: true });
  }
  function runQuery() {
    var q = document.getElementById("j-palette-input").value.trim().toLowerCase();
    var seq = ++pal.seq;
    var items = tabItems(q).slice(0, q ? 6 : 40);
    paint(items, q ? "Searching…" : "");
    if (q.length < 2) return;
    var jobs = [
      fetch("/api/books/search?q=" + encodeURIComponent(q)).then(function (r) { return r.ok ? r.json() : { chapters: [] }; })
        .then(function (d) { return (d.chapters || []).slice(0, 6).map(function (c) {
          return { group: "Volumes chapters", title: c.title, sub: c.volume + " · " + c.status + " · " + c.n_sources + " sources",
                   run: function () { window.JarvisOpen("books", { chapter: c.id }); } }; }); }),
      fetch("/api/debate/threads").then(function (r) { return r.ok ? r.json() : { threads: [] }; })
        .then(function (d) { var ws = q.split(/\s+/); return (d.threads || []).filter(function (t) {
            var hay = (t.title + " " + t.participants.map(function (p) { return p.name; }).join(" ")).toLowerCase();
            return ws.every(function (w) { return hay.indexOf(w) >= 0; }); }).slice(0, 6).map(function (t) {
          return { group: "Debates", title: t.title, sub: t.participants.slice(0, 3).map(function (p) { return p.name; }).join(", ") +
                     " · " + (t.last_ts || "").slice(0, 10) + (t.unsent_points ? " · " + t.unsent_points + " unsent" : ""),
                   run: function () { window.JarvisOpen("threads", { id: t.id }); } }; }); }),
      fetch("/api/files/find?limit=8&q=" + encodeURIComponent(q)).then(function (r) { return r.ok ? r.json() : { files: [] }; })
        .then(function (d) { return (d.files || []).map(function (x) {
          return { group: "Files", title: x.name, sub: x.root + " · " + x.path,
                   run: function (beside) { if (beside && /\.(md|txt|html?)$/i.test(x.path)) openPeek(x.path, 0); else window.JarvisOpen("files", { path: x.path }); } }; }); }),
      fetch("/api/reader/docs?limit=8&q=" + encodeURIComponent(q)).then(function (r) { return r.ok ? r.json() : { docs: [] }; })
        .then(function (d) { return (d.docs || []).map(function (x) {
          return { group: "Documents", title: x.title, sub: x.path, run: function (beside) { openDoc(x.path, beside); } }; }); }),
      fetch("/api/recall/search?limit=8&q=" + encodeURIComponent(q)).then(function (r) { return r.ok ? r.json() : { results: [] }; })
        .then(function (d) { return (d.results || []).map(function (x) {
          var isFile = x.type === "file";
          return { group: isFile ? "In files (Recall)" : "In conversations (Recall)",
                   title: isFile ? (x.title || x.rel_path || x.path) : ((x.surface === "AG" ? "Antigravity" : "Claude") + " · " + (x.role === "user" ? "you" : "AI") + " · " + (x.date || "")),
                   sub: x.snippet || "",
                   run: function (beside) { if (isFile && x.path) openDoc(x.path, beside); else window.JarvisOpen("recall", { q: q }); } }; }); })
    ];
    // paint each group as soon as its search answers (a cold server can take seconds for one of them)
    var lists = jobs.map(function () { return null; });
    var tail = { group: "Search", title: "Search everything for “" + q + "” in Recall", sub: "", run: function () { window.JarvisOpen("recall", { q: q }); } };
    jobs.forEach(function (p, k) {
      p.catch(function () { return []; }).then(function (l) {
        if (seq !== pal.seq) return;
        lists[k] = l;
        var all = items.slice();
        lists.forEach(function (x) { if (x) all = all.concat(x); });
        var pending = lists.filter(function (x) { return x === null; }).length;
        var keep = pal.items[pal.sel];
        paint(all.concat([tail]), pending ? "Still searching " + pending + " more place" + (pending === 1 ? "" : "s") + "…" : "");
        var again = keep ? pal.items.indexOf(keep) : -1;      // keep the highlighted row while results arrive
        if (again > 0) { pal.sel = again; paintSel(); }
      });
    });
  }
  function paint(items, status) {
    pal.items = items; pal.sel = 0;
    var box = document.getElementById("j-palette-results");
    box.textContent = "";
    var last = null;
    items.forEach(function (it, i) {
      if (it.group !== last) { box.appendChild(el("div", { class: "j-pal-group", text: it.group })); last = it.group; }
      box.appendChild(el("div", { class: "j-pal-item", "data-i": i, on: { mousedown: function (e) { e.preventDefault(); closePalette(); it.run(e.shiftKey); },
                                                                       mousemove: function () { pal.sel = i; paintSel(); } } },
        [el("span", { class: "j-pal-title", text: it.title }), el("span", { class: "j-pal-sub", text: it.sub })]));
    });
    if (status) box.appendChild(el("div", { class: "j-pal-empty", text: status }));
    else if (!items.length) box.appendChild(el("div", { class: "j-pal-empty", text: "Nothing found." }));
    paintSel();
  }
  function paintSel() {
    document.querySelectorAll(".j-pal-item").forEach(function (n) {
      var on = +n.getAttribute("data-i") === pal.sel;
      n.classList.toggle("sel", on);
      if (on) n.scrollIntoView({ block: "nearest" });
    });
  }

  // ── stale-server banner ───────────────────────────────────────────────────────
  function checkBuild() {
    fetch("/api/build_info", { cache: "no-store" }).then(function (r) { return r.ok ? r.json() : null; }).then(function (b) {
      var bn = document.getElementById("j-banner");
      if (!b) { bn.className = "show"; bn.textContent = "This server predates the new shell (no /api/build_info). Restart it to load the latest code."; return; }
      if (b.stale && b.stale.length) {
        bn.className = "show";
        bn.textContent = "";
        bn.appendChild(document.createTextNode("This server (port " + location.port + ") started before " + b.stale.length +
          " code file(s) changed on disk, so it is running older code. Restart it to load: "));
        bn.appendChild(el("code", { text: b.stale.slice(0, 4).join(", ") + (b.stale.length > 4 ? ", …" : "") }));
      } else bn.className = "";
    }).catch(function () { /* offline: the header's health dot already says so */ });
  }

  // ── keys ──────────────────────────────────────────────────────────────────────
  window.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) { e.preventDefault(); e.stopPropagation(); openPalette(); return; }
    if (e.key === "Escape" && document.getElementById("j-peek").classList.contains("open") &&
        !document.getElementById("j-palette-backdrop").classList.contains("show")) closePeek();
  }, true);
  window.addEventListener("popstate", function () { applyHash(location.hash); });

  // ── boot ──────────────────────────────────────────────────────────────────────
  function boot() {
    buildFrame();
    buildPalette();
    var due = document.getElementById("due-badge");
    if (due && window.MutationObserver) new MutationObserver(updateCounts).observe(due, { childList: true, characterData: true, subtree: true });
    var saved = null;
    try { saved = localStorage.getItem("jarvis.lastHash"); } catch (e) { /* ignore */ }
    var home = function () { go(paneExists("today") ? "today" : "cockpit", { noHash: !!location.hash }); };
    var want = parseHash(location.hash) || (saved && parseHash(saved));
    var wantHash = want ? (parseHash(location.hash) ? location.hash : saved) : null;
    if (!want) { want = { ws: "today", tab: "today", q: {} }; wantHash = "#today/today"; }   // first visit: the home screen
    // a link to a built-in tab applies now; a link to a module tab waits for the module panes (no flash of the home tab)
    var pending = false;
    if (!(wantHash && applyHash(wantHash))) {
      if (want && TAB_TO_WS[want.tab]) {
        pending = true;
        current.ws = TAB_TO_WS[want.tab]; renderSidebar();
        document.querySelectorAll(".tab-pane.active").forEach(function (p) { p.classList.remove("active"); });
      } else home();
    }
    // module tabs are added asynchronously from manifest.json; once they exist, re-render and honour a deep link to one
    var tries = 0;
    var wait = setInterval(function () {
      tries++;
      var ready = document.querySelectorAll("#module-panes > .tab-pane").length > 0;
      if (ready) {
        renderSidebar(); renderSubtabs();
        if (pending && !applyHash(wantHash)) home();
        pending = false;
      }
      if (ready || tries > 40) {
        clearInterval(wait);
        if (pending) home();          // manifest never arrived: fall back rather than show nothing
      }
    }, 100);
    checkBuild();
    setInterval(checkBuild, 60000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
