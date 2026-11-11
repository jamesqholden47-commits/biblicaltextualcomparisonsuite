"""
Unit tests for Vatican Intel, Religious Orders & Scholarly Journals Module.
"""

import unittest
from fastapi.testclient import TestClient
import os
import sys

# Ensure suite directory is in sys.path
SUITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SUITE_DIR not in sys.path:
    sys.path.insert(0, SUITE_DIR)

from app import app
from modules import vatican_culture_core as core


class TestVaticanCulture(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_core_overview_and_counts(self):
        data = core.get_culture_data()
        self.assertIn("orders", data)
        self.assertIn("journals", data)
        self.assertIn("curial_debates", data)
        self.assertIn("curial_bookshelf", data)
        self.assertTrue(len(data["orders"]) >= 6)
        self.assertTrue(len(data["journals"]) >= 10)

    def test_api_overview_endpoint(self):
        resp = self.client.get("/api/vatican-culture/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("counts", data)
        self.assertGreaterEqual(data["counts"]["orders"], 6)
        self.assertGreaterEqual(data["counts"]["journals"], 10)

    def test_api_orders_endpoint(self):
        resp = self.client.get("/api/vatican-culture/orders")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 6)
        order_names = [o["name"] for o in data["orders"]]
        self.assertTrue(any("Jesuit" in n for n in order_names))
        self.assertTrue(any("Dominican" in n for n in order_names))
        self.assertTrue(any("Benedictine" in n for n in order_names))
        self.assertTrue(any("Bollandist" in n for n in order_names))
        self.assertTrue(any("Augustinian" in n for n in order_names))
        self.assertTrue(any("Franciscan" in n for n in order_names))

    def test_api_orders_filter(self):
        resp = self.client.get("/api/vatican-culture/orders?query=Augustinian")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["count"], 1)
        self.assertTrue(any("Augustinian" in o["name"] for o in data["orders"]))

    def test_api_journals_endpoint(self):
        resp = self.client.get("/api/vatican-culture/journals")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 10)
        titles = [j["title"] for j in data["journals"]]
        self.assertTrue(any("Civiltà Cattolica" in t for t in titles))
        self.assertTrue(any("Revue Thomiste" in t for t in titles))
        self.assertTrue(any("Revue Bénédictine" in t for t in titles))
        self.assertTrue(any("Analecta Bollandiana" in t for t in titles))
        self.assertTrue(any("Augustinianum" in t for t in titles))
        self.assertTrue(any("Acta Apostolicae Sedis" in t for t in titles))

    def test_api_journals_filter_by_order(self):
        resp = self.client.get("/api/vatican-culture/journals?order=bollandist")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["count"], 1)
        self.assertTrue(any("Analecta Bollandiana" in j["title"] for j in data["journals"]))

    def test_api_bookshelf_endpoint(self):
        resp = self.client.get("/api/vatican-culture/bookshelf")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 5)
        titles = [b["title"] for b in data["bookshelf"]]
        self.assertTrue(any("Lake Como" in t for t in titles))
        self.assertTrue(any("Principles of Catholic Theology" in t for t in titles))
        self.assertTrue(any("True and False Reform" in t for t in titles))

    def test_api_debates_endpoint(self):
        resp = self.client.get("/api/vatican-culture/debates")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 5)
        debates = [d["title"] for d in data["debates"]]
        self.assertTrue(any("Artificial Intelligence" in d for d in debates))
        self.assertTrue(any("Primacy & Synodality" in d for d in debates))
        self.assertTrue(any("Liturgical Pacification" in d for d in debates))
        self.assertTrue(any("Marian Titles" in d for d in debates))

    def test_api_feed_endpoint(self):
        resp = self.client.get("/api/vatican-culture/feed")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 5)


if __name__ == "__main__":
    unittest.main()
