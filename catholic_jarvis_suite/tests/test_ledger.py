"""
Question Ledger tests (module id "ledger").
Run from the suite folder:  python -m unittest tests.test_ledger -v

Every test writes only to a temporary folder (core.QUESTIONS_FILE / core.STATUS_FILE are patched);
the real data/ledger_*.json files are never touched by this file.
Falsification tests (a planted defect that the feature must catch) are named test_FALSIFY_*.
"""
import json
import os
import sys
import tempfile
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from fastapi.testclient import TestClient  # noqa: E402
from app import app  # noqa: E402
from modules import ledger_core as core  # noqa: E402
import modules.log_reader as log_reader  # noqa: E402


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def U(i, text, sid="s1", surface="CL", day="2026-09-29"):
    return {"ts": f"{day}T10:{i:02d}:00Z", "surface": surface, "sid": sid, "role": "user", "text": text, "file": "x"}


def A(i, text, sid="s1", surface="CL", day="2026-09-29"):
    return {"ts": f"{day}T10:{i:02d}:30Z", "surface": surface, "sid": sid, "role": "assistant", "text": text, "file": "x"}


class Tmp(unittest.TestCase):
    """Patches the two data files into a temp folder for the length of each test."""

    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.q = os.path.join(self._td.name, "ledger_questions.json")
        self.s = os.path.join(self._td.name, "ledger_status.json")
        self._old = (core.QUESTIONS_FILE, core.STATUS_FILE)
        core.QUESTIONS_FILE, core.STATUS_FILE = self.q, self.s

    def tearDown(self):
        core.QUESTIONS_FILE, core.STATUS_FILE = self._old
        self._td.cleanup()


class TestClassifier(unittest.TestCase):
    """Q1: the written rule that decides what is a question."""

    def label(self, text):
        return core.classify(text)[0]

    def test_questions(self):
        for t in ["is it true that the fire spares the elect?",
                  "what does the church teach about purgatory",
                  "how do we define the great apostasy",
                  "cant we make a quickview wrapper",
                  "tell me whether aquinas thought the fire spares the elect",
                  "did you ever note that down? would be worth including"]:
            self.assertEqual(self.label(t), "question", t)

    def test_requests(self):
        for t in ["explain the proof texts wagner uses and why they work or fail",
                  "run subagents on the popes of the tenth century",
                  "use subagents to dig into it",
                  "give me the full breadth of the patristic response",
                  "bro just fucking tell mewhat the patristics and scholastics wrote about the sequence"]:
            self.assertEqual(self.label(t), "request", t)

    def test_bare_instructions_are_not_questions(self):
        for t in ["continue", "Try again", "yes", "retry", "go ahead", "ok", "do it", "yes please"]:
            self.assertEqual(self.label(t), "instruction", t)

    def test_code_requests_are_not_questions(self):
        for t in ["write a python script to diff the two files",
                  "ok now fix the bug in the search endpoint",
                  "can you make a stylized html"]:
            self.assertEqual(self.label(t), "code", t)

    def test_question_mentioning_a_program_stays_a_question(self):
        self.assertEqual(self.label("so what are we doing wrong? also did you fix the blur in the program"),
                         "question")

    def test_url_query_string_is_not_a_question_mark(self):
        self.assertEqual(self.label("look at https://example.com/page?id=5 and do nothing"), "statement")

    def test_pasted_log_without_a_question(self):
        log = "Sen [IHS], Role icon, Catechumen - 8:11 PM " + ("they said a lot of things here. " * 80)
        self.assertGreater(len(log), core.LOG_MIN)
        self.assertEqual(self.label(log), "pasted_log")

    def test_question_in_the_last_300_chars_of_a_pasted_log_counts(self):
        log = ("they said a lot of things here. " * 80) + " what do you think about the last point"
        self.assertEqual(self.label(log), "question")

    def test_question_mark_in_the_middle_of_a_pasted_log_is_ignored(self):
        mid = "and who is the real author of this letter? nobody knows. " * 3
        log = ("opening words of the paste. " * 20) + mid + ("closing words of the paste. " * 80)
        self.assertGreater(len(log), core.LOG_MIN)
        self.assertNotIn("?", core.james_words(log))
        self.assertEqual(self.label(log), "pasted_log")

    def test_quoted_ai_text_does_not_count_as_james(self):
        t = 'ai leo told me this "What is the nature of the sin that you are describing here, exactly?" ok so'
        self.assertEqual(self.label(t), "statement")

    def test_pasted_agent_brief(self):
        t = "You are a Catholic Biblical theologian. " + "Investigate the objection thoroughly. " * 8
        self.assertEqual(self.label(t), "pasted_brief")

    def test_empty(self):
        self.assertEqual(self.label("   "), "empty")

    def test_james_words_rule(self):
        short = "x" * core.SHORT_MAX
        self.assertEqual(core.james_words(short), short)
        long = "a" * 400 + "b" * 400
        w = core.james_words(long)
        self.assertTrue(w.startswith("a" * 300) and w.endswith("b" * 300))
        self.assertLess(len(w), len(long))


