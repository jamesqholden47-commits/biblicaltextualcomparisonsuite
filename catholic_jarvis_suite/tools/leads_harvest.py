"""
Harvest the leads buried in James's AI conversations: books mentioned to him, and career leads
(Claude GUI, Opus 5.5, 2026-10-14).

    python tools\\leads_harvest.py

Sources (all read-only):
  Claude       C:\\Users\\Elation\\.claude\\projects\\*\\*.jsonl   (main sessions; subagent research transcripts left out:
               their citations are research, not leads, and the files they wrote are already in the catalog)
  Antigravity  C:\\Users\\Elation\\AG_HISTORY_BACKUP\\brain\\*\\...\\transcript_full.jsonl   (the backup: keeps deleted ones)
  Gemini       every MyActivity.html export found under the home folder's Takeout folders and the vault, de-duplicated
               by prompt + time (several exports overlap)

BOOKS. A book is recognised only by a citation shape, never by a bare phrase:
   *Title* (… 1999 …)            italic title followed by a year or publisher within the same parentheses
   Author, *Title*               a capitalised name, comma, italic title
   *Title* by Author             italic title, "by", a capitalised name
   Title by Firstname Lastname   plain title in quotes followed by "by" and a name
Each title is counted across all conversations, keeps its first sighting (where, when, a snippet), and is matched
against the books on disk (data\\drive_inventory.json: .pdf/.epub/.mobi file names) by title words, so the list
says which ones James already owns. This is a pattern match, not a reading: expect some false titles, and books
named without italics or a citation shape are missed.

CAREER. James's own messages (not the AI's) that talk about work, money, school, the military or his business,
sorted into themes by keywords, plus the AI-reply sentences that name a concrete programme, certificate, benefit or
employer in answer to such a message. Plus the saved web pages in his home folder whose titles match a theme
(e.g. "Eligibility For Veteran Readiness And Employment").

Writes data\\leads.json.
"""
import datetime
import glob
import html
import json
import os
import re
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME = r"C:\Users\Elation"
OUT = os.path.join(BASE, "data", "leads.json")
INVENTORY = os.path.join(BASE, "data", "drive_inventory.json")
CLAUDE = r"C:\Users\Elation\.claude\projects"
AG = r"C:\Users\Elation\AG_HISTORY_BACKUP\brain"
GEMINI_GLOBS = [os.path.join(HOME, "Easter", "**", "MyActivity.html"),
                os.path.join(HOME, "takeout*", "**", "Gemini Apps", "MyActivity.html"),
                os.path.join(HOME, "aa1", "**", "MyActivity.html")]

NOT_HUMAN = ("<task-notification", "<command-", "<local-command", "[SYSTEM NOTIFICATION", "<agent-message",
             "Caveat:", "This session is being continued", "<system-reminder")


# ---------------------------------------------------------------- reading the conversations
def claude_messages():
    for p in glob.glob(os.path.join(CLAUDE, "*", "*.jsonl")):
        sid = os.path.basename(p)[:8]
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"type":"user"' not in line and '"type":"assistant"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get("isSidechain") or o.get("isMeta") or o.get("isCompactSummary"):
                    continue
                m = o.get("message") or {}
                c = m.get("content")
                if isinstance(c, list):
                    if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                        continue
                    c = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
                if not isinstance(c, str) or not c.strip() or (o["type"] == "user" and c.lstrip().startswith(NOT_HUMAN)):
                    continue
                if m.get("model") == "<synthetic>":
                    continue
                yield {"src": "Claude", "sid": sid, "ts": o.get("timestamp", ""), "role": "james" if o["type"] == "user" else "ai",
                       "text": c}


def ag_messages():
    for p in glob.glob(os.path.join(AG, "*", ".system_generated", "logs", "transcript_full.jsonl")) + \
             glob.glob(os.path.join(AG, "*", "transcript_full.jsonl")):
        sid = os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p)))) if ".system_generated" in p \
            else os.path.basename(os.path.dirname(p))
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                t, c = o.get("type"), o.get("content")
                if not isinstance(c, str) or not c.strip():
                    continue
                if t == "USER_INPUT":
                    m = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", c, re.S)
                    yield {"src": "Antigravity", "sid": sid[:8], "ts": o.get("created_at", ""), "role": "james",
                           "text": m.group(1) if m else c}
                elif t == "PLANNER_RESPONSE":
                    yield {"src": "Antigravity", "sid": sid[:8], "ts": o.get("created_at", ""), "role": "ai", "text": c}


_TAG = re.compile(r"<[^>]+>")
_CELL = re.compile(r'<div class="outer-cell.*?(?=<div class="outer-cell|\Z)', re.S)


