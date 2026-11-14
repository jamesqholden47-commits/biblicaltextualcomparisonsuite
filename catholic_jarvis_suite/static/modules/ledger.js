/* Question Ledger tab (module id "ledger").
 * Every piece of log text goes in through textContent (el() below); nothing is inserted as raw HTML. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

  var STATUS_BUTTONS = [
    ["open", "Open"],
    ["answered", "Answered"],
    ["dropped", "Dropped"],
    ["not-a-question", "Not a question"]
  ];
  var STATUS_COLOR = {
    "unreviewed": "var(--text-dim)", "open": "var(--accent-cyan)", "answered": "var(--accent-green)",
    "dropped": "var(--accent-red)", "not-a-question": "var(--text-muted)"
  };
  var PAGE = 50;

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
    "border-radius:4px;padding:5px 8px;font-size:12px;";
  var BTN_CSS = "background:var(--bg-card);color:var(--text-muted);border:1px solid var(--border);" +
    "border-radius:4px;padding:4px 10px;font-size:11px;cursor:pointer;";

  // C007: the question's first meaningful words, for the Recall search the "Find in Recall" button opens.
  // Skips filler words (English and Spanish) and keeps at most `max` words, in order.
  var STOP = {};
  ("a an and are as at be but by can could did do does for from had has have how i if in is it its me my of on or our " +
   "please so that the their then there these this to up us was we were what when where which who why will with would you your " +
   "el la los las un una y o de del en que se es por para con lo al como mi su").split(" ").forEach(function (w) { STOP[w] = 1; });
  function firstWords(text, max) {
    var out = [];
    var toks = String(text || "").replace(/https?:\/\/\S+/g, " ").split(/\s+/);
    for (var i = 0; i < toks.length && out.length < (max || 5); i++) {
      var w = toks[i].replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, "");
      if (w.length < 2 || STOP[w.toLowerCase()]) continue;
      out.push(w);
    }
    return out.join(" ");
  }

  function load(root) {
    root.textContent = "";
    root.style.cssText = "padding:16px;color:var(--text-main);";

    var state = { offset: 0, total: 0, shown: [] };

    var title = el("div", { style: "display:flex;align-items:baseline;gap:12px;margin-bottom:10px;" }, null, [
      el("h2", { style: "margin:0;font-size:16px;color:var(--accent-gold);" }, "Question Ledger"),
      el("span", { style: "font-size:11px;color:var(--text-dim);" },
        "every question or request you sent an AI, whether the next reply looks answered, and which may have been dropped")
    ]);

    var fStatus = el("select", { style: INPUT_CSS }, null, [
      el("option", { value: "" }, "any status"),
      el("option", { value: "unreviewed" }, "unreviewed"),
      el("option", { value: "open" }, "open"),
      el("option", { value: "answered" }, "answered"),
      el("option", { value: "dropped" }, "dropped"),
      el("option", { value: "not-a-question" }, "not-a-question")
    ]);
    var fSurface = el("select", { style: INPUT_CSS }, null, [
      el("option", { value: "" }, "any surface"),
      el("option", { value: "CL" }, "Claude (CL)"),
      el("option", { value: "AG" }, "Antigravity (AG)")
    ]);
    var fFrom = el("input", { type: "date", style: INPUT_CSS, title: "from date" });
    var fTo = el("input", { type: "date", style: INPUT_CSS, title: "to date" });
    var fText = el("input", { type: "text", placeholder: "text in question, reply or later message", style: INPUT_CSS + "min-width:240px;" });
    var fMissed = el("input", { type: "checkbox", id: "ledger-missed" });
    var fMissedLbl = el("label", { for: "ledger-missed", style: "font-size:12px;color:var(--text-muted);display:flex;align-items:center;gap:4px;" }, null,
      [fMissed, el("span", null, "possibly missed only")]);
    var fStrong = el("input", { type: "checkbox", id: "ledger-strong" });
    var fStrongLbl = el("label", { for: "ledger-strong", style: "font-size:12px;color:var(--text-muted);display:flex;align-items:center;gap:4px;" }, null,
      [fStrong, el("span", null, "strong signals only")]);
    var bSearch = el("button", { style: BTN_CSS + "color:var(--accent-gold);border-color:var(--accent-gold);" }, "Apply");
    var bReset = el("button", { style: BTN_CSS }, "Reset");
    var bRebuild = el("button", { style: BTN_CSS, title: "Re-extract from the logs. Your marks are not touched." }, "Rebuild list");
    var bExport = el("button", { style: BTN_CSS, title: "Markdown checklist of the filtered list" }, "Export .md");

    var bar = el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px;" }, null,
      [fStatus, fSurface, fFrom, fTo, fText, fMissedLbl, fStrongLbl, bSearch, bReset, bRebuild, bExport]);

    var summary = (window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading()
      : el("div", { style: "font-size:12px;color:var(--text-muted);margin-bottom:8px;" }, "Loading...");
    var list = el("div");
    var pager = el("div", { style: "display:flex;gap:8px;align-items:center;margin:12px 0;font-size:12px;color:var(--text-muted);" });

    root.appendChild(title);
    root.appendChild(bar);
    root.appendChild(summary);
    root.appendChild(list);
    root.appendChild(pager);

    function qs(withPaging) {
      var p = new URLSearchParams();
      if (fStatus.value) p.set("status", fStatus.value);
      if (fSurface.value) p.set("surface", fSurface.value);
      if (fFrom.value) p.set("date_from", fFrom.value);
      if (fTo.value) p.set("date_to", fTo.value);
      if (fText.value.trim()) p.set("text", fText.value.trim());
      if (fMissed.checked) p.set("missed", "true");
      if (fStrong.checked) p.set("strong", "true");
      if (withPaging) { p.set("limit", String(PAGE)); p.set("offset", String(state.offset)); }
      return p.toString();
    }

    function pill(text, color) {
      return el("span", { style: "font-size:10px;padding:1px 6px;border-radius:8px;border:1px solid " + color +
        ";color:" + color + ";white-space:nowrap;" }, text);
    }

    function card(q) {
      var statusPill = pill(q.status, STATUS_COLOR[q.status] || "var(--text-dim)");
      var head = el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:6px;font-size:11px;color:var(--text-dim);" }, null, [
        el("span", null, q.date || "no date"),
        pill(q.surface === "CL" ? "Claude" : "Antigravity", "var(--accent-cyan)"),
        pill(q.kind, "var(--text-muted)"),
        statusPill
      ]);
      if (q.missed) head.appendChild(pill("possibly missed", "var(--accent-red)"));
      if (q.no_reply) head.appendChild(pill("no reply logged", "var(--accent-gold)"));
      if (q.reply_after_other_user) head.appendChild(pill("another message sent before the reply", "var(--accent-gold)"));

      var qtext = q.text;
      var qbody = el("div", { style: "font-size:13px;white-space:pre-wrap;word-break:break-word;" },
        qtext.length > 500 ? qtext.slice(0, 500) + " ..." : qtext);
      var kids = [head, qbody];
      if (qtext.length > 500) {
        var more = el("a", { href: "#", style: "font-size:11px;color:var(--accent-cyan);" }, "show all stored text (" + q.text_len + " characters in the message)");
        var open = false;
        more.addEventListener("click", function (e) {
          e.preventDefault();
          open = !open;
          qbody.textContent = open ? qtext : qtext.slice(0, 500) + " ...";
          more.textContent = open ? "show less" : "show all stored text (" + q.text_len + " characters in the message)";
        });
        kids.push(more);
      }

      if (q.reply) {
        var rdet = el("details", { style: "margin-top:6px;" }, null, [
          el("summary", { style: "font-size:11px;color:var(--text-muted);cursor:pointer;" },
            "reply excerpt (first " + q.reply.length + " of " + q.reply_len + " characters)"),
          el("div", { style: "font-size:12px;color:var(--text-muted);white-space:pre-wrap;word-break:break-word;margin-top:4px;padding-left:8px;border-left:2px solid var(--border);" }, q.reply)
        ]);
        kids.push(rdet);
      }

      (q.signals || []).forEach(function (s) {
        var why = s.reason === "previous" ? "follows this question" :
          "refers back to it (shares: " + (s.shared || []).join(", ") + ")";
        kids.push(el("div", { style: "margin-top:6px;padding:6px 8px;border-left:3px solid var(--accent-red);background:var(--bg-panel);font-size:12px;" }, null, [
          el("div", { style: "color:var(--accent-red);font-size:11px;" },
            "missed signal \"" + s.phrase + "\" (" + s.strength + ", " + why + ") at " + s.ts),
          el("div", { style: "color:var(--text-muted);white-space:pre-wrap;word-break:break-word;margin-top:2px;" }, s.text)
        ]));
      });

      var btns = el("div", { style: "display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;align-items:center;" });
      STATUS_BUTTONS.forEach(function (sb) {
        var active = q.status === sb[0];
        var b = el("button", { "data-status": sb[0], style: BTN_CSS + (active ?
          "color:var(--bg-base);background:" + STATUS_COLOR[sb[0]] + ";border-color:" + STATUS_COLOR[sb[0]] + ";" : "") }, sb[1]);
        b.addEventListener("click", function () { mark(q, sb[0]); });
        btns.appendChild(b);
      });
      if (q.status !== "unreviewed") {
        var clr = el("button", { style: BTN_CSS + "border-style:dashed;" }, "clear mark");
        clr.addEventListener("click", function () { mark(q, "unreviewed"); });
        btns.appendChild(clr);
      }
      // C007: jump to Recall with this question's first meaningful words
      var finder = el("button", { "data-action": "find-in-recall", title: "Search every conversation and file for these words in the Recall tab",
        style: BTN_CSS + "color:var(--accent-cyan);border-color:var(--accent-cyan);margin-left:auto;" }, "Find in Recall");
      finder.addEventListener("click", function () {
        var words = firstWords(q.text, 5);
        if (words && window.JarvisOpen) window.JarvisOpen("recall", { q: words });
      });
      btns.appendChild(finder);
      kids.push(btns);

      return el("div", { class: "ledger-card", "data-id": q.id,
        style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px 12px;margin-bottom:8px;" }, null, kids);
    }

    function mark(q, status) {
      fetch("/api/ledger/mark", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: q.id, status: status })
      }).then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      }).then(function () { refresh(); })
        .catch(function (e) { summary.textContent = "Could not save the mark: " + e; });
    }

    function renderPager() {
      pager.textContent = "";
      var from = state.total ? state.offset + 1 : 0;
      var to = Math.min(state.offset + PAGE, state.total);
      var prev = el("button", { style: BTN_CSS }, "Prev");
      var next = el("button", { style: BTN_CSS }, "Next");
      prev.disabled = state.offset <= 0;
      next.disabled = state.offset + PAGE >= state.total;
      prev.addEventListener("click", function () { state.offset = Math.max(0, state.offset - PAGE); refresh(); });
      next.addEventListener("click", function () { state.offset += PAGE; refresh(); });
      pager.appendChild(prev);
      pager.appendChild(el("span", null, from + " to " + to + " of " + state.total));
      pager.appendChild(next);
    }

    function refresh() {
      fetch("/api/ledger/questions?" + qs(true))
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(function (d) {
          state.total = d.total;
          var c = d.counts || {};
          summary.textContent = d.total + " of " + d.all_total + " questions shown. unreviewed " + (c.unreviewed || 0) +
            ", open " + (c.open || 0) + ", answered " + (c.answered || 0) + ", dropped " + (c.dropped || 0) +
            ", not-a-question " + (c["not-a-question"] || 0) + " (in the filtered list).";
          list.textContent = "";
          if (!d.items.length) list.appendChild(el("div", { style: "color:var(--text-dim);padding:12px;" }, "Nothing matches these filters."));
          d.items.forEach(function (q) { list.appendChild(card(q)); });
          renderPager();
        })
        .catch(function (e) { summary.textContent = "Could not load the ledger: " + e; });
    }

    function apply() { state.offset = 0; refresh(); }

    bSearch.addEventListener("click", apply);
    fText.addEventListener("keydown", function (e) { if (e.key === "Enter") apply(); });
    [fStatus, fSurface, fFrom, fTo, fMissed, fStrong].forEach(function (n) { n.addEventListener("change", apply); });
    bReset.addEventListener("click", function () {
      fStatus.value = ""; fSurface.value = ""; fFrom.value = ""; fTo.value = ""; fText.value = ""; fMissed.checked = false; fStrong.checked = false;
      apply();
    });
    bRebuild.addEventListener("click", function () {
      summary.textContent = "Rebuilding from the logs...";
      fetch("/api/ledger/rebuild", { method: "POST" })
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
        .then(function () { apply(); })
        .catch(function (e) { summary.textContent = "Rebuild failed: " + e; });
    });
    bExport.addEventListener("click", function () {
      window.open("/api/ledger/export.md?" + qs(false), "_blank");
    });

    refresh();
  }

  window.JarvisModules["ledger"] = { load: load, firstWords: firstWords };
})();
