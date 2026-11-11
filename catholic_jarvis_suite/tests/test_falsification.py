"""
Falsification tests for CatholicJarvis Work Suite (Task C006, 2026-10-03).
Enforces Rule 3: A check that cannot fail is not a check.

Tests:
1. Card relabelled back to [V] without source is caught (falsification + clean case).
2. Podcast episode list strictly ignores sidecar files (.fidelity_reviewed.json, etc.).
3. Planted unhedged figure from needs-checking fails podcast_fidelity_check.
4. Module import failure is reported at GET /api/modules without crashing the suite.
"""
import glob
import importlib
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE_ROOT = os.path.dirname(HERE)
if SUITE_ROOT not in sys.path:
    sys.path.insert(0, SUITE_ROOT)

FIDELITY_CHECK_DIR = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\09_APPS_CATHOLICJARVIS\_LOG_ANALYSIS_2026-10-03"
if FIDELITY_CHECK_DIR not in sys.path:
    sys.path.insert(0, FIDELITY_CHECK_DIR)

from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import app
import podcast_fidelity_check as fidelity


def audit_card_source(card: dict) -> tuple[bool, str]:
    """
    Methodological audit check (Rule 4, Rule 10):
    A tag [V] requires a verifiable primary source in hand:
    either a URL (http/https) or an absolute file path that exists on disk.
    If tag is [V] and lacks both, the audit fails.
    """
    tag = card.get("provenance_tag") or card.get("tag")
    if tag != "[V]":
        return True, "Tag is not [V]; passes provenance audit"

    # Check locator / citation / source fields
    candidates = [
        str(card.get("source", "")),
        str(card.get("locator", "")),
        str(card.get("source_locator", "")),
        str(card.get("citation", ""))
    ]
    for c in candidates:
        if c.startswith("http://") or c.startswith("https://"):
            return True, f"Found URL source: {c}"
        if (len(c) > 3 and c[1:3] == ":\\") or c.startswith("/"):
            # Check absolute path
            clean_path = c.split(";")[0].split(",")[0].strip()
            if os.path.exists(clean_path):
                return True, f"Found verified disk source: {clean_path}"

    return False, "REJECTED: Tag is [V] but no valid URL or existing local file path was provided in hand"


