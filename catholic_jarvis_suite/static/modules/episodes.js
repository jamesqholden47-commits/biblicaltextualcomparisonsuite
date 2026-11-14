/* Episodes module tab (module id "episodes"). Task C005.
 * Multi-host conversational podcast pipeline for The Catholic Case.
 * Inspects podcast scripts, executes the fidelity check gate,
 * displays open vs reviewed fidelity flags, and triggers audio builds.
 * Strict DOM safety: textContent / escape only. */
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

  function load(root) {
    root.textContent = "";
    root.style.cssText = "padding:16px;color:var(--text-main);max-width:1400px;margin:0 auto;";

    var allEpisodes = [];
    var currentEpId = null;

    // Header
    var header = el("div", { style: "display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;border-bottom:1px solid var(--border);padding-bottom:10px;" }, null, [
      el("div", null, null, [
        el("h2", { style: "margin:0 0 4px 0;font-size:18px;color:var(--accent-gold);" }, "Podcast Episodes & Fidelity Gate"),
        el("span", { style: "font-size:12px;color:var(--text-dim);" },
          "Script-based conversational audio episodes with pre-render fidelity gating against source chapters.")
      ]),
      el("div", { style: "display:flex;gap:8px;" }, null, [
        el("button", { style: BTN_CYAN, onclick: function () { loadEpisodes(); } }, "Refresh Gate Status")
      ])
    ]);

    // Workspace container (Left: episode list, Right: detailed fidelity & turns)
    var workspace = el("div", { style: "display:grid;grid-template-columns:1fr 1.8fr;gap:20px;" });
    var leftCol = el("div");
    var rightCol = el("div");
    workspace.appendChild(leftCol);
    workspace.appendChild(rightCol);

    root.appendChild(header);
    root.appendChild(workspace);

    function loadEpisodes() {
      leftCol.textContent = "";
      leftCol.appendChild((window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading episodes...") : document.createTextNode("Loading episodes..."));
      rightCol.textContent = "";

      fetch("/api/episodes").then(function (r) { return r.json(); }).then(function (data) {
        allEpisodes = data.episodes || [];
        renderEpisodeList();
        if (allEpisodes.length > 0) {
          currentEpId = allEpisodes[0].id;
          loadEpisodeDetail(currentEpId);
        } else {
          rightCol.textContent = "No podcast scripts found in data/podcast_scripts/.";
        }
      });
    }

    function renderEpisodeList() {
      leftCol.textContent = "";
      var card = el("div", { style: CARD_CSS }, null, [
        el("h4", { style: "margin:0 0 10px 0;font-size:13px;color:var(--accent-gold);" }, "Available Episodes (" + allEpisodes.length + ")"),
        (function () {
          var list = el("div");
          allEpisodes.forEach(function (ep) {
            var stColor = ep.gate_status === "PASS" ? "var(--accent-green)" :
              ep.gate_status === "STALE" ? "var(--accent-gold)" : "var(--accent-red)";
            var isSelected = ep.id === currentEpId;
            var item = el("div", {
              style: "background:" + (isSelected ? "rgba(212,175,55,0.12)" : "var(--bg-card)") + ";border:1px solid " + (isSelected ? "var(--accent-gold)" : "var(--border)") + ";border-radius:4px;padding:10px;margin-bottom:8px;cursor:pointer;",
              onclick: function () {
                currentEpId = ep.id;
                renderEpisodeList();
                loadEpisodeDetail(ep.id);
              }
            }, null, [
              el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;" }, null, [
                el("span", { style: "font-weight:600;font-size:12px;color:var(--text-main);" }, ep.title),
                pill(ep.gate_status, stColor)
              ]),
              el("div", { style: "display:flex;justify-content:space-between;font-size:11px;color:var(--text-dim);" }, null, [
                el("span", null, ep.total_turns + " turns"),
                el("span", null, ep.has_audio ? "MP3 Ready" : "Audio not built")
              ])
            ]);
            list.appendChild(item);
          });
          return list;
        })()
      ]);
      leftCol.appendChild(card);
    }

    function loadEpisodeDetail(epId) {
      rightCol.textContent = "";
      rightCol.appendChild((window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading episode gate details...") : document.createTextNode("Loading episode gate details..."));

      fetch("/api/episodes/" + epId + "/fidelity").then(function (r) { return r.json(); }).then(function (data) {
        renderEpisodeDetail(data);
      });
    }

    function renderEpisodeDetail(data) {
      rightCol.textContent = "";

      var statusPill = data.passed ? pill("FIDELITY GATE: PASS", "var(--accent-green)") :
        pill("FIDELITY GATE: " + data.open_flags.length + " OPEN FLAGS", "var(--accent-red)");

      var mainCard = el("div", { style: CARD_CSS }, null, [
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;" }, null, [
          el("h3", { style: "margin:0;font-size:16px;color:var(--accent-gold);" }, data.title),
          statusPill
        ]),
        el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:12px;" }, "Source: " + (data.source_document || "unknown")),
        // Action bar
        el("div", { style: "display:flex;gap:8px;margin-bottom:16px;" }, null, [
          el("button", { style: BTN_GOLD, onclick: function () {
            triggerBuild(data.id, false);
          }}, "Build Episode Audio (Edge TTS)"),
          el("button", { style: BTN_CYAN, onclick: function () {
            triggerBuild(data.id, true);
          }}, "Dry-Run Fidelity Check")
        ]),
        // Status notice
        (function () {
          if (data.passed) {
            return el("div", { style: "background:rgba(46,204,113,0.12);border:1px solid var(--accent-green);border-radius:4px;padding:10px;font-size:12px;color:var(--accent-green);margin-bottom:14px;" },
              "Pass: All figures voiced in this script are either traced to the source document or appropriately hedged against needs-checking items. Audio build is cleared.");
          } else {
            return el("div", { style: "background:rgba(231,76,60,0.12);border:1px solid var(--accent-red);border-radius:4px;padding:10px;font-size:12px;color:var(--accent-red);margin-bottom:14px;" },
              "Blocked: The fidelity gate refused audio synthesis. " + data.open_flags.length + " unreviewed flags remain. Audio will not render until these are hedged or reviewed.");
          }
        })(),
        // Open flags list
        (function () {
          if (!data.open_flags || data.open_flags.length === 0) return null;
          var flagBox = el("div", { style: "margin-bottom:16px;" });
          flagBox.appendChild(el("h4", { style: "margin:0 0 8px 0;font-size:12px;color:var(--accent-red);" }, "Open Fidelity Flags (" + data.open_flags.length + "):"));
          data.open_flags.forEach(function (fl) {
            var row = el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-left:3px solid var(--accent-red);padding:8px;border-radius:4px;margin-bottom:6px;font-size:11px;" }, null, [
              el("div", { style: "display:flex;justify-content:space-between;color:var(--accent-gold);margin-bottom:4px;" }, null, [
                el("span", { style: "font-weight:600;" }, "Turn " + fl.turn_id + " [" + fl.kind + "]: '" + fl.figure + "'"),
                pill(fl.kind, "var(--accent-red)")
              ]),
              el("div", { style: "margin-bottom:4px;color:var(--text-main);" }, "Podcast text: " + fl.podcast_sentence),
              fl.source_line ? el("div", { style: "color:var(--text-dim);font-style:italic;" }, "Source still-to-check: " + fl.source_line) : null
            ]);
            flagBox.appendChild(row);
          });
          return flagBox;
        })(),
        // Reviewed exceptions list
        (function () {
          if (!data.cleared_exceptions || data.cleared_exceptions.length === 0) return null;
          var revBox = el("details", { style: "margin-bottom:14px;" });
          revBox.appendChild(el("summary", { style: "font-size:11px;color:var(--text-dim);cursor:pointer;margin-bottom:6px;" },
            "Audited & Reviewed Exceptions (" + data.cleared_exceptions.length + ")"));
          data.cleared_exceptions.forEach(function (cl) {
            revBox.appendChild(el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-left:3px solid var(--accent-green);padding:6px;border-radius:4px;margin-bottom:4px;font-size:11px;" }, null, [
              el("div", { style: "font-weight:600;color:var(--accent-green);" }, "Turn " + cl.turn_id + " [" + cl.kind + "]: '" + cl.figure + "'"),
              el("div", { style: "color:var(--text-muted);" }, cl.podcast_sentence)
            ]));
          });
          return revBox;
        })()
      ]);
      rightCol.appendChild(mainCard);
    }

    function triggerBuild(epId, dryRun) {
      var msg = dryRun ? "Running dry-run fidelity check..." : "Triggering Edge TTS audio synthesis...";
      alert(msg);
      fetch("/api/episodes/" + epId + "/build?dry_run=" + (dryRun ? "true" : "false"), {
        method: "POST"
      }).then(function (r) {
        if (!r.ok) {
          return r.json().then(function (err) { throw new Error(err.detail || "Build failed"); });
        }
        return r.json();
      }).then(function (res) {
        alert("Operation successful: " + (res.result ? res.result.status || "built" : "done"));
        loadEpisodes();
      }).catch(function (err) {
        alert("Build refused or failed: " + err.message);
        loadEpisodes();
      });
    }

    loadEpisodes();
  }

  window.JarvisModules["episodes"] = { load: load };
})();