class TestSignals(unittest.TestCase):
    BRIEF_PHRASES = ["you ignored", "ignoring", "you didnt answer", "you never answered", "you never commented",
                     "you misunderstood", "u misunderstood", "thats not what i asked", "i said", "again",
                     "ffs", "you forgot"]

    def test_constant_holds_every_phrase_from_the_brief(self):
        for p in self.BRIEF_PHRASES:
            self.assertIn(p, core.MISSED_SIGNALS)

    def test_every_phrase_is_detected_in_a_sentence(self):
        for p in core.MISSED_SIGNALS:
            text = f"honestly {p} the thing i wanted so look"
            got = [s["phrase"] for s in core.find_signals(text)]
            self.assertIn(p, got, p)

    def test_apostrophes_and_case(self):
        self.assertTrue(core.find_signals("You didn’t answer my question"))
        self.assertTrue(core.find_signals("THAT'S NOT WHAT I ASKED"))
        self.assertTrue(core.find_signals("u Misunderstood me"))

    def test_retry_is_not_a_missed_signal(self):
        for t in ["try again", "can you run it again", "Try again please", "once again thanks", "again"]:
            self.assertEqual(core.find_signals(t), [], t)

    def test_again_as_complaint_is_weak(self):
        s = core.find_signals("you are doing the same mistake again")
        self.assertEqual([x["strength"] for x in s], ["weak"])

    def test_strong_vs_weak(self):
        self.assertEqual(core.find_signals("ffs")[0]["strength"], "strong")
        self.assertEqual(core.find_signals("i said the earlier one")[0]["strength"], "weak")

    def test_signal_inside_pasted_ai_text_is_ignored(self):
        t = 'ai leo told me this "You are ignoring the premise that I gave you in the earlier message, again." ok'
        self.assertEqual(core.find_signals(t), [])

    def test_signal_in_the_middle_of_a_long_paste_is_ignored(self):
        t = ("opening. " * 40) + "ffs you ignored it " + ("closing. " * 80)
        self.assertEqual(core.find_signals(t), [])


class TestStableId(unittest.TestCase):
    def test_deterministic_and_field_sensitive(self):
        a = core.stable_id("CL", "s", "2026-01-01T00:00:00Z", "hello")
        self.assertEqual(a, core.stable_id("CL", "s", "2026-01-01T00:00:00Z", "hello"))
        self.assertRegex(a, r"^[0-9a-f]{40}$")
        self.assertNotEqual(a, core.stable_id("AG", "s", "2026-01-01T00:00:00Z", "hello"))
        self.assertNotEqual(a, core.stable_id("CL", "t", "2026-01-01T00:00:00Z", "hello"))
        self.assertNotEqual(a, core.stable_id("CL", "s", "2026-01-01T00:00:01Z", "hello"))
        self.assertNotEqual(a, core.stable_id("CL", "s", "2026-01-01T00:00:00Z", "hellp"))

    def test_only_first_200_characters_matter(self):
        base = "q" * 200
        self.assertEqual(core.stable_id("CL", "s", "t", base + "tail one"), core.stable_id("CL", "s", "t", base + "tail two"))
        self.assertNotEqual(core.stable_id("CL", "s", "t", "q" * 199 + "z"), core.stable_id("CL", "s", "t", base))


