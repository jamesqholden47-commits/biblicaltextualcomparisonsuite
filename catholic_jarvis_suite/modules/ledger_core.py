"""
Question Ledger core (module id "ledger"): every question James asked an AI, whether the reply
that followed it looks answered, and which ones may have been dropped.

Deterministic heuristics only. No network, no LLM. Reads logs ONLY through modules.log_reader.

Data files (both in the suite's data/ folder):
  ledger_questions.json  extracted and regenerable (rebuild() rewrites it; nothing of James's lives here)
  ledger_status.json     James's marks, keyed by the stable id; rebuild() NEVER touches it

THE WRITTEN RULES (each one is unit-tested in tests/test_ledger.py)

R0  James's words.  Long messages are mostly pasted Discord logs, so the classifier reads only
    james_words(text): first every quoted passage of 40+ characters ("..." or curly quotes) and every
    '>' line is removed (somebody else's words), then the whole remainder if it is at most SHORT_MAX
    (600) characters, otherwise its first HEAD_TAIL (300) plus its last HEAD_TAIL (300) characters.
R1  empty             -> "empty".
R2  bare instruction  -> "instruction": the whole message, lowercased and stripped of punctuation,
    is at most 4 words and matches BARE_INSTRUCTION_RE (continue, try again, go ahead, ok, yes ...).
R2b agent brief       -> "pasted_brief": the message is over 200 characters and opens with "You are a/an/the ..."
    (a subagent brief James pasted back into the chat; the question inside it is not his).
R3  code request      -> "code": a CODE_VERB occurs within 60 characters (no sentence break) before a
    CODE_NOUN ("write a python script", "fix the bug", "add an endpoint") AND either the message has no
    question evidence (R4) or it opens with a code verb ("ok now write ...", "can you make ..."). A
    question that merely mentions a program ("so what are we doing wrong? did you fix the app") stays a
    question.
R4  question          -> "question": the question evidence test below finds a question mark (not part
    of a URL), a sentence-initial interrogative word, or an interrogative frame ("whether",
    "how does", "what about", "do you think" ...).
R5  request           -> "request": no question form, but a request-for-an-answer verb (explain, tell me,
    compare, exposit, identify, look into, research, give me ...) or "run/use <sub>agents / a workflow ...".
R6  otherwise         -> "pasted_log" if the message is longer than LOG_MIN (1500) characters, else
    "statement".
Only "question" and "request" enter the ledger.

THE MISSED-ANSWER RULES
S1  A later user message S in the same (surface, session) whose james_words contains a phrase of
    MISSED_SIGNALS is a signal message. "again" is not counted inside a retry ("try again", "run it
    again" ...: AGAIN_RETRY_RE).
S2  S attaches to ledger question Q of the same session when Q comes before S and Q's reply (the
    first assistant message after Q) also comes before S, and either
      (a) Q is the nearest ledger question before S (reason "previous"), or
      (b) Q shares distinctive words with S whose weight is at least MIN_REF_SCORE when a number is
          among them (the "12" in "the 12 signs"), or at least MIN_REF_SCORE_NO_NUMBER when not
          (reason "refers-to"; a number weighs 2, any other word of 3+ letters that is not a stop
          word weighs 1; at most MAX_REF_EXTRA questions are attached this way, best score first).
    A question that gets at least one attached signal has missed = true (a POSSIBLY missed answer:
    the ledger never says the answer was missed, only that James later sounded as if it was).
S3  The stable id is sha1("surface|sid|ts|first 200 chars of text"). It does not depend on anything
    that changes between rebuilds, so James's marks survive a rebuild.
"""
import datetime
import hashlib
import json
import os
import re

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_HERE, "data")
QUESTIONS_FILE = os.path.join(DATA_DIR, "ledger_questions.json")
STATUS_FILE = os.path.join(DATA_DIR, "ledger_status.json")

HEAD_TAIL = 300
SHORT_MAX = 600
LOG_MIN = 1500
TEXT_KEEP = 1200       # question text stored in ledger_questions.json
REPLY_KEEP = 600       # reply excerpt (first 600 characters of the next assistant message)
SIGNAL_KEEP = 300
MIN_REF_SCORE = 3
MIN_REF_SCORE_NO_NUMBER = 5
MAX_REF_EXTRA = 2

STATUSES = ("open", "answered", "dropped", "not-a-question")
DEFAULT_STATUS = "unreviewed"

