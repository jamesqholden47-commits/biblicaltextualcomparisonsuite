"""
Cross-tab links (task C007, 2026-10-06).

  Reader   : window event "jarvis:open-reader" {path} opens a document; a path box does the same.
  Recall   : every file result gets an "Open in Reader" button -> window.JarvisOpen("reader", {path});
             window event "jarvis:open-recall" {q} runs a search.
  Ledger   : every question card gets "Find in Recall" -> window.JarvisOpen("recall", {q: first meaningful words}).

The page scripts are plain browser JavaScript, so they are executed here under Node with a small fake
DOM (no network, no browser). Each scenario records what the script asked the page to do (fetch URLs,
JarvisOpen calls) and the test asserts on that record. Falsification cases are included: an event with no
path or no query must do nothing, a stop-word-only question must not send James anywhere, and a conversation
result must not get an "Open in Reader" button.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE_ROOT = os.path.dirname(HERE)
if SUITE_ROOT not in sys.path:
    sys.path.insert(0, SUITE_ROOT)

MODULES_DIR = os.path.join(SUITE_ROOT, "static", "modules")
NODE = shutil.which("node")

HARNESS = r"""
"use strict";
const fs = require("fs");
const path = require("path");
const modulesDir = process.argv[2];

class FakeNode {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase(); this.children = []; this.listeners = {}; this.style = {};
    this.attrs = {}; this._text = ""; this._html = ""; this.className = ""; this.value = ""; this.dataset = {};
    this.parentNode = null; this.selected = false; this.disabled = false;
  }
  appendChild(c) { if (c) { c.parentNode = this; this.children.push(c); } return c; }
  insertBefore(c, ref) { c.parentNode = this; const i = this.children.indexOf(ref); if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; }
  removeChild(c) { const i = this.children.indexOf(c); if (i >= 0) this.children.splice(i, 1); return c; }
  setAttribute(k, v) { this.attrs[k] = String(v); if (k === "id") this.ctx.byId[v] = this; }
  getAttribute(k) { return this.attrs[k] === undefined ? null : this.attrs[k]; }
  addEventListener(t, f) { (this.listeners[t] = this.listeners[t] || []).push(f); }
  fire(t, ev) { (this.listeners[t] || []).forEach(f => f(Object.assign({ preventDefault() {}, stopPropagation() {} }, ev || {}))); }
  set textContent(v) { this._text = String(v); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(""); }
  set innerHTML(v) { this._html = String(v); this.children = []; this._text = ""; }
  get innerHTML() { return this._html; }
  get firstChild() { return this.children[0] || null; }
  get options() { return this.children.filter(c => c.tagName === "OPTION"); }
  focus() {} select() {} scrollIntoView() {} pause() {} play() {}
  querySelectorAll() { return []; }
  querySelector() { return null; }
}

function walk(node, fn) { fn(node); node.children.forEach(c => walk(c, fn)); }
function findAll(root, pred) { const out = []; walk(root, n => { if (pred(n)) out.push(n); }); return out; }
const tick = (ms) => new Promise(r => setTimeout(r, ms || 25));

// Builds a fresh page context (own window, document, fetch log) and loads one module script into it.
function makeContext(scriptName, routes) {
  const ctx = { byId: {}, fetches: [], opens: [], windowListeners: {} };
  FakeNode.prototype.ctx = ctx;
  const document = {
    head: new FakeNode("head"), body: new FakeNode("body"),
    createElement: t => { const n = new FakeNode(t); n.ctx = ctx; return n; },
    createTextNode: t => { const n = new FakeNode("#text"); n._text = String(t); n.ctx = ctx; return n; },
    getElementById: id => ctx.byId[id] || null,
    execCommand() { return true; },
  };
  const window = {
    JarvisModules: {},
    addEventListener(t, f) { (ctx.windowListeners[t] = ctx.windowListeners[t] || []).push(f); },
    dispatch(t, detail) { (ctx.windowListeners[t] || []).forEach(f => f({ type: t, detail: detail })); },
    JarvisOpen(tab, detail) { ctx.opens.push([tab, detail]); },
    open() {},
  };
  function fetchStub(url) {
    ctx.fetches.push(String(url));
    let hit = null;
    for (const r of routes) if (String(url).indexOf(r.match) === 0 || String(url).indexOf(r.match) > 0) { hit = r; break; }
    const status = hit ? (hit.status || 200) : 404;
    const body = hit ? (typeof hit.body === "function" ? hit.body(String(url)) : hit.body) : {};
    return Promise.resolve({ ok: status < 400, status: status, json: () => Promise.resolve(body) });
  }
  class CustomEvent { constructor(n, o) { this.type = n; this.detail = (o || {}).detail; } }
  const src = fs.readFileSync(path.join(modulesDir, scriptName), "utf8");
  new Function("window", "document", "fetch", "navigator", "CustomEvent", "Audio", src)(
    window, document, fetchStub, {}, CustomEvent, function () { this.play = () => {}; this.pause = () => {}; });
  ctx.window = window; ctx.document = document;
  ctx.mount = function (id) {
    const root = new FakeNode("div"); root.ctx = ctx;
    window.JarvisModules[id].load(root);
    return root;
  };
  return ctx;
}

