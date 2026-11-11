"""
Tests for the Recall module (modules/recall_index.py, modules/recall_routes.py,
static/modules/recall.js) and the whole-word topic tagging in session_navigator_engine.py.

Run from the suite folder:   python -m unittest tests.test_recall -v

Two kinds of test:
  * FIXTURE tests build a throw-away SQLite index in a temp dir from planted messages and files,
    and plant defects the feature must catch (falsification).
  * LIVE tests query the real data/recall_fts.sqlite and data/ai_session_index.json.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402
from modules import recall_index as R  # noqa: E402
import session_navigator_engine as ENG  # noqa: E402


def _msg(surface, sid, role, text, ts="2026-10-01T10:00:00.000Z"):
    return {"ts": ts, "surface": surface, "sid": sid, "role": role, "text": text, "file": f"C:\\logs\\{sid}.jsonl"}


class FixtureIndexTests(unittest.TestCase):
    """A small planted index, built through the same refresh() the app uses."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="recall_test_")
        cls.db = os.path.join(cls.tmp, "fixture.sqlite")
        # planted files: the target word sits on a KNOWN line (line 7 of notes.md)
        cls.notes = os.path.join(cls.tmp, "notes.md")
        with open(cls.notes, "w", encoding="utf-8") as fh:
            fh.write("# Notes\n\nfirst paragraph about nothing in particular, long enough to stand alone as a chunk of text.\n\n"
                     "second paragraph, also long enough to stand alone as its own chunk of searchable text here.\n\n"
                     "The quokkaquartz argument appears here and nowhere else in this fixture file at all.\n")
        cls.other = os.path.join(cls.tmp, "other.md")
        with open(cls.other, "w", encoding="utf-8") as fh:
            fh.write("# Other file\n\nNothing here but filler sentences about baptism and sprinkling, padded out to pass the minimum.\n")
        cls.files = [
            {"path": cls.notes, "rel_path": "notes.md", "title": "Fixture notes", "kind": "SUBJECT",
             "size": os.path.getsize(cls.notes), "mtime": os.path.getmtime(cls.notes)},
            {"path": cls.other, "rel_path": "other.md", "title": "Other", "kind": "INFRASTRUCTURE",
             "size": os.path.getsize(cls.other), "mtime": os.path.getmtime(cls.other)},
        ]
        cls.msgs = [
            _msg("CL", "sid-claude-1", "user", "where is the zorblaxian ledger we discussed"),
            _msg("CL", "sid-claude-1", "assistant", "The zorblaxian ledger lives in <b>tests</b> & friends; also quokkaquartz.",
                 ts="2026-10-02T10:00:00.000Z"),
            _msg("AG", "sid-ag-1", "assistant", "Antigravity said something unrelated about incense.",
                 ts="2026-10-03T10:00:00.000Z"),
        ]
        cls.res = R.refresh(db_path=cls.db, messages=cls.msgs, files=cls.files, conv_fp="fp-A")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def S(self, q, **kw):
        return R.search(q, db_path=self.db, **kw)

    # --- clean cases that must pass --------------------------------------------------------
    def test_first_build_counts(self):
        self.assertTrue(self.res["rebuilt"])
        st = R.status(self.db, check_current=False)
        self.assertEqual(st["messages"], 3)
        self.assertEqual(st["files"], 2)

    def test_conversation_hit_has_session_surface_role_date_and_highlight(self):
        r = self.S("zorblaxian", scope="conversations")
        self.assertEqual(r["total"], 2)
        hit = [x for x in r["results"] if x["role"] == "assistant"][0]
        self.assertEqual((hit["surface"], hit["sid"], hit["date"], hit["copy"]),
                         ("CL", "sid-claude-1", "2026-10-02", "sid-claude-1"))
        s, e = hit["highlights"][0]
        self.assertEqual(hit["snippet"][s:e].lower(), "zorblaxian")      # highlight really covers the match
        self.assertIn("<b>tests</b>", hit["snippet"])                        # raw HTML stays literal text in the API

    def test_file_hit_reports_path_and_exact_line(self):
        r = self.S("quokkaquartz", scope="files")
        self.assertEqual(r["total"], 1)
        hit = r["results"][0]
        self.assertEqual(hit["type"], "file")
        self.assertEqual(hit["path"], self.notes)
        self.assertEqual(hit["line"], 7)                                    # the planted line number
        self.assertEqual(hit["copy"], f"{self.notes}:7")

    def test_one_query_finds_the_conversation_and_the_file(self):
        r = self.S("quokkaquartz")
        types = {x["type"] for x in r["results"]}
        self.assertEqual(types, {"conversation", "file"})

    def test_filters(self):
        self.assertEqual(self.S("zorblaxian", surface="AG")["total"], 0)
        self.assertEqual(self.S("zorblaxian", surface="CL")["total"], 2)
        self.assertEqual(self.S("zorblaxian", role="user")["total"], 1)
        self.assertEqual(self.S("incense", surface="AG")["total"], 1)
        self.assertEqual(self.S("baptism", fkind="SUBJECT")["total"], 0)
        self.assertEqual(self.S("baptism", fkind="INFRASTRUCTURE")["total"], 1)

    # --- falsification: plant a defect the feature must catch ------------------------------
    def test_absent_word_returns_zero(self):
        self.assertEqual(self.S("xylophonicallyunlikelytoken")["total"], 0)

    def test_hostile_queries_never_raise(self):
        hostile = ['"unbalanced', "AND OR NOT", "NEAR(a b)", "a:b ^c", "*", "-", "(", ")", '""', "'", "foo OR",
                   "col:zorblaxian", "zorblaxian*", "T1-T6", "\\", "\x02\x03", "%", "a AND (b OR", "\u202e\u0000x"]
        for q in hostile:
            for mode in ("all", "any", "phrase"):
                with self.subTest(q=q, mode=mode):
                    r = self.S(q, mode=mode)             # must not raise sqlite3.OperationalError
                    self.assertIn("results", r)
                    # the safety net inside search() must not be what saved us: the sanitiser
                    # itself has to produce a runnable expression
                    self.assertNotIn("could not be run", r.get("note") or "")

    def test_syntax_characters_around_a_real_word_still_find_it(self):
        """A planted defect for the sanitiser: with raw FTS5 syntax each of these is an error or a
        different query; sanitised, each must still find the planted word (2 conversation hits)."""
        for q in ['"zorblaxian', "(zorblaxian", "zorblaxian)", "zorblaxian^", "-zorblaxian", "zorblaxian'",
                  "{zorblaxian}", "zorblaxian:", "zorblaxian\x00", "  zorblaxian  "]:
            with self.subTest(q=q):
                self.assertEqual(self.S(q, scope="conversations")["total"], 2)

    def test_hostile_queries_over_http_never_500(self):
        with mock.patch.object(R, "DB_PATH", self.db):
            c = TestClient(app)
            for q in ['"unbalanced', "AND OR NOT", "NEAR(a b)", "a:b ^c", "*", "T1-T6", "(", "x" * 5000]:
                with self.subTest(q=q[:20]):
                    resp = c.get("/api/recall/search", params={"q": q})
                    self.assertEqual(resp.status_code, 200)

    def test_prefix_and_phrase(self):
        self.assertEqual(self.S("zorblax*", scope="conversations")["total"], 2)
        self.assertEqual(self.S("zorblaxian ledger", mode="phrase", scope="conversations")["total"], 2)
        self.assertEqual(self.S("ledger zorblaxian", mode="phrase", scope="conversations")["total"], 0)

    def test_missing_index_is_reported_not_crashed(self):
        with self.assertRaises(R.IndexMissing):
            R.search("anything", db_path=os.path.join(self.tmp, "nope.sqlite"))
        with mock.patch.object(R, "DB_PATH", os.path.join(self.tmp, "nope.sqlite")):
            resp = TestClient(app).get("/api/recall/search", params={"q": "x"})
            self.assertEqual(resp.status_code, 409)
            self.assertEqual(resp.json()["error"], "index_missing")


