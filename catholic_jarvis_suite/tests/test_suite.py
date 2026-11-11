"""
CatholicJarvis Master Work Suite - Test Suite
Verifies SM-2 algorithm, API routes, security guards, and static file mounting.
Standard library unittest + FastAPI TestClient.
"""

import os
import sys
import json
import unittest
from fastapi.testclient import TestClient

# Add app dir to path
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from app import app, load_anki_cards

class TestCatholicJarvisSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_static_mounting(self):
        """Verify defect #1 is fixed: /static/studio_frame.html must return 200, not 404."""
        resp = self.client.get("/static/studio_frame.html")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Auditory Research Studio", resp.text)

    def test_health_check(self):
        """Verify defect #2 is fixed: /api/health returns online status and index stats."""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["app"], "CatholicJarvis Master Work Suite")
        self.assertIn("uptime_seconds", data)
        self.assertIn("anki_total_cards", data)

    def test_voices(self):
        """Verify default voices include Ava Neural."""
        resp = self.client.get("/api/voices")
        self.assertEqual(resp.status_code, 200)
        voices = resp.json()
        self.assertTrue(any(v["id"] == "en-US-AvaNeural" for v in voices))

    def test_anki_deck_and_review(self):
        """Verify Anki deck retrieval and review flow."""
        resp = self.client.get("/api/anki")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total"], 6)
        self.assertGreaterEqual(len(data["cards"]), 6)

        # Test SM-2 review endpoint
        card_id = data["cards"][0]["id"]
        rev_resp = self.client.post("/api/anki/review", json={"id": card_id, "grade": 3})
        self.assertEqual(rev_resp.status_code, 200)
        rev_data = rev_resp.json()
        self.assertEqual(rev_data["status"], "ok")
        self.assertGreaterEqual(rev_data["card"]["repetition"], 1)

    def test_defeaters_endpoint(self):
        """Verify Pope Tools defeaters endpoint returns audited records."""
        resp = self.client.get("/api/defeaters")
        self.assertEqual(resp.status_code, 200)
        defeaters = resp.json()
        self.assertEqual(len(defeaters), 6)
        self.assertTrue(any(d["id"] == "defeater_nasranis" for d in defeaters))
        self.assertTrue(any(d["id"] == "defeater_hishtachavah" for d in defeaters))
        # 2026-10-06: was `all(... == "[V]")`, which enforced unearned [V] tags. Now: a [V] needs a source on disk/URL.
        for d in defeaters:
            self.assertIn(d["provenance_tag"], ("[V]", "[R]", "[S]"))
            if d["provenance_tag"] == "[V]":
                self.assertTrue(d.get("source_url") or (d.get("source_path") and os.path.exists(d["source_path"])),
                                f"{d['id']}: [V] without a source in hand")

    def test_arguments_register(self):
        """Verify argument register endpoint returns theses and anchors."""
        resp = self.client.get("/api/arguments")
        self.assertEqual(resp.status_code, 200)
        args = resp.json()
        self.assertEqual(len(args), 10)
        self.assertTrue(any(a["id"] == "arg_nasranis_control" for a in args))

    def test_corpus_routes_and_security(self):
        """Verify corpus routes and security path restriction."""
        stats_resp = self.client.get("/api/corpus/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats = stats_resp.json()
        self.assertGreaterEqual(stats["total_files"], 700)

        # Query
        q_resp = self.client.get("/api/corpus?q=hishtachavah")
        self.assertEqual(q_resp.status_code, 200)
        q_data = q_resp.json()
        self.assertIn("results", q_data)

        # Security check: must forbid paths not in the corpus index
        bad_resp = self.client.get("/api/corpus/file?path=C:\\Windows\\System32\\calc.exe")
        self.assertEqual(bad_resp.status_code, 403)

    def test_anki_export_tsv(self):
        """Verify TSV export includes proper Anki comment directives."""
        resp = self.client.get("/api/anki/export")
        self.assertEqual(resp.status_code, 200)
        text = resp.text
        self.assertIn("#separator:tab", text)
        self.assertIn("#html:true", text)
        self.assertIn("#deck column:1", text)

    def test_studio_cards_persistence(self):
        """Verify Scrivener index card saving and retrieval."""
        test_cards = [
            {"id": "test_1", "title": "Test Note", "text": "Sample text", "page": 1, "doc_title": "Doc"}
        ]
        post_resp = self.client.post("/api/studio/cards", json=test_cards)
        self.assertEqual(post_resp.status_code, 200)

        get_resp = self.client.get("/api/studio/cards")
        self.assertEqual(get_resp.status_code, 200)
        self.assertGreaterEqual(len(get_resp.json()), 1)

    def test_debates_battle_cards(self):
        """Verify tactical debate arena endpoint and filtering."""
        resp = self.client.get("/api/debates")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total"], 11)
        self.assertEqual(len(data["fronts"]), 4)

        # Filter by front
        p_resp = self.client.get("/api/debates?front=Protestant")
        self.assertEqual(p_resp.status_code, 200)
        p_data = p_resp.json()
        self.assertGreaterEqual(p_data["total"], 4)
        for c in p_data["cards"]:
            self.assertIn("Protestant", c["front"])
            self.assertIn("concession", c)
            self.assertIn("fatal_counter_fact", c)
            self.assertIn("verbal_soundbite_15s", c)
            # 2026-10-06: was assertEqual(..., "[V]"); see test_defeaters_endpoint.
            self.assertIn(c["provenance_tag"], ("[V]", "[R]", "[S]"))
            if c["provenance_tag"] == "[V]":
                self.assertTrue(c.get("source_url") or (c.get("source_path") and os.path.exists(c["source_path"])),
                                f"{c.get('id')}: [V] without a source in hand")

        # Search filter
        s_resp = self.client.get("/api/debates?search=hishtachavah")
        self.assertEqual(s_resp.status_code, 200)
        self.assertGreaterEqual(s_resp.json()["total"], 1)

    def test_ai_session_intelligence(self):
        """Verify universal AI session intelligence index and search."""
        resp = self.client.get("/api/sessions")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertGreaterEqual(data["total_sessions"], 500)
        self.assertGreaterEqual(data["total_words"], 5000000)
        self.assertIn("Antigravity", data["platforms"])

        # Search query
        q_resp = self.client.get("/api/sessions?query=icon&limit=10")
        self.assertEqual(q_resp.status_code, 200)
        q_data = q_resp.json()
        self.assertGreaterEqual(q_data["total_sessions"], 1)
        self.assertLessEqual(len(q_data["sessions"]), 10)

    def test_vault_concordance_dedup(self):
        """Verify L3 Obsidian vault concordance and deduplication metrics."""
        resp = self.client.get("/api/vaults/concordance?view=summary")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ready")
        summary = data["summary"]
        self.assertGreaterEqual(summary["total_files_scanned"], 45000)
        self.assertGreaterEqual(summary["duplicate_clusters_count"], 700)
        self.assertGreaterEqual(summary["redundant_words_wasted"], 20000000)

        # Test clusters view
        cl_resp = self.client.get("/api/vaults/concordance?view=clusters&limit=5")
        self.assertEqual(cl_resp.status_code, 200)
        cl_data = cl_resp.json()
        self.assertEqual(len(cl_data["items"]), 5)
        self.assertGreaterEqual(cl_data["items"][0]["count"], 2)

    def test_podcast_deep_dive_suite(self):
        """Verify OpenNotebookLM-style Deep Dive podcast API and audio delivery."""
        # 1. Episode listing
        resp = self.client.get("/api/podcast/episodes")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("episodes", data)
        self.assertGreaterEqual(len(data["episodes"]), 1)
        
        ep_map = {e["id"]: e for e in data["episodes"]}
        self.assertIn("catholic_case_deep_dive", ep_map)
        ep = ep_map["catholic_case_deep_dive"]
        self.assertIn("The Catholic Case", ep["title"])
        self.assertEqual(ep["total_turns"], 43)
        self.assertGreaterEqual(ep["total_duration_seconds"], 600)
        
        # 2. Synchronized Transcript
        tr_resp = self.client.get("/api/podcast/transcript/catholic_case_deep_dive")
        self.assertEqual(tr_resp.status_code, 200)
        tr_data = tr_resp.json()
        self.assertEqual(len(tr_data["turns"]), 43)
        self.assertEqual(tr_data["turns"][0]["speaker"], "Rachel")
        self.assertEqual(tr_data["turns"][1]["speaker"], "Leo")
        self.assertIn("start_s", tr_data["turns"][0])
        self.assertIn("end_s", tr_data["turns"][0])
        
        # 3. Audio Stream
        audio_resp = self.client.get("/api/podcast/audio/catholic_case_deep_dive")
        self.assertEqual(audio_resp.status_code, 200)
        self.assertEqual(audio_resp.headers["content-type"], "audio/mpeg")
        self.assertGreaterEqual(len(audio_resp.content), 4000000)  # > 4 MB MP3 audio

        # 4. Frontend Integration
        index_resp = self.client.get("/")
        self.assertEqual(index_resp.status_code, 200)
        self.assertIn("btn-tab-podcast", index_resp.text)
        self.assertIn("tab-podcast", index_resp.text)
        self.assertIn("podcast-audio-player", index_resp.text)
        self.assertIn("OpenNotebookLM Engine", index_resp.text)

if __name__ == "__main__":
    unittest.main()