def eschatology_thread(sid="esch"):
    """A small copy of the real 2026-09-29 thread's shape."""
    return [
        U(1, "now run subagents on whether aquinas and church fathers believe this fire will spare the elect; "
             "and then help my fiance identify the credibility of such 12 signs", sid),
        A(2, "Subagents launched in parallel. Here is the exposition of the Final Fire.", sid),
        U(3, "subagents delve into what we are talking about: the sequence of the events; like if the fire is after "
             "the 12 signs you earlier said", sid),
        A(4, "It is completely understandable to feel a sense of intensity about these texts.", sid),
        U(5, "bro just fucking tell me what the patristics and scholastics wrote about the general sequence of "
             "events and ffs youre ignoring the 12 signs u mentioned earlier", sid),
        A(6, "Here is the direct, systematic breakdown of the Last Things.", sid),
    ]


class TestExtraction(Tmp):
    def test_eschatology_thread_flags_the_earlier_question(self):
        items, stats = core.extract(eschatology_thread())
        by_ts = {i["ts"]: i for i in items}
        first = by_ts["2026-09-29T10:01:00Z"]
        self.assertTrue(first["missed"], "the question the 12 signs were first asked in must carry the signal")
        sig = [s for s in first["signals"] if s["phrase"] in ("ignoring", "ffs")]
        self.assertTrue(sig)
        self.assertEqual(sig[0]["reason"], "refers-to")
        self.assertIn("12", sig[0]["shared"])
        self.assertIn("signs", sig[0]["shared"])
        self.assertIn("ignoring the 12 signs", sig[0]["text"])
        # the question just before the complaint carries it too (reason: previous)
        second = by_ts["2026-09-29T10:03:00Z"]
        self.assertTrue(second["missed"])
        self.assertEqual({s["reason"] for s in second["signals"]}, {"previous"})
        # the complaining message is itself a question and must not be flagged by itself
        third = by_ts["2026-09-29T10:05:00Z"]
        self.assertFalse(third["missed"])

    def test_clean_session_has_no_missed_signal(self):
        msgs = [U(1, "what is purgatory?", "clean"), A(2, "Purgatory is...", "clean"),
                U(3, "and how long does it last?", "clean"), A(4, "Nobody knows.", "clean"),
                U(5, "thanks that makes sense", "clean")]
        items, stats = core.extract(msgs)
        self.assertEqual(stats["n_ledger"], 2)
        self.assertEqual(stats["n_missed"], 0)
        self.assertTrue(all(not i["missed"] for i in items))

    def test_FALSIFY_planted_missed_answer_is_caught(self):
        msgs = [U(1, "why did Nicaea condemn Arius?", "p"), A(2, "Nicaea met in 325.", "p"),
                U(3, "thats not what i asked, you ignored the why", "p"), A(4, "Sorry.", "p")]
        items, stats = core.extract(msgs)
        q = next(i for i in items if i["text"].startswith("why did Nicaea"))
        self.assertTrue(q["missed"])
        self.assertEqual(stats["n_missed_strong"], 1)
        # remove the planted complaint and the flag must go away (the check can fail both ways)
        items2, stats2 = core.extract(msgs[:2] + [U(3, "ok next topic then", "p"), A(4, "Sure.", "p")])
        self.assertEqual(stats2["n_missed"], 0)

    def test_signal_in_another_session_is_not_attached(self):
        msgs = [U(1, "why did Nicaea condemn Arius?", "a"), A(2, "Nicaea met in 325.", "a"),
                U(3, "ffs you ignored me", "b"), A(4, "Sorry.", "b")]
        items, stats = core.extract(msgs)
        self.assertEqual(stats["n_missed"], 0)

    def test_signal_before_any_reply_is_not_attached(self):
        msgs = [U(1, "why did Nicaea condemn Arius?", "a"), U(2, "ffs why is it so slow", "a"), A(3, "Nicaea.", "a")]
        items, stats = core.extract(msgs)
        self.assertEqual(stats["n_missed"], 0)

    def test_weak_only_signal_is_marked_weak(self):
        msgs = [U(1, "why did Nicaea condemn Arius?", "w"), A(2, "Nicaea met in 325.", "w"),
                U(3, "i said the date matters", "w"), A(4, "Ok.", "w")]
        items, stats = core.extract(msgs)
        q = next(i for i in items if i["text"].startswith("why did"))
        self.assertTrue(q["missed"])
        self.assertEqual({s["strength"] for s in q["signals"]}, {"weak"})
        self.assertEqual(stats["n_missed_strong"], 0)

    def test_retry_instruction_is_not_a_missed_signal(self):
        msgs = [U(1, "why did Nicaea condemn Arius?", "a"), A(2, "Nicaea met in 325.", "a"),
                U(3, "try again", "a"), A(4, "Nicaea condemned him for denying the Son is homoousios.", "a")]
        items, stats = core.extract(msgs)
        self.assertEqual(stats["n_missed"], 0)

    def test_reply_excerpt_is_first_600_characters_of_next_assistant_message(self):
        reply = "R" * 900
        items, _ = core.extract([U(1, "what is grace?", "r"), A(2, reply, "r"), A(3, "second assistant message", "r")])
        self.assertEqual(items[0]["reply"], "R" * core.REPLY_KEEP)
        self.assertEqual(items[0]["reply_len"], 900)
        self.assertFalse(items[0]["no_reply"])

    def test_no_reply_and_reply_after_other_user(self):
        items, _ = core.extract([U(1, "what is grace?", "r"), U(2, "also what is nature?", "r"), A(3, "Both are...", "r")])
        by = {i["text"]: i for i in items}
        self.assertTrue(by["what is grace?"]["reply_after_other_user"])
        self.assertFalse(by["also what is nature?"]["reply_after_other_user"])
        items2, _ = core.extract([U(1, "what is grace?", "z")])
        self.assertTrue(items2[0]["no_reply"])
        self.assertEqual(items2[0]["reply"], "")

    def test_ledger_holds_questions_and_requests_only(self):
        msgs = [U(1, "continue", "k"), A(2, "ok", "k"), U(3, "write a python script for this", "k"), A(4, "ok", "k"),
                U(5, "what is grace?", "k"), A(6, "Grace is...", "k"), U(7, "k fine", "k")]
        items, stats = core.extract(msgs)
        self.assertEqual([i["text"] for i in items], ["what is grace?"])
        self.assertEqual(stats["n_user_by_label"]["instruction"], 1)
        self.assertEqual(stats["n_user_by_label"]["code"], 1)

    def test_ids_are_unique(self):
        items, _ = core.extract(eschatology_thread("a") + eschatology_thread("b"))
        self.assertEqual(len({i["id"] for i in items}), len(items))


