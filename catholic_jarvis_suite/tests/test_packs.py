"""
Packs and drill tests (Phase 4, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).

Acceptance tests from the plan, each able to fail:
  - no pack entry shows [V] without a source on disk (visible_tag is shown to fail-safe to [S]);
  - every drill card links back to the thread and the message it came from (the message text is the card's front);
plus SM-2 scheduling, grading into a temporary state file, and topic matching.
"""
import os
import shutil
import sys
import tempfile
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from modules import packs_core as pc, debate_core  # noqa: E402


class TestTags(unittest.TestCase):
    def test_visible_tag(self):
        self.assertEqual(pc.visible_tag("[V]"), "[S]")                                    # no source: never [V]
        self.assertEqual(pc.visible_tag("[V]", source_path=r"C:\nope\missing.pdf"), "[S]")
        self.assertEqual(pc.visible_tag("[V]", source_path=os.path.abspath(__file__)), "[V]")
        self.assertEqual(pc.visible_tag("[V]", source_url="https://example.org/x"), "[V]")
        self.assertEqual(pc.visible_tag("[R]"), "[R]")
        self.assertEqual(pc.visible_tag(None), "[S]")

    def test_no_unsourced_V_in_any_pack(self):
        d = pc.build()
        bad = []
        for p in d["packs"]:
            for e in p["seeds"] + p["posted"]:
                if (e.get("tag") or "").upper().startswith("[V"):
                    bad.append((p["id"], e.get("title") or e.get("text", "")[:40]))
        self.assertEqual(bad, [])


class TestRetirement(unittest.TestCase):
    """Phase 5 retires the Arena and Pope Tools tabs into Packs: every card, and every field, must still be there."""

    def test_every_card_in_some_pack_with_its_fields(self):
        import json
        d = pc.build()
        placed = {}
        for p in d["packs"]:
            for s in p["seeds"]:
                placed[s["id"]] = s
        arena = json.load(open(os.path.join(pc.DATA_DIR, "debate_battle_cards.json"), encoding="utf-8"))
        popes = json.load(open(os.path.join(pc.DATA_DIR, "defeaters.json"), encoding="utf-8"))
        for c in arena:
            self.assertIn(c["id"], placed, c.get("topic"))
            s = placed[c["id"]]
            for src, dst in (("charge", "charge"), ("concession", "concession"), ("proof_text", "proof"),
                             ("verbal_soundbite_15s", "soundbite"), ("source_locator", "locator"), ("copy_paste_text", "copy")):
                self.assertEqual(s.get(dst) or "", c.get(src) or "", f"{c['id']}.{src}")
        for c in popes:
            self.assertIn(c["id"], placed, c.get("title"))
            s = placed[c["id"]]
            for src, dst in (("quote", "body"), ("body", "long"), ("original_text", "original"), ("source_locator", "locator"),
                             ("copy_text", "copy")):
                self.assertEqual(s.get(dst) or "", c.get(src) or "", f"{c['id']}.{src}")
            self.assertEqual(len(s["claims"]), len([x for x in (c.get("claims") or []) if isinstance(x, dict)]))
            for cl in s["claims"]:
                self.assertFalse(cl["tag"].upper().startswith("[V") and not cl.get("source_path"), cl)


class TestTopics(unittest.TestCase):
    def test_matching(self):
        self.assertIn("saints", pc.topics_of("why do Catholics pray to the saints instead of Jesus"))
        self.assertIn("papacy", pc.topics_of("the Bishop of Rome and the keys given to Peter"))
        self.assertNotIn("saints", pc.topics_of("the weather was nice today"))
        # word boundaries: "maryland" is not Mary, "peters" counts only as its own word
        self.assertNotIn("mary", pc.topics_of("I moved to Maryland last year"))


class TestDrillCards(unittest.TestCase):
    def test_every_card_links_back(self):
        d = pc.build()
        if not d["cards"]:
            self.skipTest("no debate logs on this machine")
        threads = {t["id"]: t for t in debate_core.harvest()["threads"]}
        for c in d["cards"]:
            t = threads.get(c["thread"])
            self.assertIsNotNone(t, c["id"])
            self.assertLess(c["msg"], len(t["messages"]))
            self.assertEqual(t["messages"][c["msg"]]["text"], c["front"])
            self.assertFalse(t["messages"][c["msg"]]["is_james"])
            if c["answer"] is not None:
                self.assertTrue(t["messages"][c["answer_msg"]]["is_james"])
                self.assertGreater(c["answer_msg"], c["msg"])


class TestSM2(unittest.TestCase):
    def test_intervals(self):
        s = pc.sm2({}, 3, "2026-10-07")
        self.assertEqual((s["interval"], s["due"]), (1, "2026-10-08"))
        s = pc.sm2(s, 3, "2026-10-08")
        self.assertEqual(s["interval"], 6)
        s = pc.sm2(s, 3, "2026-10-14")
        self.assertGreater(s["interval"], 6)
        lapsed = pc.sm2(s, 1, "2026-10-30")
        self.assertEqual((lapsed["interval"], lapsed["reps"], lapsed["lapses"]), (1, 0, 1))
        self.assertGreater(pc.sm2({}, 4, "2026-10-07")["ef"], pc.sm2({}, 2, "2026-10-07")["ef"])

    def test_grade_writes_only_the_drill_state(self):
        d = pc.build()
        if not d["cards"]:
            self.skipTest("no debate logs on this machine")
        tmp = tempfile.mkdtemp(prefix="jarvis_drill_")
        saved = pc.DRILL_FILE
        pc.DRILL_FILE = os.path.join(tmp, "drill.json")
        try:
            q = pc.drill_queue(limit=5, today="2026-10-07")
            self.assertGreater(len(q["queue"]), 0)
            cid = q["queue"][0]["id"]
            pc.grade(cid, 3, today="2026-10-07")
            q2 = pc.drill_queue(limit=5, today="2026-10-07")
            self.assertNotIn(cid, [c["id"] for c in q2["queue"]])             # graded: not due again today
            q3 = pc.drill_queue(limit=500, today="2026-10-08")
            self.assertIn(cid, [c["id"] for c in q3["queue"]])                 # due tomorrow
            with self.assertRaises(ValueError):
                pc.grade(cid, 7)
        finally:
            pc.DRILL_FILE = saved
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
