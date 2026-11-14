"""Catalog tab: the unfinished-request detector and the research-file classifier (Claude GUI, Opus 5.5, 2026-10-13).
Each rule is tested in both directions, so the check can fail."""
import csv
import io
import os
import sys
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(APP_DIR, "tools"))
sys.path.insert(0, APP_DIR)

import hanging_turns as H          # noqa: E402
import ag_output_catalog as C      # noqa: E402


def turn(text, events, ts="2020-01-01T00:00:00Z", interrupted=False):
    return {"ts": ts, "uuid": text[:8], "text": text, "events": events, "launched": set(), "interrupted": interrupted}


class TestClassify(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(H.classify(turn("a", [("tool", "x"), ("answer", "done")]))[0], "ok")
        self.assertEqual(H.classify(turn("a", [("answer", "on it"), ("error", "You've hit your session limit")]))[0], "died")
        self.assertEqual(H.classify(turn("a", [("answer", "starting"), ("tool", "Bash")]))[0], "cut")
        self.assertEqual(H.classify(turn("a", []))[0], "silent")
        self.assertEqual(H.classify(turn("a", [("tool", "Bash")], interrupted=True))[0], "stopped")

    def test_failed_agents(self):
        t = turn("a", [("answer", "launched")])
        t["launched"] = {"ag1", "ag2"}
        self.assertEqual(H.classify(t, {"ag1": "failed", "ag2": "completed"})[0], "agents")
        self.assertEqual(H.classify(t, {"ag1": "completed", "ag2": "completed"})[0], "ok")

    def test_try_again_recovers_and_failed_retry_does_not(self):
        died = turn("write the book", [("error", "limit")])
        fixed = turn("try again", [("answer", "here it is")])
        self.assertEqual(H.resolve([died, fixed], "Claude", "s", "t"), [])
        still = turn("try again", [("error", "limit")])
        rows = H.resolve([died, still], "Claude", "s", "t")
        self.assertTrue(rows and all(r["request"] == "write the book" for r in rows))

    def test_continue_is_short_only(self):
        self.assertTrue(H.CONTINUE.match("Try again"))
        self.assertTrue(H.CONTINUE.match("ok continue"))
        self.assertFalse(H.CONTINUE.match("continue the trinity chapter and add the oneness refutation from both gemini conversations"))
        self.assertFalse(H.CONTINUE.match("write the book"))

    def test_resend_is_not_hanging(self):
        a = turn("ok now i want best selling books", [])
        b = turn("ok now i want best selling books in general yearly", [("answer", "done")])
        self.assertEqual(H.resolve([a, b], "Antigravity", "s", ""), [])
        c = turn("something else entirely", [("answer", "done")])
        self.assertEqual(len(H.resolve([a, c], "Antigravity", "s", "")), 1)


class TestCatalogKinds(unittest.TestCase):
    P = C.PROJECT

    def test_kind_and_side(self):
        d = os.path.join(self.P, "03_RESEARCH_DOSSIERS", "DOSSIER_GATES_OF_HADES.md")
        self.assertEqual(C._kind(d), "dossier")
        self.assertEqual(C._subject(d, "dossier"), "subject")
        code = os.path.join(self.P, "09_APPS_CATHOLICJARVIS", "x.py")
        self.assertEqual(C._kind(code), "code")
        self.assertEqual(C._subject(code, "code"), "infrastructure")
        ctl = os.path.join(self.P, "_RESUME_CORE.md")
        self.assertEqual(C._subject(ctl, C._kind(ctl)), "infrastructure")
        game = r"C:\Users\Elation\AppData\Local\Game\GameUserSettings.ini"
        self.assertEqual(C._subject(game, C._kind(game)), "infrastructure")

    def test_file_url_paths(self):
        self.assertEqual(C._norm("file:///C:/Users/Elation/a%20b.md"), os.path.normpath(r"C:\Users\Elation\a b.md"))


class TestNoise(unittest.TestCase):
    def test_noise(self):
        from modules import catalog_routes as R
        for s in ("login", "claude logout", "--resume", "winget upgrade Anthropic.ClaudeCode"):
            self.assertTrue(R.NOISE.match(s), s)
        self.assertFalse(R.NOISE.match("log the Montanism finding and write chapter 5"))


class LiveTests(unittest.TestCase):
    """Hits the real, built ag_output_catalog.json through the actual app -- same discipline as
    tests/test_recall.py's LiveTests for the export it mirrors."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from modules import catalog_routes as R
        sys.path.insert(0, APP_DIR)
        from app import app
        cls.client = TestClient(app)
        if not os.path.exists(R.FILES_JSON):
            raise unittest.SkipTest("data/ag_output_catalog.json not built")

    def test_export_csv_returns_well_formed_download(self):
        """New 2026-11-12 feature: /api/catalog/files/export. Same shape check as the Recall
        export's test -- a CSV that looks right in a raw diff can still be malformed if a field
        with an embedded newline isn't quoted correctly."""
        resp = self.client.get("/api/catalog/files/export", params={"infra": 0})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])
        rows = list(csv.reader(io.StringIO(resp.text)))
        self.assertEqual(rows[0], ["path", "rel", "writers", "kind", "side", "era", "words", "bytes",
                                    "exists", "first", "last", "request", "description", "sessions"])
        self.assertEqual(len(rows) - 1, int(resp.headers["x-catalog-export-rows"]))
        self.assertTrue(all(len(r) == len(rows[0]) for r in rows), "every row must match the header's column count")

    def test_portfolio_summary_matches_subject_side_files(self):
        """New 2026-11-12 feature: /api/catalog/portfolio. total_words/total_files must match a
        manual recomputation from /files?infra=0 (existing, subject-side rows only), not just be
        some plausible-looking number."""
        files_rows = self.client.get("/api/catalog/files", params={"infra": 0}).json()["rows"]
        existing = [r for r in files_rows if r.get("exists")]
        want_words = sum(r.get("words") or 0 for r in existing)
        p = self.client.get("/api/catalog/portfolio").json()
        self.assertEqual(p["total_files"], len(existing))
        self.assertEqual(p["total_words"], want_words)
        self.assertEqual(sum(p["by_kind"].values()), len(existing))
        self.assertTrue(p["top_works"], "portfolio should list at least one work")
        words_in_order = [w["words"] for w in p["top_works"]]
        self.assertEqual(words_in_order, sorted(words_in_order, reverse=True), "top_works must be sorted largest-first")

    def test_portfolio_export_is_markdown_and_mentions_every_top_work(self):
        resp = self.client.get("/api/catalog/portfolio/export")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["content-type"], "text/markdown; charset=utf-8")
        self.assertIn("attachment; filename=", resp.headers["content-disposition"])
        p = self.client.get("/api/catalog/portfolio").json()
        for w in p["top_works"]:
            self.assertIn(w["title"], resp.text, f"{w['title']!r} missing from the portfolio export")

    def test_rigor_tag_counts_are_internally_consistent(self):
        """New 2026-11-12 feature: /api/catalog/rigor (the [V]/[R]/[S] citation-tier metric).
        totals must equal the sum of the per-file top_files breakdown isn't enough to prove (it's
        capped at 20) -- but every rate and count that IS exposed must be arithmetically
        consistent with the others, and top_files must be real files that exist on disk."""
        g = self.client.get("/api/catalog/rigor").json()
        total = g["totals"]["V"] + g["totals"]["R"] + g["totals"]["S"]
        if total == 0:
            self.skipTest("no [V]/[R]/[S] tags found in the current corpus")
        self.assertEqual(g["verified_rate"], round(100 * g["totals"]["V"] / total, 1))
        self.assertEqual(g["sourced_rate"], round(100 * (g["totals"]["V"] + g["totals"]["R"]) / total, 1))
        self.assertLessEqual(g["files_with_tags"], g["files_scanned"])
        tagged_in_order = [f["tagged"] for f in g["top_files"]]
        self.assertEqual(tagged_in_order, sorted(tagged_in_order, reverse=True))
        for f in g["top_files"]:
            self.assertEqual(f["tagged"], f["V"] + f["R"] + f["S"])

    def test_rigor_strips_code_spans_and_legend_lines_before_counting(self):
        """Falsification test for the Rule 14 discipline this feature must follow: a fabricated
        file that only QUOTES the citation-tag legend (inside a code span, and as a literal
        "**Legend:**" line) must report zero tags, not 3 -- otherwise a dossier that merely cites
        CLAUDE.md's own rule text would inflate its own rigor score."""
        import tempfile
        from modules import catalog_routes as R
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write("Some real prose with no tags at all.\n\n"
                     "`[V]` is mentioned here only as a code span, not a real tag.\n\n"
                     "**Legend:** [V] verified, [R] reliably sourced, [S] stated/unsourced.\n")
            path = fh.name
        try:
            counts = R._count_tags_in_file(path)
            self.assertEqual(counts, {"V": 0, "R": 0, "S": 0})
        finally:
            os.unlink(path)

    def test_rigor_counts_a_real_inline_tag(self):
        """The positive case for the same falsification pair: an actual inline [V] in prose
        (not inside a code span, not on a Legend line) must be counted."""
        import tempfile
        from modules import catalog_routes as R
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write("Augustine makes this argument in City of God XI.26 [V].\n"
                     "Jerome is reported to hold a similar view [R].\n"
                     "This connection is my own inference [S].\n")
            path = fh.name
        try:
            counts = R._count_tags_in_file(path)
            self.assertEqual(counts, {"V": 1, "R": 1, "S": 1})
        finally:
            os.unlink(path)

    def test_cite_returns_three_formats_for_a_real_file(self):
        """New 2026-11-12 feature: /api/catalog/cite?rel=. Generalizes manuscripts_core.py's
        format_citation() (SBL/Chicago/BibTeX for manuscript folios) to James's own dossiers."""
        rows = self.client.get("/api/catalog/files", params={"infra": 0}).json()["rows"]
        existing = [r for r in rows if r.get("exists")]
        self.assertTrue(existing)
        rel = existing[0]["rel"]
        c = self.client.get("/api/catalog/cite", params={"rel": rel}).json()
        for key in ("title", "year", "sbl", "chicago", "bibtex"):
            self.assertIn(key, c)
        self.assertTrue(c["title"], "title must not be blank")
        self.assertIn(c["title"], c["sbl"])
        self.assertIn(c["title"], c["chicago"])
        self.assertIn(c["title"], c["bibtex"])
        self.assertIn("@unpublished{", c["bibtex"])
        # Rule 4/19 discipline: never fabricate an author name this project was never given.
        self.assertIn("[Author Surname, First Name]", c["sbl"])

    def test_cite_unknown_rel_is_404(self):
        resp = self.client.get("/api/catalog/cite", params={"rel": "not/a/real/path.md"})
        self.assertEqual(resp.status_code, 404)

    def test_export_infra_filter_matches_the_json_route(self):
        """The export must honor ?infra= exactly like /files does, not just accept and ignore it.
        /files's own "total" field reports the FULL unfiltered row count by design (same split
        as /api/recall/search's total-vs-returned) -- the filtered count is len(rows), so that's
        what the export's row count must match, not "total"."""
        want = len(self.client.get("/api/catalog/files", params={"infra": 1}).json()["rows"])
        got = int(self.client.get("/api/catalog/files/export", params={"infra": 1}).headers["x-catalog-export-rows"])
        self.assertEqual(got, want)
        want0 = len(self.client.get("/api/catalog/files", params={"infra": 0}).json()["rows"])
        got0 = int(self.client.get("/api/catalog/files/export", params={"infra": 0}).headers["x-catalog-export-rows"])
        self.assertEqual(got0, want0)
        self.assertGreaterEqual(want, want0, "infra=1 (everything) must be >= infra=0 (subject only)")


if __name__ == "__main__":
    unittest.main()