class FingerprintRebuildTests(unittest.TestCase):
    """The index is rebuilt only when a fingerprint changes, and a rebuild really replaces rows."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="recall_fp_")
        self.db = os.path.join(self.tmp, "fp.sqlite")
        self.f = os.path.join(self.tmp, "a.md")
        with open(self.f, "w", encoding="utf-8") as fh:
            fh.write("# A\n\nThe oldmarkerword paragraph sits in this file and is long enough to count as a chunk.\n")
        self.entry = lambda: [{"path": self.f, "rel_path": "a.md", "title": "A", "kind": "SUBJECT",
                               "size": os.path.getsize(self.f), "mtime": os.path.getmtime(self.f)}]
        self.m1 = [_msg("CL", "s1", "user", "alpha conversation oldmessageword")]
        R.refresh(db_path=self.db, messages=self.m1, files=self.entry(), conv_fp="fp1")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_unchanged_fingerprint_does_not_rebuild(self):
        called = []
        def boom():
            called.append(1)
            return []
        with mock.patch.object(R, "_load_messages", boom):
            res = R.refresh(db_path=self.db, files=self.entry(), conv_fp="fp1")
        self.assertFalse(res["rebuilt"])
        self.assertEqual(called, [])                       # messages were not even loaded

    def test_changed_conversation_fingerprint_replaces_rows(self):
        m2 = [_msg("CL", "s2", "user", "beta conversation newmessageword")]
        res = R.refresh(db_path=self.db, messages=m2, files=self.entry(), conv_fp="fp2")
        self.assertTrue(res["rebuilt"])
        self.assertTrue(res["conversations_reindexed"])
        self.assertEqual(res["files_reindexed"], 0)         # the file itself did not change
        self.assertEqual(R.search("newmessageword", db_path=self.db)["total"], 1)
        self.assertEqual(R.search("oldmessageword", db_path=self.db)["total"], 0)   # stale row is gone
        self.assertEqual(R.search("oldmarkerword", db_path=self.db)["total"], 1)    # file rows untouched

    def test_changed_file_is_reindexed_and_old_text_disappears(self):
        time.sleep(0.05)
        with open(self.f, "w", encoding="utf-8") as fh:
            fh.write("# A\n\nThe freshmarkerword paragraph replaced the old one and is long enough to count as a chunk.\n")
        os.utime(self.f, (time.time() + 5, time.time() + 5))
        res = R.refresh(db_path=self.db, messages=self.m1, files=self.entry(), conv_fp="fp1")
        self.assertTrue(res["rebuilt"])
        self.assertEqual(res["files_reindexed"], 1)
        self.assertFalse(res["conversations_reindexed"])
        self.assertEqual(R.search("freshmarkerword", db_path=self.db)["total"], 1)
        self.assertEqual(R.search("oldmarkerword", db_path=self.db)["total"], 0)

    def test_removed_file_leaves_the_index(self):
        res = R.refresh(db_path=self.db, messages=self.m1, files=[], conv_fp="fp1")
        self.assertEqual(res["files_removed"], 1)
        self.assertEqual(R.search("oldmarkerword", db_path=self.db)["total"], 0)

    def test_stale_flag_follows_fingerprint(self):
        with mock.patch.object(R, "conversation_fingerprint", return_value="fp1"), \
             mock.patch.object(R, "load_corpus_files", return_value=(self.entry(), 0, 0)):
            self.assertFalse(R.status(self.db)["stale"])
        with mock.patch.object(R, "conversation_fingerprint", return_value="fp-other"), \
             mock.patch.object(R, "load_corpus_files", return_value=(self.entry(), 0, 0)):
            st = R.status(self.db)
            self.assertTrue(st["stale"])
            self.assertTrue(st["conversations_stale"])


class ChunkingTests(unittest.TestCase):
    def test_line_numbers_are_the_real_line_numbers(self):
        text = "\n".join(["# Title", "", "x" * 100, "y" * 100, "", "", "z" * 100, "target " + "w" * 100])
        chunks = dict(R.chunk_text(text))
        # the one-line heading (line 1) is merged forward into the block that follows it (lines 3-4),
        # so that chunk starts at line 1; the next block (lines 7-8) starts at line 7
        self.assertEqual(sorted(chunks), [1, 7])
        self.assertTrue(chunks[1].startswith("# Title\nxxx"))
        self.assertTrue(chunks[7].startswith("z"))
        self.assertEqual(chunks[7].splitlines()[1][:6], "target")                  # line 8 of the text

    def test_long_line_is_split_but_nothing_is_lost(self):
        long_line = "abc " * 1000
        chunks = R.chunk_text(long_line)
        self.assertGreater(len(chunks), 1)
        self.assertEqual("".join(c[1] for c in chunks), long_line)

    def test_corpus_loader_skips_session_transcripts(self):
        tmp = tempfile.mkdtemp()
        try:
            good = os.path.join(tmp, "good.md")
            bad_dir = os.path.join(tmp, "_SESSION_TRANSCRIPTS")
            os.makedirs(bad_dir)
            bad = os.path.join(bad_dir, "raw.md")
            for p in (good, bad):
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write("text")
            idx = os.path.join(tmp, "ci.json")
            with open(idx, "w", encoding="utf-8") as fh:
                json.dump({"files": [{"path": good}, {"path": bad}, {"path": os.path.join(tmp, "missing.md")}]}, fh)
            keep, excl, missing = R.load_corpus_files(idx)
            self.assertEqual([k["path"] for k in keep], [good])
            self.assertEqual((excl, missing), (1, 1))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TopicTaggingTests(unittest.TestCase):
    """Question 2: topics match whole words only."""

    def test_dura_is_not_duration_or_endure(self):
        for text in ("the duration of the session", "we must endure", "procedural durability", "endurance and durable goods"):
            with self.subTest(text=text):
                self.assertNotIn("dura", ENG.match_topics(text))

    def test_dura_whole_word_still_matches(self):
        for text in ("The Dura-Europos baptistery", "dura europos", "see Dura.", "dura_europos.md", "DURA"):
            with self.subTest(text=text):
                self.assertIn("dura", ENG.match_topics(text))

    def test_other_substring_pollution_is_gone(self):
        self.assertNotIn("anki", ENG.match_topics("ranking mankind banking frankincense thanking"))
        self.assertIn("anki", ENG.match_topics("make an Anki deck"))
        self.assertNotIn("keys", ENG.match_topics("turkeys are birds"))
        self.assertNotIn("john 1:1", ENG.match_topics("John 1:14 and John 1:17"))
        self.assertIn("john 1:1", ENG.match_topics("compare John 1:1, 1:18"))

    def test_stems_and_plurals_still_work(self):
        self.assertIn("dikaio", ENG.match_topics("the verb dikaioo and noun dikaiosyne"))
        self.assertIn("icon", ENG.match_topics("veneration of icons"))
        self.assertIn("rev 21", ENG.match_topics("Rev\n21:21"))

    def test_regenerated_index_keeps_the_keys_app_py_reads(self):
        with open(os.path.join(APP_DIR, "data", "ai_session_index.json"), encoding="utf-8") as fh:
            d = json.load(fh)
        for k in ("sessions", "total_words", "top_topics", "total_sessions"):
            self.assertIn(k, d)
        need = {"id", "platform", "title", "mtime", "mtime_iso", "first_prompt", "turns_count",
                "approx_words", "artifacts", "topics"}
        for s in d["sessions"]:
            self.assertTrue(need <= set(s), s.get("id"))


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        if not os.path.exists(R.DB_PATH):
            raise unittest.SkipTest("data/recall_fts.sqlite not built")

    def test_module_is_mounted(self):
        r = self.client.get("/api/modules").json()
        self.assertEqual(r["routers"].get("recall_routes"), "loaded")
        self.assertIn("recall", [t["id"] for t in r["tabs"]])

    def test_status(self):
        s = self.client.get("/api/recall/status").json()
        self.assertTrue(s["exists"])
        self.assertGreater(s["messages"], 5000)
        self.assertGreater(s["files"], 500)
        for k in ("built_at", "fingerprint", "stale", "db_bytes"):
            self.assertIn(k, s)

    def test_all_sessions_from_log_reader_are_indexed(self):
        """Question 1: every Claude session log_reader returns is in ai_session_index.json."""
        from modules.log_reader import load_sessions
        with open(os.path.join(APP_DIR, "data", "ai_session_index.json"), encoding="utf-8") as fh:
            d = json.load(fh)
        indexed = {s["id"] for s in d["sessions"]}
        cl = {s["sid"] for s in load_sessions() if s["surface"] == "CL"}
        # the session writing this very test may be newer than the index; allow only those
        # whose last message is after the index was generated
        missing = cl - indexed
        gen = d["generated_at"].replace("+00:00", "Z")
        newer = {s["sid"] for s in load_sessions() if s["sid"] in missing and (s["last"] or "") >= gen[:19]}
        self.assertEqual(missing - newer, set(), "Claude sessions missing from the index")
        self.assertGreaterEqual(len(indexed & cl), 150)

    def test_three_required_queries_return_linkable_results(self):
        for q in ("Trinity chapter", "T1-T6", "twelve signs"):
            with self.subTest(q=q):
                resp = self.client.get("/api/recall/search", params={"q": q, "limit": 10})
                self.assertEqual(resp.status_code, 200)
                d = resp.json()
                self.assertGreater(d["total"], 0)
                for x in d["results"]:
                    self.assertTrue(x["copy"])
                    if x["type"] == "conversation":
                        self.assertRegex(x["sid"], r"^[0-9a-f-]{8,}$")
                        self.assertEqual(x["copy"], x["sid"])
                        self.assertIn(x["surface"], ("CL", "AG"))
                    else:
                        self.assertTrue(os.path.exists(x["path"]))
                        self.assertEqual(x["copy"], f"{x['path']}:{x['line']}")
                    for s, e in x["highlights"]:
                        self.assertTrue(0 <= s < e <= len(x["snippet"]))

    def test_t1_t6_hit_is_a_real_message(self):
        d = self.client.get("/api/recall/search", params={"q": "T1-T6", "scope": "conversations", "limit": 20}).json()
        self.assertTrue(any("t1" in x["snippet"].lower() for x in d["results"]))

    def test_query_is_fast(self):
        t0 = time.time()
        for q in ("Trinity chapter", "twelve signs", "dura", "baptism", "john 1:1"):
            self.client.get("/api/recall/search", params={"q": q, "limit": 25})
        per = (time.time() - t0) / 5
        self.assertLess(per, 1.0, f"{per:.3f}s per query")

    def test_rebuild_without_change_is_a_noop(self):
        # force a known-fresh state first (the live session log grows constantly), then the
        # second call must report nothing to do
        self.client.post("/api/recall/rebuild")
        again = self.client.post("/api/recall/rebuild").json()
        if again["rebuilt"]:
            self.skipTest("conversation logs changed between the two calls (a live session is writing)")
        self.assertFalse(again["rebuilt"])
        self.assertEqual(again["reason"], "fingerprints unchanged")

    def test_static_script_is_served_and_registers(self):
        r = self.client.get("/static/modules/recall.js")
        self.assertEqual(r.status_code, 200)
        self.assertIn('window.JarvisModules["recall"]', r.text)
        self.assertNotIn("innerHTML", r.text)          # engineering rule: DOM nodes / textContent only


if __name__ == "__main__":
    unittest.main()