const results = {};

(async function main() {
  // ---------------------------------------------------------------- ledger: first meaningful words
  {
    const ctx = makeContext("ledger.js", []);
    const fw = ctx.window.JarvisModules.ledger.firstWords;
    results.firstWords = {
      trent: fw("How do I know the Council of Trent actually defined the canon at its fourth session?", 5),
      punct: fw("  ...\"Sola scriptura\" -- where does it appear in Augustine?? ", 5),
      url: fw("see https://example.com/a?b=1 about Eucharist and transubstantiation", 5),
      only_stop: fw("Is it? Do we?", 5),
      empty: fw("", 5),
      accents: fw("¿Cuál es la fe católica sobre la Inmaculada Concepción?", 5),
      cap: fw("one two three four five six seven eight", 5),
    };
  }

  // ---------------------------------------------------------------- ledger: Find in Recall button
  {
    const q1 = { id: "q1", date: "2026-10-01", surface: "CL", kind: "question", status: "open",
      text: "How do I know the Council of Trent actually defined the canon at its fourth session?", text_len: 84,
      reply: "", reply_len: 0, signals: [] };
    const q2 = { id: "q2", date: "2026-10-02", surface: "AG", kind: "question", status: "open",
      text: "Is it?", text_len: 6, reply: "", reply_len: 0, signals: [] };
    const ctx = makeContext("ledger.js", [
      { match: "/api/ledger/questions", body: { total: 2, all_total: 2, counts: {}, items: [q1, q2] } },
    ]);
    const root = ctx.mount("ledger");
    await tick();
    const btns = findAll(root, n => n.attrs["data-action"] === "find-in-recall");
    results.ledger = { n_buttons: btns.length, labels: btns.map(b => b.textContent) };
    btns[0].fire("click");
    results.ledger.after_first = JSON.parse(JSON.stringify(ctx.opens));
    btns[1].fire("click");                       // question made only of filler words: must not navigate
    results.ledger.after_second = JSON.parse(JSON.stringify(ctx.opens));
  }

  // ---------------------------------------------------------------- recall
  const recallRoutes = [
    { match: "/api/recall/status", body: { exists: true, messages: 1, files: 1, file_chunks: 1, built_at: "2026-10-06T00:00:00", fingerprint: "fp", stale: false } },
    { match: "/api/recall/search", body: { total: 2, took_ms: 1, results: [
      { type: "file", surface: "FILE", date: "2026-10-01", file_kind: "SUBJECT", title: "A file", path: "C:\\proj\\a.md", rel_path: "a.md", line: 3, snippet: "hello", highlights: [[0, 2]], copy: "C:\\proj\\a.md:3" },
      { type: "conversation", surface: "CL", role: "user", date: "2026-10-01", sid: "s1", message_no: 2, snippet: "conv text", highlights: [], copy: "s1" },
    ] } },
  ];
  {
    const ctx = makeContext("recall.js", recallRoutes);
    const root = ctx.mount("recall");
    await tick();
    ctx.fetches.length = 0;
    ctx.window.dispatch("jarvis:open-recall", { q: "trinity chapter" });
    await tick();
    const input = findAll(root, n => n.tagName === "INPUT")[0];
    const searchFetch = ctx.fetches.filter(u => u.indexOf("/api/recall/search") === 0);
    const openBtns = findAll(root, n => n.tagName === "BUTTON" && n.textContent === "Open in Reader");
    results.recall = {
      input_value: input.value, search_fetches: searchFetch,
      n_open_buttons: openBtns.length,
      n_cards: findAll(root, n => n.className === "rc-card").length,
    };
    openBtns[0].fire("click");
    results.recall.opens = JSON.parse(JSON.stringify(ctx.opens));
    // an event with an empty or missing query must not search
    ctx.fetches.length = 0;
    ctx.window.dispatch("jarvis:open-recall", { q: "   " });
    ctx.window.dispatch("jarvis:open-recall", {});
    await tick();
    results.recall.fetches_after_empty_events = ctx.fetches.filter(u => u.indexOf("/api/recall/search") === 0).length;
  }
  {   // event that arrives before the tab has loaded is kept and applied by load()
    const ctx = makeContext("recall.js", recallRoutes);
    ctx.window.dispatch("jarvis:open-recall", { q: "early bird" });
    const root = ctx.mount("recall");
    await tick();
    const input = findAll(root, n => n.tagName === "INPUT")[0];
    results.recall_early = { input_value: input.value, search_fetches: ctx.fetches.filter(u => u.indexOf("/api/recall/search") === 0) };
  }

  // ---------------------------------------------------------------- reader
  const chapterBody = { stem: "06_x", filename: "06_x.md", title: "Ch 6", tag_counts: { V: 0, R: 0, S: 0 }, sections: [], checking_items: [], checking_count: 0, available_tiers: [], html: "" };
  const readerRoutes = [
    { match: "/api/reader/chapters/", body: chapterBody },
    { match: "/api/reader/chapters", body: { chapters: [{ stem: "06_x", title: "Ch 6", filename: "06_x.md", size: 1, path: "C:\\ch\\06_x.md" }], count: 1 } },
    { match: "path=C%3A%5Cbad%5Csecret.md", status: 403, body: { detail: "this path is not in the Reader's allowed set" } },
    { match: "/api/reader/doc?path=", body: { path: "C:\\a\\b.md", stem: "b", filename: "b.md", source: "registry", format: "markdown", bytes: 10, title: "B",
        tag_counts: { V: 1, R: 0, S: 0 }, sections: [], checking_items: [], checking_count: 0, available_tiers: [], parts: [{ index: 0, title: "B", chars: 5 }], part: 0, part_count: 1, html: "<p>x</p>" } },
  ];
  const chapterFetches = ctx => ctx.fetches.filter(u => u.indexOf("/api/reader/chapters/") === 0);
  const docFetches = ctx => ctx.fetches.filter(u => u.indexOf("/api/reader/doc?") === 0);
  {   // 1. event after load; the chapter list must still work
    const ctx = makeContext("reader.js", readerRoutes);
    const root = ctx.mount("reader");
    await tick();
    const select = findAll(root, n => n.tagName === "SELECT")[0];
    results.reader_after = { n_chapter_options: select.options.length, chapter_fetches_before: chapterFetches(ctx) };
    ctx.window.dispatch("jarvis:open-reader", { path: "C:\\a\\b.md" });
    await tick();
    results.reader_after.doc_fetches = docFetches(ctx);
    results.reader_after.msg = ctx.byId["reader-doc-msg"].textContent;
    ctx.window.dispatch("jarvis:open-reader", {});          // no path: nothing happens
    ctx.window.dispatch("jarvis:open-reader", { path: "" });
    await tick();
    results.reader_after.doc_fetches_after_empty = docFetches(ctx).length;
  }
  {   // 2. event BEFORE load, then load: the document wins over the default chapter
    const ctx = makeContext("reader.js", readerRoutes);
    ctx.window.dispatch("jarvis:open-reader", { path: "C:\\a\\b.md" });
    const root = ctx.mount("reader");
    await tick();
    const select = findAll(root, n => n.tagName === "SELECT")[0];
    results.reader_early = { doc_fetches: docFetches(ctx), chapter_fetches: chapterFetches(ctx), n_chapter_options: select.options.length };
  }
  {   // 3. path box (Enter and the button) and a refused path
    const ctx = makeContext("reader.js", readerRoutes);
    const root = ctx.mount("reader");
    await tick();
    const box = findAll(root, n => n.tagName === "INPUT" && (n.attrs.placeholder || "").indexOf("Paste a file path") === 0)[0];
    const openBtn = findAll(root, n => n.tagName === "BUTTON" && n.textContent === "Open document")[0];
    box.value = "   ";                                       // blank: nothing
    box.fire("keydown", { key: "Enter" });
    openBtn.fire("click");
    await tick();
    results.reader_box = { fetches_blank: docFetches(ctx).length };
    box.value = "C:\\a\\b.md";
    box.fire("keydown", { key: "x" });                       // not Enter: nothing
    results.reader_box.fetches_nonenter = docFetches(ctx).length;
    box.fire("keydown", { key: "Enter" });
    await tick();
    results.reader_box.fetches_enter = docFetches(ctx);
    box.value = "C:\\bad\\secret.md";
    openBtn.fire("click");
    await tick();
    results.reader_box.refused_msg = ctx.byId["reader-doc-msg"].textContent;
    results.reader_box.main_text = (ctx.byId["reader-main-pane"] || {}).textContent;
  }
  console.log(JSON.stringify(results));
})().catch(e => { console.error("HARNESS ERROR", e && e.stack || e); process.exit(2); });
"""


@unittest.skipUnless(NODE, "node is not installed; the browser scripts cannot be exercised")
class CrossLinkScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.harness = os.path.join(cls.tmp.name, "harness.js")
        with open(cls.harness, "w", encoding="utf-8") as fh:
            fh.write(HARNESS)
        res = subprocess.run([NODE, cls.harness, MODULES_DIR], capture_output=True, text=True, encoding="utf-8", timeout=60)
        if res.returncode != 0:
            raise AssertionError("harness failed (exit %s): %s %s" % (res.returncode, res.stdout[-500:], res.stderr[-1500:]))
        cls.r = json.loads(res.stdout.strip().splitlines()[-1])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ----------------------------------------------------------------------- question 4 (Question Ledger)
    def test_first_meaningful_words(self):
        fw = self.r["firstWords"]
        self.assertEqual(fw["trent"], "know Council Trent actually defined")
        self.assertEqual(fw["punct"], "Sola scriptura appear Augustine")
        self.assertEqual(fw["url"], "see about Eucharist transubstantiation")
        self.assertEqual(fw["only_stop"], "")
        self.assertEqual(fw["empty"], "")
        self.assertEqual(fw["accents"], "Cuál fe católica sobre Inmaculada")
        self.assertEqual(fw["cap"], "one two three four five")

    def test_every_ledger_card_has_find_in_recall_and_it_navigates(self):
        led = self.r["ledger"]
        self.assertEqual(led["n_buttons"], 2)                       # one per card
        self.assertEqual(set(led["labels"]), {"Find in Recall"})
        self.assertEqual(led["after_first"], [["recall", {"q": "know Council Trent actually defined"}]])

    def test_falsification_filler_only_question_does_not_navigate(self):
        # the second card's text is "Is it?": there is nothing to search for, so the click must not send James anywhere
        self.assertEqual(self.r["ledger"]["after_second"], self.r["ledger"]["after_first"])

    # ----------------------------------------------------------------------- question 3 (Recall)
    def test_recall_runs_a_search_when_the_open_event_arrives(self):
        rc = self.r["recall"]
        self.assertEqual(rc["input_value"], "trinity chapter")
        self.assertEqual(len(rc["search_fetches"]), 1)
        self.assertIn("q=trinity+chapter", rc["search_fetches"][0])
        self.assertEqual(rc["n_cards"], 2)

    def test_only_file_results_get_open_in_reader(self):
        rc = self.r["recall"]
        self.assertEqual(rc["n_open_buttons"], 1)                   # the conversation result has none
        self.assertEqual(rc["opens"], [["reader", {"path": "C:\\proj\\a.md"}]])

    def test_falsification_recall_events_without_a_query_do_nothing(self):
        self.assertEqual(self.r["recall"]["fetches_after_empty_events"], 0)

    def test_recall_event_before_the_tab_loaded_is_not_lost(self):
        e = self.r["recall_early"]
        self.assertEqual(e["input_value"], "early bird")
        self.assertEqual(len(e["search_fetches"]), 1)

    # ----------------------------------------------------------------------- question 2 (Reader)
    def test_reader_opens_a_document_on_the_event_and_keeps_the_chapter_list(self):
        a = self.r["reader_after"]
        self.assertEqual(a["n_chapter_options"], 1)                 # chapter list still populated
        self.assertEqual(a["chapter_fetches_before"], ["/api/reader/chapters/06_x"])   # default chapter still loads
        self.assertEqual(a["doc_fetches"], ["/api/reader/doc?path=C%3A%5Ca%5Cb.md&part=0"])
        self.assertIn("registry document", a["msg"])

    def test_reader_ignores_events_without_a_path(self):
        a = self.r["reader_after"]
        self.assertEqual(a["doc_fetches_after_empty"], 1)           # still only the one real open

    def test_reader_event_before_load_wins_over_the_default_chapter(self):
        e = self.r["reader_early"]
        self.assertEqual(e["doc_fetches"], ["/api/reader/doc?path=C%3A%5Ca%5Cb.md&part=0"])
        self.assertEqual(e["chapter_fetches"], [])                  # the default chapter did not overwrite the document
        self.assertEqual(e["n_chapter_options"], 1)                 # but the list is there for later

    def test_reader_path_box(self):
        b = self.r["reader_box"]
        self.assertEqual(b["fetches_blank"], 0)
        self.assertEqual(b["fetches_nonenter"], 0)
        self.assertEqual(b["fetches_enter"], ["/api/reader/doc?path=C%3A%5Ca%5Cb.md&part=0"])
        self.assertIn("Not allowed", b["refused_msg"])              # a 403 is shown to James, not swallowed
        self.assertIn("allowed set", b["refused_msg"])


class StaticWiringTests(unittest.TestCase):
    """Cheap source checks that hold even when node is missing."""

    def read(self, name):
        with open(os.path.join(MODULES_DIR, name), "r", encoding="utf-8") as fh:
            return fh.read()

    def test_scripts_use_the_bus_names_index_html_defines(self):
        with open(os.path.join(SUITE_ROOT, "static", "index.html"), "r", encoding="utf-8") as fh:
            index = fh.read()
        self.assertIn("window.JarvisOpen = function", index)
        self.assertIn('"jarvis:open-" + tabId', index)
        self.assertIn("jarvis:open-reader", self.read("reader.js"))
        self.assertIn("jarvis:open-recall", self.read("recall.js"))
        self.assertIn('JarvisOpen("reader"', self.read("recall.js"))
        self.assertIn('JarvisOpen("recall"', self.read("ledger.js"))

    def test_no_raw_html_insertion_of_user_text_in_the_new_code(self):
        # recall.js and ledger.js must stay free of the HTML-string setter; reader.js has the one server-escaped use
        self.assertNotIn("innerHTML", self.read("recall.js"))
        self.assertNotIn("innerHTML", self.read("ledger.js"))
        self.assertEqual(self.read("reader.js").count("innerHTML"), 1)    # the one server-escaped chapter render (pre-existing)

    @unittest.skipUnless(NODE, "node is not installed")
    def test_scripts_parse(self):
        for name in ("reader.js", "recall.js", "ledger.js"):
            res = subprocess.run([NODE, "--check", os.path.join(MODULES_DIR, name)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, name + ": " + res.stderr)


class RecallToReaderCoverageTests(unittest.TestCase):
    """Question 3, end to end on this machine's data: a Recall file result's path, handed to the Reader,
    must either open (200) or be refused with a stated reason (403), never crash (500)."""

    def test_recall_file_paths_never_crash_the_reader(self):
        from fastapi.testclient import TestClient
        from app import app
        client = TestClient(app)
        r = client.get("/api/recall/search", params={"q": "dissertation", "scope": "files", "limit": 25})
        if r.status_code != 200:
            self.skipTest("Recall index not built here")
        # session transcripts are never opened by this suite's tests (project rule: use log_reader for those)
        files = [x for x in r.json()["results"] if x.get("type") == "file" and "_SESSION_TRANSCRIPTS" not in x["path"]]
        self.assertTrue(files)
        codes = {}
        for x in files:
            code = client.get("/api/reader/doc", params={"path": x["path"]}).status_code
            codes[code] = codes.get(code, 0) + 1
            self.assertIn(code, (200, 403, 404, 413), x["path"])
        print("\nC007 recall->reader status codes for %d file results: %s" % (len(files), codes))


if __name__ == "__main__":
    unittest.main()
