"""Argument packs and objection drills (Phase 4, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).

PACKS — one per recurring debate topic, gathered from what already exists:
  seeds      the 14 Arena cards and 6 Pope Tools cards whose text is on the topic (their audited tags kept)
  posted     James's own substantive posts (40+ words) in debates on the topic — tagged [S]: his claims, not verified
  owed       drafted replies on the topic never seen posted (from the Threads harvest)
  dossiers   Loose Ends SUBJECT documents whose title is on the topic (opened in Files)
  chapters   Volumes chapters whose title is on the topic (final ones marked)
Rule: no entry shows [V] unless it carries a source file that exists on disk or a URL (visible_tag()).

DRILL — real objections from the harvested debates as flashcards: an opponent's message (25+ words, with a
factual-looking claim or a question) on the front; James's next reply in that debate on the back, if he made one.
Every card links back to its thread and message. Opponents' names are not shown. Scheduling is SM-2 (as Anki),
stored in data/drill_state.json. Topics are editable: create data/debate_topics.json with the same shape as TOPICS.
"""
import hashlib
import json
import os
import re
import threading
import time
from collections import Counter

from modules import debate_core, desk_core

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TOPICS_FILE = os.path.join(DATA_DIR, "debate_topics.json")
DRILL_FILE = os.path.join(DATA_DIR, "drill_state.json")

TOPICS = [
    {"id": "saints", "title": "Saints and intercession", "keywords": ["saint", "saints", "intercession", "intercede", "intercessor",
        "pray to", "praying to", "prayers to", "invocation", "invoke", "departed", "cloud of witnesses", "communion of saints", "one mediator"]},
    {"id": "mary", "title": "Mary", "keywords": ["mary", "marian", "theotokos", "immaculate", "assumption", "virgin", "mother of god",
        "mediatrix", "rosary", "perpetual virginity", "brothers of jesus"]},
    {"id": "papacy", "title": "Peter and the papacy", "keywords": ["pope", "papal", "papacy", "peter", "primacy", "keys", "rome", "roman see",
        "infallible", "infallibility", "vatican i", "hormisdas", "successor of peter", "bishop of rome", "pastor aeternus"]},
    {"id": "scripture", "title": "Scripture, canon and tradition", "keywords": ["sola scriptura", "scripture alone", "canon", "deuterocanon",
        "deuterocanonical", "apocrypha", "tradition", "magisterium", "septuagint", "maccabees", "sirach", "bible alone", "oral tradition"]},
    {"id": "baptism", "title": "Baptism and regeneration", "keywords": ["baptism", "baptize", "baptized", "baptised", "regeneration",
        "born again", "infant baptism", "baptismal", "born of water", "credobaptism"]},
    {"id": "eucharist", "title": "The Eucharist and the Mass", "keywords": ["eucharist", "real presence", "transubstantiation", "the mass",
        "holy communion", "body and blood", "sacrifice of the mass", "john 6", "lord's supper"]},
    {"id": "justification", "title": "Faith, works and justification", "keywords": ["justification", "justified", "faith alone", "sola fide",
        "works", "grace", "pistis", "imputed", "imputation", "dikaio", "merit", "james 2", "penal substitution"]},
    {"id": "salvation", "title": "Hell, salvation and the last things", "keywords": ["hell", "damnation", "damned", "universalism",
        "universal salvation", "apokatastasis", "salvation", "purgatory", "eternal punishment", "judgment", "heaven", "rapture", "eschatology"]},
    {"id": "trinity", "title": "The Trinity and Christ", "keywords": ["trinity", "trinitarian", "godhead", "deity of christ", "divinity of christ",
        "oneness", "unitarian", "homoousios", "hypostatic", "three persons", "modalism", "arian", "christology"]},
    {"id": "east", "title": "Orthodoxy and the East", "keywords": ["orthodox", "orthodoxy", "filioque", "patriarch", "patriarchs", "schism",
        "eastern", "byzantine", "pentarchy", "photius", "palamas", "ecumenical patriarch", "great schism"]},
    {"id": "images", "title": "Icons, images and bowing", "keywords": ["icon", "icons", "images", "statue", "statues", "idol", "idolatry",
        "bowing", "bow down", "veneration", "venerate", "latria", "dulia", "hishtachavah", "graven image"]},
    {"id": "councils", "title": "Creeds and councils", "keywords": ["creed", "creeds", "council", "councils", "nicaea", "chalcedon",
        "ecumenical council", "synod", "anathema", "ephesus", "constantinople"]},
    {"id": "reason", "title": "Atheism, science and reason", "keywords": ["atheist", "atheism", "atheists", "science", "scientific", "evidence",
        "empirical", "existence of god", "god exists", "miracle", "miracles", "epistemology", "testimony", "naturalism", "determinism", "free will"]},
    {"id": "morality", "title": "Moral questions", "keywords": ["death penalty", "capital punishment", "abortion", "contraception",
        "homosexual", "homosexuality", "transgender", "gender", "divorce", "just war", "euthanasia", "sexual"]},
    {"id": "history", "title": "History and its myths", "keywords": ["inquisition", "crusade", "crusades", "galileo", "black legend",
        "reformation", "luther", "medieval", "constantine", "conquistador", "witch"]},
    {"id": "protestant", "title": "Protestant and Anglican traditions", "keywords": ["baptist", "baptists", "anglican", "anglicanism", "calvin",
        "calvinist", "lutheran", "reformed", "evangelical", "pentecostal", "trail of blood", "presbyterian", "methodist"]},
]

