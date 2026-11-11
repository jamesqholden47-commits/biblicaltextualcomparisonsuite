"""
Files viewer tests (Phase 1, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).

Acceptance tests from the plan, each able to fail:
  - a path outside the roots is refused, including through a junction that points outside;
  - viewing 50 random vault notes changes no modification time and no hash;
  - a [[link]] to a renamed note shows as unresolved instead of pointing at the wrong note;
  - a 5 MB file opens in parts, each within 2 seconds;
plus renderer safety (no raw HTML or javascript: links get through), the raw endpoint's sandbox header,
Obsidian features, diff counts, notes kept out of the file, and backlinks from the link index.
Every test points files_core at temporary roots and a temporary state file, except the read-only vault sample.
"""
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from modules import files_core as core, files_md  # noqa: E402

VAULT = r"C:\Users\Elation\aa1"


def _sha(p):
    with open(p, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class TempRoots(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="jarvis_files_")
        self.root = os.path.join(self.tmp, "vault")
        self.outside = os.path.join(self.tmp, "outside")
        os.makedirs(os.path.join(self.root, "sub"))
        os.makedirs(self.outside)
        self._saved = (core.ROOTS_FILE, core.STATE_FILE, core.LINKS_FILE)
        core.ROOTS_FILE = os.path.join(self.tmp, "roots.json")
        core.STATE_FILE = os.path.join(self.tmp, "state.json")
        core.LINKS_FILE = os.path.join(self.tmp, "links.json")
        with open(core.ROOTS_FILE, "w", encoding="utf-8") as fh:
            json.dump([[self.root, "Test vault"]], fh)
        core._links.update(inverse=None, mtime=0, state="idle")
        core.names(force=True)

    def tearDown(self):
        core.ROOTS_FILE, core.STATE_FILE, core.LINKS_FILE = self._saved
        core._links.update(inverse=None, mtime=0, state="idle")
        core._names["built"] = 0          # the real roots are re-walked lazily, on next use
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, text):
        p = os.path.normpath(os.path.join(self.root, rel))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        return p


class TestBoundary(TempRoots):
    def test_outside_refused(self):
        secret = os.path.join(self.outside, "secret.md")
        with open(secret, "w", encoding="utf-8") as fh:
            fh.write("# secret")
        with self.assertRaises(core.Forbidden):
            core.view(secret)
        with self.assertRaises(core.Forbidden):
            core.view(os.path.join(self.root, "..", "outside", "secret.md"))
        with self.assertRaises(core.Forbidden):
            core.list_dir(self.outside)
        # falsification: the same kind of file inside the root opens
        inside = self.write("ok.md", "# fine")
        self.assertEqual(core.view(inside, record=False)["type"], "markdown")

    def test_junction_escape_refused(self):
        link = os.path.join(self.root, "escape")
        r = subprocess.run(["cmd", "/c", "mklink", "/J", link, self.outside], capture_output=True)
        if r.returncode != 0 or not os.path.isdir(link):
            self.skipTest("could not create a junction here")
        with open(os.path.join(self.outside, "s.md"), "w", encoding="utf-8") as fh:
            fh.write("x")
        try:
            with self.assertRaises(core.Forbidden):
                core.view(os.path.join(link, "s.md"))
        finally:
            os.rmdir(link)        # removes the junction itself, never its target


class TestLinks(TempRoots):
    def test_renamed_note_is_unresolved_not_misdirected(self):
        a = self.write("a.md", "See [[b]] and [[b|the bee note]] and [[c]].")
        self.write("sub/b.md", "# B")
        core._names["built"] = time.time() - 1000      # index predates the new note: the miss must trigger a refresh
        html = core.view(a, record=False)["html"]
        self.assertEqual(html.count('data-path="' + os.path.join(self.root, "sub", "b.md")), 2)
        self.assertIn("No note named c", html)
        os.rename(os.path.join(self.root, "sub", "b.md"), os.path.join(self.root, "sub", "b2.md"))
        core._names["built"] = time.time() - 1000
        html = core.view(a, record=False)["html"]
        self.assertNotIn("data-path=", html)
        self.assertEqual(html.count("md-unresolved"), 3)

    def test_nearest_note_wins_for_duplicate_names(self):
        a = self.write("sub/a.md", "[[dup]]")
        self.write("dup.md", "top")
        near = self.write("sub/dup.md", "near")
        core.names(force=True)
        html = core.view(a, record=False)["html"]
        self.assertIn('data-path="' + near, html)

    def test_backlinks_from_index(self):
        self.write("hub.md", "# Hub")
        self.write("one.md", "links to [[hub]]")
        self.write("sub/two.md", "and ![[hub#Section|alias]]")
        self.write("three.md", "no link here")
        core._build_links_worker()
        b = core.backlinks(os.path.join(self.root, "hub.md"))
        self.assertEqual(sorted(x["name"] for x in b["backlinks"]), ["one", "two"])
        # incremental: a changed note is re-read, an unchanged one is not
        time.sleep(1.1)
        self.write("three.md", "now [[hub]]")
        core._build_links_worker()
        with open(core.LINKS_FILE, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["reread"], 1)
        self.assertEqual(core.backlinks(os.path.join(self.root, "hub.md"))["total"], 3)


