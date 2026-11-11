/* Packs — argument preparation by topic (Phase 4, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).
   Each pack gathers what you already have on one recurring topic: the Arena / Pope Tools cards (seeds), your own
   posted replies, replies drafted but never posted, the dossiers, and the planned Volumes chapters. Every entry
   shows its tag and where it came from; [V] appears only with a source on disk. Styles: jarvis.css (.dx-*, .pk-*). */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};
  var S = { list: [], pid: null };

  function el(tag, attrs, kids) {
    var e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "text") e.textContent = v;
      else if (k === "on") Object.keys(v).forEach(function (ev) { e.addEventListener(ev, v[ev]); });
      else e.setAttribute(k, v === true ? "" : v);
    });
    (kids || []).forEach(function (c) { if (c !== null && c !== undefined) e.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return e;
  }
  function get(u) { return fetch(u).then(function (r) { return r.json().then(function (j) { if (!r.ok) throw new Error(j.detail || r.status); return j; }); }); }
  function copy(t, what) { navigator.clipboard.writeText(t).then(function () { if (window.showToast) window.showToast((what || "Copied"), "success"); }); }
  function tagEl(t) { var k = (t || "[S]").charAt(1).toLowerCase(); return el("span", { class: "j-tag " + (k === "v" || k === "r" ? k : "s"), text: t || "[S]" }); }
  function sec(title, n, note) {
    return el("div", { class: "pk-sec" }, [el("h4", { class: "dx-sec", text: title + (n !== undefined ? " (" + n + ")" : "") }), note ? el("div", { class: "fx-muted", text: note }) : null]);
  }

  function load(root) {
    root.textContent = "";
    root.classList.add("dx-root");
    var listBox = el("div", { class: "dx-list" });
    var side = el("div", { class: "dx-side" }, [el("div", { class: "dx-listhead" }, [el("div", { class: "fx-muted", text: "Topics you debate, with everything you have on each." })]), listBox]);
    var main = el("div", { class: "dx-main" }, [el("div", { class: "j-empty", text: "Gathering packs from your debates, cards, dossiers and chapters…" })]);
    root.appendChild(side); root.appendChild(main);
    S.ui = { list: listBox, main: main };
    get("/api/packs").then(function (d) {
      S.list = d.packs;
      S.list.sort(function (a, b) { return (b.n_debates * 3 + b.n_owed + b.n_posted) - (a.n_debates * 3 + a.n_owed + a.n_posted); });
      S.list.forEach(function (p) {
        listBox.appendChild(el("div", { class: "dx-item", "data-id": p.id, on: { click: function () { open(p.id); } } }, [
          el("div", { class: "dx-title" }, [p.title, p.n_owed ? el("span", { class: "dx-badge", title: "drafted replies on this topic not seen posted", text: p.n_owed }) : null]),
          el("div", { class: "fx-muted", text: p.n_debates + " debates · " + p.n_posted + " of your posts · " + p.n_seeds + " cards · " + p.n_dossiers + " dossiers · " + p.n_cards + " drill cards" })
        ]));
      });
      if (S.list.length) open(S.pid || S.list[0].id);
    }).catch(function (e) { main.textContent = "Could not build packs: " + e.message; });
  }

  function open(pid) {
    S.pid = pid;
    document.querySelectorAll("#tab-packs .dx-item").forEach(function (n) { n.classList.toggle("active", n.getAttribute("data-id") === pid); });
    get("/api/packs/" + pid).then(render).catch(function (e) { S.ui.main.textContent = e.message; });
  }

  function render(p) {
    var m = S.ui.main;
    m.textContent = "";
    m.appendChild(el("div", { class: "dx-top" }, [
      el("div", { style: "flex:1;min-width:0" }, [el("h2", { class: "dx-h", text: p.title }),
        el("div", { class: "fx-muted", text: "Matched on: " + p.keywords.slice(0, 12).join(", ") + (p.keywords.length > 12 ? "…" : "") })]),
      el("button", { class: "j-btn primary", title: "Practise the real objections people raised on this topic", on: { click: function () { window.JarvisOpen("drill", { topic: p.id }); } } }, ["Drill this topic"])
    ]));

    // seeds
    m.appendChild(sec("Cards", p.seeds.length, "From the Arena and Pope Tools tabs, with their audited tags."));
    p.seeds.forEach(function (s) {
      m.appendChild(el("details", { class: "dx-point pk-card" }, [
        el("summary", null, [tagEl(s.tag), el("span", { class: "dx-ptitle", text: " " + s.title }), el("span", { class: "fx-muted", text: "  " + s.origin + (s.placed ? " (best match)" : "") })]),
        s.target || s.front ? el("div", { class: "fx-muted", text: [s.front, s.target].filter(Boolean).join(" · ") }) : null,
        s.charge ? el("div", { class: "pk-text" }, [el("strong", { text: "Their charge: " }), s.charge]) : null,
        s.concession ? el("div", { class: "pk-text" }, [el("strong", { text: "Concede first: " }), s.concession]) : null,
        el("div", { class: "pk-text" }, [s.charge ? el("strong", { text: "Answer: " }) : null, s.body]),
        s.long && s.long !== s.body ? el("div", { class: "pk-text", text: s.long }) : null,
        s.proof ? el("div", { class: "pk-text pk-proof", text: s.proof }) : null,
        s.original ? el("div", { class: "pk-text pk-proof", text: s.original }) : null,
        s.soundbite ? el("div", { class: "pk-text" }, [el("strong", { text: "15-second version: " }), s.soundbite]) : null,
        s.claims && s.claims.length ? el("ul", { class: "pk-claims" }, s.claims.map(function (c) { return el("li", null, [tagEl(c.tag), " " + c.text]); })) : null,
        s.locator ? el("div", { class: "fx-muted", text: "Source: " + s.locator }) : null,
        s.audit_note ? el("div", { class: "fx-muted", text: "Audit: " + s.audit_note }) : null,
        s.copy ? el("div", { class: "dx-pactions" }, [el("button", { class: "j-btn", on: { click: function () { copy(s.copy, "Card text copied"); } } }, ["Copy text"])]) : null
      ]));
    });
    if (!p.seeds.length) m.appendChild(el("div", { class: "fx-muted", text: "No card on this topic yet." }));

    // owed
    m.appendChild(sec("Drafted, never seen posted", p.owed.length, "Replies prepared for you in these debates that the logs never show you posting."));
    p.owed.slice(0, 25).forEach(function (o) {
      m.appendChild(el("div", { class: "pk-row", on: { click: function () { window.JarvisOpen("threads", { id: o.thread }); } } }, [
        el("div", { class: "td-main", text: o.title }), el("div", { class: "fx-muted", text: o.thread_title + " · " + o.date + " · " + o.words + " words" })]));
    });

    // posted
    m.appendChild(sec("What you've already argued", p.n_posted, "Your own posts on this topic (40+ words). Tagged [S]: your claims, not yet checked against sources."));
    p.posted.forEach(function (x) {
      m.appendChild(el("details", { class: "dx-point pk-posted" }, [
        el("summary", null, [tagEl(x.tag), el("span", { class: "dx-ptitle", text: " " + x.text.slice(0, 110).replace(/\s+/g, " ") + (x.text.length > 110 ? "…" : "") })]),
        el("div", { class: "dx-text", text: x.text }),
        el("div", { class: "dx-pactions" }, [
          el("span", { class: "fx-muted", text: x.locator + ", " + x.date + "  " }),
          el("button", { class: "j-btn ghost", on: { click: function () { window.JarvisOpen("threads", { id: x.thread, msg: x.msg }); } } }, ["Show in the debate"]),
          el("button", { class: "j-btn ghost", on: { click: function () { copy(x.text, "Post copied"); } } }, ["Copy"])
        ])
      ]));
    });

    // debates
    m.appendChild(sec("Debates on this topic", p.debates.length));
    p.debates.slice(0, 20).forEach(function (t) {
      m.appendChild(el("div", { class: "pk-row", on: { click: function () { window.JarvisOpen("threads", { id: t.id }); } } }, [
        el("div", { class: "td-main" }, [t.title, t.unsent_points ? el("span", { class: "dx-badge", text: t.unsent_points }) : null]),
        el("div", { class: "fx-muted", text: (t.last_ts || "").slice(0, 10) })]));
    });

    // dossiers
    m.appendChild(sec("Dossiers", p.n_dossiers, "Your research documents on this topic. Tag counts show how much of each is verified."));
    p.dossiers.forEach(function (d) {
      var tg = d.tags || {};
      m.appendChild(el("div", { class: "pk-row", title: d.path, on: { click: function () { window.JarvisOpen("files", { path: d.path }); } } }, [
        el("div", { class: "td-main", text: d.title }),
        el("div", { class: "fx-muted", text: (d.words || 0).toLocaleString() + " words · [V] " + (tg.V || 0) + " · [R] " + (tg.R || 0) + " · [S] " + (tg.S || 0) + (d.integrated ? " · already in a book" : "") })]));
    });

    // chapters
    m.appendChild(sec("Volumes chapters", p.n_chapters, "Chapters planned on this topic; when one is final, it becomes the best source here."));
    p.chapters.forEach(function (c) {
      m.appendChild(el("div", { class: "pk-row", on: { click: function () { window.JarvisOpen("books", { chapter: c.id }); } } }, [
        el("div", { class: "td-main" }, [c.title, el("span", { class: "dx-state", text: c.state })]),
        el("div", { class: "fx-muted", text: c.volume + " · " + Math.round((c.words || 0) / 1000) + "k source words" })]));
    });
    m.scrollTop = 0;
  }

  window.JarvisModules.packs = { load: load };
})();
