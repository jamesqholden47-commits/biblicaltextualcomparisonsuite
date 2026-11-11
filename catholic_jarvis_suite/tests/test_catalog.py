"""Catalog tab: the unfinished-request detector and the research-file classifier (Claude GUI, Opus 5.5, 2026-10-13).
Each rule is tested in both directions, so the check can fail."""
import os
import sys
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(APP_DIR, "tools"))
sys.path.insert(0, APP_DIR)

import hanging_turns as H          # noqa: E402
import ag_output_catalog as C      # noqa: E402


def turn(text, events, ts="2020-01-01T00:00:00Z", interrupted=False):
    return {"ts": ts, "uuid": text[:8], "text": text, "events": events, "launched": set(), "interrupted": interrupted}


class TestClassify(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(H.classify(turn("a", [("tool", "x"), ("answer", "done")]))[0], "ok")
        self.assertEqual(H.classify(turn("a", [("answer", "on it"), ("error", "You've hit your session limit")]))[0], "died")
        self.assertEqual(H.classify(turn("a", [("answer", "starting"), ("tool", "Bash")]))[0], "cut")
        self.assertEqual(H.classify(turn("a", []))[0], "silent")
        self.assertEqual(H.classify(turn("a", [("tool", "Bash")], interrupted=True))[0], "stopped")

    def test_failed_agents(self):
        t = turn("a", [("answer", "launched")])
        t["launched"] = {"ag1", "ag2"}
        self.assertEqual(H.classify(t, {"ag1": "failed", "ag2": "completed"})[0], "agents")
        self.assertEqual(H.classify(t, {"ag1": "completed", "ag2": "completed"})[0], "ok")

    def test_try_again_recovers_and_failed_retry_does_not(self):
        died = turn("write the book", [("error", "limit")])
        fixed = turn("try again", [("answer", "here it is")])
        self.assertEqual(H.resolve([died, fixed], "Claude", "s", "t"), [])
        still = turn("try again", [("error", "limit")])
        rows = H.resolve([died, still], "Claude", "s", "t")
        self.assertTrue(rows and all(r["request"] == "write the book" for r in rows))

    def test_continue_is_short_only(self):
        self.assertTrue(H.CONTINUE.match("Try again"))
        self.assertTrue(H.CONTINUE.match("ok continue"))
        self.assertFalse(H.CONTINUE.match("continue the trinity chapter and add the oneness refutation from both gemini conversations"))
        self.assertFalse(H.CONTINUE.match("write the book"))

    def test_resend_is_not_hanging(self):
        a = turn("ok now i want best selling books", [])
        b = turn("ok now i want best selling books in general yearly", [("answer", "done")])
        self.assertEqual(H.resolve([a, b], "Antigravity", "s", ""), [])
        c = turn("something else entirely", [("answer", "done")])
        self.assertEqual(len(H.resolve([a, c], "Antigravity", "s", "")), 1)


class TestCatalogKinds(unittest.TestCase):
    P = C.PROJECT

    def test_kind_and_side(self):
        d = os.path.join(self.P, "03_RESEARCH_DOSSIERS", "DOSSIER_GATES_OF_HADES.md")
        self.assertEqual(C._kind(d), "dossier")
        self.assertEqual(C._subject(d, "dossier"), "subject")
        code = os.path.join(self.P, "09_APPS_CATHOLICJARVIS", "x.py")
        self.assertEqual(C._kind(code), "code")
        self.assertEqual(C._subject(code, "code"), "infrastructure")
        ctl = os.path.join(self.P, "_RESUME_CORE.md")
        self.assertEqual(C._subject(ctl, C._kind(ctl)), "infrastructure")
        game = r"C:\Users\Elation\AppData\Local\Game\GameUserSettings.ini"
        self.assertEqual(C._subject(game, C._kind(game)), "infrastructure")

    def test_file_url_paths(self):
        self.assertEqual(C._norm("file:///C:/Users/Elation/a%20b.md"), os.path.normpath(r"C:\Users\Elation\a b.md"))


class TestNoise(unittest.TestCase):
    def test_noise(self):
        from modules import catalog_routes as R
        for s in ("login", "claude logout", "--resume", "winget upgrade Anthropic.ClaudeCode"):
            self.assertTrue(R.NOISE.match(s), s)
        self.assertFalse(R.NOISE.match("log the Montanism finding and write chapter 5"))


if __name__ == "__main__":
    unittest.main()