class TestLargeAndTypes(TempRoots):
    def test_five_mb_file_in_parts_fast(self):
        chunk = "\n".join(f"Paragraph {i} " + "word " * 60 for i in range(40))
        text = "\n\n".join(f"## Section {k}\n\n{chunk}" for k in range(400))
        p = self.write("big.md", text)
        self.assertGreater(os.path.getsize(p), 5_000_000)
        t = time.time()
        first = core.view(p, 0, record=False)
        self.assertLess(time.time() - t, 2.0)
        self.assertGreater(first["part_count"], 1)
        t = time.time()
        last = core.view(p, first["part_count"] - 1, record=False)
        self.assertLess(time.time() - t, 2.0)
        self.assertIn("Section 399", last["html"])
        with self.assertRaises(IndexError):
            core.view(p, first["part_count"], record=False)

    def test_docx_and_code(self):
        import zipfile
        p = os.path.join(self.root, "d.docx")
        xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
               '<w:p><w:r><w:t>First para</w:t></w:r></w:p><w:p><w:r><w:t>Second</w:t></w:r></w:p></w:body></w:document>')
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("word/document.xml", xml)
        v = core.view(p, record=False)
        self.assertIn("First para", v["html"])
        self.assertIn("Second", v["html"])
        c = self.write("x.py", "print('<b>hi</b>')\n")
        v = core.view(c, record=False)
        self.assertEqual(v["type"], "code")
        self.assertEqual(v["text"], "print('<b>hi</b>')\n")

    def test_notes_never_touch_the_file(self):
        p = self.write("n.md", "# note")
        h, m = _sha(p), os.path.getmtime(p)
        core.add_note(p, "my margin note")
        notes = core.get_notes(p)
        self.assertEqual(len(notes), 1)
        core.delete_note(p, notes[0]["id"])
        self.assertEqual(core.get_notes(p), [])
        self.assertEqual((_sha(p), os.path.getmtime(p)), (h, m))

    def test_diff_counts(self):
        a = self.write("v1.md", "\n".join(["same"] * 20 + ["old line"] + ["same"] * 20))
        b = self.write("v2.md", "\n".join(["same"] * 20 + ["new line", "extra"] + ["same"] * 20))
        d = core.diff(a, b)
        self.assertEqual((d["changed_a"], d["changed_b"]), (1, 2))
        self.assertTrue(any(r["op"] == "fold" for r in d["rows"]))
        same = core.diff(a, a)
        self.assertEqual((same["changed_a"], same["changed_b"], same["similarity"]), (0, 0, 1.0))


class TestRendererSafety(unittest.TestCase):
    def test_no_html_or_script_gets_through(self):
        evil = ('<script>alert(1)</script>\n\n[x](javascript:alert(1)) <img src=x onerror=alert(1)>\n\n'
                '| a | b |\n|---|---|\n| <b>c</b> | `<i>` |\n\n> [!note] <script>t</script>\n> body')
        h = files_md.render(evil)["html"]
        self.assertNotIn("<script", h)
        self.assertNotIn("<img src=x", h)
        self.assertNotIn('href="javascript', h)
        self.assertIn("&lt;script&gt;", h)

    def test_obsidian_features(self):
        md = ("---\ntitle: T\ntags: [mary, saints]\n---\n# Head\n\n> [!warning]- Folded\n> inside\n\n- [ ] todo\n- [x] done\n"
              "  - nested\n\n| A | B |\n|:--|--:|\n| 1 | 2 |\n\n```py\nx = 1 < 2\n```\n\n==hi== ~~old~~ #topic [V] [S:mem]")
        r = files_md.render(md)
        h = r["html"]
        self.assertEqual(r["frontmatter"]["title"], "T")
        self.assertEqual(sorted(r["tags"]), ["mary", "saints", "topic"])
        self.assertIn('<details class="md-callout md-callout-warning">', h)
        self.assertEqual(h.count('type="checkbox"'), 2)
        self.assertIn(" checked", h)
        self.assertIn('style="text-align:right"', h)
        self.assertIn("x = 1 &lt; 2", h)
        self.assertIn('<mark class="md-mark">hi</mark>', h)
        self.assertIn('<span class="j-tag v"', h)
        self.assertIn('<span class="j-tag s"', h)
        self.assertEqual(r["headings"][0]["id"], "head")

    def test_wiki_targets(self):
        self.assertEqual(files_md.wiki_targets("[[A b|x]] ![[c.md#h]] [[folder/D]]"), ["a b", "c", "d"])


