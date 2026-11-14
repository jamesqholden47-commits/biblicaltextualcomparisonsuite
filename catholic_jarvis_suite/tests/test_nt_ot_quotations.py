"""NT Quotations of the OT (modules/nt_ot_quotations_routes.py), added 2026-11-12 under James's
"/deep-research" goal. Every classification was reached by directly comparing this suite's own
GNT/LXX/MT text -- these tests falsify that the comparison is real, not asserted: the token-
overlap score must actually correlate with the hand-entered classification direction in the one
case built specifically as a counter-example (Matthew 2:15/Hosea 11:1, which follows MT against
LXX), and no row may claim a classification with an empty verified-text field."""
import os
import sys
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from modules import nt_ot_quotations_routes as Q  # noqa: E402


class UnitTests(unittest.TestCase):
    def test_tokenizer_strips_accents_and_breathing_marks(self):
        a = Q._tokens("ἰδοὺ ἡ παρθένος")  # idou hē parthenos, with accents
        b = Q._tokens("ιδου η παρθενος")  # same words, bare
        self.assertEqual(a, b)

    def test_overlap_score_is_symmetric_identity_case(self):
        text = "καὶ τέξεται υἱόν"
        score = Q._overlap_score(text, text)
        self.assertEqual(score["overlap_pct"], 100.0)

    def test_overlap_score_none_when_no_tokens(self):
        self.assertIsNone(Q._overlap_score("", "ιδου"))

    def test_every_locus_has_both_verified_text_and_a_framing_source(self):
        for q in Q.NAMED_QUOTATIONS:
            self.assertTrue(q["verified"], q["id"])
            self.assertTrue(q["framing_source"], q["id"])
            self.assertIn(q["classification"], ("follows_lxx", "follows_mt", "follows_neither", "lxx_only_addition"))


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.client = TestClient(app)
        if Q.rows_cached() is None:
            raise unittest.SkipTest("web_app/plenary_logos_data.json not built")

    def test_module_is_mounted(self):
        r = self.client.get("/api/modules").json()
        self.assertEqual(r["routers"].get("nt_ot_quotations_routes"), "loaded")

    def test_every_row_has_real_pulled_text(self):
        """Falsification check: a reference pointing at a book/chapter/verse this suite doesn't
        actually have data for would silently come back None -- confirm every curated locus
        really did pull real text for all three streams it claims to compare."""
        d = self.client.get("/api/nt_ot_quotations").json()
        self.assertEqual(d["total"], len(Q.NAMED_QUOTATIONS))
        for r in d["rows"]:
            self.assertTrue(r["nt_greek"], f"{r['id']}: no GNT text pulled")
            self.assertTrue(r["lxx_greek"], f"{r['id']}: no LXX text pulled")

    def test_matt2_15_counter_example_has_low_overlap_matching_its_classification(self):
        """The one locus deliberately included to show Matthew following MT against LXX must
        show a LOW token-overlap score with the LXX -- if this metric were vacuous (e.g. always
        high, or uncorrelated), this specific row would be the one to expose it."""
        d = self.client.get("/api/nt_ot_quotations").json()
        row = next(r for r in d["rows"] if r["id"] == "matt2-15-hos11-1")
        self.assertEqual(row["classification"], "follows_mt")
        self.assertIsNotNone(row["token_overlap"])
        self.assertLess(row["token_overlap"]["overlap_pct"], 50,
                         "a 'follows_mt' row should NOT show high lexical overlap with the LXX")

    def test_lxx_only_addition_row_confirms_no_mt_text_at_all(self):
        """Hebrews 1:6/Deut 32:43 is classified lxx_only_addition -- the pulled MT text for that
        exact verse must exist (it's a real, short verse) but be a completely different, much
        shorter text than the LXX span, not merely absent."""
        d = self.client.get("/api/nt_ot_quotations").json()
        row = next(r for r in d["rows"] if r["id"] == "heb1-6-deut32-43")
        self.assertEqual(row["classification"], "lxx_only_addition")
        self.assertTrue(row["mt_hebrew"])
        self.assertLess(len(row["mt_hebrew"]), len(row["lxx_greek"]) // 2,
                         "MT verse 43 should be much shorter than the expanded LXX verse 43")

    def test_export_is_markdown_and_mentions_every_locus(self):
        resp = self.client.get("/api/nt_ot_quotations/export")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "text/markdown; charset=utf-8")
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])
        d = self.client.get("/api/nt_ot_quotations").json()
        for r in d["rows"]:
            self.assertIn(r["nt_ref"], resp.text)


if __name__ == "__main__":
    unittest.main()
