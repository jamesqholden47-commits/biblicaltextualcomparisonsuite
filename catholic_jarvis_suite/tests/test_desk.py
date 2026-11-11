"""
Tests for Did I Cook? debate desk (module id "desk", task C003).
Includes unit tests for desk_core logic, API integration tests with TestClient,
and falsification tests for sanitisation, drift detection, and claim warnings.
"""
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
from modules import desk_core as core


class DeskCoreUnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_data = os.path.join(self.tmp_dir.name, "desk_threads.json")
        core.configure(data_file=self.tmp_data)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_parse_log_format_a_and_b(self):
        # Format A: with role icon
        log_a = """
JamesQ [NOUS], Role icon, Trial Moderator — 12:43 AM
i dont really understand his first point
the rules of Christianity are virtue
 [NOUS], 
g r a s s o   l a s s o [INRI], Role icon, Catholic
OP
 — Yesterday at 11:54 PM
So i debate with my athiest friends in school often
"""
        res_a = core.parse_log(log_a, handles=["JamesQ"])
        self.assertEqual(len(res_a["messages"]), 2)
        self.assertTrue(res_a["messages"][0]["is_james"])
        self.assertFalse(res_a["messages"][1]["is_james"])
        self.assertIn("rules of Christianity", res_a["messages"][0]["text"])

        # Format B: condensed
        log_b = """
JamesQ [NOUS], — 12:43 AM
first point here
Tanner
OP
 — 12:56 AM
Nope
"""
        res_b = core.parse_log(log_b, handles=["JamesQ"])
        self.assertEqual(len(res_b["messages"]), 2)
        self.assertTrue(res_b["messages"][0]["is_james"])
        self.assertEqual(res_b["messages"][1]["text"], "Nope")

    def test_match_drafts_states(self):
        msgs = [
            {"i": 0, "author": "JamesQ", "is_james": True, "text": "This is exact draft text that was posted word for word."},
            {"i": 1, "author": "Opponent", "is_james": False, "text": "What about Romans?"},
            {"i": 2, "author": "JamesQ", "is_james": True, "text": "Here is an adapted version of my argument about the Church and tradition."}
        ]
        drafts = [
            {"id": "d1", "text": "This is exact draft text that was posted word for word.", "status": "draft"},
            {"id": "d2", "text": "Here is an adapted version of my argument regarding Church and apostolic tradition.", "status": "draft"},
            {"id": "d3", "text": "This argument was never posted to Discord anywhere at all.", "status": "draft"},
            {"id": "d4", "text": "Dropped argument by user.", "status": "dropped"}
        ]
        matches = core.match_drafts(drafts, msgs)
        m_dict = {m["id"]: m["state"] for m in matches}
        self.assertEqual(m_dict["d1"], "sent_verbatim")
        self.assertEqual(m_dict["d2"], "sent_adapted")
        self.assertEqual(m_dict["d3"], "unsent")
        self.assertEqual(m_dict["d4"], "dropped")

    def test_extract_claims_signals(self):
        text = "Matthew 16:18 gives Peter the keys. In 1569, the Reina Bible was published. Tertullian said 'the blood of martyrs'."
        claims = core.extract_claims(text)
        self.assertGreaterEqual(len(claims), 2)
        # Check Bible ref detected
        all_refs = [r["canon"] for c in claims for r in c["refs"]]
        self.assertIn("Matthew 16:18", all_refs)
        # Check date/number detected
        all_dates = [d for c in claims for d in c["dates"]]
        self.assertTrue(any("1569" in d for d in all_dates) or any("1569" in n for c in claims for n in c["numbers"]))

    def test_discordify_cleans_markup(self):
        bad_text = "Here is **bold** text\n# Heading\n| a | b |\nMath: $$x = y$$ and arrow: A → B"
        clean, changes = core.discordify(bad_text)
        # Check that bold, headings, table pipes, math, and arrow symbols are eliminated
        self.assertNotIn("**", clean)
        self.assertNotIn("#", clean)
        self.assertNotIn("$$", clean)
        self.assertNotIn("→", clean)
        self.assertIn("to", clean)  # arrow replaced with word
        self.assertGreaterEqual(len(changes), 3)


