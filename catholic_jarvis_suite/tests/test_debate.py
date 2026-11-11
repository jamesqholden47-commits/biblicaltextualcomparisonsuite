"""
Debate harvester tests (Phase 2, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).

Acceptance tests from the plan, each able to fail:
  - re-pasting the same log adds no new thread;
  - THE RULE 15 FAILURE, ENCODED: a point drafted at the first paste and never posted is still owed after three
    later pastes of the same debate (2026-09-10 and 2026-10-05 were this failure);
  - a point James did post (in a later log) stops being owed;
  - new-messages-only pastes in one AI chat join one thread; unrelated debates stay apart; James's split/join win;
  - the real logs: every one of the 183 pastes measured on 2026-10-07 is found (skipped on another machine).
All synthetic tests run on in-memory messages; marks go to a temporary file.
"""
import os
import shutil
import sys
import tempfile
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from modules import debate_core as dc  # noqa: E402

UNSENT = ("@Sam Look at Sirach 15:15 and Deuteronomy 30:19 together: the choice is set before every person, so the "
          "claim that the will is merely a puppet cannot stand with the text itself.")
POSTED = ("@Sam Augustine in De Trinitate 15 says the Spirit proceeds principally from the Father, so the Filioque "
          "never denied the monarchy of the Father in the first place.")


def log(*pairs):
    return "\n".join(f"{who} — 10:{i:02d} AM\n{text}" for i, (who, text) in enumerate(pairs))


BASE = [("Sam", "Free will is an illusion and every choice is fixed by prior causes, that is just science."),
        ("JamesQ", "Scripture treats the will as real, and so does every court that holds people responsible."),
        ("Sam", "Courts are a social convenience, not a proof of anything metaphysical about the will."),
        ("JamesQ", "Then your own argument is a social convenience too, since you chose to make it.")]


def msg(ts, role, text, sid="s1", surface="CL"):
    return {"ts": ts, "surface": surface, "sid": sid, "role": role, "text": text, "file": ""}


def reply_with(*sections):
    return "Here is where things stand.\n\n" + "\n\n".join(f"### {t}\n\n> {b}" for t, b in sections)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="jarvis_debate_")
        self._saved = dc.MARKS_FILE
        dc.MARKS_FILE = os.path.join(self.tmp, "marks.json")

    def tearDown(self):
        dc.MARKS_FILE = self._saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def harvest(self, messages):
        return dc._harvest(force=True, messages=messages)

    def owed(self, thread):
        return [p for p in thread["points"] if p["state"] in dc.LIVE_STATES and p["role"] == "draft"]


class TestRule15(Base):
    def test_unsent_point_survives_three_later_pastes(self):
        msgs = [msg("2026-10-01T10:00:00Z", "user", log(*BASE)),
                msg("2026-10-01T10:01:00Z", "assistant", reply_with(("Free will in Scripture", UNSENT), ("Filioque", POSTED)))]
        conv = list(BASE)
        for k, (who, text) in enumerate([("JamesQ", POSTED),
                                         ("Sam", "That is a different topic entirely, we were talking about free will here."),
                                         ("JamesQ", "Fair, but the same Father-first logic shapes how I read the will too.")]):
            conv.append((who, text))
            conv.append(("Sam", f"Round {k}: I still think determinism wins, you have not shown otherwise yet."))
            msgs.append(msg(f"2026-10-01T10:{10 + k * 5:02d}:00Z", "user", log(*conv)))
            msgs.append(msg(f"2026-10-01T10:{11 + k * 5:02d}:00Z", "assistant", "Short note with no headed sections and too few words."))
        h = self.harvest(msgs)
        self.assertEqual(h["n_snapshots"], 4)
        self.assertEqual(h["n_threads"], 1)
        t = h["threads"][0]
        states = {p["title"]: p["state"] for p in t["points"]}
        self.assertIn(states["Free will in Scripture"], dc.LIVE_STATES)         # never posted: still owed
        self.assertNotIn(states["Filioque"], dc.LIVE_STATES)                    # posted in the second paste: done
        self.assertEqual([p["title"] for p in self.owed(t)], ["Free will in Scripture"])
        # and it is in the brief an AI would get
        dc._mem.update(data=h, checked=10 ** 12)
        try:
            b = dc.brief(t["id"])
        finally:
            dc._mem.update(data=None, checked=0)
        self.assertIn("Sirach 15:15", b)
        self.assertIn("Carry EVERY unsent point", b)

    def test_check_can_fail_when_point_is_posted(self):
        # falsification: same setup, but James posts the free-will point too -> nothing owed
        msgs = [msg("2026-10-01T10:00:00Z", "user", log(*BASE)),
                msg("2026-10-01T10:01:00Z", "assistant", reply_with(("Free will in Scripture", UNSENT)))]
        conv = list(BASE) + [("JamesQ", UNSENT), ("Sam", "Sirach is not even in my Bible, so that does not move me at all.")]
        msgs.append(msg("2026-10-01T10:20:00Z", "user", log(*conv)))
        t = self.harvest(msgs)["threads"][0]
        self.assertEqual(self.owed(t), [])

    def test_no_later_paste_means_not_seen_posted(self):
        msgs = [msg("2026-10-01T10:00:00Z", "user", log(*BASE)),
                msg("2026-10-01T10:01:00Z", "assistant", reply_with(("Free will in Scripture", UNSENT)))]
        t = self.harvest(msgs)["threads"][0]
        self.assertEqual(len(self.owed(t)), 1)
        self.assertIn("no later paste", self.owed(t)[0]["why"])