# One constant, as the brief requires. Apostrophes are stripped before matching, so "didnt" covers
# "didn't". The first block is strong evidence, the last two are weak (they fire in ordinary speech).
MISSED_SIGNALS = (
    "you ignored", "u ignored", "ignoring", "you didnt answer", "u didnt answer",
    "you never answered", "u never answered", "you never commented", "u never commented",
    "you misunderstood", "u misunderstood", "misunderstood me", "thats not what i asked",
    "not what i asked", "you forgot", "u forgot", "ffs",
    "i said", "again",
)
WEAK_SIGNALS = ("i said", "again")

# "try again" is a retry instruction, not a complaint that an answer was missed.
AGAIN_RETRY_RE = re.compile(
    r"\b(?:try|run|do|go|check|look|read|search|start|ask|say|send|redo|retry|generate|make|write)\b"
    r"(?:\s+\w+){0,2}\s+again\b|\bonce again\b|\bagain please\b|\bagain pls\b|^again$")

AGENT_BRIEF_RE = re.compile(r"\s*you are (?:an? |the )", re.I)

BARE_INSTRUCTION_RE = re.compile(
    r"(?:continue|go on|go ahead|go|ok|okay|k|kk|yes|yep|yeah|ya|no|nope|proceed|retry|try again|do it|"
    r"next|thanks|thank you|thx|ty|stop|done|good|great|nice|cool|lol|wait|hm|hmm|keep going|carry on|"
    r"resume|again|sure|please|yes please|do that|continue please|go for it|beautiful|perfect|amazing)"
    r"(?:\s+(?:continue|go|ok|okay|yes|please|pls|now|it|that|then))*")

CODE_VERB = r"(?:write|create|build|make|implement|fix|refactor|debug|add|edit|modify|patch|rewrite|install|compile|code)"
CODE_NOUN = (r"(?:script|function|code|python|powershell|regex|endpoint|module|bug|html|css|javascript|json|"
             r"program|bash|\.py|\.js|\.pyw|commit|repo|compile|traceback|stack trace|unit test|tests?|"
             r"app|api|class|parser|scraper|hook)")
CODE_REQUEST_RE = re.compile(rf"\b{CODE_VERB}\b[^.\n?!]{{0,60}}?(?<![a-z0-9_])(?:{CODE_NOUN})(?![a-z0-9_])")

_QMARK_RE = re.compile(r"\?+(?=\s|$|[\"')\]*_])")
_SENT_INTERROG_RE = re.compile(
    r"(?:^|[.!;:\n]\s*)(?:what|why|how|who|whom|whose|when|where|which|is|are|was|were|does|did|can|could|"
    r"would|should|isnt|arent|doesnt|cant|couldnt|wouldnt|shouldnt|wont|didnt|hasnt|havent)\b")
_FRAME_RE = re.compile(
    r"\b(?:whether|how (?:do|does|did|can|could|would|should|come|many|much|is|are|was)|"
    r"what (?:is|are|was|were|does|do|did|about|if|exactly)|why (?:is|are|was|were|does|do|did|would|didnt)|"
    r"is it true|do you think|any idea|i wonder|wondering)\b")
_REQUEST_VERB_RE = re.compile(
    r"\b(?:explain|describe|compare|summari[sz]e|exposit|elaborate|walk me through|define|"
    r"find out|find a way|figure out|look into|research|investigate|analy[sz]e|identify|clarify|"
    r"i want to know|i wanna know)\b|\b(?:tell|show|give) ?me")
_RUN_AGENTS_RE = re.compile(
    r"\b(?:run|use|launch|spawn|deploy|send)\b[^.\n]{0,40}?\b(?:sub-?agents?|workflow|agents?|fleet)\b|"
    r"^sub-?agents?\b")
# a code verb at the head of the message ("ok now write a script", "can you make the app ...")
_CODE_LEAD_RE = re.compile(
    r"^(?:(?:ok|okay|now|pls|please|and|so|then|can you|could you|can u|would you)\s+)*" + CODE_VERB + r"\b")

_STOP = frozenset("""the and for are but not you your yours with that this these those from have has had was were
will would could should can cant cannot did does dont doesnt just like also then than them they their there here
what when where which who whom whose why how about into onto over under again very much more most some any all
its it's out off our ours his her him she let lets get got say said says see seen mean meant need needs want wants
now one two bro ffs fucking fuck shit damn really actually basically still even ever never always already because
while being been before after between through during without within against among upon per via yes yeah okay
mentioned earlier ignoring ignored ignore misunderstood forgot tell told make made too perhaps people thing
things going think know use using want wanna gonna kinda sorta maybe""".split())


# ----------------------------------------------------------------------------------------------
# text helpers


