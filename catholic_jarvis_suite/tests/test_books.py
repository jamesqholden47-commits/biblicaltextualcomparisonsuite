"""Tests for the Bookbinder (modules/books_core.py). Everything runs in a temporary sandbox: a fake Loose
Ends register, a fake vault concordance, and a temporary 10_VOLUMES. The real plan and overrides are
never touched. The brief gate and data_check.py are the REAL tools, so these tests can fail for real."""
import json
import os
import shutil
import sys
import tempfile
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from modules import books_core as core  # noqa: E402
from modules import loose_core  # noqa: E402

TRINITY = ("John 17:5 has the Son praying 'glorify thou me with the glory which I had with thee before the world was', "
           "and John 8:17-18 counts the Father and the Son as two witnesses under Deuteronomy 19:15. Tertullian, Against "
           "Praxeas 2, written about AD 213, already answers the modalist reading. [V: Tertullian, Adv. Prax. 2] ")
ONENESS = ("Oneness Pentecostals teach that Jesus is the Father incarnate; the IAFCJ was founded in 1914 at Villa Aldama, "
           "Chihuahua, and counts 284,000 members across 2,283 churches. [R: IAFCJ yearbook 2019] ")


def write(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)


class BooksTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="books_")
        self.saved = {k: getattr(core, k) for k in ("DATA_DIR", "VOLUMES_DIR", "TAXONOMY_FILE", "PLAN_FILE", "OVERRIDES_FILE",
                                                     "CLASSIFY_CACHE", "VAULT_CONCORDANCE", "LOOSE_REGISTRY")}
        self.loose_saved = (loose_core.STATUS_FILE,)
        d = os.path.join(self.tmp, "data")
        os.makedirs(d)
        core.DATA_DIR = d
        core.VOLUMES_DIR = os.path.join(self.tmp, "10_VOLUMES")
        for k, f in (("TAXONOMY_FILE", "books_taxonomy.json"), ("PLAN_FILE", "books_plan.json"), ("OVERRIDES_FILE", "books_overrides.json"),
                     ("CLASSIFY_CACHE", "books_classify_cache.json"), ("VAULT_CONCORDANCE", "vault_concordance.json"),
                     ("LOOSE_REGISTRY", "loose_registry.json")):
            setattr(core, k, os.path.join(d, f))
        loose_core.STATUS_FILE = os.path.join(d, "loose_status.json")
        src = os.path.join(self.tmp, "src")
        self.a1 = os.path.join(src, "Trinity_Oneness_Witnesses.md")
        self.a2 = os.path.join(src, "Trinity_Oneness_Rebuttal_Notes.md")
        self.a3 = os.path.join(src, "Inquisition_Count.md")
        write(self.a1, "# Trinity against Oneness: the witnesses\n\n" + TRINITY * 3)
        write(self.a2, "# Trinity and Oneness rebuttal notes\n\n" + ONENESS * 3)
        write(self.a3, "# Inquisition count\n\nGarcia-Molina counts 43 relaxed in person; Alberro 34 to 37.\n")
        self.v1 = os.path.join(self.tmp, "vault", "15_Fundamental_Theology", "Trinity_Oneness_Vault_Note.md")
        self.v_old = os.path.join(self.tmp, "vault", "old", "Trinity_Oneness_Vault_Note.md")
        write(self.v1, "---\ntags: x\n---\n# Trinity Oneness vault note\n\n" + TRINITY)
        write(self.v_old, "# old copy\n\nOld text about the Trinity and Oneness and modalism.\n")
        # a copy whose every line is inside v1 (2026-10-08 rule: only such a copy may be dropped)
        self.v_dup = os.path.join(self.tmp, "vault", "dup", "Trinity_Oneness_Vault_Note.md")
        write(self.v_dup, "# Trinity Oneness vault note\n\n" + TRINITY.split("\n")[0] + "\n")
        reg = {"docs": [
            {"id": core.source_id(p), "path": p, "title": t, "kind": "SUBJECT", "ext": ".md", "area": "Project", "subarea": "",
             "words": 200, "mtime": "2026-10-0%dT10:00" % i, "integrated_into": [], "open_items": []}
            for i, (p, t) in enumerate([(self.a1, "Trinity against Oneness: the witnesses"),
                                        (self.a2, "Trinity and Oneness rebuttal notes"),
                                        (self.a3, "Inquisition count")], 1)]}
        json.dump(reg, open(core.LOOSE_REGISTRY, "w", encoding="utf-8"))
        conc = {"unique_documents": [
            {"vault_id": "aa1_live", "vault_name": "AA1 Live Vault", "path": self.v1, "rel_path": "15_Fundamental_Theology/Trinity_Oneness_Vault_Note.md",
             "title": "Trinity Oneness vault note", "words": 400, "mtime": 2000, "mtime_iso": "2026-09-01T10:00"},
            {"vault_id": "aa1_live", "vault_name": "AA1 Live Vault", "path": self.v_old, "rel_path": "old/Trinity_Oneness_Vault_Note.md",
             "title": "old copy", "words": 400, "mtime": 1000, "mtime_iso": "2026-01-01T10:00"},
            {"vault_id": "aa1_live", "vault_name": "AA1 Live Vault", "path": self.v_dup, "rel_path": "dup/Trinity_Oneness_Vault_Note.md",
             "title": "contained copy", "words": 400, "mtime": 3000, "mtime_iso": "2026-10-01T10:00"},
            {"vault_id": "aa1_live", "vault_name": "AA1 Live Vault", "path": os.path.join(self.tmp, "vault", "stub.md"), "rel_path": "stub.md",
             "title": "stub", "words": 5, "mtime": 1, "mtime_iso": "2026-01-01T10:00"},
            {"vault_id": "aa1_live", "vault_name": "AA1 Live Vault", "path": os.path.join(self.tmp, "vault", "98_Archives", "x.md"),
             "rel_path": "98_Archives/x.md", "title": "Trinity archive", "words": 900, "mtime": 1, "mtime_iso": "2026-01-01T10:00"}],
            "version_drift_files": [{"filename": "Trinity_Oneness_Vault_Note.md", "variants": [
                {"vault_id": "aa1_live", "path": self.v1, "rel_path": "15_Fundamental_Theology/Trinity_Oneness_Vault_Note.md", "mtime": 2000},
                {"vault_id": "aa1_live", "path": self.v_old, "rel_path": "old/Trinity_Oneness_Vault_Note.md", "mtime": 1000},
                {"vault_id": "aa1_live", "path": self.v_dup, "rel_path": "dup/Trinity_Oneness_Vault_Note.md", "mtime": 3000}]}]}
        json.dump(conc, open(core.VAULT_CONCORDANCE, "w", encoding="utf-8"))

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(core, k, v)
        (loose_core.STATUS_FILE,) = self.loose_saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def plan(self):
        return core.build_plan()

    def chapter_with(self, plan, path):
        sid = core.source_id(path)
        for v in plan["volumes"]:
            for c in v["chapters"]:
                if sid in c["sources"]:
                    return v, c
        return None, None

    def test_pool_rules(self):
        p = self.plan()
        sk = p["pool"]["vault_skipped"]
        self.assertEqual(p["pool"]["ai"], 3)
        # 2026-10-08 rule: the differing "old copy" stays even though it is older; the copy whose every line is in
        # v1 is dropped even though it is the NEWEST by date (dates are ignored)
        self.assertEqual(p["pool"]["vault"], 2, "both differing copies kept; the fully contained copy dropped; no stub, no archive")
        self.assertEqual(sk.get("copy whose every line is in another copy"), 1)
        kept = {s["path"] for s in p["sources"].values()}
        self.assertIn(self.v_old, kept)
        self.assertNotIn(self.v_dup, kept)
        self.assertEqual(sk.get("excluded folder"), 1)

    def test_FALSIFY_existing_books_and_oversized_files_stay_out_of_the_pool(self):
        reg = json.load(open(core.LOOSE_REGISTRY, encoding="utf-8"))
        master = os.path.join(self.tmp, "proj", "01_MASTER_DISSERTATION", "Master_Readers_Edition.md")
        huge = os.path.join(self.tmp, "src", "Giant_Trinity_Compilation.md")
        write(master, "# Master\n\n" + TRINITY)
        write(huge, "# Giant Trinity compilation\n\n" + TRINITY)
        for p, w in ((master, 300), (huge, core.MAX_SOURCE_WORDS + 1)):
            reg["docs"].append({"id": core.source_id(p), "path": p, "title": os.path.basename(p), "kind": "SUBJECT", "ext": ".md",
                                "area": "Project", "subarea": "", "words": w, "mtime": "2026-10-05T10:00", "integrated_into": [], "open_items": []})
        json.dump(reg, open(core.LOOSE_REGISTRY, "w", encoding="utf-8"))
        p = self.plan()
        planned = {sid for v in p["volumes"] for c in v["chapters"] for sid in c["sources"]} | set(p["unsorted"])
        self.assertNotIn(core.source_id(master), planned, "a master-dissertation file must never be re-synthesised")
        self.assertEqual(p["pool"]["ai_skipped"].get("part of an existing book"), 1)
        self.assertNotIn(core.source_id(huge), planned)
        self.assertEqual([o["path"] for o in p["oversized"]], [huge])

    def test_split_is_lossless_and_parts_replace_the_original(self):
        saved = (core.SPLIT_TARGET, core.SPLIT_HARD)
        core.SPLIT_TARGET, core.SPLIT_HARD = 60, 120
        try:
            huge = os.path.join(self.tmp, "src", "Huge_Trinity_Oneness_Notes.md")
            body = "".join(f"## Section {i} on the Trinity and Oneness\n\n" + TRINITY + "\n\n" + ("plain line about modalism " * 20) + "\n\n" for i in range(8))
            write(huge, body)
            r = core.split_source(huge, "Huge Trinity Oneness notes", "vault")
            self.assertGreater(r["parts"], 2)
            self.assertTrue(core.verify_split(r["folder"]), "parts must rejoin to the original byte for byte")
            # FALSIFY: tamper with one part and the verification must fail
            p1 = os.path.join(r["folder"], "part_001.md")
            with open(p1, "a", encoding="utf-8") as f:
                f.write("x")
            self.assertFalse(core.verify_split(r["folder"]))
            plan = self.plan()
            paths = {s["path"] for s in plan["sources"].values()}
            self.assertNotIn(huge, paths)
            self.assertTrue(any(os.path.basename(pth).startswith("part_") for pth in paths))
        finally:
            core.SPLIT_TARGET, core.SPLIT_HARD = saved

    def test_classification_and_clustering(self):
        p = self.plan()
        v, c = self.chapter_with(p, self.a1)
        self.assertEqual(v["id"], "V04")
        self.assertIn(core.source_id(self.a2), c["sources"], "the two Trinity/Oneness docs share a chapter")
        v3, c3 = self.chapter_with(p, self.a3)
        self.assertEqual(v3["id"], "V08")

    def test_approve_freezes_against_replan_and_moves(self):
        p = self.plan()
        v, c = self.chapter_with(p, self.a1)
        core.approve(c["id"])
        frozen = list(c["sources"])
        core.move_source(core.source_id(self.a3), "V04", c["id"] + "-other")
        with self.assertRaises(ValueError):
            core.move_source(core.source_id(self.a1), "V01")
        p2 = self.plan()
        v2, c2 = self.chapter_with(p2, self.a1)
        self.assertEqual(c2["id"], c["id"])
        self.assertEqual(c2["sources"], frozen, "re-planning never changes an approved chapter")
        self.assertEqual(c2["state"], "approved")
        v3, _ = self.chapter_with(p2, self.a3)
        self.assertEqual(v3["id"], "V04", "James's move is applied on re-plan")

    def test_brief_passes_the_real_gate(self):
        p = self.plan()
        v, c = self.chapter_with(p, self.a1)
        with self.assertRaises(ValueError):
            core.write_brief(c["id"])                 # not approved yet
        core.approve(c["id"])
        r = core.write_brief(c["id"])
        self.assertEqual(r["gate_exit"], 0, r["gate"])
        self.assertIn("PASS", r["gate"])
        txt = open(r["brief"], encoding="utf-8").read()
        self.assertIn(self.a1, txt)
        self.assertIn(self.a2, txt)
        with self.assertRaises(FileExistsError):
            core.write_brief(c["id"])
        self.assertEqual(core.find_chapter(core.load_plan(), c["id"])[1]["state"], "briefed")

    def test_states_checks_and_FALSIFY_lossy_draft(self):
        p = self.plan()
        v, c = self.chapter_with(p, self.a1)
        core.approve(c["id"])
        core.write_brief(c["id"])
        out = os.path.join(core.chapter_dir(c), "CHAPTER.md")
        write(out, "# The two witnesses\n\n" + TRINITY + "\n")   # no marker yet, and the Oneness source is dropped
        self.assertEqual(core.find_chapter(core.load_plan(), c["id"])[1]["state"], "drafting")
        write(out, "# The two witnesses\n\n" + TRINITY + f"\n<!-- WORKER COMPLETE: {c['id']} -->\n")
        self.assertEqual(core.find_chapter(core.load_plan(), c["id"])[1]["state"], "drafted")
        res = core.run_checks(c["id"])
        a2 = res["per_source"][core.source_id(self.a2)]
        self.assertGreater(a2["missing"], 0, "the dropped source's numbers (1914, 284,000, 2,283) must be reported missing")
        self.assertEqual(res["per_source"][core.source_id(self.a1)]["missing"], 0)
        self.assertEqual(core.find_chapter(core.load_plan(), c["id"])[1]["state"], "checked")
        with self.assertRaises(ValueError):
            core.unapprove(c["id"])

    def test_final_marks_loose_sources_and_assembly(self):
        p = self.plan()
        v, c = self.chapter_with(p, self.a1)
        core.approve(c["id"])
        out = os.path.join(core.chapter_dir(c), "CHAPTER.md")
        write(out, "# The two witnesses\n\n" + TRINITY + ONENESS + f"\n<!-- WORKER COMPLETE: {c['id']} -->\n")
        core.run_checks(c["id"])
        core.set_final(c["id"], True)
        marks = loose_core.load_status()["marks"]
        self.assertEqual(marks[core.source_id(self.a1)]["status"], "merged")
        self.assertEqual(marks[core.source_id(self.a1)]["merged_into"], out)
        self.assertNotIn(core.source_id(self.v1), marks, "vault notes are not Loose Ends documents")
        r = core.assemble_volume("V04")
        vol = open(r["volume"], encoding="utf-8").read()
        self.assertIn("## Contents", vol)
        self.assertIn("Tertullian", vol)
        self.assertNotIn("WORKER COMPLETE", vol)
        self.assertEqual(r["chapters_included"], 1)

    def test_routes(self):
        from fastapi.testclient import TestClient
        from app import app
        cl = TestClient(app)
        self.assertEqual(cl.get("/api/modules").json()["routers"].get("books_routes"), "loaded")
        self.plan()
        s = cl.get("/api/books/summary").json()
        self.assertEqual(s["pool"]["ai"], 3)
        nx = cl.get("/api/books/next?n=3").json()
        self.assertTrue(nx["items"])
        self.assertEqual(cl.post("/api/books/chapter/V99-nope/approve").status_code, 404)
        self.assertEqual(cl.post("/api/books/rename", json={"kind": "shelf", "id": "x", "title": "y"}).status_code, 400)

    def test_js_safe(self):
        js = open(os.path.join(APP_DIR, "static", "modules", "books.js"), encoding="utf-8").read()
        self.assertNotIn("innerHTML", js)
        self.assertIn('window.JarvisModules["books"]', js)


if __name__ == "__main__":
    unittest.main()