POSTED_MIN_WORDS = 40
OBJECTION_MIN_WORDS = 25
_lock = threading.Lock()
_cache = {"key": None, "data": None}


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


def topics():
    t = _read_json(TOPICS_FILE)
    return t if isinstance(t, list) and t else TOPICS


def _patterns(tp):
    out = []
    for k in tp["keywords"]:
        k = k.lower()
        out.append(re.compile(r"\b" + re.escape(k) + (r"\b" if k[-1].isalnum() else ""), re.I))
    return out


_PAT = {}


def topic_hits(text, tp):
    pats = _PAT.get(tp["id"])
    if pats is None or len(pats) != len(tp["keywords"]):
        pats = _PAT[tp["id"]] = _patterns(tp)
    return sum(len(p.findall(text or "")) for p in pats)


def topics_of(text, min_hits=1):
    scores = {tp["id"]: topic_hits(text, tp) for tp in topics()}
    return {k: v for k, v in scores.items() if v >= min_hits}


def visible_tag(tag, source_path=None, source_url=None):
    """A [V] is shown only when its source can be opened: a file that exists, or a URL. Otherwise [S]."""
    tag = (tag or "[S]").strip()
    if tag.upper().startswith("[V"):
        if (source_path and os.path.exists(source_path)) or (source_url and re.match(r"^https?://", source_url)):
            return tag
        return "[S]"
    return tag


def _words(s):
    return len(re.findall(r"\w+", s or ""))


def _id(*parts):
    return hashlib.sha1("|".join(parts).encode("utf-8", "replace")).hexdigest()[:14]


