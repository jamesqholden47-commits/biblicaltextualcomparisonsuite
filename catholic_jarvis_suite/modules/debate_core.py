"""Debate threads harvested from the logs (Phase 2, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).

Why: James's debates do not happen in the suite. He pastes the Discord log into a Claude or Antigravity chat and the
help happens there (183 such pastes measured 2026-10-07, against one thread in Did I Cook?). This module collects
them from the logs instead of waiting for them to be re-entered.

Pipeline (all read-only on the logs):
  1. find_snapshots   every user message that parses as a Discord log with James and at least one other speaker
                      (desk_core.parse_log), plus the AI reply that followed it in the same session (the draft).
  2. group            snapshots that share messages are the same debate pasted again as it grew (union-find on
                      message fingerprints; 2+ shared substantive messages = same thread).
  3. merge            one ordered conversation per thread: a message first seen in a later paste is placed after
                      the message that preceded it there.
  4. points           each AI reply is cut into argument points: Discord drop-in code blocks if it has them, else
                      its headed sections (the analysis before the first heading is not a point), else its long
                      paragraphs.
  5. posted/unsent    each point is matched (desk_core.match_drafts) against James's messages that first appear in a
                      LATER paste. Rule 15: a point counts as posted only when a later log shows it. A point never
                      seen posted stays in the payload until James drops it; a newer draft never removes an older
                      point (Rules 15.2 and 15.5).

Records only arguments. Participant names are labels on threads James was in; there is no per-person profile.
Data: data/debate_harvest.json (cache, keyed by the log fingerprint) and data/debate_marks.json (James's drops,
titles, hidden threads).
"""
import hashlib
import json
import os
import re
import threading
import time
from collections import Counter, defaultdict

from modules import desk_core, log_reader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HARVEST_FILE = os.path.join(DATA_DIR, "debate_harvest.json")
MARKS_FILE = os.path.join(DATA_DIR, "debate_marks.json")
VERSION = 4

MIN_PASTE_CHARS = 300
MIN_FP_CHARS = 25          # shorter messages ("lol", "ok") are too common to prove two pastes are the same debate
MIN_SHARED = 2
MIN_POINT_WORDS = 12
LIVE_STATES = ("unsent", "partial", "drawn on")   # still owed to the debate: carried forward until James drops them

_lock = threading.Lock()


# ----------------------------------------------------------------------------- small helpers
def _read_json(p, default=None):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _write_json(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)
    for k in range(8):
        try:
            os.replace(tmp, p)
            return
        except PermissionError:
            time.sleep(0.05 * (k + 1))
    os.replace(tmp, p)


def _h(s, n=12):
    return hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:n]


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", (s or "").lower())).strip()


def fingerprint(m):
    return _norm(m.get("author")) + "|" + _norm(m.get("text"))[:80]


# ----------------------------------------------------------------------------- 1. snapshots
def is_debate_paste(text, handles=None):
    if not text or len(text) < MIN_PASTE_CHARS:
        return None
    p = desk_core.parse_log(text, handles)
    ms = p["messages"]
    if len(ms) >= 4 and len({m["author"] for m in ms}) >= 2 and p["stats"]["n_james"] >= 1:
        return p
    return None


