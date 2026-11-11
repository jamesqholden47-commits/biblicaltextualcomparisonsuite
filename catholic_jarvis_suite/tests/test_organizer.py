"""Organizer: the bucket rules and the book-citation finder, each tested in both directions (Claude GUI, 2026-10-14)."""
import os
import sys
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)
sys.path.insert(0, os.path.join(APP_DIR, "tools"))

from modules import organizer_core as O   # noqa: E402
import leads_harvest as L                 # noqa: E402

H = O.HOME


def c(rel, ext=None):
    ext = ext or os.path.splitext(rel)[1].lower()
    return O.classify(os.path.join(H, rel), ext)


class TestBuckets(unittest.TestCase):
    def test_vault_and_archives_first(self):
        self.assertEqual(c(r"aa1\11_Philosophical_Theology\note.md"), ("Vault & archives", "AA1 Obsidian vault (the live one)"))
        self.assertEqual(c(r"aa1\98_Archives\x.md")[1], "AA1 vault: 98_Archives")
        self.assertEqual(c(r"CLONE_FOR_SORTING_2026-10-08__COPIES_NOT_ORIGINALS\aa1\x.md")[0], "Vault & archives")
        self.assertEqual(c(r"takeout-20260314T073316Z-3-001\Takeout\x.html")[1], "AI history: Google Takeout")
        # an archive folder inside the project is an archive, not project content
        self.assertEqual(c(r"DXM\Clippings\_PROJECT_HistoryProvesCatholicism\07_ARCHIVE_OLD_PROCESS\old.md")[0], "Vault & archives")
        # a book inside the vault stays with the vault
        self.assertEqual(c(r"aa1\attachments\book.pdf")[0], "Vault & archives")

    def test_books_by_subject(self):
        self.assertEqual(c(r"PDFS\Pope Peter -- Heschemeyer.pdf"), ("Books", "Papacy and church history"))
        self.assertEqual(c(r"Downloads\Basics of Biblical Greek Grammar.pdf")[1], "Languages and grammar")
        self.assertEqual(c(r"PDFS\The Gospel of John commentary.pdf")[1], "Bible and translations")
        self.assertEqual(c(r"PDFS\Untitled scan 0042.pdf")[1], "Other books")
        self.assertEqual(c(r"Research_Imports\PDFs_and_Documents\My Resume (1).pdf")[1], "Personal papers (forms, letters, resume)")
        self.assertEqual(c(r"Default Folder\How to add DuckDuckGo - Tor Stack Exchange.pdf")[1], "Articles and saved pages (PDF)")
        # a source PDF inside the project stays with the project
        self.assertEqual(c(r"DXM\Clippings\_PROJECT_HistoryProvesCatholicism\03_RESEARCH_DOSSIERS\_sources\x.pdf")[0], "Dissertation project")
        # the assets of a saved page are not "your code"
        self.assertEqual(c(r"Ephesians 2 - Google Search_files\app.js")[0], "Saved web pages")

    def test_project_folders(self):
        self.assertEqual(c(r"DXM\Clippings\_PROJECT_HistoryProvesCatholicism\03_RESEARCH_DOSSIERS\D.md"),
                         ("Dissertation project", "Research dossiers"))
        self.assertEqual(c(r"DXM\Clippings\_PROJECT_HistoryProvesCatholicism\09_APPS_CATHOLICJARVIS\x\app.py")[1], "Work suite (code)")
        self.assertEqual(c(r"DXM\Clippings\other_note.md"), ("Vault & archives", "DXM parent vault (around the project)"))

    def test_other_projects_web_code_loose(self):
        self.assertEqual(c(r"Mexico_Protestantism_Study\05_READERS_EDITION\x.md"), ("Other projects", "Mexico Protestantism study"))
        self.assertEqual(c(r"warriors-public-site\index.html")[1], "Warriors business sites")
        self.assertEqual(c(r"Hermes Trismegistus - Wikipedia.html")[0], "Saved web pages")
        self.assertEqual(c(r"Downloads\tool.py"), ("Code elsewhere", "Downloads"))
        self.assertEqual(c(r"Desktop\random thought.md"), ("Loose notes", "Desktop"))
        self.assertEqual(c(r"NOTES\1 Timothy 315.txt"), ("Loose notes", "NOTES"))