# ----------------------------------------------------------------------------- inputs
def _seed_cards():
    out = []
    for c in _read_json(os.path.join(DATA_DIR, "debate_battle_cards.json"), []) or []:
        text = " ".join(str(c.get(k) or "") for k in ("topic", "charge", "concession", "fatal_counter_fact", "copy_paste_text"))
        # every field the retired Arena tab showed travels with the card, so retiring the tab hides nothing
        out.append({"kind": "card", "origin": "Arena card", "id": c.get("id"), "title": c.get("topic") or c.get("id"),
                    "body": c.get("fatal_counter_fact") or c.get("copy_paste_text") or "", "concession": c.get("concession") or "",
                    "copy": c.get("copy_paste_text") or "", "locator": c.get("source_locator") or "",
                    "front": c.get("front") or "", "target": c.get("target") or "", "charge": c.get("charge") or "",
                    "proof": c.get("proof_text") or "", "soundbite": c.get("verbal_soundbite_15s") or "",
                    "audit_note": c.get("audit_note") or "",
                    "tag": visible_tag(c.get("audited_tag") or c.get("provenance_tag"), c.get("source_path"), c.get("source_url")),
                    "_text": text})
    for d in _read_json(os.path.join(DATA_DIR, "defeaters.json"), []) or []:
        text = " ".join(str(d.get(k) or "") for k in ("title", "category", "quote", "body", "copy_text"))
        claims = [{"text": x.get("text", ""), "tag": visible_tag(x.get("tag"), x.get("source_path"), x.get("source_url"))}
                  for x in (d.get("claims") or []) if isinstance(x, dict)]
        out.append({"kind": "card", "origin": "Pope Tools card", "id": d.get("id"), "title": d.get("title") or d.get("id"),
                    "body": d.get("quote") or "", "long": d.get("body") or "", "original": d.get("original_text") or "",
                    "claims": claims, "category": d.get("category") or "", "concession": "", "copy": d.get("copy_text") or "",
                    "locator": d.get("source_locator") or "", "audit_note": d.get("audit_note") or "",
                    "tag": visible_tag(d.get("provenance_tag"), d.get("source_path"), d.get("source_url")), "_text": text})
    return out


def _dossiers():
    reg = _read_json(os.path.join(DATA_DIR, "loose_registry.json"), {}) or {}
    return [d for d in reg.get("docs", []) if d.get("kind") == "SUBJECT"]


def _chapters():
    try:
        from modules import books_core
        p = books_core.load_plan(build_if_missing=False)
    except Exception:  # noqa: BLE001
        p = None
    out = []
    for v in (p or {}).get("volumes", []):
        for c in v["chapters"]:
            out.append({"id": c["id"], "title": c["title"], "volume": v["id"], "volume_title": v.get("title", ""),
                        "state": c.get("state", ""), "words": c.get("words", 0)})
    return out


# ----------------------------------------------------------------------------- build
def _thread_topics(t):
    text = " ".join(m["text"] for m in t["messages"])
    sc = topics_of(text, 1)
    if not sc:
        return {}
    top = max(sc.values())
    return {k: v for k, v in sc.items() if v >= max(5, 0.3 * top)}


