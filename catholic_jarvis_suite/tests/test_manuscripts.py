"""
test_manuscripts.py - Unit and Integration Tests for CatholicJarvis Manuscript Suite
Path: 09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/tests/test_manuscripts.py
Author: Antigravity Autonomous Academic Fleet
Date: 2026-10-09
"""

import os
import re
import sys
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from modules import manuscripts_core as mc  # noqa: E402


class TestManuscriptsCore(unittest.TestCase):
    def test_list_manuscripts(self):
        ms_list = mc.list_manuscripts()
        self.assertGreaterEqual(len(ms_list), 16)
        ids = [m["id"] for m in ms_list]
        self.assertIn("codex_vaticanus", ids)
        self.assertIn("codex_sinaiticus", ids)
        self.assertIn("papyrus_75", ids)
        self.assertIn("codex_alexandrinus", ids)
        self.assertIn("codex_ephraemi", ids)
        self.assertIn("codex_bezae", ids)
        self.assertIn("codex_washingtonianus", ids)
        self.assertIn("codex_claromontanus", ids)
        self.assertIn("papyrus_52", ids)
        self.assertIn("papyrus_46", ids)
        self.assertIn("papyrus_66", ids)
        self.assertIn("papyrus_45", ids)
        self.assertIn("codex_hierosolymitanus", ids)
        self.assertIn("papyrus_oxyrhynchus_840", ids)
        self.assertIn("great_isaiah_scroll", ids)
        self.assertIn("scroll_4qmmt", ids)

    def test_get_manuscript_details(self):
        vat = mc.get_manuscript("codex_vaticanus")
        self.assertEqual(vat["name"], "Codex Vaticanus")
        self.assertEqual(vat["siglum"], "B / 03 / Vat.gr.1209")
        self.assertIn("digi.vatlib.it", vat["iiif_manifest"])
        self.assertGreaterEqual(len(vat["folios"]), 2)

    def test_get_folio_and_morphological_alignment(self):
        folio_data = mc.get_folio("codex_vaticanus", "p1303_luke1")
        self.assertEqual(folio_data["manuscript_id"], "codex_vaticanus")
        fol = folio_data["folio"]
        self.assertEqual(fol["passage"], "Luke 1:1–4")
        self.assertGreaterEqual(len(fol["lines"]), 8)
        
        # Verify first-person singular 'ΚΑΜΟΙ' (κἀμοί) exists in the morphological alignment
        words = [w["word"] for w in fol.get("words_morph", [])]
        self.assertIn("ΚΑΜΟΙ", words)
        
        kamoi_item = next(w for w in fol["words_morph"] if w["word"] == "ΚΑΜΟΙ")
        self.assertIn("1st Sg", kamoi_item["parse"])
        self.assertIn("ME", kamoi_item["gloss"])

    def test_citation_generation(self):
        cite = mc.format_citation("codex_vaticanus", "p1303_luke1", style="sbl")
        self.assertIn("Codex Vaticanus", cite["sbl"])
        self.assertIn("Luke 1:1–4", cite["sbl"])
        self.assertIn("digi.vatlib.it", cite["sbl"])
        self.assertIn("xywh=", cite["iiif_anchor"])
        self.assertIn("@misc", cite["bibtex"])
        
        # Verify Logos / Verbum structured copy
        self.assertIn("logos_verbum", cite)
        self.assertIn("ref.ly/logosres", cite["logos_verbum"])
        self.assertIn("Latin Vulgate (Verbum Catholic Edition)", cite["logos_verbum"])
        self.assertIn("Quoniam quidem multi conati sunt", cite["logos_verbum"])
        self.assertIn("logosres:gntmorph", cite["logos_verbum"])
        self.assertIn("logosres:vulgataclem", cite["logos_verbum"])

    def test_search_manuscripts(self):
        hits_luke = mc.search_manuscripts("Luke 1")
        self.assertGreaterEqual(len(hits_luke), 1)
        self.assertEqual(hits_luke[0]["manuscript_id"], "codex_vaticanus")

        hits_clement = mc.search_manuscripts("Clement")
        self.assertGreaterEqual(len(hits_clement), 1)
        self.assertEqual(hits_clement[0]["manuscript_id"], "codex_alexandrinus")

        hits_eyewitness = mc.search_manuscripts("eyewitness")
        self.assertGreaterEqual(len(hits_eyewitness), 1)

        hits_p52 = mc.search_manuscripts("truth")
        self.assertGreaterEqual(len(hits_p52), 1)

        hits_isaiah = mc.search_manuscripts("Suffering Servant")
        self.assertGreaterEqual(len(hits_isaiah), 1)
        self.assertEqual(hits_isaiah[0]["manuscript_id"], "great_isaiah_scroll")

    def test_falsification_on_nonexistent_manuscript(self):
        with self.assertRaises(KeyError):
            mc.get_manuscript("nonexistent_codex_999")
        with self.assertRaises(KeyError):
            mc.get_folio("codex_vaticanus", "nonexistent_folio_999")


class TestManuscriptsDesignCompliance(unittest.TestCase):
    def test_no_hardcoded_hex_colours(self):
        js_path = os.path.join(APP_DIR, "static", "modules", "manuscripts.js")
        with open(js_path, encoding="utf-8") as f:
            content = f.read()
        
        # Remove comments before regex search
        cleaned = re.sub(r"/\*.*?\*/", "", content, flags=re.S)
        cleaned = re.sub(r"(?m)^\s*//.*$", "", cleaned)
        
        hex_pattern = re.compile(r"""(?<![\w&])(?<!href=")(?<!href=')#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])""")
        hits = hex_pattern.findall(cleaned)
        self.assertEqual(hits, [], f"Hardcoded hex colours found in manuscripts.js: {hits}")


if __name__ == "__main__":
    unittest.main()