def _replace_retry(tmp, path, tries=8):
    """os.replace with a short retry: on Windows an antivirus or indexer can hold the target for a
    moment and the replace fails with PermissionError (seen once in tests/test_ledger, 2026-10-06)."""
    import time as _t
    for i in range(tries):
        try:
            return os.replace(tmp, path)
        except PermissionError:
            if i == tries - 1:
                raise
            _t.sleep(0.05 * (i + 1))

def norm(text):
    """Lowercase, drop apostrophes, collapse whitespace. 'Didn't' -> 'didnt'."""
    t = (text or "").lower().replace("’", "").replace("'", "").replace("`", "")
    return re.sub(r"\s+", " ", t).strip()


_QUOTED_RE = re.compile('"[^"]{40,}?"|“[^”]{40,}?”')
_QUOTE_LINE_RE = re.compile(r"^[ \t]*>.*$", re.M)


def strip_quoted(text):
    """Quoted passages of 40+ characters and '>' lines are somebody else's words (an AI reply or a Discord
    message James pasted), so a '?' or 'ignoring' inside them says nothing about what James asked."""
    return _QUOTE_LINE_RE.sub(" ", _QUOTED_RE.sub(" ", text or ""))


def james_words(text):
    """R0: the part of a message that is James's own words."""
    t = strip_quoted(text).strip()
    if len(t) <= SHORT_MAX:
        return t
    return t[:HEAD_TAIL] + "\n...\n" + t[-HEAD_TAIL:]


def stable_id(surface, sid, ts, text):
    """S3."""
    key = f"{surface}|{sid}|{ts}|{(text or '')[:200]}"
    return hashlib.sha1(key.encode("utf-8", "replace")).hexdigest()


def question_evidence(words):
    """Return the name of the question evidence found in normalized text, or None."""
    if _QMARK_RE.search(words):
        return "question-mark"
    if _SENT_INTERROG_RE.search(words):
        return "interrogative-start"
    if _FRAME_RE.search(words):
        return "interrogative-frame"
    return None


def classify(text):
    """Apply R1-R6. Returns (label, reason). Label is one of
    empty / instruction / code / question / request / pasted_log / statement."""
    raw = (text or "").strip()
    if not raw:
        return "empty", "R1 empty"
    words = norm(james_words(raw))
    plain = re.sub(r"[^\w\s]", "", words).strip()
    if len(raw) <= SHORT_MAX and len(plain.split()) <= 4 and BARE_INSTRUCTION_RE.fullmatch(plain):
        return "instruction", "R2 bare instruction"
    if len(raw) > 200 and AGENT_BRIEF_RE.match(raw):
        return "pasted_brief", "R2b pasted agent brief ('You are a ...')"
    ev = question_evidence(words)
    if CODE_REQUEST_RE.search(words) and (ev is None or _CODE_LEAD_RE.match(words)):
        return "code", "R3 code request"
    if ev:
        return "question", f"R4 {ev}"
    if _REQUEST_VERB_RE.search(words):
        return "request", "R5 request verb"
    if _RUN_AGENTS_RE.search(words):
        return "request", "R5 run agents/workflow"
    if len(raw) > LOG_MIN:
        return "pasted_log", "R6 long, no question in James's words"
    return "statement", "R6 statement"


def is_ledger_kind(label):
    return label in ("question", "request")


def find_signals(text):
    """S1: every MISSED_SIGNALS phrase found in James's words. Returns [{"phrase", "strength"}]."""
    words = norm(james_words(text))
    found = []
    for ph in MISSED_SIGNALS:
        pat = r"(?<![a-z0-9])" + r"\s+".join(re.escape(w) for w in ph.split()) + r"(?![a-z0-9])"
        for m in re.finditer(pat, words):
            if ph == "again":
                lo = max(0, m.start() - 40)
                ctx = words[lo:m.end()]
                if AGAIN_RETRY_RE.search(ctx) or words == "again":
                    continue
            found.append({"phrase": ph, "strength": "weak" if ph in WEAK_SIGNALS else "strong"})
            break
    return found


def _weights(text):
    """Distinctive-word weights of James's words: number 2, other 3+ letter non-stop word 1."""
    out = {}
    for w in re.findall(r"[a-z0-9]+", norm(james_words(text))):
        if w.isdigit():
            out[w] = 2
        elif len(w) >= 3 and w not in _STOP:
            out[w] = 1
    return out


def shared_score(a_text, b_text):
    wa, wb = _weights(a_text), _weights(b_text)
    shared = sorted(set(wa) & set(wb))
    return sum(max(wa[w], wb[w]) for w in shared), shared


