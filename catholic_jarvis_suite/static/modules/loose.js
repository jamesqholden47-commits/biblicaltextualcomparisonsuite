/* Loose Ends tab (module id "loose"). Claude GUI, Opus 5.5, 2026-10-06.
 * Four views over one register of every document the AIs produced:
 *   Top loose ends  - subject documents not found inside any canonical book, ranked
 *   Threads         - documents grouped by topic, with the Question Ledger's questions on the same topic
 *   What they owe   - every "still needs checking / FETCH LIST / OPEN QUESTIONS / TODO" item, book-wide
 *   All documents   - the full register with filters
 * All document and log text goes in through textContent; nothing is inserted as raw HTML. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

  var STATUS = [["open", "Open"], ["merged", "Merged"], ["superseded", "Superseded"], ["parked", "Parked"],
                ["done", "Done"], ["ignore", "Ignore"]];
  var STATUS_COLOR = { unreviewed: "var(--text-dim)", open: "var(--accent-cyan)", merged: "var(--accent-green)",
    superseded: "var(--text-muted)", parked: "var(--accent-gold)", done: "var(--accent-green)", ignore: "var(--text-dim)" };
  var KIND_COLOR = { SUBJECT: "var(--accent-gold)", INFRASTRUCTURE: "var(--accent-blue)", PROVENANCE: "var(--text-muted)" };
  var INPUT = "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:4px;padding:5px 8px;font-size:12px;";
  var BTN = "background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);border-radius:4px;padding:4px 10px;font-size:11px;cursor:pointer;";
  var CARD = "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px 12px;margin-bottom:8px;";

  function el(tag, props, text, children) {
    var n = document.createElement(tag);
    if (props) Object.keys(props).forEach(function (k) {
      if (k === "style") n.style.cssText = props[k];
      else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), props[k]);
      else n.setAttribute(k, props[k]);
    });
    if (text !== undefined && text !== null) n.textContent = text;
    (children || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }
  function chip(text, color, title) {
    return el("span", { style: "display:inline-block;font-size:10px;padding:1px 6px;margin-right:4px;border-radius:3px;" +
      "border:1px solid " + color + ";color:" + color + ";", title: title || "" }, text);
  }
  function kb(n) { return n >= 1048576 ? (n / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB"; }
  function short(p) { var parts = p.split("\\"); return parts.slice(-3).join("\\"); }
  function copyBtn(text, label) {
    return el("button", { style: BTN + "padding:1px 6px;", title: text, onclick: function (e) {
      e.stopPropagation(); navigator.clipboard && navigator.clipboard.writeText(text);
      e.target.textContent = "copied"; setTimeout(function () { e.target.textContent = label; }, 900); } }, label);
  }
  function api(url, opts) { return fetch(url, opts).then(function (r) { if (!r.ok) throw new Error(r.status + " " + url); return r.json(); }); }

  function load(root) {
    root.textContent = "";
    root.style.cssText = "padding:16px;color:var(--text-main);";
    var view = "top";

    var header = el("div", { style: "display:flex;align-items:baseline;gap:12px;margin-bottom:6px;" }, null, [
      el("h2", { style: "margin:0;font-size:16px;color:var(--accent-gold);" }, "Loose Ends"),
      el("span", { style: "font-size:11px;color:var(--text-dim);" },
        "every report, dossier and dissertation the AIs produced: which went into a book, what each still owes, and which are the same thing twice")
    ]);
    var stats = el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 12px 0;" });
    var tabs = el("div", { style: "display:flex;gap:6px;margin-bottom:10px;" });
    var bar = el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px;" });
    var info = el("div", { style: "font-size:12px;color:var(--text-muted);margin-bottom:8px;" });
    var list = el("div");
    var pager = el("div", { style: "display:flex;gap:8px;align-items:center;margin:12px 0;font-size:12px;color:var(--text-muted);" });
    [header, stats, tabs, bar, info, list, pager].forEach(function (n) { root.appendChild(n); });

    var fText = el("input", { type: "text", placeholder: "words in title, path or open items", style: INPUT + "min-width:230px;" });
    var fArea = el("select", { style: INPUT }, null, [el("option", { value: "" }, "any area")]);
    var fKind = el("select", { style: INPUT }, null, [["", "any kind"], ["SUBJECT", "subject"], ["INFRASTRUCTURE", "infrastructure"], ["PROVENANCE", "provenance"]]
      .map(function (o) { return el("option", { value: o[0] }, o[1]); }));
    var fSignal = el("select", { style: INPUT }, null, [["", "any signal"], ["not_integrated", "not in any book"], ["open_items", "owes items"],
      ["variants", "has variants/copies"], ["never_mentioned", "never mentioned again"], ["partial", "partial worker report"]]
      .map(function (o) { return el("option", { value: o[0] }, o[1]); }));
    var fMark = el("select", { style: INPUT }, null, [el("option", { value: "" }, "any mark"), el("option", { value: "unreviewed" }, "unreviewed")]
      .concat(STATUS.map(function (s) { return el("option", { value: s[0] }, s[1].toLowerCase()); })));
    var fSince = el("input", { type: "date", style: INPUT, title: "changed since" });
    var fSort = el("select", { style: INPUT }, null, [["score", "loosest first"], ["newest", "newest"], ["oldest", "oldest"], ["size", "largest"], ["open_items", "most owed"]]
      .map(function (o) { return el("option", { value: o[0] }, o[1]); }));
    var bApply = el("button", { style: BTN + "color:var(--accent-gold);border-color:var(--accent-gold);" }, "Apply");
    var bRebuild = el("button", { style: BTN, title: "Rescan every document (about 25 s). Your marks are never touched." }, "Rescan");
    var bExport = el("button", { style: BTN, title: "Markdown checklist of subject documents not in any book" }, "Export .md");
    var state = { offset: 0, limit: 40 };

    function setTabs() {
      tabs.textContent = "";
      [["top", "Top loose ends"], ["threads", "Threads"], ["owed", "What they owe"], ["all", "All documents"]].forEach(function (t) {
        tabs.appendChild(el("button", { style: BTN + (view === t[0] ? "color:var(--accent-gold);border-color:var(--accent-gold);" : ""),
          onclick: function () { view = t[0]; state.offset = 0; render(); } }, t[1]));
      });
    }
    function setBar(fields) {
      bar.textContent = "";
      fields.concat([bApply, bRebuild, bExport]).forEach(function (f) { bar.appendChild(f); });
    }

    function stat(label, value, color, onclick) {
      return el("div", { style: CARD + "margin:0;padding:6px 10px;min-width:110px;cursor:" + (onclick ? "pointer" : "default") + ";", onclick: onclick }, null, [
        el("div", { style: "font-size:18px;font-weight:600;color:" + (color || "var(--text-main)") + ";" }, String(value)),
        el("div", { style: "font-size:10px;color:var(--text-dim);" }, label)]);
    }
    function loadSummary() {
      return api("/api/loose/summary").then(function (s) {
        stats.textContent = "";
        stats.appendChild(stat("documents registered", s.n_docs));
        stats.appendChild(stat("subject docs NOT in any book", s.subject_not_integrated, "var(--accent-red)", function () { view = "top"; render(); }));
        stats.appendChild(stat("subject docs found in a book", s.subject_integrated, "var(--accent-green)"));
        stats.appendChild(stat("items still owed", s.open_items_total, "var(--accent-gold)", function () { view = "owed"; render(); }));
        stats.appendChild(stat("docs with variants/copies", s.with_variants, "var(--accent-cyan)", function () { fSignal.value = "variants"; view = "all"; render(); }));
        stats.appendChild(stat("never mentioned again", s.never_mentioned, "var(--text-muted)"));
        stats.appendChild(stat("changed in last 7 days", s.changed_last_7_days));
        stats.appendChild(stat("topic threads", s.threads, null, function () { view = "threads"; render(); }));
        fArea.textContent = ""; fArea.appendChild(el("option", { value: "" }, "any area"));
        Object.keys(s.by_area || {}).forEach(function (a) { fArea.appendChild(el("option", { value: a }, a + " (" + s.by_area[a] + ")")); });
        info.dataset.built = "register built " + (s.built_at || "?") + " in " + s.seconds + " s; books checked: " + (s.targets_found || []).length;
      });
    }

    function markRow(d, onDone) {
      var row = el("div", { style: "display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-top:6px;" });
      var note = el("input", { type: "text", placeholder: "note / merged into (path)", style: INPUT + "padding:2px 6px;font-size:11px;min-width:220px;",
        value: (d.mark && (d.mark.merged_into || d.mark.note)) || "" });
      STATUS.forEach(function (s) {
        row.appendChild(el("button", { style: BTN + "padding:1px 8px;" + (d.status === s[0] ? "color:" + STATUS_COLOR[s[0]] + ";border-color:" + STATUS_COLOR[s[0]] + ";" : ""),
          onclick: function () {
            var v = note.value || "";
            api("/api/loose/mark", { method: "POST", headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: d.id, status: s[0], note: s[0] === "merged" ? "" : v, merged_into: s[0] === "merged" ? v : "" }) })
              .then(function () { d.status = s[0]; onDone(); }).catch(function (e) { alert(e); });
          } }, s[1]));
      });
      row.appendChild(el("button", { style: BTN + "padding:1px 8px;", onclick: function () {
        api("/api/loose/mark", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: d.id, status: "unreviewed" }) })
          .then(function () { d.status = "unreviewed"; onDone(); }); } }, "clear"));
      row.appendChild(note);
      return row;
    }

    function docCard(d) {
      var card = el("div", { style: CARD });
      function paint() {
        card.textContent = "";
        var top = el("div", { style: "display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;" }, null, [
          el("span", { style: "font-size:13px;font-weight:600;" }, d.title),
          chip(d.kind.toLowerCase(), KIND_COLOR[d.kind] || "var(--text-dim)"),
          chip(d.area, "var(--text-muted)"),
          chip(d.status, STATUS_COLOR[d.status] || "var(--text-dim)", d.mark && d.mark.note ? d.mark.note : ""),
          el("span", { style: "font-size:11px;color:var(--text-dim);" }, d.mtime.replace("T", " ") + " · " + kb(d.bytes) + (d.words ? " · " + d.words.toLocaleString() + " words" : "") + " · score " + d.score)
        ]);
        card.appendChild(top);
        card.appendChild(el("div", { style: "font-size:11px;color:var(--text-muted);margin-top:3px;display:flex;gap:6px;align-items:center;" }, null,
          [el("span", null, short(d.path)), copyBtn(d.path, "copy path")]));
        var sig = el("div", { style: "margin-top:5px;" });
        if (d.kind === "SUBJECT") sig.appendChild(d.integrated_into.length ? chip("in " + d.integrated_into.map(function (t) { return t.target.split("\\").pop(); }).join(", "), "var(--accent-green)",
          d.integrated_into.map(function (t) { return t.found + "/" + t.of + " sampled passages found in " + t.target; }).join("\n")) : chip("not in any book", "var(--accent-red)", "none of its sampled passages were found in the master dissertation, the Mexico books or the Scriptorium"));
        if (d.open_items.length) sig.appendChild(chip("owes " + d.open_items.length, "var(--accent-gold)"));
        if (d.exact_copies.length) sig.appendChild(chip(d.exact_copies.length + " identical copies", "var(--accent-cyan)"));
        if (d.title_variants.length) sig.appendChild(chip(d.title_variants.length + " same-title versions", "var(--accent-cyan)"));
        if (d.referenced_by.length) sig.appendChild(chip("named in " + d.referenced_by.length + " docs", "var(--text-muted)"));
        if (d.chat_mentions.count) sig.appendChild(chip("mentioned in chat " + d.chat_mentions.count + "×, last " + (d.chat_mentions.last || "").slice(0, 10), "var(--text-muted)"));
        if (!d.referenced_by.length && !d.chat_mentions.count) sig.appendChild(chip("never mentioned again", "var(--text-dim)"));
        if (d.producer) sig.appendChild(chip("made by " + d.producer.sessions.slice(0, 3).join(", ") + (d.producer.sessions.length > 3 ? " …" : ""), "var(--text-dim)",
          "first write " + (d.producer.first || "?") + ", last " + (d.producer.last || "?") + ", " + d.producer.edits + " write calls"));
        if (d.partial) sig.appendChild(chip("PARTIAL (no completion marker)", "var(--accent-red)"));
        card.appendChild(sig);
        if (d.open_items.length) {
          var det = el("details", { style: "margin-top:5px;font-size:12px;" }, null, [el("summary", { style: "cursor:pointer;color:var(--accent-gold);" }, "what it still owes (" + d.open_items.length + ")")]);
          var ul = el("ul", { style: "margin:4px 0 0 18px;padding:0;" });
          d.open_items.slice(0, 25).forEach(function (it) { ul.appendChild(el("li", { style: "margin:2px 0;color:var(--text-main);" }, null,
            [el("span", { style: "color:var(--text-dim);font-size:10px;" }, "[" + it.section + "] "), document.createTextNode(it.text)])); });
          det.appendChild(ul); card.appendChild(det);
        }
        card.appendChild(markRow(d, paint));
      }
      paint();
      return card;
    }

    function renderDocs(params) {
      var q = new URLSearchParams(params);
      q.set("limit", state.limit); q.set("offset", state.offset);
      list.textContent = ""; info.textContent = "Loading…";
      return api("/api/loose/items?" + q.toString()).then(function (r) {
        info.textContent = r.total + " documents · " + (info.dataset.built || "");
        var cards = {};
        r.items.forEach(function (d) { var cd = docCard(d); cards[d.id] = cd; list.appendChild(cd); });
        // Where is each document planned in the Volumes tab? (one request for the whole page)
        if (r.items.length) api("/api/books/where?ids=" + r.items.map(function (d) { return d.id; }).join(",")).then(function (w) {
          Object.keys(w).forEach(function (id) {
            var x = w[id], cd = cards[id]; if (!cd) return;
            var line = el("div", { style: "margin-top:4px;font-size:11px;" });
            if (x.chapter) {
              line.appendChild(el("a", { href: "#", style: "color:var(--accent-cyan);", onclick: function (e) { e.preventDefault(); window.JarvisOpen && window.JarvisOpen("books", { chapter: x.chapter }); } },
                "planned → " + x.volume + " · " + x.chapter_title + " (" + x.state + ")"));
            } else {
              line.appendChild(el("span", { style: "color:var(--text-dim);" }, "volumes: " + x.state));
            }
            cd.appendChild(line);
          });
        }).catch(function () { /* Volumes not planned yet: no link */ });
        r.items.forEach(function (d) {
          var cd = cards[d.id];
          cd.appendChild(el("button", { style: BTN + "margin-top:4px;margin-right:4px;", onclick: function () { window.JarvisOpen && window.JarvisOpen("reader", { path: d.path }); } }, "read in Reader"));
        });
        pager.textContent = "";
        if (state.offset > 0) pager.appendChild(el("button", { style: BTN, onclick: function () { state.offset = Math.max(0, state.offset - state.limit); render(); } }, "‹ prev"));
        pager.appendChild(el("span", null, (state.offset + 1) + "–" + Math.min(r.total, state.offset + state.limit) + " of " + r.total));
        if (state.offset + state.limit < r.total) pager.appendChild(el("button", { style: BTN, onclick: function () { state.offset += state.limit; render(); } }, "next ›"));
      });
    }

    function renderThreads() {
      list.textContent = ""; pager.textContent = ""; info.textContent = "Loading…";
      var q = fText.value ? "?text=" + encodeURIComponent(fText.value) : "";
      return api("/api/loose/threads" + q).then(function (r) {
        info.textContent = r.threads.length + " of " + r.total + " threads (topics with two or more subject documents), loosest first";
        r.threads.forEach(function (t) {
          var c = el("div", { style: CARD });
          c.appendChild(el("div", { style: "display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;" }, null, [
            el("span", { style: "font-size:13px;font-weight:600;color:var(--accent-gold);" }, t.label.join(" · ")),
            chip(t.n_docs + " docs", "var(--text-muted)"),
            chip(t.n_integrated + " in a book", t.n_integrated ? "var(--accent-green)" : "var(--accent-red)"),
            t.n_open_items ? chip("owes " + t.n_open_items, "var(--accent-gold)") : null,
            t.n_questions ? chip(t.n_questions + " questions asked", "var(--accent-cyan)") : null,
            t.n_missed_questions ? chip(t.n_missed_questions + " possibly missed", "var(--accent-red)") : null,
            el("span", { style: "font-size:11px;color:var(--text-dim);" }, t.first.slice(0, 10) + " → " + t.last.slice(0, 10))]));
          var ul = el("ul", { style: "margin:6px 0 0 18px;padding:0;font-size:12px;" });
          t.docs.forEach(function (d) {
            ul.appendChild(el("li", { style: "margin:2px 0;" }, null, [
              el("span", { style: "color:" + (d.integrated ? "var(--accent-green)" : "var(--accent-red)") + ";" }, d.integrated ? "● " : "○ "),
              el("span", null, d.title + "  "), el("span", { style: "color:var(--text-dim);font-size:10px;" }, d.mtime.slice(0, 10) + " · " + d.status + (d.open_items ? " · owes " + d.open_items : "") + "  "),
              copyBtn(d.path, "path")]));
          });
          c.appendChild(ul);
          if (t.questions.length) {
            var det = el("details", { style: "margin-top:4px;font-size:12px;" }, null, [el("summary", { style: "cursor:pointer;color:var(--accent-cyan);" }, "questions you asked on this topic (" + t.questions.length + ")")]);
            var qu = el("ul", { style: "margin:4px 0 0 18px;padding:0;" });
            t.questions.forEach(function (q) { qu.appendChild(el("li", { style: "margin:2px 0;" }, (q.ts || "").slice(0, 10) + " " + (q.surface || "") + (q.missed ? " [possibly missed] " : " ") + q.text.slice(0, 260))); });
            det.appendChild(qu); c.appendChild(det);
          }
          list.appendChild(c);
        });
      });
    }

    function renderOwed() {
      list.textContent = ""; pager.textContent = ""; info.textContent = "Loading…";
      var q = new URLSearchParams(); if (fText.value) q.set("text", fText.value); if (fArea.value) q.set("area", fArea.value);
      return api("/api/loose/open_items?" + q.toString()).then(function (r) {
        info.textContent = r.total + " items listed under the documents' own 'still needs checking / FETCH LIST / OPEN QUESTIONS / TODO / next steps' headings (newest documents first)";
        var groups = {};
        r.items.forEach(function (it) { (groups[it.doc_id] = groups[it.doc_id] || { title: it.title, path: it.path, mtime: it.mtime, items: [] }).items.push(it); });
        Object.keys(groups).forEach(function (k) {
          var g = groups[k];
          var c = el("div", { style: CARD }, null, [el("div", { style: "display:flex;gap:8px;align-items:baseline;" }, null, [
            el("span", { style: "font-weight:600;font-size:13px;" }, g.title), el("span", { style: "font-size:11px;color:var(--text-dim);" }, g.mtime.slice(0, 10)), copyBtn(g.path, "copy path")])]);
          var ul = el("ul", { style: "margin:4px 0 0 18px;padding:0;font-size:12px;" });
          g.items.forEach(function (it) { ul.appendChild(el("li", { style: "margin:2px 0;" }, null, [el("span", { style: "color:var(--text-dim);font-size:10px;" }, "[" + it.section + "] "), document.createTextNode(it.text)])); });
          c.appendChild(ul); list.appendChild(c);
        });
      });
    }

    function render() {
      setTabs();
      var p;
      if (view === "top") {
        setBar([fText, fArea, fMark, fSince]);
        var params = { kind: "SUBJECT", signal: "not_integrated", sort: "score" };
        if (fText.value) params.text = fText.value; if (fArea.value) params.area = fArea.value;
        if (fMark.value) params.mark = fMark.value; if (fSince.value) params.changed_since = fSince.value;
        p = renderDocs(params);
      } else if (view === "threads") { setBar([fText]); p = renderThreads(); }
      else if (view === "owed") { setBar([fText, fArea]); p = renderOwed(); }
      else {
        setBar([fText, fArea, fKind, fSignal, fMark, fSince, fSort]);
        var a = { sort: fSort.value };
        [["text", fText], ["area", fArea], ["kind", fKind], ["signal", fSignal], ["mark", fMark], ["changed_since", fSince]].forEach(function (x) { if (x[1].value) a[x[0]] = x[1].value; });
        p = renderDocs(a);
      }
      p.catch(function (e) { info.textContent = "Could not load: " + e; });
    }

    bApply.onclick = function () { state.offset = 0; render(); };
    fText.addEventListener("keydown", function (e) { if (e.key === "Enter") { state.offset = 0; render(); } });
    bRebuild.onclick = function () {
      bRebuild.disabled = true; bRebuild.textContent = "Rescanning…";
      api("/api/loose/rebuild", { method: "POST" }).then(function (r) { bRebuild.textContent = "Rescan (" + r.n_docs + " docs, " + r.seconds + " s)"; return loadSummary(); })
        .then(render).catch(function (e) { alert(e); }).finally(function () { bRebuild.disabled = false; });
    };
    bExport.onclick = function () {
      fetch("/api/loose/export.md").then(function (r) { return r.text(); }).then(function (t) {
        var a = el("a", { href: URL.createObjectURL(new Blob([t], { type: "text/markdown" })), download: "loose_ends.md" }); a.click(); });
    };
    loadSummary().then(render).catch(function (e) { info.textContent = "Could not load the register: " + e; });
  }

  window.JarvisModules["loose"] = { load: load };
})();