class TestRawHeader(TempRoots):
    def test_html_served_sandboxed(self):
        from fastapi.testclient import TestClient
        import app as app_mod
        p = self.write("page.html", "<script>alert(1)</script>")
        r = TestClient(app_mod.app).get("/api/files/raw", params={"path": p})
        self.assertEqual(r.status_code, 200)
        self.assertIn("sandbox", r.headers.get("content-security-policy", ""))
        self.assertEqual(r.headers.get("x-content-type-options"), "nosniff")
        r = TestClient(app_mod.app).get("/api/files/raw", params={"path": r"C:\Windows\win.ini"})
        self.assertEqual(r.status_code, 403)


class TestColorCodedTree(TempRoots):
    def test_classify_role_all_roles(self):
        self.assertEqual(core.classify_role(r"C:\proj\01_MASTER_DISSERTATION\ch1.md"), "master")
        self.assertEqual(core.classify_role(r"C:\proj\03_RESEARCH_DOSSIERS\Papacy.md"), "subject")
        self.assertEqual(core.classify_role(r"C:\proj\06_SOURCE_MATERIAL\doc.pdf"), "source")
        self.assertEqual(core.classify_role(r"C:\PDFS\Sanders.pdf"), "source")
        self.assertEqual(core.classify_role(r"C:\proj\05_DRAFTS\draft.md"), "draft")
        self.assertEqual(core.classify_role(r"C:\proj\07_ARCHIVE_OLD_PROCESS\old.md"), "archive")
        self.assertEqual(core.classify_role(r"C:\proj\notes\test.bak"), "archive")
        self.assertEqual(core.classify_role(r"C:\proj\02_CONTROL_AND_STATE\task.md"), "infra")
        self.assertEqual(core.classify_role(r"C:\proj\09_APPS_CATHOLICJARVIS\app.py"), "infra")
        self.assertEqual(core.classify_role(r"C:\proj\script.py"), "infra")

    def test_list_dir_and_find_include_roles(self):
        self.write("sub/a.md", "# A")
        self.write("sub/tool.py", "print(1)")
        core.names(force=True)
        res = core.list_dir(os.path.join(self.root, "sub"))
        self.assertTrue(any(f["name"] == "tool.py" and f["role"] == "infra" and "role_label" in f for f in res["files"]))
        fres = core.find("tool")
        self.assertTrue(any(f["name"] == "tool.py" and f["role"] == "infra" and "status_badge" in f for f in fres["files"]))
        r_list = core.roots()
        self.assertTrue(all("role" in r and "role_label" in r and "status_badge" in r for r in r_list))


@unittest.skipUnless(os.path.isdir(VAULT), "AA1 vault not on this machine")
class TestVaultReadOnly(unittest.TestCase):
    def test_fifty_random_notes_unchanged(self):
        saved = core.STATE_FILE
        tmp = tempfile.mkdtemp(prefix="jarvis_files_state_")
        core.STATE_FILE = os.path.join(tmp, "state.json")
        try:
            notes = []
            for dp, dns, fns in os.walk(VAULT):
                dns[:] = [d for d in dns if not d.startswith(".")]
                notes += [os.path.join(dp, f) for f in fns if f.endswith(".md")]
                if len(notes) > 5000:
                    break
            sample = random.Random(20261007).sample(notes, 50)
            before = {p: (_sha(p), os.path.getmtime(p), os.path.getsize(p)) for p in sample}
            for p in sample:
                core.view(p)
                core.where(p)
            after = {p: (_sha(p), os.path.getmtime(p), os.path.getsize(p)) for p in sample}
            self.assertEqual(before, after)
        finally:
            core.STATE_FILE = saved
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
