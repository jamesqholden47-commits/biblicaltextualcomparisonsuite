"""Methodology & Reproducibility statement (modules/methodology_routes.py), added 2026-11-12
under James's "more impressive to scientists/scholars/scholarships" goal.

Every number this feature reports is supposed to come from a live disk check, never a hand-typed
claim -- these tests falsify that in both directions: a real, present corpus must be reported
(not silently dropped), and a corpus that was never downloaded must report as absent (not as a
zero-but-present fabrication)."""
import os
import sys
import tempfile
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from modules import methodology_routes as M  # noqa: E402


class UnitTests(unittest.TestCase):
    def test_dir_stats_absent_directory_is_none_not_zero(self):
        """A directory that doesn't exist must report None (corpus absent), never {"files": 0,
        ...} (corpus present but empty) -- those mean different things to a reader of the
        methodology statement."""
        self.assertIsNone(M._dir_stats(r"C:\this\path\does\not\exist\__methodology_test__"))

    def test_dir_stats_counts_only_matching_extensions(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "a.pdf"), "w") as fh:
                fh.write("x" * 100)
            with open(os.path.join(d, "b.pdf"), "w") as fh:
                fh.write("x" * 50)
            with open(os.path.join(d, "readme.txt"), "w") as fh:
                fh.write("not a pdf")
            stats = M._dir_stats(d, exts=(".pdf",))
            self.assertEqual(stats["files"], 2)
            self.assertEqual(stats["bytes"], 150)

    def test_file_stats_absent_file_is_none(self):
        self.assertIsNone(M._file_stats(r"C:\this\file\does\not\exist.json"))

    def test_size_human_picks_gb_above_one_billion_bytes(self):
        self.assertEqual(M._size_human(500_000_000), "500.0 MB")
        self.assertEqual(M._size_human(1_500_000_000), "1.5 GB")
        self.assertEqual(M._size_human(None), "?")


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.client = TestClient(app)

    def test_module_is_mounted(self):
        r = self.client.get("/api/modules").json()
        self.assertEqual(r["routers"].get("methodology_routes"), "loaded")

    def test_methodology_json_reports_known_present_corpora(self):
        """Falsification check: these corpora were independently confirmed on disk this session
        (38 Schaff volumes, 221 Migne PL, 171 Migne PG) -- the endpoint must actually find them,
        not just return a well-shaped response with everything None."""
        m = self.client.get("/api/methodology").json()
        inv = m["corpus_inventory"]
        self.assertIsNotNone(inv["schaff_anf_npnf"])
        self.assertGreaterEqual(inv["schaff_anf_npnf"]["files"], 30)
        self.assertIsNotNone(inv["migne_patrologia_latina"])
        self.assertGreaterEqual(inv["migne_patrologia_latina"]["files"], 100)
        self.assertIsNotNone(inv["migne_patrologia_graeca"])
        self.assertGreaterEqual(inv["migne_patrologia_graeca"]["files"], 100)

    def test_export_is_markdown_and_cross_checks_against_json(self):
        resp = self.client.get("/api/methodology/export")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "text/markdown; charset=utf-8")
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])
        m = self.client.get("/api/methodology").json()
        schaff = m["corpus_inventory"]["schaff_anf_npnf"]
        self.assertIn(f"{schaff['files']} files", resp.text, "exported file count must match the live JSON, not a stale copy")
        rigor = m["citation_rigor"]
        if rigor and sum(rigor["totals"].values()):
            self.assertIn(f"{rigor['verified_rate']}%", resp.text)

    def test_methodology_json_matches_catalog_rigor_endpoint(self):
        """The methodology statement recomputes the rigor numbers independently (it can't import
        the live /rigor route's response) -- confirm the two never silently diverge."""
        m = self.client.get("/api/methodology").json()
        r_resp = self.client.get("/api/catalog/rigor")
        if r_resp.status_code != 200:
            self.assertIsNone(m["citation_rigor"])
            return
        r = r_resp.json()
        self.assertEqual(m["citation_rigor"]["totals"], r["totals"])
        self.assertEqual(m["citation_rigor"]["verified_rate"], r["verified_rate"])

    def test_methodology_json_matches_portfolio_word_count(self):
        m = self.client.get("/api/methodology").json()
        p_resp = self.client.get("/api/catalog/portfolio")
        if p_resp.status_code != 200:
            self.assertIsNone(m["research_output"])
            return
        p = p_resp.json()
        self.assertEqual(m["research_output"]["total_words"], p["total_words"])


if __name__ == "__main__":
    unittest.main()