def build():
    h = debate_core.harvest()
    reg_m = _mtime(os.path.join(DATA_DIR, "loose_registry.json"))
    key = (h.get("built_at"), h.get("fingerprint"), reg_m, json.dumps(topics(), sort_keys=True)[:2000])
    with _lock:
        if _cache["key"] == key:
            return _cache["data"]
        t0 = time.time()
        marks = debate_core._marks()
        threads = [debate_core._apply_marks(t, marks) for t in h["threads"]]
        seeds, dossiers, chapters = _seed_cards(), _dossiers(), _chapters()
        tps = topics()
        thread_topics = {t["id"]: _thread_topics(t) for t in threads}
        packs = []
        for tp in tps:
            ths = sorted([t for t in threads if tp["id"] in thread_topics[t["id"]]],
                         key=lambda t: thread_topics[t["id"]][tp["id"]], reverse=True)
            posted, owed = [], []
            for t in ths:
                for m in t["messages"]:
                    if m["is_james"] and _words(m["text"]) >= POSTED_MIN_WORDS and topic_hits(m["text"], tp):
                        posted.append({"kind": "posted", "id": _id(t["id"], str(m["i"])), "text": m["text"],
                                       "thread": t["id"], "thread_title": t["title"], "msg": m["i"],
                                       "date": t["snapshots"][m["first_snap"]]["ts"][:10], "tag": "[S]",
                                       "locator": f"your post in “{t['title']}”",
                                       "hits": topic_hits(m["text"], tp)})
                for p in t["points"]:
                    if (p["state"] in debate_core.LIVE_STATES and not p.get("dropped") and p.get("role") == "draft"
                            and topic_hits(p["text"], tp)):
                        owed.append({"kind": "owed", "id": p["id"], "title": p["title"], "thread": t["id"],
                                     "thread_title": t["title"], "date": p["ts"][:10], "words": p["words"]})
            posted.sort(key=lambda x: (x["hits"], _words(x["text"])), reverse=True)
            sd = [dict({k: v for k, v in s.items() if k != "_text"}, hits=topic_hits(s["_text"], tp)) for s in seeds]
            sd = sorted([s for s in sd if s["hits"] >= 2], key=lambda s: s["hits"], reverse=True)
            ds = []
            for d in dossiers:
                hits = topic_hits((d.get("title") or "") + " " + os.path.basename(d["path"]).replace("_", " "), tp)
                if hits:
                    tg = d.get("tags") or {}
                    ds.append({"kind": "dossier", "path": d["path"], "title": d.get("title") or os.path.basename(d["path"]),
                               "words": d.get("words"), "tags": tg, "integrated": bool(d.get("integrated_into")), "hits": hits})
            ds.sort(key=lambda d: (d["hits"], d.get("words") or 0), reverse=True)
            # the chapter's own title only: a volume title ("...and the Papacy") would pull in its every chapter
            ch = [dict(c, hits=topic_hits(c["title"], tp)) for c in chapters]
            ch = sorted([c for c in ch if c["hits"]], key=lambda c: (c["state"] == "final", c["hits"], c["words"]), reverse=True)
            packs.append({"id": tp["id"], "title": tp["title"], "keywords": tp["keywords"],
                          "debates": [{"id": t["id"], "title": t["title"], "last_ts": t["last_ts"], "unsent_points": t["unsent_points"],
                                       "score": thread_topics[t["id"]][tp["id"]]} for t in ths],
                          "seeds": sd, "posted": posted[:25], "n_posted": len(posted), "owed": owed,
                          "dossiers": ds[:20], "n_dossiers": len(ds), "chapters": ch[:15], "n_chapters": len(ch)})
        # every seed card must live in some pack (the Arena and Pope Tools tabs are retired into Packs):
        # a card that met no topic's bar of 2 hits goes to its best topic, or the first pack if it hits none
        placed = {s["id"] for p in packs for s in p["seeds"]}
        for s in seeds:
            if s["id"] in placed:
                continue
            best = max(tps, key=lambda tp: topic_hits(s["_text"], tp))
            target = next(p for p in packs if p["id"] == best["id"])
            target["seeds"].append(dict({k: v for k, v in s.items() if k != "_text"}, hits=topic_hits(s["_text"], best), placed="best match"))
        cards = _objection_cards(threads, thread_topics)
        data = {"built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "seconds": round(time.time() - t0, 1),
                "packs": packs, "cards": cards}
        _cache.update(key=key, data=data)
        return data


def _mtime(p):
    try:
        return os.path.getmtime(p)
    except OSError:
        return 0


def _objection_cards(threads, thread_topics):
    cards, seen = [], set()
    for t in threads:
        msgs = t["messages"]
        for m in msgs:
            if m["is_james"] or _words(m["text"]) < OBJECTION_MIN_WORDS:
                continue
            claims = desk_core.extract_claims(m["text"])
            if not claims and "?" not in m["text"]:
                continue
            key = re.sub(r"\W+", " ", m["text"].lower()).strip()[:200]
            if key in seen:
                continue
            seen.add(key)
            answer = None
            for n in msgs[m["i"] + 1:m["i"] + 6]:
                if n["is_james"] and _words(n["text"]) >= 8:
                    answer = n
                    break
            sc = topics_of(m["text"])
            topic = max(sc, key=sc.get) if sc else (max(thread_topics[t["id"]], key=thread_topics[t["id"]].get)
                                                      if thread_topics[t["id"]] else "other")
            cards.append({"id": _id(t["id"], key), "thread": t["id"], "thread_title": t["title"], "msg": m["i"],
                          "date": t["snapshots"][m["first_snap"]]["ts"][:10], "topic": topic, "front": m["text"],
                          "answer": answer["text"] if answer else None, "answer_msg": answer["i"] if answer else None,
                          "n_claims": len(claims)})
    return cards