def gemini_messages():
    seen = set()
    for g in GEMINI_GLOBS:
        for p in glob.glob(g, recursive=True):
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    doc = fh.read()
            except OSError:
                continue
            for cell in _CELL.findall(doc):
                text = html.unescape(_TAG.sub("\n", cell))
                text = re.sub(r"\n\s*\n+", "\n", text).strip()
                m = re.search(r"Prompted\s+(.*?)\n(\w{3} \d{1,2}, \d{4}, [\d:]+\s*[AP]M[^\n]*)\n(.*)", text, re.S)
                if not m:
                    continue
                prompt, when, reply = m.group(1).strip(), m.group(2).strip(), m.group(3)
                key = (prompt[:200], when)
                if key in seen:
                    continue
                seen.add(key)
                try:
                    ts = datetime.datetime.strptime(re.sub(r"\s+[A-Z]{2,4}$", "", when.replace("\u202f", " ")),
                                                    "%b %d, %Y, %I:%M:%S %p").isoformat()
                except ValueError:
                    ts = when
                yield {"src": "Gemini", "sid": "MyActivity", "ts": ts, "role": "james", "text": prompt}
                yield {"src": "Gemini", "sid": "MyActivity", "ts": ts, "role": "ai", "text": reply[:20000]}


# ---------------------------------------------------------------- books
NAME = r"(?:[A-Z][a-zA-Z'’\.-]+(?:\s+(?:[A-Z][a-zA-Z'’\.-]+|de|van|von|der|la|du|of|&|and)){0,4})"
IT = r"[*_]{1,2}([A-Z0-9][^*_\n]{2,120}?)[*_]{1,2}"
PAT_PAREN = re.compile(IT + r"\s*\(([^()\n]{0,80}?\b(1[5-9]\d\d|20[0-3]\d)\b[^()\n]{0,40})\)")
PAT_AUTH = re.compile(r"(" + NAME + r"),\s+" + IT)
PAT_BY = re.compile(IT + r",?\s+by\s+(" + NAME + r")")
PAT_QBY = re.compile(r"[\"“]([A-Z][^\"”\n]{3,100})[\"”]\s+by\s+(" + NAME + r")")
STOP_TITLES = {"note", "nota bene", "sic", "et al", "ibid", "contra", "passim", "not", "and", "the", "this", "very"}


def _norm_title(t):
    t = re.sub(r"[\[\]`]", "", t).strip(" .,:;")
    t = re.sub(r"\s+", " ", t)
    return t


def _key(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower().replace("&", "and")).strip()


