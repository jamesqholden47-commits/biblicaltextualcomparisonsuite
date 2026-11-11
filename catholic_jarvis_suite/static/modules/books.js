/* Volumes tab (module id "books"): the Bookbinder. Claude GUI, Opus 5.5, 2026-10-06.
 * Plan -> approve -> brief -> draft -> check -> judge -> final -> assemble, one chapter at a time.
 * Every state shown here is read from files on disk by the server. All text goes in via textContent. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

  var INPUT = "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:4px;padding:5px 8px;font-size:12px;";
  var BTN = "background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);border-radius:4px;padding:3px 9px;font-size:11px;cursor:pointer;";
  var GOLD = BTN + "color:var(--accent-gold);border-color:var(--accent-gold);";
  var CARD = "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px 12px;margin-bottom:8px;";
  var STATE_COLOR = { proposed: "var(--text-dim)", approved: "var(--accent-cyan)", briefed: "var(--accent-blue)",
    drafting: "var(--accent-gold)", drafted: "var(--accent-gold)", checked: "var(--accent-green)", judged: "var(--accent-green)", final: "var(--accent-green)" };
  var STATES = ["proposed", "approved", "briefed", "drafting", "drafted", "checked", "judged", "final"];
  var NEXT_STEP = { proposed: "review the sources, then Approve (freezes them)", approved: "write the brief",
    briefed: "launch the brief (copy the prompt into Claude or Antigravity)", drafting: "the draft is partial: launch the same brief again to continue it",
    drafted: "run the checks", checked: "Opus judge read (JUDGE.md in the chapter folder), then mark final",
    judged: "mark final", final: "done: its sources are marked merged in Loose Ends" };

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
    return el("span", { style: "display:inline-block;font-size:10px;padding:1px 6px;margin-right:4px;border-radius:3px;border:1px solid " + color + ";color:" + color + ";", title: title || "" }, text);
  }
  function words(n) { return n >= 1e6 ? (n / 1e6).toFixed(1) + "M" : n >= 1e3 ? Math.round(n / 1e3) + "k" : String(n || 0); }
  function api(url, opts) {
    return fetch(url, opts).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok) throw new Error((j && j.detail) || (r.status + " " + url)); return j; });
    });
  }
  function post(url, body) { return api(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) }); }
  function copy(text, btn, label) {
    if (navigator.clipboard) navigator.clipboard.writeText(text);
    btn.textContent = "copied"; setTimeout(function () { btn.textContent = label; }, 1000);
  }
  function openReader(path) { if (window.JarvisOpen) window.JarvisOpen("reader", { path: path }); }
  function progress(states, total) {
    var bar = el("div", { style: "display:flex;height:8px;border-radius:4px;overflow:hidden;background:var(--bg-panel);margin:6px 0;" });
    STATES.forEach(function (s) {
      var n = states[s] || 0; if (!n) return;
      bar.appendChild(el("div", { style: "width:" + (100 * n / total) + "%;background:" + STATE_COLOR[s] + ";", title: s + ": " + n }));
    });
    return bar;
  }

  function load(root) {
    root.textContent = "";
    root.style.cssText = "padding:16px;color:var(--text-main);";
    var head = el("div", { style: "display:flex;align-items:baseline;gap:12px;margin-bottom:6px;flex-wrap:wrap;" }, null, [
      el("h2", { style: "margin:0;font-size:16px;color:var(--accent-gold);" }, "Volumes"),
      el("span", { style: "font-size:11px;color:var(--text-dim);" }, "your loose files, planned into volumes and synthesised one checked chapter at a time")]);
    var nav = el("div", { style: "display:flex;gap:6px;margin:8px 0;flex-wrap:wrap;" });
    var body = el("div");
    root.appendChild(head); root.appendChild(nav); root.appendChild(body);
    var crumbs = [];

    function go(view, arg, label) { crumbs.push({ view: view, arg: arg, label: label }); render(); }
    function back(i) { crumbs = crumbs.slice(0, i + 1); render(); }
    function setNav() {
      nav.textContent = "";
      crumbs.forEach(function (c, i) {
        nav.appendChild(el("button", { style: i === crumbs.length - 1 ? GOLD : BTN, onclick: function () { back(i); } }, c.label));
      });
    }
    function busy(msg) { body.textContent = ""; body.appendChild(el("div", { style: "color:var(--text-muted);font-size:12px;" }, msg)); }
    function fail(e) { body.appendChild(el("div", { style: "color:var(--accent-red);font-size:12px;margin-top:8px;" }, String(e))); }

    // ---------------------------------------------------------------- overview
    function overview() {
      busy("Loading the plan…");
      Promise.all([api("/api/books/summary"), api("/api/books/next?n=6")]).then(function (r) {
        var s = r[0], nx = r[1];
        body.textContent = "";
        var stats = el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px;" });
        function stat(label, v, color, onclick) {
          stats.appendChild(el("div", { style: CARD + "margin:0;padding:6px 10px;min-width:120px;" + (onclick ? "cursor:pointer;" : ""), onclick: onclick }, null, [
            el("div", { style: "font-size:18px;font-weight:600;color:" + (color || "var(--text-main)") + ";" }, String(v)),
            el("div", { style: "font-size:10px;color:var(--text-dim);" }, label)]));
        }
        stat("sources in the pool", s.pool.total.toLocaleString());
        stat("AI-made documents", s.pool.ai.toLocaleString());
        stat("Obsidian vault notes", s.pool.vault.toLocaleString());
        stat("already inside a book", s.pool.already_in_books, "var(--accent-green)");
        stat("waiting in Unsorted", s.pool.unsorted.toLocaleString(), "var(--accent-red)", function () { go("unsorted", null, "Unsorted"); });
        if (s.pool.oversized) stat("oversized compilations held back (" + words(s.pool.oversized_words) + " words)", s.pool.oversized, "var(--accent-red)", function () {
          if (!confirm(s.pool.oversized + " files of over 60,000 words are held back because no synthesis job can take them whole.\n\nSplit them now? Each is cut at its own headings into verbatim parts of about 15,000 words (nothing rewritten, proved lossless by checksum) under 10_VOLUMES\\_split_sources, and the parts join the pool. The originals are not touched.")) return;
          busy("Splitting and re-planning…");
          post("/api/books/split_oversized").then(function (r) { alert(r.split + " files split; all verified lossless: " + r.all_verified); overview(); }).catch(fail);
        });
        stat("chapters planned", s.chapters.toLocaleString());
        stat("source words", words(s.source_words));
        stat("synthesised so far", s.percent_synthesised + "%", "var(--accent-gold)");
        body.appendChild(stats);
        var sk = s.pool.vault_skipped || {};
        body.appendChild(el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:8px;" },
          "Left out of the pool on purpose: " + Object.keys(sk).map(function (k) { return sk[k].toLocaleString() + " " + k; }).join(", ") +
          ". Plan built " + s.built_at + " in " + s.seconds + " s."));

        var tools = el("div", { style: "display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;" });
        var bRe = el("button", { style: GOLD, title: "Recompute the proposal from the current files and your edits. Approved chapters never change." }, "Re-plan");
        bRe.onclick = function () { bRe.disabled = true; bRe.textContent = "Re-planning… (about 30 s)"; post("/api/books/replan").then(overview).catch(function (e) { alert(e); bRe.disabled = false; bRe.textContent = "Re-plan"; }); };
        var bAcc = el("button", { style: BTN, title: "Place every unsorted source whose best volume scores 4+ and clearly leads (you can move any back)" }, "Accept clear suggestions");
        bAcc.onclick = function () { post("/api/books/accept_suggestions?min_score=4").then(function (r) { alert(r.moved + " sources placed. Re-plan to see them in chapters."); }).catch(alert); };
        tools.appendChild(bRe); tools.appendChild(bAcc);
        tools.appendChild(el("button", { style: BTN, onclick: function () { go("books", null, "Existing books"); } }, "Existing books"));
        body.appendChild(tools);

        if (nx.items.length) {
          var nc = el("div", { style: CARD + "border-color:var(--accent-gold);" }, null, [el("div", { style: "font-weight:600;font-size:13px;color:var(--accent-gold);margin-bottom:4px;" }, "Next up")]);
          nx.items.forEach(function (it) {
            nc.appendChild(el("div", { style: "font-size:12px;margin:3px 0;cursor:pointer;", onclick: function () { go("chapter", it.chapter, it.title.slice(0, 30)); } }, null, [
              chip(it.state, STATE_COLOR[it.state]), el("span", { style: "color:var(--text-main);" }, it.title + " "),
              el("span", { style: "color:var(--text-dim);font-size:11px;" }, "(" + it.volume + ", " + it.sources + " sources, " + words(it.words) + " words) → " + it.action)]));
          });
          body.appendChild(nc);
        }
        s.volumes.forEach(function (v) {
          var c = el("div", { style: CARD + "cursor:pointer;", onclick: function () { go("volume", v.id, v.id); } }, null, [
            el("div", { style: "display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;" }, null, [
              el("span", { style: "font-weight:600;font-size:13px;" }, v.id + "  " + v.title),
              chip(v.chapters + " chapters", "var(--text-muted)"), chip(v.n_sources.toLocaleString() + " sources", "var(--text-muted)"),
              chip(words(v.words) + " words", "var(--text-muted)")]),
            progress(v.states, Math.max(1, v.chapters)),
            el("div", { style: "font-size:10px;color:var(--text-dim);" }, STATES.filter(function (st) { return v.states[st]; }).map(function (st) { return st + " " + v.states[st]; }).join(" · "))]);
          body.appendChild(c);
        });
      }).catch(function (e) { body.textContent = ""; fail("No plan yet or it failed to load: " + e + ". Press Re-plan.");
        var b = el("button", { style: GOLD }, "Re-plan"); b.onclick = function () { b.textContent = "Re-planning… (first run reads every opening: several minutes)"; post("/api/books/replan").then(overview).catch(fail); }; body.appendChild(b); });
    }

    // ---------------------------------------------------------------- volume
    function volume(vid) {
      busy("Loading volume…");
      api("/api/books/volume/" + encodeURIComponent(vid)).then(function (v) {
        body.textContent = "";
        var t = el("div", { style: "display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;margin-bottom:4px;" }, null, [
          el("span", { style: "font-size:15px;font-weight:600;color:var(--accent-gold);" }, v.title)]);
        var ren = el("button", { style: BTN }, "rename"); ren.onclick = function () { var n = prompt("Volume title", v.title); if (n) post("/api/books/rename", { kind: "volume", id: v.id, title: n }).then(function () { alert("Renamed. Re-plan to apply."); }); };
        var asm = el("button", { style: GOLD, title: "Rebuild the volume file from its drafted chapters, with contents and a source list" }, "Assemble volume");
        asm.onclick = function () { post("/api/books/volume/" + v.id + "/assemble").then(function (r) { alert(r.chapters_included + " chapter(s) assembled into\n" + r.volume); openReader(r.volume); }).catch(alert); };
        t.appendChild(ren); t.appendChild(asm);
        body.appendChild(t);
        body.appendChild(el("div", { style: "font-size:12px;color:var(--text-muted);margin-bottom:8px;" }, v.purpose + "  (" + v.chapters.length + " chapters, " + v.n_sources.toLocaleString() + " sources, " + words(v.words) + " source words)"));
        var f = el("input", { type: "text", placeholder: "filter chapters", style: INPUT + "min-width:220px;margin-bottom:8px;" });
        var st = el("select", { style: INPUT + "margin-left:6px;" }, null, [el("option", { value: "" }, "any state")].concat(STATES.map(function (s) { return el("option", { value: s }, s); })));
        body.appendChild(f); body.appendChild(st);
        var list = el("div"); body.appendChild(list);
        function paint() {
          list.textContent = "";
          var q = f.value.toLowerCase();
          v.chapters.filter(function (c) { return (!q || c.title.toLowerCase().indexOf(q) >= 0) && (!st.value || c.state === st.value); }).slice(0, 300).forEach(function (c) {
            list.appendChild(el("div", { style: CARD + "padding:7px 10px;cursor:pointer;", onclick: function () { go("chapter", c.id, c.title.slice(0, 30)); } }, null, [
              chip(c.state, STATE_COLOR[c.state]), el("span", { style: "font-size:13px;" }, c.title + "  "),
              el("span", { style: "font-size:11px;color:var(--text-dim);" }, c.n_sources + " sources · " + words(c.words) + " words · " +
                Object.keys(c.origins || {}).map(function (o) { return c.origins[o] + " " + o; }).join(", ") + (c.draft_words ? " · draft " + words(c.draft_words) + " words" : ""))]));
          });
        }
        f.oninput = paint; st.onchange = paint; paint();
      }).catch(fail);
    }

    // ---------------------------------------------------------------- chapter
    function chapter(cid) {
      busy("Loading chapter…");
      api("/api/books/chapter/" + encodeURIComponent(cid)).then(function (r) {
        var c = r.chapter;
        body.textContent = "";
        body.appendChild(el("div", { style: "display:flex;gap:8px;align-items:baseline;flex-wrap:wrap;" }, null, [
          el("span", { style: "font-size:15px;font-weight:600;" }, c.title), chip(c.state, STATE_COLOR[c.state]),
          el("span", { style: "font-size:11px;color:var(--text-dim);" }, r.volume.title + " · " + c.n_sources + " sources · " + words(c.words) + " source words")]));
        body.appendChild(el("div", { style: "font-size:12px;color:var(--accent-gold);margin:6px 0;" }, "Next step: " + NEXT_STEP[c.state]));
        var acts = el("div", { style: "display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;" });
        function act(label, style, fn, title) { var b = el("button", { style: style, title: title || "" }, label); b.onclick = function () { b.disabled = true; fn(b).catch(function (e) { alert(e); }).finally(function () { b.disabled = false; }); }; acts.appendChild(b); return b; }
        act("Rename", BTN, function () { var n = prompt("Chapter title", c.title); return n ? post("/api/books/rename", { kind: "chapter", id: c.id, title: n }).then(function () { chapter(cid); }) : Promise.resolve(); });
        if (c.state === "proposed") act("Approve (freeze sources)", GOLD, function () { return post("/api/books/chapter/" + c.id + "/approve").then(function () { chapter(cid); }); },
          "Freezes this exact source list and creates the chapter folder in 10_VOLUMES. Re-planning never changes it afterwards.");
        if (c.state === "approved") act("Un-approve", BTN, function () { return post("/api/books/chapter/" + c.id + "/unapprove").then(function () { chapter(cid); }); });
        if (c.frozen) act(c.files && c.files["BRIEF.md"] ? "Rewrite brief" : "Write brief", c.state === "approved" ? GOLD : BTN, function () {
          return post("/api/books/chapter/" + c.id + "/brief" + (c.files && c.files["BRIEF.md"] ? "?overwrite=true" : "")).then(function (b) {
            var box = el("div", { style: CARD }, null, [el("div", { style: "font-size:12px;" }, "Brief written: " + b.brief + "  ·  gate " + b.gate),
              el("div", { style: "font-size:11px;color:var(--text-dim);margin:4px 0;" }, "Paste this into a Claude Code session (Sonnet 5.5) or Antigravity to have the chapter written:")]);
            var pre = el("textarea", { style: INPUT + "width:100%;height:110px;font-family:monospace;" }); pre.value = b.launch_prompt;
            var cb = el("button", { style: GOLD }, "Copy launch prompt"); cb.onclick = function () { copy(b.launch_prompt, cb, "Copy launch prompt"); };
            box.appendChild(pre); box.appendChild(cb); body.insertBefore(box, acts.nextSibling); });
        });
        if (c.files && c.files["CHAPTER.md"]) {
          act("Open draft in Reader", BTN, function () { openReader(c.files["CHAPTER.md"]); return Promise.resolve(); });
          act("Run checks", c.state === "drafted" ? GOLD : BTN, function () {
            return post("/api/books/chapter/" + c.id + "/check").then(function (k) {
              alert("Gate: " + k.gate + "\nSources checked: " + k.sources_checked + "\nData items: " + k.items + ", missing: " + k.missing +
                (k.worst ? "\nWorst source: " + k.worst.missing + "/" + k.worst.items + " missing\n" + k.worst.path : "") + "\n\nMissing includes machinery the brief removed on purpose; a judge read decides.");
              chapter(cid); });
          });
        }
        if (["checked", "judged"].indexOf(c.state) >= 0) act("Mark final", GOLD, function () { return post("/api/books/chapter/" + c.id + "/final", { final: true }).then(function () { chapter(cid); }); },
          "Marks every AI-made source of this chapter as merged in Loose Ends.");
        if (c.state === "final") act("Un-mark final", BTN, function () { return post("/api/books/chapter/" + c.id + "/final", { final: false }).then(function () { chapter(cid); }); });
        body.appendChild(acts);
        body.appendChild(el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:6px;" }, "Chapter folder: " + r.dir));
        if (c.check) body.appendChild(el("div", { style: CARD + "font-size:12px;" }, "Last check " + c.check.at + ": " + c.check.gate + " · " + c.check.sources_checked + " sources · " + c.check.items + " data items, " + c.check.missing + " missing"));

        body.appendChild(el("div", { style: "font-weight:600;font-size:13px;margin:10px 0 6px;" }, "Sources (" + r.sources.length + ")"));
        r.sources.forEach(function (s) {
          var row = el("div", { style: CARD + "padding:6px 10px;" }, null, [
            el("div", { style: "display:flex;gap:6px;align-items:baseline;flex-wrap:wrap;" }, null, [
              chip(s.origin, s.origin === "ai" ? "var(--accent-cyan)" : "var(--accent-blue)"), el("span", { style: "font-size:12px;" }, s.title + "  "),
              el("span", { style: "font-size:10px;color:var(--text-dim);" }, words(s.words) + " words · " + (s.mtime || "").slice(0, 10) + " · " + (s.folder || s.area || "") + (s.open_items ? " · owes " + s.open_items : ""))])]);
          var line = el("div", { style: "display:flex;gap:4px;margin-top:4px;flex-wrap:wrap;" });
          line.appendChild(el("button", { style: BTN, onclick: function () { openReader(s.path); } }, "read"));
          var cp = el("button", { style: BTN }, "copy path"); cp.onclick = function () { copy(s.path, cp, "copy path"); }; line.appendChild(cp);
          if (!c.frozen) {
            line.appendChild(el("button", { style: BTN, title: "Leave this source out of every volume", onclick: function () { post("/api/books/exclude", { source_ids: [s.id] }).then(function () { row.style.opacity = 0.4; }); } }, "exclude"));
            line.appendChild(el("button", { style: BTN, title: "Send back to Unsorted", onclick: function () { post("/api/books/move", { source_ids: [s.id], volume: "unsorted" }).then(function () { row.style.opacity = 0.4; }); } }, "unsort"));
          }
          row.appendChild(line); body.appendChild(row);
        });
      }).catch(fail);
    }

    // ---------------------------------------------------------------- unsorted
    function unsorted() {
      busy("Loading unsorted sources…");
      var f = el("input", { type: "text", placeholder: "words in title or folder", style: INPUT + "min-width:220px;" });
      var org = el("select", { style: INPUT }, null, [["", "any origin"], ["ai", "AI-made"], ["vault", "vault"]].map(function (o) { return el("option", { value: o[0] }, o[1]); }));
      var list = el("div");
      var state = { offset: 0 };
      function paint() {
        list.textContent = "";
        var q = new URLSearchParams({ limit: 60, offset: state.offset }); if (f.value) q.set("text", f.value); if (org.value) q.set("origin", org.value);
        api("/api/books/unsorted?" + q).then(function (r) {
          var vt = {}; r.volumes.forEach(function (v) { vt[v.id] = v.title; });
          list.appendChild(el("div", { style: "font-size:12px;color:var(--text-muted);margin:6px 0;" }, r.total.toLocaleString() + " sources have no clear volume. Click a suggestion to place one; re-plan to see placed sources in chapters."));
          r.items.forEach(function (s) {
            var row = el("div", { style: CARD + "padding:6px 10px;" }, null, [el("div", { style: "font-size:12px;" }, s.title),
              el("div", { style: "font-size:10px;color:var(--text-dim);" }, s.origin + " · " + words(s.words) + " words · " + (s.folder || s.area || ""))]);
            var line = el("div", { style: "display:flex;gap:4px;margin-top:4px;flex-wrap:wrap;align-items:center;" });
            Object.keys(s.candidates || {}).forEach(function (vid) {
              line.appendChild(el("button", { style: BTN, title: vt[vid] || vid, onclick: function () { post("/api/books/move", { source_ids: [s.id], volume: vid }).then(function () { row.style.opacity = 0.4; }); } }, "→ " + vid + " (" + s.candidates[vid] + ")"));
            });
            var sel = el("select", { style: INPUT + "padding:2px 4px;font-size:11px;" }, null, [el("option", { value: "" }, "other volume…")].concat(r.volumes.map(function (v) { return el("option", { value: v.id }, v.id + " " + v.title.slice(0, 40)); })));
            sel.onchange = function () { if (sel.value) post("/api/books/move", { source_ids: [s.id], volume: sel.value }).then(function () { row.style.opacity = 0.4; }); };
            line.appendChild(sel);
            line.appendChild(el("button", { style: BTN, onclick: function () { openReader(s.path); } }, "read"));
            line.appendChild(el("button", { style: BTN, onclick: function () { post("/api/books/exclude", { source_ids: [s.id] }).then(function () { row.style.opacity = 0.4; }); } }, "exclude"));
            row.appendChild(line); list.appendChild(row);
          });
          var pg = el("div", { style: "display:flex;gap:6px;margin:10px 0;font-size:12px;color:var(--text-muted);" });
          if (state.offset > 0) pg.appendChild(el("button", { style: BTN, onclick: function () { state.offset -= 60; paint(); } }, "‹ prev"));
          pg.appendChild(el("span", null, (state.offset + 1) + "–" + Math.min(r.total, state.offset + 60) + " of " + r.total));
          if (state.offset + 60 < r.total) pg.appendChild(el("button", { style: BTN, onclick: function () { state.offset += 60; paint(); } }, "next ›"));
          list.appendChild(pg);
        }).catch(fail);
      }
      body.textContent = "";
      var bar = el("div", { style: "display:flex;gap:6px;flex-wrap:wrap;" }, null, [f, org, el("button", { style: GOLD, onclick: function () { state.offset = 0; paint(); } }, "Apply")]);
      body.appendChild(bar); body.appendChild(list); paint();
    }

    function books() {
      busy("Loading…");
      api("/api/loose/summary").then(function (s) {
        body.textContent = "";
        body.appendChild(el("div", { style: "font-size:12px;color:var(--text-muted);margin-bottom:8px;" },
          "Books that already exist. A source whose sampled passages are found inside one of these counts as already in a book and is not re-synthesised. Assembled volumes join this list automatically."));
        (s.targets_found || []).forEach(function (p) {
          body.appendChild(el("div", { style: CARD }, null, [el("div", { style: "font-size:13px;" }, p.split("\\").pop()),
            el("div", { style: "font-size:11px;color:var(--text-dim);" }, p),
            el("button", { style: BTN + "margin-top:4px;", onclick: function () { openReader(p); } }, "read")]));
        });
      }).catch(fail);
    }

    function render() {
      setNav();
      var c = crumbs[crumbs.length - 1];
      if (c.view === "overview") overview();
      else if (c.view === "volume") volume(c.arg);
      else if (c.view === "chapter") chapter(c.arg);
      else if (c.view === "unsorted") unsorted();
      else if (c.view === "books") books();
    }
    crumbs = [{ view: "overview", label: "All volumes" }];
    render();
    window.addEventListener("jarvis:open-books", function (e) {
      var d = e.detail || {};
      if (d.chapter) { crumbs = [crumbs[0]]; go("chapter", d.chapter, "chapter"); }
    });
  }

  window.JarvisModules["books"] = { load: load };
})();
