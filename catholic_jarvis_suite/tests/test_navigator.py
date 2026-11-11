"""
tests/test_navigator.py — Unit tests for File Genealogy & Treemap Navigator
CatholicJarvis Master Work Suite
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app
from modules import navigator_core as core


class TestNavigatorCore(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_classify_file(self):
        cat, tier = core.classify_file(r"01_MASTER_DISSERTATION\Chapter_01.md")
        self.assertEqual(cat, "master")
        self.assertEqual(tier, 3)

        cat, tier = core.classify_file(r"10_VOLUMES\Volume_1\Chapter_02.md")
        self.assertEqual(cat, "volumes")
        self.assertEqual(tier, 3)

        cat, tier = core.classify_file(r"03_RESEARCH_DOSSIERS\Forensic_Justification.md")
        self.assertEqual(cat, "dossiers")
        self.assertEqual(tier, 1)

        cat, tier = core.classify_file(r"05_DRAFTS\Monograph_On_Incense.md")
        self.assertEqual(cat, "drafts")
        self.assertEqual(tier, 2)

        cat, tier = core.classify_file(r"tools\audit_citations.py")
        self.assertEqual(cat, "scripts")
        self.assertEqual(tier, 4)

        cat, tier = core.classify_file(r"C:\Users\Elation\PDFS\Early_Church_Fathers.pdf")
        self.assertEqual(cat, "books")
        self.assertEqual(tier, 0)

    def test_extract_links_and_citations(self):
        text = """
        As established in [[Forensic_Justification_Extract]] and detailed in [Chapter 1](01_MASTER_DISSERTATION/Chapter_01.md),
        the patristic evidence cites Qumran_Melchizedek_Dossier.md directly.
        """
        targets = core.extract_links_and_citations(text)
        self.assertIn("Forensic_Justification_Extract", targets)
        self.assertIn("Chapter_01.md", targets)
        self.assertIn("Qumran_Melchizedek_Dossier.md", targets)

    def test_build_treemap_structure(self):
        mock_data = {
            "nodes": {
                "n1": {
                    "id": "n1",
                    "name": "Chapter_01.md",
                    "path": r"01_MASTER_DISSERTATION\Chapter_01.md",
                    "category": "master",
                    "academic_tier": 3,
                    "author_type": "hybrid",
                    "size": 50000,
                    "line_count": 1200,
                    "mtime": 1728000000,
                    "ctime": 1728000000,
                    "atime": 1728000000,
                    "mtime_iso": "2026-10-01 12:00:00",
                    "ctime_iso": "2026-10-01 12:00:00",
                    "atime_iso": "2026-10-01 12:00:00",
                    "temporal_month": "2026-10",
                    "color_var": "var(--accent-gold)",
                    "badge": "Master",
                    "snippet": "Test"
                },
                "n2": {
                    "id": "n2",
                    "name": "Justification_Dossier.md",
                    "path": r"03_RESEARCH_DOSSIERS\Justification_Dossier.md",
                    "category": "dossiers",
                    "academic_tier": 1,
                    "author_type": "ai_authored",
                    "size": 30000,
                    "line_count": 800,
                    "mtime": 1727000000,
                    "ctime": 1727000000,
                    "atime": 1727000000,
                    "mtime_iso": "2026-09-20 12:00:00",
                    "ctime_iso": "2026-09-20 12:00:00",
                    "atime_iso": "2026-09-20 12:00:00",
                    "temporal_month": "2026-09",
                    "color_var": "var(--accent-green)",
                    "badge": "Dossier",
                    "snippet": "Test 2"
                }
            },
            "edges": []
        }
        tree = core.build_treemap(mock_data, sort_by="mtime", group_by="category")
        self.assertEqual(tree["name"], "Corpus Knowledge Base")
        self.assertTrue(len(tree["children"]) >= 1)

    def test_api_endpoints(self):
        resp = self.client.get("/api/navigator/status")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("status", resp.json())

        resp = self.client.get("/api/navigator/tree")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("children", data)

        resp = self.client.get("/api/navigator/genealogy")
        self.assertEqual(resp.status_code, 200)
        gen = resp.json()
        self.assertIn("nodes", gen)
        self.assertIn("edges", gen)

    def test_count_citations(self):
        sample = """
        Patristic testimony includes PG 28, col. 45 and PL 33, col. 12.
        Furthermore, Denzinger records DH 3001 and DH 1500.
        As noted in footnote [^1] and discussed in [^patristic_witness_2026].
        """
        citations = core.count_citations(sample)
        self.assertEqual(citations, 6)

    def test_infrastructure_tagging_and_treemap_filters(self):
        mock_data = {
            "nodes": {
                "n_scholarly": {
                    "id": "n_scholarly",
                    "name": "Chapter_01.md",
                    "path": r"01_MASTER_DISSERTATION\Chapter_01.md",
                    "category": "master",
                    "academic_tier": 3,
                    "author_type": "hybrid",
                    "size": 50000,
                    "line_count": 1200,
                    "citations": 45,
                    "is_infrastructure": False,
                    "mtime": 1728000000,
                    "temporal_month": "2026-10",
                    "color_var": "var(--accent-gold)",
                    "badge": "Master"
                },
                "n_infra": {
                    "id": "n_infra",
                    "name": "build_script.py",
                    "path": r"tools\build_script.py",
                    "category": "scripts",
                    "academic_tier": 4,
                    "author_type": "ai_authored",
                    "size": 15000,
                    "line_count": 300,
                    "citations": 0,
                    "is_infrastructure": True,
                    "mtime": 1725000000,
                    "temporal_month": "2026-08",
                    "color_var": "var(--text-muted)",
                    "badge": "Script"
                }
            },
            "edges": []
        }
        # Treemap with citations size_metric
        tree_cit = core.build_treemap(mock_data, size_metric="citations")
        all_children = []
        for g in tree_cit["children"]:
            all_children.extend(g["children"])
        scholarly = next(c for c in all_children if c["id"] == "n_scholarly")
        self.assertEqual(scholarly["value"], 45)

        # Treemap with exclude_infrastructure
        tree_no_infra = core.build_treemap(mock_data, exclude_infrastructure=True)
        no_infra_children = []
        for g in tree_no_infra["children"]:
            no_infra_children.extend(g["children"])
        self.assertEqual(len(no_infra_children), 1)
        self.assertEqual(no_infra_children[0]["id"], "n_scholarly")

        # Chrono filter
        tree_chrono = core.build_treemap(mock_data, chrono_max_month="2026-09")
        chrono_children = []
        for g in tree_chrono["children"]:
            chrono_children.extend(g["children"])
        self.assertEqual(len(chrono_children), 1)
        self.assertEqual(chrono_children[0]["id"], "n_infra")


if __name__ == "__main__":
    unittest.main()

