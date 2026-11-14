"""
Fold the AI pass back into the Organizer, CHECKING it first (Claude GUI, Opus 5.5, 2026-10-14).

    python tools\\organizer_ai_merge.py

Reads data\\organizer_ai\\books_out.json, shelves_out.json, career_out_1..3.json (written by Sonnet workers from the
*_in.jsonl files that tools\\organizer_ai_prep.py made). Workers never grade themselves, so:
  * a career lead is kept only if its "quote" is found character for character in the text of one of the input
    items it names (whitespace runs collapsed); otherwise it goes to "rejected" with the reason;
  * a book row is kept only if its id exists in the input; rows marked "not a title" are dropped; rows marked
    "same_as" another row are merged into it (mentions added up, sources joined);
  * a shelf is accepted only from the allowed list.
Writes data\\leads.json (adds books_clean, career_leads, career_rejected) and data\\book_shelves.json.
Prints what it accepted and rejected.
"""
import glob
import json
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI = os.path.join(BASE, "data", "organizer_ai")
LEADS = os.path.join(BASE, "data", "leads.json")
SHELVES_OUT = os.path.join(BASE, "data", "book_shelves.json")
sys.path.insert(0, os.path.join(BASE, "tools"))
import leads_harvest  # noqa: E402

SHELVES = {"Bible and translations", "Church Fathers and patristics", "Papacy and church history", "Theology and doctrine",
           "Judaism and rabbinics", "Philosophy", "Languages and grammar", "Islam and other religions",
           "Science, health and practical", "Politics, society and current events", "Fiction and literature", "Other books",
           "Personal papers (forms, letters, resume)", "Articles and saved pages (PDF)", "Software and computer manuals"}
KINDS = {"book", "church document", "ancient or patristic work", "article or chapter", "not a title"}


def _ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def _read_json(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _jsonl(p):
    with open(p, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def merge_books(leads):
    out = _read_json(os.path.join(AI, "books_out.json"))
    if not isinstance(out, list):
        return None, "books_out.json missing or not a list"
    src = {r["id"]: r for r in _jsonl(os.path.join(AI, "books_in.jsonl"))}
    raw = {f"b{i}": b for i, b in enumerate(leads["books"])}
    complete = any(isinstance(x, dict) and x.get("id") == "__complete__" for x in out)
    rows, bad, dropped = {}, 0, 0
    for x in out:
        if not isinstance(x, dict) or x.get("id") not in src:
            bad += 1 if isinstance(x, dict) and x.get("id") != "__complete__" else 0
            continue
        if x.get("kind") not in KINDS or x.get("shelf") not in SHELVES:
            bad += 1
            continue
        if x["kind"] == "not a title":
            dropped += 1
            continue
        rows[x["id"]] = x
    idx = leads_harvest.owned_index()
    clean = {}
    for bid, x in rows.items():
        head = x.get("same_as") if x.get("same_as") in rows else bid
        b = raw[bid]
        c = clean.get(head)
        if not c:
            h = rows[head]
            c = clean[head] = {"title": _ws(h.get("title")) or raw[head]["title"], "author": _ws(h.get("author")),
                               "kind": h["kind"], "shelf": h["shelf"], "mentions": 0, "sources": set(),
                               "first": raw[head]["first"], "variants": [], "owned": raw[head].get("owned") or ""}
        c["mentions"] += b["mentions"]
        c["sources"].update(b["sources"])
        if bid != head:
            c["variants"].append(b["title"])
        if not c["owned"] and b.get("owned"):
            c["owned"] = b["owned"]
    for c in clean.values():
        c["sources"] = sorted(c["sources"])
        if not c["owned"]:
            c["owned"] = leads_harvest.owned_match(c["title"], idx)
    lst = sorted(clean.values(), key=lambda c: (-c["mentions"], c["title"].lower()))
    return lst, (f"books: {len(out)} rows back ({'complete' if complete else 'PARTIAL'}), {len(lst)} kept after merging, "
                 f"{dropped} 'not a title', {bad} malformed")


def merge_shelves():
    out = _read_json(os.path.join(AI, "shelves_out.json"))
    if not isinstance(out, list):
        return None, "shelves_out.json missing or not a list"
    ids = {r["id"] for r in _jsonl(os.path.join(AI, "shelves_in.jsonl"))}
    ok = {x["id"]: x["shelf"] for x in out if isinstance(x, dict) and x.get("id") in ids and x.get("shelf") in SHELVES}
    return ok, f"shelves: {len(out)} rows back, {len(ok)} accepted of {len(ids)} files"


def merge_career():
    items = {}
    for p in glob.glob(os.path.join(AI, "career_in_*.jsonl")):
        for r in _jsonl(p):
            items[r["id"]] = r
    leads, rejected, notes = {}, [], []
    for p in sorted(glob.glob(os.path.join(AI, "career_out_*.json"))):
        d = _read_json(p)
        if not isinstance(d, dict) or not isinstance(d.get("leads"), list):
            notes.append(f"{os.path.basename(p)}: unreadable")
            continue
        notes.append(f"{os.path.basename(p)}: {len(d['leads'])} leads, {d.get('discarded', '?')} discarded, "
                     f"{'complete' if d.get('complete') else 'PARTIAL'}")
        for L in d["leads"]:
            ids = [i for i in (L.get("ids") or []) if i in items]
            q = _ws(L.get("quote"))
            found = len(q) >= 15 and any(q in _ws(items[i]["text"]) for i in ids)
            if not ids or not found:
                rejected.append({"lead": L.get("lead"), "why": "no valid ids" if not ids else "quote not found in its items"})
                continue
            key = re.sub(r"[^a-z0-9 ]", "", (L.get("lead") or "").lower()).strip()
            m = leads.get(key)
            if not m:
                m = leads[key] = {"lead": _ws(L.get("lead")), "type": L.get("type", ""), "detail": _ws(L.get("detail")),
                                  "who": L.get("who", ""), "dates": set(), "ids": set(), "quote": q,
                                  "sources": set()}
            m["dates"].update(d_ for d_ in (L.get("dates") or []) if isinstance(d_, str))
            m["ids"].update(ids)
            m["sources"].update(items[i]["source"] for i in ids)
    out = []
    for m in leads.values():
        m["dates"] = sorted(m["dates"])
        m["ids"] = sorted(m["ids"])
        m["sources"] = sorted(m["sources"])
        out.append(m)
    out.sort(key=lambda m: (m["dates"][-1] if m["dates"] else ""), reverse=True)
    return out, rejected, notes


def main():
    with open(LEADS, encoding="utf-8") as fh:
        leads = json.load(fh)
    books, msg_b = merge_books(leads)
    shelves, msg_s = merge_shelves()
    career, rejected, notes = merge_career()
    if books is not None:
        leads["books_clean"] = books
    leads["career_leads"] = career
    leads["career_rejected"] = rejected
    with open(LEADS + ".tmp", "w", encoding="utf-8") as w:
        json.dump(leads, w, ensure_ascii=False)
    os.replace(LEADS + ".tmp", LEADS)
    if shelves is not None:
        with open(SHELVES_OUT + ".tmp", "w", encoding="utf-8") as w:
            json.dump(shelves, w, ensure_ascii=False)
        os.replace(SHELVES_OUT + ".tmp", SHELVES_OUT)
    print(msg_b)
    print(msg_s)
    for n in notes:
        print(n)
    print(f"career: {len(career)} leads kept after merging, {len(rejected)} rejected by the quote check")
    print("MERGE-END")


if __name__ == "__main__":
    main()