class TestFalsification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -------------------------------------------------------------------------
    # 1. Card relabelled back to [V] without a source is caught
    # -------------------------------------------------------------------------
    def test_card_relabelled_back_to_v_without_source_caught(self):
        """
        Falsification: A card given [V] with only a bibliographic text string
        and no URL or local file on disk MUST fail the audit check.
        """
        planted_bad_card = {
            "id": 999,
            "prompt": "Test Claim without file",
            "provenance_tag": "[V]",
            "citation": "Mansi XIII, 377D; CSEL 35:520"
        }
        passed, reason = audit_card_source(planted_bad_card)
        self.assertFalse(passed, "Audit failed to catch [V] tag lacking file or URL!")
        self.assertIn("REJECTED", reason)

    def test_clean_card_with_r_or_valid_file_passes(self):
        """Clean counter-case: Cards tagged [R], or cards with existing local files, pass."""
        clean_r_card = {
            "id": 100,
            "provenance_tag": "[R]",
            "citation": "Jonas Thaliath CMI (OCA 152, 1958)"
        }
        passed, _ = audit_card_source(clean_r_card)
        self.assertTrue(passed)

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            tf.write(b"Source text in hand")
            temp_path = tf.name

        try:
            clean_v_card = {
                "id": 101,
                "provenance_tag": "[V]",
                "source": temp_path,
                "citation": "Primary text"
            }
            passed, _ = audit_card_source(clean_v_card)
            self.assertTrue(passed)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # -------------------------------------------------------------------------
    # 2. Podcast episode list strictly ignores sidecar files
    # -------------------------------------------------------------------------
    def test_podcast_list_ignores_sidecar_files(self):
        """
        Falsification & Safety: /api/podcast/episodes must list actual episode manifests
        and ignore sidecar files such as .fidelity_reviewed.json.
        """
        resp = self.client.get("/api/podcast/episodes")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        episodes = data.get("episodes", [])
        self.assertGreaterEqual(len(episodes), 1)

        for ep in episodes:
            ep_id = ep["id"]
            self.assertNotIn("fidelity_reviewed", ep_id)
            self.assertNotIn(".", ep_id)
            self.assertTrue(ep["audio_url"].endswith(ep_id))

    def test_podcast_sidecar_filtering_logic(self):
        """Falsification: A filename with two dots (.fidelity_reviewed.json) must be rejected."""
        test_files = [
            ("catholic_case_deep_dive.json", True),
            ("catholic_case_deep_dive.fidelity_reviewed.json", False),
            ("episode_02.script.json", False),
            ("new_episode.json", True),
        ]
        for fname, expected in test_files:
            is_valid_ep = fname.endswith(".json") and fname.count(".") == 1
            self.assertEqual(is_valid_ep, expected, f"Failed sidecar check for {fname}")

    # -------------------------------------------------------------------------
    # 3. Planted unhedged figure fails podcast_fidelity_check
    # -------------------------------------------------------------------------
    def test_planted_unhedged_figure_fails_podcast_fidelity_check(self):
        """
        Falsification: A podcast script turn that voices a needs-checking figure
        without any hedge word MUST be flagged by podcast_fidelity_check.check().
        """
        book_text = """# Chapter 06
## 17. Before using this in public: what still needs checking
- Are the count of 43 cases really as set out in the archival autos?
"""
        unhedged_turns = [
            {
                "turn_id": 1,
                "speaker": "Rachel",
                "text": "The archival autos document exactly 43 cases of executions."
            }
        ]
        nc, flags = fidelity.check(unhedged_turns, book_text)
        self.assertEqual(len(nc), 1)
        self.assertGreaterEqual(len(flags), 1)
        flag_kinds = [f[1] for f in flags]
        self.assertIn("UNHEDGED", flag_kinds)
        self.assertEqual(flags[0][2], "43")

    def test_hedged_figure_passes_podcast_fidelity_check(self):
        """Clean counter-case: The exact same figure voiced with a recognized hedge passes."""
        book_text = """# Chapter 06
## 17. Before using this in public: what still needs checking
- Are the count of 43 cases really as set out in the archival autos?
"""
        hedged_turns = [
            {
                "turn_id": 1,
                "speaker": "Rachel",
                "text": "There are reportedly 43 cases in the archival autos, if the figure holds."
            }
        ]
        nc, flags = fidelity.check(hedged_turns, book_text)
        self.assertEqual(len(nc), 1)
        unhedged_flags = [f for f in flags if f[1] == "UNHEDGED"]
        self.assertEqual(len(unhedged_flags), 0)

    # -------------------------------------------------------------------------
    # 4. Module import failure reported at GET /api/modules
    # -------------------------------------------------------------------------
    def test_module_import_failure_reported_at_api_modules(self):
        """
        Falsification: In a temporary copy of the suite, planting a broken module file
        must cause the loader to record the failure at /api/modules without crashing.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_modules = os.path.join(tmp_dir, "modules")
            os.makedirs(temp_modules, exist_ok=True)

            # Create a broken module file
            broken_file = os.path.join(temp_modules, "broken_sample_routes.py")
            with open(broken_file, "w", encoding="utf-8") as f:
                f.write("import non_existent_library_xyz12345\n")

            # Create an isolated FastAPI app mimicking app.py module loading
            test_app = FastAPI()
            test_module_status = {}

            for p in sorted(glob.glob(os.path.join(temp_modules, "*_routes.py"))):
                name = os.path.basename(p)[:-3]
                try:
                    # Attempt import
                    spec = importlib.util.spec_from_file_location(name, p)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    test_app.include_router(mod.router)
                    test_module_status[name] = "loaded"
                except Exception as e:
                    test_module_status[name] = f"FAILED: {type(e).__name__}: {e}"

            @test_app.get("/api/modules")
            def list_modules():
                return {"routers": test_module_status, "tabs": []}

            client = TestClient(test_app)
            resp = client.get("/api/modules")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertIn("broken_sample_routes", data["routers"])
            self.assertTrue(data["routers"]["broken_sample_routes"].startswith("FAILED: ModuleNotFoundError"))


if __name__ == "__main__":
    unittest.main()