def find_snapshots(messages, handles=None):
    """messages: log_reader.load_messages() shape. Returns snapshots in time order."""
    by_sid = defaultdict(list)
    for m in messages:
        by_sid[(m["surface"], m["sid"])].append(m)
    snaps, by_sha = [], {}
    for (surface, sid), ms in by_sid.items():
        for k, m in enumerate(ms):
            if m["role"] != "user":
                continue
            p = is_debate_paste(m["text"], handles)
            if not p:
                continue
            reply = []
            for n in ms[k + 1:]:
                if n["role"] == "user":
                    break
                if n["text"].strip():
                    reply.append(n["text"])
            sha = _h(m["text"], 16)
            draft = {"surface": surface, "sid": sid, "ts": m["ts"], "text": "\n\n".join(reply)}
            if sha in by_sha:                      # the same log pasted again elsewhere: one snapshot, two replies
                by_sha[sha]["drafts"].append(draft)
                continue
            # James's own words around the log (the instruction he typed with it)
            snap = {"id": sha, "surface": surface, "sid": sid, "ts": m["ts"], "chars": len(m["text"]),
                    "messages": [{"author": x["author"], "is_james": x["is_james"], "text": x["text"],
                                  "time": x.get("time") or ""} for x in p["messages"]],
                    "preamble": " ".join(p.get("preamble") or [])[:600],
                    "drafts": [draft]}
            by_sha[sha] = snap
            snaps.append(snap)
    snaps.sort(key=lambda s: s["ts"])
    return snaps


# ----------------------------------------------------------------------------- 2. grouping
SESSION_GAP_MIN = 90       # consecutive pastes in one AI session this close together ...


def _parts(s):
    return {_norm(m["author"]) for m in s["messages"] if not m["is_james"]}


def _minutes(a, b):
    from datetime import datetime
    f = lambda x: datetime.fromisoformat(x.replace("Z", "+00:00"))
    return abs((f(b) - f(a)).total_seconds()) / 60


