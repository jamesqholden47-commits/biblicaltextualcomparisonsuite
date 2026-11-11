"""
Unit, integration, and falsification tests for Reader module (module id "reader", task C004).
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE_ROOT = os.path.dirname(HERE)
if SUITE_ROOT not in sys.path:
    sys.path.insert(0, SUITE_ROOT)

from fastapi.testclient import TestClient
from app import app
from modules import reader_core as core
from tools.make_tier_briefs import generate_tier_brief


class ReaderUnitTests(unittest.TestCase):
    def test_list_chapters_count(self):
        chapters = core.list_chapters()
        self.assertEqual(len(chapters), 35)
        for ch in chapters:
            self.assertTrue(ch["filename"].endswith(".md"))
            self.assertTrue(len(ch["title"]) > 0)
            self.assertGreater(ch["size"], 0)

    def test_render_markdown_and_badge_conversion(self):
        sample = """# Chapter Header
This is a paragraph with [V: García-Molina, p. 177] and [R: Alberro 1988] and [S].

## Section 1
- Item 1 [V]
- Item 2
"""
        html = core.render_markdown(sample)
        self.assertIn('<h1 class="reader-h reader-h1">Chapter Header</h1>', html)
        self.assertIn('<h2 class="reader-h reader-h2">Section 1</h2>', html)
        self.assertIn('class="reader-badge badge-v"', html)
        self.assertIn('class="reader-badge badge-r"', html)
        self.assertIn('class="reader-badge badge-s"', html)
        self.assertIn('title="[V: García-Molina, p. 177]"', html)

    def test_count_tags(self):
        text = "Fact 1 [V], fact 2 [V: note], fact 3 [R], fact 4 [S], fact 5 [V/S]."
        counts = core.count_tags(text)
        self.assertEqual(counts["V"], 3)  # [V], [V: note], [V/S]
        self.assertEqual(counts["R"], 1)
        self.assertEqual(counts["S"], 2)  # [S], [V/S]

    def test_extract_checking_items(self):
        sample = """
# Chapter 06

## 17. Before using this in public: what still needs checking

### The load-bearing claims
- Are the count of 43 really as set out?
- Do the four Protestants stand as quoted?
"""
        items = core.extract_checking_items(sample, "06_test")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["category"], "The load-bearing claims")
        self.assertIn("count of 43", items[0]["text"])

    def test_tier_loading(self):
        # When tier file does not exist
        res = core.get_section_tier("06_inquisition_black_legend", "999")
        self.assertEqual(res["status"], "not_generated")


class ReaderFalsificationTests(unittest.TestCase):
    def test_html_injection_is_strictly_escaped(self):
        """Falsification: Planted raw <script> and angle brackets in markdown must be escaped, never raw."""
        malicious = "Malicious text <script>alert('xss')</script> and <img src=x onerror=alert(1)> [V]"
        rendered = core.render_markdown(malicious)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&lt;img", rendered)

    def test_make_tier_briefs_refuses_overwrite(self):
        """Falsification: Attempting to generate a brief over an existing file must raise FileExistsError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            import tools.make_tier_briefs as tb
            old_inbox = tb.INBOX_TIERS
            tb.INBOX_TIERS = tmp_dir
            try:
                p1 = tb.generate_tier_brief("test_ch", "1", "Test Title")
                self.assertTrue(os.path.exists(p1))
                with self.assertRaises(FileExistsError):
                    tb.generate_tier_brief("test_ch", "1", "Test Title")
            finally:
                tb.INBOX_TIERS = old_inbox


class ReaderAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_reader_endpoints(self):
        # 1. Chapters list
        r1 = self.client.get("/api/reader/chapters")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["count"], 35)

        # 2. Specific chapter data
        r2 = self.client.get("/api/reader/chapters/06_inquisition_black_legend")
        self.assertEqual(r2.status_code, 200)
        data = r2.json()
        self.assertEqual(data["stem"], "06_inquisition_black_legend")
        self.assertIn("html", data)
        self.assertIn("tag_counts", data)
        self.assertIn("checking_items", data)

        # 3. Book-wide checking
        r3 = self.client.get("/api/reader/checking")
        self.assertEqual(r3.status_code, 200)
        self.assertGreater(r3.json()["count"], 10)

        # 4. Tiers endpoint
        r4 = self.client.get("/api/reader/tiers/06_inquisition_black_legend/1")
        self.assertEqual(r4.status_code, 200)
        self.assertIn("status", r4.json())


