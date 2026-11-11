"""Tests for the Loose Ends module (modules/loose_core.py, modules/loose_routes.py).
Everything runs on a temporary folder; the real register and James's marks are never touched."""
import json
import os
import shutil
import sys
import tempfile
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from modules import loose_core as core  # noqa: E402

PARA_A1 = ("Irenaeus of Lyons, writing around the year one hundred and eighty, appeals to the succession of bishops "
           "in the church of Rome as the public, checkable line through which the apostolic teaching was handed down, "
           "and he lists the bishops by name from Linus to Eleutherius so that any reader can verify the chain.")
PARA_A2 = ("Optatus of Milevis, answering the Donatist Parmenian, names the single chair of Peter as the one chair in "
           "which unity is kept by all, and he argues that whoever sets up another chair against it is a schismatic "
           "and a sinner, which makes the cathedra Petri the test of communion for the African churches.")
PARA_A3 = ("Cyprian of Carthage speaks of the chair of Peter and the principal church from which priestly unity takes its "
           "rise, and although he later quarrelled with Stephen of Rome over baptism, his early letters treat communion "
           "with Rome as communion with the Catholic Church itself, a point both his defenders and critics concede.")
PARA_B = ("The census series for Mexico between eighteen ninety five and nineteen seventy shows a flat Protestant share "
          "under about two percent, and the jump after nineteen seventy is concentrated in the south east and the border, "
          "which is the pattern a pastoral vacuum explanation predicts and a foreign plot explanation does not predict.")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class LooseCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="loose_")
        self.root = os.path.join(self.tmp, "root")
        self.book = os.path.join(self.tmp, "BOOK.md")
        self._orig = (core.REGISTRY_FILE, core.STATUS_FILE, core.DATA_DIR, core._corpus_kinds, core._not_dissertation,
                      core._ledger_questions)
        core.DATA_DIR = self.tmp
        core.REGISTRY_FILE = os.path.join(self.tmp, "reg.json")
        core.STATUS_FILE = os.path.join(self.tmp, "status.json")
        core._corpus_kinds = lambda: {}
        core._not_dissertation = lambda: set()
        core._ledger_questions = lambda: [{"id": "q1", "text": "what did the census show about protestant growth in mexico?",
                                           "ts": "2026-10-01", "surface": "AG", "missed": True}]
        self.A = os.path.join(self.root, "03_RESEARCH_DOSSIERS", "Roman_Primacy_Fathers.md")
        self.B = os.path.join(self.root, "03_RESEARCH_DOSSIERS", "Mexico_Census_Protestant_Growth.md")
        self.C = os.path.join(self.root, "05_DRAFTS", "copy", "Mexico_Census_Protestant_Growth.md")
        self.E = os.path.join(self.root, "05_DRAFTS", "Mexico_Census_Protestant_Growth_Readers_Edition.md")
        self.D = os.path.join(self.root, "02_CONTROL_AND_STATE", "Battleplan_Overnight.md")
        write(self.A, f"# Roman primacy in the Fathers\n\n{PARA_A1}\n\n{PARA_A2}\n\n{PARA_A3}\n")
        b_text = (f"# Mexico census and Protestant growth\n\n{PARA_B}\n\n## Before using this in public: what still needs checking\n"
                  "- The 0.66 correlation: can it be reproduced from named sources?\n- Tabasco priest count in 1950.\n\n"
                  "## FETCH LIST\n- none\n\n## Notes\n- not an open item\n")
        write(self.B, b_text)
        write(self.C, b_text)
        write(self.E, f"# Mexico census and Protestant growth (Reader's Edition)\n\n{PARA_B} Rewritten.\n")
        write(self.D, "# Battleplan overnight\n\n## Next steps\n1. Run the workers.\n")
        write(self.book, f"# The Book\n\n{PARA_A1}\n\n{PARA_A2}\n\n{PARA_A3}\n")
        self.cfg = {"roots": [[self.root, "Test"]], "targets": [self.book], "skip": ["\\copyskip\\"], "exts": [".md"]}
        self.msgs = [{"text": "please re-read Mexico_Census_Protestant_Growth.md tomorrow", "ts": "2026-10-02T10:00:00Z"}]

    def tearDown(self):
        (core.REGISTRY_FILE, core.STATUS_FILE, core.DATA_DIR, core._corpus_kinds, core._not_dissertation,
         core._ledger_questions) = self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self):
        reg = core.rebuild(cfg=self.cfg, producers={}, messages=self.msgs)
        return reg, {d["path"]: d for d in reg["docs"]}

    def test_integration_found_and_not_found(self):
        reg, by = self.build()
        self.assertTrue(by[self.A]["integrated_into"], "A's paragraphs are in the book")
        self.assertEqual(by[self.A]["integrated_into"][0]["target"], self.book)
        self.assertFalse(by[self.B]["integrated_into"], "B's paragraph is not in the book")

    def test_FALSIFY_removing_passages_from_the_book_flips_integration(self):
        write(self.book, "# The Book\n\nNothing from the dossier survives here.\n")
        reg, by = self.build()
        self.assertFalse(by[self.A]["integrated_into"])

    def test_open_items_extracted_none_ignored_other_sections_ignored(self):
        reg, by = self.build()
        items = [i["text"] for i in by[self.B]["open_items"]]
        self.assertEqual(len(items), 2, items)
        self.assertTrue(any("0.66" in t for t in items))
        self.assertFalse(any("not an open item" in t for t in items))
        self.assertFalse(any(t.lower() == "none" for t in items))
        self.assertEqual([i["text"] for i in by[self.D]["open_items"]], ["Run the workers."])

    def test_open_items_inside_code_blocks_ignored(self):
        self.assertEqual(core.extract_open_items("```\n## TODO\n- fake\n```\n"), [])

    def test_exact_copies_and_title_variants(self):
        reg, by = self.build()
        ids = {p: d["id"] for p, d in by.items()}
        self.assertIn(ids[self.C], by[self.B]["exact_copies"])
        self.assertIn(ids[self.E], by[self.B]["title_variants"])
        self.assertEqual(by[self.A]["exact_copies"], [])

    def test_kind_from_path(self):
        reg, by = self.build()
        self.assertEqual(by[self.D]["kind"], "INFRASTRUCTURE")
        self.assertEqual(by[self.B]["kind"], "SUBJECT")

    def test_chat_mentions_and_never_mentioned(self):
        reg, by = self.build()
        self.assertEqual(by[self.B]["chat_mentions"]["count"], 1)
        self.assertEqual(by[self.A]["chat_mentions"]["count"], 0)

    def test_priority_ranks_loose_subject_above_integrated_and_infra(self):
        reg, by = self.build()
        self.assertGreater(by[self.B]["score"], by[self.A]["score"])
        self.assertGreater(by[self.A]["score"], by[self.D]["score"])

    def test_marks_survive_rebuild_and_validate(self):
        reg, by = self.build()
        did = by[self.B]["id"]
        core.set_mark(did, "merged", merged_into="BOOK.md ch 4")
        with open(core.STATUS_FILE, "rb") as fh:
            before = fh.read()
        self.build()
        with open(core.STATUS_FILE, "rb") as fh:
            after = fh.read()
        self.assertEqual(after, before, "rebuild must not touch the status file")
        self.assertEqual(core.load_status()["marks"][did]["merged_into"], "BOOK.md ch 4")
        with self.assertRaises(ValueError):
            core.set_mark(did, "deleted")
        with self.assertRaises(ValueError):
            core.set_mark("../../etc", "open")
        core.set_mark(did, "unreviewed")
        self.assertNotIn(did, core.load_status()["marks"])

    def test_threads_group_same_topic_and_attach_questions(self):
        reg, by = self.build()
        tB = by[self.B]["thread"]
        self.assertIsNotNone(tB)
        self.assertEqual(by[self.E]["thread"], tB)
        self.assertNotEqual(by[self.A]["thread"], tB)
        t = [x for x in reg["threads"] if x["id"] == tB][0]
        self.assertIn("q1", t["question_ids"])

    def test_FALSIFY_threads_do_not_chain_unrelated_topics(self):
        docs = []
        for i, title in enumerate(["alpha beta gamma", "beta gamma delta", "gamma delta epsilon", "delta epsilon zeta",
                                   "epsilon zeta theta", "zeta theta iota"]):
            docs.append({"id": f"d{i}", "kind": "SUBJECT", "mtime": f"2026-10-0{i + 1}", "_tokens": set(title.split()),
                         "title": title})
        threads = core.build_threads(docs, [], max_df_frac=1.0)
        self.assertTrue(all(len(t["doc_ids"]) <= 3 for t in threads), [t["doc_ids"] for t in threads])

    def test_query_filters(self):
        reg, by = self.build()
        r = core.query(reg, {}, signal="not_integrated", kind="SUBJECT")
        paths = {d["path"] for d in r["items"]}
        self.assertIn(self.B, paths)
        self.assertNotIn(self.A, paths)
        r = core.query(reg, {}, text="0.66 correlation")
        self.assertEqual({d["path"] for d in r["items"]}, {self.B, self.C})
        self.assertIn("Mexico census", core.export_md(reg, {}))


class LooseRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from app import app
        cls.client = TestClient(app)
        cls.tmp = tempfile.mkdtemp(prefix="looseapi_")
        cls._orig = (core.REGISTRY_FILE, core.STATUS_FILE)
        core.REGISTRY_FILE = os.path.join(cls.tmp, "reg.json")
        core.STATUS_FILE = os.path.join(cls.tmp, "status.json")
        reg = {"built_at": "x", "seconds": 0, "n_docs": 1, "targets_found": [], "threads": [], "questions": {},
               "docs": [{"id": "0123456789abcdef", "path": "C:\\x\\a.md", "title": "A", "area": "Test", "subarea": "", "ext": ".md",
                         "bytes": 2000, "mtime": "2026-10-05T10:00", "kind": "SUBJECT", "open_items": [{"section": "todo", "text": "check it"}],
                         "tags": {}, "words": 10, "partial": False, "producer": None, "integrated_into": [], "referenced_by": [],
                         "chat_mentions": {"count": 0, "last": None}, "exact_copies": [], "title_variants": [], "thread": None, "score": 5}]}
        with open(core.REGISTRY_FILE, "w", encoding="utf-8") as fh:
            json.dump(reg, fh)

    @classmethod
    def tearDownClass(cls):
        core.REGISTRY_FILE, core.STATUS_FILE = cls._orig
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_module_loaded(self):
        self.assertEqual(self.client.get("/api/modules").json()["routers"].get("loose_routes"), "loaded")

    def test_summary_items_owed_mark_export(self):
        s = self.client.get("/api/loose/summary").json()
        self.assertEqual(s["subject_not_integrated"], 1)
        r = self.client.get("/api/loose/items?signal=not_integrated").json()
        self.assertEqual(r["total"], 1)
        o = self.client.get("/api/loose/open_items").json()
        self.assertEqual(o["items"][0]["text"], "check it")
        self.assertEqual(self.client.post("/api/loose/mark", json={"id": "0123456789abcdef", "status": "parked", "note": "later"}).status_code, 200)
        self.assertEqual(self.client.get("/api/loose/items?mark=parked").json()["total"], 1)
        self.assertEqual(self.client.post("/api/loose/mark", json={"id": "0123456789abcdef", "status": "burn"}).status_code, 400)
        self.assertIn("A", self.client.get("/api/loose/export.md").text)

    def test_js_never_inserts_raw_html(self):
        with open(os.path.join(APP_DIR, "static", "modules", "loose.js"), encoding="utf-8") as fh:
            js = fh.read()
        self.assertNotIn("innerHTML", js)
        self.assertIn('window.JarvisModules["loose"]', js)


if __name__ == "__main__":
    unittest.main()