def group(snaps, joins=(), separate=()):
    """Snapshots -> threads. Joined when (a) they share 2+ substantive messages (the same log pasted again as it
    grew), or (b) they are consecutive pastes in one AI session, at most SESSION_GAP_MIN apart, sharing 2+ other
    participants (1 when either paste has only one or two others): new-messages-only pastes of one conversation.
    James's own decisions override: `joins` = [[snap_id, snap_id], ...], `separate` = snap ids that start a new
    thread (rule (b) never links them to the paste before)."""
    parent = list(range(len(snaps)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    owners = defaultdict(set)              # fingerprint -> snapshot indexes
    for i, s in enumerate(snaps):
        for m in s["messages"]:
            if len(_norm(m["text"])) >= MIN_FP_CHARS:
                owners[fingerprint(m)].add(i)
    shared = Counter()
    for idxs in owners.values():
        idxs = sorted(idxs)
        for a in range(len(idxs)):
            for b in range(a + 1, len(idxs)):
                shared[(idxs[a], idxs[b])] += 1
    for (a, b), n in shared.items():
        if n >= MIN_SHARED:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
    sep = set(separate)
    by_session = defaultdict(list)
    for i, sn in enumerate(snaps):
        by_session[(sn["surface"], sn["sid"])].append(i)
    for idxs in by_session.values():
        idxs.sort(key=lambda i: snaps[i]["ts"])
        for x, y in zip(idxs, idxs[1:]):
            if snaps[y]["id"] in sep:
                continue
            pa, pb = _parts(snaps[x]), _parts(snaps[y])
            need = 1 if min(len(pa), len(pb)) <= 2 else 2
            if len(pa & pb) >= need and _minutes(snaps[x]["ts"], snaps[y]["ts"]) <= SESSION_GAP_MIN:
                rx, ry = find(x), find(y)
                if rx != ry:
                    parent[ry] = rx
    pos = {sn["id"]: i for i, sn in enumerate(snaps)}
    for a_id, b_id in joins:
        if a_id in pos and b_id in pos:
            ra, rb = find(pos[a_id]), find(pos[b_id])
            if ra != rb:
                parent[rb] = ra
    groups = defaultdict(list)
    for i in range(len(snaps)):
        groups[find(i)].append(snaps[i])
    return [sorted(g, key=lambda s: s["ts"]) for g in groups.values()]


# ----------------------------------------------------------------------------- 3. merge
def merge(snaps):
    """One ordered message list for a thread. Each message carries first_snap: the paste it first appeared in."""
    merged, index = [], {}
    for k, s in enumerate(snaps):
        fps = [fingerprint(m) for m in s["messages"]]
        prev = None
        for j, m in enumerate(s["messages"]):
            fp = fps[j]
            if fp in index:
                prev = index[fp]
                continue
            node = dict(m, first_snap=k, fp=fp)
            if prev is not None:
                pos = merged.index(prev) + 1                 # right after what preceded it in this paste
            else:
                nxt = next((index[f] for f in fps[j + 1:] if f in index), None)
                pos = merged.index(nxt) if nxt is not None else len(merged)   # before what follows it, else at the end
            merged.insert(pos, node)
            index[fp] = node
            prev = node
    for i, m in enumerate(merged):
        m["i"] = i
    return merged


# ----------------------------------------------------------------------------- 4. points
FENCE_RE = re.compile(r"```[\w-]*\n(.*?)```", re.S)
HEAD_RE = re.compile(r"(?m)^(#{2,6})\s+(.+?)\s*$")


def _words(s):
    return len(re.findall(r"\w+", s or ""))


def extract_points(reply):
    """Argument points of one AI reply: drop-in code blocks, else headed sections, else long paragraphs."""
    reply = (reply or "").replace("\r\n", "\n")
    blocks = [b.strip() for b in FENCE_RE.findall(reply) if _words(b) >= MIN_POINT_WORDS]
    if blocks:
        out = []
        for b in blocks:
            # the heading just above a block names it ("DISCORD DROP-IN BLOCK 1: ...")
            at = reply.find(b)
            heads = HEAD_RE.findall(reply[:at])
            title = re.sub(r"[*_`#]", "", heads[-1][1]).strip() if heads else b.split("\n", 1)[0][:80]
            out.append({"kind": "block", "title": title[:120], "text": b})
        return out
    heads = list(HEAD_RE.finditer(reply))
    if heads:
        out = []
        for j, h in enumerate(heads):
            end = heads[j + 1].start() if j + 1 < len(heads) else len(reply)
            body = reply[h.end():end].strip().strip("-").strip()
            if _words(body) >= MIN_POINT_WORDS:
                out.append({"kind": "section", "title": re.sub(r"[*_`#]", "", h.group(2)).strip()[:120], "text": body})
        if out:
            return out
    paras = [p.strip() for p in re.split(r"\n\s*\n", reply) if _words(p) >= 25]
    return [{"kind": "paragraph", "title": re.sub(r"[*_`#>]", "", p.split("\n", 1)[0])[:80], "text": p} for p in paras]


def point_role(pt):
    """'draft' = text meant to be posted: a drop-in code block, a section that is mostly blockquoted reply text,
    or one addressed to someone (@name). 'notes' = the AI's analysis addressed to James ("He dodged...", "Notice...").
    Only drafts count as owed; notes stay visible and travel in the brief as background (nothing is discarded).
    Calibrated 2026-10-07 on a sample of real points: coaching sections had no blockquotes; drafts were quoted."""
    if pt["kind"] == "block":
        return "draft"
    lines = [ln for ln in pt["text"].split("\n") if ln.strip()]
    if not lines:
        return "notes"
    quoted = sum(1 for ln in lines if ln.lstrip().startswith(">"))
    if quoted / len(lines) >= 0.4:
        return "draft"
    first = re.sub(r"^[>\s*_]+", "", lines[0])
    if first.startswith("@"):
        return "draft"
    return "notes"


STATE_OF = {"sent_verbatim": "posted", "sent_adapted": "adapted", "partial": "partial", "unsent": "unsent"}
DRAWN_ON = 0.5     # share of a later James message (12+ words) found in this point in runs of 3+ words.
                   # Calibrated 2026-10-07 on the real threads: >=0.55 were genuine condensed posts, <=0.37 a shared quote or noise.


def drawn_on(point_text, james_msgs):
    """How much of James's best later message was taken from this point: (share, message index)."""
    import difflib
    a = desk_core.tok(point_text)
    best = (0.0, None)
    if not a:
        return best
    aset = set(a)
    for m in james_msgs:
        b = desk_core.tok(m["text"])
        if len(b) < 12 or not (aset & set(b)):
            continue
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        share = sum(bl.size for bl in sm.get_matching_blocks() if bl.size >= 3) / len(b)
        if share > best[0]:
            best = (share, m["i"])
    return best


def score_points(snaps, merged):
    """Every point of every draft, with its posted state against James's LATER messages."""
    points = []
    for k, s in enumerate(snaps):
        later = [m for m in merged if m["first_snap"] > k]
        later_james = [m for m in later if m["is_james"]]
        for d in s["drafts"]:
            for n, pt in enumerate(extract_points(d["text"])):
                pid = _h(s["id"] + d["ts"] + pt["text"], 12)
                rec = {"id": pid, "snap": k, "ts": d["ts"], "surface": d["surface"], "kind": pt["kind"], "role": point_role(pt),
                       "title": pt["title"], "text": pt["text"], "words": _words(pt["text"])}
                if not later:
                    rec.update(state="unsent", why="no later paste yet, so nothing shows it posted")
                elif not later_james:
                    rec.update(state="unsent", why="later pastes show no message from James")
                else:
                    r = desk_core.match_drafts([{"id": pid, "text": pt["text"]}], later)[0]
                    rec["state"] = STATE_OF.get(r["state"], r["state"])
                    if r["state"] == "partial":
                        rec["unsent_text"] = r["unsent_text"]
                    if r.get("best") and r["best"].get("messages"):
                        rec["matched_messages"] = r["best"]["messages"]
                    if rec["state"] == "unsent":
                        used, mi = drawn_on(pt["text"], later_james)
                        if used >= DRAWN_ON:
                            rec.update(state="drawn on", drawn=round(used, 2), matched_messages=[mi],
                                       why="a later message of James's takes most of its words from this point; the rest may be unsent")
                points.append(rec)
    return points


# ----------------------------------------------------------------------------- 5. threads
STOP_EXTRA = set("""like just know think get got one really would could also even said say says dont im youre thats
yeah yes lol lmao bro dude ok okay well thing things people way make made see good right want need going much many
still mean literally actually never ever every something anything nothing because there""".split())


def topic_words(merged, names, n=4):
    c = Counter()
    name_toks = set()
    for nm in names:
        name_toks.update(_norm(nm).split())
    for m in merged:
        for t in desk_core._content(desk_core.tok(m["text"])):
            if len(t) > 3 and t not in STOP_EXTRA and t not in name_toks and not t.isdigit():
                c[t] += 1
    return [w for w, k in c.most_common(n) if k >= 3]


def build_thread(snaps):
    merged = merge(snaps)
    others = Counter(m["author"] for m in merged if not m["is_james"])
    names = list(others) + [m["author"] for m in merged if m["is_james"]][:1]
    points = score_points(snaps, merged)
    words = topic_words(merged, names)
    tid = _h(snaps[0]["id"] + (merged[0]["fp"] if merged else ""), 10)
    latest = desk_core.their_latest(merged) if merged else None
    states = Counter(p["state"] for p in points)
    return {
        "id": tid,
        "auto_title": " · ".join(words) if words else "debate with " + ", ".join(list(others)[:2]),
        "participants": [{"name": a, "messages": n} for a, n in others.most_common()],
        "first_ts": snaps[0]["ts"], "last_ts": snaps[-1]["ts"],
        "surfaces": sorted({s["surface"] for s in snaps}),
        "n_snapshots": len(snaps), "n_messages": len(merged), "n_james": sum(1 for m in merged if m["is_james"]),
        "snapshots": [{"id": s["id"], "ts": s["ts"], "surface": s["surface"], "sid": s["sid"], "chars": s["chars"],
                       "n_messages": len(s["messages"]), "preamble": s["preamble"],
                       "n_drafts": len(s["drafts"])} for s in snaps],
        "messages": [{k: m[k] for k in ("i", "author", "is_james", "text", "time", "first_snap")} for m in merged],
        "points": points,
        "point_states": dict(states),
        "their_latest": ({"author": latest["author"], "james_posted_since": latest["james_posted_since"],
                          "messages": [m["i"] for m in latest["messages"]]} if latest else None),
    }


def _log_fingerprint():
    return log_reader.source_fingerprint()


_mem = {"data": None, "checked": 0.0}
RECHECK_SECONDS = 20       # how often a request re-checks the ~2,000 log files for changes (0.5 s per check)


def harvest(force=False, messages=None):
    """Build (or load the cached) thread list. Re-harvests only when the logs or James's join/split marks changed."""
    if not force and messages is None and _mem["data"] is not None and time.time() - _mem["checked"] < RECHECK_SECONDS:
        return _mem["data"]
    out = _harvest(force, messages)
    if messages is None:
        _mem.update(data=out, checked=time.time())
    return out


def _harvest(force=False, messages=None):
    with _lock:
        marks = _marks()
        mkey = _h(json.dumps([marks["joins"], sorted(marks["separate"])], sort_keys=True), 10)
        fp = None if messages is not None else _log_fingerprint() + "|" + mkey
        if not force and messages is None:
            c = _read_json(HARVEST_FILE)
            if c and c.get("fingerprint") == fp and c.get("version") == VERSION:
                return c
        t0 = time.time()
        msgs = messages if messages is not None else log_reader.load_messages()
        snaps = find_snapshots(msgs)
        threads = [build_thread(g) for g in group(snaps, marks["joins"], marks["separate"])]
        threads.sort(key=lambda t: t["last_ts"], reverse=True)
        out = {"version": VERSION, "fingerprint": fp, "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "seconds": round(time.time() - t0, 1), "n_snapshots": len(snaps),
               "n_threads": len(threads), "threads": threads}
        if messages is None:
            _write_json(HARVEST_FILE, out)
        return out


# ----------------------------------------------------------------------------- marks (James's decisions)
def _marks():
    m = _read_json(MARKS_FILE, {}) or {}
    m.setdefault("version", 1)
    for k in ("dropped", "titles", "hidden"):
        m.setdefault(k, {})
    m.setdefault("joins", [])
    m.setdefault("separate", [])
    return m


def _apply_marks(t, marks):
    t = dict(t)
    t["title"] = marks["titles"].get(t["id"]) or t["auto_title"]
    t["hidden"] = bool(marks["hidden"].get(t["id"]))
    pts = []
    for p in t.get("points", []):
        p = dict(p)
        if p["id"] in marks["dropped"]:
            p["dropped"] = marks["dropped"][p["id"]]
        pts.append(p)
    t["points"] = pts
    live = [p for p in pts if p["state"] in LIVE_STATES and not p.get("dropped") and p.get("role") == "draft"]
    t["unsent_points"] = len(live)
    t["unsent_notes"] = sum(1 for p in pts if p["state"] in LIVE_STATES and not p.get("dropped") and p.get("role") != "draft")
    return t


def list_threads(include_hidden=False):
    h = harvest()
    marks = _marks()
    out = []
    for t in h["threads"]:
        t = _apply_marks(t, marks)
        if t["hidden"] and not include_hidden:
            continue
        out.append({k: t[k] for k in ("id", "title", "auto_title", "participants", "first_ts", "last_ts", "surfaces",
                                      "n_snapshots", "n_messages", "n_james", "point_states", "unsent_points",
                                      "unsent_notes", "hidden")})
    return {"built_at": h["built_at"], "seconds": h["seconds"], "n_snapshots": h["n_snapshots"],
            "n_threads": h["n_threads"], "threads": out}


def get_thread(tid):
    for t in harvest()["threads"]:
        if t["id"] == tid:
            return _apply_marks(t, _marks())
    raise KeyError(tid)


def join(snap_a, snap_b):
    """James: these two pastes are the same debate."""
    with _lock:
        m = _marks()
        if [snap_a, snap_b] not in m["joins"]:
            m["joins"].append([snap_a, snap_b])
        m["separate"] = [x for x in m["separate"] if x not in (snap_a, snap_b)]
        _write_json(MARKS_FILE, m)
    _mem["checked"] = 0.0          # the marks changed: the next read regroups


def split_at(snap_id):
    """James: a new debate starts at this paste (undoes the same-session rule and any join that crosses it)."""
    with _lock:
        m = _marks()
        if snap_id not in m["separate"]:
            m["separate"].append(snap_id)
        m["joins"] = [j for j in m["joins"] if snap_id not in j]
        _write_json(MARKS_FILE, m)
    _mem["checked"] = 0.0          # the marks changed: the next read regroups


def set_mark(kind, key, value):
    if kind not in ("dropped", "titles", "hidden"):
        raise ValueError(kind)
    with _lock:
        m = _marks()
        if value in (None, False, ""):
            m[kind].pop(key, None)
        else:
            m[kind][key] = value
        _write_json(MARKS_FILE, m)
    return m[kind].get(key)


# ----------------------------------------------------------------------------- brief for the AI
def brief(tid, socratic=False, tail=40):
    t = get_thread(tid)
    msgs = t["messages"]
    lines = [f"# Debate state: {t['title']}",
             f"Harvested from {t['n_snapshots']} pasted log(s), {t['first_ts'][:10]} to {t['last_ts'][:10]}. "
             f"Participants: " + ", ".join(p["name"] for p in t["participants"][:6]) + ".",
             "",
             "## Rules for this reply (CLAUDE.md / GEMINI.md Rule 15)",
             "- Draft against THIS state, not against your last answer. A point counts as posted only when the log shows it.",
             "- Carry EVERY unsent point below forward unless James dropped it. A new finding is ADDED to the stack, never substituted for it.",
             "- Concede first: say what the opponent has right before answering.",
             "- Mark every factual claim: checked against a named source (with locator), or 'from memory, check before posting'.",
             "- Discord: keep each message under 2,000 characters; split longer replies into numbered posts."]
    if socratic:
        lines += ["- Rule 17 (Socratic / bottom-up): do not lecture from sources James has not read. Ask the opponent for the exact "
                  "passage, the definition, and how the conclusion follows. Short and conversational."]
    lines += ["", f"## The conversation as posted (last {min(tail, len(msgs))} of {len(msgs)} messages)"]
    for m in msgs[-tail:]:
        who = "JAMES" if m["is_james"] else m["author"]
        lines.append(f"**{who}:** {m['text'].strip()}")
    tl = t.get("their_latest")
    if tl:
        lines += ["", f"## Their latest (from {tl['author']}; James has posted {tl['james_posted_since']} message(s) since)"]
        for i in tl["messages"]:
            lines.append("> " + msgs[i]["text"].strip().replace("\n", "\n> "))
    owed = [p for p in t["points"] if p["state"] in LIVE_STATES and not p.get("dropped")]
    live = [p for p in owed if p.get("role") == "draft"]
    notes = [p for p in owed if p.get("role") != "draft"]
    lines += ["", f"## Unsent points from earlier drafts ({len(live)}) - carry these forward"]
    for p in live:
        body = p.get("unsent_text") or p["text"]
        lines += [f"### {p['title']}  ({p['ts'][:10]}, {p['state']})", body.strip(), ""]
    if notes:
        lines += [f"## Earlier analysis notes ({len(notes)}) - background, not drafts; use what still applies"]
        for p in notes:
            body = (p.get("unsent_text") or p["text"]).strip()
            lines += [f"### {p['title']}  ({p['ts'][:10]})", body if len(body) <= 1200 else body[:1200] + " [...]", ""]
    done = [p for p in t["points"] if p["state"] in ("posted", "adapted")]
    if done:
        lines += ["## Already posted by James (do not repeat)"] + [f"- {p['title']} ({p['state']})" for p in done]
    return "\n".join(lines)