class TestGrouping(Base):
    def test_repaste_adds_no_thread(self):
        text = log(*BASE)
        msgs = [msg("2026-10-01T10:00:00Z", "user", text, sid="a"),
                msg("2026-10-01T10:01:00Z", "assistant", reply_with(("Point", UNSENT)), sid="a"),
                msg("2026-10-03T09:00:00Z", "user", text, sid="b", surface="AG"),
                msg("2026-10-03T09:01:00Z", "assistant", reply_with(("Other point", POSTED)), sid="b", surface="AG")]
        h = self.harvest(msgs)
        self.assertEqual((h["n_snapshots"], h["n_threads"]), (1, 1))
        self.assertEqual(len(h["threads"][0]["points"]), 2)            # both AI replies kept as drafts

    def test_new_messages_only_paste_in_same_chat_joins(self):
        part2 = [("Sam", "Another thing: neuroscience shows decisions happen before awareness of them, Libet proved it."),
                 ("JamesQ", "Libet's own follow-up allowed a conscious veto, so even he did not draw that conclusion."),
                 ("Sam", "The veto could be determined too, you are just moving the problem back a step."),
                 ("JamesQ", "Then nothing you say could count as evidence either, it would all be fixed in advance.")]
        unrelated = [("Kim", "The rapture is in First Thessalonians four and it happens before the tribulation."),
                     ("Lee", "No it does not, read the context, that passage is about the resurrection of the dead."),
                     ("JamesQ", "Both of you are reading a pre-trib grid into Paul, the early Church never did that."),
                     ("Kim", "The early Church was not reading Darby, so of course they missed it, that proves nothing.")]
        msgs = [msg("2026-10-01T10:00:00Z", "user", log(*BASE)),
                msg("2026-10-01T10:30:00Z", "user", log(*part2)),                 # same chat, 30 min, same people
                msg("2026-10-01T10:40:00Z", "user", log(*unrelated))]            # same chat, different people
        h = self.harvest(msgs)
        self.assertEqual(h["n_threads"], 2)
        big = max(h["threads"], key=lambda t: t["n_snapshots"])
        self.assertEqual(big["n_snapshots"], 2)
        # James's split wins over the same-chat rule, and a join wins over the people rule
        snaps = {s["ts"]: s["id"] for t in h["threads"] for s in t["snapshots"]}
        dc.split_at(snaps["2026-10-01T10:30:00Z"])
        self.assertEqual(self.harvest(msgs)["n_threads"], 3)
        dc.join(snaps["2026-10-01T10:00:00Z"], snaps["2026-10-01T10:40:00Z"])
        h = self.harvest(msgs)
        self.assertEqual(h["n_threads"], 2)
        dc._mem.update(data=None, checked=0)

    def test_far_apart_pastes_stay_apart(self):
        msgs = [msg("2026-10-01T10:00:00Z", "user", log(*BASE)),
                msg("2026-10-01T15:00:00Z", "user", log(("Sam", "New day, new topic: was Peter ever in Rome at all, really?"),
                                                         ("JamesQ", "Clement, Ignatius and Irenaeus all say he was, within a century."),
                                                         ("Sam", "Those are Catholic sources, so of course they say that."),
                                                         ("JamesQ", "Ignatius wrote before there was any Catholic versus anything to take sides in.")))]
        self.assertEqual(self.harvest(msgs)["n_threads"], 2)


class TestRoles(unittest.TestCase):
    def test_draft_vs_notes(self):
        self.assertEqual(dc.point_role({"kind": "block", "text": "anything"}), "draft")
        self.assertEqual(dc.point_role({"kind": "section", "text": "> @Sam here is the reply\n> second line"}), "draft")
        self.assertEqual(dc.point_role({"kind": "section", "text": "He dodged the question again.\nNotice how he shifts."}), "notes")
        self.assertEqual(dc.point_role({"kind": "section", "text": "@Sam the text says otherwise, read verse 19."}), "draft")


class TestRealLogs(unittest.TestCase):
    def test_all_measured_pastes_found(self):
        from modules import log_reader
        try:
            msgs = log_reader.load_messages()
        except Exception as e:  # noqa: BLE001
            self.skipTest(f"logs not readable here: {e}")
        if len(msgs) < 5000:
            self.skipTest("not James's machine")
        snaps = dc.find_snapshots(msgs)
        # 183 on 2026-10-07; the logs only grow (Claude keeps 3,650 days; the AG backup keeps deleted sessions'
        # files, but log_reader reads the live AG folder, which can shrink as AG prunes - so allow a small drop)
        self.assertGreaterEqual(len(snaps), 170)


if __name__ == "__main__":
    unittest.main()
