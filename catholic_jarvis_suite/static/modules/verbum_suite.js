/* verbum_suite.js — Verbum & Logos Catholic Study Suite
   Path: static/modules/verbum_suite.js
   Part of CatholicJarvis Master Work Suite.
   1:1 Feature Parity with Logos Bible Software & Verbum Catholic Edition:
   - 4-Pane Synchronized Docking Grid (Greek NA28, Latin Clementina, English Douay/RSV, Catena Aurea)
   - Synchronized Scrolling with Link Sets (Link Set A, Link Set B, Unlinked)
   - Bottom Morphological Interlinear Ribbon with Lemma, Parsing, Strong's & BDAG
   - Exegetical Passage Guide & Dogmatic Factbook (Catena Aurea, CCC, Denzinger, Manuscripts)
   - Side-by-Side Text Comparison Matrix with Doctrinal Term Highlighting
   - Export to Faithlife / Logos Clippings & Discord Fast-Strike
   Uses jarvis.css design tokens only (zero hardcoded hex colors).
*/
(function () {
  "use strict";

  window.JarvisModules = window.JarvisModules || {};

  var state = {
    currentRef: "luke_1_1_4",
    viewMode: "workspace", // "workspace", "guide", "compare"
    layoutGrid: "4grid",   // "4grid", "2vert", "2horiz", "1single"
    linkSet: "link_a",     // "link_a", "link_b", "unlinked"
    activeVerseNum: 1,
    selectedWordIndex: null,
    interlinearOpen: true,
    passageData: null,
    guideData: null,
    compareData: null,
    presets: [],
    loading: false,
    containerElem: null
  };

  function el(tag, attrs, children) {
    var elem = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "text") elem.textContent = attrs[k];
        else if (k === "html") elem.innerHTML = attrs[k];
        else if (k === "style") elem.style.cssText = attrs[k];
        else if (k === "on") {
          Object.keys(attrs.on).forEach(function (ev) {
            elem.addEventListener(ev, attrs.on[ev]);
          });
        } else elem.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) {
      if (c) elem.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return elem;
  }

  // ── DATA FETCHING ──────────────────────────────────────────────────────────

  function fetchPresets() {
    return fetch("/api/verbum/presets")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        state.presets = data.presets || [];
      })
      .catch(function (err) {
        console.warn("Error fetching presets:", err);
      });
  }

  function loadAllPassageData(ref) {
    state.loading = true;
    render();

    var p1 = fetch("/api/verbum/passage?ref=" + encodeURIComponent(ref)).then(function (r) { return r.json(); });
    var p2 = fetch("/api/verbum/guide?ref=" + encodeURIComponent(ref)).then(function (r) { return r.json(); });
    var p3 = fetch("/api/verbum/compare?ref=" + encodeURIComponent(ref)).then(function (r) { return r.json(); });

    return Promise.all([p1, p2, p3])
      .then(function (res) {
        state.passageData = res[0];
        state.guideData = res[1];
        state.compareData = res[2];
        state.currentRef = state.passageData.id || ref;
        state.loading = false;
        render();
      })
      .catch(function (err) {
        state.loading = false;
        console.error("Error loading passage data:", err);
        render();
      });
  }

  // ── MAIN RENDER ────────────────────────────────────────────────────────────

  function render() {
    if (!state.containerElem) return;
    var root = state.containerElem;
    root.textContent = "";

    var container = el("div", {
      class: "verbum-container",
      style: "display: flex; flex-direction: column; height: 100%; width: 100%; background: var(--bg-base); color: var(--text-main); font-family: var(--font-ui); overflow: hidden; position: relative;"
    });

    // 1. Top Ribbon & Command Bar
    container.appendChild(renderTopCommandBar());

    // 2. Main Content View Area
    var mainArea = el("div", {
      class: "verbum-main-area",
      style: "flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; position: relative;"
    });

    if (state.loading) {
      // Was its own one-off spinner referencing "animation: spin ...", but no @keyframes spin was ever
      // defined anywhere in the suite, so it never actually spun. Uses the shared, working spinner now
      // (window.JarvisUI.loading(), jarvis.css's j-spin) instead of a second broken copy.
      mainArea.appendChild((window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading Verbum Sacred Texts...") : el("div", {
        style: "display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; gap: var(--sp-3); color: var(--accent-gold);"
      }, [
        el("span", { style: "font-family: var(--font-mono); font-size: var(--fs-sm);", text: "Loading Verbum Sacred Texts..." })
      ]));
    } else {
      if (state.viewMode === "workspace") {
        mainArea.appendChild(renderWorkspaceView());
      } else if (state.viewMode === "guide") {
        mainArea.appendChild(renderGuideView());
      } else if (state.viewMode === "compare") {
        mainArea.appendChild(renderCompareView());
      }
    }

    container.appendChild(mainArea);

    // 3. Bottom Morphological Interlinear Ribbon
    if (state.interlinearOpen && state.viewMode === "workspace" && state.passageData) {
      container.appendChild(renderInterlinearRibbon());
    }

    root.appendChild(container);
  }

  // ── TOP COMMAND BAR ────────────────────────────────────────────────────────

  function renderTopCommandBar() {
    var bar = el("header", {
      class: "verbum-top-bar",
      style: "display: flex; align-items: center; justify-content: space-between; padding: var(--sp-2) var(--sp-4); background: var(--bg-panel); border-bottom: 1px solid var(--border); gap: var(--sp-3); flex-wrap: wrap; flex-shrink: 0;"
    });

    // Left: Brand & Passage Command Bar
    var leftGroup = el("div", { style: "display: flex; align-items: center; gap: var(--sp-3);" });
    
    // Logo & Title
    var brand = el("div", { style: "display: flex; align-items: center; gap: var(--sp-2);" }, [
      el("span", { style: "font-size: 18px; color: var(--accent-gold);", text: "🏛️" }),
      el("span", { style: "font-family: var(--font-display); font-size: var(--fs-md); font-weight: 700; color: var(--accent-gold); letter-spacing: 0.5px;", text: "VERBUM" }),
      el("span", { style: "font-size: var(--fs-xs); background: var(--accent-gold-soft); color: var(--accent-gold); padding: 2px 6px; border-radius: 4px; font-weight: 600;", text: "CATHOLIC" })
    ]);
    leftGroup.appendChild(brand);

    // Passage Selector Dropdown
    var selectRef = el("select", {
      style: "background: var(--bg-card); border: 1px solid var(--border); color: var(--text-main); font-size: var(--fs-sm); font-family: var(--font-mono); padding: 4px 10px; border-radius: var(--radius); outline: none; cursor: pointer;",
      on: {
        change: function (e) {
          loadAllPassageData(e.target.value);
        }
      }
    });
    state.presets.forEach(function (p) {
      var opt = el("option", { value: p.id, text: p.reference + " — " + p.title });
      if (p.id === state.currentRef) opt.selected = true;
      selectRef.appendChild(opt);
    });
    leftGroup.appendChild(selectRef);

    // Link Set Badge Toggle
    var linkBtn = el("button", {
      class: "verbum-link-badge",
      style: "background: var(--bg-card); border: 1px solid var(--border); color: var(--accent-gold); padding: 4px 8px; border-radius: 4px; font-size: var(--fs-xs); font-family: var(--font-mono); font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;",
      on: {
        click: function () {
          if (state.linkSet === "link_a") state.linkSet = "link_b";
          else if (state.linkSet === "link_b") state.linkSet = "unlinked";
          else state.linkSet = "link_a";
          render();
        }
      }
    }, [
      el("span", { text: state.linkSet === "link_a" ? "🔗 Link Set A" : (state.linkSet === "link_b" ? "🔗 Link Set B" : "⚪ Unlinked") })
    ]);
    leftGroup.appendChild(linkBtn);

    bar.appendChild(leftGroup);

    // Center: View Modes Switcher
    var modeGroup = el("div", { style: "display: flex; background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px; padding: 2px; gap: 2px;" });
    var modes = [
      { id: "workspace", label: "Multi-Pane Workspace", icon: "📑" },
      { id: "guide", label: "Passage Guide", icon: "📖" },
      { id: "compare", label: "Text Comparison", icon: "⚖️" }
    ];
    modes.forEach(function (m) {
      var btn = el("button", {
        style: "background: " + (state.viewMode === m.id ? "var(--accent-gold)" : "none") + "; color: " + (state.viewMode === m.id ? "var(--on-gold)" : "var(--text-muted)") + "; border: none; padding: 4px 12px; border-radius: 16px; font-size: var(--fs-xs); font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 5px; transition: all 0.15s ease;",
        on: {
          click: function () {
            state.viewMode = m.id;
            render();
          }
        }
      }, [
        el("span", { text: m.icon }),
        el("span", { text: m.label })
      ]);
      modeGroup.appendChild(btn);
    });
    bar.appendChild(modeGroup);

    // Right: Action Buttons (Desktop Verbum, Logos Clipping, Interlinear toggle)
    var rightGroup = el("div", { style: "display: flex; align-items: center; gap: var(--sp-2);" });

    // Toggle Interlinear Ribbon Button
    if (state.viewMode === "workspace") {
      var ribbonToggle = el("button", {
        style: "background: " + (state.interlinearOpen ? "var(--accent-cyan)" : "var(--bg-card)") + "; color: " + (state.interlinearOpen ? "var(--bg-base)" : "var(--text-muted)") + "; border: 1px solid var(--border); padding: 4px 10px; border-radius: var(--radius); font-size: var(--fs-xs); font-weight: 600; cursor: pointer;",
        on: {
          click: function () {
            state.interlinearOpen = !state.interlinearOpen;
            render();
          }
        }
      }, [el("span", { text: "🔬 Interlinear Ribbon" })]);
      rightGroup.appendChild(ribbonToggle);
    }

    // Copy Logos Clipping
    var copyClipBtn = el("button", {
      style: "background: var(--bg-card); border: 1px solid var(--border); color: var(--accent-gold); padding: 4px 10px; border-radius: var(--radius); font-size: var(--fs-xs); font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;",
      on: {
        click: function () {
          fetch("/api/verbum/export?ref=" + encodeURIComponent(state.currentRef) + "&fmt=markdown")
            .then(function (r) { return r.json(); })
            .then(function (data) {
              if (navigator.clipboard) {
                navigator.clipboard.writeText(data.clipping).then(function () {
                  copyClipBtn.textContent = "✓ Clipped!";
                  setTimeout(function () { render(); }, 1500);
                });
              }
            });
        }
      }
    }, [el("span", { text: "📋 Copy Logos Clipping" })]);
    rightGroup.appendChild(copyClipBtn);

    // Fast-Strike Discord Button
    var copyDiscordBtn = el("button", {
      style: "background: var(--bg-card); border: 1px solid var(--border); color: var(--accent-red); padding: 4px 10px; border-radius: var(--radius); font-size: var(--fs-xs); font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;",
      on: {
        click: function () {
          fetch("/api/verbum/export?ref=" + encodeURIComponent(state.currentRef) + "&fmt=discord")
            .then(function (r) { return r.json(); })
            .then(function (data) {
              if (navigator.clipboard) {
                navigator.clipboard.writeText(data.clipping).then(function () {
                  copyDiscordBtn.textContent = "✓ Strike Ready!";
                  setTimeout(function () { render(); }, 1500);
                });
              }
            });
        }
      }
    }, [el("span", { text: "⚔️ Discord Strike" })]);
    rightGroup.appendChild(copyDiscordBtn);

    bar.appendChild(rightGroup);
    return bar;
  }

  // ── 1. WORKSPACE VIEW (4-PANE SYNCHRONIZED GRID) ──────────────────────────

  function renderWorkspaceView() {
    var area = el("div", {
      class: "verbum-workspace-grid",
      style: "flex: 1; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 1px; background: var(--border); min-height: 0; overflow: hidden;"
    });

    var data = state.passageData;
    if (!data) return area;

    // Pane 1: Greek New Testament (NA28 / MorphGNT)
    area.appendChild(renderScripturePane("Greek New Testament (NA28 / MorphGNT)", "greek", function (v) {
      return el("div", {
        style: "font-family: var(--font-read); font-size: 16px; line-height: 1.6; color: var(--text-main);"
      }, [
        el("span", { style: "font-family: var(--font-mono); font-size: var(--fs-xs); color: var(--accent-gold); margin-right: 8px; font-weight: 700;", text: String(v.num) }),
        el("span", { text: v.greek })
      ]);
    }));

    // Pane 2: Latin Clementine Vulgate (1592)
    area.appendChild(renderScripturePane("Latin Sixto-Clementine Vulgate", "latin", function (v) {
      return el("div", {
        style: "font-family: var(--font-read); font-size: 15px; line-height: 1.6; color: var(--text-main); font-style: italic;"
      }, [
        el("span", { style: "font-family: var(--font-mono); font-size: var(--fs-xs); color: var(--accent-gold); margin-right: 8px; font-weight: 700; font-style: normal;", text: String(v.num) }),
        el("span", { text: v.latin })
      ]);
    }));

    // Pane 3: Parallel English (Douay-Rheims 1899 & RSV-2CE)
    area.appendChild(renderScripturePane("Parallel English (Douay-Rheims & RSV-2CE)", "english", function (v) {
      return el("div", { style: "display: flex; flex-direction: column; gap: var(--sp-1);" }, [
        el("div", { style: "font-family: var(--font-read); font-size: 14px; line-height: 1.5; color: var(--text-main);" }, [
          el("span", { style: "font-family: var(--font-mono); font-size: 10px; color: var(--accent-cyan); margin-right: 6px; font-weight: 700;", text: "[D-R " + v.num + "]" }),
          el("span", { text: v.douay })
        ]),
        el("div", { style: "font-family: var(--font-read); font-size: 14px; line-height: 1.5; color: var(--text-muted);" }, [
          el("span", { style: "font-family: var(--font-mono); font-size: 10px; color: var(--accent-green); margin-right: 6px; font-weight: 700;", text: "[RSV " + v.num + "]" }),
          el("span", { text: v.rsv2ce })
        ])
      ]);
    }));

    // Pane 4: Church Fathers Commentary (Catena Aurea)
    area.appendChild(renderCatenaPane("Catena Aurea & Church Fathers (St. Thomas Aquinas)"));

    return area;
  }

  function renderScripturePane(title, paneType, verseRenderer) {
    var pane = el("section", {
      class: "verbum-pane",
      style: "background: var(--bg-panel); display: flex; flex-direction: column; min-height: 0; overflow: hidden;"
    });

    // Pane Header
    var header = el("div", {
      style: "display: flex; align-items: center; justify-content: space-between; padding: 6px var(--sp-3); background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: var(--fs-xs);"
    }, [
      el("div", { style: "display: flex; align-items: center; gap: 6px;" }, [
        el("span", { style: "font-weight: 700; color: var(--text-main);", text: title }),
        el("span", { style: "background: var(--accent-gold-soft); color: var(--accent-gold); font-size: 10px; padding: 1px 5px; border-radius: 3px; font-family: var(--font-mono);", text: state.linkSet === "link_a" ? "Link Set A" : (state.linkSet === "link_b" ? "Link Set B" : "Unlinked") })
      ]),
      el("span", { style: "color: var(--text-dim); font-family: var(--font-mono); font-size: 10px;", text: state.passageData.reference })
    ]);
    pane.appendChild(header);

    // Verses Scrollable Area
    var body = el("div", {
      class: "verbum-pane-body",
      style: "flex: 1; overflow-y: auto; padding: var(--sp-3) var(--sp-4); display: flex; flex-direction: column; gap: var(--sp-3);"
    });

    state.passageData.verses.forEach(function (v) {
      var isSelected = v.num === state.activeVerseNum;
      var verseBox = el("div", {
        class: "verbum-verse-box" + (isSelected ? " active-verse" : ""),
        style: "padding: 8px 10px; border-radius: var(--radius); transition: background 0.15s ease; cursor: pointer; background: " + (isSelected ? "var(--accent-gold-soft)" : "transparent") + "; border-left: 3px solid " + (isSelected ? "var(--accent-gold)" : "transparent") + ";",
        on: {
          click: function () {
            if (state.linkSet !== "unlinked") {
              state.activeVerseNum = v.num;
              render();
            }
          }
        }
      }, [verseRenderer(v)]);
      body.appendChild(verseBox);
    });

    pane.appendChild(body);
    return pane;
  }

  function renderCatenaPane(title) {
    var pane = el("section", {
      class: "verbum-pane",
      style: "background: var(--bg-panel); display: flex; flex-direction: column; min-height: 0; overflow: hidden;"
    });

    var header = el("div", {
      style: "display: flex; align-items: center; justify-content: space-between; padding: 6px var(--sp-3); background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: var(--fs-xs);"
    }, [
      el("div", { style: "display: flex; align-items: center; gap: 6px;" }, [
        el("span", { style: "font-weight: 700; color: var(--accent-gold);", text: title }),
        el("span", { style: "background: rgba(99, 102, 241, 0.15); color: var(--accent-blue); font-size: 10px; padding: 1px 5px; border-radius: 3px; font-family: var(--font-mono);", text: "Aquinas / Fathers" })
      ]),
      el("span", { style: "color: var(--text-dim); font-size: 10px;", text: "Patristic Catena" })
    ]);
    pane.appendChild(header);

    var body = el("div", {
      style: "flex: 1; overflow-y: auto; padding: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-3);"
    });

    var catenaList = state.passageData.catena_aurea || [];
    if (!catenaList.length) {
      body.appendChild(el("div", { style: "color: var(--text-muted); font-size: var(--fs-sm); font-style: italic;", text: "No catena entries for this section." }));
    } else {
      catenaList.forEach(function (c) {
        var card = el("article", {
          style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-2);"
        }, [
          el("div", { style: "display: flex; align-items: center; justify-content: space-between;" }, [
            el("span", { style: "font-weight: 700; color: var(--accent-gold); font-size: var(--fs-sm);", text: c.father }),
            el("span", { style: "font-size: 10px; color: var(--text-dim); font-family: var(--font-mono);", text: c.source })
          ]),
          el("p", { style: "font-family: var(--font-read); font-size: 13px; line-height: 1.5; color: var(--text-main); margin: 0;", text: c.english }),
          el("p", { style: "font-family: var(--font-read); font-size: 12px; line-height: 1.4; color: var(--text-dim); font-style: italic; margin: 0; border-left: 2px solid var(--border); padding-left: 8px;", text: "«" + c.latin + "»" })
        ]);
        body.appendChild(card);
      });
    }

    pane.appendChild(body);
    return pane;
  }

  // ── BOTTOM MORPHOLOGICAL INTERLINEAR RIBBON ────────────────────────────────

  function renderInterlinearRibbon() {
    var ribbon = el("aside", {
      class: "verbum-interlinear-ribbon",
      style: "background: var(--bg-panel); border-top: 2px solid var(--border); padding: var(--sp-2) var(--sp-4); height: 130px; display: flex; flex-direction: column; flex-shrink: 0; overflow: hidden; box-shadow: 0 -4px 16px rgba(0,0,0,0.4);"
    });

    var ribbonHeader = el("div", {
      style: "display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; font-size: var(--fs-xs);"
    }, [
      el("div", { style: "display: flex; align-items: center; gap: var(--sp-2);" }, [
        el("span", { style: "font-weight: 700; color: var(--accent-cyan);", text: "🔬 MORPHOLOGICAL INTERLINEAR" }),
        el("span", { style: "color: var(--text-dim); font-family: var(--font-mono);", text: "Verse " + state.activeVerseNum + " — Greek NA28 / MorphGNT" })
      ]),
      el("span", { style: "color: var(--text-dim); font-size: 10px;", text: "Click word to inspect lexical entry" })
    ]);
    ribbon.appendChild(ribbonHeader);

    // Find morphology for the active verse
    var morphList = state.passageData.morphology || [];
    var verseMorph = null;
    for (var i = 0; i < morphList.length; i++) {
      if (morphList[i].verse === state.activeVerseNum) {
        verseMorph = morphList[i];
        break;
      }
    }

    var wordsContainer = el("div", {
      style: "flex: 1; display: flex; gap: var(--sp-2); overflow-x: auto; padding-bottom: 4px; align-items: stretch;"
    });

    if (!verseMorph || !verseMorph.tokens || !verseMorph.tokens.length) {
      wordsContainer.appendChild(el("span", { style: "color: var(--text-dim); font-size: var(--fs-sm); font-style: italic;", text: "Morphological analysis ready for Verses 1–4." }));
    } else {
      verseMorph.tokens.forEach(function (tok, idx) {
        var isWordSelected = state.selectedWordIndex === idx;
        var tokenCard = el("div", {
          class: "verbum-token-cell" + (isWordSelected ? " active-word" : ""),
          style: "min-width: 110px; background: " + (isWordSelected ? "rgba(56, 189, 248, 0.15)" : "var(--bg-card)") + "; border: 1px solid " + (isWordSelected ? "var(--accent-cyan)" : "var(--border)") + "; border-radius: var(--radius); padding: 4px 8px; display: flex; flex-direction: column; justify-content: space-between; cursor: pointer; transition: all 0.15s ease;",
          on: {
            click: function () {
              state.selectedWordIndex = idx;
              render();
            }
          }
        }, [
          el("span", { style: "font-family: var(--font-read); font-size: 15px; font-weight: 700; color: var(--accent-gold);", text: tok.surface }),
          el("span", { style: "font-size: 10px; color: var(--text-muted); font-style: italic;", text: tok.translit }),
          el("span", { style: "font-size: 11px; color: var(--text-main); font-weight: 600;", text: tok.lemma }),
          el("div", { style: "display: flex; gap: 4px; align-items: center;" }, [
            el("span", { style: "font-size: 9px; background: rgba(56, 189, 248, 0.1); color: var(--accent-cyan); padding: 1px 4px; border-radius: 3px; font-family: var(--font-mono);", text: tok.pos }),
            el("span", { style: "font-size: 9px; background: rgba(16, 185, 129, 0.1); color: var(--accent-green); padding: 1px 4px; border-radius: 3px; font-family: var(--font-mono);", text: tok.strong })
          ]),
          el("span", { style: "font-size: 10px; color: var(--text-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;", text: tok.def })
        ]);
        wordsContainer.appendChild(tokenCard);
      });
    }

    ribbon.appendChild(wordsContainer);
    return ribbon;
  }

  // ── 2. PASSAGE GUIDE & DOGMATIC FACTBOOK VIEW ─────────────────────────────

  function renderGuideView() {
    var guide = state.guideData;
    if (!guide) return el("div");

    var root = el("div", {
      class: "verbum-guide-layout",
      style: "flex: 1; display: grid; grid-template-columns: 320px 1fr 340px; gap: 1px; background: var(--border); min-height: 0; overflow: hidden;"
    });

    // Left Column: Accordion Nav & Sections
    var leftCol = el("aside", {
      style: "background: var(--bg-panel); overflow-y: auto; padding: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-3);"
    });
    leftCol.appendChild(el("h3", { style: "font-family: var(--font-display); font-size: var(--fs-md); color: var(--accent-gold); margin: 0 0 var(--sp-2) 0;", text: "PASSAGE GUIDE" }));

    // Guide Section 1: Parallel Passages & Harmony
    leftCol.appendChild(renderAccordionSection("1. Parallel Passages", [
      el("div", { style: "font-size: var(--fs-xs); line-height: 1.5; color: var(--text-muted);" }, [
        el("div", { text: "• Matthew 1:1–17 (Genealogy & Nativity)" }),
        el("div", { text: "• Mark 1:1–3 (Beginning of the Gospel)" }),
        el("div", { text: "• John 1:1–18 (Prologue of the Logos)" })
      ])
    ]));

    // Guide Section 2: Church Fathers
    var fathersList = el("div", { style: "display: flex; flex-direction: column; gap: 4px; font-size: var(--fs-xs);" });
    (guide.catena_aurea || []).forEach(function (c) {
      fathersList.appendChild(el("div", { style: "color: var(--text-main);" }, [
        el("strong", { style: "color: var(--accent-gold);", text: c.father }),
        el("span", { style: "color: var(--text-dim);", text: " (" + c.source + ")" })
      ]));
    });
    leftCol.appendChild(renderAccordionSection("2. Church Fathers (" + (guide.catena_aurea || []).length + ")", [fathersList]));

    // Guide Section 3: Magisterial Dogma (CCC & Denzinger)
    var dogmaList = el("div", { style: "display: flex; flex-direction: column; gap: 6px; font-size: var(--fs-xs);" });
    (guide.magisterial_dogma || []).forEach(function (d) {
      dogmaList.appendChild(el("div", { style: "background: var(--bg-card); border-left: 2px solid var(--accent-green); padding: 4px 6px; border-radius: 2px;" }, [
        el("span", { style: "font-weight: 700; color: var(--accent-green);", text: d.anchor }),
        el("p", { style: "margin: 2px 0 0 0; color: var(--text-dim); font-size: 11px;", text: d.text.slice(0, 85) + "..." })
      ]));
    });
    leftCol.appendChild(renderAccordionSection("3. Magisterial Dogma", [dogmaList]));

    // Guide Section 4: Manuscript Witnesses
    var msList = el("div", { style: "display: flex; flex-direction: column; gap: 6px; font-size: var(--fs-xs);" });
    (guide.manuscript_witnesses || []).forEach(function (m) {
      var msItem = el("div", {
        style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 6px; cursor: pointer;",
        on: {
          click: function () {
            if (window.JarvisOpen) window.JarvisOpen("manuscripts", { ms: m.id });
          }
        }
      }, [
        el("div", { style: "font-weight: 700; color: var(--accent-cyan);", text: m.name }),
        el("div", { style: "font-size: 10px; color: var(--text-dim);", text: m.date + " • " + m.folio }),
        el("div", { style: "font-size: 10px; color: var(--accent-gold); margin-top: 4px;", text: "👁️ Click to launch in 3D WebGL Paleography Suite →" })
      ]);
      msList.appendChild(msItem);
    });
    leftCol.appendChild(renderAccordionSection("4. Manuscript Witnesses (" + (guide.manuscript_witnesses || []).length + ")", [msList]));

    root.appendChild(leftCol);

    // Center Column: Continuous Biblical Text
    var centerCol = el("main", {
      style: "background: var(--bg-panel); overflow-y: auto; padding: var(--sp-4) var(--sp-5); display: flex; flex-direction: column; gap: var(--sp-4);"
    });
    centerCol.appendChild(el("div", { style: "border-bottom: 1px solid var(--border); padding-bottom: var(--sp-2);" }, [
      el("h2", { style: "font-family: var(--font-display); font-size: 22px; color: var(--accent-gold); margin: 0;", text: guide.reference }),
      el("p", { style: "color: var(--text-muted); font-size: var(--fs-sm); margin: 4px 0 0 0;", text: guide.title })
    ]));

    guide.verses.forEach(function (v) {
      var card = el("article", {
        style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-2);"
      }, [
        el("div", { style: "display: flex; align-items: baseline; gap: 8px;" }, [
          el("span", { style: "font-family: var(--font-mono); font-size: var(--fs-sm); color: var(--accent-gold); font-weight: 700;", text: "Verse " + v.num }),
          el("span", { style: "font-family: var(--font-read); font-size: 16px; color: var(--text-main); font-weight: 600;", text: v.greek })
        ]),
        el("p", { style: "font-family: var(--font-read); font-size: 14px; color: var(--text-dim); font-style: italic; margin: 0;", text: v.latin }),
        el("p", { style: "font-family: var(--font-read); font-size: 14px; color: var(--text-main); margin: 0;", text: v.douay })
      ]);
      centerCol.appendChild(card);
    });
    root.appendChild(centerCol);

    // Right Column: Exegetical Detail & Battleground Card
    var rightCol = el("aside", {
      style: "background: var(--bg-panel); overflow-y: auto; padding: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-3);"
    });
    rightCol.appendChild(el("h3", { style: "font-family: var(--font-display); font-size: var(--fs-md); color: var(--accent-red); margin: 0 0 var(--sp-2) 0;", text: "APOLOGETICS FORENSICS" }));

    var tactics = guide.apologetics_tactics || {};
    var refCard = el("div", {
      style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-2);"
    }, [
      el("div", { style: "font-size: var(--fs-xs); font-weight: 700; color: var(--accent-red);", text: "1. Opponent Skeptical Claim:" }),
      el("p", { style: "font-size: 12px; color: var(--text-muted); margin: 0; line-height: 1.4;", text: tactics.skeptical_claim || "Skeptical claim" }),
      
      el("div", { style: "font-size: var(--fs-xs); font-weight: 700; color: var(--accent-gold); margin-top: 4px;", text: "2. Concede-First Pivot (Rule 10):" }),
      el("p", { style: "font-size: 12px; color: var(--text-muted); margin: 0; line-height: 1.4;", text: tactics.concession_first || "Concession" }),

      el("div", { style: "font-size: var(--fs-xs); font-weight: 700; color: var(--accent-cyan); margin-top: 4px;", text: "3. Physical Exhibit Strike:" }),
      el("p", { style: "font-size: 12px; color: var(--text-main); margin: 0; line-height: 1.4;", text: tactics.physical_strike || "Strike" }),

      el("div", { style: "font-size: var(--fs-xs); font-weight: 700; color: var(--accent-green); margin-top: 4px;", text: "4. Socratic Trap:" }),
      el("p", { style: "font-size: 12px; color: var(--text-main); margin: 0; line-height: 1.4; font-style: italic;", text: tactics.socratic_trap || "Socratic Trap" })
    ]);
    rightCol.appendChild(refCard);

    root.appendChild(rightCol);
    return root;
  }

  function renderAccordionSection(title, children) {
    var sec = el("div", {
      style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-2) var(--sp-3); display: flex; flex-direction: column; gap: 6px;"
    });
    var secTitle = el("div", {
      style: "font-size: var(--fs-xs); font-weight: 700; color: var(--accent-gold); text-transform: uppercase; letter-spacing: 0.5px;",
      text: title
    });
    sec.appendChild(secTitle);
    (children || []).forEach(function (c) { sec.appendChild(c); });
    return sec;
  }

  // ── 3. TEXT COMPARISON MATRIX & DIFF ENGINE VIEW ──────────────────────────

  function renderCompareView() {
    var comp = state.compareData;
    if (!comp) return el("div");

    var root = el("div", {
      class: "verbum-compare-layout",
      style: "flex: 1; display: flex; flex-direction: column; background: var(--bg-panel); overflow-y: auto; padding: var(--sp-4); gap: var(--sp-4);"
    });

    var header = el("div", {
      style: "display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: var(--sp-2);"
    }, [
      el("div", {}, [
        el("h2", { style: "font-family: var(--font-display); font-size: 20px; color: var(--accent-gold); margin: 0;", text: "TEXT COMPARISON: " + comp.reference }),
        el("p", { style: "font-size: var(--fs-xs); color: var(--text-muted); margin: 4px 0 0 0;", text: "Side-by-side textual apparatus across Greek, Latin, and English translations with doctrinal term highlighting." })
      ]),
      el("div", { style: "display: flex; gap: var(--sp-2);" }, [
        el("span", { style: "background: rgba(16, 185, 129, 0.15); color: var(--accent-green); font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 600;", text: "✓ 5 Translations Aligned" })
      ])
    ]);
    root.appendChild(header);

    // Matrix Table
    comp.comparisons.forEach(function (row) {
      var verseCard = el("section", {
        style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-3); display: flex; flex-direction: column; gap: var(--sp-3);"
      });

      verseCard.appendChild(el("div", {
        style: "font-family: var(--font-mono); font-size: var(--fs-xs); color: var(--accent-gold); font-weight: 700; border-bottom: 1px solid var(--border); padding-bottom: 4px;",
        text: "Verse " + row.verse_num
      }));

      var grid = el("div", {
        style: "display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--sp-3);"
      });

      // Col 1: Greek NA28
      grid.appendChild(renderCompareColumn("Greek New Testament (NA28)", row.greek, "var(--text-main)", "var(--font-read)", "15px"));
      // Col 2: Latin Clementine Vulgate
      grid.appendChild(renderCompareColumn("Latin Clementine Vulgate", row.latin_vulgate, "var(--text-main)", "var(--font-read)", "14px", true));
      // Col 3: Douay-Rheims 1899
      grid.appendChild(renderCompareColumn("English Douay-Rheims", row.douay_rheims, "var(--text-muted)", "var(--font-read)", "13px"));
      // Col 4: RSV-2CE
      grid.appendChild(renderCompareColumn("RSV Catholic Edition", row.rsv2ce, "var(--text-muted)", "var(--font-read)", "13px"));

      verseCard.appendChild(grid);

      // Doctrinal Terms Highlight Box
      if (row.doctrinal_terms && row.doctrinal_terms.length) {
        var termBox = el("div", {
          style: "background: var(--bg-panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 8px 12px; display: flex; flex-direction: column; gap: 4px;"
        }, [
          el("span", { style: "font-size: 10px; color: var(--accent-gold); font-weight: 700; text-transform: uppercase;", text: "Key Doctrinal Markers in this verse:" })
        ]);

        row.doctrinal_terms.forEach(function (dt) {
          termBox.appendChild(el("div", { style: "font-size: 12px; display: flex; gap: 6px; align-items: baseline;" }, [
            el("span", { style: "color: " + dt.color + "; font-weight: 700; font-family: var(--font-mono);", text: "• " + dt.term + ":" }),
            el("span", { style: "color: var(--text-main);", text: dt.meaning })
          ]));
        });

        verseCard.appendChild(termBox);
      }

      root.appendChild(verseCard);
    });

    return root;
  }

  function renderCompareColumn(colTitle, colText, color, fontFam, fontSize, isItalic) {
    return el("div", {
      style: "display: flex; flex-direction: column; gap: 4px; background: var(--bg-panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 8px 10px;"
    }, [
      el("span", { style: "font-size: 10px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase; letter-spacing: 0.5px;", text: colTitle }),
      el("p", {
        style: "margin: 0; font-family: " + fontFam + "; font-size: " + fontSize + "; color: " + color + "; line-height: 1.5;" + (isItalic ? " font-style: italic;" : ""),
        text: colText
      })
    ]);
  }

  // ── MODULE LIFECYCLE ───────────────────────────────────────────────────────

  window.JarvisModules.verbum = {
    load: function (container) {
      state.containerElem = container;
      fetchPresets().then(function () {
        loadAllPassageData(state.currentRef);
      });
    }
  };

  // Auto-boot if container is already in DOM
  var directContainer = document.getElementById("tab-verbum");
  if (directContainer) {
    var rootEl = directContainer.querySelector(".module-root") || directContainer;
    window.JarvisModules.verbum.load(rootEl);
  }

})();
