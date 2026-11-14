/* Visual Audit & Comparison Matrix tab (module id "audit").
 * Enforces Rule 11 (Absolute Lossless Consolidation: Zero dropped sentences)
 * and Rule 13 (Subject vs Infrastructure Scoping).
 */
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
    "border-radius:4px;padding:6px 10px;font-size:12px;font-family:inherit;width:100%;box-sizing:border-box;";
  var TEXTAREA_CSS = "background:var(--bg-card);color:var(--text-main);border:1px solid var(--border);" +
    "border-radius:4px;padding:8px 10px;font-size:12px;font-family:monospace;width:100%;height:160px;box-sizing:border-box;resize:vertical;";
  var BTN_CSS = "background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);" +
    "border-radius:4px;padding:6px 14px;font-size:12px;cursor:pointer;font-family:inherit;font-weight:600;";
  var BTN_GREEN = BTN_CSS + "color:var(--ok);border-color:var(--ok);background:rgba(46,164,78,0.1);";
  var BTN_GOLD = BTN_CSS + "color:var(--accent-gold);border-color:var(--accent-gold);";
  var CARD_CSS = "background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:16px;margin-bottom:16px;";

  function csvField(v) {
    v = v === undefined || v === null ? "" : String(v);
    return /[",\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v;
  }

  // 2026-11-12: the audit matrix is ad-hoc (pasted source/target, nothing stored server-side),
  // so unlike Recall/Catalog's export there is no list to re-fetch -- the result the user just
  // saw IS the export, built client-side from what's already in the browser rather than a round
  // trip that would re-run the whole diff for no reason.
  function downloadDiffCsv(res) {
    var lines = ["status,badge,source_sentence,target_sentence"];
    (res.diff_blocks || []).forEach(function (b) {
      lines.push([b.status, b.badge, b.source_text || "", b.target_text || ""].map(csvField).join(","));
    });
    var blob = new Blob([lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = el("a", { href: url, download: "audit_matrix_" + new Date().toISOString().replace(/[:.]/g, "-") + ".csv" });
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function load(root) {
    root.textContent = "";
    root.style.cssText = "padding:20px;color:var(--text-main);max-width:1400px;margin:0 auto;";

    // Header
    var header = el("div", { style: "margin-bottom:20px;" }, null, [
      el("h2", { style: "margin:0 0 6px 0;color:var(--accent-gold);font-size:22px;" }, "⚖️ Visual Audit & Comparison Matrix"),
      el("p", { style: "margin:0;color:var(--text-muted);font-size:13px;line-height:1.5;" },
        "Automated Rule 11 Lossless Verifier & Rule 13 Infrastructure Scoping. Evaluates source against target line-by-line to guarantee zero dropped sentences, citations, or propositions."
      )
    ]);
    root.appendChild(header);

    // Campaigns Selector Card
    var campaignCard = el("div", { style: CARD_CSS }, null, [
      el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;" }, null, [
        el("strong", { style: "font-size:14px;color:var(--accent-cyan);" }, "🎯 8 Laser Deduplication Campaigns (730 Duplicate Clusters)"),
        el("span", { style: "font-size:11px;color:var(--text-muted);" }, "Select a campaign to auto-fill canonical anchor target")
      ]),
      el("select", { id: "audit-campaign-select", style: INPUT_CSS }, null, [
        el("option", { value: "" }, "-- Select a Deduplication Campaign --")
      ])
    ]);
    root.appendChild(campaignCard);

    // Form Card: Source vs Target
    var formCard = el("div", { style: CARD_CSS }, null, [
      el("div", { style: "display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:12px;" }, null, [
        el("div", null, null, [
          el("label", { style: "display:block;font-size:12px;font-weight:600;margin-bottom:4px;color:var(--accent-gold);" }, "Source Text / Candidate Draft (to be merged)"),
          el("textarea", { id: "audit-source-text", style: TEXTAREA_CSS, placeholder: "Paste source markdown or note text here..." })
        ]),
        el("div", null, null, [
          el("label", { style: "display:block;font-size:12px;font-weight:600;margin-bottom:4px;color:var(--accent-cyan);" }, "Target Text / Master Dossier (destination)"),
          el("textarea", { id: "audit-target-text", style: TEXTAREA_CSS, placeholder: "Paste destination dossier or chapter text here..." })
        ])
      ]),
      el("div", { style: "display:flex;gap:10px;justify-content:flex-end;" }, null, [
        el("button", {
          id: "audit-preset-lossless",
          style: BTN_CSS,
          onclick: function () {
            document.getElementById("audit-source-text").value = 
              "Deuteronomy 17:8-12 proves the Old Covenant had a Supreme Court of appeal.\n" +
              "In Matthew 16:18-19, Jesus transferred the Davidic keys to Peter.\n" +
              "The St. Thomas Christians of Malabar preserved the Eucharistic sacrifice in isolation.";
            document.getElementById("audit-target-text").value = 
              "# Chapter 2: The Living Court\n\n" +
              "Deuteronomy 17:8-12 proves the Old Covenant had a Supreme Court of appeal.\n" +
              "Furthermore, in Matthew 16:18-19, Jesus transferred the Davidic keys to Peter.\n" +
              "As seen in Chapter 4, the St. Thomas Christians of Malabar preserved the Eucharistic sacrifice in isolation.";
          }
        }, "Load Lossless Sample"),
        el("button", {
          id: "audit-preset-loss",
          style: BTN_CSS,
          onclick: function () {
            document.getElementById("audit-source-text").value = 
              "Deuteronomy 17:8-12 proves the Old Covenant had a Supreme Court of appeal.\n" +
              "In Matthew 16:18-19, Jesus transferred the Davidic keys to Peter.\n" +
              "The St. Thomas Christians of Malabar preserved the Eucharistic sacrifice in isolation.";
            document.getElementById("audit-target-text").value = 
              "# Chapter 2: The Living Court\n\n" +
              "Deuteronomy 17:8-12 proves the Old Covenant had a Supreme Court of appeal.\n" +
              "In Matthew 16:18-19, Jesus transferred the Davidic keys to Peter.";
          }
        }, "Load Dropped-Sentence Sample (Fail Case)"),
        el("button", {
          id: "audit-run-btn",
          style: BTN_GREEN,
          onclick: runAudit
        }, "🚀 Run Visual Audit & Lossless Check")
      ])
    ]);
    root.appendChild(formCard);

    // Results Container
    var resultsContainer = el("div", { id: "audit-results", style: "display:none;" });
    root.appendChild(resultsContainer);

    // Fetch campaigns
    fetch("/api/audit/campaigns")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var sel = document.getElementById("audit-campaign-select");
        if (data.campaigns) {
          data.campaigns.forEach(function (c) {
            var opt = el("option", { value: c.id }, c.id + ": " + c.name + " (" + c.cluster_count + " clusters, " + c.token_estimate + " tokens)");
            sel.appendChild(opt);
          });
        }
      })
      .catch(function (err) {
        console.error("Failed to fetch campaigns:", err);
      });

    function runAudit() {
      var src = document.getElementById("audit-source-text").value;
      var tgt = document.getElementById("audit-target-text").value;

      if (!src.trim() && !tgt.trim()) {
        alert("Please enter source and target text.");
        return;
      }

      var runBtn = document.getElementById("audit-run-btn");
      runBtn.disabled = true;
      runBtn.textContent = "Auditing...";

      fetch("/api/audit/matrix", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_text: src, target_text: tgt })
      })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function (res) {
          renderResults(res);
        })
        .catch(function (err) {
          alert("Audit error: " + err.message);
        })
        .finally(function () {
          runBtn.disabled = false;
          runBtn.textContent = "🚀 Run Visual Audit & Lossless Check";
        });
    }

    function renderResults(res) {
      resultsContainer.textContent = "";
      resultsContainer.style.display = "block";

      var sum = res.summary;
      var passed = sum.rule_11_passed;

      // Verdict Banner
      var bannerBg = passed ? "rgba(46,164,78,0.15)" : "rgba(207,34,46,0.15)";
      var bannerBorder = passed ? "var(--ok)" : "var(--bad)";
      var bannerColor = passed ? "var(--ok)" : "var(--bad)";
      var verdictText = passed ? "✅ PASS: 100% LOSSLESS CONSOLIDATION (Rule 11 Verified)" : "❌ FAIL: " + sum.omitted_count + " SENTENCE(S) DROPPED (Rule 11 Violation)";

      var banner = el("div", {
        style: "padding:16px;border-radius:6px;border:1px solid " + bannerBorder + ";background:" + bannerBg + ";margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;"
      }, null, [
        el("div", null, null, [
          el("div", { style: "font-size:16px;font-weight:bold;color:" + bannerColor + ";" }, verdictText),
          el("div", { style: "font-size:12px;color:var(--text-muted);margin-top:4px;" }, 
            passed ? "Every substantive sentence from the source survives in the destination text." : "Substantive sentences were detected in the source that are missing in the target."
          )
        ]),
        el("div", { style: "font-size:24px;font-weight:bold;color:" + bannerColor + ";" }, sum.preservation_rate + "%")
      ]);
      resultsContainer.appendChild(banner);

      // Rule 13 Infrastructure Warning
      if (res.rule_13_audit && (res.rule_13_audit.source_infra || res.rule_13_audit.target_infra)) {
        var infraWarning = el("div", {
          style: "padding:12px;border-radius:6px;border:1px solid var(--warn);background:rgba(210,153,34,0.15);margin-bottom:16px;color:var(--warn);"
        }, null, [
          el("strong", { style: "display:block;margin-bottom:4px;" }, "⚠️ RULE 13 WARNING: Infrastructure Content Detected"),
          el("div", { style: "font-size:12px;" }, 
            (res.rule_13_audit.source_infra ? res.rule_13_audit.source_reason + " " : "") +
            (res.rule_13_audit.target_infra ? res.rule_13_audit.target_reason : "")
          )
        ]);
        resultsContainer.appendChild(infraWarning);
      }

      // Stats Bar
      var stats = el("div", {
        style: "display:grid;grid-template-columns:repeat(5, 1fr);gap:12px;background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:16px;text-align:center;"
      }, null, [
        el("div", null, null, [
          el("div", { style: "font-size:11px;color:var(--text-muted);text-transform:uppercase;" }, "Source Sentences"),
          el("div", { style: "font-size:20px;font-weight:bold;margin-top:4px;" }, String(sum.total_source_sentences))
        ]),
        el("div", null, null, [
          el("div", { style: "font-size:11px;color:var(--text-muted);text-transform:uppercase;" }, "Preserved"),
          el("div", { style: "font-size:20px;font-weight:bold;color:var(--ok);margin-top:4px;" }, String(sum.preserved_count))
        ]),
        el("div", null, null, [
          el("div", { style: "font-size:11px;color:var(--text-muted);text-transform:uppercase;" }, "Omitted (Lost)"),
          el("div", { style: "font-size:20px;font-weight:bold;color:var(--bad);margin-top:4px;" }, String(sum.omitted_count))
        ]),
        el("div", null, null, [
          el("div", { style: "font-size:11px;color:var(--text-muted);text-transform:uppercase;" }, "Target Added"),
          el("div", { style: "font-size:20px;font-weight:bold;color:var(--info);margin-top:4px;" }, String(sum.added_count))
        ]),
        el("div", null, null, [
          el("div", { style: "font-size:11px;color:var(--text-muted);text-transform:uppercase;" }, "Preservation Rate"),
          el("div", { style: "font-size:20px;font-weight:bold;color:" + bannerColor + ";margin-top:4px;" }, sum.preservation_rate + "%")
        ])
      ]);
      resultsContainer.appendChild(stats);

      // Diff Table
      var tableCard = el("div", { style: CARD_CSS }, null, [
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;" }, null, [
          el("h3", { style: "margin:0;font-size:16px;color:var(--accent-gold);" }, "Sentence-Level Red / Green Comparison Grid"),
          el("button", { style: BTN_CSS, onclick: function () { downloadDiffCsv(res); } }, "Export CSV")
        ])
      ]);

      var table = el("table", { style: "width:100%;border-collapse:collapse;font-size:12px;" });
      var thead = el("thead", null, null, [
        el("tr", { style: "border-bottom:2px solid var(--border);text-align:left;" }, null, [
          el("th", { style: "padding:8px;width:150px;color:var(--text-muted);" }, "STATUS"),
          el("th", { style: "padding:8px;width:45%;color:var(--text-muted);" }, "SOURCE SENTENCE (CANDIDATE DRAFT)"),
          el("th", { style: "padding:8px;width:45%;color:var(--text-muted);" }, "TARGET SENTENCE (DESTINATION DOSSIER)")
        ])
      ]);
      table.appendChild(thead);

      var tbody = el("tbody");
      (res.diff_blocks || []).forEach(function (b) {
        var trBg = "transparent";
        var badgeColor = "var(--text-muted)";
        var badgeBg = "rgba(255,255,255,0.05)";

        if (b.status === "equal") {
          badgeColor = "var(--ok)";
          badgeBg = "rgba(46,164,78,0.15)";
        } else if (b.status === "omitted" || b.status === "delete") {
          trBg = "rgba(207,34,46,0.1)";
          badgeColor = "var(--bad)";
          badgeBg = "rgba(207,34,46,0.2)";
        } else if (b.status === "added") {
          trBg = "rgba(46,164,78,0.08)";
          badgeColor = "var(--ok)";
          badgeBg = "rgba(46,164,78,0.2)";
        } else if (b.status === "relocated") {
          trBg = "rgba(210,153,34,0.08)";
          badgeColor = "var(--warn)";
          badgeBg = "rgba(210,153,34,0.2)";
        }

        var badgeSpan = el("span", {
          style: "padding:2px 8px;border-radius:4px;font-size:10px;font-weight:bold;color:" + badgeColor + ";background:" + badgeBg + ";"
        }, b.badge);

        var tr = el("tr", { style: "border-bottom:1px solid var(--border);background:" + trBg + ";" }, null, [
          el("td", { style: "padding:8px;vertical-align:top;" }, null, [badgeSpan]),
          el("td", { style: "padding:8px;font-family:monospace;line-height:1.4;vertical-align:top;" }, b.source_text || "—"),
          el("td", { style: "padding:8px;font-family:monospace;line-height:1.4;vertical-align:top;" }, b.target_text || "—")
        ]);
        tbody.appendChild(tr);
      });

      table.appendChild(tbody);
      tableCard.appendChild(table);
      resultsContainer.appendChild(tableCard);
    }
  }

  window.JarvisModules.audit = { load: load };
})();