class TestMarksSurviveRebuild(Tmp):
    def test_mark_survives_rebuild_and_rebuild_leaves_status_file_untouched(self):
        msgs = eschatology_thread()
        doc = core.rebuild(messages=msgs)
        qid = doc["items"][0]["id"]
        core.set_mark(qid, "dropped", note="never got the 12 signs")
        before = read_bytes(self.s)
        core.rebuild(messages=msgs)
        self.assertEqual(read_bytes(self.s), before, "rebuild must not rewrite ledger_status.json")
        items, _, orphans = core.merged_items()
        got = next(i for i in items if i["id"] == qid)
        self.assertEqual(got["status"], "dropped")
        self.assertEqual(got["note"], "never got the 12 signs")
        self.assertEqual(orphans, 0)
        # default status
        self.assertTrue(all(i["status"] == "unreviewed" for i in items if i["id"] != qid))

    def test_FALSIFY_mark_on_a_message_that_vanished_becomes_an_orphan_not_a_wrong_mark(self):
        msgs = eschatology_thread()
        doc = core.rebuild(messages=msgs)
        qid = doc["items"][0]["id"]
        core.set_mark(qid, "answered")
        core.rebuild(messages=msgs[2:])  # first question gone
        items, _, orphans = core.merged_items()
        self.assertEqual(orphans, 1)
        self.assertTrue(all(i["status"] == "unreviewed" for i in items))
        core.rebuild(messages=msgs)  # comes back: the mark is still there
        items, _, orphans = core.merged_items()
        self.assertEqual(next(i for i in items if i["id"] == qid)["status"], "answered")
        self.assertEqual(orphans, 0)

    def test_unreviewed_removes_the_mark(self):
        doc = core.rebuild(messages=eschatology_thread())
        qid = doc["items"][0]["id"]
        core.set_mark(qid, "open")
        core.set_mark(qid, "unreviewed")
        self.assertNotIn(qid, core.load_marks())

    def test_bad_input_rejected(self):
        with self.assertRaises(ValueError):
            core.set_mark("nothex", "open")
        with self.assertRaises(ValueError):
            core.set_mark("a" * 40, "finished")