# ---------------------------------------------------------------------------------------------------
# C007 (2026-10-06): the Reader opens any allowed document, and refuses every other path with 403.
# These tests point the core module at temporary folders so they do not depend on 10_VOLUMES existing.
# ---------------------------------------------------------------------------------------------------
import json
import subprocess
import time

SAMPLE_MD = """# Sample Volume

Intro paragraph with a verified claim [V: Smith 1999, p. 4] and a reported one [R: Jones 2001] and a loose one [S].

## 1. First section

- bullet one [V]
- bullet two

## 2. Second section

Text <script>alert('xss')</script> stays text.

## 17. Before using this in public: what still needs checking

### The load-bearing claims
- Is the 1999 date right?
- Does Jones really say this?
"""


def _free_drive_path():
    for letter in "QYZXW":
        if not os.path.exists(letter + ":\\"):
            return letter + ":\\anything\\secret.md"
    return "Q:\\anything\\secret.md"


class ReaderDocBase(unittest.TestCase):
    """Builds tmp/chapters, tmp/volumes, tmp/volumes_evil, tmp/outside and a registry, and points core at them."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self._saved = (core.CHAPTERS_DIR, core.VOLUMES_DIR, core.REGISTRY_PATH, core.ASSEMBLED_FILE)
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.chapters = os.path.join(t, "chapters")
        self.volumes = os.path.join(t, "volumes")
        self.evil = os.path.join(t, "volumes_evil")      # shares the prefix "volumes" with the allowed folder
        self.outside = os.path.join(t, "outside")
        for d in (self.chapters, self.volumes, os.path.join(self.volumes, "sub"), self.evil, self.outside):
            os.makedirs(d)
        self.vol_md = os.path.join(self.volumes, "sub", "volume_one.md")
        self.reg_md = os.path.join(self.outside, "registered.md")
        self.reg_html = os.path.join(self.outside, "registered.html")
        self.unreg_md = os.path.join(self.outside, "unregistered.md")
        self.evil_md = os.path.join(self.evil, "x.md")
        self.vol_py = os.path.join(self.volumes, "evil.py")
        self.reg_py = os.path.join(self.outside, "listed.py")
        self.chap_py = os.path.join(self.chapters, "evil.py")
        self.chap_md = os.path.join(self.chapters, "01_test_chapter.md")
        self.assembled = os.path.join(t, "ASSEMBLED.md")
        for path, text in ((self.vol_md, SAMPLE_MD), (self.reg_md, SAMPLE_MD), (self.unreg_md, SAMPLE_MD),
                           (self.evil_md, SAMPLE_MD), (self.vol_py, "print('x')\n"), (self.reg_py, "print('y')\n"),
                           (self.chap_py, "print('z')\n"), (self.chap_md, SAMPLE_MD), (self.assembled, SAMPLE_MD)):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
        with open(self.reg_html, "w", encoding="utf-8") as fh:
            fh.write("<html><head><title>Reg Page</title><style>p{color:red}</style><script>var leak=1;</script></head>"
                     "<body><h1>Heading One</h1><p>Body text [V: Someone 2000] with <b>bold</b> &amp; an entity.</p>"
                     "<h2>2. Part Two</h2><ul><li>first</li><li>second</li></ul></body></html>")
        self.registry = os.path.join(t, "loose_registry.json")
        self.write_registry([self.reg_md, self.reg_html, self.reg_py])
        core.set_chapters_dir(self.chapters)
        core.set_volumes_dir(self.volumes)
        core.set_registry_path(self.registry)
        core.set_assembled_file(self.assembled)
        core._DOC_CACHE.clear()
        del core._DOC_CACHE_ORDER[:]

    def tearDown(self):
        core.set_chapters_dir(self._saved[0])
        core.set_volumes_dir(self._saved[1])
        core.set_registry_path(self._saved[2])
        core.set_assembled_file(self._saved[3])
        core._DOC_CACHE.clear()
        del core._DOC_CACHE_ORDER[:]
        self.tmp.cleanup()

    def write_registry(self, paths):
        docs = [{"path": p, "title": os.path.basename(p), "kind": "SUBJECT", "area": "test"} for p in paths]
        with open(self.registry, "w", encoding="utf-8") as fh:
            json.dump({"docs": docs}, fh)

    def doc(self, path, **kw):
        params = {"path": path}
        params.update(kw)
        return self.client.get("/api/reader/doc", params=params)


class ReaderDocOpenTests(ReaderDocBase):
    """Question 1, the allowed side."""

    def test_registry_markdown_has_chapter_structure(self):
        r = self.doc(self.reg_md)
        self.assertEqual(r.status_code, 200, r.text)
        d = r.json()
        self.assertEqual(d["source"], "registry")
        self.assertEqual(d["tag_counts"], {"V": 2, "R": 1, "S": 1, "other": 0})
        self.assertEqual(d["checking_count"], 2)
        self.assertEqual(d["checking_items"][0]["category"], "The load-bearing claims")
        self.assertEqual([s["title"] for s in d["sections"] if s["level"] == 2][:2], ["1. First section", "2. Second section"])
        self.assertIn('class="reader-badge badge-v"', d["html"])
        self.assertIn('class="reader-badge badge-r"', d["html"])
        for key in ("stem", "filename", "title", "tag_counts", "sections", "checking_items", "checking_count",
                    "available_tiers", "html", "parts", "part", "part_count"):
            self.assertIn(key, d)
        self.assertEqual(d["title"], "Sample Volume")
        self.assertEqual(d["part_count"], 1)

    def test_clean_case_matches_the_chapter_endpoint_exactly(self):
        """A real chapter opened by path must equal what /chapters/{stem} returns (same render, tags, checks)."""
        core.set_chapters_dir(self._saved[0])
        chapters = core.list_chapters()
        self.assertEqual(len(chapters), 35)
        ch = chapters[5]
        via_doc = self.doc(ch["path"]).json()
        via_chapter = self.client.get("/api/reader/chapters/" + ch["stem"]).json()
        self.assertEqual(via_doc["source"], "chapter")
        self.assertEqual(via_doc["html"], via_chapter["html"])
        self.assertEqual(via_doc["tag_counts"], via_chapter["tag_counts"])
        self.assertEqual(via_doc["checking_items"], via_chapter["checking_items"])
        self.assertEqual([(s["level"], s["title"]) for s in via_doc["sections"]],
                         [(s["level"], s["title"]) for s in via_chapter["sections"]])

    def test_volumes_folder_file_opens_and_assembled_file_opens(self):
        r = self.doc(self.vol_md)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["source"], "volume")
        r2 = self.doc(self.assembled)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["source"], "chapter")
        r3 = self.doc(self.chap_md)
        self.assertEqual(r3.status_code, 200)

    def test_quoted_path_and_case_variant(self):
        """Explorer's 'Copy as path' wraps the path in quotes; Windows paths are case-insensitive."""
        self.assertEqual(self.doc('"' + self.vol_md + '"').status_code, 200)
        if os.name == "nt":
            self.assertEqual(self.doc(self.vol_md.upper()).status_code, 200)

    def test_html_document_is_reduced_to_safe_text(self):
        d = self.doc(self.reg_html).json()
        self.assertEqual(d["format"], "html")
        self.assertEqual(d["title"], "Heading One")
        self.assertIn("Body text", d["html"])
        self.assertNotIn("var leak", d["html"])          # <script> body dropped
        self.assertNotIn("color:red", d["html"])         # <style> body dropped
        self.assertEqual(d["tag_counts"]["V"], 1)
        self.assertIn("&amp;", d["html"])                # the "&" is escaped again by the renderer
        self.assertEqual([s["title"] for s in d["sections"]], ["Heading One", "2. Part Two"])

    def test_missing_volumes_folder_is_not_an_error(self):
        core.set_volumes_dir(os.path.join(self.tmp.name, "does_not_exist_yet"))
        r = self.client.get("/api/reader/docs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["volumes"], [])
        # a file "inside" the missing folder is allowed-by-prefix but absent: 404, not 403 and not 500
        self.assertEqual(self.doc(os.path.join(self.tmp.name, "does_not_exist_yet", "a.md")).status_code, 404)

    def test_library_lists_volumes_and_filters_registry(self):
        d = self.client.get("/api/reader/docs").json()
        self.assertEqual([v["rel"] for v in d["volumes"]], [os.path.join("sub", "volume_one.md")])
        titles = [x["title"] for x in d["docs"]]
        self.assertIn("registered.md", titles)
        self.assertNotIn("listed.py", titles)             # not a renderable type, so not offered
        d2 = self.client.get("/api/reader/docs", params={"q": "REGISTERED html"}).json()
        self.assertEqual([x["title"] for x in d2["docs"]], ["registered.html"])

    def test_regenerated_registry_is_picked_up(self):
        self.assertEqual(self.doc(self.unreg_md).status_code, 403)
        self.write_registry([self.reg_md, self.reg_html, self.reg_py, self.unreg_md])
        self.assertEqual(self.doc(self.unreg_md).status_code, 200)

    def test_missing_registry_allows_only_folders(self):
        core.set_registry_path(os.path.join(self.tmp.name, "no_such_registry.json"))
        self.assertEqual(self.doc(self.reg_md).status_code, 403)
        self.assertEqual(self.doc(self.vol_md).status_code, 200)


class ReaderDocRefusalTests(ReaderDocBase):
    """Question 1, the refusing side: the security boundary."""

    def assert403(self, path, why):
        r = self.doc(path)
        self.assertEqual(r.status_code, 403, f"{why}: {path!r} gave {r.status_code} {r.text[:120]}")

    def test_paths_outside_the_allowed_set(self):
        self.assert403(self.unreg_md, "markdown file not in registry, not in an allowed folder")
        self.assert403(os.path.join(self.outside, "nope.md"), "non-existent file outside: must not leak existence")
        self.assert403(os.environ.get("WINDIR", "C:\\Windows") + "\\win.ini", "system file")
        self.assert403(_free_drive_path(), "another drive")
        self.assert403("\\\\server\\share\\a.md", "UNC path")

    def test_dotdot_paths(self):
        self.assert403(os.path.join(self.volumes, "..", "outside", "unregistered.md"), ".. out of volumes")
        self.assert403(self.volumes + "\\sub\\..\\..\\outside\\unregistered.md", ".. with backslashes")
        self.assert403(self.chapters + "\\..\\outside\\unregistered.md", ".. out of chapters")
        # a .. that stays inside the folder is fine
        self.assertEqual(self.doc(os.path.join(self.volumes, "sub", "..", "sub", "volume_one.md")).status_code, 200)

    def test_sibling_folder_sharing_a_name_prefix(self):
        """Falsification for a startswith() bug: 'volumes_evil' begins with 'volumes'."""
        self.assert403(self.evil_md, "sibling folder with the same prefix")

    def test_non_document_files_in_allowed_places(self):
        self.assert403(self.vol_py, ".py inside the volumes folder")
        self.assert403(self.chap_py, ".py inside the chapters folder")
        self.assert403(self.reg_py, ".py listed in the registry")
        self.assert403(self.registry, ".json registry itself")
        self.assert403(self.reg_md + ":stream", "alternate data stream suffix")

    def test_malformed_input(self):
        self.assert403("", "empty")
        self.assert403("   ", "blank")
        self.assert403("volume_one.md", "relative path")
        self.assert403("..\\..\\volume_one.md", "relative with ..")
        self.assert403(self.vol_md + chr(0) + ".py", "NUL byte")
        self.assert403("C:foo.md", "drive-relative path")
        self.assertEqual(self.client.get("/api/reader/doc").status_code, 422)

    def test_junction_inside_allowed_folder_cannot_lead_outside(self):
        """Falsification: plant a directory junction inside the volumes folder that points at the outside
        folder. Lexically the path is under volumes; really it is not. It must be refused."""
        link = os.path.join(self.volumes, "escape")
        res = subprocess.run(["cmd", "/c", "mklink", "/J", link, self.outside], capture_output=True, text=True)
        if res.returncode != 0 or not os.path.isdir(link):
            self.skipTest("could not create a junction here: " + res.stdout + res.stderr)
        try:
            self.assertTrue(os.path.isfile(os.path.join(link, "unregistered.md")))     # the defect really is planted
            self.assert403(os.path.join(link, "unregistered.md"), "junction escape")
        finally:
            os.rmdir(link)                    # removes only the link, never its target

    def test_chapter_stem_cannot_walk_out_of_the_chapters_folder(self):
        for stem in ("..%5C..%5Coutside%5Cunregistered", "..%2Foutside%2Funregistered", "C%3A%5Cx", "%00"):
            r = self.client.get("/api/reader/chapters/" + stem)
            self.assertEqual(r.status_code, 404, stem)
        self.assertEqual(self.client.get("/api/reader/chapters/01_test_chapter").status_code, 200)

    def test_file_over_the_size_limit_is_413(self):
        old = core.MAX_DOC_BYTES
        core.MAX_DOC_BYTES = 100
        try:
            self.assertEqual(self.doc(self.vol_md).status_code, 413)
        finally:
            core.MAX_DOC_BYTES = old


class ReaderDocInjectionTests(ReaderDocBase):
    def test_planted_markup_in_a_document_is_escaped(self):
        """Falsification: a volume containing live-looking markup must come back as inert text."""
        evil = os.path.join(self.volumes, "evil_markup.md")
        with open(evil, "w", encoding="utf-8") as fh:
            fh.write('# T\n\n<img src=x onerror=alert(1)> and <script>alert(2)</script> [V: "q" onmouseover="x"]\n')
        h = self.doc(evil).json()["html"]
        self.assertNotIn("<img", h)
        self.assertNotIn("<script", h)
        self.assertNotIn('onmouseover="x"', h)
        self.assertIn("&lt;script&gt;", h)
        # and the same text delivered as an HTML document
        evil_html = os.path.join(self.volumes, "evil_markup.html")
        with open(evil_html, "w", encoding="utf-8") as fh:
            fh.write('<h1>T</h1><p>&lt;b&gt;not bold&lt;/b&gt; <img src=x onerror=alert(1)></p>')
        h2 = self.doc(evil_html).json()["html"]
        self.assertNotIn("<img", h2)
        self.assertNotIn("<b>", h2)
        self.assertIn("&lt;b&gt;", h2)


class ReaderDocPartsTests(ReaderDocBase):
    """Question 5 (design): a table of contents first, sections on demand, nothing lost."""

    def big_text(self, n_sections=60, para_chars=4000):
        out = ["# Big Volume\n"]
        for i in range(n_sections):
            out.append(f"## {i + 1}. Section number {i + 1}\n")
            out.append(("Paragraph text with a tag [R: Scholar {0}] ".format(i) * (para_chars // 40)).strip() + "\n")
        return "\n".join(out)

    def test_split_is_lossless_and_bounded(self):
        text = self.big_text()
        parts = core._split_parts(text)
        self.assertGreater(len(parts), 1)
        self.assertEqual("\n".join(parts), text)            # not one character dropped
        self.assertLessEqual(max(len(p) for p in parts), core.PART_CHARS * 2)

    def test_split_of_one_giant_unheaded_block_is_lossless(self):
        text = "\n\n".join(("Paragraph %d. " % i) * 200 for i in range(400))      # no headings at all
        parts = core._split_parts(text)
        self.assertGreater(len(parts), 1)
        self.assertEqual("\n".join(parts), text)

    def test_small_file_is_a_single_part(self):
        self.assertEqual(core._split_parts("# t\n\nshort"), ["# t\n\nshort"])

    def test_every_heading_is_reachable_through_the_parts(self):
        path = os.path.join(self.volumes, "big.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.big_text())
        first = self.doc(path).json()
        n = first["part_count"]
        self.assertGreater(n, 1)
        self.assertEqual(len(first["parts"]), n)
        self.assertEqual(len(first["sections"]), 61)          # whole-document table of contents, not just part 0
        self.assertEqual(first["tag_counts"]["R"], 60 * (4000 // 40))
        seen = 0
        for k in range(n):
            d = self.doc(path, part=k).json()
            self.assertEqual(d["part"], k)
            for s in d["sections"]:
                if s["part"] == k:
                    seen += 1
                    if s["level"] == 2:
                        self.assertIn(">" + s["title"] + "<", d["html"])
        self.assertEqual(seen, 61)
        self.assertEqual(self.doc(path, part=n).status_code, 404)
        self.assertEqual(self.doc(path, part=-1).status_code, 422)

    def test_assembled_readers_edition_is_responsive(self):
        """Question 5: the real 4.7 MB assembled edition. Measured times are printed (see the C007 report)."""
        real = r"C:\Users\Elation\Mexico_Protestantism_Study\05_READERS_EDITION\THE_CATHOLIC_CASE_Readers_Edition.md"
        if not os.path.isfile(real):
            self.skipTest("assembled edition not on this machine")
        core.set_assembled_file(real)
        core._DOC_CACHE.clear()
        del core._DOC_CACHE_ORDER[:]
        size = os.path.getsize(real)
        t0 = time.perf_counter()
        r = self.doc(real)
        cold = time.perf_counter() - t0
        self.assertEqual(r.status_code, 200)
        d = r.json()
        t0 = time.perf_counter()
        r2 = self.doc(real, part=d["part_count"] - 1)
        last = time.perf_counter() - t0
        t0 = time.perf_counter()
        self.doc(real, part=7)
        mid = time.perf_counter() - t0
        print("\nC007 timing: %d bytes, %d parts, first request (cold) %.3f s, last part %.3f s, part 7 %.3f s, payload part 0 %d bytes"
              % (size, d["part_count"], cold, last, mid, len(r.content)))
        self.assertGreater(size, 4_000_000)
        self.assertGreater(d["part_count"], 10)
        self.assertLess(cold, 5.0)
        self.assertLess(last, 1.0)
        self.assertLess(len(r.content), 1_000_000)           # a part, not the whole 4.7 MB
        self.assertEqual(r2.status_code, 200)


class ReaderRenderHangTests(unittest.TestCase):
    """Found by C007: a line that starts like a rule ("***x***", "--- note", "___x") but is not one was taken by no
    branch of render_markdown, so the loop never advanced and the request hung forever. Run in a thread with a timeout
    so a regression fails the test instead of freezing the suite."""

    def run_with_timeout(self, text, seconds=10):
        import threading
        out = {}

        def work():
            out["html"] = core.render_markdown(text)
        th = threading.Thread(target=work, daemon=True)
        th.start()
        th.join(seconds)
        self.assertFalse(th.is_alive(), "render_markdown did not finish: infinite loop on %r" % text)
        return out["html"]

    def test_rule_lookalike_lines_terminate_and_keep_their_text(self):
        for line in ("***bold*** start of a line", "--- a note after dashes", "___x", "---a", "***"):
            html = self.run_with_timeout("before\n" + line + "\nafter")
            self.assertIn("before", html)
            self.assertIn("after", html)
        self.assertIn("--- a note after dashes", self.run_with_timeout("--- a note after dashes"))

    def test_real_rules_are_still_rules(self):
        self.assertIn('<hr class="reader-hr"/>', self.run_with_timeout("a\n\n---\n\nb"))


if __name__ == "__main__":
    unittest.main()
