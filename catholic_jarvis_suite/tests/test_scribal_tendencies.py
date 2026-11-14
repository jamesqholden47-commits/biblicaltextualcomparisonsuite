"""Scribal Tendencies Profiler (modules/scribal_tendencies_routes.py), added 2026-11-12 to close
the gap named in the prior /deep-research entry: wiring up the already-computed-but-never-exposed
web_app/sources_cache/scribal_tendencies.json, plus the Jeremiah cross-check research agent #3
proposed. These tests falsify that the cross-check is a real, independently-computed convergence,
not an asserted one: Jeremiah's rank must actually come from the data, and the flagged-chapter
count must actually match modules/mt_lxx_routes.py's own live output, not a hardcoded guess."""
import os
import sys
import unittest
from unittest import mock

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from fastapi.testclient import TestClient  # noqa: E402

from modules import scribal_tendencies_routes as S  # noqa: E402
from modules import mt_lxx_routes as M  # noqa: E402


class UnitTests(unittest.TestCase):
    def test_jeremiah_cross_check_handles_none_correlation_without_crashing(self):
        """Falsification check for the real bug self-refinement loop 1 found: pearson() in
        build_scribal_tendencies.py can return None (too few paired verses, or zero variance),
        and sorting None against a float raises TypeError. None of the 39 shipped books hit this
        today, but a future rebuild could -- plant a fake book with None and confirm no crash."""
        fake_data = {"books": {
            "jer": {"book_id": "jer", "display": "Jeremiah", "greek_words_per_hebrew_word": 1.359,
                    "verse_length_correlation": 0.4144, "rank_freest_to_most_literal": 1},
            "weird": {"book_id": "weird", "display": "Weird", "greek_words_per_hebrew_word": 2.0,
                      "verse_length_correlation": None, "rank_freest_to_most_literal": 2},
        }}
        result = S._jeremiah_cross_check(fake_data)  # must not raise
        self.assertIsNotNone(result)
        self.assertEqual(result["verse_length_correlation_rank"].split("/")[0], "1")

    def test_load_returns_none_on_malformed_json_not_a_crash(self):
        """_load() previously only caught OSError -- a present-but-corrupt JSON file would raise
        ValueError/JSONDecodeError and 500 the route instead of degrading to 503."""
        with mock.patch("builtins.open", mock.mock_open(read_data="{not valid json")):
            self.assertIsNone(S._load())


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        cls.client = TestClient(app)
        if S._load() is None:
            raise unittest.SkipTest("web_app/sources_cache/scribal_tendencies.json not built")

    def test_module_is_mounted(self):
        r = self.client.get("/api/modules").json()
        self.assertEqual(r["routers"].get("scribal_tendencies_routes"), "loaded")

    def test_returns_503_when_data_file_missing(self):
        with mock.patch.object(S, "DATA_PATH", r"C:\does\not\exist\scribal_tendencies.json"):
            resp = self.client.get("/api/scribal_tendencies")
            self.assertEqual(resp.status_code, 503)

    def test_jeremiah_cross_check_rank_matches_raw_data(self):
        """The reported rank must be independently re-derivable from the raw book data, not a
        number that could silently drift out of sync with it."""
        d = self.client.get("/api/scribal_tendencies").json()
        books = d["books"]
        jer = books["jer"]
        cross = d["jeremiah_cross_check"]
        self.assertEqual(cross["greek_words_per_hebrew_word"], jer["greek_words_per_hebrew_word"])
        want_rank = f"{jer['rank_freest_to_most_literal']}/{len(books)}"
        self.assertEqual(cross["freest_to_most_literal_rank"], want_rank)
        # Jeremiah is well known to be the most heavily compressed LXX book (Tov) -- the freest
        # rank should be 1, not merely present.
        self.assertEqual(jer["rank_freest_to_most_literal"], 1)

    def test_jeremiah_flagged_chapter_count_matches_live_mt_lxx_scan(self):
        """Falsification check: the cross-check's chapter count must equal an independent count
        from the actual live /api/mt_lxx/divergence scan, not a cached or guessed number."""
        d = self.client.get("/api/scribal_tendencies").json()
        reported = d["jeremiah_cross_check"]["mt_lxx_flagged_chapter_count"]
        live = self.client.get("/api/mt_lxx/divergence").json()
        want = sum(1 for r in live["rows"] if r["book_id"] == "jer")
        self.assertEqual(reported, want)
        self.assertGreater(want, 0, "Jeremiah should have at least one flagged chapter for this cross-check to mean anything")

    def test_deferred_metrics_note_is_present_and_explains_why(self):
        d = self.client.get("/api/scribal_tendencies").json()
        self.assertIn("alignment", d["deferred_metrics_note"].lower())

    def test_export_is_markdown_and_contains_the_cross_check(self):
        resp = self.client.get("/api/scribal_tendencies/export")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "text/markdown; charset=utf-8")
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])
        d = self.client.get("/api/scribal_tendencies").json()
        self.assertIn(d["jeremiah_cross_check"]["convergence"], resp.text)

    def test_function_word_share_extends_kai_without_breaking_it(self):
        """New 2026-11-12 addition (self-refinement loop 5's finding): function_word_share
        extends the original kai_share_of_greek density metric to en/eis/gar/de. The kai entry
        inside function_word_share must still equal the original standalone field -- confirms
        the extension didn't silently change the existing metric's value."""
        d = self.client.get("/api/scribal_tendencies").json()
        for bid, b in d["books"].items():
            self.assertIn("function_word_share", b, bid)
            fw = b["function_word_share"]
            for key in ("kai", "en", "eis", "gar", "de"):
                self.assertIn(key, fw, f"{bid} missing {key}")
                self.assertGreaterEqual(fw[key], 0)
            self.assertEqual(fw["kai"], b["kai_share_of_greek"], f"{bid}: kai share diverged from the original field")

    def test_all_39_books_present_in_ranking(self):
        d = self.client.get("/api/scribal_tendencies").json()
        self.assertEqual(len(d["ranked_freest_to_most_literal"]), len(d["books"]))
        self.assertEqual(set(d["ranked_freest_to_most_literal"]), set(d["books"].keys()))


if __name__ == "__main__":
    unittest.main()