def refers_to(score, shared):
    """S2(b): is a shared-word score strong enough to say S refers to the other message?"""
    has_number = any(w.isdigit() for w in shared)
    return score >= (MIN_REF_SCORE if has_number else MIN_REF_SCORE_NO_NUMBER)


# ----------------------------------------------------------------------------------------------
# extraction

def extract(messages):
    """Pure function: list of log_reader messages (chronological) -> (items, stats).
    Used by rebuild() and by the tests (which feed it planted messages)."""
    sessions = {}
    for idx, m in enumerate(messages):
        sessions.setdefault((m["surface"], m["sid"]), []).append(idx)

    items, by_label, seen_ids = [], {}, set()
    by_session_items = {}
    for key, idxs in sessions.items():
        for pos, idx in enumerate(idxs):
            m = messages[idx]
            if m["role"] != "user":
                continue
            label, reason = classify(m["text"])
            by_label[label] = by_label.get(label, 0) + 1
            if not is_ledger_kind(label):
                continue
            qid = stable_id(m["surface"], m["sid"], m["ts"], m["text"])
            if qid in seen_ids:
                continue
            seen_ids.add(qid)
            reply, reply_ts, reply_pos, other_user = None, "", None, False
            for p2 in range(pos + 1, len(idxs)):
                r = messages[idxs[p2]]
                if r["role"] == "assistant":
                    reply, reply_ts, reply_pos = r["text"], r["ts"], p2
                    break
                other_user = True
            it = {
                "id": qid, "surface": m["surface"], "sid": m["sid"], "ts": m["ts"],
                "date": (m["ts"] or "")[:10], "kind": label, "reason": reason,
                "text": m["text"][:TEXT_KEEP], "text_len": len(m["text"]),
                "long": len(m["text"]) > SHORT_MAX,
                "reply": (reply or "")[:REPLY_KEEP], "reply_ts": reply_ts,
                "reply_len": len(reply or ""), "no_reply": reply is None,
                "reply_after_other_user": bool(reply is not None and other_user),
                "signals": [], "missed": False,
                "_pos": pos, "_rpos": reply_pos,
            }
            items.append(it)
            by_session_items.setdefault(key, []).append(it)

    n_signal_msgs = 0
    for key, its in by_session_items.items():
        idxs = sessions[key]
        # signal messages: any user message in the session (the signal message may itself be a question)
        for pos, idx in enumerate(idxs):
            m = messages[idx]
            if m["role"] != "user":
                continue
            sigs = find_signals(m["text"])
            if not sigs:
                continue
            n_signal_msgs += 1
            eligible = [q for q in its if q["_pos"] < pos and q["_rpos"] is not None and q["_rpos"] < pos]
            if not eligible:
                continue
            eligible.sort(key=lambda q: q["_pos"])
            targets = {id(eligible[-1]): (eligible[-1], "previous", [])}
            scored = []
            for q in eligible:
                if id(q) in targets:
                    continue
                sc, shared = shared_score(m["text"], q["text"])
                if refers_to(sc, shared):
                    scored.append((sc, q["_pos"], q, shared))
            scored.sort(key=lambda t: (-t[0], -t[1]))
            for sc, _, q, shared in scored[:MAX_REF_EXTRA]:
                targets[id(q)] = (q, "refers-to", shared)
            # the nearest question may also share words; report them for display
            prev_q = eligible[-1]
            targets[id(prev_q)] = (prev_q, "previous", shared_score(m["text"], prev_q["text"])[1])
            for q, why, shared in targets.values():
                for s in sigs:
                    q["signals"].append({
                        "phrase": s["phrase"], "strength": s["strength"], "reason": why,
                        "shared": shared, "ts": m["ts"], "text": james_words(m["text"])[:SIGNAL_KEEP * 2 + 5],
                    })
                q["missed"] = True

    for it in items:
        it.pop("_pos", None)
        it.pop("_rpos", None)
    items.sort(key=lambda q: (q["ts"], q["id"]))
    n_strong = sum(1 for q in items if any(s["strength"] == "strong" for s in q["signals"]))
    stats = {
        "n_user_by_label": by_label,
        "n_ledger": len(items),
        "n_missed": sum(1 for q in items if q["missed"]),
        "n_missed_strong": n_strong,
        "n_signal_messages": n_signal_msgs,
        "n_no_reply": sum(1 for q in items if q["no_reply"]),
    }
    return items, stats


def _atomic_write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as w:
        json.dump(obj, w, ensure_ascii=False, indent=1)
    _replace_retry(tmp, path)


