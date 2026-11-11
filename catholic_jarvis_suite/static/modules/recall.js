/* Recall tab: "where did X go?" search over every conversation and every project file.
   Registers window.JarvisModules["recall"]. All log/file text reaches the page through
   textContent / createTextNode only (never the HTML-string setter): logs contain HTML and angle brackets. */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

  var PAGE = 25;

  var CSS = [
    ".rc-wrap{padding:16px;display:flex;flex-direction:column;gap:12px;max-width:1100px;margin:0 auto;}",
    ".rc-bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;}",
    ".rc-in,.rc-sel{background:var(--bg-card);border:1px solid var(--border);color:var(--text-main);border-radius:6px;padding:7px 10px;font-size:13px;}",
    ".rc-in{flex:1 1 320px;min-width:200px;}",
    ".rc-in:focus,.rc-sel:focus{outline:none;border-color:var(--accent-gold);}",
    ".rc-btn{background:var(--bg-card);border:1px solid var(--border);color:var(--text-main);border-radius:6px;padding:6px 12px;font-size:12px;cursor:pointer;}",
    ".rc-btn:hover{border-color:var(--accent-gold);color:var(--accent-gold);}",
    ".rc-btn[disabled]{opacity:.5;cursor:default;}",
    ".rc-status{font-size:11px;color:var(--text-dim);display:flex;gap:10px;flex-wrap:wrap;align-items:center;}",
    ".rc-stale{color:var(--accent-gold);}",
    ".rc-summary{font-size:12px;color:var(--text-muted);}",
    ".rc-card{background:var(--bg-panel);border:1px solid var(--border);border-radius:8px;padding:10px 12px;display:flex;flex-direction:column;gap:6px;}",
    ".rc-head{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:11px;color:var(--text-dim);}",
    ".rc-badge{font-weight:600;letter-spacing:.04em;padding:1px 7px;border-radius:4px;font-size:10px;}",
    ".rc-b-CL{background:rgba(212,175,55,.15);color:var(--accent-gold);}",
    ".rc-b-AG{background:rgba(56,189,248,.15);color:var(--accent-cyan);}",
    ".rc-b-FILE{background:rgba(16,185,129,.15);color:var(--accent-green);}",
    ".rc-role{border:1px solid var(--border);border-radius:4px;padding:0 6px;}",
    ".rc-loc{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text-muted);word-break:break-all;}",
    ".rc-snip{font-size:13px;line-height:1.5;color:var(--text-main);white-space:pre-wrap;word-break:break-word;}",
    ".rc-snip mark{background:var(--accent-gold-soft);color:var(--accent-gold);border-radius:2px;padding:0 1px;}",
    ".rc-title{font-size:13px;font-weight:600;color:var(--text-main);}",
    ".rc-empty{text-align:center;color:var(--text-dim);padding:32px;font-size:13px;}",
    ".rc-err{color:var(--accent-red);font-size:13px;padding:8px 0;}",
  ].join("\n");

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined && text !== null) n.textContent = String(text);
    return n;
  }

  function opt(sel, value, label) {
    var o = document.createElement("option");
    o.value = value;
    o.textContent = label;
    sel.appendChild(o);
  }

  function copyText(text, btn) {
    var done = function () {
      var old = btn.textContent;
      btn.textContent = "copied";
      setTimeout(function () { btn.textContent = old; }, 1200);
    };
    var fallback = function () {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { btn.textContent = "copy failed"; }
      document.body.removeChild(ta);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else {
      fallback();
    }
  }

  // Build the snippet from DOM nodes: plain text with <mark> elements over the highlight ranges.
  function renderSnippet(text, ranges) {
    var box = el("div", "rc-snip");
    var pos = 0;
    (ranges || []).forEach(function (r) {
      var s = Math.max(pos, r[0]), e = Math.max(s, r[1]);
      if (s > pos) box.appendChild(document.createTextNode(text.slice(pos, s)));
      if (e > s) box.appendChild(el("mark", "", text.slice(s, e)));
      pos = e;
    });
    if (pos < text.length) box.appendChild(document.createTextNode(text.slice(pos)));
    return box;
  }

  function renderCard(r) {
    var card = el("div", "rc-card");
    var head = el("div", "rc-head");
    head.appendChild(el("span", "rc-badge rc-b-" + r.surface, r.surface === "CL" ? "CLAUDE" : r.surface === "AG" ? "ANTIGRAVITY" : "FILE"));
    head.appendChild(el("span", "", r.date || ""));
    if (r.type === "conversation") head.appendChild(el("span", "rc-role", r.role));
    else if (r.file_kind) head.appendChild(el("span", "rc-role", r.file_kind));
    card.appendChild(head);

    if (r.type === "file" && r.title) card.appendChild(el("div", "rc-title", r.title));

    var loc = el("div", "rc-head");
    var locText = r.type === "conversation"
      ? "session " + r.sid + "  (message " + r.message_no + ")"
      : (r.path + ":" + r.line);
    loc.appendChild(el("span", "rc-loc", locText));
    var b = el("button", "rc-btn", r.type === "conversation" ? "copy session id" : "copy path:line");
    b.type = "button";
    b.addEventListener("click", function () { copyText(r.copy, b); });
    loc.appendChild(b);
    if (r.type === "file" && r.path) {
      // C007: hand the file to the Reader tab (window.JarvisOpen is defined by index.html)
      var ob = el("button", "rc-btn rc-open", "Open in Reader");
      ob.type = "button";
      ob.title = "Open this file in the Reader tab";
      ob.addEventListener("click", function () {
        if (window.JarvisOpen) window.JarvisOpen("reader", { path: r.path });
      });
      loc.appendChild(ob);
    }
    card.appendChild(loc);

    card.appendChild(renderSnippet(r.snippet || "", r.highlights));
    return card;
  }

  // C007: window.JarvisOpen("recall", {q}) (from the Question Ledger, Loose Ends ...) switches to this tab and
  // 350 ms later fires "jarvis:open-recall". The listener is at script level; an early event waits in pendingQ.
  var recallApi = null;
  var pendingQ = null;
  window.addEventListener("jarvis:open-recall", function (ev) {
    var d = (ev && ev.detail) || {};
    if (typeof d.q !== "string" || !d.q.trim()) return;
    if (recallApi) recallApi.search(d.q); else pendingQ = d.q;
  });

  window.JarvisModules["recall"] = {
    load: function (root) {
      if (!document.getElementById("rc-style")) {
        var st = document.createElement("style");
        st.id = "rc-style";
        st.textContent = CSS;
        document.head.appendChild(st);
      }
      root.textContent = "";
      var wrap = el("div", "rc-wrap");
      root.appendChild(wrap);

      var bar = el("div", "rc-bar");
      var q = el("input", "rc-in");
      q.type = "search";
      q.placeholder = "Where did it go?  e.g.  Trinity chapter,  T1-T6,  \"twelve signs\",  dikaio*";
      q.setAttribute("aria-label", "Recall search");
      var surface = el("select", "rc-sel");
      opt(surface, "", "All surfaces");
      opt(surface, "CL", "Claude");
      opt(surface, "AG", "Antigravity");
      opt(surface, "FILE", "Project files");
      var scope = el("select", "rc-sel");
      opt(scope, "all", "Conversations + files");
      opt(scope, "conversations", "Conversations only");
      opt(scope, "files", "Files only");
      var role = el("select", "rc-sel");
      opt(role, "", "Any role");
      opt(role, "user", "James (user)");
      opt(role, "assistant", "AI (assistant)");
      var mode = el("select", "rc-sel");
      opt(mode, "all", "All words");
      opt(mode, "any", "Any word");
      opt(mode, "phrase", "Exact phrase");
      var sort = el("select", "rc-sel");
      opt(sort, "rank", "Best match");
      opt(sort, "newest", "Newest first");
      opt(sort, "oldest", "Oldest first");
      [q, surface, scope, role, mode, sort].forEach(function (n) { bar.appendChild(n); });
      wrap.appendChild(bar);

      var statusRow = el("div", "rc-status");
      var statusText = el("span", "", "checking index...");
      var rebuild = el("button", "rc-btn", "Rebuild index");
      rebuild.type = "button";
      statusRow.appendChild(statusText);
      statusRow.appendChild(rebuild);
      wrap.appendChild(statusRow);

      var summary = el("div", "rc-summary");
      var list = el("div");
      list.style.display = "flex";
      list.style.flexDirection = "column";
      list.style.gap = "8px";
      var more = el("button", "rc-btn", "Show more");
      more.type = "button";
      more.style.alignSelf = "center";
      more.style.display = "none";
      wrap.appendChild(summary);
      wrap.appendChild(list);
      wrap.appendChild(more);

      var seq = 0, shown = 0, timer = null;

      function loadStatus() {
        fetch("/api/recall/status").then(function (r) { return r.json(); }).then(function (s) {
          statusText.className = "";
          if (!s.exists) {
            statusText.textContent = "No index yet. Press Rebuild index.";
            statusText.className = "rc-stale";
            return;
          }
          var t = s.messages.toLocaleString() + " messages, " + s.files.toLocaleString() + " files ("
            + s.file_chunks.toLocaleString() + " passages), built " + (s.built_at || "?").slice(0, 16).replace("T", " ")
            + " UTC, fingerprint " + s.fingerprint;
          if (s.stale) {
            t += "  -  STALE: " + (s.conversations_stale ? "new conversation activity" : "")
              + (s.conversations_stale && s.files_stale ? " and " : "") + (s.files_stale ? "changed files" : "")
              + " since the last build";
            statusText.className = "rc-stale";
          }
          statusText.textContent = t;
        }).catch(function (e) { statusText.textContent = "status unavailable: " + e; });
      }

      function params(offset) {
        var p = new URLSearchParams();
        p.set("q", q.value);
        if (surface.value) p.set("surface", surface.value);
        if (scope.value !== "all") p.set("scope", scope.value);
        if (role.value) p.set("role", role.value);
        p.set("mode", mode.value);
        p.set("sort", sort.value);
        p.set("limit", String(PAGE));
        p.set("offset", String(offset));
        return p.toString();
      }

      function run(append) {
        var my = ++seq;
        if (!append) { shown = 0; list.textContent = ""; }
        if (!q.value.trim()) {
          summary.textContent = "";
          more.style.display = "none";
          return;
        }
        fetch("/api/recall/search?" + params(shown)).then(function (r) {
          return r.json().then(function (d) { return { status: r.status, d: d }; });
        }).then(function (x) {
          if (my !== seq) return;           // a newer search superseded this one
          var d = x.d;
          if (x.status === 409) {
            summary.textContent = "";
            list.appendChild(el("div", "rc-empty", "The Recall index has not been built. Press Rebuild index."));
            more.style.display = "none";
            return;
          }
          if (x.status !== 200) {
            list.appendChild(el("div", "rc-err", "Search failed (" + x.status + ")."));
            return;
          }
          (d.results || []).forEach(function (r) { list.appendChild(renderCard(r)); });
          shown += (d.results || []).length;
          summary.textContent = d.total.toLocaleString() + " match" + (d.total === 1 ? "" : "es")
            + " in " + d.took_ms + " ms" + (d.note ? "  -  " + d.note : "");
          if (!append && !d.results.length) list.appendChild(el("div", "rc-empty", d.note || "Nothing found. Try fewer words, or Any word."));
          more.style.display = shown < d.total ? "" : "none";
        }).catch(function (e) {
          if (my === seq) list.appendChild(el("div", "rc-err", "Search failed: " + e));
        });
      }

      function schedule() {
        clearTimeout(timer);
        timer = setTimeout(function () { run(false); }, 300);
      }

      q.addEventListener("input", schedule);
      q.addEventListener("keydown", function (e) { if (e.key === "Enter") { clearTimeout(timer); run(false); } });
      [surface, scope, role, mode, sort].forEach(function (n) { n.addEventListener("change", function () { run(false); }); });
      more.addEventListener("click", function () { run(true); });
      rebuild.addEventListener("click", function () {
        rebuild.disabled = true;
        statusText.className = "";
        statusText.textContent = "rebuilding (can take a minute)...";
        fetch("/api/recall/rebuild", { method: "POST" }).then(function (r) { return r.json(); }).then(function (d) {
          statusText.textContent = d.rebuilt
            ? "rebuilt in " + d.seconds + " s"
            : "index already current (" + d.reason + ")";
          loadStatus();
          if (q.value.trim()) run(false);
        }).catch(function (e) { statusText.textContent = "rebuild failed: " + e; })
          .then(function () { rebuild.disabled = false; });
      });

      recallApi = {
        search: function (text) {
          surface.value = ""; scope.value = "all"; role.value = ""; mode.value = "all"; sort.value = "rank";
          q.value = text;
          clearTimeout(timer);
          run(false);
          q.focus();
        }
      };
      if (pendingQ !== null) { var pq = pendingQ; pendingQ = null; recallApi.search(pq); }

      loadStatus();
      q.focus();
    }
  };
})();
