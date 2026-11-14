/* Catalog — what the AIs wrote, and what they left unfinished (Claude GUI, Opus 5.5, 2026-10-13).
   Two views, both built from the Claude and Antigravity logs by tools\ag_output_catalog.py and tools\hanging_turns.py:
     Research files  every book, dossier, report and plan Antigravity or Claude wrote (who, when, size, what was asked)
     Unfinished      every request that died on a limit, was cut off, or got no answer, newest first
   Clicking a file opens it in Files. Rebuild re-reads the logs once; nothing runs in the background. */
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
  function get(url) {
    return fetch(url).then(function (r) {
      if (!r.ok) return r.json().catch(function () { return {}; }).then(function (j) { throw new Error(j.detail || ("HTTP " + r.status)); });
      return r.json();
    });
  }
  function words(n) { return n >= 1000 ? Math.round(n / 1000) + "k words" : (n || 0) + " words"; }
  function day(ts) { return (ts || "").slice(0, 10); }
  function short(s, n) { s = (s || "").replace(/\s+/g, " ").trim(); return s.length > n ? s.slice(0, n) + "…" : s; }

  var S = { view: "files", files: null, hanging: null, q: "", writer: "", kind: "", month: "", era: "", src: "", label: "", noise: false, infra: false, root: null };
  var KIND_WORDS = {
    died: "Died on a usage limit or error, never retried",
    cut: "Cut off while the AI was still working",
    silent: "Got no reply",
    stopped: "You pressed stop and didn't ask again",
    lost: "Typed but never delivered",
    agents: "Answered, but its background agents failed"
  };

  function css() {
    if (document.getElementById("cat-css")) return;
    var st = document.createElement("style");
    st.id = "cat-css";
    st.textContent = [
      ".cat-root{padding:var(--sp-4);font:var(--fs-md) var(--font-ui);color:var(--text-main)}",
      ".cat-bar{display:flex;flex-wrap:wrap;gap:var(--sp-2);align-items:center;margin-bottom:var(--sp-3)}",
      ".cat-bar input,.cat-bar select{background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:var(--radius);padding:6px 8px;font:var(--fs-sm) var(--font-ui)}",
      ".cat-bar input{min-width:220px;flex:1}",
      ".cat-views{display:flex;gap:var(--sp-1);margin-bottom:var(--sp-3)}",
      ".cat-views .j-btn.on{border-color:var(--accent-gold);color:var(--accent-gold)}",
      ".cat-sum{color:var(--text-muted);font-size:var(--fs-sm);margin-bottom:var(--sp-3)}",
      ".cat-month{font:600 var(--fs-sm) var(--font-ui);color:var(--accent-gold);margin:var(--sp-4) 0 var(--sp-2)}",
      ".cat-row{border:1px solid var(--border);background:var(--bg-panel);border-radius:var(--radius);padding:var(--sp-2) var(--sp-3);margin-bottom:var(--sp-2)}",
      ".cat-row.click{cursor:pointer}.cat-row.click:hover{background:var(--bg-card-hover)}",
      ".cat-name{font-weight:600;word-break:break-word}",
      ".cat-meta{color:var(--text-dim);font-size:var(--fs-xs);margin-top:2px}",
      ".cat-ask{color:var(--text-muted);font-size:var(--fs-sm);margin-top:4px}",
      ".cat-tag{display:inline-block;border:1px solid var(--border);border-radius:10px;padding:0 7px;margin-right:6px;font:var(--fs-xs) var(--font-mono);color:var(--text-muted)}",
      ".cat-tag.ag{color:var(--accent-cyan);border-color:var(--accent-cyan)}",
      ".cat-tag.cl{color:var(--accent-purple);border-color:var(--accent-purple)}",
      ".cat-tag.died,.cat-tag.lost{color:var(--bad);border-color:var(--bad)}",
      ".cat-tag.cut,.cat-tag.agents{color:var(--warn);border-color:var(--warn)}",
      ".cat-gone{color:var(--bad)}",
      ".cat-more{margin-top:6px;white-space:pre-wrap;font-size:var(--fs-sm);color:var(--text-main);background:var(--bg-card);border-radius:var(--radius);padding:var(--sp-2)}",
      ".cat-actions{margin-top:6px;display:flex;gap:var(--sp-2);flex-wrap:wrap}"
    ].join("\n");
    document.head.appendChild(st);
  }

  function open(path) { if (path) window.JarvisOpen("files", { path: path }); }

  function writerTag(w) {
    var c = /Antigravity/.test(w) ? "ag" : (/Claude/.test(w) ? "cl" : "");
    return el("span", { class: "cat-tag " + c, text: w });
  }

  // ── research files ──────────────────────────────────────────────────────────
  function renderFiles(box) {
    var d = S.files, q = S.q.toLowerCase();
    var rows = d.rows.filter(function (r) {
      if (S.writer && r.writers.indexOf(S.writer) < 0) return false;
      if (S.kind && r.kind !== S.kind) return false;
      if (S.month && (r.last || "").slice(0, 7) !== S.month) return false;
      if (S.era && r.era !== S.era) return false;
      if (q && (r.rel + " " + (r.request || "") + " " + (r.description || "")).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    var tw = rows.reduce(function (a, r) { return a + (r.exists ? r.words || 0 : 0); }, 0);
    box.appendChild(el("div", { class: "cat-sum", text: rows.length + " files shown, about " + words(tw) +
      " in total. Catalog made " + (d.made || "?").replace("T", " ") + "." }));
    var month = null, shown = 0;
    rows.forEach(function (r) {
      if (shown >= 600) return;
      shown++;
      var m = (r.last || "").slice(0, 7);
      if (m !== month) { month = m; box.appendChild(el("div", { class: "cat-month", text: m || "undated" })); }
      var name = r.rel.split(/[\\/]/).pop();
      var folder = r.rel.slice(0, r.rel.length - name.length);
      var citeBox = el("div", { class: "cat-cite", style: "display:none" });
      var citeLink = el("a", { href: "#", class: "cat-cite-link", on: { click: function (e) {
        e.preventDefault(); e.stopPropagation();
        if (citeBox.style.display !== "none") { citeBox.style.display = "none"; return; }
        citeBox.style.display = ""; citeBox.textContent = "loading citation…";
        fetch("/api/catalog/cite?rel=" + encodeURIComponent(r.rel)).then(function (resp) { return resp.json(); }).then(function (c) {
          citeBox.textContent = "";
          citeBox.appendChild(el("div", { class: "fx-muted", text: "Author is a placeholder — not yet told your legal name for citations." }));
          [["SBL", c.sbl], ["Chicago", c.chicago], ["BibTeX", c.bibtex]].forEach(function (pair) {
            var row = el("div", { class: "cat-cite-row" });
            row.appendChild(el("div", { class: "cat-cite-label", text: pair[0] }));
            row.appendChild(el("pre", { class: "cat-cite-text", text: pair[1] }));
            var cb = el("button", { class: "j-btn", text: "Copy" });
            cb.addEventListener("click", function (ev) {
              ev.preventDefault(); ev.stopPropagation();
              navigator.clipboard && navigator.clipboard.writeText(pair[1]).then(function () {
                cb.textContent = "copied"; setTimeout(function () { cb.textContent = "Copy"; }, 1200);
              });
            });
            row.appendChild(cb);
            citeBox.appendChild(row);
          });
        }).catch(function (e2) { citeBox.textContent = "Couldn't build a citation: " + e2; });
      } } }, ["Cite"]);
      box.appendChild(el("div", { class: "cat-row" + (r.exists ? " click" : ""), title: r.path, on: r.exists ? { click: function () { open(r.path); } } : null }, [
        el("div", { class: "cat-name" }, [name, r.exists ? null : el("span", { class: "cat-gone", text: "  (no longer at this path)" })]),
        el("div", { class: "cat-meta" }, [].concat(r.writers.map(writerTag), [
          el("span", { class: "cat-tag", text: r.kind }),
          r.era ? el("span", { class: "cat-tag", text: r.era }) : null,
          day(r.last) + " · " + words(r.words) + (folder ? " · " + folder : ""), " · ", citeLink])),
        r.request ? el("div", { class: "cat-ask", text: "You had asked: " + short(r.request, 260) }) : null,
        citeBox
      ]));
    });
    if (rows.length > shown) box.appendChild(el("div", { class: "fx-muted", text: (rows.length - shown) + " more — narrow the search to see them." }));
  }

  function filesBar(bar) {
    var d = S.files;
    var writers = {}, kinds = {}, months = {};
    d.rows.forEach(function (r) { r.writers.forEach(function (w) { writers[w] = 1; }); kinds[r.kind] = 1; months[(r.last || "").slice(0, 7)] = 1; });
    bar.appendChild(select("Everyone", Object.keys(writers).sort(), "writer"));
    bar.appendChild(select("Every kind", Object.keys(kinds).sort(), "kind"));
    bar.appendChild(select("Every month", Object.keys(months).sort().reverse(), "month"));
    // 21 Sep 2026: the day James first asked for natural-language prose (see tools\ag_output_catalog.py)
    bar.appendChild(select("Before and after 21 Sep (natural language)", ["before natural language", "after natural language"], "era"));
    bar.appendChild(el("label", { class: "fx-muted" }, [
      el("input", { type: "checkbox", checked: S.infra || null, on: { change: function (e) { S.infra = e.target.checked; S.files = null; draw(); } } }),
      " include code, logs and AI working notes"]));
    bar.appendChild(el("a", { class: "j-btn", href: "/api/catalog/files/export?infra=" + (S.infra ? 1 : 0), text: "Export CSV" }));
    bar.appendChild(el("a", { class: "j-btn", href: "/api/catalog/portfolio/export", title: "A Markdown summary of your independent research output, attachable to a scholarship application or CV" }, ["Research Portfolio"]));
    bar.appendChild(el("a", { class: "j-btn", href: "/api/methodology/export", title: "A Methods-section-style statement: which primary-source corpora are in use and how claims are verified, with every number computed live from disk" }, ["Methodology Statement"]));
    bar.appendChild(el("a", { class: "j-btn", href: "/api/mt_lxx/divergence/export", title: "Surface-level, no-model, verse-count scan of every MT vs LXX chapter in Plenary Suite's data -- rows are tagged [R] only against named scholarship, [S] (unverified) otherwise" }, ["MT/LXX Divergence Report"]));
    bar.appendChild(el("a", { class: "j-btn", href: "/api/nt_ot_quotations/export", title: "Which text-type (MT, LXX, neither) each curated NT quotation of the OT actually follows -- verified by direct comparison of the GNT/LXX/MT text already in this suite's data, not a model's say-so" }, ["NT-OT Quotations Report"]));
    bar.appendChild(el("a", { class: "j-btn", href: "/api/scribal_tendencies/export", title: "Deterministic per-book LXX translation-technique metrics (words-per-word ratio, kai share, verse-length correlation), plus a cross-check against the MT/LXX divergence scan for Jeremiah" }, ["Scribal Tendencies Report"]));
    var rigorBox = el("span", { class: "fx-muted", text: "checking citation rigor…" });
    bar.appendChild(rigorBox);
    fetch("/api/catalog/rigor").then(function (r) { return r.json(); }).then(function (g) {
      var total = g.totals.V + g.totals.R + g.totals.S;
      if (!total) { rigorBox.textContent = ""; return; }
      rigorBox.textContent = "Citation rigor across " + g.files_with_tags + " dossiers/reports: " +
        total.toLocaleString() + " tagged claims, " + g.verified_rate + "% [V] verified, " + g.sourced_rate + "% [V]+[R] sourced.";
      rigorBox.title = g.totals.V + " [V] verified, " + g.totals.R + " [R] reliably sourced, " + g.totals.S + " [S] unsourced/stated.";
    }).catch(function () { rigorBox.textContent = ""; });
  }

  // ── unfinished requests ─────────────────────────────────────────────────────
  function renderHanging(box) {
    var d = S.hanging, q = S.q.toLowerCase();
    var rows = d.rows.filter(function (r) {
      if (S.src && r.source !== S.src) return false;
      if (S.label && r.kind !== S.label) return false;
      if (q && ((r.request || "") + " " + (r.title || "") + " " + (r.last_answer || "")).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    box.appendChild(el("div", { class: "cat-sum", text: rows.length + " unfinished requests shown, newest first, from " + d.claude_logs +
      " Claude logs and " + d.ag_sessions + " Antigravity sessions. A request a later “try again” finished is not listed. " +
      "Whether it was done later in another session isn't visible in the logs, so check the files before redoing anything." }));
    var month = null;
    rows.slice(0, 500).forEach(function (r) {
      var m = (r.ts || "").slice(0, 7);
      if (m !== month) { month = m; box.appendChild(el("div", { class: "cat-month", text: m })); }
      var more = el("div", { class: "cat-more", style: "display:none" });
      var row = el("div", { class: "cat-row" }, [
        el("div", { class: "cat-meta" }, [
          el("span", { class: "cat-tag " + (r.source === "Antigravity" ? "ag" : "cl"), text: r.source }),
          el("span", { class: "cat-tag " + r.kind, text: r.kind, title: KIND_WORDS[r.kind] || "" }),
          (r.ts || "").slice(0, 16).replace("T", " ") + " · " + (r.title || r.session.slice(0, 8)) +
            (r.attempts > 1 ? " · tried " + r.attempts + " times" : "") + (r.is_last_turn ? " · the session ended here" : "")]),
        el("div", { class: "cat-name", text: short(r.request, 300) }),
        el("div", { class: "cat-ask", text: KIND_WORDS[r.kind] + (r.error ? ": " + short(r.error, 120) : "") +
          (r.failed_agents && r.failed_agents.length ? " (" + r.failed_agents.length + " agents)" : "") }),
        el("div", { class: "cat-actions" }, [
          el("a", { href: "#", on: { click: function (e) {
            e.preventDefault();
            if (more.style.display === "none") {
              more.textContent = "You asked:\n" + r.request + (r.last_answer ? "\n\nLast words from the AI:\n" + r.last_answer : "");
              more.style.display = "";
            } else more.style.display = "none";
          } } }, ["show all"]),
          r.readable ? el("a", { href: "#", on: { click: function (e) { e.preventDefault(); open(r.readable); } } }, ["open the Antigravity conversation"]) : null
        ]),
        more
      ]);
      box.appendChild(row);
    });
  }

  function hangingBar(bar) {
    bar.appendChild(select("Claude and Antigravity", ["Claude", "Antigravity"], "src"));
    bar.appendChild(select("Every reason", Object.keys(KIND_WORDS), "label", KIND_WORDS));
    bar.appendChild(el("label", { class: "fx-muted" }, [
      el("input", { type: "checkbox", checked: S.noise || null, on: { change: function (e) { S.noise = e.target.checked; S.hanging = null; draw(); } } }),
      " include login / logout / --resume commands"]));
  }

  function select(all, opts, key, words) {
    var s = el("select", { on: { change: function (e) { S[key] = e.target.value; draw(true); } } },
      [el("option", { value: "", text: all })].concat(opts.filter(Boolean).map(function (o) {
        return el("option", { value: o, text: words && words[o] ? words[o] : o, selected: S[key] === o || null });
      })));
    return s;
  }

  // ── frame ───────────────────────────────────────────────────────────────────
  var listBox = null;
  function draw(onlyList) {
    var root = S.root;
    if (!root) return;
    if (onlyList && listBox && S[S.view]) { listBox.textContent = ""; (S.view === "files" ? renderFiles : renderHanging)(listBox); return; }
    root.textContent = "";
    root.appendChild(el("div", { class: "cat-views" }, [
      el("button", { class: "j-btn" + (S.view === "files" ? " on" : ""), on: { click: function () { S.view = "files"; draw(); } } }, ["Research files"]),
      el("button", { class: "j-btn" + (S.view === "hanging" ? " on" : ""), on: { click: function () { S.view = "hanging"; draw(); } } }, ["Unfinished requests"]),
      el("span", { style: "flex:1" }),
      rebuildBtn()
    ]));
    var bar = el("div", { class: "cat-bar" }, [
      el("input", { type: "search", placeholder: S.view === "files" ? "Search names and what you asked…" : "Search what you asked…",
        value: S.q, on: { input: function (e) { S.q = e.target.value; clearTimeout(draw.t); draw.t = setTimeout(function () { draw(true); }, 200); } } })]);
    root.appendChild(bar);
    listBox = el("div", null, [(window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading() : el("div", { class: "fx-muted", text: "Loading…" })]);
    root.appendChild(listBox);
    var key = S.view;
    var url = key === "files" ? "/api/catalog/files?infra=" + (S.infra ? 1 : 0) : "/api/catalog/hanging?noise=" + (S.noise ? 1 : 0);
    (S[key] ? Promise.resolve(S[key]) : get(url)).then(function (d) {
      S[key] = d;
      (key === "files" ? filesBar : hangingBar)(bar);
      listBox.textContent = "";
      (key === "files" ? renderFiles : renderHanging)(listBox);
    }).catch(function (e) { listBox.textContent = ""; listBox.appendChild(el("div", { class: "fx-muted", text: e.message })); });
  }

  function rebuildBtn() {
    var b = el("button", { class: "j-btn", title: "Re-read every Claude and Antigravity log (about a minute). Run the Antigravity backup first for the newest AG sessions." }, ["Rebuild from the logs"]);
    b.addEventListener("click", function () {
      b.disabled = true; b.textContent = "Reading the logs…";
      fetch("/api/catalog/rebuild", { method: "POST" }).then(function () {
        var t = setInterval(function () {
          get("/api/catalog/rebuild").then(function (s) {
            if (s.running) return;
            clearInterval(t);
            b.disabled = false;
            b.textContent = s.error ? "Rebuild failed" : "Rebuilt";
            if (s.error) b.title = s.error;
            S.files = null; S.hanging = null; draw();
          });
        }, 3000);
      });
    });
    return b;
  }

  function load(root, opts) {
    css();
    root.classList.add("cat-root");
    S.root = root;
    if (opts && opts.view) S.view = opts.view;      // the Organizer opens it on "files" or "hanging"
    draw();
  }

  window.JarvisModules.catalog = { load: load };
})();
