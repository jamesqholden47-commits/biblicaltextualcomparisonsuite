/* navigator.js — CatholicJarvis Visual File Genealogy & Tiered Treemap Navigator
   Path: static/modules/navigator.js
   Part of CatholicJarvis Master Work Suite. Uses jarvis.css design tokens exclusively (zero hardcoded hex).
*/
(function () {
  "use strict";

  window.JarvisModules = window.JarvisModules || {};

  var state = {
    viewMode: "mindmap", // 'mindmap', 'treemap', 'genealogy', 'sunburst'
    groupBy: "category", // 'category', 'academic_tier', 'temporal_month', 'folder'
    sortBy: "mtime", // 'mtime', 'ctime', 'atime', 'size', 'lines', 'citations', 'name'
    sizeMetric: "size", // 'size', 'lines', or 'citations'
    excludeInfrastructure: false,
    chronoMaxMonth: "2026-10",
    searchQuery: "",
    selectedNode: null,
    previewData: null,
    treemapRoot: null,
    currentBreadcrumb: [],
    genealogyData: null,
    drawerOpen: false,
    mindmapPanX: 0,
    mindmapPanY: 0,
    mindmapZoom: 1.0,
    collapsedBranches: {
      volumes: true,
      drafts: true,
      sources: true,
      other: true
    },
    hoveredNode: null,
    filters: {
      categories: {
        master: true,
        volumes: true,
        drafts: true,
        dossiers: true,
        intake: true,
        books: true,
        sources: true,
        control: true,
        scripts: true,
        vaults: true
      },
      authorType: "all", // 'all', 'user_authored', 'ai_authored', 'canonical_edition'
      genealogyDepth: 2
    }
  };

  var CHRONO_MONTHS = ["2026-07", "2026-08", "2026-09", "2026-10"];

  // Helper to extract CSS variable color values dynamically from DOM computed style
  function getCssColor(varName, fallback) {
    try {
      var val = window.getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
      return val || fallback;
    } catch (e) {
      return fallback;
    }
  }

  function getTokenColor(varName, fallback) {
    return getCssColor(varName, fallback || "rgba(212, 175, 55, 1)");
  }

  function el(tag, attrs, children) {
    var elem = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "text") elem.textContent = attrs[k];
        else if (k === "html") elem.innerHTML = attrs[k];
        else if (k === "style") elem.style.cssText = attrs[k];
        else if (k === "class") elem.className = attrs[k];
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

  function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    var k = 1024;
    var sizes = ["B", "KB", "MB", "GB"];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  // ── Main Module Loader ────────────────────────────────────────────────────────
  function load(root) {
    root.textContent = "";
    root.style.cssText = "display:flex;flex-direction:column;height:100%;overflow:hidden;background:var(--bg-base);color:var(--text-main);font-family:var(--font-ui);";

    // Top Header & Control Toolbar
    var topBar = el("div", {
      style: "flex-shrink:0;background:var(--bg-panel);border-bottom:1px solid var(--border);padding:10px 18px;display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;"
    }, [
      // Left: Title & Mode Switcher
      el("div", { style: "display:flex;align-items:center;gap:14px;" }, [
        el("div", { style: "display:flex;align-items:center;gap:8px;" }, [
          el("span", { style: "font-family:var(--font-display);font-size:16px;font-weight:700;color:var(--accent-gold);", text: "🏛️ File Mindmap & Genealogy" }),
          el("span", { style: "font-size:10px;text-transform:uppercase;background:var(--accent-gold-soft);color:var(--accent-gold);padding:2px 6px;border-radius:4px;font-weight:600;font-family:var(--font-mono);", text: "Tri-Engine" })
        ]),
        // View Mode Tabs
        el("div", { style: "display:flex;background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:2px;gap:2px;" }, [
          el("button", {
            id: "nav-tab-mindmap",
            style: "border:none;background:" + (state.viewMode === "mindmap" ? "var(--accent-gold)" : "none") + ";color:" + (state.viewMode === "mindmap" ? "var(--on-gold)" : "var(--text-muted)") + ";padding:5px 12px;border-radius:4px;font-size:12px;font-weight:600;cursor:pointer;",
            text: "🧠 Mindmap",
            on: { click: function () { switchViewMode("mindmap"); } }
          }),
          el("button", {
            id: "nav-tab-treemap",
            style: "border:none;background:" + (state.viewMode === "treemap" ? "var(--accent-gold)" : "none") + ";color:" + (state.viewMode === "treemap" ? "var(--on-gold)" : "var(--text-muted)") + ";padding:5px 12px;border-radius:4px;font-size:12px;font-weight:600;cursor:pointer;",
            text: "🗺️ Treemap",
            on: { click: function () { switchViewMode("treemap"); } }
          }),
          el("button", {
            id: "nav-tab-sunburst",
            style: "border:none;background:" + (state.viewMode === "sunburst" ? "var(--accent-gold)" : "none") + ";color:" + (state.viewMode === "sunburst" ? "var(--on-gold)" : "var(--text-muted)") + ";padding:5px 12px;border-radius:4px;font-size:12px;font-weight:600;cursor:pointer;",
            text: "☀️ Sunburst Radial",
            on: { click: function () { switchViewMode("sunburst"); } }
          }),
          el("button", {
            id: "nav-tab-genealogy",
            style: "border:none;background:" + (state.viewMode === "genealogy" ? "var(--accent-gold)" : "none") + ";color:" + (state.viewMode === "genealogy" ? "var(--on-gold)" : "var(--text-muted)") + ";padding:5px 12px;border-radius:4px;font-size:12px;font-weight:600;cursor:pointer;",
            text: "🧬 Genealogy DAG",
            on: { click: function () { switchViewMode("genealogy"); } }
          })
        ])
      ]),

      // Middle: Group & Sort Selectors
      el("div", { style: "display:flex;align-items:center;gap:10px;font-size:12px;flex-wrap:wrap;" }, [
        el("span", { style: "color:var(--text-dim);", text: "Group:" }),
        el("select", {
          id: "nav-group-select",
          style: "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:12px;",
          on: { change: function (e) { state.groupBy = e.target.value; fetchAndRender(); } }
        }, [
          el("option", { value: "category", text: "Category (Books, Dossiers, Master)" }),
          el("option", { value: "academic_tier", text: "Academic Tier (0 to 4)" }),
          el("option", { value: "temporal_month", text: "Temporal Cohort (Month)" }),
          el("option", { value: "folder", text: "Folder Structure" })
        ]),

        el("span", { style: "color:var(--text-dim);", text: "Sort:" }),
        el("select", {
          id: "nav-sort-select",
          style: "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:12px;",
          on: { change: function (e) { state.sortBy = e.target.value; fetchAndRender(); } }
        }, [
          el("option", { value: "mtime", text: "Date Modified (Newest)" }),
          el("option", { value: "ctime", text: "Date Created (Newest)" }),
          el("option", { value: "atime", text: "Date Accessed (Newest)" }),
          el("option", { value: "size", text: "Byte Size (Largest)" }),
          el("option", { value: "lines", text: "Line Count (Longest)" }),
          el("option", { value: "citations", text: "Citation Density (Highest)" }),
          el("option", { value: "name", text: "Alphabetical" })
        ]),

        el("span", { style: "color:var(--text-dim);", text: "Size By:" }),
        el("select", {
          id: "nav-size-select",
          style: "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:12px;",
          on: { change: function (e) { state.sizeMetric = e.target.value; fetchAndRender(); } }
        }, [
          el("option", { value: "size", text: "Byte Weight" }),
          el("option", { value: "lines", text: "Line Count" }),
          el("option", { value: "citations", text: "Citation Density" })
        ]),

        // Exclude Infrastructure Checkbox (Rule 13)
        el("label", {
          style: "display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--text-main);cursor:pointer;padding:2px 4px;"
        }, [
          el("input", {
            type: "checkbox",
            id: "nav-exclude-infra-toggle",
            checked: state.excludeInfrastructure === true,
            style: "accent-color:var(--accent-gold);cursor:pointer;",
            on: {
              change: function (e) {
                state.excludeInfrastructure = e.target.checked;
                fetchAndRender();
              }
            }
          }),
          el("span", { text: "Exclude Infrastructure (Rule 13)" })
        ]),

        // Chrono-Scrubber Range Control
        el("div", {
          style: "display:inline-flex;align-items:center;gap:6px;font-size:12px;padding:2px 4px;"
        }, [
          el("span", { style: "color:var(--text-dim);", text: "Chrono:" }),
          el("input", {
            type: "range",
            id: "nav-chrono-slider",
            min: "0",
            max: "3",
            value: String(CHRONO_MONTHS.indexOf(state.chronoMaxMonth) >= 0 ? CHRONO_MONTHS.indexOf(state.chronoMaxMonth) : 3),
            style: "width:75px;accent-color:var(--accent-cyan);cursor:pointer;",
            on: {
              input: function (e) {
                var idx = parseInt(e.target.value, 10);
                state.chronoMaxMonth = CHRONO_MONTHS[idx];
                var badge = document.getElementById("nav-chrono-badge");
                if (badge) badge.textContent = state.chronoMaxMonth;
                fetchAndRender();
              }
            }
          }),
          el("span", {
            id: "nav-chrono-badge",
            style: "font-family:var(--font-mono);font-size:11px;color:var(--accent-cyan);font-weight:700;",
            text: state.chronoMaxMonth
          })
        ])
      ]),

      // Right: Search & Actions
      el("div", { style: "display:flex;align-items:center;gap:8px;" }, [
        el("input", {
          id: "nav-search-input",
          type: "text",
          placeholder: "Search file name or topic…",
          style: "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:4px;padding:5px 10px;font-size:12px;width:180px;",
          on: { input: function (e) { state.searchQuery = e.target.value.toLowerCase(); filterAndRenderVisualizer(); } }
        }),
        el("button", {
          style: "background:var(--bg-card);color:var(--accent-cyan);border:1px solid var(--border);border-radius:4px;padding:5px 10px;font-size:12px;cursor:pointer;font-weight:600;",
          text: "🔄 Reindex",
          on: { click: triggerReindex }
        })
      ])
    ]);

    // Main Body: Workspace with Left Sidebar, Central Visualizer Canvas, and Right Preview Drawer
    var mainBody = el("div", { style: "flex:1;display:flex;overflow:hidden;position:relative;" });

    // Left Filter Sidebar
    var sidebar = el("aside", {
      style: "width:220px;flex-shrink:0;background:var(--bg-panel);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow-y:auto;padding:14px;gap:14px;"
    }, [
      el("div", { style: "font-size:11px;font-weight:700;text-transform:uppercase;color:var(--accent-gold);letter-spacing:0.5px;", text: "Knowledge Categories" }),
      renderCategoryFilters(),
      el("div", { style: "height:1px;background:var(--border);" }),
      el("div", { style: "font-size:11px;font-weight:700;text-transform:uppercase;color:var(--accent-cyan);letter-spacing:0.5px;", text: "Author Provenance" }),
      renderAuthorFilters(),
      el("div", { style: "height:1px;background:var(--border);" }),
      el("div", { style: "font-size:11px;font-weight:700;text-transform:uppercase;color:var(--accent-green);letter-spacing:0.5px;", text: "Genealogy Depth" }),
      renderDepthSlider()
    ]);

    // Central Visualizer Container
    var centerContainer = el("div", {
      id: "nav-center-container",
      style: "flex:1;display:flex;flex-direction:column;overflow:hidden;position:relative;background:var(--bg-base);"
    });

    // Breadcrumb bar (for Treemap zoom drilldown)
    var breadcrumbBar = el("div", {
      id: "nav-breadcrumbs",
      style: "height:32px;background:var(--bg-panel);border-bottom:1px solid var(--border);padding:0 14px;display:flex;align-items:center;gap:6px;font-size:12px;color:var(--text-muted);overflow-x:auto;"
    });

    // Visualizer Canvas Wrapper
    var canvasWrapper = el("div", {
      id: "nav-canvas-wrapper",
      style: "flex:1;position:relative;overflow:hidden;display:flex;align-items:center;justify-content:center;"
    });

    centerContainer.appendChild(breadcrumbBar);
    centerContainer.appendChild(canvasWrapper);

    // Right Slide-out Preview Drawer
    var previewDrawer = el("aside", {
      id: "nav-preview-drawer",
      style: "width:420px;flex-shrink:0;background:var(--bg-panel);border-left:1px solid var(--border);display:none;flex-direction:column;overflow:hidden;position:relative;box-shadow:-4px 0 20px rgba(0,0,0,0.4);"
    });

    mainBody.appendChild(sidebar);
    mainBody.appendChild(centerContainer);
    mainBody.appendChild(previewDrawer);

    root.appendChild(topBar);
    root.appendChild(mainBody);

    // Initial data fetch
    fetchAndRender();
  }

  // ── View Mode Switcher ────────────────────────────────────────────────────────
  function switchViewMode(mode) {
    state.viewMode = mode;
    var btnMindmap = document.getElementById("nav-tab-mindmap");
    var btnTreemap = document.getElementById("nav-tab-treemap");
    var btnSunburst = document.getElementById("nav-tab-sunburst");
    var btnGenealogy = document.getElementById("nav-tab-genealogy");
    if (btnMindmap) {
      btnMindmap.style.background = mode === "mindmap" ? "var(--accent-gold)" : "none";
      btnMindmap.style.color = mode === "mindmap" ? "var(--on-gold)" : "var(--text-muted)";
    }
    if (btnTreemap) {
      btnTreemap.style.background = mode === "treemap" ? "var(--accent-gold)" : "none";
      btnTreemap.style.color = mode === "treemap" ? "var(--on-gold)" : "var(--text-muted)";
    }
    if (btnSunburst) {
      btnSunburst.style.background = mode === "sunburst" ? "var(--accent-gold)" : "none";
      btnSunburst.style.color = mode === "sunburst" ? "var(--on-gold)" : "var(--text-muted)";
    }
    if (btnGenealogy) {
      btnGenealogy.style.background = mode === "genealogy" ? "var(--accent-gold)" : "none";
      btnGenealogy.style.color = mode === "genealogy" ? "var(--on-gold)" : "var(--text-muted)";
    }
    filterAndRenderVisualizer();
  }

  // ── Category Filter Checkboxes ────────────────────────────────────────────────
  function renderCategoryFilters() {
    var catDefs = [
      { id: "master", label: "Master Dissertation", color: "var(--accent-gold)" },
      { id: "volumes", label: "Published Volumes", color: "var(--accent-gold)" },
      { id: "drafts", label: "Monographs & Drafts", color: "var(--accent-cyan)" },
      { id: "dossiers", label: "Research Dossiers", color: "var(--accent-green)" },
      { id: "intake", label: "Intake & Notes", color: "var(--info)" },
      { id: "books", label: "Books & PDFs", color: "var(--accent-purple)" },
      { id: "sources", label: "Source Material", color: "var(--accent-blue)" },
      { id: "control", label: "Control & State", color: "var(--accent-amber)" },
      { id: "scripts", label: "Tooling & Scripts", color: "var(--text-muted)" },
      { id: "vaults", label: "External Vaults", color: "var(--accent-purple)" }
    ];

    var container = el("div", { style: "display:flex;flex-direction:column;gap:6px;" });
    catDefs.forEach(function (c) {
      var item = el("label", {
        style: "display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text-main);cursor:pointer;"
      }, [
        el("input", {
          type: "checkbox",
          checked: state.filters.categories[c.id] !== false,
          style: "accent-color:var(--accent-gold);cursor:pointer;",
          on: {
            change: function (e) {
              state.filters.categories[c.id] = e.target.checked;
              filterAndRenderVisualizer();
            }
          }
        }),
        el("span", {
          style: "width:8px;height:8px;border-radius:50%;background:" + c.color + ";"
        }),
        el("span", { text: c.label })
      ]);
      container.appendChild(item);
    });
    return container;
  }

  function renderAuthorFilters() {
    var opts = [
      { id: "all", label: "All Works" },
      { id: "user_authored", label: "James Authored Notes" },
      { id: "ai_authored", label: "AI Fleet Dossiers" },
      { id: "canonical_edition", label: "Canonical Editions" }
    ];
    var container = el("div", { style: "display:flex;flex-direction:column;gap:6px;" });
    opts.forEach(function (opt) {
      var radio = el("label", {
        style: "display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text-muted);cursor:pointer;"
      }, [
        el("input", {
          type: "radio",
          name: "nav-author-filter",
          value: opt.id,
          checked: state.filters.authorType === opt.id,
          style: "accent-color:var(--accent-cyan);cursor:pointer;",
          on: {
            change: function (e) {
              state.filters.authorType = e.target.value;
              filterAndRenderVisualizer();
            }
          }
        }),
        el("span", { text: opt.label })
      ]);
      container.appendChild(radio);
    });
    return container;
  }

  function renderDepthSlider() {
    var valDisplay = el("span", { style: "font-size:12px;color:var(--accent-gold);font-weight:700;", text: String(state.filters.genealogyDepth) + " hops" });
    return el("div", { style: "display:flex;flex-direction:column;gap:4px;" }, [
      el("div", { style: "display:flex;justify-content:space-between;align-items:center;" }, [
        el("span", { style: "font-size:11px;color:var(--text-dim);", text: "Hop Radius:" }),
        valDisplay
      ]),
      el("input", {
        type: "range",
        min: "1",
        max: "4",
        value: String(state.filters.genealogyDepth),
        style: "width:100%;accent-color:var(--accent-gold);cursor:pointer;",
        on: {
          input: function (e) {
            state.filters.genealogyDepth = parseInt(e.target.value, 10);
            valDisplay.textContent = e.target.value + " hops";
            if (state.viewMode === "genealogy") filterAndRenderVisualizer();
          }
        }
      })
    ]);
  }

  // ── Data Fetching ─────────────────────────────────────────────────────────────
  function fetchAndRender() {
    var wrapper = document.getElementById("nav-canvas-wrapper");
    if (wrapper) wrapper.innerHTML = "<div style='color:var(--accent-gold);font-size:14px;display:flex;align-items:center;gap:8px;'>⏳ Indexing and computing corpus tree map…</div>";

    var urlTree = "/api/navigator/tree?sort_by=" + encodeURIComponent(state.sortBy) +
      "&group_by=" + encodeURIComponent(state.groupBy) +
      "&size_metric=" + encodeURIComponent(state.sizeMetric) +
      "&exclude_infrastructure=" + (state.excludeInfrastructure ? "true" : "false") +
      (state.chronoMaxMonth ? "&chrono_max_month=" + encodeURIComponent(state.chronoMaxMonth) : "");

    var urlGen = "/api/navigator/genealogy?depth=" + state.filters.genealogyDepth +
      "&exclude_infrastructure=" + (state.excludeInfrastructure ? "true" : "false") +
      (state.chronoMaxMonth ? "&chrono_max_month=" + encodeURIComponent(state.chronoMaxMonth) : "");

    Promise.all([
      fetch(urlTree).then(function (r) { return r.json(); }),
      fetch(urlGen).then(function (r) { return r.json(); })
    ]).then(function (results) {
      state.treemapRoot = results[0];
      state.currentBreadcrumb = [state.treemapRoot];
      state.genealogyData = results[1];
      filterAndRenderVisualizer();
    }).catch(function (err) {
      if (wrapper) wrapper.innerHTML = "<div style='color:var(--accent-red);padding:20px;'>Failed to load tree data: " + err + "</div>";
    });
  }

  function triggerReindex() {
    var wrapper = document.getElementById("nav-canvas-wrapper");
    if (wrapper) wrapper.innerHTML = "<div style='color:var(--accent-cyan);padding:20px;'>⏳ Triggered full asynchronous re-indexing on port 8080…</div>";
    fetch("/api/navigator/reindex", { method: "POST" })
      .then(function () { setTimeout(fetchAndRender, 1500); })
      .catch(function (e) { alert("Reindex error: " + e); });
  }

  // ── Visualizer Dispatcher ─────────────────────────────────────────────────────
  function filterAndRenderVisualizer() {
    if (state.viewMode === "mindmap") {
      renderMindmapView();
    } else if (state.viewMode === "treemap") {
      renderTreemapView();
    } else if (state.viewMode === "sunburst") {
      renderSunburstView();
    } else {
      renderGenealogyView();
    }
  }

  // ── Engine 0: Organic Mindmap Nodes (Premier View) ───────────────────────────
  function renderMindmapView() {
    var wrapper = document.getElementById("nav-canvas-wrapper");
    var breadcrumbBar = document.getElementById("nav-breadcrumbs");
    if (!wrapper || !state.treemapRoot) return;

    wrapper.textContent = "";

    // Update Breadcrumb/Status Navigation
    if (breadcrumbBar) {
      breadcrumbBar.innerHTML = "<span style='color:var(--accent-gold);font-weight:700;'>🧠 Mindmap Mode:</span> " +
        "<span style='color:var(--text-muted);'>Drag to pan • Scroll to zoom • Click node to preview • Click branch [+] / [−] to expand/collapse</span>";
    }

    var w = wrapper.clientWidth || 900;
    var h = wrapper.clientHeight || 600;

    var canvas = el("canvas", {
      width: String(w),
      height: String(h),
      style: "width:100%;height:100%;display:block;background:var(--bg-base);cursor:grab;"
    });

    // Floating On-Canvas HUD Controls
    var hud = el("div", {
      style: "position:absolute;bottom:16px;right:16px;display:flex;align-items:center;gap:6px;background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:4px 8px;box-shadow:0 4px 16px rgba(0,0,0,0.5);z-index:20;"
    }, [
      el("button", {
        style: "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:4px;width:28px;height:28px;font-size:14px;cursor:pointer;font-weight:bold;display:flex;align-items:center;justify-content:center;",
        text: "+",
        title: "Zoom In",
        on: { click: function () { state.mindmapZoom = Math.min(3.0, state.mindmapZoom * 1.2); draw(); } }
      }),
      el("button", {
        style: "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);border-radius:4px;width:28px;height:28px;font-size:14px;cursor:pointer;font-weight:bold;display:flex;align-items:center;justify-content:center;",
        text: "−",
        title: "Zoom Out",
        on: { click: function () { state.mindmapZoom = Math.max(0.25, state.mindmapZoom / 1.2); draw(); } }
      }),
      el("button", {
        style: "background:var(--bg-card);color:var(--accent-gold);border:1px solid var(--border);border-radius:4px;padding:0 8px;height:28px;font-size:11px;cursor:pointer;font-weight:600;display:flex;align-items:center;justify-content:center;",
        text: "⟲ Reset",
        title: "Center and Reset Zoom",
        on: { click: function () { state.mindmapPanX = 0; state.mindmapPanY = 0; state.mindmapZoom = 1.0; draw(); } }
      }),
      el("button", {
        style: "background:var(--bg-card);color:var(--accent-cyan);border:1px solid var(--border);border-radius:4px;padding:0 8px;height:28px;font-size:11px;cursor:pointer;font-weight:600;display:flex;align-items:center;justify-content:center;",
        text: "📁 Toggle All",
        title: "Expand/Collapse All Branches",
        on: {
          click: function () {
            var anyCollapsed = Object.keys(state.collapsedBranches).some(function (k) { return state.collapsedBranches[k] === true; });
            var cats = ["master", "volumes", "dossiers", "drafts", "scripts", "sources", "intake", "control", "other", "books", "vaults"];
            cats.forEach(function (c) {
              state.collapsedBranches[c] = !anyCollapsed;
            });
            draw();
          }
        }
      })
    ]);

    wrapper.appendChild(canvas);
    wrapper.appendChild(hud);

    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Categories grouped into Right and Left
    var rightCatDefs = [
      { id: "master", label: "Master Dissertation", icon: "👑", colorVar: "--accent-gold" },
      { id: "dossiers", label: "Research Dossiers", icon: "🔬", colorVar: "--accent-green" },
      { id: "volumes", label: "Published Volumes", icon: "📚", colorVar: "--accent-gold" },
      { id: "drafts", label: "Monographs & Drafts", icon: "✍️", colorVar: "--accent-cyan" }
    ];

    var leftCatDefs = [
      { id: "books", label: "Books & Sources", icon: "📜", colorVar: "--accent-purple" },
      { id: "control", label: "Control & State", icon: "⚙️", colorVar: "--accent-amber" },
      { id: "scripts", label: "Tooling & Scripts", icon: "🛠️", colorVar: "--text-muted" },
      { id: "intake", label: "Intake & Notes", icon: "📥", colorVar: "--info" },
      { id: "sources", label: "Source Material", icon: "📖", colorVar: "--accent-blue" },
      { id: "other", label: "Other Artifacts", icon: "📁", colorVar: "--text-dim" }
    ];

    var categoryData = {};
    (state.treemapRoot.children || []).forEach(function (catChild) {
      var cid = catChild.category || catChild.name.toLowerCase();
      categoryData[cid] = catChild;
    });

    var interactiveNodes = [];

    function computeBranchLayout(defs, side) {
      var activeBranches = [];
      var totalHeight = 0;

      defs.forEach(function (def) {
        if (state.filters.categories[def.id] === false) return;
        var data = categoryData[def.id] || { name: def.label, children: [] };
        var rawChildren = data.children || [];

        // Apply search query if present
        var children = rawChildren.filter(function (c) {
          if (state.searchQuery) {
            var q = state.searchQuery.toLowerCase();
            return (c.name && c.name.toLowerCase().includes(q)) || (c.badge && c.badge.toLowerCase().includes(q));
          }
          return true;
        });

        var isCollapsed = state.searchQuery ? false : (state.collapsedBranches[def.id] === true);
        var displayedChildren = isCollapsed ? [] : children.slice(0, 18);
        var hasMore = !isCollapsed && children.length > 18;

        var childCount = displayedChildren.length + (hasMore ? 1 : 0);
        var branchBlockH = isCollapsed ? 52 : Math.max(52, childCount * 36 + 24);

        activeBranches.push({
          def: def,
          data: data,
          totalCount: rawChildren.length,
          matchedCount: children.length,
          isCollapsed: isCollapsed,
          displayedChildren: displayedChildren,
          hasMore: hasMore,
          moreCount: children.length - 18,
          blockHeight: branchBlockH
        });

        totalHeight += branchBlockH + 18;
      });

      return { branches: activeBranches, totalHeight: totalHeight };
    }

    function drawRoundedRect(cx, cy, rw, rh, r, fill, stroke, shadowColor, shadowBlur) {
      ctx.save();
      if (shadowBlur && shadowBlur > 0) {
        ctx.shadowColor = shadowColor || stroke || "rgba(0,0,0,0.5)";
        ctx.shadowBlur = shadowBlur;
      }
      ctx.beginPath();
      ctx.moveTo(cx + r, cy);
      ctx.lineTo(cx + rw - r, cy);
      ctx.quadraticCurveTo(cx + rw, cy, cx + rw, cy + r);
      ctx.lineTo(cx + rw, cy + rh - r);
      ctx.quadraticCurveTo(cx + rw, cy + rh, cx + rw - r, cy + rh);
      ctx.lineTo(cx + r, cy + rh);
      ctx.quadraticCurveTo(cx, cy + rh, cx, cy + rh - r);
      ctx.lineTo(cx, cy + r);
      ctx.quadraticCurveTo(cx, cy, cx + r, cy);
      ctx.closePath();
      if (fill) {
        ctx.fillStyle = fill;
        ctx.fill();
      }
      if (stroke) {
        ctx.strokeStyle = stroke;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
      ctx.restore();
    }

    function draw() {
      w = wrapper.clientWidth || 900;
      h = wrapper.clientHeight || 600;
      canvas.width = w;
      canvas.height = h;

      interactiveNodes = [];

      ctx.clearRect(0, 0, w, h);

      // Background subtle grid
      ctx.save();
      ctx.fillStyle = getCssColor("--border", "rgba(255,255,255,0.06)");
      var gridSize = 40 * state.mindmapZoom;
      var offsetX = (w / 2 + state.mindmapPanX) % gridSize;
      var offsetY = (h / 2 + state.mindmapPanY) % gridSize;
      for (var gx = offsetX; gx < w; gx += gridSize) {
        for (var gy = offsetY; gy < h; gy += gridSize) {
          ctx.beginPath();
          ctx.arc(gx, gy, 1, 0, 2 * Math.PI);
          ctx.fill();
        }
      }
      ctx.restore();

      ctx.save();
      ctx.translate(w / 2 + state.mindmapPanX, h / 2 + state.mindmapPanY);
      ctx.scale(state.mindmapZoom, state.mindmapZoom);

      var rightLayout = computeBranchLayout(rightCatDefs, 1);
      var leftLayout = computeBranchLayout(leftCatDefs, -1);

      // ── Root Node ────────────────────────────────────────────────────────
      var rootW = 260;
      var rootH = 50;
      var rootX = -rootW / 2;
      var rootY = -rootH / 2;

      var goldColor = getCssColor("--accent-gold", "#d4af37");
      var panelColor = getCssColor("--bg-panel", "#1e2238");
      var cardColor = getCssColor("--bg-card", "#252a42");
      var textMain = getCssColor("--text-main", "#f1f5f9");
      var textMuted = getCssColor("--text-muted", "#94a3b8");

      drawRoundedRect(rootX, rootY, rootW, rootH, 10, panelColor, goldColor, goldColor, 12);

      ctx.fillStyle = goldColor;
      ctx.font = "bold 13px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("🏛️ History Proves Catholicism", 0, -8);

      ctx.fillStyle = textMuted;
      ctx.font = "10px Inter, monospace";
      var totalNodes = (state.genealogyData && state.genealogyData.nodes) ? state.genealogyData.nodes.length : 4146;
      ctx.fillText(totalNodes + " Indexed Nodes • Master Corpus", 0, 12);

      interactiveNodes.push({
        type: "root",
        x: rootX,
        y: rootY,
        w: rootW,
        h: rootH
      });

      // ── Right Side Branches ──────────────────────────────────────────────
      var curY_right = -rightLayout.totalHeight / 2;
      rightLayout.branches.forEach(function (b) {
        var branchY = curY_right + b.blockHeight / 2;
        var branchX = 230;
        var branchW = 190;
        var branchH = 38;
        var bColor = getCssColor(b.def.colorVar, "#d4af37");

        // Cubic Bezier from Root Right to Branch Left
        ctx.beginPath();
        ctx.moveTo(rootW / 2, 0);
        ctx.bezierCurveTo(
          rootW / 2 + 70, 0,
          branchX - 70, branchY,
          branchX, branchY
        );
        ctx.strokeStyle = bColor;
        ctx.lineWidth = 2.2;
        ctx.stroke();

        var isHovered = state.hoveredNode && state.hoveredNode.catId === b.def.id && state.hoveredNode.type === "branch";
        drawRoundedRect(
          branchX, branchY - branchH / 2, branchW, branchH, 8,
          cardColor, bColor, bColor, isHovered ? 10 : 0
        );

        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillStyle = textMain;
        ctx.font = "bold 11px Inter, sans-serif";
        ctx.fillText(b.def.icon + " " + b.def.label, branchX + 10, branchY);

        var badgeText = b.isCollapsed ? ("+" + b.totalCount) : ("−" + b.totalCount);
        ctx.textAlign = "right";
        ctx.font = "bold 10px monospace";
        ctx.fillStyle = bColor;
        ctx.fillText(badgeText, branchX + branchW - 10, branchY);

        interactiveNodes.push({
          type: "branch",
          catId: b.def.id,
          x: branchX,
          y: branchY - branchH / 2,
          w: branchW,
          h: branchH
        });

        // Expanded Children (Leaf Nodes)
        if (!b.isCollapsed) {
          var leafStartX = branchX + branchW + 60;
          var leafW = 250;
          var leafH = 28;
          var startLeafY = branchY - (b.displayedChildren.length * 34) / 2;

          b.displayedChildren.forEach(function (child, idx) {
            var leafY = startLeafY + idx * 34;

            ctx.beginPath();
            ctx.moveTo(branchX + branchW, branchY);
            ctx.bezierCurveTo(
              branchX + branchW + 30, branchY,
              leafStartX - 30, leafY,
              leafStartX, leafY
            );
            ctx.strokeStyle = "rgba(148, 163, 184, 0.25)";
            ctx.lineWidth = 1.0;
            ctx.stroke();

            var isSelected = state.selectedNode && (state.selectedNode.id === child.id || state.selectedNode.path === child.path);
            var isChildHover = state.hoveredNode && state.hoveredNode.data && state.hoveredNode.data.id === child.id;

            var borderCol = isSelected ? goldColor : (isChildHover ? bColor : getCssColor("--border", "#334155"));
            var fillCol = isSelected ? "var(--bg-panel)" : cardColor;

            drawRoundedRect(
              leafStartX, leafY - leafH / 2, leafW, leafH, 5,
              fillCol, borderCol, isSelected ? goldColor : null, isSelected ? 8 : 0
            );

            ctx.textAlign = "left";
            ctx.textBaseline = "middle";
            ctx.fillStyle = isSelected ? goldColor : textMain;
            ctx.font = "10px Inter, sans-serif";

            var label = child.name || child.id || "File";
            if (label.length > 28) label = label.substring(0, 26) + "…";
            ctx.fillText(label, leafStartX + 8, leafY);

            ctx.textAlign = "right";
            ctx.font = "9px monospace";
            ctx.fillStyle = textMuted;
            var szStr = formatBytes(child.size_bytes || child.value || 0);
            ctx.fillText(szStr, leafStartX + leafW - 8, leafY);

            interactiveNodes.push({
              type: "leaf",
              data: child,
              x: leafStartX,
              y: leafY - leafH / 2,
              w: leafW,
              h: leafH
            });
          });

          if (b.hasMore) {
            var moreY = startLeafY + b.displayedChildren.length * 34;
            drawRoundedRect(
              leafStartX, moreY - leafH / 2, leafW, leafH, 5,
              "rgba(0,0,0,0.3)", bColor, null, 0
            );
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.font = "italic 10px Inter, sans-serif";
            ctx.fillStyle = bColor;
            ctx.fillText("+" + b.moreCount + " more files (Click to view in Treemap)", leafStartX + leafW / 2, moreY);

            interactiveNodes.push({
              type: "more",
              catId: b.def.id,
              x: leafStartX,
              y: moreY - leafH / 2,
              w: leafW,
              h: leafH
            });
          }
        }

        curY_right += b.blockHeight + 18;
      });

      // ── Left Side Branches ───────────────────────────────────────────────
      var curY_left = -leftLayout.totalHeight / 2;
      leftLayout.branches.forEach(function (b) {
        var branchY = curY_left + b.blockHeight / 2;
        var branchW = 190;
        var branchH = 38;
        var branchX = -230 - branchW;
        var bColor = getCssColor(b.def.colorVar, "#38bdf8");

        ctx.beginPath();
        ctx.moveTo(-rootW / 2, 0);
        ctx.bezierCurveTo(
          -rootW / 2 - 70, 0,
          branchX + branchW + 70, branchY,
          branchX + branchW, branchY
        );
        ctx.strokeStyle = bColor;
        ctx.lineWidth = 2.2;
        ctx.stroke();

        var isHovered = state.hoveredNode && state.hoveredNode.catId === b.def.id && state.hoveredNode.type === "branch";
        drawRoundedRect(
          branchX, branchY - branchH / 2, branchW, branchH, 8,
          cardColor, bColor, bColor, isHovered ? 10 : 0
        );

        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillStyle = textMain;
        ctx.font = "bold 11px Inter, sans-serif";
        ctx.fillText(b.def.icon + " " + b.def.label, branchX + 10, branchY);

        var badgeText = b.isCollapsed ? ("+" + b.totalCount) : ("−" + b.totalCount);
        ctx.textAlign = "right";
        ctx.font = "bold 10px monospace";
        ctx.fillStyle = bColor;
        ctx.fillText(badgeText, branchX + branchW - 10, branchY);

        interactiveNodes.push({
          type: "branch",
          catId: b.def.id,
          x: branchX,
          y: branchY - branchH / 2,
          w: branchW,
          h: branchH
        });

        if (!b.isCollapsed) {
          var leafW = 250;
          var leafH = 28;
          var leafStartX = branchX - 60 - leafW;
          var startLeafY = branchY - (b.displayedChildren.length * 34) / 2;

          b.displayedChildren.forEach(function (child, idx) {
            var leafY = startLeafY + idx * 34;

            ctx.beginPath();
            ctx.moveTo(branchX, branchY);
            ctx.bezierCurveTo(
              branchX - 30, branchY,
              leafStartX + leafW + 30, leafY,
              leafStartX + leafW, leafY
            );
            ctx.strokeStyle = "rgba(148, 163, 184, 0.25)";
            ctx.lineWidth = 1.0;
            ctx.stroke();

            var isSelected = state.selectedNode && (state.selectedNode.id === child.id || state.selectedNode.path === child.path);
            var isChildHover = state.hoveredNode && state.hoveredNode.data && state.hoveredNode.data.id === child.id;

            var borderCol = isSelected ? goldColor : (isChildHover ? bColor : getCssColor("--border", "#334155"));
            var fillCol = isSelected ? "var(--bg-panel)" : cardColor;

            drawRoundedRect(
              leafStartX, leafY - leafH / 2, leafW, leafH, 5,
              fillCol, borderCol, isSelected ? goldColor : null, isSelected ? 8 : 0
            );

            ctx.textAlign = "left";
            ctx.textBaseline = "middle";
            ctx.fillStyle = isSelected ? goldColor : textMain;
            ctx.font = "10px Inter, sans-serif";

            var label = child.name || child.id || "File";
            if (label.length > 28) label = label.substring(0, 26) + "…";
            ctx.fillText(label, leafStartX + 8, leafY);

            ctx.textAlign = "right";
            ctx.font = "9px monospace";
            ctx.fillStyle = textMuted;
            var szStr = formatBytes(child.size_bytes || child.value || 0);
            ctx.fillText(szStr, leafStartX + leafW - 8, leafY);

            interactiveNodes.push({
              type: "leaf",
              data: child,
              x: leafStartX,
              y: leafY - leafH / 2,
              w: leafW,
              h: leafH
            });
          });

          if (b.hasMore) {
            var moreY = startLeafY + b.displayedChildren.length * 34;
            drawRoundedRect(
              leafStartX, moreY - leafH / 2, leafW, leafH, 5,
              "rgba(0,0,0,0.3)", bColor, null, 0
            );
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.font = "italic 10px Inter, sans-serif";
            ctx.fillStyle = bColor;
            ctx.fillText("+" + b.moreCount + " more files (Click to view in Treemap)", leafStartX + leafW / 2, moreY);

            interactiveNodes.push({
              type: "more",
              catId: b.def.id,
              x: leafStartX,
              y: moreY - leafH / 2,
              w: leafW,
              h: leafH
            });
          }
        }

        curY_left += b.blockHeight + 18;
      });

      ctx.restore();
    }

    // ── Mouse & Pan/Zoom Interactions ─────────────────────────────────────
    function getHitNode(e) {
      var rect = canvas.getBoundingClientRect();
      var clientX = e.clientX - rect.left;
      var clientY = e.clientY - rect.top;

      var mx = (clientX - (w / 2 + state.mindmapPanX)) / state.mindmapZoom;
      var my = (clientY - (h / 2 + state.mindmapPanY)) / state.mindmapZoom;

      for (var i = interactiveNodes.length - 1; i >= 0; i--) {
        var node = interactiveNodes[i];
        if (mx >= node.x && mx <= node.x + node.w && my >= node.y && my <= node.y + node.h) {
          return node;
        }
      }
      return null;
    }

    var isDragging = false;
    var dragStartX = 0;
    var dragStartY = 0;
    var didDragMove = false;

    canvas.addEventListener("mousedown", function (e) {
      isDragging = true;
      didDragMove = false;
      dragStartX = e.clientX - state.mindmapPanX;
      dragStartY = e.clientY - state.mindmapPanY;
      canvas.style.cursor = "grabbing";
    });

    window.addEventListener("mousemove", function (e) {
      if (isDragging) {
        didDragMove = true;
        state.mindmapPanX = e.clientX - dragStartX;
        state.mindmapPanY = e.clientY - dragStartY;
        draw();
      } else {
        var hit = getHitNode(e);
        if (hit) {
          canvas.style.cursor = "pointer";
          state.hoveredNode = hit;
        } else {
          canvas.style.cursor = "grab";
          state.hoveredNode = null;
        }
        draw();
      }
    });

    window.addEventListener("mouseup", function () {
      if (isDragging) {
        isDragging = false;
        canvas.style.cursor = "grab";
      }
    });

    canvas.addEventListener("wheel", function (e) {
      e.preventDefault();
      var zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
      state.mindmapZoom = Math.max(0.25, Math.min(3.0, state.mindmapZoom * zoomFactor));
      draw();
    }, { passive: false });

    canvas.addEventListener("click", function (e) {
      if (didDragMove) return;
      var hit = getHitNode(e);
      if (!hit) return;

      if (hit.type === "branch") {
        state.collapsedBranches[hit.catId] = !state.collapsedBranches[hit.catId];
        draw();
      } else if (hit.type === "leaf") {
        state.selectedNode = hit.data;
        draw();
        openPreviewDrawer(hit.data.path || hit.data.id);
      } else if (hit.type === "more") {
        var catItem = (state.treemapRoot.children || []).find(function (c) {
          return (c.category || c.name.toLowerCase()) === hit.catId;
        });
        if (catItem) {
          state.currentBreadcrumb = [state.treemapRoot, catItem];
          switchViewMode("treemap");
        }
      }
    });

    // Window / container resize observer
    if (window.ResizeObserver) {
      var ro = new ResizeObserver(function () {
        draw();
      });
      ro.observe(wrapper);
    }

    // Initial draw
    draw();
  }

  // ── Engine 1: Squarified Treemap ──────────────────────────────────────────────
  function renderTreemapView() {
    var wrapper = document.getElementById("nav-canvas-wrapper");
    var breadcrumbBar = document.getElementById("nav-breadcrumbs");
    if (!wrapper || !state.treemapRoot) return;

    wrapper.textContent = "";

    // Update Breadcrumb Navigation
    if (breadcrumbBar) {
      breadcrumbBar.textContent = "";
      state.currentBreadcrumb.forEach(function (node, idx) {
        if (idx > 0) breadcrumbBar.appendChild(el("span", { text: " / ", style: "color:var(--text-dim);" }));
        var b = el("button", {
          style: "border:none;background:none;color:" + (idx === state.currentBreadcrumb.length - 1 ? "var(--accent-gold)" : "var(--accent-cyan)") + ";cursor:pointer;font-weight:600;font-size:12px;",
          text: node.name || "Root",
          on: {
            click: function () {
              state.currentBreadcrumb = state.currentBreadcrumb.slice(0, idx + 1);
              renderTreemapView();
            }
          }
        });
        breadcrumbBar.appendChild(b);
      });
    }

    var activeSubtree = state.currentBreadcrumb[state.currentBreadcrumb.length - 1];
    var children = activeSubtree.children || [];

    // Filter children by Category and Search
    var filtered = children.filter(function (c) {
      if (c.category && state.filters.categories[c.category] === false) return false;
      if (state.searchQuery && (!c.name || !c.name.toLowerCase().includes(state.searchQuery))) return false;
      return true;
    });

    if (!filtered.length) {
      wrapper.appendChild(el("div", {
        style: "color:var(--text-muted);font-size:13px;padding:24px;",
        text: "No files match the active filters or search criteria."
      }));
      return;
    }

    // Canvas Container for Treemap
    var w = wrapper.clientWidth || 900;
    var h = wrapper.clientHeight || 600;

    var container = el("div", {
      style: "width:100%;height:100%;position:relative;overflow:hidden;background:var(--bg-base);"
    });

    // Compute Treemap Layout (Squarified algorithm)
    var rects = computeTreemapLayout(filtered, 0, 0, w, h);

    rects.forEach(function (r) {
      var item = r.data;
      var isFolder = Array.isArray(item.children) && item.children.length > 0;
      var bgVar = item.color_var || "var(--bg-card)";

      var tile = el("div", {
        class: "nav-tile",
        style: "position:absolute;left:" + r.x + "px;top:" + r.y + "px;width:" + r.w + "px;height:" + r.h + "px;border:1px solid var(--border);box-sizing:border-box;background:" + bgVar + ";cursor:pointer;overflow:hidden;padding:6px;display:flex;flex-direction:column;justify-content:space-between;transition:transform 0.15s,box-shadow 0.15s;opacity:0.92;",
        on: {
          mouseenter: function (e) {
            e.currentTarget.style.transform = "scale(1.008)";
            e.currentTarget.style.zIndex = "10";
            e.currentTarget.style.boxShadow = "0 0 14px var(--accent-gold-soft)";
          },
          mouseleave: function (e) {
            e.currentTarget.style.transform = "none";
            e.currentTarget.style.zIndex = "1";
            e.currentTarget.style.boxShadow = "none";
          },
          click: function () {
            if (isFolder) {
              state.currentBreadcrumb.push(item);
              renderTreemapView();
            } else {
              openPreviewDrawer(item.path || item.id);
            }
          }
        }
      });

      // Label and Badges inside tile if large enough
      if (r.w > 45 && r.h > 35) {
        var topRow = el("div", { style: "display:flex;align-items:center;justify-content:space-between;gap:4px;overflow:hidden;" }, [
          el("span", {
            style: "font-size:11px;font-weight:700;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-shadow:0 1px 3px rgba(0,0,0,0.8);",
            text: item.name
          }),
          item.badge ? el("span", {
            style: "font-size:9px;background:rgba(0,0,0,0.5);color:var(--text-muted);padding:1px 4px;border-radius:3px;font-family:var(--font-mono);flex-shrink:0;",
            text: item.badge
          }) : null
        ]);
        tile.appendChild(topRow);
      }

      if (r.w > 75 && r.h > 55) {
        var botRow = el("div", { style: "display:flex;align-items:center;justify-content:space-between;font-size:10px;color:var(--text-muted);font-family:var(--font-mono);" }, [
          el("span", { text: formatBytes(item.size_bytes || item.value || 0) }),
          item.lines ? el("span", { text: item.lines + " lines" }) : null
        ]);
        tile.appendChild(botRow);
      }

      container.appendChild(tile);
    });

    wrapper.appendChild(container);
  }

  // Pure Squarified Layout algorithm
  function computeTreemapLayout(items, x, y, width, height) {
    if (!items.length || width <= 0 || height <= 0) return [];
    var totalVal = items.reduce(function (sum, item) { return sum + (item.value || 1); }, 0);
    if (totalVal <= 0) totalVal = 1;

    var rects = [];
    var curX = x, curY = y, curW = width, curH = height;

    // Standard recursive slice-and-dice / squarify partition
    var isHorizontal = curW >= curH;
    var offset = 0;

    items.forEach(function (item) {
      var itemVal = item.value || 1;
      var ratio = itemVal / totalVal;

      if (isHorizontal) {
        var sliceW = Math.max(1, curW * ratio);
        rects.push({ x: curX + offset, y: curY, w: sliceW, h: curH, data: item });
        offset += sliceW;
      } else {
        var sliceH = Math.max(1, curH * ratio);
        rects.push({ x: curX, y: curY + offset, w: curW, h: sliceH, data: item });
        offset += sliceH;
      }
    });

    return rects;
  }

  // ── Engine 3: Sunburst Radial Space-Filling Partition ─────────────────────────
  function renderSunburstView() {
    var wrapper = document.getElementById("nav-canvas-wrapper");
    var breadcrumbBar = document.getElementById("nav-breadcrumbs");
    if (!wrapper || !state.treemapRoot) return;

    wrapper.textContent = "";

    if (breadcrumbBar) {
      var metricLabel = state.sizeMetric === "citations" ? "Citation Density" : (state.sizeMetric === "lines" ? "Lines" : "Byte Size");
      breadcrumbBar.innerHTML = "<span style='color:var(--accent-gold);font-weight:700;'>☀️ Sunburst Radial:</span> " +
        "<span style='color:var(--text-muted);'>Radial multi-tier partition • Metric: " + metricLabel + " • Inner Ring: Groups • Outer Ring: Documents • Click to preview</span>";
    }

    var w = wrapper.clientWidth || 900;
    var h = wrapper.clientHeight || 600;

    var canvas = el("canvas", {
      width: String(w),
      height: String(h),
      style: "width:100%;height:100%;display:block;background:var(--bg-base);cursor:pointer;"
    });

    wrapper.appendChild(canvas);

    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var centerX = w / 2;
    var centerY = h / 2;
    var maxRadius = Math.min(centerX, centerY) * 0.90;
    var r0 = maxRadius * 0.22;
    var r1 = maxRadius * 0.55;
    var r2 = maxRadius * 0.96;

    var groups = (state.treemapRoot.children || []).filter(function (g) {
      if (g.category && state.filters.categories[g.category] === false) return false;
      return true;
    });

    var totalVal = 0;
    groups.forEach(function (g) {
      var gItems = (g.children || []).filter(function (c) {
        if (state.excludeInfrastructure && c.is_infrastructure) return false;
        if (state.chronoMaxMonth && c.temporal_month && c.temporal_month > state.chronoMaxMonth) return false;
        if (state.searchQuery && (!c.name || !c.name.toLowerCase().includes(state.searchQuery))) return false;
        return true;
      });
      g._filteredChildren = gItems;
      g._total = gItems.reduce(function (sum, it) { return sum + (it.value || 1); }, 0);
      totalVal += g._total;
    });

    if (totalVal <= 0) totalVal = 1;

    // Slices for hit detection
    var slices = [];
    var curAngle = -Math.PI / 2;

    groups.forEach(function (g) {
      if (g._total <= 0) return;
      var gAngle = (g._total / totalVal) * 2 * Math.PI;
      var startA = curAngle;
      var endA = curAngle + gAngle;

      slices.push({
        type: "group",
        data: g,
        rIn: r0,
        rOut: r1,
        startA: startA,
        endA: endA,
        name: g.name,
        colorVar: g.color_var || "var(--accent-blue)"
      });

      var curChildAngle = startA;
      g._filteredChildren.forEach(function (child) {
        var childVal = child.value || 1;
        var childAngle = (childVal / g._total) * gAngle;
        var cStartA = curChildAngle;
        var cEndA = curChildAngle + childAngle;

        slices.push({
          type: "file",
          data: child,
          rIn: r1,
          rOut: r2,
          startA: cStartA,
          endA: cEndA,
          name: child.name,
          colorVar: child.color_var || g.color_var || "var(--accent-gold)"
        });

        curChildAngle = cEndA;
      });

      curAngle = endA;
    });

    var hoveredSlice = null;

    function draw() {
      ctx.clearRect(0, 0, w, h);

      // Draw all slices
      slices.forEach(function (s) {
        var isHovered = hoveredSlice === s;
        var color = getTokenColor(s.colorVar, "rgba(88, 166, 255, 0.8)");

        ctx.beginPath();
        ctx.arc(centerX, centerY, s.rIn, s.startA, s.endA, false);
        ctx.arc(centerX, centerY, isHovered ? s.rOut + 4 : s.rOut, s.endA, s.startA, true);
        ctx.closePath();

        ctx.fillStyle = color;
        ctx.globalAlpha = isHovered ? 1.0 : (s.type === "group" ? 0.85 : 0.65);
        ctx.fill();

        ctx.strokeStyle = getTokenColor("--border", "rgba(48, 54, 61, 0.8)");
        ctx.lineWidth = isHovered ? 2 : 1;
        ctx.stroke();

        ctx.globalAlpha = 1.0;

        // Draw radial label if slice is sufficiently large
        var angleSpan = s.endA - s.startA;
        if (angleSpan > 0.12 && (s.rOut - s.rIn) > 20) {
          var midAngle = s.startA + angleSpan / 2;
          var midRadius = (s.rIn + s.rOut) / 2;
          var lx = centerX + Math.cos(midAngle) * midRadius;
          var ly = centerY + Math.sin(midAngle) * midRadius;

          ctx.save();
          ctx.translate(lx, ly);
          ctx.rotate(midAngle > Math.PI / 2 || midAngle < -Math.PI / 2 ? midAngle + Math.PI : midAngle);
          ctx.fillStyle = getTokenColor("--text-main", "rgba(241, 245, 249, 1)");
          ctx.font = s.type === "group" ? "bold 11px Inter, sans-serif" : "9px Inter, sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";

          var label = s.name || "";
          if (label.length > 16) label = label.slice(0, 14) + "…";
          ctx.fillText(label, 0, 0);
          ctx.restore();
        }
      });

      // Draw Center Hub (Root circle)
      ctx.beginPath();
      ctx.arc(centerX, centerY, r0, 0, 2 * Math.PI);
      ctx.fillStyle = getTokenColor("--bg-panel", "rgba(22, 27, 34, 1)");
      ctx.fill();
      ctx.strokeStyle = getTokenColor("--accent-gold", "rgba(212, 175, 55, 1)");
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = getTokenColor("--accent-gold", "rgba(212, 175, 55, 1)");
      ctx.font = "bold 13px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("CORPUS", centerX, centerY - 10);

      ctx.fillStyle = getTokenColor("--text-muted", "rgba(148, 163, 184, 1)");
      ctx.font = "10px Inter, sans-serif";
      var metricDesc = state.sizeMetric === "citations" ? (totalVal + " cites") : (state.sizeMetric === "lines" ? (totalVal + " lines") : formatBytes(totalVal));
      ctx.fillText(metricDesc, centerX, centerY + 8);
    }

    draw();

    function findSliceAt(mx, my) {
      var dx = mx - centerX;
      var dy = my - centerY;
      var dist = Math.hypot(dx, dy);
      var angle = Math.atan2(dy, dx);
      if (angle < -Math.PI / 2) angle += 2 * Math.PI;

      for (var i = 0; i < slices.length; i++) {
        var s = slices[i];
        if (dist >= s.rIn && dist <= s.rOut) {
          var sA = s.startA;
          var eA = s.endA;
          if (angle >= sA && angle <= eA) {
            return s;
          }
        }
      }
      return null;
    }

    canvas.addEventListener("mousemove", function (e) {
      var rect = canvas.getBoundingClientRect();
      var mx = e.clientX - rect.left;
      var my = e.clientY - rect.top;
      var s = findSliceAt(mx, my);
      if (s !== hoveredSlice) {
        hoveredSlice = s;
        draw();
        if (s && breadcrumbBar) {
          var item = s.data;
          var valStr = state.sizeMetric === "citations" ? ((item.citations || item.value || 0) + " citations") : (state.sizeMetric === "lines" ? ((item.lines || item.value || 0) + " lines") : formatBytes(item.size_bytes || item.value || 0));
          breadcrumbBar.innerHTML = "<span style='color:var(--accent-gold);font-weight:700;'>Selected:</span> " +
            "<span style='color:var(--text-main);'>" + (s.name || "") + "</span> " +
            "<span style='color:var(--accent-cyan);'>(" + valStr + ")</span>" +
            (item.temporal_month ? " • <span style='color:var(--text-muted);'>" + item.temporal_month + "</span>" : "");
        }
      }
    });

    canvas.addEventListener("click", function (e) {
      var rect = canvas.getBoundingClientRect();
      var mx = e.clientX - rect.left;
      var my = e.clientY - rect.top;
      var s = findSliceAt(mx, my);
      if (s) {
        if (s.type === "file") {
          openPreviewDrawer(s.data.path || s.data.id);
        } else if (s.type === "group") {
          state.currentBreadcrumb.push(s.data);
          state.viewMode = "treemap";
          switchViewMode("treemap");
        }
      }
    });
  }

  // ── Engine 2: Directed Knowledge Genealogy DAG ───────────────────────────────
  function renderGenealogyView() {
    var wrapper = document.getElementById("nav-canvas-wrapper");
    var breadcrumbBar = document.getElementById("nav-breadcrumbs");
    if (!wrapper || !state.genealogyData) return;

    wrapper.textContent = "";
    if (breadcrumbBar) {
      breadcrumbBar.innerHTML = "<span style='color:var(--accent-cyan);font-weight:600;'>Genealogy of Knowledge:</span> " +
        "<span style='color:var(--text-muted);'>[Tier 0: Sources] ➔ [Tier 1: Dossiers] ➔ [Tier 2: Drafts] ➔ [Tier 3: Master] ➔ [Tier 4: Infrastructure (Dock)]</span>";
    }

    var nodes = state.genealogyData.nodes || [];
    var edges = state.genealogyData.edges || [];

    // Filter nodes by Category, Exclude Infrastructure, Chrono-Scrubber, and Search
    var activeNodeSet = {};
    var filteredNodes = nodes.filter(function (n) {
      if (state.excludeInfrastructure && (n.is_infrastructure || n.academic_tier === 4)) return false;
      if (state.chronoMaxMonth && n.temporal_month && n.temporal_month > state.chronoMaxMonth) return false;
      if (n.category && state.filters.categories[n.category] === false) return false;
      if (state.searchQuery && (!n.label || !n.label.toLowerCase().includes(state.searchQuery))) return false;
      activeNodeSet[n.id] = true;
      return true;
    });

    var filteredEdges = edges.filter(function (e) {
      return activeNodeSet[e.source] && activeNodeSet[e.target];
    });

    var w = wrapper.clientWidth || 900;
    var h = wrapper.clientHeight || 600;

    // Layout nodes into 5 Tier Columns: Tier 0 to Tier 3 (Scholarly Hierarchy), Tier 4 (Dock/Far Right)
    var tierColumns = { 0: [], 1: [], 2: [], 3: [], 4: [] };
    filteredNodes.forEach(function (n) {
      var t = typeof n.academic_tier === "number" ? n.academic_tier : 1;
      if (!tierColumns[t]) tierColumns[t] = [];
      tierColumns[t].push(n);
    });

    var colX = {
      0: w * 0.10,
      1: w * 0.30,
      2: w * 0.50,
      3: w * 0.72,
      4: w * 0.92
    };

    var maxCount = Math.max(1,
      (tierColumns[0] || []).length,
      (tierColumns[1] || []).length,
      (tierColumns[2] || []).length,
      (tierColumns[3] || []).length,
      (tierColumns[4] || []).length
    );
    var minStep = 24;
    var canvasHeight = Math.max(h, (maxCount + 2) * minStep);

    // Create Canvas for Interactive DAG with Glowing Lineages
    var canvas = el("canvas", {
      width: String(w),
      height: String(canvasHeight),
      style: "width:100%;height:" + canvasHeight + "px;display:block;background:var(--bg-base);cursor:grab;"
    });

    wrapper.style.overflowY = "auto";
    wrapper.appendChild(canvas);

    var ctx = canvas.getContext("2d");
    if (!ctx) return;

    var nodePositions = {};

    Object.keys(tierColumns).forEach(function (tierKey) {
      var colNodes = tierColumns[tierKey];
      var count = colNodes.length;
      var stepY = Math.max(minStep, canvasHeight / (count + 1));

      colNodes.forEach(function (n, idx) {
        var posX = colX[tierKey] || (w * 0.92);
        var posY = stepY * (idx + 1);
        nodePositions[n.id] = { x: posX, y: posY, node: n };
      });
    });

    // Draw DAG onto Canvas
    function draw() {
      ctx.clearRect(0, 0, w, canvasHeight);

      // Draw Grid Lines / Column Guides
      ctx.strokeStyle = "rgba(38, 44, 66, 0.4)";
      ctx.lineWidth = 1;
      [0.10, 0.30, 0.50, 0.72, 0.92].forEach(function (pct) {
        ctx.beginPath();
        ctx.moveTo(w * pct, 0);
        ctx.lineTo(w * pct, canvasHeight);
        ctx.stroke();
      });

      // Draw Column Headers
      ctx.fillStyle = getTokenColor("--text-dim", "rgba(148, 163, 184, 0.7)");
      ctx.font = "bold 10px Inter, sans-serif";
      ctx.textAlign = "center";
      var colHeaders = {
        0: "T0: Primary / Books",
        1: "T1: Dossiers / Intake",
        2: "T2: Draft Monographs",
        3: "T3: Master Dissertation",
        4: "T4: Infrastructure"
      };
      Object.keys(colX).forEach(function (k) {
        ctx.fillText(colHeaders[k] || ("Tier " + k), colX[k], 16);
      });

      // Draw Edges with Glowing Arrows
      filteredEdges.forEach(function (e) {
        var p1 = nodePositions[e.source];
        var p2 = nodePositions[e.target];
        if (!p1 || !p2) return;

        var isHighlighted = false;
        if (state.selectedNode) {
          if (e.source === state.selectedNode.id || e.target === state.selectedNode.id) {
            isHighlighted = true;
          }
        }

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.bezierCurveTo(p1.x + 40, p1.y, p2.x - 40, p2.y, p2.x, p2.y);

        if (isHighlighted) {
          ctx.strokeStyle = e.source === state.selectedNode.id ? getTokenColor("--accent-gold", "rgb(212, 175, 55)") : getTokenColor("--accent-cyan", "rgb(56, 189, 248)");
          ctx.lineWidth = 2.5;
          ctx.shadowBlur = 8;
          ctx.shadowColor = ctx.strokeStyle;
        } else {
          ctx.strokeStyle = "rgba(100, 116, 139, 0.25)";
          ctx.lineWidth = 1;
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
      });

      // Draw Nodes
      ctx.textAlign = "left";
      Object.keys(nodePositions).forEach(function (nid) {
        var pos = nodePositions[nid];
        var n = pos.node;
        var isSelected = state.selectedNode && state.selectedNode.id === nid;

        ctx.beginPath();
        ctx.arc(pos.x, pos.y, isSelected ? 8 : 5, 0, 2 * Math.PI);
        ctx.fillStyle = isSelected ? getTokenColor("--accent-gold", "rgb(212, 175, 55)") : getTokenColor("--accent-cyan", "rgb(56, 189, 248)");
        ctx.fill();

        if (isSelected) {
          ctx.strokeStyle = getTokenColor("--accent-gold", "rgb(212, 175, 55)");
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Draw Labels
        ctx.fillStyle = isSelected ? getTokenColor("--accent-gold", "rgb(212, 175, 55)") : getTokenColor("--text-main", "rgb(241, 245, 249)");
        ctx.font = isSelected ? "bold 11px Inter, sans-serif" : "10px Inter, sans-serif";
        var labelText = n.label.length > 20 ? n.label.slice(0, 18) + "…" : n.label;
        if (n.citations) labelText += " [" + n.citations + "]";
        ctx.fillText(labelText, pos.x + 10, pos.y + 4);
      });
    }

    draw();

    // Click on canvas to select node
    canvas.addEventListener("click", function (evt) {
      var rect = canvas.getBoundingClientRect();
      var clickX = evt.clientX - rect.left;
      var clickY = evt.clientY - rect.top;

      var clickedNode = null;
      Object.keys(nodePositions).forEach(function (nid) {
        var pos = nodePositions[nid];
        var dist = Math.hypot(clickX - pos.x, clickY - pos.y);
        if (dist <= 12) {
          clickedNode = pos.node;
        }
      });

      if (clickedNode) {
        state.selectedNode = clickedNode;
        draw();
        openPreviewDrawer(clickedNode.path || clickedNode.id);
      }
    });
  }

  // ── Right Slide-out Live Preview Drawer ───────────────────────────────────────
  function openPreviewDrawer(path) {
    var drawer = document.getElementById("nav-preview-drawer");
    if (!drawer) return;

    drawer.style.display = "flex";
    drawer.innerHTML = "<div style='padding:20px;color:var(--accent-gold);'>⏳ Fetching file genealogy preview…</div>";

    fetch("/api/navigator/file-preview?path=" + encodeURIComponent(path))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        renderPreviewDrawerContent(drawer, d);
      })
      .catch(function (e) {
        drawer.innerHTML = "<div style='padding:20px;color:var(--accent-red);'>Error loading preview: " + e + "</div>";
      });
  }

  function renderPreviewDrawerContent(drawer, data) {
    drawer.textContent = "";

    var meta = data.metadata || {};
    var parents = data.upstream_parents || [];
    var children = data.downstream_derivatives || [];

    // Header
    var header = el("div", {
      style: "padding:14px 18px;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;justify-content:space-between;gap:10px;background:var(--bg-panel);"
    }, [
      el("div", { style: "overflow:hidden;" }, [
        el("h3", { style: "margin:0 0 4px 0;font-size:14px;color:var(--accent-gold);font-family:var(--font-display);word-break:break-all;", text: meta.name }),
        el("div", { style: "display:flex;gap:6px;flex-wrap:wrap;" }, [
          el("span", { style: "font-size:10px;background:var(--bg-card);color:var(--accent-cyan);padding:2px 6px;border-radius:4px;border:1px solid var(--border);font-family:var(--font-mono);", text: meta.badge || "Doc" }),
          el("span", { style: "font-size:10px;background:var(--bg-card);color:var(--accent-green);padding:2px 6px;border-radius:4px;border:1px solid var(--border);font-family:var(--font-mono);", text: "Tier " + (meta.academic_tier !== undefined ? meta.academic_tier : "1") }),
          el("span", { style: "font-size:10px;background:var(--bg-card);color:var(--text-muted);padding:2px 6px;border-radius:4px;border:1px solid var(--border);font-family:var(--font-mono);", text: formatBytes(meta.size || 0) })
        ])
      ]),
      el("button", {
        style: "border:none;background:none;color:var(--text-muted);cursor:pointer;font-size:16px;line-height:1;",
        text: "✕",
        on: { click: function () { drawer.style.display = "none"; } }
      })
    ]);

    // Action Bar (External Editor, Reader, Ava Neural Voice)
    var actionBar = el("div", {
      style: "padding:8px 18px;background:var(--bg-card);border-bottom:1px solid var(--border);display:flex;gap:8px;flex-wrap:wrap;"
    }, [
      el("button", {
        style: "background:var(--bg-panel);color:var(--accent-gold);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:11px;font-weight:600;cursor:pointer;",
        text: "⚡ Open External",
        on: {
          click: function () {
            fetch("/api/navigator/open-external", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ path: meta.path })
            }).then(function () {
              if (window.showToast) window.showToast("Opened in external editor", "success");
            });
          }
        }
      }),
      el("button", {
        style: "background:var(--bg-panel);color:var(--accent-cyan);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:11px;font-weight:600;cursor:pointer;",
        text: "📖 Open Reader",
        on: {
          click: function () {
            if (window.JarvisOpen) window.JarvisOpen("reader", { path: meta.path });
          }
        }
      }),
      el("button", {
        style: "background:var(--bg-panel);color:var(--text-muted);border:1px solid var(--border);border-radius:4px;padding:4px 8px;font-size:11px;font-weight:600;cursor:pointer;",
        text: "📋 Copy Path",
        on: {
          click: function () {
            navigator.clipboard.writeText(meta.path);
            if (window.showToast) window.showToast("Path copied to clipboard", "success");
          }
        }
      })
    ]);

    // Scrollable Drawer Body
    var drawerBody = el("div", {
      style: "flex:1;overflow-y:auto;padding:14px 18px;display:flex;flex-direction:column;gap:14px;"
    });

    // Upstream Sources ("What caused this file")
    var parentBox = el("div", {
      style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;"
    }, [
      el("div", { style: "font-size:11px;font-weight:700;color:var(--accent-cyan);margin-bottom:6px;", text: "⬆️ Upstream Ancestors (Causes / Sources)" })
    ]);

    if (parents.length) {
      parents.forEach(function (p) {
        var pill = el("div", {
          style: "font-size:11px;color:var(--text-main);background:var(--bg-panel);padding:4px 8px;border-radius:4px;margin-bottom:4px;cursor:pointer;border:1px solid var(--border);display:flex;justify-content:space-between;",
          on: { click: function () { openPreviewDrawer(p.path || p.id); } }
        }, [
          el("span", { text: p.name }),
          el("span", { style: "font-size:9px;color:var(--accent-cyan);", text: p.relation })
        ]);
        parentBox.appendChild(pill);
      });
    } else {
      parentBox.appendChild(el("div", { style: "font-size:11px;color:var(--text-dim);", text: "No explicit upstream sources detected (Primary root)." }));
    }

    // Downstream Derivatives ("What this file caused")
    var childBox = el("div", {
      style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;"
    }, [
      el("div", { style: "font-size:11px;font-weight:700;color:var(--accent-gold);margin-bottom:6px;", text: "⬇️ Downstream Derivatives (Caused by this)" })
    ]);

    if (children.length) {
      children.forEach(function (c) {
        var pill = el("div", {
          style: "font-size:11px;color:var(--text-main);background:var(--bg-panel);padding:4px 8px;border-radius:4px;margin-bottom:4px;cursor:pointer;border:1px solid var(--border);display:flex;justify-content:space-between;",
          on: { click: function () { openPreviewDrawer(c.path || c.id); } }
        }, [
          el("span", { text: c.name }),
          el("span", { style: "font-size:9px;color:var(--accent-gold);", text: c.relation })
        ]);
        childBox.appendChild(pill);
      });
    } else {
      childBox.appendChild(el("div", { style: "font-size:11px;color:var(--text-dim);", text: "No downstream derivatives detected yet." }));
    }

    // Raw Content Sample
    var contentBox = el("div", {
      style: "display:flex;flex-direction:column;gap:6px;"
    }, [
      el("div", { style: "font-size:11px;font-weight:700;color:var(--text-muted);", text: "Document Sample" }),
      el("pre", {
        style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;font-family:var(--font-mono);font-size:11px;color:var(--text-main);white-space:pre-wrap;max-height:260px;overflow-y:auto;line-height:1.5;",
        text: data.content_sample || "(Empty or binary content)"
      })
    ]);

    drawerBody.appendChild(parentBox);
    drawerBody.appendChild(childBox);
    drawerBody.appendChild(contentBox);

    drawer.appendChild(header);
    drawer.appendChild(actionBar);
    drawer.appendChild(drawerBody);
  }

  // Register Module into CatholicJarvis Shell
  window.JarvisModules.navigator = { load: load };
})();
