"""
Prepare the inputs for the AI pass over the Organizer's leads (Claude GUI, Opus 5.5, 2026-10-14).

    python tools\\organizer_ai_prep.py

Writes data\\organizer_ai\\:
  books_in.jsonl        every harvested book title (id, title, author, detail, mentions, owned, snippet)
  shelves_in.jsonl      every book FILE the keyword rules could not shelve (id, file name, folder)
  career_in_N.jsonl     the career candidates, split into 3 parts (id, kind, date, source, text, answering)
The agents write books_out.json, shelves_out.json and career_out_N.json next to them; tools\\organizer_ai_merge.py
folds those back into data\\leads.json and data\\book_shelves.json. Nothing original is read or changed here.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from modules import organizer_core as core  # noqa: E402

OUT = os.path.join(BASE, "data", "organizer_ai")
LEADS = os.path.join(BASE, "data", "leads.json")


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(LEADS, encoding="utf-8") as fh:
        leads = json.load(fh)
    with open(os.path.join(OUT, "books_in.jsonl"), "w", encoding="utf-8") as w:
        for i, b in enumerate(leads["books"]):
            w.write(json.dumps({"id": f"b{i}", "title": b["title"], "author": b["author"], "detail": b["detail"],
                                "mentions": b["mentions"], "owned": bool(b["owned"]),
                                "snippet": b["first"]["snippet"][:300]}, ensure_ascii=False) + "\n")
    d = core.load()
    n = 0
    with open(os.path.join(OUT, "shelves_in.jsonl"), "w", encoding="utf-8") as w:
        for r in d["rows"]:
            if r["bucket"] == "Books" and r["shelf"] == "Other books":
                w.write(json.dumps({"id": r["fp"] or r["path"], "file": os.path.basename(r["path"]),
                                    "folder": os.path.dirname(r["rel"])}, ensure_ascii=False) + "\n")
                n += 1
    # Keep what is about James himself: his own short messages in the first person, not pasted Discord logs or long
    # research briefs (those match "seminary", "apply", "debate" without being about his career), and the AI's concrete
    # suggestions, and saved career pages.
    import re
    discord = re.compile(r"Role icon|— \d{1,2}:\d\d|\bOP —|Today at|Yesterday at|\[[A-Z]{2,6}\],", re.I)
    first_person = re.compile(r"\b(i|i'm|im|i've|ive|my|me|myself|should i|can i|could i|do i)\b", re.I)
    cands = [c for c in leads["career"]
             if c["kind"] != "you said"
             or (len(c["text"]) <= 900 and not discord.search(c["text"]) and first_person.search(c["text"]))]
    print(f"career candidates kept {len(cands)} of {len(leads['career'])}")
    parts = 3
    size = (len(cands) + parts - 1) // parts
    for p in range(parts):
        with open(os.path.join(OUT, f"career_in_{p + 1}.jsonl"), "w", encoding="utf-8") as w:
            for i, c in enumerate(cands[p * size:(p + 1) * size], p * size):
                w.write(json.dumps({"id": f"c{i}", "kind": c["kind"], "date": (c["ts"] or "")[:10], "source": c["src"],
                                    "text": c["text"][:1200], "answering": c.get("answering", "")[:300]},
                                   ensure_ascii=False) + "\n")
    print(f"books {len(leads['books'])}, unshelved files {n}, career {len(cands)} in {parts} parts -> {OUT}")


if __name__ == "__main__":
    main()