class DeskFalsificationTests(unittest.TestCase):
    def test_paste_bad_rules_parity_with_worker_gates(self):
        """Falsification: PASTE_BAD in desk_core must match PASTE_BAD in worker_gates.py."""
        gates_path = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\02_CONTROL_AND_STATE\_WORKER_SPEC\worker_gates.py"
        self.assertTrue(os.path.exists(gates_path), "worker_gates.py must exist")
        with open(gates_path, "r", encoding="utf-8") as f:
            gates_code = f.read()
        for pat, desc in core.PASTE_BAD:
            self.assertIn(pat, gates_code, f"Pattern {pat} must be present in worker_gates.py")

    def test_planted_never_deploy_claim_detected(self):
        """Falsification: Planted known never-deploy claim must be flagged as warning/never_deploy."""
        never_deploy_entry = "Pope Liberius subscribed to Arianism under torture"
        claims = core.extract_claims(never_deploy_entry)
        res, stats = core.check_claims(claims, kinds=("SUBJECT",))
        self.assertGreaterEqual(len(res), 1)
        suffix = core.provenance_suffix(res[0])
        # It must trigger either NEVER_DEPLOY warning or memory caveat
        self.assertTrue("NEVER_DEPLOY" in suffix or "memory" in suffix)

    def test_split_for_discord_under_limit(self):
        """Falsification: Long text exceeding 2000 chars must be cut into chunks <= limit."""
        long_text = ("This is a paragraph of apologetics text. " * 50 + "\n\n") * 5
        parts = core.split_for_discord(long_text, limit=1900)
        self.assertGreater(len(parts), 1)
        for p in parts:
            self.assertLessEqual(len(p), 1900)


class DeskAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_data = os.path.join(self.tmp_dir.name, "desk_threads.json")
        core.configure(data_file=self.tmp_data)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_threads_crud_and_reporting(self):
        # 1. Create thread
        res = self.client.post("/api/desk/threads", json={
            "title": "Oneness Debate with Dad",
            "position": "Christ possesses eternal divine sonship",
            "opponent": "Dad",
            "log": "Dad — 10:00 AM\nJesus is the Father\nJamesQ — 10:05 AM\nJohn 17:5 says Father glorify Me\n"
        })
        self.assertEqual(res.status_code, 200)
        t_data = res.json()
        tid = t_data["id"]
        self.assertEqual(t_data["title"], "Oneness Debate with Dad")

        # 2. Add draft
        d_res = self.client.post(f"/api/desk/threads/{tid}/drafts", json={
            "label": "John 8:17-18 witness argument",
            "text": "In John 8:17-18, the testimony of two men is true: Father and Son are two witnesses."
        })
        self.assertEqual(d_res.status_code, 200)
        did = d_res.json()["id"]

        # 3. Get thread state
        s_res = self.client.get(f"/api/desk/threads/{tid}/state?check=1")
        self.assertEqual(s_res.status_code, 200)
        st = s_res.json()
        self.assertIn("summary", st)
        self.assertIn("their_latest", st)

        # 4. Generate report
        r_res = self.client.post(f"/api/desk/threads/{tid}/report", json={
            "paste": "stack",
            "kinds": ["SUBJECT"]
        })
        self.assertEqual(r_res.status_code, 200)
        rep = r_res.json()
        self.assertIn("POSTED:", rep["text"])
        self.assertIn("THEIR LATEST:", rep["text"])
        self.assertIn("UNSENT CARRIED FORWARD:", rep["text"])
        self.assertIn("CLAIMS:", rep["text"])
        self.assertIn("PASTE:", rep["text"])

        # 5. Generate brief
        b_res = self.client.post(f"/api/desk/threads/{tid}/brief", json={
            "target": "claude",
            "socratic": False
        })
        self.assertEqual(b_res.status_code, 200)
        brief = b_res.json()
        self.assertIn("WORKER_CONTRACT v1", brief["text"])
        self.assertIn("## TASK", brief["text"])
        self.assertIn("## GATE", brief["text"])

        # 6. Parse stateless endpoint
        p_res = self.client.post("/api/desk/parse", json={
            "log": "JamesQ — 1:00 PM\nHello world\n"
        })
        self.assertEqual(p_res.status_code, 200)
        self.assertEqual(len(p_res.json()["messages"]), 1)

        # 7. Check stateless endpoint
        c_res = self.client.post("/api/desk/check", json={
            "text": "Matthew 16:18 establishes Peter as the Rock."
        })
        self.assertEqual(c_res.status_code, 200)
        self.assertIn("claims", c_res.json())


if __name__ == "__main__":
    unittest.main()
