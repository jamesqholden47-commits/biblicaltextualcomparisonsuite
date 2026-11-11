"""
Unit tests for Pope Leo XIV Tracker module and routes.
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
from modules import pope_leo_core as core


class TestPopeLeoTracker(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_core_feed_structure(self):
        feed = core.get_feed()
        self.assertIn("pontiff", feed)
        self.assertEqual(feed["pontiff"]["name"], "Pope Leo XIV")
        self.assertIn("Robert Francis Prevost", feed["pontiff"]["secular_name"])
        self.assertEqual(feed["current_date"], "2026-10-04")
        self.assertIn("today_events", feed)
        self.assertTrue(len(feed["today_events"]) >= 2)

    def test_today_angelus_and_processions(self):
        feed = core.get_feed()
        angelus = next((e for e in feed["today_events"] if e["id"] == "angelus-20261004"), None)
        self.assertIsNotNone(angelus)
        self.assertIn("Matthew 21:33–43", angelus["readings"]["gospel"])
        self.assertIn("Saint Francis of Assisi", angelus["franciscan_centenary"])
        processions = angelus["processions_and_pilgrimages"]
        self.assertTrue(len(processions) >= 4)
        proc_names = [p["name"] for p in processions]
        self.assertTrue(any("Our Lady of Revelation" in n for n in proc_names))
        self.assertTrue(any("Pompeii" in n for n in proc_names))
        self.assertTrue(any("Via Francigena" in n for n in proc_names))

    def test_gendarmerie_mass_homily(self):
        feed = core.get_feed()
        mass = next((e for e in feed["today_events"] if e["id"] == "mass-20261003-gendarmeria"), None)
        self.assertIsNotNone(mass)
        self.assertIn("Isaiah 5:1–7", mass["readings"]["reading_1"])
        self.assertIn("Philippians 4:6–8", mass["readings"]["reading_2"])
        self.assertIn("custodire il cuore", mass["full_text_it"])
        self.assertIn("guard your heart", mass["full_text_en_translation"].lower())

    def test_api_feed_endpoint(self):
        resp = self.client.get("/api/pope-leo/feed")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["pontiff"]["name"], "Pope Leo XIV")

    def test_api_today_endpoint(self):
        resp = self.client.get("/api/pope-leo/today")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["date"], "2026-10-04")
        self.assertTrue(len(data["events"]) >= 2)

    def test_api_processions_endpoint(self):
        resp = self.client.get("/api/pope-leo/processions")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 4)

    def test_api_homilies_filter(self):
        resp = self.client.get("/api/pope-leo/homilies?query=France")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 1)
        self.assertTrue(any("France" in h["title"] for h in data["homilies"]))

    def test_standalone_ui_removed(self):
        # As requested by user: standalone fullscreen view removed in favor of integrated worksuite module
        resp = self.client.get("/pope-leo-tracker")
        self.assertEqual(resp.status_code, 404)

    def test_api_videos_endpoint(self):
        resp = self.client.get("/api/pope-leo/videos")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("live_channels", data)
        self.assertIn("today_replays", data)
        self.assertIn("backup_urls", data)
        self.assertTrue(len(data["live_channels"]) >= 3)
        self.assertTrue(len(data["backup_urls"]) >= 10)
        self.assertIn("troubleshooting_advisory", data)

    def test_api_backups_endpoint(self):
        resp = self.client.get("/api/pope-leo/backups")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("count", data)
        self.assertTrue(data["count"] >= 10)
        self.assertIn("backups", data)
        urls = [b["url"] for b in data["backups"]]
        self.assertTrue(any("@VaticanNewsEN/live" in u for u in urls))
        self.assertTrue(any("@VaticanNewsIT/live" in u for u in urls))
        self.assertTrue(any("vaticannews.va/en/epg.html" in u for u in urls))
        self.assertTrue(any("radio.vaticannews.va/stream-en" in u for u in urls))
        self.assertTrue(any("@EWTN/live" in u for u in urls))

    def test_api_documents_endpoint(self):
        resp = self.client.get("/api/pope-leo/documents")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 4)
        doc_titles = [d["title"] for d in data["documents"]]
        self.assertTrue(any("Magnifica Humanitas" in t for t in doc_titles))
        self.assertTrue(any("Mater Populi Fidelis" in t for t in doc_titles))

    def test_api_moves_endpoint(self):
        resp = self.client.get("/api/pope-leo/moves")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 4)

    def test_api_abraccio_endpoint(self):
        resp = self.client.get("/api/pope-leo/abraccio")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["count"] >= 3)

    def test_api_analytics_endpoint(self):
        resp = self.client.get("/api/pope-leo/analytics")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("levels", data)
        self.assertEqual(len(data["levels"]), 4)
        self.assertIn("emerging_doctrinal_patterns", data)
        self.assertTrue(len(data["emerging_doctrinal_patterns"]) >= 2)

    def test_dynamic_liturgical_day_october_15(self):
        import datetime
        lit = core.get_live_liturgical_day(datetime.date(2026, 10, 15))
        self.assertEqual(lit["date"], "2026-10-15")
        self.assertEqual(lit["liturgical_color"], "White")
        self.assertEqual(lit["rank"], "Memorial")
        self.assertEqual(lit["season"], "Ordinary Time")
        self.assertEqual(lit["week_of_season"], 28)
        self.assertIn("St. Teresa of Jesus", lit["liturgical_day_name"])
        self.assertEqual(lit["weekday_cycle"], "Year II")
        self.assertEqual(lit["sunday_cycle"], "Year A")

    def test_feed_includes_live_liturgical_and_youtube(self):
        feed = core.get_feed()
        self.assertIn("liturgical_today_live", feed)
        self.assertIn("current_date_display", feed)
        self.assertIn("latest_youtube_video_id", feed)
        self.assertTrue(len(feed["latest_youtube_video_id"]) > 5)
        self.assertIn("vatican_status", feed)


if __name__ == "__main__":
    unittest.main()