class TestFilters(Tmp):
    def setUp(self):
        super().setUp()
        self.msgs = (
            [U(1, "what is grace?", "c1", "CL", "2026-08-01"), A(2, "Grace is a gift.", "c1", "CL", "2026-08-01")] +
            [U(1, "why did Nicaea condemn Arius?", "c2", "CL", "2026-09-10"), A(2, "It met in 325.", "c2", "CL", "2026-09-10"),
             U(3, "ffs you ignored the why", "c2", "CL", "2026-09-10"), A(4, "Sorry", "c2", "CL", "2026-09-10")] +
            [U(1, "how does the Octave of Easter work?", "g1", "AG", "2026-09-20"), A(2, "Eight days.", "g1", "AG", "2026-09-20")]
        )
        core.rebuild(messages=self.msgs)
        self.items, _, _ = core.merged_items()
        by = {i["text"][:12]: i for i in self.items}
        core.set_mark(by["what is grac"]["id"], "answered")
        core.set_mark(by["why did Nica"]["id"], "dropped")
        self.items, _, _ = core.merged_items()

    def texts(self, **kw):
        return sorted(i["text"][:12] for i in core.filter_items(self.items, **kw))

    def test_status(self):
        self.assertEqual(self.texts(status="answered"), ["what is grac"])
        self.assertEqual(self.texts(status="dropped"), ["why did Nica"])
        self.assertEqual(self.texts(status="unreviewed"), ["how does the"])
        self.assertEqual(len(self.texts(status="answered,dropped")), 2)

    def test_surface(self):
        self.assertEqual(self.texts(surface="AG"), ["how does the"])
        self.assertEqual(len(self.texts(surface="cl")), 2)

    def test_date_range_inclusive(self):
        self.assertEqual(self.texts(date_from="2026-09-01", date_to="2026-09-10"), ["why did Nica"])
        self.assertEqual(self.texts(date_to="2026-08-01"), ["what is grac"])
        self.assertEqual(len(self.texts(date_from="2026-09-10")), 2)

    def test_text_searches_question_reply_and_later_message(self):
        self.assertEqual(self.texts(text="octave easter"), ["how does the"])
        self.assertEqual(self.texts(text="325"), ["why did Nica"])          # in the reply
        self.assertEqual(self.texts(text="you ignored"), ["why did Nica"])  # in the later message
        self.assertEqual(self.texts(text="octave 325"), [])                 # all words must occur

    def test_missed(self):
        self.assertEqual(self.texts(missed=True), ["why did Nica"])
        self.assertEqual(len(self.texts(missed=False)), 2)

    def test_strong_only(self):
        self.assertEqual(self.texts(strong=True), ["why did Nica"])
        weak = [dict(i, signals=[{"phrase": "again", "strength": "weak"}], missed=True) for i in self.items[:1]]
        self.assertEqual(core.filter_items(weak, missed=True), weak)
        self.assertEqual(core.filter_items(weak, strong=True), [])

    def test_markdown_export(self):
        md = core.to_markdown(core.filter_items(self.items))
        self.assertIn("- [x] 2026-08-01 CL [answered]", md)
        self.assertIn("- [ ] 2026-09-10 CL [dropped] POSSIBLY MISSED", md)
        self.assertIn("- [ ] 2026-09-20 AG [unreviewed]", md)
        self.assertIn('signal "you ignored"', md)
        self.assertEqual(md.count("- ["), 3)