def rebuild(messages=None, path=None):
    """Re-extract from the logs and rewrite ledger_questions.json. Never touches ledger_status.json."""
    if messages is None:
        from modules.log_reader import load_messages
        messages = load_messages()
    items, stats = extract(messages)
    stats["n_messages"] = len(messages)
    stats["n_user_messages"] = sum(1 for m in messages if m["role"] == "user")
    doc = {
        "version": 1,
        "built": datetime.datetime.now().isoformat(timespec="seconds"),
        "missed_signals": list(MISSED_SIGNALS),
        "stats": stats,
        "items": items,
    }
    _atomic_write(path or QUESTIONS_FILE, doc)
    return doc


def load_questions(path=None, build_if_missing=True):
    p = path or QUESTIONS_FILE
    if not os.path.exists(p):
        if not build_if_missing:
            return {"version": 1, "built": "", "stats": {}, "items": []}
        return rebuild(path=p)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# ----------------------------------------------------------------------------------------------
# status marks (James's, never overwritten by a rebuild)

def load_marks(path=None):
    p = path or STATUS_FILE
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("marks", {}) if isinstance(d, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def set_mark(qid, status, note=None, path=None):
    """Store a mark by stable id. status 'unreviewed' removes the mark. Raises ValueError on bad input."""
    if not re.fullmatch(r"[0-9a-f]{40}", qid or ""):
        raise ValueError("bad id")
    if status != DEFAULT_STATUS and status not in STATUSES:
        raise ValueError(f"bad status {status!r}; use one of {STATUSES + (DEFAULT_STATUS,)}")
    p = path or STATUS_FILE
    marks = load_marks(p)
    if status == DEFAULT_STATUS:
        marks.pop(qid, None)
    else:
        marks[qid] = {"status": status, "updated": datetime.datetime.now().isoformat(timespec="seconds")}
        if note:
            marks[qid]["note"] = str(note)[:500]
    _atomic_write(p, {"version": 1, "marks": marks})
    return marks.get(qid, {"status": DEFAULT_STATUS})


def merged_items(questions_path=None, status_path=None):
    doc = load_questions(questions_path)
    marks = load_marks(status_path)
    out = []
    for it in doc.get("items", []):
        x = dict(it)
        mk = marks.get(it["id"])
        x["status"] = mk["status"] if mk else DEFAULT_STATUS
        x["note"] = (mk or {}).get("note", "")
        out.append(x)
    ids = {it["id"] for it in doc.get("items", [])}
    orphans = sum(1 for k in marks if k not in ids)
    return out, doc, orphans


def filter_items(items, status=None, surface=None, date_from=None, date_to=None, text=None, missed=None,
                 strong=None):
    """status: one status or comma list; surface CL/AG; dates YYYY-MM-DD inclusive on the question date;
    text: every word must occur (case-insensitive) in the question, the reply excerpt or a signal;
    missed: True/False (a signal of any strength); strong: True keeps only questions with a strong signal."""
    wanted = {s.strip() for s in status.split(",") if s.strip()} if status else None
    words = [w for w in (text or "").lower().split() if w]
    out = []
    for q in items:
        if wanted and q["status"] not in wanted:
            continue
        if surface and q["surface"] != surface.upper():
            continue
        if date_from and (q["date"] or "") < date_from:
            continue
        if date_to and (q["date"] or "9999") > date_to:
            continue
        if missed is not None and q["missed"] != missed:
            continue
        if strong and not any(s["strength"] == "strong" for s in q["signals"]):
            continue
        if words:
            hay = (q["text"] + "\n" + q["reply"] + "\n" + "\n".join(s["text"] for s in q["signals"])).lower()
            if not all(w in hay for w in words):
                continue
        out.append(q)
    return out


def counts(items):
    c = {s: 0 for s in (DEFAULT_STATUS,) + STATUSES}
    for q in items:
        c[q["status"]] = c.get(q["status"], 0) + 1
    return c


def _one_line(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def to_markdown(items, title="Question Ledger"):
    """Markdown checklist. [x] = answered or not-a-question; [ ] = everything else."""
    lines = [f"# {title}", "", f"{len(items)} item(s).", ""]
    for q in items:
        done = q["status"] in ("answered", "not-a-question")
        flag = " POSSIBLY MISSED" if q["missed"] else ""
        lines.append(f"- [{'x' if done else ' '}] {q['date']} {q['surface']} [{q['status']}]{flag} "
                     f"{_one_line(q['text'], 300)}")
        if q["signals"]:
            s = q["signals"][0]
            lines.append(f"  - later message ({s['ts']}, signal \"{s['phrase']}\"): {_one_line(s['text'], 200)}")
        if q.get("note"):
            lines.append(f"  - note: {_one_line(q['note'], 200)}")
    lines.append("")
    return "\n".join(lines)
