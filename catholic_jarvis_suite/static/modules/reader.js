/* Reader module tab (module id "reader"). Task C004.
 * Reads The Catholic Case (Reader's Edition) chapter by chapter.
 * Renders formatted HTML with interactive coloured evidence badges,
 * surfaces 'still needs checking' checklists, plays TTS audio, and displays tiered explanations.
 * Safe DOM rendering: textContent / escape functions only. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

  function el(tag, props, text, children) {
    var n = document.createElement(tag);
    if (props) {
      Object.keys(props).forEach(function (k) {
        if (k === "style") n.style.cssText = props[k];
        else if (k === "class") n.className = props[k];
        else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), props[k]);
        else n.setAttribute(k, props[k]);
      });
    }
    if (text !== undefined && text !== null) n.textContent = text;
    (children || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }

  var INPUT_CSS = "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);" +
    "border-radius:4px;padding:6px 10px;font-size:12px;font-family:inherit;";
  var BTN_CSS = "background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);" +
    "border-radius:4px;padding:5px 12px;font-size:11px;cursor:pointer;font-family:inherit;";
  var BTN_GOLD = BTN_CSS + "color:var(--accent-gold);border-color:var(--accent-gold);";
  var BTN_CYAN = BTN_CSS + "color:var(--accent-cyan);border-color:var(--accent-cyan);";
  var CARD_CSS = "background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:12px;";

  function pill(text, color) {
    return el("span", {
      style: "font-size:10px;padding:1px 7px;border-radius:8px;border:1px solid " + color +
        ";color:" + color + ";white-space:nowrap;font-weight:600;"
    }, text);
  }

  // C007: other tabs (Loose Ends, Recall) call window.JarvisOpen("reader", {path}); index.html switches to
  // this tab and 350 ms later fires "jarvis:open-reader". The listener lives at script level so an event
  // that arrives before load() has finished is kept in pendingOpen and applied at the end of load().
  var api = null;
  var pendingOpen = null;
  window.addEventListener("jarvis:open-reader", function (ev) {
    var d = (ev && ev.detail) || {};
    if (!d.path) return;
    if (api) api.openPath(String(d.path), d.part ? parseInt(d.part, 10) || 0 : 0);
    else pendingOpen = d;
  });

  function load(root) {
    root.textContent = "";
    root.style.cssText = "padding:16px;color:var(--text-main);max-width:1400px;margin:0 auto;";

    // Inject reader styling for badges and layout
    if (!document.getElementById("reader-custom-style")) {
      var st = document.createElement("style");
      st.id = "reader-custom-style";
      st.textContent = [
        ".reader-badge { display:inline-block; font-size:10px; font-weight:600; padding:1px 5px; border-radius:4px; margin:0 3px; cursor:help; vertical-align:baseline; }",
        ".reader-badge.badge-v { background:rgba(46,204,113,0.18); border:1px solid var(--accent-green); color:var(--accent-green); }",
        ".reader-badge.badge-r { background:rgba(241,196,15,0.18); border:1px solid var(--accent-gold); color:var(--accent-gold); }",
        ".reader-badge.badge-s { background:rgba(149,165,166,0.18); border:1px solid var(--text-dim); color:var(--text-dim); }",
        ".reader-h { color:var(--accent-gold); margin-top:1.4em; margin-bottom:0.6em; }",
        ".reader-h1 { font-size:22px; border-bottom:1px solid var(--border); padding-bottom:8px; }",
        ".reader-h2 { font-size:18px; color:var(--accent-cyan); border-bottom:1px dashed var(--border); padding-bottom:4px; }",
        ".reader-h3 { font-size:15px; color:var(--text-main); }",
        ".reader-p { line-height:1.65; margin:0.8em 0; font-size:14px; position:relative; }",
        ".reader-p:hover { background:rgba(255,255,255,0.02); }",
        ".reader-quote { border-left:3px solid var(--accent-gold); padding:6px 12px; margin:0.8em 0; background:var(--bg-card); font-style:italic; }",
        ".reader-list { padding-left:24px; margin:0.8em 0; line-height:1.6; }",
        ".reader-code { background:var(--bg-card); padding:2px 5px; border-radius:3px; font-family:monospace; font-size:12px; }",
        ".reader-hr { border:0; border-top:1px solid var(--border); margin:24px 0; }"
      ].join("\n");
      document.head.appendChild(st);
    }

    var currentStem = null;
    var allChapters = [];
    var currentAudio = null;
    var userChose = false;     // set once a document was opened by path, so the default chapter does not overwrite it
    var docSeq = 0;            // ignores responses of superseded document requests

    // Header bar
    var header = el("div", { style: "display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;border-bottom:1px solid var(--border);padding-bottom:10px;" }, null, [
      el("div", null, null, [
        el("h2", { style: "margin:0 0 4px 0;font-size:18px;color:var(--accent-gold);" }, "The Catholic Case — Reader's Edition"),
        el("span", { style: "font-size:12px;color:var(--text-dim);" },
          "35 Chapters · Full text with evidence tags, 'still needs checking' audits, read-aloud TTS, and 3-level explanations.")
      ]),
      el("div", { style: "display:flex;gap:8px;" }, null, [
        el("button", { style: BTN_CYAN, onclick: function () { showBookwideCheckingModal(); } }, "Book-Wide Checking Audit")
      ])
    ]);

    // Navigation bar
    var chapterSelect = el("select", { style: INPUT_CSS + "min-width:320px;", onchange: function () {
      currentStem = this.value;
      if (currentStem) loadChapter(currentStem);
    }});
    var navBar = el("div", { style: "display:flex;gap:12px;align-items:center;margin-bottom:16px;background:var(--bg-panel);padding:8px 12px;border-radius:6px;border:1px solid var(--border);" }, null, [
      el("span", { style: "font-size:12px;font-weight:600;color:var(--text-muted);" }, "Select Chapter:"),
      chapterSelect,
      el("div", { id: "reader-tag-bar", style: "display:flex;gap:8px;align-items:center;margin-left:auto;font-size:11px;" })
    ]);

    // Workspace container (Main reader pane + Side panel for checklist & tiers)
    var workspace = el("div", { style: "display:grid;grid-template-columns:2.5fr 1fr;gap:20px;" });
    var mainPane = el("div", { id: "reader-main-pane", style: "background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:24px;min-height:500px;" });
    var sidePane = el("div", { id: "reader-side-pane" });
    workspace.appendChild(mainPane);
    workspace.appendChild(sidePane);

    // C007: open any allowed document by pasted path, or pick one from the library (Loose Ends registry + 10_VOLUMES).
    var pathBox = el("input", { type: "text", "aria-label": "Document path", placeholder: "Paste a file path (.md or .html) and press Enter",
      style: INPUT_CSS + "flex:1 1 380px;min-width:240px;", onkeydown: function (e) {
        if (e.key === "Enter") { var v = pathBox.value.trim(); if (v) openDoc(v, 0); }
      } });
    var openBtn = el("button", { style: BTN_GOLD, onclick: function () { var v = pathBox.value.trim(); if (v) openDoc(v, 0); } }, "Open document");
    var libBtn = el("button", { style: BTN_CYAN, onclick: function () { toggleLibrary(); } }, "Browse documents");
    var docMsg = el("div", { id: "reader-doc-msg", style: "font-size:11px;color:var(--text-dim);margin-top:6px;min-height:14px;" });
    var libPanel = el("div", { style: "display:none;margin-top:8px;" });
    var docBar = el("div", { style: "margin-bottom:16px;background:var(--bg-panel);padding:8px 12px;border-radius:6px;border:1px solid var(--border);" }, null, [
      el("div", { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap;" }, null, [
        el("span", { style: "font-size:12px;font-weight:600;color:var(--text-muted);" }, "Open a document:"),
        pathBox, openBtn, libBtn
      ]),
      docMsg, libPanel
    ]);

    var libLoaded = false;
    var libTimer = null;
    function toggleLibrary() {
      if (libPanel.style.display === "none") {
        libPanel.style.display = "block";
        if (!libLoaded) buildLibrary();
      } else {
        libPanel.style.display = "none";
      }
    }
    function buildLibrary() {
      libLoaded = true;
      libPanel.textContent = "";
      var q = el("input", { type: "search", "aria-label": "Search documents", placeholder: "Search titles and paths (all words must match)",
        style: INPUT_CSS + "width:100%;box-sizing:border-box;margin-bottom:6px;" });
      var volBox = el("div", { style: "font-size:12px;margin-bottom:6px;" });
      var results = el("div", { style: "max-height:240px;overflow-y:auto;border:1px solid var(--border);border-radius:4px;background:var(--bg-card);" });
      libPanel.appendChild(q);
      libPanel.appendChild(volBox);
      libPanel.appendChild(results);

      function row(d, extra) {
        return el("div", { style: "padding:5px 8px;border-bottom:1px solid var(--border);cursor:pointer;font-size:12px;",
          title: d.path, onclick: function () { libPanel.style.display = "none"; openDoc(d.path, 0); } }, null, [
          el("div", { style: "color:var(--text-main);" }, d.title || d.path),
          el("div", { style: "font-size:10px;color:var(--text-dim);word-break:break-all;" }, (extra ? extra + "  " : "") + d.path)
        ]);
      }
      function search() {
        fetch("/api/reader/docs?limit=60&q=" + encodeURIComponent(q.value)).then(function (r) { return r.json(); }).then(function (d) {
          volBox.textContent = "";
          if ((d.volumes || []).length) {
            volBox.appendChild(el("div", { style: "color:var(--accent-gold);font-weight:600;margin-bottom:3px;" }, "Finished volumes (" + d.volumes.length + ")"));
            var vb = el("div", { style: "border:1px solid var(--border);border-radius:4px;background:var(--bg-card);" });
            d.volumes.forEach(function (v) { vb.appendChild(row(v, v.rel)); });
            volBox.appendChild(vb);
          } else {
            volBox.appendChild(el("div", { style: "color:var(--text-dim);" }, "No finished volumes found yet (the 10_VOLUMES folder is empty or absent)."));
          }
          results.textContent = "";
          (d.docs || []).forEach(function (x) { results.appendChild(row(x, x.kind || "")); });
          if (!(d.docs || []).length) results.appendChild(el("div", { style: "padding:8px;color:var(--text-dim);font-size:12px;" }, "No documents match."));
          if (d.total > (d.docs || []).length) results.appendChild(el("div", { style: "padding:6px 8px;color:var(--text-dim);font-size:11px;" },
            "Showing " + d.docs.length + " of " + d.total + ". Type more words to narrow the list."));
        }).catch(function (e) { results.textContent = "Could not load the document list: " + e; });
      }
      q.addEventListener("input", function () { clearTimeout(libTimer); libTimer = setTimeout(search, 250); });
      search();
    }

    root.appendChild(header);
    root.appendChild(navBar);
    root.appendChild(docBar);
    root.appendChild(workspace);

    function loadChaptersList() {
      fetch("/api/reader/chapters").then(function (r) { return r.json(); }).then(function (data) {
        allChapters = data.chapters || [];
        chapterSelect.textContent = "";
        allChapters.forEach(function (ch) {
          var opt = el("option", { value: ch.stem }, ch.title);
          chapterSelect.appendChild(opt);
        });
        if (allChapters.length > 0 && !userChose) {
          // Default to Chapter 06 if present, else first (unless a document was already opened by path)
          var ch06 = allChapters.find(function (c) { return c.stem.indexOf("06_") === 0; });
          currentStem = ch06 ? ch06.stem : allChapters[0].stem;
          chapterSelect.value = currentStem;
          loadChapter(currentStem);
        }
      });
    }

    function loadChapter(stem) {
      userChose = true;
      docSeq++;
      docMsg.textContent = "";
      mainPane.textContent = "";
      mainPane.appendChild((window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading chapter...") : document.createTextNode("Loading chapter..."));
      sidePane.textContent = "";

      fetch("/api/reader/chapters/" + encodeURIComponent(stem)).then(function (r) { return r.json(); }).then(function (data) {
        renderChapter(data);
      });
    }

    // C007: open any allowed document by absolute path. part = which slice of a large file (0 = first);
    // scrollIdx = index of the section heading (levels 1-3) inside that part to scroll to.
    function openDoc(path, part, scrollIdx) {
      userChose = true;
      var my = ++docSeq;
      pathBox.value = path;
      docMsg.style.color = "var(--text-dim)";
      docMsg.textContent = "Opening...";
      if (!part) {
        mainPane.textContent = "";
        mainPane.appendChild((window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading document...") : document.createTextNode("Loading document..."));
        sidePane.textContent = "";
      }
      fetch("/api/reader/doc?path=" + encodeURIComponent(path) + "&part=" + (part || 0)).then(function (r) {
        return r.json().then(function (d) { return { ok: r.ok, status: r.status, d: d }; }, function () { return { ok: r.ok, status: r.status, d: {} }; });
      }).then(function (x) {
        if (my !== docSeq) return;
        if (!x.ok) {
          var why = x.status === 403 ? "Not allowed: " : x.status === 404 ? "Not found: " : "Could not open (" + x.status + "): ";
          docMsg.style.color = "var(--accent-red)";
          docMsg.textContent = why + ((x.d && x.d.detail) ? String(x.d.detail) : "") + "  Allowed: the Reader's Edition chapters, 10_VOLUMES, and documents listed by Loose Ends.";
          if (!part) mainPane.textContent = "";
          return;
        }
        docMsg.style.color = "var(--text-dim)";
        docMsg.textContent = x.d.source + " document, " + x.d.bytes.toLocaleString() + " bytes" +
          (x.d.part_count > 1 ? ", part " + (x.d.part + 1) + " of " + x.d.part_count : "");
        renderChapter(x.d, { doc: true });
        if (scrollIdx !== undefined && scrollIdx !== null) {
          var heads = mainPane.querySelectorAll("h1,h2,h3");
          if (heads[scrollIdx]) heads[scrollIdx].scrollIntoView();
        } else if (part) {
          mainPane.scrollIntoView();
        }
      }).catch(function (e) {
        if (my !== docSeq) return;
        docMsg.style.color = "var(--accent-red)";
        docMsg.textContent = "Could not open the document: " + e;
      });
    }

    function partBar(data) {
      var n = data.part_count || 1;
      if (n < 2) return null;
      var sel = el("select", { style: INPUT_CSS + "max-width:420px;", "aria-label": "Part of this document", onchange: function () { openDoc(data.path, parseInt(this.value, 10)); } });
      (data.parts || []).forEach(function (p) {
        var o = el("option", { value: String(p.index) }, (p.index + 1) + ". " + p.title);
        if (p.index === data.part) o.selected = true;
        sel.appendChild(o);
      });
      var prev = el("button", { style: BTN_CSS, onclick: function () { openDoc(data.path, data.part - 1); } }, "Previous part");
      var next = el("button", { style: BTN_CSS, onclick: function () { openDoc(data.path, data.part + 1); } }, "Next part");
      prev.disabled = data.part <= 0;
      next.disabled = data.part >= n - 1;
      return el("div", { style: "display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px;padding-bottom:10px;border-bottom:1px solid var(--border);font-size:12px;color:var(--text-muted);" }, null, [
        el("span", null, "Large document: part " + (data.part + 1) + " of " + n),
        prev, sel, next
      ]);
    }

    function tocCard(data) {
      var secs = data.sections || [];
      if (!secs.length) return null;
      var perPart = {};
      var rows = [];
      secs.forEach(function (s) {
        var k = perPart[s.part] = (perPart[s.part] === undefined ? 0 : perPart[s.part] + 1);
        if (s.level <= 2) rows.push({ s: s, idx: k });
      });
      var CAP = 500;
      var box = el("div", { style: "max-height:300px;overflow-y:auto;font-size:12px;" });
      rows.slice(0, CAP).forEach(function (r) {
        box.appendChild(el("div", { style: "padding:2px 0 2px " + ((r.s.level - 1) * 12) + "px;cursor:pointer;color:" + (r.s.level === 1 ? "var(--accent-gold)" : "var(--text-main)") + ";",
          title: "Go to this section", onclick: function () {
            if (r.s.part === data.part) {
              var heads = mainPane.querySelectorAll("h1,h2,h3");
              if (heads[r.idx]) heads[r.idx].scrollIntoView();
            } else {
              openDoc(data.path, r.s.part, r.idx);
            }
          } }, r.s.title));
      });
      if (rows.length > CAP) box.appendChild(el("div", { style: "color:var(--text-dim);font-size:11px;padding-top:4px;" }, "Showing the first " + CAP + " of " + rows.length + " headings. Use the part list above the text for the rest."));
      return el("div", { style: CARD_CSS }, null, [
        el("h4", { style: "margin:0 0 8px 0;font-size:13px;color:var(--accent-gold);" }, "Contents (" + rows.length + " headings)"),
        box
      ]);
    }

    function renderChapter(data, opts) {
      opts = opts || {};
      // Update top tag bar
      var tagBar = document.getElementById("reader-tag-bar");
      tagBar.textContent = "";
      var tc = data.tag_counts || {};
      tagBar.appendChild(pill("V: " + (tc.V || 0), "var(--accent-green)"));
      tagBar.appendChild(pill("R: " + (tc.R || 0), "var(--accent-gold)"));
      tagBar.appendChild(pill("S: " + (tc.S || 0), "var(--text-dim)"));
      if (data.checking_count > 0) {
        tagBar.appendChild(pill(data.checking_count + " checks pending", "var(--accent-red)"));
      }

      // Render main reader content
      mainPane.innerHTML = data.html || "";   // server-side render_markdown escapes every character of the source first
      if (opts.doc) {
        var pb = partBar(data);
        if (pb) {
          mainPane.insertBefore(pb, mainPane.firstChild);
          var pb2 = partBar(data);      // the same controls again at the end of the part
          pb2.style.marginTop = "18px";
          mainPane.appendChild(pb2);
        }
      }

      // Add TTS read-aloud buttons to paragraphs
      var paragraphs = mainPane.querySelectorAll("p.reader-p");
      paragraphs.forEach(function (p) {
        var isSpanish = p.getAttribute("data-lang") === "es";
        var btn = el("button", {
          style: "position:absolute;right:4px;top:2px;font-size:10px;padding:2px 5px;background:var(--bg-card);border:1px solid var(--border);border-radius:3px;color:var(--text-muted);cursor:pointer;opacity:0.3;transition:opacity 0.2s;",
          title: "Read aloud (" + (isSpanish ? "Spanish" : "English") + ")",
          onclick: function (e) {
            e.stopPropagation();
            playTts(p.textContent, isSpanish);
          }
        }, isSpanish ? "🔊 ES" : "🔊 EN");
        p.addEventListener("mouseenter", function () { btn.style.opacity = "1"; });
        p.addEventListener("mouseleave", function () { btn.style.opacity = "0.3"; });
        p.appendChild(btn);
      });

      // Render Side Pane
      sidePane.textContent = "";

      // 1. 'Still needs checking' card
      var checkCard = el("div", { style: CARD_CSS }, null, [
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;" }, null, [
          el("h4", { style: "margin:0;font-size:13px;color:var(--accent-red);" }, "Still Needs Checking (" + data.checking_count + ")"),
          pill("Pre-Deployment Gate", "var(--accent-red)")
        ]),
        (function () {
          var box = el("div", { style: "max-height:280px;overflow-y:auto;font-size:12px;" });
          if (!data.checking_items || data.checking_items.length === 0) {
            box.appendChild(el("div", { style: "color:var(--text-dim);font-size:11px;" }, "No items flagged for checking in this chapter."));
            return box;
          }
          data.checking_items.forEach(function (ci) {
            var item = el("div", { style: "margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--border);" }, null, [
              ci.category ? el("div", { style: "font-size:10px;font-weight:600;color:var(--accent-gold);" }, ci.category) : null,
              el("div", { style: "color:var(--text-main);line-height:1.4;" }, ci.text)
            ]);
            box.appendChild(item);
          });
          return box;
        })()
      ]);
      sidePane.appendChild(checkCard);

      // C007: contents list for documents opened by path; tiers exist only for the chapters
      if (opts.doc) {
        var toc = tocCard(data);
        if (toc) sidePane.appendChild(toc);
        if (data.source !== "chapter") {
          sidePane.appendChild(el("div", { style: CARD_CSS + "font-size:11px;color:var(--text-dim);" }, "Three-level explanations exist only for the Reader's Edition chapters."));
          return;
        }
      }

      // 2. Three-Level & Spanish Tiers Card
      var tiersCard =el("div", { style: CARD_CSS }, null, [
        el("h4", { style: "margin:0 0 10px 0;font-size:13px;color:var(--accent-gold);" }, "Three-Level Explanations"),
        el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:8px;" }, "Select a section to inspect plain ELI5, working, expert, or Spanish family register tiers:"),
        (function () {
          var secSelect = el("select", { style: INPUT_CSS + "width:100%;margin-bottom:10px;", onchange: function () {
            loadSectionTier(data.stem, this.value);
          }});
          (data.sections || []).forEach(function (s) {
            if (s.level === 2) {
              var m = s.title.match(/^(\d+)\.\s*(.*)/);
              var secNum = m ? m[1] : s.title;
              secSelect.appendChild(el("option", { value: secNum }, s.title));
            }
          });
          var tierContainer = el("div", { id: "reader-tier-display" });
          var box = el("div", null, null, [secSelect, tierContainer]);
          if (secSelect.options.length > 0) {
            setTimeout(function () { loadSectionTier(data.stem, secSelect.value); }, 50);
          }
          return box;
        })()
      ]);
      sidePane.appendChild(tiersCard);
    }

    function loadSectionTier(stem, secNum) {
      var container = document.getElementById("reader-tier-display");
      if (!container) return;
      container.textContent = "";
      container.appendChild((window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading tier...") : document.createTextNode("Loading tier..."));

      fetch("/api/reader/tiers/" + stem + "/" + secNum).then(function (r) { return r.json(); }).then(function (res) {
        container.textContent = "";
        if (res.status === "not_generated") {
          container.appendChild(el("div", { style: "background:var(--bg-card);border:1px dashed var(--border);border-radius:4px;padding:12px;text-align:center;font-size:11px;color:var(--text-dim);" }, null, [
            el("div", { style: "margin-bottom:6px;" }, "Tier not generated yet for this section."),
            el("div", { style: "font-size:10px;color:var(--text-muted);" }, "Generate with tools/make_tier_briefs.py")
          ]));
          return;
        }
        var d = res.data || {};
        var tabs = el("div", { style: "display:flex;gap:4px;margin-bottom:8px;" });
        var content = el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:10px;font-size:12px;line-height:1.5;min-height:120px;" });

        function setTab(name, text) {
          Array.from(tabs.children).forEach(function (btn) {
            btn.style.borderColor = btn.getAttribute("data-name") === name ? "var(--accent-gold)" : "var(--border)";
            btn.style.color = btn.getAttribute("data-name") === name ? "var(--accent-gold)" : "var(--text-muted)";
          });
          content.textContent = text || "(empty)";
        }

        var tPlain = el("button", { "data-name": "plain", style: BTN_CSS, onclick: function () { setTab("plain", d.plain); } }, "ELI5");
        var tWork = el("button", { "data-name": "working", style: BTN_CSS, onclick: function () { setTab("working", d.working); } }, "Working");
        var tExp = el("button", { "data-name": "expert", style: BTN_CSS, onclick: function () { setTab("expert", d.expert); } }, "Expert");
        var tEs = el("button", { "data-name": "spanish", style: BTN_CSS, onclick: function () { setTab("spanish", d.spanish); } }, "Español");

        tabs.appendChild(tPlain);
        tabs.appendChild(tWork);
        tabs.appendChild(tExp);
        tabs.appendChild(tEs);

        container.appendChild(tabs);
        container.appendChild(content);
        setTab("plain", d.plain);
      });
    }

    function playTts(text, isSpanish) {
      if (!text) return;
      var cleanText = text.replace(/\[[VRS][^\]]*\]/g, "").trim();
      var voice = isSpanish ? "es-MX-DaliaNeural" : "en-US-AvaNeural";
      var url = "/api/tts?text=" + encodeURIComponent(cleanText.slice(0, 500)) + "&voice=" + voice;
      if (currentAudio) {
        currentAudio.pause();
      }
      currentAudio = new Audio(url);
      currentAudio.play();
    }

    function showBookwideCheckingModal() {
      var modal = el("div", { style: "position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.75);display:flex;align-items:center;justify-content:center;z-index:9999;" }, null, [
        el("div", { style: "background:var(--bg-panel);border:1px solid var(--border);border-radius:8px;padding:24px;width:800px;max-width:90%;max-height:85vh;display:flex;flex-direction:column;color:var(--text-main);" }, null, [
          el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;border-bottom:1px solid var(--border);padding-bottom:10px;" }, null, [
            el("h3", { style: "margin:0;color:var(--accent-red);" }, "Book-Wide 'Still Needs Checking' Audit"),
            el("button", { style: BTN_CSS, onclick: function () { document.body.removeChild(modal); } }, "Close")
          ]),
          (function () {
            var box = (window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading book-wide checklist...")
              : el("div", { style: "overflow-y:auto;flex:1;padding-right:8px;" }, "Loading book-wide checklist...");
            fetch("/api/reader/checking").then(function (r) { return r.json(); }).then(function (data) {
              box.textContent = "";
              box.appendChild(el("div", { style: "font-size:12px;color:var(--text-dim);margin-bottom:12px;" },
                "Total items pending verification before deployment: " + data.count));
              (data.items || []).forEach(function (it, idx) {
                var row = el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:8px;margin-bottom:8px;font-size:12px;" }, null, [
                  el("div", { style: "display:flex;justify-content:space-between;font-size:11px;color:var(--accent-gold);margin-bottom:4px;" }, null, [
                    el("span", { style: "font-weight:600;" }, it.chapter + (it.category ? " › " + it.category : "")),
                    el("span", { style: "color:var(--text-dim);" }, "#" + (idx + 1))
                  ]),
                  el("div", { style: "line-height:1.4;" }, it.text)
                ]);
                box.appendChild(row);
              });
            });
            return box;
          })()
        ])
      ]);
      document.body.appendChild(modal);
    }

    api = { openPath: function (p, part) { openDoc(p, part || 0); } };
    if (pendingOpen) {
      var pd = pendingOpen;
      pendingOpen = null;
      openDoc(String(pd.path), pd.part ? parseInt(pd.part, 10) || 0 : 0);
    }
    loadChaptersList();
  }

  window.JarvisModules["reader"] = { load: load };
})();
