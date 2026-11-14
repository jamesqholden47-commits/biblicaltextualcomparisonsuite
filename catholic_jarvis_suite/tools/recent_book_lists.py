"""
Every book an AI named to James in a recent window, from Antigravity's own markdown (Claude GUI, Opus 5.5, 2026-10-14).

    python tools\\recent_book_lists.py [since=2026-10-11]

Antigravity writes reading lists as "**Author**, *Title* (details)" or "* ***Title*** (Publisher)"; the general
harvester (leads_harvest.py) only knows the plain "Author, *Title*" shape, so this adds the bold-author and
bold-italic-title shapes. Reads AG_HISTORY_BACKUP (read-only). Each title is checked against: the 668-title
conversation list (data\\leads.json books_clean), the book files on the drive (owned_match), and the doctoral reading
lists in the verified curricula report (Catholic University 2017, Puritan Reformed 2018, a 2004 student list).
Writes data\\recent_book_lists.json.
"""
import datetime
import glob
import json
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "tools"))
import leads_harvest as L  # noqa: E402

AG = r"C:\Users\Elation\AG_HISTORY_BACKUP\brain"
OUT = os.path.join(BASE, "data", "recent_book_lists.json")

# titles on the public doctoral reading lists (CURRICULA_AND_STUDY_PLAN__VERIFIED.md §2.4 and §4.3, read 2026-10-13)
ON_DOCTORAL_LISTS = ["old testament pseudepigrapha", "dead sea scrolls study edition", "josephus", "apostolic fathers",
                     "apocryphal new testament", "mishnah", "history of new testament research", "canon of the new testament",
                     "text of the new testament", "unity and diversity in the new testament",
                     "history and theology of the new testament writings", "new testament theology",
                     "semantics of biblical language", "biblical theology of the old and new testaments",
                     "first urban christians", "introduction to the new testament", "theology of the new testament",
                     "textual criticism of the hebrew bible"]

P_BOLD_AUTH = re.compile(r"\*\*([^*\n]{3,160}?)\*\*,?\s*\*{1,3}([A-Z0-9][^*\n]{2,200}?)\*{1,3}(?:\s*\(([^)\n]{0,160})\))?")
P_BOLD_TITLE = re.compile(r"\*\*\*([A-Z0-9][^*\n]{3,200}?)\*\*\*(?:\s*\(([^)\n]{0,160})\))?")
P_TITLE_BY = re.compile(r"\*([A-Z0-9][^*\n]{3,200}?)\*\s*(?:by|—|-)\s*\*{0,2}([A-Z][^*\n,;()]{3,80})")


def _transcripts():
    for p in glob.glob(os.path.join(AG, "*", ".system_generated", "logs", "transcript_full.jsonl")):
        yield os.path.basename(os.path.dirname(os.path.dirname(os.path.dirname(p))))[:8], p


def main(since):
    found = {}
    msgs = 0
    for sid, p in _transcripts():
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                if o.get("type") != "PLANNER_RESPONSE" or (o.get("created_at") or "") < since:
                    continue
                text = o.get("content") or ""
                if not isinstance(text, str) or not text.strip():
                    continue
                msgs += 1
                cands = []
                for m in P_BOLD_AUTH.finditer(text):
                    cands.append((m.group(2), m.group(1), m.group(3) or ""))
                for m in P_BOLD_TITLE.finditer(text):
                    cands.append((m.group(1), "", m.group(2) or ""))
                for m in P_TITLE_BY.finditer(text):
                    cands.append((m.group(1), m.group(2), ""))
                for t, a, d, _ in L.find_books(text):
                    cands.append((t, a, d))
                for title, author, detail in cands:
                    title = L._norm_title(title)
                    author = re.sub(r"\s+", " ", author.replace("*", "")).strip(" ,.")
                    if not L._looks_like_title(title) or len(title) > 160:
                        continue
                    if re.search(r"(?i)^(stage|track|section|part|tier|desk|cluster|phase|step|the [a-z]+ desk)\b|prompt|directive", title):
                        continue
                    k = L._key(title)
                    r = found.setdefault(k, {"title": title, "author": "", "detail": "", "mentions": 0, "sessions": set(),
                                             "first": o.get("created_at", "")})
                    r["mentions"] += 1
                    r["sessions"].add(sid)
                    if author and not r["author"] and len(author) < 120:
                        r["author"] = author
                    if detail and not r["detail"]:
                        r["detail"] = detail.strip()
    try:
        with open(os.path.join(BASE, "data", "leads.json"), encoding="utf-8") as fh:
            known = {L._key(b["title"]) for b in json.load(fh).get("books_clean", [])}
    except (OSError, ValueError):
        known = set()
    idx = L.owned_index()
    rows = []
    for r in found.values():
        k = L._key(r["title"])
        r["sessions"] = sorted(r["sessions"])
        r["in_conversation_list"] = k in known
        r["owned"] = L.owned_match(r["title"], idx)
        r["on_doctoral_lists"] = any(x in k for x in ON_DOCTORAL_LISTS)
        rows.append(r)
    rows.sort(key=lambda r: (-r["mentions"], r["title"].lower()))
    with open(OUT + ".tmp", "w", encoding="utf-8") as w:
        json.dump({"made": datetime.datetime.now().isoformat(timespec="seconds"), "since": since, "ag_replies_read": msgs,
                   "rows": rows}, w, ensure_ascii=False, indent=1)
    os.replace(OUT + ".tmp", OUT)
    print(f"{msgs} Antigravity replies since {since}: {len(rows)} titles; {sum(r['in_conversation_list'] for r in rows)} "
          f"already in the 668-title list; {sum(bool(r['owned']) for r in rows)} on the drive; "
          f"{sum(r['on_doctoral_lists'] for r in rows)} on a doctoral reading list")
    print("wrote", OUT)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-10-11")