def list_packs():
    d = build()
    return {"built_at": d["built_at"], "seconds": d["seconds"], "n_cards": len(d["cards"]),
            "packs": [{"id": p["id"], "title": p["title"], "n_debates": len(p["debates"]), "n_seeds": len(p["seeds"]),
                       "n_posted": p["n_posted"], "n_owed": len(p["owed"]), "n_dossiers": p["n_dossiers"],
                       "n_chapters": p["n_chapters"],
                       "n_cards": sum(1 for c in d["cards"] if c["topic"] == p["id"])} for p in d["packs"]]}


def get_pack(pid):
    for p in build()["packs"]:
        if p["id"] == pid:
            return p
    raise KeyError(pid)


# ----------------------------------------------------------------------------- drill (SM-2)
def _drill_state():
    s = _read_json(DRILL_FILE, {}) or {}
    s.setdefault("version", 1)
    s.setdefault("cards", {})
    s.setdefault("new_per_day", 20)
    s.setdefault("introduced", {})       # date -> number of new cards first shown that day
    return s


def sm2(card, grade, today=None):
    """Grades 1 again, 2 hard, 3 good, 4 easy (as the Anki tab). Returns the updated schedule dict."""
    today = today or time.strftime("%Y-%m-%d")
    ef = card.get("ef", 2.5)
    reps = card.get("reps", 0)
    interval = card.get("interval", 0)
    q = {1: 1, 2: 3, 3: 4, 4: 5}[grade]
    if q < 3:
        reps, interval = 0, 1
    else:
        reps += 1
        interval = 1 if reps == 1 else (6 if reps == 2 else round(interval * ef))
        if grade == 4:
            interval = round(interval * 1.3)
    ef = max(1.3, ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
    due = time.strftime("%Y-%m-%d", time.localtime(time.mktime(time.strptime(today, "%Y-%m-%d")) + interval * 86400))
    return {"ef": round(ef, 3), "reps": reps, "interval": interval, "due": due, "last": today, "lapses":
            card.get("lapses", 0) + (1 if q < 3 and card.get("reps", 0) else 0)}


def drill_queue(topic=None, limit=20, today=None):
    today = today or time.strftime("%Y-%m-%d")
    cards = [c for c in build()["cards"] if not topic or c["topic"] == topic]
    st = _drill_state()
    due, new = [], []
    for c in cards:
        s = st["cards"].get(c["id"])
        if s is None:
            new.append(c)
        elif s["due"] <= today:
            due.append(dict(c, schedule=s))
    due.sort(key=lambda c: c["schedule"]["due"])
    left_new = max(0, st["new_per_day"] - st["introduced"].get(today, 0))
    # newest debates first, answered cards first (they have something to learn from)
    new.sort(key=lambda c: (c["answer"] is not None, c["date"]), reverse=True)
    queue = due[:limit] + new[:max(0, min(left_new, limit - len(due[:limit])))]
    return {"today": today, "topic": topic, "due": len(due), "new_available": len(new), "new_left_today": left_new,
            "total": len(cards), "queue": queue}


def grade(card_id, g, today=None):
    if g not in (1, 2, 3, 4):
        raise ValueError("grade must be 1-4")
    today = today or time.strftime("%Y-%m-%d")
    if not any(c["id"] == card_id for c in build()["cards"]):
        raise KeyError(card_id)
    with _lock:
        st = _drill_state()
        old = st["cards"].get(card_id)
        if old is None:
            st["introduced"][today] = st["introduced"].get(today, 0) + 1
        st["cards"][card_id] = sm2(old or {}, g, today)
        _write_json(DRILL_FILE, st)
    return st["cards"][card_id]
