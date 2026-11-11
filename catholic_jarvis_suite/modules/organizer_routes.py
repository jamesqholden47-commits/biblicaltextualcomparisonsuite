"""Organizer API (/api/organizer). Claude GUI, Opus 5.5, 2026-10-14. See modules/organizer_core.py for the rules.

  GET  /summary                 buckets, shelves, counts, duplicate totals
  GET  /files                   bucket, shelf, kind, q, dupes, sort, limit, offset
  GET  /folders                your own virtual folders;  POST /place  {path, folder, hidden}  files or hides a file
  GET  /duplicates              identical files (same fingerprint) in more than one place
  GET  /leads/books             books mentioned in conversations: owned / not owned, q, limit
  GET  /leads/career            career leads by theme, q, kind
  POST /rebuild                 re-scan the drive, then re-read the conversations (one run; nothing stays running)
  GET  /rebuild                 progress of that run
Nothing here moves, renames or deletes a file.
"""
import json
import os
import subprocess
import sys
import threading
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from modules import organizer_core as core

router = APIRouter(prefix="/api/organizer", tags=["organizer"])

BASE = core.BASE
LEADS = os.path.join(BASE, "data", "leads.json")
STEPS = [("Scanning the drive", "drive_inventory.py"), ("Reading the conversations for books and career leads", "leads_harvest.py"),
         ("Listing what the AIs wrote", "ag_output_catalog.py"), ("Finding unfinished requests", "hanging_turns.py")]
_state = {"running": False, "step": "", "started": 0, "finished": 0, "error": ""}
_lock = threading.Lock()
_leads = {"mtime": None, "data": None}


def _need(x, what="Nothing scanned yet. Press Rebuild (or run tools\\drive_inventory.py)."):
    if x is None:
        raise HTTPException(503, what)
    return x


@router.get("/summary")
def summary():
    return _need(core.summary())


@router.get("/files")
def files(bucket: Optional[str] = None, shelf: Optional[str] = None, kind: Optional[str] = None, q: Optional[str] = None,
          dupes: int = 0, sort: str = Query("mtime", pattern="^(mtime|size|name)$"),
          limit: int = Query(300, ge=1, le=2000), offset: int = Query(0, ge=0),
          folder: Optional[str] = None, hidden: int = 0):
    return _need(core.files(bucket, shelf, kind, q, bool(dupes), limit, offset, sort, folder, bool(hidden)))


class Place(BaseModel):
    path: str
    folder: Optional[str] = None      # "" takes it out of your folders
    hidden: Optional[bool] = None


@router.get("/folders")
def folders():
    """Your own folders (virtual: the files stay where they are) and how many files each holds."""
    return {"folders": core.my_folders(), "hidden": sum(1 for e in core.placements().values() if e.get("hidden"))}


@router.post("/place")
def place(p: Place):
    """File a file under one of your folders, or hide it. Nothing on disk moves."""
    if not os.path.isfile(p.path):
        raise HTTPException(404, "no such file")
    return {"entry": core.place(p.path, p.folder, p.hidden), "folders": core.my_folders()}


@router.get("/duplicates")
def duplicates(limit: int = Query(300, ge=1, le=2000), bucket: Optional[str] = None):
    return _need(core.duplicates(limit, bucket))


def _load_leads():
    try:
        mt = os.path.getmtime(LEADS)
    except OSError:
        raise HTTPException(503, "No leads yet. Press Rebuild (or run tools\\leads_harvest.py).")
    if _leads["mtime"] != mt:
        with open(LEADS, encoding="utf-8") as fh:
            _leads.update(mtime=mt, data=json.load(fh))
    return _leads["data"]


@router.get("/leads/books")
def lead_books(owned: Optional[int] = None, q: Optional[str] = None, min_mentions: int = 1, shelf: Optional[str] = None,
               kind: Optional[str] = None, raw: int = 0,
               limit: int = Query(500, ge=1, le=5000), offset: int = Query(0, ge=0)):
    """The AI-checked list when there is one (tools\\organizer_ai_merge.py), else the raw harvest."""
    d = _load_leads()
    src = d["books"] if raw or "books_clean" not in d else d["books_clean"]
    ql = (q or "").lower().split()
    rows = [b for b in src
            if b["mentions"] >= min_mentions
            and (owned is None or bool(b.get("owned")) == bool(owned))
            and (not shelf or b.get("shelf") == shelf) and (not kind or b.get("kind") == kind)
            and all(w in (b["title"] + " " + (b.get("author") or "")).lower() for w in ql)]
    shelves, kinds = {}, {}
    for b in src:
        if b.get("shelf"):
            shelves[b["shelf"]] = shelves.get(b["shelf"], 0) + 1
        if b.get("kind"):
            kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    return {"made": d["made"], "read": d["messages_read"], "checked": src is not d["books"], "total": len(rows),
            "owned": sum(1 for b in src if b.get("owned")), "all": len(src), "raw_all": len(d["books"]),
            "shelves": shelves, "kinds": kinds, "rows": rows[offset:offset + limit]}


@router.get("/leads/career")
def lead_career(theme: Optional[str] = None, kind: Optional[str] = None, q: Optional[str] = None, raw: int = 0,
                type: Optional[str] = None, limit: int = Query(400, ge=1, le=5000), offset: int = Query(0, ge=0)):
    """The checked leads (each quote found word for word in James's messages) unless raw=1: the keyword pile."""
    d = _load_leads()
    ql = (q or "").lower().split()
    if not raw and d.get("career_leads") is not None:
        src = d["career_leads"]
        rows = [c for c in src if (not type or c["type"] == type)
                and all(w in (c["lead"] + " " + c["detail"] + " " + c["quote"]).lower() for w in ql)]
        types = {}
        for c in src:
            types[c["type"]] = types.get(c["type"], 0) + 1
        return {"made": d["made"], "checked": True, "total": len(rows), "types": types,
                "rejected": len(d.get("career_rejected") or []), "pile": len(d["career"]), "rows": rows[offset:offset + limit]}
    rows = [c for c in d["career"]
            if (not theme or theme in c["themes"]) and (not kind or c["kind"] == kind)
            and all(w in c["text"].lower() for w in ql)]
    themes = {}
    for c in d["career"]:
        for t in c["themes"]:
            themes[t] = themes.get(t, 0) + 1
    return {"made": d["made"], "checked": False, "total": len(rows), "themes": themes, "rows": rows[offset:offset + limit]}


def _run():
    try:
        for label, script in STEPS:
            _state["step"] = label
            p = subprocess.run([sys.executable, os.path.join(BASE, "tools", script)], capture_output=True, text=True,
                               timeout=3600, cwd=BASE)
            if p.returncode != 0:
                _state["error"] = f"{script} failed: {(p.stderr or p.stdout)[-400:]}"
                break
        else:
            _state["error"] = ""
    except Exception as e:                                   # noqa: BLE001 - reported to the page
        _state["error"] = str(e)
    finally:
        _state.update(running=False, finished=time.time(), step="")


@router.post("/rebuild")
def rebuild():
    with _lock:
        if _state["running"]:
            return dict(_state, already=True)
        _state.update(running=True, started=time.time(), error="", step="starting")
    threading.Thread(target=_run, daemon=True).start()
    return dict(_state)


@router.get("/rebuild")
def rebuild_status():
    return dict(_state)
