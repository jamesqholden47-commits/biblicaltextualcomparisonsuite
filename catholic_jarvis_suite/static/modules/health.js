/* health.js — System Health & Daemon Monitor for CatholicJarvis Master Work Suite.
   Provides real-time inspection of API endpoints, memory/uptime, background tasks,
   corpus indexing, and module readiness.
   Complies 100% with jarvis.css design tokens (0 hardcoded hex colors). */
(function () {
  "use strict";

  window.JarvisModules = window.JarvisModules || {};

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

  function renderHealth(root) {
    root.textContent = "";
    root.style.cssText = "padding: 24px; overflow-y: auto; height: 100%; display: flex; flex-direction: column; gap: 20px;";

    // Header card
    var header = el("div", {
      style: "background: var(--bg-panel); border: 1px solid var(--border); border-radius: 8px; padding: 20px; display: flex; justify-content: space-between; align-items: center;"
    }, [
      el("div", null, [
        el("h2", { style: "font-family: 'Cinzel', serif; color: var(--accent-gold); font-size: 20px; margin-bottom: 6px;", text: "System Health & Daemon Monitor" }),
        el("p", { style: "color: var(--text-muted); font-size: 13px;", text: "Live diagnostics, dual-stack network sockets, corpus index status, and background process health." })
      ]),
      el("div", { style: "display: flex; gap: 10px;" }, [
        el("button", {
          style: "background: var(--accent-gold); color: var(--bg-base); font-weight: 600; border: none; border-radius: 4px; padding: 8px 16px; cursor: pointer;",
          text: "Refresh Diagnostics",
          on: { click: function () { renderHealth(root); } }
        })
      ])
    ]);
    root.appendChild(header);

    // Loading indicator
    var contentArea = el("div", { style: "display: flex; flex-direction: column; gap: 20px;" }, [
      el("p", { style: "color: var(--text-muted); font-size: 14px;", text: "Querying /api/health and /api/build_info..." })
    ]);
    root.appendChild(contentArea);

    Promise.all([
      fetch("/api/health").then(function (r) { return r.ok ? r.json() : null; }),
      fetch("/api/build_info").then(function (r) { return r.ok ? r.json() : null; }),
      fetch("/api/modules").then(function (r) { return r.ok ? r.json() : null; })
    ]).then(function (results) {
      var health = results[0];
      var build = results[1];
      var modules = results[2];

      contentArea.textContent = "";

      if (!health) {
        contentArea.appendChild(el("div", {
          style: "background: var(--bg-card); border: 1px solid var(--accent-red); border-radius: 8px; padding: 16px; color: var(--accent-red);",
          text: "Failed to connect to /api/health endpoint. Ensure the server is running."
        }));
        return;
      }

      // Metrics Grid
      var grid = el("div", { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px;" });

      function metricCard(label, val, sub, statusColor) {
        var card = el("div", {
          style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 6px;"
        }, [
          el("div", { style: "color: var(--text-dim); font-size: 11px; text-transform: uppercase; font-family: 'JetBrains Mono', monospace;", text: label }),
          el("div", { style: "color: " + (statusColor || "var(--text-main)") + "; font-size: 22px; font-weight: 700; font-family: 'JetBrains Mono', monospace;", text: String(val) }),
          el("div", { style: "color: var(--text-muted); font-size: 12px;", text: sub || "" })
        ]);
        return card;
      }

      grid.appendChild(metricCard("Server Status", (health.status || "ONLINE").toUpperCase(), "Uvicorn Port " + (health.port || 8080), "var(--accent-green)"));
      grid.appendChild(metricCard("System Uptime", Math.round(health.uptime_seconds || 0) + " s", "Dual-Stack IPv4 / IPv6 Active", "var(--accent-cyan)"));
      grid.appendChild(metricCard("Corpus Index", health.corpus_indexed ? "INDEXED" : "PENDING", "Age: " + Math.round(health.corpus_index_age_seconds || 0) + "s", health.corpus_indexed ? "var(--accent-green)" : "var(--accent-gold)"));
      grid.appendChild(metricCard("Anki Cards Due", health.anki_due_today + " / " + health.anki_total_cards, "Active Recall Queue", health.anki_due_today > 0 ? "var(--accent-gold)" : "var(--accent-green)"));
      grid.appendChild(metricCard("TTS Voice", "AVA NEURAL", "Cache: " + (health.audio_cache_count || 0) + " audio files", "var(--accent-blue)"));
      contentArea.appendChild(grid);

      // Network & Interfaces Card
      var netCard = el("div", {
        style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; gap: 12px;"
      }, [
        el("h3", { style: "font-size: 15px; color: var(--accent-gold);", text: "🌐 Network Interfaces & Direct Links" }),
        el("div", { style: "display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; font-family: 'JetBrains Mono', monospace; font-size: 13px;" }, [
          el("a", { href: "http://localhost:" + health.port + "/#library/verbum", target: "_blank", style: "color: var(--accent-cyan); text-decoration: none; padding: 10px; background: var(--bg-panel); border-radius: 4px; border: 1px solid var(--border);", text: "📖 Verbum Catholic Suite (#library/verbum)" }),
          el("a", { href: "http://localhost:" + health.port + "/#library/manuscripts", target: "_blank", style: "color: var(--accent-cyan); text-decoration: none; padding: 10px; background: var(--bg-panel); border-radius: 4px; border: 1px solid var(--border);", text: "📜 3D Manuscripts Suite (#library/manuscripts)" }),
          el("a", { href: "http://localhost:" + health.port + "/api/health", target: "_blank", style: "color: var(--accent-cyan); text-decoration: none; padding: 10px; background: var(--bg-panel); border-radius: 4px; border: 1px solid var(--border);", text: "🩺 Raw /api/health Endpoint" }),
          el("a", { href: "http://127.0.0.1:" + health.port + "/", target: "_blank", style: "color: var(--accent-cyan); text-decoration: none; padding: 10px; background: var(--bg-panel); border-radius: 4px; border: 1px solid var(--border);", text: "⚡ Loopback IPv4 (http://127.0.0.1:" + health.port + ")" })
        ])
      ]);
      contentArea.appendChild(netCard);

      // Hot-Path Cache Status -- the cache-fix work from 2026-11-12 (recall/navigator/catalog/
      // log_reader) is real data on /api/health already (hot_path_caches), but nothing in this
      // tab ever rendered it; added 2026-11-12 along with a "jump to this tab" link per cache so
      // a cold cache is one click from the tab that will warm it.
      var caches = health.hot_path_caches || {};
      var CACHE_META = {
        recall_corpus_files: { label: "Recall corpus files", hash: "#system/recall", tabLabel: "Open Recall" },
        log_reader_sources: { label: "Log reader sources (TTL cache)", hash: "#system/sessions", tabLabel: "Open Sessions" },
        navigator_scan: { label: "Genealogy / Treemap scan", hash: "#library/navigator", tabLabel: "Open Genealogy & Treemap" },
        catalog_files: { label: "Catalog files (ag_output_catalog.json)", hash: "#library/organizer", tabLabel: "Open Organizer" },
      };
      if (Object.keys(caches).length) {
        var cacheCard = el("div", {
          style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; gap: 12px;"
        }, [
          el("h3", { style: "font-size: 15px; color: var(--accent-gold);", text: "⚡ Hot-Path Cache Status" }),
          el("p", { style: "color: var(--text-muted); font-size: 12px; margin: 0;", text: "Each of these re-parses a multi-MB file from disk on a cold miss; COLD after a fresh server start is normal -- click through to warm it." })
        ]);
        var cacheGrid = el("div", { style: "display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px;" });
        Object.keys(caches).forEach(function (key) {
          var c = caches[key];
          var meta = CACHE_META[key] || { label: key, hash: null, tabLabel: null };
          var isWarm = !!c.warm;
          var sub = c.error ? ("error: " + c.error)
            : (key === "log_reader_sources" && c.age_seconds != null) ? ("age " + c.age_seconds + "s / ttl " + c.ttl_seconds + "s")
            : (key === "catalog_files" && c.paths_cached != null) ? (c.paths_cached + " path(s) cached")
            : "";
          var row = el("div", {
            style: "padding: 10px 12px; background: var(--bg-panel); border-radius: 4px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 4px;"
          }, [
            el("div", { style: "display: flex; justify-content: space-between; align-items: center;" }, [
              el("span", { style: "font-size: 12px; color: var(--text-main);", text: meta.label }),
              el("span", { style: "font-size: 10px; padding: 2px 6px; border-radius: 3px; font-weight: 600; color: " + (isWarm ? "var(--accent-green)" : "var(--accent-gold)") + "; background: " + (isWarm ? "rgba(16, 185, 129, 0.15)" : "rgba(234, 179, 8, 0.15)"), text: isWarm ? "WARM" : "COLD" })
            ]),
            sub ? el("div", { style: "font-size: 11px; color: var(--text-dim); font-family: 'JetBrains Mono', monospace;", text: sub }) : null,
            (!isWarm && meta.hash) ? el("a", {
              href: meta.hash, style: "font-size: 11px; color: var(--accent-cyan); text-decoration: none; cursor: pointer;",
              text: "→ " + meta.tabLabel + " (warm this cache)",
              on: { click: function (e) {
                // A relative hash change within THIS SPA, not a new tab against health.port --
                // health.port reflects a config/PORT_FILE value that can go stale the moment a
                // dev server gets reassigned to a different port (as preview_start does on a
                // conflict), which would silently point this link at the wrong server entirely.
                e.preventDefault();
                location.hash = meta.hash.slice(1);
              } }
            }) : null
          ]);
          cacheGrid.appendChild(row);
        });
        cacheCard.appendChild(cacheGrid);
        contentArea.appendChild(cacheCard);
      }

      // Loaded Modules Inventory
      if (build && build.modules) {
        var modCard = el("div", {
          style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; gap: 12px;"
        }, [
          el("h3", { style: "font-size: 15px; color: var(--accent-gold);", text: "📦 Backend Router Modules Inventory" })
        ]);

        var modGrid = el("div", { style: "display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 8px;" });
        Object.keys(build.modules).forEach(function (mKey) {
          var status = build.modules[mKey];
          var isOk = status === "loaded";
          modGrid.appendChild(el("div", {
            style: "padding: 8px 12px; background: var(--bg-panel); border-radius: 4px; border: 1px solid var(--border); font-size: 12px; display: flex; justify-content: space-between; align-items: center;"
          }, [
            el("span", { style: "font-family: 'JetBrains Mono', monospace; color: var(--text-main);", text: mKey }),
            el("span", { style: "font-size: 10px; padding: 2px 6px; border-radius: 3px; font-weight: 600; color: " + (isOk ? "var(--accent-green)" : "var(--accent-red)") + "; background: " + (isOk ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)"), text: isOk ? "LOADED" : "FAILED" })
          ]));
        });
        modCard.appendChild(modGrid);
        contentArea.appendChild(modCard);
      }
    }).catch(function (err) {
      contentArea.textContent = "";
      contentArea.appendChild(el("div", {
        style: "background: var(--bg-card); border: 1px solid var(--accent-red); border-radius: 8px; padding: 16px; color: var(--accent-red);",
        text: "Error loading diagnostics: " + String(err)
      }));
    });
  }

  window.JarvisModules.health = {
    load: function (elRoot) {
      renderHealth(elRoot);
    },
    onShow: function (elRoot) {
      renderHealth(elRoot);
    }
  };
})();
