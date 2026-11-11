"""Smart sorting for the Volumes planner (2026-10-08, James: "i dont want crude sorting i want smart llm-sorting").

The keyword sorter counts each volume's keywords in a source's title, folder and opening. That is cheap but blind:
a note titled "Problem of the unevangelized" lands wherever its words happen to point. Here a language model reads
each source's title, folder, opening and screenshot text and decides, like a librarian would:
  volume          V01..V12, or one of NOT_BOOK labels: PERSONAL, PROJECT, NOT_USEFUL
  topic           what the source is about, in plain words (becomes the basis for real chapter titles)
  confidence      high / medium / low
  reason          one short sentence
Decisions live in data/books_llm_sort.json. The planner applies them unless James moved the source himself.
Nothing here edits any note; batches and decisions are working files under data/llm_sort/.

  export_batch(n, which, seed)   -> writes data/llm_sort/batch_<name>.jsonl and INSTRUCTIONS.md, returns the path
  import_decisions(path)         -> validates a decisions JSON file and merges it into books_llm_sort.json
"""
import json
import os
import random
import re
import time

from modules import books_core as core

WORK_DIR = os.path.join(core.DATA_DIR, "llm_sort")
DECISIONS_FILE = os.path.join(core.DATA_DIR, "books_llm_sort.json")
NOT_BOOK = {
    "PERSONAL": "James's own life: health, medication, fitness, money, legal, relationships, private matters",
    "PROJECT": "running the project or its tools: AI prompts, pipelines, logs, software, file organisation",
    "NOT_USEFUL": "empty, broken, a bare link or fragment with nothing usable",
}


def _opening(path, words=150):
    path = core.working_copy(path)          # read the clone, never the original (James, 2026-10-08)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            t = fh.read(20000)
    except OSError:
        return ""
    t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S)
    t = re.sub(r"!\[\[[^\]]*\]\]|!\[[^\]]*\]\([^)]*\)", " ", t)
    return " ".join(t.split()[:words])


def instructions(tax):
    vols = "\n".join(f"- {v['id']}: {v['title']}. {v.get('purpose', '')}" for v in tax["volumes"])
    nb = "\n".join(f"- {k}: {v}" for k, v in NOT_BOOK.items())
    return f"""# Sorting instructions (Volumes planner)

James is turning his notes and research into a Catholic apologetics encyclopedia in 12 volumes. For EACH source in the
batch file (one JSON object per line: id, title, area, folder, words, opening, screenshot_text), decide where it
belongs. Judge by what the source is actually about, not by isolated words. Short or messy notes are still real
material: a bare scripture reference or a one-line claim belongs with its subject.

## The 12 volumes
{vols}

## Not book material (use these labels instead of a volume)
{nb}

## Output
Write ONE JSON file: a list with one object per source, in the batch's order:
{{"id": "<the id>", "volume": "V01".."V12" or "PERSONAL" | "PROJECT" | "NOT_USEFUL",
 "topic": "<what it is about, plain words, at most 8 words>", "confidence": "high" | "medium" | "low",
 "reason": "<one short sentence>"}}
Every id in the batch must appear exactly once. Do not invent ids. Do not open or edit any other file.
"""


def export_batch(n=200, which="unsorted", seed=7, name=None, extra_sorted=0):
    """A batch of sources for the model: `which` = "unsorted" (default) or "all"; plus `extra_sorted` sources the
    keyword sorter already placed (to measure how often the two agree)."""
    plan = core.load_plan()
    tax = core.load_taxonomy()
    src = plan["sources"]
    done = set((_read(DECISIONS_FILE) or {}).keys())
    pool = [sid for sid in (plan["unsorted"] if which == "unsorted" else list(src)) if sid not in done]
    rnd = random.Random(seed)
    pick = rnd.sample(pool, min(n, len(pool)))
    if extra_sorted:
        placed = [sid for sid, s in src.items() if s.get("volume") and sid not in plan["unsorted"] and sid not in done]
        pick += rnd.sample(placed, min(extra_sorted, len(placed)))
    os.makedirs(WORK_DIR, exist_ok=True)
    name = name or time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(WORK_DIR, f"batch_{name}.jsonl")
    with open(path, "w", encoding="utf-8") as w:
        for sid in pick:
            s = src[sid]
            rec = {"id": sid, "title": s.get("title"), "area": s.get("area"), "folder": s.get("folder"),
                   "words": s.get("words"), "opening": _opening(s["path"])}
            if s.get("screenshot_words"):
                rec["screenshot_text"] = " ".join(core.screenshot_text(s["path"], 2000).split()[:80])
            w.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(os.path.join(WORK_DIR, "INSTRUCTIONS.md"), "w", encoding="utf-8") as w:
        w.write(instructions(tax))
    with open(os.path.join(WORK_DIR, f"batch_{name}.keyword_view.json"), "w", encoding="utf-8") as w:
        json.dump({sid: {"keyword_volume": src[sid].get("volume"), "unsorted": sid in plan["unsorted"]} for sid in pick}, w)
    return {"batch": path, "n": len(pick), "instructions": os.path.join(WORK_DIR, "INSTRUCTIONS.md")}


def _read(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def import_decisions(path, batch_path, model="", note=""):
    """Validate a model's decisions against its batch, then merge them. Refuses the whole file on any bad record."""
    tax = core.load_taxonomy()
    vids = {v["id"] for v in tax["volumes"]}
    with open(batch_path, encoding="utf-8") as fh:
        ids = [json.loads(l)["id"] for l in fh if l.strip()]
    got = _read(path)
    if not isinstance(got, list):
        raise ValueError("decisions file is not a JSON list")
    seen, bad = set(), []
    for d in got:
        if d.get("id") not in ids:
            bad.append(f"unknown id {d.get('id')}")
        elif d["id"] in seen:
            bad.append(f"duplicate id {d['id']}")
        if d.get("volume") not in vids and d.get("volume") not in NOT_BOOK:
            bad.append(f"{d.get('id')}: bad volume {d.get('volume')}")
        if d.get("confidence") not in ("high", "medium", "low"):
            bad.append(f"{d.get('id')}: bad confidence {d.get('confidence')}")
        seen.add(d.get("id"))
    missing = [i for i in ids if i not in seen]
    if missing:
        bad.append(f"{len(missing)} ids missing")
    if bad:
        raise ValueError("decisions refused: " + "; ".join(bad[:10]))
    allx = _read(DECISIONS_FILE) or {}
    stamp = time.strftime("%Y-%m-%dT%H:%M")
    for d in got:
        allx[d["id"]] = {"volume": d["volume"], "topic": (d.get("topic") or "")[:80], "confidence": d["confidence"],
                         "reason": (d.get("reason") or "")[:200], "batch": os.path.basename(batch_path),
                         "model": model, "at": stamp, "note": note}
    core._write_json(DECISIONS_FILE, allx)
    return {"imported": len(got), "total_decisions": len(allx)}


def load_decisions():
    return _read(DECISIONS_FILE) or {}
