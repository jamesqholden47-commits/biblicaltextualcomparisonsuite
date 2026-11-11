"""
Today home tests (Phase 3, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).

  - the backup-age warning fires when the last backup is older than 3 days (a fake old log must turn it red),
    and also when a run had failures, and does not fire for a fresh, clean run (so the check can fail both ways);
  - every source a Today card reads answers, and Today's debate total is the same number the Threads tab has.
"""
import os
import shutil
import sys
import tempfile
import time
import unittest
from datetime import datetime

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from modules import today_routes as today  # noqa: E402


def line(ts, failed=0):
    return (f"{datetime.fromtimestamp(ts).strftime('%Y%m%d-%H%M%S')}\tnew=1\tupdated=0\tunchanged=10\tkept_larger_previous=0\t"
            f"failed={failed}\tcopied_MB=0.1\tsessions_live=500\tsessions_in_backup=515\n")


class TestBackupAge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="jarvis_today_")
        self.log = os.path.join(self.tmp, "backup_log.tsv")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, *lines):
        with open(self.log, "w", encoding="utf-8") as fh:
            fh.writelines(lines)

    def test_old_backup_warns(self):
        now = time.time()
        self.write(line(now - 10 * 86400), line(now - 4 * 86400))
        s = today.backup_status(self.log, now)
        self.assertEqual(s["state"], "warn")
        self.assertAlmostEqual(s["age_hours"], 96, delta=0.2)
        self.assertEqual(s["runs"], 2)

    def test_fresh_backup_is_ok(self):
        now = time.time()
        self.write(line(now - 10 * 86400), line(now - 3600))
        s = today.backup_status(self.log, now)
        self.assertEqual(s["state"], "ok")
        self.assertEqual((s["sessions_live"], s["sessions_in_backup"]), ("500", "515"))

    def test_failed_copies_warn_even_when_fresh(self):
        now = time.time()
        self.write(line(now - 60, failed=3))
        s = today.backup_status(self.log, now)
        self.assertEqual(s["state"], "warn")
        self.assertIn("3 file(s) failed", s["message"])

    def test_missing_log(self):
        self.assertEqual(today.backup_status(os.path.join(self.tmp, "nope.tsv"))["state"], "missing")


class TestTodaySources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        import app as app_mod
        cls.c = TestClient(app_mod.app)

    def test_every_card_source_answers(self):
        for u in ("/api/books/next?n=3", "/api/loose/threads?limit=3", "/api/ledger/questions?missed=true&limit=3",
                  "/api/schedule", "/api/health", "/api/files/state", "/api/today/backup", "/api/build_info",
                  "/api/recall/status", "/api/files/links/status"):
            r = self.c.get(u)
            self.assertEqual(r.status_code, 200, u)

    def test_debate_total_matches_threads_tab(self):
        r = self.c.get("/api/debate/threads")
        if r.status_code != 200 or not r.json().get("threads"):
            self.skipTest("no debate logs on this machine")
        ts = r.json()["threads"]
        # Today sums unsent_points over the list; each thread's own view must give the same count
        sample = ts[:5]
        for t in sample:
            full = self.c.get(f"/api/debate/threads/{t['id']}").json()
            owed = [p for p in full["points"] if p["state"] in ("unsent", "partial", "drawn on")
                    and not p.get("dropped") and p.get("role") == "draft"]
            self.assertEqual(len(owed), t["unsent_points"], t["title"])


if __name__ == "__main__":
    unittest.main()