class TestRoutes(Tmp):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        super().setUp()
        self.msgs = eschatology_thread() + [U(1, "what is grace?", "c1", "AG", "2026-08-01"),
                                             A(2, "Grace is a gift.", "c1", "AG", "2026-08-01")]
        self._lm = log_reader.load_messages
        log_reader.load_messages = lambda use_cache=True: self.msgs
        self.client.post("/api/ledger/rebuild")

    def tearDown(self):
        log_reader.load_messages = self._lm
        super().tearDown()

    def test_module_registered(self):
        d = self.client.get("/api/modules").json()
        self.assertEqual(d["routers"].get("ledger_routes"), "loaded")
        self.assertIn("ledger", [t["id"] for t in d["tabs"]])

    def test_questions_endpoint_and_filters(self):
        d = self.client.get("/api/ledger/questions").json()
        self.assertEqual(d["total"], 4)
        self.assertEqual(self.client.get("/api/ledger/questions?surface=AG").json()["total"], 1)
        self.assertEqual(self.client.get("/api/ledger/questions?missed=true").json()["total"], 2)
        self.assertEqual(self.client.get("/api/ledger/questions?text=12+signs").json()["total"], 3)
        self.assertEqual(self.client.get("/api/ledger/questions?date_to=2026-08-31").json()["total"], 1)
        self.assertEqual(self.client.get("/api/ledger/questions?limit=2").json()["items"].__len__(), 2)

    def test_mark_roundtrip_through_api_and_rebuild(self):
        q = self.client.get("/api/ledger/questions?text=credibility").json()["items"][0]
        self.assertEqual(q["status"], "unreviewed")
        r = self.client.post("/api/ledger/mark", json={"id": q["id"], "status": "dropped"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(read_json(self.s)["marks"][q["id"]]["status"], "dropped")
        self.client.post("/api/ledger/rebuild")
        again = self.client.get("/api/ledger/questions?status=dropped").json()
        self.assertEqual([i["id"] for i in again["items"]], [q["id"]])
        self.assertEqual(self.client.get("/api/ledger/stats").json()["counts"]["dropped"], 1)

    def test_mark_rejects_bad_status_and_id(self):
        q = self.client.get("/api/ledger/questions").json()["items"][0]
        self.assertEqual(self.client.post("/api/ledger/mark", json={"id": q["id"], "status": "finished"}).status_code, 400)
        self.assertEqual(self.client.post("/api/ledger/mark", json={"id": "../../etc", "status": "open"}).status_code, 400)
        self.assertFalse(os.path.exists(self.s))

    def test_export_md(self):
        q = self.client.get("/api/ledger/questions?text=credibility").json()["items"][0]
        self.client.post("/api/ledger/mark", json={"id": q["id"], "status": "answered"})
        r = self.client.get("/api/ledger/export.md?surface=CL")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/markdown", r.headers["content-type"])
        self.assertIn("- [x]", r.text)
        self.assertNotIn("what is grace", r.text)  # AG question filtered out

    def test_strong_filter_endpoint(self):
        self.assertEqual(self.client.get("/api/ledger/questions?strong=true").json()["total"], 2)
        self.assertEqual(self.client.get("/api/ledger/export.md?strong=true").text.count("- ["), 2)

    def test_stats(self):
        s = self.client.get("/api/ledger/stats").json()
        self.assertEqual(s["n_ledger"], 4)
        self.assertEqual(s["n_missed"], 2)
        self.assertIn("ffs", s["missed_signals"])

    def test_static_script_served_and_safe(self):
        r = self.client.get("/static/modules/ledger.js")
        self.assertEqual(r.status_code, 200)
        self.assertIn('window.JarvisModules["ledger"]', r.text)
        self.assertNotIn("innerHTML", r.text)  # all log text goes through textContent
        for label in ("Open", "Answered", "Dropped", "Not a question"):
            self.assertIn(label, r.text)


class TestRealLogs(Tmp):
    """Runs on the real logs when they exist (skipped otherwise). Writes only to the temp folder."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.msgs = log_reader.load_messages()
        except Exception:
            cls.msgs = []

    def test_real_eschatology_thread(self):
        sid = "2e8c5c15-e89f-4dc4-b90c-b0076e99d784"
        if not any(m["sid"] == sid for m in self.msgs):
            self.skipTest("eschatology session not on this machine")
        items, stats = core.extract(self.msgs)
        self.assertGreater(stats["n_ledger"], 100)
        first = [i for i in items if i["sid"] == sid and "credibility of such 12 signs" in i["text"]]
        self.assertEqual(len(first), 1)
        self.assertTrue(first[0]["missed"])
        phrases = {s["phrase"] for s in first[0]["signals"]}
        self.assertTrue({"ignoring", "ffs"} <= phrases, phrases)
        sig = next(s for s in first[0]["signals"] if s["phrase"] == "ignoring")
        self.assertIn("ignoring the 12 signs u mentioned earlier", sig["text"])
        self.assertEqual(len({i["id"] for i in items}), len(items))


if __name__ == "__main__":
    unittest.main()