def _looks_like_title(t):
    w = t.split()
    if len(w) < 2 or len(t) < 6 or _key(t) in STOP_TITLES:
        return False
    if sum(1 for x in w if x[:1].isupper()) < max(1, len(w) // 3):
        return False
    if re.search(r"[{}<>=|\\]|https?:|\.md\b|\.py\b|\[V\]|\[R\]|\[S\]", t):
        return False
    return True


def find_books(text):
    out = []
    for m in PAT_PAREN.finditer(text):
        out.append((m.group(1), "", m.group(2), m.start()))
    for m in PAT_AUTH.finditer(text):
        out.append((m.group(2), m.group(1), "", m.start()))
    for m in PAT_BY.finditer(text):
        out.append((m.group(1), m.group(2), "", m.start()))
    for m in PAT_QBY.finditer(text):
        out.append((m.group(1), m.group(2), "", m.start()))
    res = []
    for title, author, paren, pos in out:
        title = _norm_title(title)
        if not _looks_like_title(title):
            continue
        author = author.strip()
        if author and (len(author.split()) > 5 or author.lower() in ("see", "in", "cf", "the", "and")):
            author = ""
        res.append((title, author, paren.strip(), pos))
    return res


def owned_index():
    try:
        with open(INVENTORY, encoding="utf-8") as fh:
            rows = json.load(fh)["rows"]
    except (OSError, ValueError, KeyError):
        return []
    idx = []
    for r in rows:
        if r["ext"] in (".pdf", ".epub", ".mobi", ".azw3", ".azw", ".djvu"):
            words = set(_key(os.path.splitext(os.path.basename(r["path"]))[0].replace("_", " ")).split())
            idx.append((words, r["path"]))
    return idx


def owned_match(title, idx):
    tw = [w for w in _key(title).split() if len(w) > 2 and w not in ("the", "and", "for", "from", "with")]
    if len(tw) < 2:
        return ""
    need = max(2, int(len(tw) * 0.8 + 0.5))
    for words, path in idx:
        if sum(1 for w in tw if w in words) >= need:
            return path
    return ""


# ---------------------------------------------------------------- career
THEMES = {
    "School and degrees": r"\b(phd|ph\.d|doctorate|master'?s|m\.?a\.|mdiv|seminar(y|ies)|tuition|degree|university|college|"
                          r"gre\b|admission|scholarship|fellowship|enrol|curriculum|professor|academi)",
    "Military and veterans' benefits": r"\b(gi bill|va\b|vr&e|veteran|air force|afrotc|rotc|tbas|mos\b|enlist|recruit|"
                                       r"usmc|marines?|army|navy|clearance|military)",
    "Business and income": r"\b(housekeep|cleaning business|client|invoice|llc|my business|side hustle|income|salary|"
                           r"pay(ing)? (me|rent)|freelanc|upwork|fiverr|customers?|pricing|warriors)",
    "Apologetics, writing and media": r"\b(youtube|podcast|channel|patreon|substack|publish|book deal|my book|debat(e|er) career|"
                                      r"speaker|apologist|content creator|monetiz)",
    "Tech and AI work": r"\b(developer|programm(er|ing) job|software engineer|cyber ?security|certification|comptia|"
                        r"ai engineer|prompt engineer|data analyst|it job|tech job|resume|cv\b|portfolio)",
    "Job search": r"\b(job|hiring|hire me|apply|application|interview|career|employ(er|ment)|work for|position|"
                  r"internship|linkedin)",
}
THEME_RX = {k: re.compile(v, re.I) for k, v in THEMES.items()}
CONCRETE = re.compile(r"\b(GI Bill|Post-9/11|VR&E|Chapter 31|Chapter 33|Yellow Ribbon|AFROTC|TBAS|CompTIA|Security\+|"
                      r"Upwork|Fiverr|Patreon|Substack|LinkedIn|Indeed|USAJobs|Coursera|edX|FAFSA|Pell Grant|"
                      r"Ph\.?D\.?|M\.?Div|Th\.?M|M\.?A\.?|STL|STB|Licentiate|Pontifical|Seminary|University of [A-Z]\w+)\b")


def career_theme(text):
    hits = [k for k, rx in THEME_RX.items() if rx.search(text)]
    return hits


def main():
    t0 = time.time()
    idx = owned_index()
    books, career, counts = {}, [], {"Claude": 0, "Antigravity": 0, "Gemini": 0}
    last_james = {}
    for gen in (claude_messages(), ag_messages(), gemini_messages()):
        for m in gen:
            counts[m["src"]] += 1
            text = m["text"]
            if m["role"] == "ai" or m["src"] == "Gemini":
                for title, author, paren, pos in find_books(text):
                    k = _key(title)
                    b = books.get(k)
                    if not b:
                        b = books[k] = {"title": title, "author": author, "detail": paren, "mentions": 0, "sources": set(),
                                        "first": {"src": m["src"], "sid": m["sid"], "ts": m["ts"],
                                                  "snippet": re.sub(r"\s+", " ", text[max(0, pos - 160):pos + 220])}}
                    b["mentions"] += 1
                    b["sources"].add(m["src"])
                    if not b["author"] and author:
                        b["author"] = author
                    if not b["detail"] and paren:
                        b["detail"] = paren
            if m["role"] == "james":
                last_james[m["src"]] = m
                short = text if len(text) < 1500 else text[:700] + " … " + text[-700:]
                th = career_theme(short)
                if th and not short.lstrip().startswith(("someone said", "\"", "“")):
                    career.append({"kind": "you said", "themes": th, "src": m["src"], "sid": m["sid"], "ts": m["ts"],
                                   "text": short[:1500]})
            elif m["role"] == "ai":
                q = last_james.get(m["src"])
                if q and q["sid"] == m["sid"] and career_theme(q["text"][:1500]):
                    for sent in re.split(r"(?<=[.!?])\s+|\n", text):
                        if CONCRETE.search(sent) and 30 < len(sent) < 500 and career_theme(sent):
                            career.append({"kind": "AI suggested", "themes": career_theme(sent), "src": m["src"],
                                           "sid": m["sid"], "ts": m["ts"], "text": sent.strip(),
                                           "answering": q["text"][:300]})
    # saved web pages in the home folder whose names are career-ish
    for p in glob.glob(os.path.join(HOME, "*.htm*")) + glob.glob(os.path.join(HOME, "*_files")):
        name = os.path.basename(p).replace("_files", "")
        th = career_theme(name)
        if th:
            career.append({"kind": "saved web page", "themes": th, "src": "Home folder", "sid": "", "ts": datetime.datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds"),
                           "text": name, "path": p})
    rows = []
    for b in books.values():
        b["sources"] = sorted(b["sources"])
        b["owned"] = owned_match(b["title"], idx)
        rows.append(b)
    rows.sort(key=lambda b: (-b["mentions"], b["title"].lower()))
    career.sort(key=lambda c: c["ts"] or "", reverse=True)
    doc = {"made": datetime.datetime.now().isoformat(timespec="seconds"), "messages_read": counts,
           "books": rows, "career": career}
    # the AI-checked lists (tools\organizer_ai_merge.py) are self-contained: carry them over a re-harvest
    try:
        with open(OUT, encoding="utf-8") as fh:
            old = json.load(fh)
        for k in ("books_clean", "career_leads", "career_rejected"):
            if k in old:
                doc[k] = old[k]
    except (OSError, ValueError):
        pass
    with open(OUT + ".tmp", "w", encoding="utf-8") as w:
        json.dump(doc, w, ensure_ascii=False)
    os.replace(OUT + ".tmp", OUT)
    print(f"read {counts} messages in {time.time() - t0:.0f} s")
    print(f"{len(rows)} book titles ({sum(1 for b in rows if b['owned'])} already on disk); {len(career)} career items")
    print("wrote", OUT)
    print("LEADS-END")


if __name__ == "__main__":
    main()
