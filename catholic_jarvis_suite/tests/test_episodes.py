"""
Unit, integration, and falsification tests for Episodes module (module id "episodes", task C005).
"""
import json
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
from tools import build_episode as builder
from tools.make_episode_briefs import generate_episode_brief

SAMPLE_BOOK_TEXT = """# Chapter 01
Here is the main text of the chapter. There were 100 people present in the year 1920.

## 17. Before using this in public: what still needs checking
### The load-bearing claims
- Are the count of 43 cases really as set out in the archival register?
"""


class EpisodeUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.script_path = os.path.join(
            SUITE_ROOT, "data", "podcast_scripts", "catholic_case_deep_dive.script.json"
        )
        cls.episode_json = os.path.join(
            SUITE_ROOT, "data", "podcast_episodes", "catholic_case_deep_dive.json"
        )

    def test_load_script(self):
        script = builder.load_script(self.script_path)
        self.assertEqual(script.get("id"), "catholic_case_deep_dive")
        self.assertGreater(len(script.get("turns", [])), 0)
        self.assertIn("speakers", script)

    def test_run_gate_on_catholic_case_script(self):
        script = builder.load_script(self.script_path)
        passed, kept, cleared, stale, ok = builder.run_gate(script, self.script_path)
        self.assertTrue(passed)
        self.assertEqual(len(kept), 0)
        self.assertEqual(len(stale), 0)
        self.assertGreater(len(cleared), 0)

    def test_script_turns_match_existing_episode(self):
        """Question 4: turn texts in script match the existing episode manifest."""
        script = builder.load_script(self.script_path)
        self.assertTrue(os.path.exists(self.episode_json))
        with open(self.episode_json, "r", encoding="utf-8") as f:
            ep = json.load(f)

        script_turns = script.get("turns", [])
        ep_turns = ep.get("turns", [])
        self.assertEqual(len(script_turns), len(ep_turns))
        for st, et in zip(script_turns, ep_turns):
            self.assertEqual(st.get("speaker"), et.get("speaker"))
            self.assertEqual(st.get("text"), et.get("text"))

    def test_mock_tts_build_episode(self):
        """Question 2: render_episode_audio produces valid .json manifest and audio file with mock TTS."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_book = os.path.join(tmp_dir, "book.md")
            with open(temp_book, "w", encoding="utf-8") as f:
                f.write(SAMPLE_BOOK_TEXT)

            script_data = {
                "id": "temp_ep",
                "title": "Temp Episode",
                "source_path": temp_book,
                "speakers": {"Rachel": "en-US-AvaNeural", "Leo": "en-US-ChristopherNeural"},
                "turns": [
                    {"turn_id": 1, "speaker": "Rachel", "text": "In 1920, there were 100 people gathered."}
                ]
            }
            temp_script = os.path.join(tmp_dir, "temp_ep.script.json")
            with open(temp_script, "w", encoding="utf-8") as f:
                json.dump(script_data, f)

            old_podcast_dir = builder.PODCAST_DIR
            builder.PODCAST_DIR = tmp_dir
            try:
                manifest = builder.build_episode(temp_script, dry_run=False, mock_tts=True)
                self.assertEqual(manifest["title"], "Temp Episode")
                self.assertEqual(manifest["total_turns"], 1)
                self.assertTrue(os.path.exists(os.path.join(tmp_dir, "temp_ep.mp3")))
                self.assertTrue(os.path.exists(os.path.join(tmp_dir, "temp_ep.json")))
            finally:
                builder.PODCAST_DIR = old_podcast_dir


class EpisodeAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_list_episodes_api(self):
        """Question 3: GET /api/episodes lists episodes with gate status."""
        resp = self.client.get("/api/episodes")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("episodes", data)
        self.assertGreaterEqual(data["count"], 1)
        found = [e for e in data["episodes"] if e["id"] == "catholic_case_deep_dive"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["gate_status"], "PASS")
        self.assertEqual(found[0]["open_flags"], 0)

    def test_episode_fidelity_api(self):
        """Question 3: GET /api/episodes/{id}/fidelity returns per-turn flags and exceptions."""
        resp = self.client.get("/api/episodes/catholic_case_deep_dive/fidelity")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["passed"])
        self.assertEqual(len(data["open_flags"]), 0)
        self.assertGreater(len(data["cleared_exceptions"]), 0)

    def test_build_dry_run_api(self):
        resp = self.client.post("/api/episodes/catholic_case_deep_dive/build?dry_run=true")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["result"]["status"], "fidelity_passed_dry_run")

    def test_fidelity_404_on_missing_id(self):
        resp = self.client.get("/api/episodes/nonexistent_episode_xyz/fidelity")
        self.assertEqual(resp.status_code, 404)


class EpisodeFalsificationTests(unittest.TestCase):
    def test_builder_refuses_unhedged_needs_checking_figure(self):
        """
        Falsification: Planted unhedged figure from 'still needs checking' must cause
        build_episode to raise PermissionError and refuse to generate audio.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_book = os.path.join(tmp_dir, "book.md")
            with open(temp_book, "w", encoding="utf-8") as f:
                f.write(SAMPLE_BOOK_TEXT)

            # Turn 1 states "43 cases" from the needs-checking line without any hedge
            script_data = {
                "id": "unhedged_test",
                "title": "Unhedged Test",
                "source_path": temp_book,
                "speakers": {"Rachel": "en-US-AvaNeural"},
                "turns": [
                    {"turn_id": 1, "speaker": "Rachel", "text": "We know for certain there are 43 cases in the register."}
                ]
            }
            temp_script = os.path.join(tmp_dir, "unhedged_test.script.json")
            with open(temp_script, "w", encoding="utf-8") as f:
                json.dump(script_data, f)

            old_podcast_dir = builder.PODCAST_DIR
            builder.PODCAST_DIR = tmp_dir
            try:
                # Gate must fail and raise PermissionError
                with self.assertRaises(PermissionError) as ctx:
                    builder.build_episode(temp_script, dry_run=False, mock_tts=True)
                self.assertIn("Fidelity gate refused audio build", str(ctx.exception))
            finally:
                builder.PODCAST_DIR = old_podcast_dir

    def test_builder_passes_when_figure_is_hedged(self):
        """
        Clean counter-case: When the needs-checking figure is hedged ('reportedly', 'if the figure holds'),
        the gate passes.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_book = os.path.join(tmp_dir, "book.md")
            with open(temp_book, "w", encoding="utf-8") as f:
                f.write(SAMPLE_BOOK_TEXT)

            script_data = {
                "id": "hedged_test",
                "title": "Hedged Test",
                "source_path": temp_book,
                "speakers": {"Rachel": "en-US-AvaNeural"},
                "turns": [
                    {"turn_id": 1, "speaker": "Rachel", "text": "There are reportedly 43 cases in the register, though that still needs checking."}
                ]
            }
            temp_script = os.path.join(tmp_dir, "hedged_test.script.json")
            with open(temp_script, "w", encoding="utf-8") as f:
                json.dump(script_data, f)

            old_podcast_dir = builder.PODCAST_DIR
            builder.PODCAST_DIR = tmp_dir
            try:
                manifest = builder.build_episode(temp_script, dry_run=False, mock_tts=True)
                self.assertEqual(manifest["total_turns"], 1)
            finally:
                builder.PODCAST_DIR = old_podcast_dir

    def test_make_episode_briefs_refuses_overwrite(self):
        """Falsification: generate_episode_brief must refuse to overwrite an existing brief."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            import tools.make_episode_briefs as meb
            old_inbox = meb.INBOX_EPISODES
            meb.INBOX_EPISODES = tmp_dir
            try:
                b1 = meb.generate_episode_brief("test_chapter", "Test Chapter Title")
                self.assertTrue(os.path.exists(b1))
                with self.assertRaises(FileExistsError):
                    meb.generate_episode_brief("test_chapter", "Test Chapter Title")
            finally:
                meb.INBOX_EPISODES = old_inbox


if __name__ == "__main__":
    unittest.main()
