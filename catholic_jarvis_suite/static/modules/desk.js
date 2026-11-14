/* Did I Cook? debate desk tab (module id "desk").
 * Reconstructs live Discord debate state (Rule 15), checks factual claims against
 * James's own files and _NEVER_DEPLOY_LIST.md, and prepares paste-ready Discord text
 * and worker briefs.
 * Every piece of log/user text is inserted via textContent; nothing is inserted as raw HTML. */
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

    var currentThreadId = null;
    var allThreads = [];

    // Header
    var header = el("div", { style: "display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;border-bottom:1px solid var(--border);padding-bottom:10px;" }, null, [
      el("div", null, null, [
        el("h2", { style: "margin:0 0 4px 0;font-size:18px;color:var(--accent-gold);" }, "Did I Cook? — Debate Desk"),
        el("span", { style: "font-size:12px;color:var(--text-dim);" },
          "Reconstruct live Discord threads (Rule 15), check claims against your verified corpus & never-deploy list, and generate paste-ready replies & briefs.")
      ]),
      el("div", { style: "display:flex;gap:8px;" }, null, [
        el("button", { style: BTN_GOLD, onclick: function () { showNewThreadModal(); } }, "+ New Thread")
      ])
    ]);

    // Top control bar
    var threadSelect = el("select", { style: INPUT_CSS + "min-width:280px;", onchange: function () {
      currentThreadId = this.value;
      if (currentThreadId) loadThread(currentThreadId);
      else renderEmpty();
    }});
    var refreshBtn = el("button", { style: BTN_CSS, onclick: function () { loadThreads(); } }, "Refresh Threads");
    var topBar = el("div", { style: "display:flex;gap:10px;align-items:center;margin-bottom:16px;" }, null, [
      el("span", { style: "font-size:12px;color:var(--text-muted);font-weight:600;" }, "Active Thread:"),
      threadSelect,
      refreshBtn
    ]);

    // Main workspace container (2 columns: left for thread/log/drafts, right for report/brief/checks)
    var workspace = el("div", { style: "display:grid;grid-template-columns:1fr 1fr;gap:16px;" });
    var leftCol = el("div");
    var rightCol = el("div");
    workspace.appendChild(leftCol);
    workspace.appendChild(rightCol);

    root.appendChild(header);
    root.appendChild(topBar);
    root.appendChild(workspace);

    function renderEmpty() {
      leftCol.textContent = "";
      rightCol.textContent = "";
      leftCol.appendChild(el("div", { style: CARD_CSS + "text-align:center;padding:30px;" }, null, [
        el("div", { style: "font-size:14px;color:var(--text-muted);margin-bottom:12px;" }, "No debate thread selected."),
        el("button", { style: BTN_GOLD, onclick: function () { showNewThreadModal(); } }, "Create a Thread to Get Started")
      ]));
    }

    function showNewThreadModal() {
      var titleIn = el("input", { style: INPUT_CSS + "width:100%;box-sizing:border-box;margin-bottom:8px;", placeholder: "Thread Title (e.g. Athiest friend on Papacy)" });
      var oppIn = el("input", { style: INPUT_CSS + "width:100%;box-sizing:border-box;margin-bottom:8px;", placeholder: "Opponent handle (optional)" });
      var posIn = el("textarea", { style: INPUT_CSS + "width:100%;box-sizing:border-box;height:60px;margin-bottom:8px;", placeholder: "James's position / thesis in one sentence" });
      var logIn = el("textarea", { style: INPUT_CSS + "width:100%;box-sizing:border-box;height:120px;margin-bottom:12px;", placeholder: "Paste raw Discord log here (optional now, can paste later)" });

      var modalBox = el("div", { style: "position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:9999;" }, null, [
        el("div", { style: "background:var(--bg-panel);border:1px solid var(--border);border-radius:8px;padding:20px;width:500px;max-width:90%;color:var(--text-main);" }, null, [
          el("h3", { style: "margin:0 0 12px 0;color:var(--accent-gold);" }, "Create New Debate Thread"),
          el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:6px;" }, "Title:"),
          titleIn,
          el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:6px;" }, "Opponent Handle:"),
          oppIn,
          el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:6px;" }, "James's Stance / Thesis:"),
          posIn,
          el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:6px;" }, "Pasted Discord Log:"),
          logIn,
          el("div", { style: "display:flex;justify-content:flex-end;gap:8px;" }, null, [
            el("button", { style: BTN_CSS, onclick: function () { document.body.removeChild(modalBox); } }, "Cancel"),
            el("button", { style: BTN_GOLD, onclick: function () {
              var payload = {
                title: titleIn.value.trim() || "Untitled thread",
                opponent: oppIn.value.trim(),
                position: posIn.value.trim(),
                log: logIn.value
              };
              fetch("/api/desk/threads", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
              }).then(function (res) { return res.json(); }).then(function (data) {
                document.body.removeChild(modalBox);
                currentThreadId = data.id;
                loadThreads();
              });
            }}, "Create Thread")
          ])
        ])
      ]);
      document.body.appendChild(modalBox);
    }

    function loadThreads() {
      fetch("/api/desk/threads").then(function (res) { return res.json(); }).then(function (data) {
        allThreads = data.threads || [];
        threadSelect.textContent = "";
        if (allThreads.length === 0) {
          threadSelect.appendChild(el("option", { value: "" }, "No threads available"));
          renderEmpty();
          return;
        }
        allThreads.forEach(function (t) {
          var opt = el("option", { value: t.id }, t.title + (t.archived ? " (archived)" : ""));
          if (t.id === currentThreadId) opt.selected = true;
          threadSelect.appendChild(opt);
        });
        if (!currentThreadId && allThreads.length > 0) {
          currentThreadId = allThreads[0].id;
        }
        if (currentThreadId) loadThread(currentThreadId);
      });
    }

    function loadThread(tid) {
      leftCol.textContent = "";
      rightCol.textContent = "";
      var loading = (window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading thread state...")
        : el("div", { style: "color:var(--text-muted);padding:20px;" }, "Loading thread state...");
      leftCol.appendChild(loading);

      fetch("/api/desk/threads/" + tid + "/state?check=1")
        .then(function (res) {
          if (!res.ok) throw new Error("Thread not found");
          return res.json();
        })
        .then(function (state) {
          return fetch("/api/desk/threads/" + tid).then(function (r) { return r.json(); }).then(function (rawThread) {
            renderThreadView(rawThread, state);
          });
        })
        .catch(function (err) {
          leftCol.textContent = "";
          leftCol.appendChild(el("div", { style: "color:var(--accent-red);" }, "Error loading thread: " + err.message));
        });
    }

    function renderThreadView(thread, state) {
      leftCol.textContent = "";
      rightCol.textContent = "";

      // Thread Metadata & Log Card
      var metaCard = el("div", { style: CARD_CSS }, null, [
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;" }, null, [
          el("h3", { style: "margin:0;font-size:15px;color:var(--accent-gold);" }, thread.title),
          el("div", { style: "display:flex;gap:6px;" }, null, [
            pill(thread.handles ? thread.handles.join(", ") : "JamesQ", "var(--accent-cyan)"),
            thread.opponent ? pill("vs " + thread.opponent, "var(--text-muted)") : null
          ])
        ]),
        thread.position ? el("div", { style: "font-size:12px;color:var(--text-muted);margin-bottom:10px;font-style:italic;" }, "Position: " + thread.position) : null,
        el("details", { style: "margin-bottom:10px;" }, null, [
          el("summary", { style: "font-size:11px;color:var(--text-dim);cursor:pointer;margin-bottom:6px;" },
            "Edit thread properties & Discord log (" + (thread.log ? thread.log.length : 0) + " chars)"),
          el("div", { style: "margin-top:8px;" }, null, [
            el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:4px;" }, "Position / Thesis:"),
            (function () {
              var posEdit = el("input", { style: INPUT_CSS + "width:100%;box-sizing:border-box;margin-bottom:8px;", value: thread.position || "" });
              var logEdit = el("textarea", { style: INPUT_CSS + "width:100%;box-sizing:border-box;height:120px;margin-bottom:8px;", value: thread.log || "" });
              var saveBtn = el("button", { style: BTN_GOLD, onclick: function () {
                saveBtn.disabled = true;
                saveBtn.textContent = "Saving...";
                fetch("/api/desk/threads/" + thread.id, {
                  method: "PUT",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ position: posEdit.value, log: logEdit.value })
                }).then(function () { loadThread(thread.id); });
              }}, "Save & Reconstruct");
              return el("div", null, null, [
                posEdit,
                el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:4px;" }, "Pasted Discord Log:"),
                logEdit,
                saveBtn
              ]);
            })()
          ])
        ]),
        // Stats summary
        (function () {
          var p = state.parse || {};
          var s = p.stats || {};
          var sm = state.summary || {};
          return el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;font-size:11px;padding:6px 8px;background:var(--bg-card);border-radius:4px;" }, null, [
            el("span", null, "Messages: " + (s.n_messages || 0)),
            el("span", { style: "color:var(--accent-cyan);" }, "James: " + (s.n_james || 0)),
            el("span", null, "Format: " + (p.format || "none")),
            el("span", { style: "color:var(--accent-green);" }, "Sent drafts: " + ((sm.sent_verbatim || 0) + (sm.sent_adapted || 0))),
            el("span", { style: "color:var(--accent-gold);" }, "Carried forward: " + ((sm.unsent || 0) + (sm.partial || 0)))
          ]);
        })()
      ]);
      leftCol.appendChild(metaCard);

      // Latest State Card (Rule 15 Reconstruction)
      var reconCard = el("div", { style: CARD_CSS }, null, [
        el("h4", { style: "margin:0 0 10px 0;font-size:13px;color:var(--accent-cyan);" }, "Live Thread Reconstruction"),
        (function () {
          var tl = state.their_latest;
          if (!tl || !tl.messages || tl.messages.length === 0) {
            return el("div", { style: "font-size:12px;color:var(--text-dim);" }, "No opponent messages found in pasted log.");
          }
          var msgs = tl.messages.map(function (m) {
            return el("div", { style: "margin-bottom:4px;padding-left:8px;border-left:2px solid var(--accent-red);font-size:12px;" }, null, [
              el("div", { style: "font-size:10px;color:var(--text-dim);" }, "[" + m.time + "] " + m.author + ":"),
              el("div", { style: "white-space:pre-wrap;" }, m.text || "(attachment only)")
            ]);
          });
          var note = tl.james_posted_since ?
            el("div", { style: "font-size:11px;color:var(--accent-gold);margin-top:6px;" },
              "Note: James has posted " + tl.james_posted_since + " message(s) since this. Opponent has not answered yet.") : null;
          return el("div", null, null, [
            el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:4px;font-weight:600;" }, "THEIR LATEST (" + tl.author + "):"),
            el("div", null, null, msgs),
            note
          ]);
        })()
      ]);
      leftCol.appendChild(reconCard);

      // Saved Drafts Card
      var draftsCard = el("div", { style: CARD_CSS }, null, [
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;" }, null, [
          el("h4", { style: "margin:0;font-size:13px;color:var(--accent-gold);" }, "Saved Drafts (" + (thread.drafts || []).length + ")"),
          el("button", { style: BTN_CSS, onclick: function () { showAddDraftModal(thread.id); } }, "+ Add Draft")
        ]),
        (function () {
          var list = el("div");
          if (!state.drafts || state.drafts.length === 0) {
            list.appendChild(el("div", { style: "font-size:12px;color:var(--text-dim);" }, "No drafts saved for this thread."));
            return list;
          }
          state.drafts.forEach(function (d) {
            var m = d.match || {};
            var st = m.state || d.status;
            var stColor = st === "sent_verbatim" ? "var(--accent-green)" :
              st === "sent_adapted" ? "var(--accent-green)" :
              st === "partial" ? "var(--accent-gold)" :
              st === "dropped" ? "var(--accent-red)" : "var(--accent-cyan)";
            var stLabel = st === "sent_verbatim" ? "SENT VERBATIM" :
              st === "sent_adapted" ? "SENT ADAPTED" :
              st === "partial" ? "PARTIALLY SENT" :
              st === "dropped" ? "DROPPED" : "UNSENT";

            var dCard = el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:8px;margin-bottom:8px;" }, null, [
              el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;" }, null, [
                el("div", { style: "display:flex;gap:6px;align-items:center;" }, null, [
                  el("span", { style: "font-size:12px;font-weight:600;color:var(--accent-gold);" }, d.id),
                  d.label ? el("span", { style: "font-size:11px;color:var(--text-muted);" }, "(" + d.label + ")") : null,
                  pill(stLabel, stColor)
                ]),
                el("div", { style: "display:flex;gap:4px;" }, null, [
                  d.status !== "dropped" ? el("button", { style: BTN_CSS + "padding:2px 6px;font-size:10px;", onclick: function () {
                    updateDraftStatus(thread.id, d.id, "dropped");
                  }}, "Drop") : el("button", { style: BTN_CSS + "padding:2px 6px;font-size:10px;", onclick: function () {
                    updateDraftStatus(thread.id, d.id, "draft");
                  }}, "Restore")
                ])
              ]),
              el("div", { style: "font-size:12px;white-space:pre-wrap;max-height:120px;overflow-y:auto;color:var(--text-main);" }, d.text)
            ]);
            list.appendChild(dCard);
          });
          return list;
        })()
      ]);
      leftCol.appendChild(draftsCard);

      // RIGHT COLUMN: Actions (Generate Report, Generate Brief, Quick Check)
      var actionsCard = el("div", { style: CARD_CSS }, null, [
        el("h4", { style: "margin:0 0 10px 0;font-size:14px;color:var(--accent-gold);" }, "Debate Actions"),
        el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;" }, null, [
          el("button", { style: BTN_GOLD, onclick: function () { generateReport(thread.id); } }, "Generate Discord Report"),
          el("button", { style: BTN_CYAN, onclick: function () { generateBrief(thread.id, false); } }, "Generate AI Brief (Standard)"),
          el("button", { style: BTN_CSS, onclick: function () { generateBrief(thread.id, true); } }, "Generate Brief (Rule 17 Socratic)")
        ])
      ]);
      rightCol.appendChild(actionsCard);

      var outputContainer = el("div", { id: "desk-output-area" });
      rightCol.appendChild(outputContainer);
    }

    function showAddDraftModal(tid) {
      var labelIn = el("input", { style: INPUT_CSS + "width:100%;box-sizing:border-box;margin-bottom:8px;", placeholder: "Label (e.g. Sola Scriptura objection reply)" });
      var textIn = el("textarea", { style: INPUT_CSS + "width:100%;box-sizing:border-box;height:120px;margin-bottom:12px;", placeholder: "Draft text..." });

      var modalBox = el("div", { style: "position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;z-index:9999;" }, null, [
        el("div", { style: "background:var(--bg-panel);border:1px solid var(--border);border-radius:8px;padding:20px;width:500px;max-width:90%;color:var(--text-main);" }, null, [
          el("h3", { style: "margin:0 0 12px 0;color:var(--accent-gold);" }, "Add Saved Draft"),
          el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:4px;" }, "Label:"),
          labelIn,
          el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:4px;" }, "Draft Text:"),
          textIn,
          el("div", { style: "display:flex;justify-content:flex-end;gap:8px;" }, null, [
            el("button", { style: BTN_CSS, onclick: function () { document.body.removeChild(modalBox); } }, "Cancel"),
            el("button", { style: BTN_GOLD, onclick: function () {
              var text = textIn.value.trim();
              if (!text) return;
              fetch("/api/desk/threads/" + tid + "/drafts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text, label: labelIn.value.trim() })
              }).then(function () {
                document.body.removeChild(modalBox);
                loadThread(tid);
              });
            }}, "Save Draft")
          ])
        ])
      ]);
      document.body.appendChild(modalBox);
    }

    function updateDraftStatus(tid, did, status) {
      fetch("/api/desk/threads/" + tid + "/drafts/" + did, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: status })
      }).then(function () { loadThread(tid); });
    }

    function generateReport(tid) {
      var outArea = document.getElementById("desk-output-area");
      outArea.textContent = "";
      var spin = el("div", { style: "color:var(--text-muted);padding:12px;" }, "Scanning corpus & checking claims against _NEVER_DEPLOY_LIST.md...");
      outArea.appendChild(spin);

      fetch("/api/desk/threads/" + tid + "/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paste: "stack", kinds: ["SUBJECT"] })
      })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        outArea.textContent = "";
        var card = el("div", { style: CARD_CSS }, null, [
          el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;" }, null, [
            el("h4", { style: "margin:0;font-size:13px;color:var(--accent-gold);" }, "Discord Debate Report (5 Sections)"),
            el("button", { style: BTN_GOLD, onclick: function () {
              navigator.clipboard.writeText(data.paste || "");
              alert("Copied PASTE section to clipboard!");
            }}, "Copy PASTE for Discord (" + (data.paste_chars || 0) + " chars)")
          ]),
          data.over_discord_limit ? el("div", { style: "background:rgba(255,50,50,0.2);border:1px solid var(--accent-red);padding:6px;border-radius:4px;font-size:11px;color:var(--accent-red);margin-bottom:8px;" },
            "Warning: Paste exceeds 2,000 character Discord limit (" + data.paste_chars + " chars). Split into " + (data.paste_parts ? data.paste_parts.length : 1) + " messages.") : null,
          data.paste_problems_left && data.paste_problems_left.length > 0 ? el("div", { style: "color:var(--accent-red);font-size:11px;margin-bottom:6px;" },
            "Paste formatting warnings: " + data.paste_problems_left.join(", ")) : null,
          // Report viewer
          el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:4px;" }, "Five-Section Report Text:"),
          el("textarea", {
            style: INPUT_CSS + "width:100%;box-sizing:border-box;height:240px;font-family:monospace;font-size:11px;",
            readonly: true,
            value: data.text || ""
          }),
          // Claims Checked Table
          el("h5", { style: "margin:10px 0 6px 0;font-size:12px;color:var(--accent-cyan);" }, "Factual Claims Provenance (" + (data.claims ? data.claims.length : 0) + ")"),
          (function () {
            var cList = el("div", { style: "max-height:160px;overflow-y:auto;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:6px;" });
            if (!data.claims || data.claims.length === 0) {
              cList.appendChild(el("div", { style: "font-size:11px;color:var(--text-dim);" }, "No factual claims identified in paste text."));
              return cList;
            }
            data.claims.forEach(function (c) {
              var provColor = c.never_deploy && c.never_deploy.length > 0 ? "var(--accent-red)" :
                c.provenance === "checked" ? "var(--accent-green)" :
                c.provenance === "warned" ? "var(--accent-red)" : "var(--accent-gold)";
              cList.appendChild(el("div", { style: "font-size:11px;margin-bottom:4px;border-bottom:1px solid var(--border);padding-bottom:3px;" }, null, [
                el("div", { style: "font-weight:600;color:var(--text-main);" }, '"' + c.text + '"'),
                el("div", { style: "color:" + provColor + ";font-size:10px;" }, c.suffix || c.provenance)
              ]));
            });
            return cList;
          })()
        ]);
        outArea.appendChild(card);
      });
    }

    function generateBrief(tid, socratic) {
      var outArea = document.getElementById("desk-output-area");
      outArea.textContent = "";
      var spin = el("div", { style: "color:var(--text-muted);padding:12px;" }, "Generating WORKER_CONTRACT v1 brief...");
      outArea.appendChild(spin);

      fetch("/api/desk/threads/" + tid + "/brief", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: "claude", socratic: socratic, recent: 0, kinds: ["SUBJECT"] })
      })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        outArea.textContent = "";
        var card = el("div", { style: CARD_CSS }, null, [
          el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;" }, null, [
            el("h4", { style: "margin:0;font-size:13px;color:var(--accent-cyan);" },
              "Worker Brief (" + (socratic ? "Rule 17 Socratic" : "Standard") + ") — Task " + (data.task_id || "")),
            el("button", { style: BTN_CYAN, onclick: function () {
              navigator.clipboard.writeText(data.text || "");
              alert("Copied complete brief to clipboard!");
            }}, "Copy Brief for AI (" + (data.chars || 0) + " chars)")
          ]),
          data.warnings && data.warnings.length > 0 ? el("div", { style: "color:var(--accent-gold);font-size:11px;margin-bottom:6px;" },
            "Notice: " + data.warnings.join("; ")) : null,
          el("div", { style: "font-size:11px;color:var(--text-dim);margin-bottom:4px;" }, "Gate: " + (data.gate || "")),
          el("textarea", {
            style: INPUT_CSS + "width:100%;box-sizing:border-box;height:300px;font-family:monospace;font-size:11px;",
            readonly: true,
            value: data.text || ""
          })
        ]);
        outArea.appendChild(card);
      });
    }

    // Initial load
    loadThreads();
  }

  window.JarvisModules["desk"] = { load: load };
})();
