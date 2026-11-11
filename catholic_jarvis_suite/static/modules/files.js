/* Files — the suite's file and Markdown viewer (Phase 1, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).
   Left: find box, pins, recent files, folder tree over the configured roots.
   Middle: the file rendered for its type (Obsidian-style Markdown, text/code with line numbers, PDF, image,
           sandboxed HTML, audio/video, .docx text), a folder listing, or a side-by-side diff.
   Right: where the file is going (Volumes chapter, Loose Ends), drifted variants and exact copies, backlinks,
          and margin notes kept in the suite (never in the file).
   Read-only: nothing here can change a file. Styles live in jarvis.css (.fx-*). */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

  var S = { root: null, path: null, folder: null, data: null, state: { pins: [], recent: [] }, pendingOpen: null, api: null };

  window.addEventListener("jarvis:open-files", function (ev) {
    var d = (ev && ev.detail) || {};
    if (!d.path) return;
    if (S.api) S.api.open(String(d.path), d.part || 0); else S.pendingOpen = d;
  });

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "text") e.textContent = v;
      else if (k === "html") e.innerHTML = v;            // only ever server-rendered, escaped markup
      else if (k === "on") Object.keys(v).forEach(function (ev) { e.addEventListener(ev, v[ev]); });
      else e.setAttribute(k, v === true ? "" : v);
    });
    (kids || []).forEach(function (c) { if (c !== null && c !== undefined) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function api(url, opts) {
    return fetch(url, opts).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (j) {
        if (!r.ok) throw new Error(j.detail || ("HTTP " + r.status));
        return j;
      });
    });
  }
  function q(p) { return encodeURIComponent(p); }
  function kb(n) { return n < 1024 ? n + " B" : n < 1048576 ? Math.round(n / 1024) + " KB" : (n / 1048576).toFixed(1) + " MB"; }
  function base(p) { return String(p).split(/[\\/]/).pop(); }
  var ICON = { epub: "\u{1F4D7}", markdown:"\u{1F4DD}", text: "\u{1F4C4}", code: "⌨", html: "\u{1F310}", pdf: "\u{1F4D5}", image: "\u{1F5BC}",
               docx: "\u{1F4C3}", audio: "\u{1F3B5}", video: "\u{1F3AC}", other: "\u{1F4E6}", dir: "\u{1F4C1}" };

  function load(root) {
    root.textContent = "";
    root.classList.add("fx-root");
    var find = el("input", { class: "fx-find", placeholder: "Find a file by name…", autocomplete: "off" });
    var side = el("div", { class: "fx-side" }, [find, el("div", { class: "fx-side-body" })]);
    var main = el("div", { class: "fx-main" }, [el("div", { class: "j-empty", text: "Pick a file on the left, or find one by name." })]);
    var info = el("div", { class: "fx-info" });
    root.appendChild(side); root.appendChild(main); root.appendChild(info);
    S.ui = { side: side.querySelector(".fx-side-body"), main: main, info: info, find: find };
    var t = null;
    find.addEventListener("input", function () { clearTimeout(t); t = setTimeout(runFind, 180); });
    find.addEventListener("keydown", function (e) { if (e.key === "Escape") { find.value = ""; renderSide(); } });
    api("/api/files/roots").then(function (d) {
      S.roots = d.roots; S.state = d.state;
      renderSide();
      S.api = { open: openFile };
      if (S.pendingOpen) { openFile(S.pendingOpen.path, S.pendingOpen.part || 0); S.pendingOpen = null; }
    }).catch(function (e) { S.ui.side.textContent = "Could not load roots: " + e.message; });
  }

  // ── left: pins, recents, tree ──────────────────────────────────────────────────
  var ROLES = [
    { id: "all", label: "All" },
    { id: "master", label: "Master" },
    { id: "subject", label: "Subject" },
    { id: "source", label: "Source" },
    { id: "draft", label: "Draft" },
    { id: "infra", label: "Infra" },
    { id: "archive", label: "Archive" }
  ];

  function roleBadges(item) {
    var out = [];
    if (item && item.role) {
      out.push(el("span", {
        class: "fx-badge fx-role-" + item.role,
        text: item.role_label || item.role.toUpperCase()
      }));
    }
    if (item && item.status_badge) {
      var sClass = item.status_badge === "IN BOOK" ? "fx-status-in-book" : "fx-status-loose";
      out.push(el("span", {
        class: "fx-status-badge " + sClass,
        text: item.status_badge
      }));
    }
    return out;
  }

  function applyRoleFilter() {
    if (!S.ui || !S.ui.side) return;
    if (S.roleFilter && S.roleFilter !== "all") {
      S.ui.side.setAttribute("data-role-filter", S.roleFilter);
    } else {
      S.ui.side.removeAttribute("data-role-filter");
    }
    var tbl = document.querySelector(".fx-table");
    if (tbl) {
      if (S.roleFilter && S.roleFilter !== "all") {
        tbl.setAttribute("data-role-filter", S.roleFilter);
      } else {
        tbl.removeAttribute("data-role-filter");
      }
    }
  }

  function renderSide() {
    var b = S.ui.side;
    b.textContent = "";
    S.roleFilter = S.roleFilter || "all";

    // Color/Role Filter & Legend Bar
    var filterBar = el("div", { class: "fx-filter-bar" });
    ROLES.forEach(function (r) {
      var chipClass = "fx-filter-chip" + (r.id === "all" ? " fx-chip-all" : " fx-role-" + r.id) + (S.roleFilter === r.id ? " active" : "");
      var chip = el("span", {
        class: chipClass,
        text: r.label,
        on: {
          click: function () {
            S.roleFilter = (S.roleFilter === r.id && r.id !== "all") ? "all" : r.id;
            applyRoleFilter();
            renderSide();
          }
        }
      });
      filterBar.appendChild(chip);
    });
    b.appendChild(filterBar);

    if (S.state.pins && S.state.pins.length) {
      b.appendChild(el("div", { class: "fx-sec", text: "Pinned" }));
      S.state.pins.forEach(function (p) {
        var pRole = p.role ? " fx-role-" + p.role : "";
        b.appendChild(el("div", {
          class: "fx-item" + pRole,
          title: p.path,
          on: { click: function () { p.dir ? openFolder(p.path) : openFile(p.path); } }
        }, [
          el("span", { class: "fx-ico", text: p.dir ? ICON.dir : "\u{1F4CC}" }),
          el("span", { class: "fx-name", text: p.name })
        ].concat(roleBadges(p))));
      });
    }
    if (S.state.recent && S.state.recent.length) {
      var rec = el("details", { class: "fx-recent" }, [el("summary", { class: "fx-sec", text: "Recent (" + S.state.recent.length + ")" })]);
      S.state.recent.forEach(function (r) {
        var rRole = r.role ? " fx-role-" + r.role : "";
        rec.appendChild(el("div", {
          class: "fx-item" + rRole,
          title: r.path + "\n" + r.at,
          on: { click: function () { openFile(r.path); } }
        }, [
          el("span", { class: "fx-ico", text: ICON[typeFromName(r.name)] || ICON.other }),
          el("span", { class: "fx-name", text: r.name })
        ].concat(roleBadges(r))));
      });
      b.appendChild(rec);
    }
    b.appendChild(el("div", { class: "fx-sec", text: "Folders" }));
    S.roots.forEach(function (r) {
      if (!r.exists) return;
      b.appendChild(treeNode({ name: r.label, path: r.path, role: r.role, role_label: r.role_label, status_badge: r.status_badge }, 0, true));
    });
    applyRoleFilter();
  }
  function typeFromName(n) {
    var ext = (n.match(/\.[^.]+$/) || [""])[0].toLowerCase();
    var map = { ".md": "markdown", ".pdf": "pdf", ".png": "image", ".jpg": "image", ".jpeg": "image", ".html": "html",
                ".txt": "text", ".json": "code", ".py": "code", ".docx": "docx", ".mp3": "audio" };
    return map[ext] || "other";
  }
  function treeNode(d, depth, isRoot) {
    var kids = el("div", { class: "fx-kids", hidden: true });
    var dRole = d.role ? " fx-role-" + d.role : "";
    var row = el("div", {
      class: "fx-item fx-dir" + (isRoot ? " fx-rootdir" : "") + dRole,
      title: d.path,
      style: "padding-left:" + (6 + depth * 14) + "px",
      on: { click: function () { toggle(); openFolder(d.path); } }
    }, [
      el("span", { class: "fx-caret", text: "▸" }),
      el("span", { class: "fx-ico", text: ICON.dir }),
      el("span", { class: "fx-name", text: d.name })
    ].concat(roleBadges(d)));
    var loaded = false;
    function toggle() {
      var open = kids.hidden;
      kids.hidden = !open;
      row.querySelector(".fx-caret").textContent = open ? "▾" : "▸";
      if (open && !loaded) {
        loaded = true;
        kids.appendChild(el("div", { class: "fx-muted", style: "padding-left:" + (20 + depth * 14) + "px", text: "…" }));
        api("/api/files/list?path=" + q(d.path)).then(function (L) {
          kids.textContent = "";
          L.dirs.forEach(function (x) { kids.appendChild(treeNode(x, depth + 1, false)); });
          var shown = L.files.slice(0, 400);
          shown.forEach(function (f) {
            var fRole = f.role ? " fx-role-" + f.role : "";
            kids.appendChild(el("div", {
              class: "fx-item fx-file" + fRole,
              title: f.name + "  ·  " + kb(f.size) + "  ·  " + f.mtime,
              "data-path": f.path,
              style: "padding-left:" + (20 + depth * 14) + "px",
              on: { click: function (e) { e.stopPropagation(); openFile(f.path); } }
            }, [
              el("span", { class: "fx-ico", text: ICON[f.type] || ICON.other }),
              el("span", { class: "fx-name", text: f.name })
            ].concat(roleBadges(f))));
          });
          if (L.files.length > shown.length || L.truncated)
            kids.appendChild(el("div", { class: "fx-muted", style: "padding-left:" + (20 + depth * 14) + "px",
                                         text: (L.n_files - shown.length) + " more files — see the folder view" }));
          markActive();
        }).catch(function (e) { kids.textContent = e.message; });
      }
    }
    var wrap = el("div", null, [row, kids]);
    return wrap;
  }
  function markActive() {
    document.querySelectorAll(".fx-file").forEach(function (n) { n.classList.toggle("active", n.getAttribute("data-path") === S.path); });
  }
  function runFind() {
    var v = S.ui.find.value.trim();
    if (!v) { renderSide(); return; }
    var b = S.ui.side;
    b.textContent = "Searching…";
    api("/api/files/find?q=" + q(v)).then(function (d) {
      b.textContent = "";
      b.appendChild(el("div", { class: "fx-sec", text: d.total + " file" + (d.total === 1 ? "" : "s") + " named “" + v + "”" + (d.total > d.files.length ? " (first " + d.files.length + ")" : "") }));
      d.files.forEach(function (f) {
        var fRole = f.role ? " fx-role-" + f.role : "";
        b.appendChild(el("div", {
          class: "fx-item fx-file" + fRole,
          title: f.path,
          "data-path": f.path,
          on: { click: function () { openFile(f.path); } }
        }, [
          el("span", { class: "fx-ico", text: ICON[f.type] || ICON.other }),
          el("span", { class: "fx-name" }, [f.name, el("span", { class: "fx-muted", text: "  " + f.root })])
        ].concat(roleBadges(f))));
      });
      markActive();
      applyRoleFilter();
    }).catch(function (e) { b.textContent = e.message; });
  }

  // ── middle: folder listing ─────────────────────────────────────────────────────
  function openFolder(path) {
    S.folder = path;
    var m = S.ui.main;
    m.textContent = "";
    m.appendChild(el("div", { class: "j-empty", text: "Loading…" }));
    api("/api/files/list?path=" + q(path)).then(function (L) {
      m.textContent = "";
      m.appendChild(crumbs(L.crumbs, null, [
        el("button", { class: "j-btn ghost", title: "Pin this folder", on: { click: function () { pin(L.path, true); } } }, ["\u{1F4CC} Pin"])
      ]));
      var tb = el("table", { class: "fx-table" });
      if (S.roleFilter && S.roleFilter !== "all") tb.setAttribute("data-role-filter", S.roleFilter);
      tb.appendChild(el("thead", null, [el("tr", null, [el("th", { text: "Name" }), el("th", { text: "Type" }), el("th", { text: "Size" }), el("th", { text: "Modified" })])]));
      var body = el("tbody");
      L.dirs.forEach(function (d) {
        var dRole = d.role ? " fx-role-" + d.role : "";
        body.appendChild(el("tr", { class: "fx-row" + dRole, on: { click: function () { openFolder(d.path); } } },
          [el("td", null, [ICON.dir + " ", d.name].concat(roleBadges(d))), el("td", { text: "folder" }), el("td"), el("td")]));
      });
      L.files.forEach(function (f) {
        var fRole = f.role ? " fx-role-" + f.role : "";
        body.appendChild(el("tr", { class: "fx-row" + fRole, on: { click: function () { openFile(f.path); } } },
          [el("td", null, [(ICON[f.type] || ICON.other) + " ", f.name].concat(roleBadges(f))), el("td", { text: f.type }), el("td", { text: kb(f.size) }), el("td", { text: f.mtime })]));
      });
      tb.appendChild(body);
      m.appendChild(el("div", { class: "fx-muted", style: "margin:6px 0", text: L.n_dirs + " folders · " + L.n_files + " files" + (L.truncated ? " (first 3,000 shown)" : "") }));
      m.appendChild(tb);
      S.ui.info.textContent = "";
    }).catch(function (e) { m.textContent = e.message; });
  }

  function crumbs(list, name, buttons) {
    var c = el("div", { class: "fx-crumbs" });
    (list || []).forEach(function (x, i) {
      if (i) c.appendChild(el("span", { class: "fx-muted", text: " › " }));
      c.appendChild(el("a", { href: "#", on: { click: function (e) { e.preventDefault(); openFolder(x.path); } } }, [x.name]));
    });
    if (name) { c.appendChild(el("span", { class: "fx-muted", text: " › " })); c.appendChild(el("strong", { text: name })); }
    var bar = el("div", { class: "fx-bar" }, [c, el("span", { class: "j-spacer", style: "flex:1" })].concat(buttons || []));
    return bar;
  }
  function crumbsFor(path) {
    // build breadcrumb objects from the root that contains path
    var best = null;
    (S.roots || []).forEach(function (r) {
      var rp = r.path.toLowerCase();
      if (path.toLowerCase().indexOf(rp) === 0 && (!best || rp.length > best.path.length)) best = r;
    });
    if (!best) return [];
    var out = [{ name: best.label, path: best.path }];
    var rest = path.slice(best.path.length).split(/[\\/]/).filter(Boolean);
    rest.pop();
    var cur = best.path;
    rest.forEach(function (seg) { cur = cur.replace(/[\\/]$/, "") + "\\" + seg; out.push({ name: seg, path: cur }); });
    return out;
  }

  // ── middle: a file ─────────────────────────────────────────────────────────────
  function openFile(path, part) {
    part = part || 0;
    S.path = path;
    markActive();
    var m = S.ui.main;
    m.textContent = "";
    m.appendChild(el("div", { class: "j-empty", text: "Opening " + base(path) + "…" }));
    try { history.replaceState(null, "", "#library/files?path=" + q(path) + (part ? "&part=" + part : "")); } catch (e) { /* ignore */ }
    api("/api/files/view?path=" + q(path) + "&part=" + part).then(function (d) {
      S.data = d;
      renderFile(d);
      renderInfo(d);
      if (!part) refreshState();
    }).catch(function (e) {
      m.textContent = "";
      m.appendChild(crumbs(crumbsFor(path), base(path)));
      m.appendChild(el("div", { class: "j-empty", text: "Could not open: " + e.message }));
      if (/MB render limit/.test(e.message)) m.appendChild(el("a", { class: "j-btn", href: "/api/files/raw?path=" + q(path), target: "_blank", rel: "noopener" }, ["Open raw"]));
    });
  }

  function renderFile(d) {
    var m = S.ui.main;
    m.textContent = "";
    var pinned = (S.state.pins || []).some(function (p) { return p.path === d.path; });
    var btns = [
      el("button", { class: "j-btn ghost", title: pinned ? "Unpin" : "Pin this file", on: { click: function () { pin(d.path, !pinned); } } }, [pinned ? "\u{1F4CC} Unpin" : "\u{1F4CC} Pin"]),
      el("button", { class: "j-btn ghost", title: "Copy the full path", on: { click: function () { copy(d.path); } } }, ["Copy path"]),
      el("a", { class: "j-btn ghost", href: d.raw_url, target: "_blank", rel: "noopener", title: "Open the file itself in a new browser tab" }, ["Raw ↗"])
    ];
    if (d.type === "markdown" || d.type === "docx") {
      btns.unshift(el("button", { class: "j-btn ghost", title: "Open in the Reader (read-aloud, tag counts)",
                                  on: { click: function () { window.JarvisOpen("reader", { path: d.path, full: true }); } } }, ["Reader"]));
    }
    if (["pdf", "epub", "markdown", "text", "docx"].indexOf(d.type) >= 0) {
      btns.unshift(el("button", { class: "j-btn primary", title: "Listen in the read-aloud Studio; it remembers where you stopped",
                                  on: { click: function () { readAloud(d.path); } } }, ["▶ Read aloud"]));
    }
    m.appendChild(crumbs(crumbsFor(d.path), d.name, btns));
    var meta = [d.root, kb(d.size), "modified " + d.mtime];
    if (d.words) meta.push(d.words.toLocaleString() + " words");
    if (d.tags && d.tags.length) meta.push(d.tags.length + " tags");
    m.appendChild(el("div", { class: "fx-meta", text: meta.join("  ·  ") }));
    if (d.part_count > 1) m.appendChild(partsBar(d));
    var body;
    if (d.type === "markdown" || d.type === "docx" || d.type === "epub") {
      if (d.headings && d.headings.length > 3) m.appendChild(outline(d.headings));
      body = el("article", { class: "fx-md", html: d.html });
      body.addEventListener("click", onLink);
    } else if (d.type === "text" || d.type === "code") {
      body = el("div", { class: "fx-code" });
      var lines = d.text.split("\n"), gutter = [], start = d.first_line || 1;
      for (var i = 0; i < lines.length; i++) gutter.push(start + i);
      body.appendChild(el("pre", { class: "fx-gutter", text: gutter.join("\n") }));
      body.appendChild(el("pre", { class: "fx-src", text: d.text }));
    } else if (d.type === "pdf") {
      body = el("iframe", { class: "fx-frame", src: d.raw_url, title: d.name });
    } else if (d.type === "html") {
      m.appendChild(el("div", { class: "fx-muted", text: "Shown with scripts switched off." }));
      body = el("iframe", { class: "fx-frame fx-white", src: d.raw_url, sandbox: "", title: d.name, referrerpolicy: "no-referrer" });
    } else if (d.type === "image") {
      body = el("div", { class: "fx-media" }, [el("img", { src: d.raw_url, alt: d.name })]);
    } else if (d.type === "audio") {
      body = el("div", { class: "fx-media" }, [el("audio", { src: d.raw_url, controls: true })]);
    } else if (d.type === "video") {
      body = el("div", { class: "fx-media" }, [el("video", { src: d.raw_url, controls: true })]);
    } else {
      body = el("div", { class: "j-empty", text: "No preview for this kind of file. Use Raw to open it." });
    }
    m.appendChild(body);
    if (d.part_count > 1) m.appendChild(partsBar(d));
    m.scrollTop = 0;
  }

  function partsBar(d) {
    var sel = el("select", { class: "fx-select", on: { change: function () { openFile(d.path, +sel.value); } } });
    for (var i = 0; i < d.part_count; i++) {
      var o = el("option", { value: i, text: "Part " + (i + 1) + (d.parts && d.parts[i] ? " — " + d.parts[i] : "") });
      if (i === d.part) o.selected = true;
      sel.appendChild(o);
    }
    return el("div", { class: "fx-parts" }, [
      el("button", { class: "j-btn", disabled: d.part === 0 ? true : null, on: { click: function () { openFile(d.path, d.part - 1); } } }, ["‹ Prev"]),
      sel,
      el("button", { class: "j-btn", disabled: d.part >= d.part_count - 1 ? true : null, on: { click: function () { openFile(d.path, d.part + 1); } } }, ["Next ›"])
    ]);
  }

  function outline(heads) {
    var det = el("details", { class: "fx-outline" }, [el("summary", { text: "Outline (" + heads.length + " headings)" })]);
    heads.slice(0, 300).forEach(function (h) {
      det.appendChild(el("a", { href: "#", style: "padding-left:" + ((h.level - 1) * 12) + "px",
                                on: { click: function (e) { e.preventDefault(); scrollToHeading(h.id); } } }, [h.text]));
    });
    return det;
  }
  function scrollToHeading(id) {
    var t = document.getElementById("h-" + id);
    if (t) t.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  function onLink(e) {
    var a = e.target.closest("a.md-wikilink");
    if (!a) return;
    e.preventDefault();
    var p = a.getAttribute("data-path"), h = a.getAttribute("data-heading");
    if (p && e.shiftKey && window.JarvisPeek) { window.JarvisPeek(p, 0); return; }
    if (p) {
      openFile(p);
      if (h) setTimeout(function () { scrollToHeading(h); }, 900);
    } else if (h) scrollToHeading(h);
  }

  // ── right: where it's going, variants, backlinks, notes ────────────────────────
  function renderInfo(d) {
    var I = S.ui.info;
    I.textContent = "";
    var where = el("section", { class: "fx-card" }, [el("h4", { text: "Where is this going?" }), el("div", { class: "fx-muted", text: "Checking…" })]);
    var back = el("section", { class: "fx-card" }, [el("h4", { text: "Backlinks" })]);
    var notes = el("section", { class: "fx-card" }, [el("h4", { text: "Your notes on this file" })]);
    I.appendChild(where);
    if (d.type === "markdown") I.appendChild(back);
    I.appendChild(notes);
    if (d.tags && d.tags.length) {
      I.appendChild(el("section", { class: "fx-card" }, [el("h4", { text: "Tags" })].concat(
        d.tags.slice(0, 40).map(function (t) { return el("span", { class: "md-tag", text: "#" + t }); }))));
    }
    api("/api/files/where?path=" + q(d.path)).then(function (w) { fillWhere(where, w, d); }).catch(function (e) { where.lastChild.textContent = e.message; });
    if (d.type === "markdown") loadBacklinks(back, d.path);
    loadNotes(notes, d.path);
  }

  function fillWhere(box, w, d) {
    box.textContent = "";
    box.appendChild(el("h4", { text: "Where is this going?" }));
    var v = w.volumes || {};
    var line;
    if (v.chapter) {
      line = el("div", null, ["Planned into ", el("a", { href: "#", on: { click: function (e) { e.preventDefault(); window.JarvisOpen("books", { chapter: v.chapter }); } } },
        [v.volume + " · " + v.chapter_title]), el("span", { class: "fx-muted", text: " (" + v.state + ")" })]);
    } else {
      var label = { "unsorted": "In the Volumes pool, waiting in Unsorted.", "already in a book": "Already inside one of the books.",
                    "not in pool": "Not in the Volumes pool (archive, stub, older version, or not book material)." }[v.state] || ("Volumes: " + (v.state || "unknown"));
      line = el("div", { text: label });
    }
    box.appendChild(line);
    if (w.loose) {
      var L = w.loose;
      var bits = ["Loose Ends: " + (L.kind || "").toLowerCase()];
      if (L.integrated_into) bits.push("integrated into " + base(L.integrated_into));
      if (L.open_items) bits.push(L.open_items + " open item" + (L.open_items === 1 ? "" : "s"));
      if (L.mark) bits.push("marked " + (L.mark.status || L.mark));
      box.appendChild(el("div", { class: "fx-muted", text: bits.join(" · ") }));
    }
    if (w.variants && w.variants.length) {
      box.appendChild(el("h4", { text: "Other versions of this note (" + w.variants.length + ")" }));
      w.variants.slice(0, 20).forEach(function (x) {
        box.appendChild(el("div", { class: "fx-variant" }, [
          el("a", { href: "#", title: x.path, on: { click: function (e) { e.preventDefault(); openFile(x.path); } } }, [x.rel || base(x.path)]),
          el("span", { class: "fx-muted", text: " " + (x.vault ? x.vault + " · " : "") + kb(x.size || 0) + " · " + (x.mtime || "").replace("T", " ") }),
          el("button", { class: "j-btn ghost", title: "Compare side by side", on: { click: function () { openDiff(d.path, x.path); } } }, ["Compare"])
        ]));
      });
    }
    if (w.exact_copies && w.exact_copies.length) {
      box.appendChild(el("div", { class: "fx-muted", text: w.exact_copies.length + " byte-identical cop" + (w.exact_copies.length === 1 ? "y" : "ies") + " elsewhere" }));
    }
  }

  function loadBacklinks(box, path) {
    api("/api/files/backlinks?path=" + q(path)).then(function (b) {
      box.textContent = "";
      box.appendChild(el("h4", { text: "Backlinks" + (b.state === "ok" ? " (" + b.total + ")" : "") }));
      if (b.state !== "ok") {
        box.appendChild(el("div", { class: "fx-muted", text: "The link index hasn't been built yet. The first build reads every note once (several minutes); after that only changed notes are re-read." }));
        box.appendChild(el("button", { class: "j-btn", on: { click: function () { buildLinks(box, path); } } }, ["Build link index"]));
        return;
      }
      if (!b.total) box.appendChild(el("div", { class: "fx-muted", text: "No note links here." }));
      b.backlinks.forEach(function (x) {
        box.appendChild(el("div", null, [el("a", { href: "#", title: x.path, on: { click: function (e) { e.preventDefault(); openFile(x.path); } } }, [x.name])]));
      });
      box.appendChild(el("button", { class: "j-btn ghost", title: "Re-read notes changed since the last build", on: { click: function () { buildLinks(box, path); } } }, ["Refresh index"]));
    });
  }
  function buildLinks(box, path) {
    api("/api/files/links/build", { method: "POST" }).then(function () {
      var tick = setInterval(function () {
        api("/api/files/links/status").then(function (s) {
          box.textContent = "";
          box.appendChild(el("h4", { text: "Backlinks" }));
          if (s.state === "running") box.appendChild(el("div", { class: "fx-muted", text: "Indexing links… " + s.done.toLocaleString() + " / " + (s.total || "?").toLocaleString() + " notes" }));
          else { clearInterval(tick); if (s.state === "error") box.appendChild(el("div", { text: "Index failed: " + s.error })); else loadBacklinks(box, path); }
        });
      }, 1000);
    });
  }

  function loadNotes(box, path) {
    api("/api/files/notes?path=" + q(path)).then(function (d) {
      box.textContent = "";
      box.appendChild(el("h4", { text: "Your notes on this file" }));
      box.appendChild(el("div", { class: "fx-muted", text: "Kept in the suite, never written into the file." }));
      d.notes.forEach(function (n) {
        box.appendChild(el("div", { class: "fx-note" }, [el("div", { class: "fx-muted", text: n.at }), el("div", { class: "fx-note-text", text: n.text }),
          el("button", { class: "j-btn ghost", title: "Remove this note", on: { click: function () {
            api("/api/files/notes?path=" + q(path) + "&id=" + q(n.id), { method: "DELETE" }).then(function () { loadNotes(box, path); }); } } }, ["✕"])]));
      });
      var ta = el("textarea", { class: "fx-textarea", rows: 3, placeholder: "Add a note…" });
      box.appendChild(ta);
      box.appendChild(el("button", { class: "j-btn", on: { click: function () {
        if (!ta.value.trim()) return;
        api("/api/files/notes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: path, text: ta.value }) })
          .then(function () { loadNotes(box, path); });
      } } }, ["Save note"]));
    });
  }

  // ── diff ───────────────────────────────────────────────────────────────────────
  function openDiff(a, b) {
    var m = S.ui.main;
    m.textContent = "";
    m.appendChild(el("div", { class: "j-empty", text: "Comparing…" }));
    api("/api/files/diff?a=" + q(a) + "&b=" + q(b)).then(function (d) {
      m.textContent = "";
      m.appendChild(el("div", { class: "fx-bar" }, [
        el("strong", { text: "Compare" }), el("span", { style: "flex:1" }),
        el("button", { class: "j-btn ghost", on: { click: function () { openFile(a); } } }, ["Back to the file"])]));
      m.appendChild(el("div", { class: "fx-meta", text: Math.round(d.similarity * 100) + "% similar  ·  left " + d.lines_a + " lines (" + d.changed_a +
        " only here)  ·  right " + d.lines_b + " lines (" + d.changed_b + " only here)" + (d.truncated ? "  ·  long diff cut short" : "") }));
      var tb = el("table", { class: "fx-diff" });
      tb.appendChild(el("tr", null, [el("th", { colspan: 2, text: base(a), title: a }), el("th", { colspan: 2, text: base(b), title: b })]));
      d.rows.forEach(function (r) {
        if (r.op === "fold") { tb.appendChild(el("tr", { class: "fx-fold" }, [el("td", { colspan: 4, text: "⋯ " + r.n + " identical lines ⋯" })])); return; }
        var ca = r.op === "equal" ? "" : (r.a === null ? "fx-blank" : "fx-del");
        var cb = r.op === "equal" ? "" : (r.b === null ? "fx-blank" : "fx-ins");
        tb.appendChild(el("tr", null, [
          el("td", { class: "fx-ln", text: r.a_no || "" }), el("td", { class: "fx-dc " + ca, text: r.a === null ? "" : r.a }),
          el("td", { class: "fx-ln", text: r.b_no || "" }), el("td", { class: "fx-dc " + cb, text: r.b === null ? "" : r.b })]));
      });
      m.appendChild(tb);
    }).catch(function (e) { m.textContent = "Could not compare: " + e.message; });
  }

  // ── state ──────────────────────────────────────────────────────────────────────
  function refreshState() {
    return api("/api/files/state").then(function (s) {
      S.state = s;
      if (!S.ui.find.value.trim()) {
        // keep the tree's expansion: only re-render the pinned/recent block
        var tree = Array.prototype.slice.call(S.ui.side.children);
        var foldersAt = tree.findIndex(function (n) { return n.classList && n.classList.contains("fx-sec") && n.textContent === "Folders"; });
        var keep = foldersAt >= 0 ? tree.slice(foldersAt) : [];
        renderSide();
        if (keep.length) {
          var fresh = Array.prototype.slice.call(S.ui.side.children);
          var at = fresh.findIndex(function (n) { return n.classList && n.classList.contains("fx-sec") && n.textContent === "Folders"; });
          fresh.slice(at).forEach(function (n) { n.remove(); });
          keep.forEach(function (n) { S.ui.side.appendChild(n); });
        }
        markActive();
      }
    });
  }
  function pin(path, on) {
    api("/api/files/pin", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path: path, pinned: on }) })
      .then(refreshState).then(function () { if (S.data && S.data.path === path) renderFile(S.data); else if (S.folder === path) openFolder(path); });
  }
  function readAloud(path) {
    // the Library > PDFs tab is the Studio; point its frame at this file and switch to it
    var frame = document.getElementById("studio-iframe");
    if (!frame) { window.open("/static/studio_frame.html?path=" + q(path), "_blank", "noopener"); return; }
    frame.src = "/static/studio_frame.html?path=" + q(path);
    if (window.JarvisGo) window.JarvisGo("studio"); else window.switchTab("studio");
  }
  function copy(text) {
    try { navigator.clipboard.writeText(text); if (window.showToast) window.showToast("Path copied", "success"); } catch (e) { /* ignore */ }
  }

  window.JarvisModules.files = { load: load };
})();
