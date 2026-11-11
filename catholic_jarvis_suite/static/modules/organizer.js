/* Organizer — everything on the drive, in buckets (Claude GUI, Opus 5.5, 2026-10-14).
   Views:
     Drive          every note, document, book, web page and code file in C:\Users\Elation, by bucket and shelf
     Duplicates     the same file (same fingerprint) in more than one place
     Book leads     books named in your Claude, Antigravity and Gemini conversations, and whether you own them
     Career leads   what you said about work, school, the military and your business, and what the AIs suggested
     Questions      questions you asked that look unanswered (from the Question Ledger)
     AI writing     every research file Antigravity or Claude wrote (the Catalog)
     Unfinished     requests that died on a limit or got no answer (the Catalog)
   Read-only: this tab sorts the list; it never moves, renames or deletes a file. */
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
  function q(s) { return encodeURIComponent(s); }
  function mb(n) { return n >= 1073741824 ? (n / 1073741824).toFixed(1) + " GB" : n >= 1048576 ? Math.round(n / 1048576) + " MB" : Math.max(1, Math.round(n / 1024)) + " KB"; }
  function num(n) { return (n || 0).toLocaleString(); }
  function day(t) { return typeof t === "number" ? new Date(t * 1000).toISOString().slice(0, 10) : (t || "").slice(0, 10); }
  function short(s, n) { s = (s || "").replace(/\s+/g, " ").trim(); return s.length > n ? s.slice(0, n) + "\u2026" : s; }
  function open(path) { if (path) window.JarvisOpen("files", { path: path }); }

  var VIEWS = [["drive", "Drive"], ["mine", "My folders"], ["dupes", "Duplicates"], ["books", "Book leads"], ["career", "Career leads"],
               ["questions", "Questions"], ["ai", "AI writing"], ["unfinished", "Unfinished"]];
  var PROGRAM = "Program files (hidden)";
  var BUCKET_WORDS = {
    "Dissertation project": "the History Proves Catholicism project: master, dossiers, drafts, sources, volumes",
    "Other projects": "your other projects: Mexico study, Scriptorium, CS2 codex, business sites and the rest",
    "Books": "every PDF and e-book outside the vault, shelved by subject from its title",
    "Loose notes": "notes and documents that belong to no project yet: Desktop, Downloads, Documents, NOTES",
    "Saved web pages": "web pages you saved from the browser",
    "Code elsewhere": "scripts that are not inside a project",
    "Vault & archives": "the Obsidian vault, older vault copies, the sorting clone, AI-history backups and old archives",
    "Program files (hidden)": "text and script files that belong to programs (SolidWorks, Tor Browser, add-ons, downloaded repos). Not yours; kept out of every other list"
  };
  var ORDER = ["Dissertation project", "Other projects", "Books", "Loose notes", "Saved web pages", "Code elsewhere", "Vault & archives", PROGRAM];
  var S = { view: "drive", bucket: null, shelf: null, kind: "", q: "", sort: "mtime", offset: 0, sum: null, root: null, folder: null, showHidden: false };
  var FOLDERS = {};

  // ── virtual filing: "File under…" and "Hide" on every file. Nothing on disk moves. ──
  function refreshFolders() { return get("/api/organizer/folders").then(function (d) { FOLDERS = d.folders || {}; return d; }); }
  function post(url, body) {
    return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
  }
  function fileActions(r, onDone) {
    var box = el("span", { class: "org-actions" });
    var form = null;
    function stop(e) { e.preventDefault(); e.stopPropagation(); }
    box.appendChild(el("a", { href: "#", on: { click: function (e) {
      stop(e);
      if (form) { form.remove(); form = null; return; }
      var listId = "org-dl-" + Math.random().toString(36).slice(2);
      var input = el("input", { type: "text", list: listId, value: r.placed || "", placeholder: "Folder, e.g. Career/Schools", on: { click: stop, keydown: function (ev) { if (ev.key === "Enter") save(ev); } } });
      function save(ev) {
        stop(ev);
        post("/api/organizer/place", { path: r.path, folder: input.value }).then(function (d) { FOLDERS = d.folders || FOLDERS; form.remove(); form = null; onDone(); });
      }
      form = el("span", { class: "org-file-form", on: { click: stop } }, [input,
        el("datalist", { id: listId }, Object.keys(FOLDERS).map(function (f) { return el("option", { value: f }); })),
        el("button", { class: "j-btn", on: { click: save } }, ["File it"]),
        r.placed ? el("button", { class: "j-btn ghost", on: { click: function (ev) { input.value = ""; save(ev); } } }, ["Take out"]) : null]);
      box.appendChild(form);
      input.focus();
    } } }, [r.placed ? "Refile" : "File under…"]));
    box.appendChild(el("a", { href: "#", on: { click: function (e) {
      stop(e);
      post("/api/organizer/place", { path: r.path, hidden: !r.hidden }).then(function () { onDone(); });
    } } }, [r.hidden ? "Unhide" : "Hide"]));
    return box;
  }

  function css() {
    if (document.getElementById("org-css")) return;
    var st = document.createElement("style");
    st.id = "org-css";
    st.textContent = [
      ".org-root{padding:var(--sp-4);font:var(--fs-md) var(--font-ui);color:var(--text-main)}",
      ".org-views{display:flex;flex-wrap:wrap;gap:var(--sp-1);margin-bottom:var(--sp-3);align-items:center}",
      ".org-views .j-btn.on{border-color:var(--accent-gold);color:var(--accent-gold)}",
      ".org-note{color:var(--text-muted);font-size:var(--fs-sm);margin-bottom:var(--sp-3)}",
      ".org-grid{display:grid;grid-template-columns:minmax(220px,300px) 1fr;gap:var(--sp-4)}",
      "@media (max-width:900px){.org-grid{grid-template-columns:1fr}}",
      ".org-side{display:flex;flex-direction:column;gap:var(--sp-2)}",
      ".org-bucket{border:1px solid var(--border);border-radius:var(--radius);background:var(--bg-panel);padding:var(--sp-2) var(--sp-3);cursor:pointer}",
      ".org-bucket.on{border-color:var(--accent-gold)}",
      ".org-bucket h4{margin:0;font:600 var(--fs-md) var(--font-ui)}",
      ".org-bucket .sub{color:var(--text-dim);font-size:var(--fs-xs)}",
      ".org-shelf{display:flex;justify-content:space-between;gap:8px;padding:3px 0 3px 10px;font-size:var(--fs-sm);color:var(--text-muted);cursor:pointer}",
      ".org-shelf:hover,.org-shelf.on{color:var(--accent-gold)}",
      ".org-bar{display:flex;flex-wrap:wrap;gap:var(--sp-2);margin-bottom:var(--sp-3)}",
      ".org-bar input,.org-bar select{background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:var(--radius);padding:6px 8px;font:var(--fs-sm) var(--font-ui)}",
      ".org-bar input{flex:1;min-width:200px}",
      ".org-row{border:1px solid var(--border);background:var(--bg-panel);border-radius:var(--radius);padding:6px var(--sp-3);margin-bottom:6px}",
      ".org-row.click{cursor:pointer}.org-row.click:hover{background:var(--bg-card-hover)}",
      ".org-name{font-weight:600;word-break:break-word}",
      ".org-meta{color:var(--text-dim);font-size:var(--fs-xs);margin-top:2px;word-break:break-all}",
      ".org-tag{display:inline-block;border:1px solid var(--border);border-radius:10px;padding:0 7px;margin-right:6px;font:var(--fs-xs) var(--font-mono);color:var(--text-muted)}",
      ".org-tag.ok{color:var(--ok);border-color:var(--ok)}.org-tag.warn{color:var(--warn);border-color:var(--warn)}",
      ".org-say{color:var(--text-muted);font-size:var(--fs-sm);margin-top:4px;white-space:pre-wrap}",
      ".org-pager{display:flex;gap:var(--sp-2);align-items:center;margin-top:var(--sp-3)}",
      ".org-actions{display:inline-flex;gap:10px;margin-left:8px;flex-wrap:wrap;align-items:center}",
      ".org-actions a{color:var(--accent-cyan);text-decoration:none}.org-actions a:hover{text-decoration:underline}",
      ".org-file-form{display:inline-flex;gap:6px;align-items:center}",
      ".org-file-form input{background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:var(--radius);padding:3px 6px;font:var(--fs-sm) var(--font-ui);min-width:200px}"
    ].join("\n");
    document.head.appendChild(st);
  }

  // ── Drive ───────────────────────────────────────────────────────────────────
  function drive(box) {
    refreshFolders().catch(function () {});
    get("/api/organizer/summary").then(function (sum) {
      S.sum = sum;
      box.textContent = "";
      box.appendChild(el("div", { class: "org-note", text: num(sum.files) + " files in " + ORDER.length + " buckets. " + num(sum.duplicate_groups) +
        " files have an identical copy somewhere else (" + mb(sum.duplicate_bytes) + " of extra copies; the sorting clone, a copy by design, is not counted). Scanned " + (sum.made || "").replace("T", " ") +
        ". Nothing here moves a file: it is a map of where things are." }));
      var grid = el("div", { class: "org-grid" });
      var side = el("div", { class: "org-side" });
      var main = el("div");
      grid.appendChild(side); grid.appendChild(main);
      box.appendChild(grid);
      ORDER.concat(Object.keys(sum.buckets).filter(function (b) { return ORDER.indexOf(b) < 0; })).forEach(function (b) {
        var info = sum.buckets[b];
        if (!info) return;
        var card = el("div", { class: "org-bucket" + (S.bucket === b ? " on" : "") }, [
          el("h4", { text: b }),
          el("div", { class: "sub", text: num(info.files) + " files \u00b7 " + mb(info.bytes) }),
          el("div", { class: "sub", text: BUCKET_WORDS[b] || "" })]);
        card.addEventListener("click", function (e) {
          if (e.target.classList.contains("org-shelf")) return;
          S.bucket = S.bucket === b && !S.shelf ? null : b; S.shelf = null; S.offset = 0; drive(box);
        });
        if (S.bucket === b) {
          Object.keys(info.shelves).sort(function (x, y) { return info.shelves[y].files - info.shelves[x].files; }).forEach(function (sh) {
            card.appendChild(el("div", { class: "org-shelf" + (S.shelf === sh ? " on" : ""), on: { click: function () { S.shelf = S.shelf === sh ? null : sh; S.offset = 0; drive(box); } } },
              [el("span", { text: sh }), el("span", { text: num(info.shelves[sh].files) })]));
          });
        }
        side.appendChild(card);
      });
      fileList(main);
    }).catch(function (e) { box.textContent = ""; box.appendChild(rebuildHint(e)); });
  }

  function fileList(main) {
    main.textContent = "";
    var bar = el("div", { class: "org-bar" }, [
      el("input", { type: "search", value: S.q, placeholder: "Search file names and titles" + (S.bucket ? " in " + S.bucket : " everywhere") + "\u2026",
        on: { input: function (e) { S.q = e.target.value; S.offset = 0; clearTimeout(fileList.t); fileList.t = setTimeout(function () { list(); }, 250); } } }),
      sel([["", "Every kind"], ["note", "Notes (md, txt)"], ["document", "Documents (Word, rtf)"], ["book", "Books"], ["web page", "Web pages"], ["code", "Code"], ["data", "Spreadsheets"]], "kind", list),
      sel([["mtime", "Newest first"], ["size", "Biggest first"], ["name", "By name"]], "sort", list)]);
    var out = el("div");
    main.appendChild(bar); main.appendChild(out);
    function list() {
      out.textContent = "";
      out.appendChild(el("div", { class: "fx-muted", text: "Loading\u2026" }));
      var mine = S.view === "mine";
      var url = "/api/organizer/files?limit=200&offset=" + S.offset + "&sort=" + S.sort + (S.showHidden ? "&hidden=1" : "") +
        (mine ? "&folder=" + q(S.folder || "") : (S.bucket ? "&bucket=" + q(S.bucket) : "") + (S.shelf ? "&shelf=" + q(S.shelf) : "")) +
        (S.kind ? "&kind=" + q(S.kind) : "") + (S.q ? "&q=" + q(S.q) : "");
      get(url).then(function (d) {
        out.textContent = "";
        out.appendChild(el("div", { class: "org-note", text: num(d.total) + " files" + (mine ? " filed under \u201c" + S.folder + "\u201d" : S.shelf ? " on \u201c" + S.shelf + "\u201d" : S.bucket ? " in " + S.bucket : "") +
          ". \u201cFile under\u2026\u201d puts a file in one of your own folders; \u201cHide\u201d takes it out of these lists. Neither moves the real file." }));
        d.rows.forEach(function (r) {
          var name = r.rel.split("\\").pop();
          out.appendChild(el("div", { class: "org-row click", title: r.path, on: { click: function () { open(r.path); } } }, [
            el("div", { class: "org-name", text: r.title && r.title !== name ? r.title : name }),
            el("div", { class: "org-meta" }, [
              el("span", { class: "org-tag", text: r.kind }),
              r.placed ? el("span", { class: "org-tag ok", text: "\u2192 " + r.placed }) : null,
              r.hidden ? el("span", { class: "org-tag warn", text: "hidden" }) : null,
              r.dupes ? el("span", { class: "org-tag warn", text: (r.dupes + 1) + " copies" }) : null,
              day(r.mtime) + " \u00b7 " + mb(r.bytes) + " \u00b7 " + r.rel, " ", fileActions(r, list)])
          ]));
        });
        pager(out, d.total, list);
      }).catch(function (e) { out.textContent = e.message; });
    }
    list();
  }

  // ── My folders (virtual) ───────────────────────────────────────────────────
  function mine(box) {
    box.textContent = "Loading…";
    refreshFolders().then(function (d) {
      box.textContent = "";
      var names = Object.keys(FOLDERS);
      box.appendChild(el("div", { class: "org-note", text: "Your own folders. They are virtual: a file you file here stays exactly where it is on the drive, " +
        "and these folders only exist in the suite (saved in data\\organizer_placements.json). Use “File under…” on any file in Drive to put it here; " +
        "write Career/Schools to make a folder inside a folder. " + (d.hidden ? num(d.hidden) + " files are hidden." : "") }));
      var grid = el("div", { class: "org-grid" });
      var side = el("div", { class: "org-side" });
      var main = el("div");
      grid.appendChild(side); grid.appendChild(main);
      box.appendChild(grid);
      if (!names.length) {
        side.appendChild(el("div", { class: "org-bucket" }, [el("h4", { text: "No folders yet" }),
          el("div", { class: "sub", text: "Go to Drive, find a file, and press “File under…”. Type a new folder name and it appears here." })]));
      }
      if (!S.folder || !(S.folder in FOLDERS)) S.folder = names[0] || null;
      names.forEach(function (n) {
        var depth = n.split("/").length - 1;
        side.appendChild(el("div", { class: "org-shelf" + (S.folder === n ? " on" : ""), style: "padding-left:" + (10 + depth * 14) + "px",
          on: { click: function () { S.folder = n; S.offset = 0; mine(box); } } }, [el("span", { text: n.split("/").pop() }), el("span", { text: num(FOLDERS[n]) })]));
      });
      side.appendChild(el("label", { class: "fx-muted" }, [
        el("input", { type: "checkbox", checked: S.showHidden || null, on: { change: function (e) { S.showHidden = e.target.checked; mine(box); } } }), " show hidden files"]));
      if (S.folder) fileList(main);
    }).catch(function (e) { box.textContent = e.message; });
  }

  function pager(out, total, again) {
    if (total <= 200) return;
    out.appendChild(el("div", { class: "org-pager" }, [
      el("button", { class: "j-btn", disabled: S.offset === 0 || null, on: { click: function () { S.offset = Math.max(0, S.offset - 200); again(); } } }, ["\u2039 Previous"]),
      el("span", { class: "fx-muted", text: (S.offset + 1) + "\u2013" + Math.min(total, S.offset + 200) + " of " + num(total) }),
      el("button", { class: "j-btn", disabled: S.offset + 200 >= total || null, on: { click: function () { S.offset += 200; again(); } } }, ["Next \u203a"])]));
  }

  function sel(opts, key, onChange) {
    return el("select", { on: { change: function (e) { S[key] = e.target.value; S.offset = 0; onChange(); } } },
      opts.map(function (o) { return el("option", { value: o[0], text: o[1], selected: S[key] === o[0] || null }); }));
  }

  // ── Duplicates ──────────────────────────────────────────────────────────────
  function dupes(box) {
    get("/api/organizer/duplicates?limit=400").then(function (d) {
      box.textContent = "";
      box.appendChild(el("div", { class: "org-note", text: num(d.groups) + " files have an identical copy somewhere else (not counting the sorting clone), biggest waste first. The copies are byte-for-byte " +
        "identical (same fingerprint). Nothing is deleted from here; when you decide, keep the copy outside \u201cVault & archives\u201d unless the vault is the home." }));
      d.rows.forEach(function (g) {
        var row = el("div", { class: "org-row" }, [
          el("div", { class: "org-name", text: g.files[0].rel.split("\\").pop() }),
          el("div", { class: "org-meta", text: g.copies + " copies \u00b7 " + mb(g.bytes) + " each \u00b7 " + mb(g.wasted) + " extra" })]);
        g.files.forEach(function (f) {
          row.appendChild(el("div", { class: "org-meta" }, [
            el("a", { href: "#", on: { click: function (e) { e.preventDefault(); open(f.path); } } }, [f.rel]), "  \u00b7 " + f.bucket + " / " + f.shelf]));
        });
        box.appendChild(row);
      });
    }).catch(function (e) { box.textContent = ""; box.appendChild(rebuildHint(e)); });
  }

  // ── Book leads ──────────────────────────────────────────────────────────────
  var B = { owned: "0", q: "", min: "1", offset: 0, shelf: "", kind: "" };
  function books(box) {
    box.textContent = "";
    books.filtersAdded = false;
    var bar = el("div", { class: "org-bar" }, [
      el("input", { type: "search", value: B.q, placeholder: "Search titles and authors\u2026", on: { input: function (e) { B.q = e.target.value; B.offset = 0; clearTimeout(books.t); books.t = setTimeout(go, 250); } } }),
      bsel([["0", "Books you don't have"], ["1", "Books you already have"], ["", "All books mentioned"]], "owned"),
      bsel([["1", "Mentioned at least once"], ["2", "Mentioned 2+ times"], ["3", "Mentioned 3+ times"], ["5", "Mentioned 5+ times"]], "min")]);
    var out = el("div");
    box.appendChild(bar); box.appendChild(out);
    function bsel(opts, key) {
      return el("select", { on: { change: function (e) { B[key] = e.target.value; B.offset = 0; go(); } } },
        opts.map(function (o) { return el("option", { value: o[0], text: o[1], selected: B[key] === o[0] || null }); }));
    }
    function go() {
      out.textContent = "Loading\u2026";
      get("/api/organizer/leads/books?limit=200&offset=" + B.offset + "&min_mentions=" + B.min + (B.shelf ? "&shelf=" + q(B.shelf) : "") + (B.kind ? "&kind=" + q(B.kind) : "") + (B.owned !== "" ? "&owned=" + B.owned : "") + (B.q ? "&q=" + q(B.q) : ""))
        .then(function (d) {
          out.textContent = "";
          var read = d.read || {};
          if (d.checked && !books.filtersAdded) {
            books.filtersAdded = true;
            bar.appendChild(el("select", { on: { change: function (e) { B.shelf = e.target.value; B.offset = 0; go(); } } },
              [el("option", { value: "", text: "Every subject" })].concat(Object.keys(d.shelves).sort().map(function (s) { return el("option", { value: s, text: s + " (" + d.shelves[s] + ")" }); }))));
            bar.appendChild(el("select", { on: { change: function (e) { B.kind = e.target.value; B.offset = 0; go(); } } },
              [el("option", { value: "", text: "Every kind" })].concat(Object.keys(d.kinds).sort().map(function (s) { return el("option", { value: s, text: s + " (" + d.kinds[s] + ")" }); }))));
          }
          out.appendChild(el("div", { class: "org-note", text: (d.checked
            ? num(d.all) + " works named in your conversations, cleaned by an AI pass (" + num(d.raw_all) + " raw matches: false titles dropped, spellings of the same book merged, each put on a subject shelf). "
            : num(d.all) + " book titles named in your conversations (raw matches, not yet cleaned). ") +
            "Read from " + num((read.Claude || 0) + (read.Antigravity || 0) + (read.Gemini || 0)) + " messages (Claude " + num(read.Claude) + ", Antigravity " + num(read.Antigravity) +
            ", Gemini " + num(read.Gemini) + "). " + num(d.owned) + " match a book file on your drive. Found by citation shape, so books named loosely in passing are missed. Most-mentioned first." }));
          d.rows.forEach(function (b) {
            out.appendChild(el("div", { class: "org-row" + (b.owned ? " click" : ""), on: b.owned ? { click: function () { open(b.owned); } } : null }, [
              el("div", { class: "org-name", text: b.title }),
              el("div", { class: "org-meta" }, [
                b.owned ? el("span", { class: "org-tag ok", text: "on your drive" }) : el("span", { class: "org-tag warn", text: "not on your drive" }),
                b.kind ? el("span", { class: "org-tag", text: b.kind }) : null,
                b.shelf ? el("span", { class: "org-tag", text: b.shelf }) : null,
                (b.author ? b.author + " \u00b7 " : "") + (b.detail ? b.detail + " \u00b7 " : "") + "named " + b.mentions + "\u00d7 in " + b.sources.join(", ") +
                  " \u00b7 first " + day(b.first.ts) + " (" + b.first.src + ")"]),
              el("div", { class: "org-say", text: short(b.first.snippet, 380) })]));
          });
          pagerB(out, d.total);
        }).catch(function (e) { out.textContent = ""; out.appendChild(rebuildHint(e)); });
    }
    function pagerB(o, total) {
      if (total <= 200) return;
      o.appendChild(el("div", { class: "org-pager" }, [
        el("button", { class: "j-btn", disabled: B.offset === 0 || null, on: { click: function () { B.offset = Math.max(0, B.offset - 200); go(); } } }, ["\u2039 Previous"]),
        el("span", { class: "fx-muted", text: (B.offset + 1) + "\u2013" + Math.min(total, B.offset + 200) + " of " + num(total) }),
        el("button", { class: "j-btn", disabled: B.offset + 200 >= total || null, on: { click: function () { B.offset += 200; go(); } } }, ["Next \u203a"])]));
    }
    go();
  }

  // ── Career leads ────────────────────────────────────────────────────────────
  var Cr = { theme: "", kind: "", q: "", raw: false, type: "" };
  function career(box) {
    box.textContent = "Loading\u2026";
    get("/api/organizer/leads/career?limit=600" + (Cr.raw ? "&raw=1" : "") + (Cr.type ? "&type=" + q(Cr.type) : "") +
        (Cr.theme ? "&theme=" + q(Cr.theme) : "") + (Cr.kind ? "&kind=" + q(Cr.kind) : "") + (Cr.q ? "&q=" + q(Cr.q) : ""))
      .then(function (d) {
        box.textContent = "";
        if (d.checked) return careerChecked(box, d);
        var themes = Object.keys(d.themes).sort(function (a, b) { return d.themes[b] - d.themes[a]; });
        box.appendChild(el("div", { class: "org-bar" }, [
          el("input", { type: "search", value: Cr.q, placeholder: "Search\u2026", on: { change: function (e) { Cr.q = e.target.value; career(box); } } }),
          el("select", { on: { change: function (e) { Cr.theme = e.target.value; career(box); } } },
            [el("option", { value: "", text: "Every theme" })].concat(themes.map(function (t) { return el("option", { value: t, text: t + " (" + d.themes[t] + ")", selected: Cr.theme === t || null }); }))),
          el("select", { on: { change: function (e) { Cr.kind = e.target.value; career(box); } } }, [["", "Everything"], ["you said", "What you said"], ["AI suggested", "What the AI suggested"], ["saved web page", "Saved web pages"]]
            .map(function (o) { return el("option", { value: o[0], text: o[1], selected: Cr.kind === o[0] || null }); })),
          Cr.raw ? el("button", { class: "j-btn ghost", on: { click: function () { Cr.raw = false; career(box); } } }, ["‹ Back to the checked leads"]) : null]));
        box.appendChild(el("div", { class: "org-note", text: num(d.total) + " items, newest first: things you said about work, school, the military and your business, the concrete programmes or benefits an AI named in reply, and career-related pages you saved. Picked by keywords, so read it as a pile to sort, not a finished list." }));
        d.rows.forEach(function (c) {
          box.appendChild(el("div", { class: "org-row" + (c.path ? " click" : ""), on: c.path ? { click: function () { window.open("/api/files/raw?path=" + q(c.path), "_blank"); } } : null }, [
            el("div", { class: "org-meta" }, [el("span", { class: "org-tag", text: c.kind })].concat(c.themes.map(function (t) { return el("span", { class: "org-tag", text: t }); }),
              [day(c.ts) + " \u00b7 " + c.src + (c.sid ? " " + c.sid : "")])),
            el("div", { class: "org-say", text: short(c.text, 700) }),
            c.answering ? el("div", { class: "org-meta", text: "in reply to: " + short(c.answering, 200) }) : null]));
        });
      }).catch(function (e) { box.textContent = ""; box.appendChild(rebuildHint(e)); });
  }

  function careerChecked(box, d) {
    var types = Object.keys(d.types).sort(function (a, b) { return d.types[b] - d.types[a]; });
    box.appendChild(el("div", { class: "org-bar" }, [
      el("input", { type: "search", value: Cr.q, placeholder: "Search the leads…", on: { change: function (e) { Cr.q = e.target.value; career(box); } } }),
      el("select", { on: { change: function (e) { Cr.type = e.target.value; career(box); } } },
        [el("option", { value: "", text: "Every kind of lead" })].concat(types.map(function (t) { return el("option", { value: t, text: t + " (" + d.types[t] + ")", selected: Cr.type === t || null }); }))),
      el("button", { class: "j-btn ghost", on: { click: function () { Cr.raw = true; career(box); } } }, ["Show the raw keyword pile (" + num(d.pile) + ")"])]));
    box.appendChild(el("div", { class: "org-note", text: num(d.total) + " career leads from your conversations, newest first. An AI read the keyword matches and kept only what is about your own work, " +
      "school, benefits and business; every lead below carries a sentence that a script found word for word in your messages (" + num(d.rejected) +
      " leads were thrown out because their quote didn't match). Nothing here is checked against the outside world: a programme, price or deadline is what was said at the time." }));
    d.rows.forEach(function (c) {
      box.appendChild(el("div", { class: "org-row" }, [
        el("div", { class: "org-name", text: c.lead }),
        el("div", { class: "org-meta" }, [el("span", { class: "org-tag", text: c.type }), el("span", { class: "org-tag", text: c.who === "AI" ? "an AI suggested it" : "you said it" }),
          (c.dates.length ? c.dates[0] + (c.dates.length > 1 ? " → " + c.dates[c.dates.length - 1] + " (" + c.dates.length + " times)" : "") : "") + " · " + c.sources.join(", ")]),
        el("div", { class: "org-say", text: c.detail }),
        el("div", { class: "org-meta", text: "“" + short(c.quote, 300) + "”" })]));
    });
  }

  // ── Questions (Question Ledger) ─────────────────────────────────────────────
  function questions(box) {
    box.textContent = "Loading\u2026";
    Promise.all([get("/api/ledger/stats"), get("/api/ledger/questions?missed=1&limit=300")]).then(function (res) {
      var st = res[0], d = res[1];
      box.textContent = "";
      box.appendChild(el("div", { class: "org-note", text: "Questions you asked an AI where the reply that followed doesn't look like an answer (the Question Ledger's \u201cmissed\u201d list, " +
        num(d.total) + " of them). Mark them in the Questions tab under System; this view is a shortcut." }));
      box.appendChild(el("div", { class: "org-bar" }, [el("button", { class: "j-btn", on: { click: function () { window.JarvisOpen("ledger"); } } }, ["Open the Question Ledger \u203a"])]));
      (d.items || []).forEach(function (x) {
        box.appendChild(el("div", { class: "org-row" }, [
          el("div", { class: "org-meta", text: day(x.ts || x.date) + " \u00b7 " + ({ CL: "Claude", AG: "Antigravity" }[x.surface] || x.surface || "") +
            (x.no_reply === true || x.no_reply === "True" ? " \u00b7 got no reply" : "") }),
          el("div", { class: "org-say", text: short(x.text || "", 600) }),
          x.reply ? el("div", { class: "org-meta", text: "what came back: " + short(x.reply, 220) }) : null]));
      });
      if (st && st.n_ledger) box.appendChild(el("div", { class: "fx-muted", text: num(st.n_ledger) + " questions in the ledger altogether." }));
    }).catch(function (e) { box.textContent = "Couldn't load the Question Ledger: " + e.message; });
  }

  // ── AI writing / Unfinished (the Catalog module) ────────────────────────────
  function catalog(box, view) {
    box.textContent = "Loading\u2026";
    function run() { box.textContent = ""; window.JarvisModules.catalog.load(box, { view: view }); }
    if (window.JarvisModules.catalog) return run();
    var s = document.createElement("script");
    s.src = "/static/modules/catalog.js?v=" + Date.now();
    s.onload = run;
    s.onerror = function () { box.textContent = "Couldn't load the catalog view."; };
    document.head.appendChild(s);
  }

  function rebuildHint(e) {
    return el("div", { class: "org-note" }, [e.message + " ", el("a", { href: "#", on: { click: function (ev) { ev.preventDefault(); rebuild(); } } }, ["Rebuild now"])]);
  }

  var rebuildBtn = null;
  function rebuild() {
    if (!rebuildBtn) return;
    rebuildBtn.disabled = true;
    fetch("/api/organizer/rebuild", { method: "POST" }).then(function () {
      var t = setInterval(function () {
        get("/api/organizer/rebuild").then(function (s) {
          rebuildBtn.textContent = s.running ? (s.step || "Working") + "\u2026" : (s.error ? "Rebuild failed" : "Rebuilt");
          if (s.error) rebuildBtn.title = s.error;
          if (!s.running) { clearInterval(t); rebuildBtn.disabled = false; draw(); }
        });
      }, 3000);
    });
  }

  function draw() {
    var root = S.root;
    root.textContent = "";
    rebuildBtn = el("button", { class: "j-btn", title: "Re-scan the drive and re-read every conversation (several minutes; runs once, nothing stays running)",
      on: { click: rebuild } }, ["Rebuild"]);
    root.appendChild(el("div", { class: "org-views" }, VIEWS.map(function (v) {
      return el("button", { class: "j-btn" + (S.view === v[0] ? " on" : ""), on: { click: function () { S.view = v[0]; draw(); } } }, [v[1]]);
    }).concat([el("span", { style: "flex:1" }), rebuildBtn])));
    var box = el("div");
    root.appendChild(box);
    ({ drive: drive, mine: mine, dupes: dupes, books: books, career: career, questions: questions,
       ai: function (b) { catalog(b, "files"); }, unfinished: function (b) { catalog(b, "hanging"); } })[S.view](box);
  }

  function load(root) {
    css();
    root.classList.add("org-root");
    S.root = root;
    draw();
  }

  window.JarvisModules.organizer = { load: load };
})();
