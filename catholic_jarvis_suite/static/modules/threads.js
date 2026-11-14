/* Threads — debates harvested from the logs (Phase 2, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).
   Left: every debate you pasted into Claude or Antigravity, newest first, with how many drafted points the logs
   never show you posting. Right: one debate's Rule 15 state —
     State        their latest message (and its claims) beside the payload: every drafted point, labelled
                  posted / adapted / drawn on / partial / unsent; unsent points stay until you drop them.
     Conversation the debate as posted, merged from every paste.
     Pastes       each paste and AI session it came from; join or split threads the grouping got wrong.
     Check        paste a reply: claim check (corpus + never-deploy) and Discord-ready split.
   "Copy brief" gives Claude/Antigravity the whole state, so a new draft cannot forget the unsent points. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};
  var S = { list: [], filter: "", tid: null, t: null, view: "state", socratic: false, showDone: false };

  // JarvisOpen("threads", {id}) from the Ctrl+K palette or another tab
  window.addEventListener("jarvis:open-threads", function (ev) {
    var d = (ev && ev.detail) || {};
    if (!d.id) return;
    S.focusMsg = (d.msg === undefined || d.msg === null) ? null : +d.msg;     // from Packs / Drill: show that message
    S.view = S.focusMsg === null ? "state" : "conv";
    if (S.ui) open(d.id); else S.tid = d.id;
  });

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "text") e.textContent = v;
      else if (k === "html") e.innerHTML = v;      // server-rendered by files_md (escaped)
      else if (k === "on") Object.keys(v).forEach(function (ev) { e.addEventListener(ev, v[ev]); });
      else e.setAttribute(k, v === true ? "" : v);
    });
    (kids || []).forEach(function (c) { if (c !== null && c !== undefined) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function api(url, body) {
    var opts = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
    return fetch(url, opts).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw new Error(j.detail || "HTTP " + r.status); return j; });
    });
  }
  function day(ts) { return (ts || "").slice(0, 10); }
  function when(ts) { return (ts || "").slice(0, 16).replace("T", " "); }
  function copy(text, what) {
    navigator.clipboard.writeText(text).then(function () { if (window.showToast) window.showToast((what || "Copied") + " — " + text.length.toLocaleString() + " characters", "success"); });
  }
  var STATE_LABEL = { posted: "posted", adapted: "posted in your words", "drawn on": "drawn on", partial: "partly posted", unsent: "not seen posted" };
  var LIVE = { unsent: 1, partial: 1, "drawn on": 1 };

  function load(root) {
    root.textContent = "";
    root.classList.add("dx-root");
    var search = el("input", { class: "fx-find", placeholder: "Filter by topic or name…", autocomplete: "off" });
    var listBox = el("div", { class: "dx-list" });
    var head = el("div", { class: "dx-listhead" });
    var side = el("div", { class: "dx-side" }, [search, head, listBox]);
    var main = el("div", { class: "dx-main" }, [(window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading your debates from the logs…") : el("div", { class: "j-empty", text: "Loading your debates from the logs…" })]);
    root.appendChild(side); root.appendChild(main);
    S.ui = { list: listBox, head: head, main: main, search: search };
    search.addEventListener("input", function () { S.filter = search.value.trim().toLowerCase(); renderList(); });
    refresh();
  }

  function refresh(force) {
    var go = force ? api("/api/debate/harvest", {}) : Promise.resolve();
    go.then(function () { return api("/api/debate/threads"); }).then(function (d) {
      S.list = d.threads; S.meta = d;
      renderList();
      if (!S.tid && S.list.length) open(S.list[0].id);
      else if (S.tid) open(S.tid);
    }).catch(function (e) { S.ui.main.textContent = "Could not harvest: " + e.message; });
  }

  function renderList() {
    var h = S.ui.head, b = S.ui.list;
    h.textContent = ""; b.textContent = "";
    var owed = S.list.reduce(function (n, t) { return n + (t.unsent_points ? 1 : 0); }, 0);
    h.appendChild(el("div", { class: "fx-muted" }, [S.meta.n_threads + " debates from " + S.meta.n_snapshots + " pastes · " + owed + " with unsent points"]));
    h.appendChild(el("button", { class: "j-btn ghost", title: "Re-read the logs now (normally automatic when they change)", on: { click: function () { refresh(true); } } }, ["↻ Re-harvest"]));
    S.list.filter(function (t) {
      if (!S.filter) return true;
      var hay = (t.title + " " + t.participants.map(function (p) { return p.name; }).join(" ")).toLowerCase();
      return S.filter.split(/\s+/).every(function (w) { return hay.indexOf(w) >= 0; });
    }).forEach(function (t) {
      var who = t.participants.slice(0, 3).map(function (p) { return p.name; }).join(", ");
      b.appendChild(el("div", { class: "dx-item" + (t.id === S.tid ? " active" : ""), "data-id": t.id, on: { click: function () { open(t.id); } } }, [
        el("div", { class: "dx-title" }, [t.title, t.unsent_points ? el("span", { class: "dx-badge", title: "points drafted but not seen posted", text: t.unsent_points }) : null]),
        el("div", { class: "fx-muted", text: who }),
        el("div", { class: "fx-muted", text: day(t.first_ts) + (day(t.last_ts) !== day(t.first_ts) ? " → " + day(t.last_ts) : "") + " · " +
                                              t.n_snapshots + " paste" + (t.n_snapshots === 1 ? "" : "s") + " · " + t.surfaces.join("+") })
      ]));
    });
  }

  function open(tid) {
    S.tid = tid;
    document.querySelectorAll(".dx-item").forEach(function (n) { n.classList.toggle("active", n.getAttribute("data-id") === tid); });
    api("/api/debate/threads/" + tid).then(function (t) { S.t = t; renderThread(); })
      .catch(function (e) { S.ui.main.textContent = e.message; });
  }

  function renderThread() {
    var t = S.t, m = S.ui.main;
    m.textContent = "";
    var title = el("h2", { class: "dx-h", title: "Click to rename", text: t.title, on: { click: rename } });
    var tabs = el("div", { class: "dx-tabs" });
    [["state", "State"], ["conv", "Conversation (" + t.n_messages + ")"], ["pastes", "Pastes (" + t.n_snapshots + ")"], ["check", "Check a reply"]].forEach(function (v) {
      tabs.appendChild(el("button", { class: "j-sub" + (S.view === v[0] ? " active" : ""), on: { click: function () { S.view = v[0]; renderThread(); } } }, [v[1]]));
    });
    var soc = el("label", { class: "dx-toggle", title: "Rule 17: ask for the passage and the reasoning instead of lecturing from unread sources" },
      [el("input", { type: "checkbox", checked: S.socratic ? true : null, on: { change: function (e) { S.socratic = e.target.checked; } } }), " Socratic"]);
    m.appendChild(el("div", { class: "dx-top" }, [
      el("div", { style: "min-width:0;flex:1" }, [title, el("div", { class: "fx-muted", text:
        t.participants.slice(0, 8).map(function (p) { return p.name + " (" + p.messages + ")"; }).join(", ") + "  ·  " + when(t.first_ts) + " → " + when(t.last_ts) })]),
      soc,
      el("button", { class: "j-btn primary", title: "Copy the whole debate state for Claude or Antigravity: conversation, their latest, every unsent point, Rule 15 instructions",
                     on: { click: function () { api("/api/debate/threads/" + t.id + "/brief?socratic=" + (S.socratic ? 1 : 0)).then(function (b) { copy(b.text, "Brief copied"); }); } } }, ["Copy brief for AI"]),
      el("button", { class: "j-btn ghost", title: "Hide this thread from the list", on: { click: function () {
        api("/api/debate/threads/" + t.id + "/hide", { hidden: true }).then(function () { S.tid = null; refresh(); }); } } }, ["Hide"])
    ]));
    m.appendChild(tabs);
    var body = el("div", { class: "dx-body" });
    m.appendChild(body);
    ({ state: viewState, conv: viewConv, pastes: viewPastes, check: viewCheck })[S.view](body, t);
  }

  function rename() {
    var v = prompt("Name this debate (empty = automatic):", S.t.title);
    if (v === null) return;
    api("/api/debate/threads/" + S.t.id + "/title", { title: v }).then(function (t) { S.t = t; renderThread(); refreshList(); });
  }
  function refreshList() { api("/api/debate/threads").then(function (d) { S.list = d.threads; S.meta = d; renderList(); }); }

  // ── State: their latest + the payload ──────────────────────────────────────────
  function viewState(body, t) {
    var left = el("div", { class: "dx-col" });
    var right = el("div", { class: "dx-col" });
    body.appendChild(el("div", { class: "dx-grid" }, [left, right]));
    var tl = t.their_latest;
    left.appendChild(el("h4", { class: "dx-sec", text: tl ? "Their latest — " + tl.author : "Their latest" }));
    if (tl) {
      left.appendChild(el("div", { class: "fx-muted", text: tl.james_posted_since ? "You have posted " + tl.james_posted_since + " message(s) since." : "Not answered yet in the logs." }));
      tl.messages.forEach(function (i) { left.appendChild(msgEl(t.messages[i])); });
      if (tl.claims && tl.claims.length) {
        left.appendChild(el("h4", { class: "dx-sec", text: "Claims in it (" + tl.claims.length + ")" }));
        tl.claims.forEach(function (c) {
          left.appendChild(el("div", { class: "dx-claim" }, [c.text, c.signals.length ? el("div", { class: "fx-muted", text: c.signals.join(" · ") }) : null]));
        });
      }
    } else left.appendChild(el("div", { class: "fx-muted", text: "Only your messages in this log." }));

    var pts = t.points;
    var live = pts.filter(function (p) { return LIVE[p.state] && !p.dropped && p.role === "draft"; });
    var notes = pts.filter(function (p) { return LIVE[p.state] && !p.dropped && p.role !== "draft"; });
    var done = pts.filter(function (p) { return !LIVE[p.state] || p.dropped; });
    right.appendChild(el("div", { class: "dx-payhead" }, [
      el("h4", { class: "dx-sec", text: "Payload: " + live.length + " drafted repl" + (live.length === 1 ? "y" : "ies") + " not seen posted" }),
      el("button", { class: "j-btn", title: "Copy every point still owed, oldest first", on: { click: function () {
        copy(live.map(function (p) { return "### " + p.title + "\n" + (p.unsent_text || p.text); }).join("\n\n"), "Payload copied"); } } }, ["Copy payload"])
    ]));
    right.appendChild(el("div", { class: "fx-muted", text: "Rule 15: a point stays here until a later paste shows you posted it, or you drop it. Newer drafts never remove older points." }));
    var byDraft = {};
    live.forEach(function (p) { (byDraft[p.ts] = byDraft[p.ts] || []).push(p); });
    Object.keys(byDraft).sort().forEach(function (ts) {
      right.appendChild(el("div", { class: "dx-draft", text: "Drafted " + when(ts) + " (" + byDraft[ts][0].surface + ")" }));
      byDraft[ts].forEach(function (p) { right.appendChild(pointEl(p)); });
    });
    if (!live.length) right.appendChild(el("div", { class: "j-empty", text: "Nothing owed: every drafted reply was posted or dropped." }));
    if (notes.length) {
      var nd = el("details", { class: "dx-done" }, [el("summary", { text: "The AI's analysis notes (" + notes.length + ") — not drafts, so not counted as owed; they still go into the brief as background" })]);
      notes.forEach(function (p) { nd.appendChild(pointEl(p)); });
      right.appendChild(nd);
    }
    if (done.length) {
      var det = el("details", { class: "dx-done" }, [el("summary", { text: "Posted or dropped (" + done.length + ")" })]);
      done.forEach(function (p) { det.appendChild(pointEl(p)); });
      right.appendChild(det);
    }
  }

  function pointEl(p) {
    var st = p.dropped ? "dropped" : p.state;
    var card = el("details", { class: "dx-point dx-" + st.replace(/\s/g, "-") }, [
      el("summary", null, [
        el("span", { class: "dx-state", text: p.dropped ? "dropped" : (STATE_LABEL[p.state] || p.state) }),
        el("span", { class: "dx-ptitle", text: p.title }),
        el("span", { class: "fx-muted", text: " " + p.words + " words" })
      ]),
      el("div", { class: "fx-md dx-pbody", html: p.html }),
      p.why ? el("div", { class: "fx-muted", text: p.why }) : null,
      el("div", { class: "dx-pactions" }, [
        el("button", { class: "j-btn", on: { click: function () { copy(p.unsent_text || p.text, "Point copied"); } } }, ["Copy"]),
        el("button", { class: "j-btn ghost", on: { click: function () { discordPreview(p.unsent_text || p.text); } } }, ["Discord-ready"]),
        p.dropped
          ? el("button", { class: "j-btn ghost", on: { click: function () { setDrop(p, false); } } }, ["Restore"])
          : el("button", { class: "j-btn ghost", title: "You decided not to use this point; it leaves the payload and the brief", on: { click: function () { setDrop(p, true); } } }, ["Drop"])
      ])
    ]);
    return card;
  }
  function setDrop(p, on) {
    api("/api/debate/threads/" + S.t.id + "/drop", { point_id: p.id, dropped: on }).then(function () { open(S.t.id); refreshList(); });
  }
  function msgEl(m) {
    return el("div", { class: "dx-msg" + (m.is_james ? " dx-me" : ""), "data-i": m.i }, [
      el("div", { class: "dx-who", text: (m.is_james ? "You" : m.author) + (m.time ? "  ·  " + m.time : "") }),
      el("div", { class: "dx-text", text: m.text })
    ]);
  }

  // ── Conversation ───────────────────────────────────────────────────────────────
  function viewConv(body, t) {
    var lastSnap = -1;
    t.messages.forEach(function (m) {
      if (m.first_snap !== lastSnap) {
        var s = t.snapshots[m.first_snap];
        body.appendChild(el("div", { class: "dx-draft", text: "First seen in the paste of " + when(s.ts) + " (" + s.surface + ")" }));
        lastSnap = m.first_snap;
      }
      body.appendChild(msgEl(m));
    });
    if (S.focusMsg !== null && S.focusMsg !== undefined) {
      var target = body.querySelector('.dx-msg[data-i="' + S.focusMsg + '"]');
      S.focusMsg = null;
      if (target) { target.classList.add("dx-focus"); setTimeout(function () { target.scrollIntoView({ block: "center" }); }, 50); }
    }
  }

  // ── Pastes: join / split ───────────────────────────────────────────────────────
  function viewPastes(body, t) {
    body.appendChild(el("div", { class: "fx-muted", text: "Pastes join into one debate when they share messages, or when they come minutes apart in the same AI chat with the same people. If that got it wrong, split here or join with another debate." }));
    t.snapshots.forEach(function (s, k) {
      body.appendChild(el("div", { class: "dx-paste" }, [
        el("div", null, [el("strong", { text: when(s.ts) }), "  " + (s.surface === "AG" ? "Antigravity" : "Claude") + " chat " + s.sid.slice(0, 8) +
          "  ·  " + s.n_messages + " messages  ·  " + s.n_drafts + " AI repl" + (s.n_drafts === 1 ? "y" : "ies")]),
        s.preamble ? el("div", { class: "fx-muted", text: "Your note with it: " + s.preamble.slice(0, 240) }) : null,
        k > 0 ? el("button", { class: "j-btn ghost", title: "Start a separate debate from this paste on", on: { click: function () {
          api("/api/debate/split", { snap: s.id }).then(function () { refresh(); }); } } }, ["Split here"]) : null
      ]));
    });
    var others = S.list.filter(function (x) { return x.id !== t.id; }).slice(0, 60);
    var sel = el("select", { class: "fx-select" }, others.map(function (x) { return el("option", { value: x.id, text: day(x.last_ts) + " — " + x.title }); }));
    body.appendChild(el("div", { class: "dx-paste" }, [el("strong", { text: "Join with another debate " }), sel,
      el("button", { class: "j-btn", on: { click: function () {
        api("/api/debate/threads/" + sel.value).then(function (o) {
          return api("/api/debate/join", { a: t.snapshots[0].id, b: o.snapshots[0].id });
        }).then(function () { refresh(); });
      } } }, ["Join"])]));
  }

  // ── Check a reply before posting ──────────────────────────────────────────────
  function viewCheck(body) {
    var ta = el("textarea", { class: "fx-textarea", rows: 10, placeholder: "Paste the reply you are about to post…" });
    var out = el("div");
    body.appendChild(ta);
    body.appendChild(el("div", { class: "dx-pactions" }, [
      el("button", { class: "j-btn primary", on: { click: function () { checkClaims(ta.value, out); } } }, ["Check claims"]),
      el("button", { class: "j-btn", on: { click: function () { discordPreview(ta.value, out); } } }, ["Make Discord-ready"])
    ]));
    body.appendChild(out);
  }
  function checkClaims(text, out) {
    out.textContent = "Checking against the corpus and the never-deploy list…";
    api("/api/desk/check", { text: text }).then(function (r) {
      out.textContent = "";
      var claims = r.claims || [];
      out.appendChild(el("h4", { class: "dx-sec", text: claims.length + " factual-looking claim(s)" + (r.note ? " — " + r.note : "") }));
      claims.forEach(function (c) {
        var strong = (c.hits || []).filter(function (h) { return h.level === "strong"; });
        var src = c.best || c.warned;
        var where = src ? (src.path.split(/[\\/]/).pop() + ":" + src.line) : "";
        out.appendChild(el("div", { class: "dx-claim dx-prov-" + c.provenance }, [
          c.text,
          el("div", { class: "fx-muted" }, [
            el("strong", { text: c.suffix || c.provenance }),
            (c.never_deploy && c.never_deploy.length ? "  ⚠ matches the never-deploy list" : ""),
            (where ? "  ·  " + where : ""),
            (strong.length > 1 ? "  ·  " + strong.length + " strong matches" : "")
          ]),
          src ? el("button", { class: "j-btn ghost", title: "Open the matching file beside this", on: { click: function () { if (window.JarvisPeek) window.JarvisPeek(src.path, 0); } } }, ["Open source"]) : null
        ]));
      });
    }).catch(function (e) { out.textContent = "Check failed: " + e.message; });
  }
  function discordPreview(text, out) {
    api("/api/debate/discord", { text: text }).then(function (d) {
      var box = out || S.ui.main.querySelector(".dx-body");
      var wrap = el("div", { class: "dx-discord" }, [el("h4", { class: "dx-sec", text: "Discord-ready: " + d.parts.length + " message(s)" + (d.changes.length ? " — " + d.changes.join(", ") : "") })]);
      d.parts.forEach(function (p, i) {
        wrap.appendChild(el("div", { class: "dx-msg dx-me" }, [
          el("div", { class: "dx-who" }, ["Message " + (i + 1) + " · " + p.length + " characters  ",
            el("button", { class: "j-btn ghost", on: { click: function () { copy(p, "Message " + (i + 1) + " copied"); } } }, ["Copy"])]),
          el("div", { class: "dx-text", text: p })]));
      });
      if (out) { out.textContent = ""; out.appendChild(wrap); } else { box.insertBefore(wrap, box.firstChild); wrap.scrollIntoView({ block: "start" }); }
    });
  }

  window.JarvisModules.threads = { load: load };
})();
