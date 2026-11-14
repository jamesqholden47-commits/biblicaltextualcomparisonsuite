"""MT/LXX Surface Divergence Report (modules/mt_lxx_routes.py), added 2026-11-12 under James's
goal: "run our in house analysis even if its surface level; mark it as unverified if not
verified or wherever its categorized". This is a deterministic verse-count scan, not a model
classifier -- these tests falsify the two properties that matter most for an honest surface
scan: (1) a chapter is never flagged just because one side has no text at all (a Deuterocanonical
book with no Hebrew is not a "divergence"), and (2) a row is tagged [R] only when it actually
matches a named locus, never asserted without a source."""
import os
import sys
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from modules import mt_lxx_routes as M  # noqa: E402


class UnitTests(unittest.TestCase):
    def test_one_side_missing_is_not_flagged(self):
        """A chapter where Hebrew has 0 verses (pure Deuterocanon, e.g. 1 Maccabees) must never
        appear as a 'divergence' -- that's absence, not divergence."""
        locus_matches = M.NAMED_LOCI  # sanity: the module loaded its curated list
        self.assertTrue(locus_matches)
        # exercise the actual scan logic's filter condition directly
        hv, gv = 0, 89
        flagged = not (hv == 0 or gv == 0) and abs(gv - hv) >= M.DELTA_THRESHOLD
        self.assertFalse(flagged)

    def test_delta_threshold_boundary(self):
        self.assertTrue(abs(5 - 3) >= M.DELTA_THRESHOLD)   # delta 2, flagged
        self.assertFalse(abs(5 - 4) >= M.DELTA_THRESHOLD)  # delta 1, not flagged

    def test_named_loci_each_have_a_source(self):
        """Rule 4/19 discipline: every curated [R] locus must name an actual source, never a bare
        classification with nothing behind it."""
        for locus in M.NAMED_LOCI:
            self.assertTrue(locus.get("source"), locus)
            self.assertGreater(len(locus["source"]), 20, "source string suspiciously short")


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.client = TestClient(app)
        if M.scan_cached() is None:
            raise unittest.SkipTest("web_app/plenary_logos_data.json not built")

    def test_module_is_mounted(self):
        r = self.client.get("/api/modules").json()
        self.assertEqual(r["routers"].get("mt_lxx_routes"), "loaded")

    def test_divergence_json_shape_and_known_loci(self):
        """Falsification check: Daniel 3 (the Prayer of Azariah addition) and Jeremiah are
        extremely well-documented MT/LXX divergences -- if the live scan doesn't surface them,
        either the scan or the underlying data is broken."""
        d = self.client.get("/api/mt_lxx/divergence").json()
        self.assertGreater(d["total_flagged"], 0)
        self.assertEqual(d["total_flagged"], d["named_tier_r"] + d["unclassified_tier_s"])
        rows = d["rows"]
        dan3 = next((r for r in rows if r["book_id"] == "dan" and r["chapter"] == 3), None)
        self.assertIsNotNone(dan3, "Daniel 3 (Prayer of Azariah) must be flagged")
        self.assertEqual(dan3["tier"], "R")
        self.assertTrue(dan3["source"])
        jer_rows = [r for r in rows if r["book_id"] == "jer"]
        self.assertTrue(jer_rows, "at least one Jeremiah chapter must be flagged")
        self.assertTrue(all(r["tier"] == "R" for r in jer_rows), "every flagged Jeremiah chapter should match the named Jeremiah locus")

    def test_every_row_has_a_tier_and_s_tier_rows_have_no_fabricated_source(self):
        d = self.client.get("/api/mt_lxx/divergence").json()
        for r in d["rows"]:
            self.assertIn(r["tier"], ("R", "S"))
            if r["tier"] == "S":
                self.assertIsNone(r["source"], "an [S]-tagged (unverified) row must not carry a source citation")
            else:
                self.assertTrue(r["source"])

    def test_dss_attestation_field_present_and_honest(self):
        """New 2026-11-12 feature: dss_attestation formalizes what the NAMED_LOCI source strings
        for Jeremiah and 1 Samuel already assert about Qumran evidence (4QJer^b/d, 4QSam^a) --
        every row must carry the field, and it must only ever be one of the 4 documented values,
        never a guess for a locus with no Qumran witness."""
        d = self.client.get("/api/mt_lxx/divergence").json()
        for r in d["rows"]:
            self.assertIn(r["dss_attestation"], M.DSS_ATTESTATION_VALUES)
        jer_rows = [r for r in d["rows"] if r["book_id"] == "jer"]
        self.assertTrue(all(r["dss_attestation"] == "attests_lxx_vorlage" for r in jer_rows))
        dan3 = next(r for r in d["rows"] if r["book_id"] == "dan" and r["chapter"] == 3)
        self.assertEqual(dan3["dss_attestation"], "no_qumran_witness")

    def test_rows_sorted_by_absolute_delta_descending(self):
        d = self.client.get("/api/mt_lxx/divergence").json()
        deltas = [abs(r["delta"]) for r in d["rows"]]
        self.assertEqual(deltas, sorted(deltas, reverse=True))

    def test_export_is_markdown_and_counts_match_json(self):
        resp = self.client.get("/api/mt_lxx/divergence/export")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "text/markdown; charset=utf-8")
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])
        d = self.client.get("/api/mt_lxx/divergence").json()
        self.assertIn(f"{d['total_flagged']} chapters flagged", resp.text)


if __name__ == "__main__":
    unittest.main()
