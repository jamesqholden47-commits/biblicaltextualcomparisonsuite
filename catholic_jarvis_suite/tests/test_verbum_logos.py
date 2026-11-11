"""
tests/test_verbum_logos.py — Unit and Integration Tests for Verbum & Logos Catholic Study Suite
Part of CatholicJarvis Master Work Suite.
"""

import unittest
from fastapi.testclient import TestClient

from app import app
from modules.verbum_logos_core import (
    get_passage_data,
    get_interlinear_data,
    get_passage_guide,
    get_text_comparison,
    list_available_presets,
    export_clipping,
    PASSAGE_DATABASE
)


class TestVerbumLogosCore(unittest.TestCase):
    """Tests for Verbum core engine functions and corpora."""

    def test_presets_exist(self):
        presets = list_available_presets()
        self.assertGreaterEqual(len(presets), 4)
        refs = [p["id"] for p in presets]
        self.assertIn("luke_1_1_4", refs)
        self.assertIn("matthew_16_13_20", refs)
        self.assertIn("luke_1_26_38", refs)
        self.assertIn("1_clement_44", refs)

    def test_luke_passage_data(self):
        data = get_passage_data("luke_1_1_4")
        self.assertIsNotNone(data)
        self.assertEqual(data["reference"], "Luke 1:1-4")
        self.assertEqual(len(data["verses"]), 4)
        v1 = data["verses"][0]
        self.assertIn("Ἐπειδήπερ", v1["greek"])
        self.assertIn("Quoniam", v1["latin"])
        self.assertIn("Forasmuch", v1["douay"])
        self.assertIn("Inasmuch", v1["rsv2ce"])

    def test_petrine_primacy_data(self):
        data = get_passage_data("matthew_16_13_20")
        self.assertIsNotNone(data)
        self.assertEqual(data["reference"], "Matthew 16:13-20")
        # Find verse 18
        v18 = next(v for v in data["verses"] if v["num"] == 18)
        self.assertIn("Πέτρος", v18["greek"])
        self.assertIn("petram", v18["latin"])
        self.assertIn("Peter", v18["douay"])

    def test_interlinear_morphology(self):
        morph = get_interlinear_data("luke_1_1_4")
        self.assertNotIn("error", morph)
        self.assertIn("morphology", morph)
        self.assertGreater(len(morph["morphology"]), 0)
        
        # Check verse 3 morphology for kamoi
        v3_morph = next((m for m in morph["morphology"] if m["verse"] == 3), None)
        self.assertIsNotNone(v3_morph)
        tokens = v3_morph["tokens"]
        surfaces = [t["surface"] for t in tokens]
        self.assertIn("κἀμοὶ", surfaces)
        
        kamoi_tok = next(t for t in tokens if t["surface"] == "κἀμοὶ")
        self.assertEqual(kamoi_tok["pos"], "P-1DS")
        self.assertEqual(kamoi_tok["strong"], "G2504")

    def test_passage_guide(self):
        guide = get_passage_guide("luke_1_1_4")
        self.assertNotIn("error", guide)
        self.assertIn("catena_aurea", guide)
        self.assertGreater(len(guide["catena_aurea"]), 0)
        fathers = [c["father"] for c in guide["catena_aurea"]]
        self.assertIn("St. Thomas Aquinas", fathers)
        
        # Dogma check
        self.assertIn("magisterial_dogma", guide)
        anchors = [d["anchor"] for d in guide["magisterial_dogma"]]
        self.assertTrue(any("CCC" in a for a in anchors))
        
        # Manuscript check
        self.assertIn("manuscript_witnesses", guide)
        ms_ids = [m["id"] for m in guide["manuscript_witnesses"]]
        self.assertIn("codex_vaticanus", ms_ids)

    def test_text_comparison(self):
        comp = get_text_comparison("luke_1_26_38")
        self.assertNotIn("error", comp)
        self.assertEqual(len(comp["comparisons"]), 1)
        row = comp["comparisons"][0]
        self.assertIn("κεχαριτωμένη", row["greek"])
        self.assertIn("gratia plena", row["latin_vulgate"])
        self.assertGreater(len(row["doctrinal_terms"]), 0)
        self.assertTrue(any("kecharitōmenē" in dt["term"] for dt in row["doctrinal_terms"]))

    def test_clipping_export(self):
        md_clip = export_clipping("luke_1_1_4", format_type="markdown")
        self.assertIn("logosres:gntmorph", md_clip)
        self.assertIn("logosres:vulgataclem", md_clip)
        self.assertIn("Catena Aurea", md_clip)

        discord_clip = export_clipping("luke_1_1_4", format_type="discord")
        self.assertIn("CATHOLIC DISCORD FAST-STRIKE", discord_clip)
        self.assertIn("Codex Vaticanus", discord_clip)


class TestVerbumLogosAPI(unittest.TestCase):
    """Integration tests for FastAPI /api/verbum endpoints."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_api_presets(self):
        res = self.client.get("/api/verbum/presets")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("presets", data)
        self.assertGreaterEqual(len(data["presets"]), 4)

    def test_api_passage(self):
        res = self.client.get("/api/verbum/passage?ref=luke_1_1_4")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["reference"], "Luke 1:1-4")

    def test_api_interlinear(self):
        res = self.client.get("/api/verbum/interlinear?ref=luke_1_1_4")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("morphology", data)

    def test_api_guide(self):
        res = self.client.get("/api/verbum/guide?ref=matthew_16_13_20")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("catena_aurea", data)
        self.assertIn("magisterial_dogma", data)

    def test_api_compare(self):
        res = self.client.get("/api/verbum/compare?ref=luke_1_26_38")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("comparisons", data)

    def test_api_export(self):
        res = self.client.get("/api/verbum/export?ref=luke_1_1_4&fmt=markdown")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("clipping", data)
        self.assertIn("logosres", data["clipping"])


if __name__ == "__main__":
    unittest.main()