class TestProgramsAndFiling(unittest.TestCase):
    def test_program_files_bucket(self):
        p = os.path.join(H, r"Documents\SOLIDWORKS Downloads\SOLIDWORKS 2024 SP04\lang\english\readme.txt")
        self.assertEqual(O.classify(p, ".txt", os.path.join(H, r"Documents\SOLIDWORKS Downloads\SOLIDWORKS 2024 SP04"))[0], O.PROGRAM_BUCKET)
        self.assertEqual(O.classify(p, ".txt", "")[0], "Loose notes")          # without the inventory's flag it is a note
        # the vault stays the vault even if a program flag were set
        self.assertEqual(O.classify(os.path.join(H, r"aa1\x.md"), ".md", os.path.join(H, "aa1"))[0], "Vault & archives")

    def test_virtual_filing_round_trip(self):
        import tempfile
        real = O.PLACEMENTS
        with tempfile.TemporaryDirectory() as d:
            O.PLACEMENTS = os.path.join(d, "p.json")
            try:
                self.assertEqual(O.place(r"C:\x\a.md", folder=r"Career\\Schools/ "), {"folder": "Career/Schools"})
                O.place(r"C:\x\b.md", folder="Career")
                O.place(r"C:\x\b.md", hidden=True)
                self.assertEqual(O.my_folders(), {"Career": 2, "Career/Schools": 1})
                self.assertEqual(O.placements()[r"C:\x\b.md"], {"folder": "Career", "hidden": True})
                self.assertIsNone(O.place(r"C:\x\a.md", folder=""))               # taking it out removes the entry
                self.assertEqual(O.place(r"C:\x\c.md", folder="../.."), None)     # no climbing out of the folder tree
            finally:
                O.PLACEMENTS = real

    def test_atomic_replace(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "src.txt")
            dst = os.path.join(d, "dst.txt")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("hello")
            O._atomic_replace(src, dst)
            self.assertFalse(os.path.exists(src))
            with open(dst, "r", encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "hello")


class TestBookFinder(unittest.TestCase):
    def titles(self, s):
        return [t for t, a, d, p in L.find_books(s)]

    def test_citation_shapes(self):
        self.assertIn("Paul and the Gift", self.titles("see John Barclay, *Paul and the Gift* (Eerdmans, 2015), ch. 3"))
        self.assertIn("The Deliverance of God", self.titles("*The Deliverance of God* by Douglas Campbell argues"))
        self.assertIn("Paul and Palestinian Judaism", self.titles("Sanders, *Paul and Palestinian Judaism* changed the field"))

    def test_not_every_italic_is_a_book(self):
        self.assertEqual(self.titles("this is *not* what Paul *meant* by *sola fide* at all"), [])
        self.assertEqual(self.titles("the word *pistis* means trust"), [])

    def test_owned_match(self):
        idx = [(set("pope peter defending the churchs most distinctive doctrine heschmeyer".split()), "x.pdf")]
        self.assertEqual(L.owned_match("Pope Peter: Defending the Church's Most Distinctive Doctrine", idx), "x.pdf")
        self.assertEqual(L.owned_match("The Deliverance of God", idx), "")

    def test_career_themes(self):
        self.assertIn("Military and veterans' benefits", L.career_theme("can i use my GI Bill for a seminary degree"))
        self.assertIn("School and degrees", L.career_theme("can i use my GI Bill for a seminary degree"))
        self.assertEqual(L.career_theme("what does pistis mean in romans 3"), [])


if __name__ == "__main__":
    unittest.main()
