"""Catalog tab API (/api/catalog). Claude GUI, Opus 5.5, 2026-10-13.

Two lists, both built from the AI logs by scripts in tools\\ (read-only on the logs):
  /files     every research file Antigravity or Claude wrote (tools\\ag_output_catalog.py -> data\\ag_output_catalog.json)
  /hanging   every request James made that was left unfinished (tools\\hanging_turns.py -> data\\hanging_turns.json)
  /rebuild   re-runs both scripts once (about a minute); nothing runs in the background.
"""
import glob
import json
import os
import re
import subprocess
import sys
import threading
import time

from fastapi import APIRouter, HTTPException

from modules.paths_config import get_path

router = APIRouter(prefix="/api/catalog", tags=["catalog"])

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
FILES_JSON = os.path.join(DATA, "ag_output_catalog.json")
HANGING_JSON = os.path.join(DATA, "hanging_turns.json")
SCRIPTS = [os.path.join(BASE, "tools", "ag_output_catalog.py"), os.path.join(BASE, "tools", "hanging_turns.py")]
AG_READABLE = os.path.join(get_path("ag_history_backup"), "readable")

# requests that are not work: account and app commands typed into a session that had run out
NOISE = re.compile(r"^\s*(?:/?(?:claude\s+)?log(?:in|out|oit)|--resume|winget\s+upgrade\b.*|test\.?|online back|"
                   r"opus max .*|raise it.*|login|logout)\s*$", re.I)

_lock = threading.Lock()
_state = {"running": False, "started": 0, "finished": 0, "error": ""}


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _ag_readable(sid):
    hits = glob.glob(os.path.join(AG_READABLE, f"*_{sid[:8]}.md"))
    return hits[0] if hits else ""


@router.get("/files")
def files(infra: int = 0):
    d = _load(FILES_JSON)
    if d is None:
        raise HTTPException(503, "No catalog yet. Press Rebuild (or run tools\\ag_output_catalog.py).")
    rows = [r for r in d["rows"] if infra or r.get("side") == "subject"]
    keep = ("path", "rel", "writers", "kind", "side", "era", "words", "bytes", "exists", "first", "last", "request",
            "description", "sessions")
    return {"made": d.get("made"), "total": len(d["rows"]),
            "rows": [{k: (r.get(k)[:600] if k == "request" and r.get(k) else r.get(k)) for k in keep} for r in rows]}


@router.get("/hanging")
def hanging(noise: int = 0):
    d = _load(HANGING_JSON)
    if d is None:
        raise HTTPException(503, "No list yet. Press Rebuild (or run tools\\hanging_turns.py).")
    out = []
    for r in d["rows"]:
        is_noise = bool(NOISE.match(r.get("request") or ""))
        if is_noise and not noise:
            continue
        x = dict(r, noise=is_noise, request=(r.get("request") or "")[:3000], last_answer=(r.get("last_answer") or "")[:1500])
        if r.get("source") == "Antigravity":
            x["readable"] = _ag_readable(r.get("session", ""))
        out.append(x)
    return {"made": d.get("made"), "claude_logs": d.get("claude_logs"), "ag_sessions": d.get("ag_sessions"), "rows": out}


def _run():
    try:
        for s in SCRIPTS:
            p = subprocess.run([sys.executable, s], capture_output=True, text=True, timeout=900, cwd=BASE)
            if p.returncode != 0:
                _state["error"] = f"{os.path.basename(s)} failed: {(p.stderr or p.stdout)[-400:]}"
                break
        else:
            _state["error"] = ""
    except Exception as e:                       # noqa: BLE001 - reported to the page, not swallowed
        _state["error"] = str(e)
    finally:
        _state["running"], _state["finished"] = False, time.time()


@router.post("/rebuild")
def rebuild():
    with _lock:
        if _state["running"]:
            return dict(_state, already=True)
        _state.update(running=True, started=time.time(), error="")
    threading.Thread(target=_run, daemon=True).start()
    return dict(_state)


@router.get("/rebuild")
def rebuild_status():
    return dict(_state)
