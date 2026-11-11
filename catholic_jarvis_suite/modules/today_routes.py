"""Today home: the one server-side piece it needs (Phase 3, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).
Every other Today card reads an endpoint that already exists (Volumes next, debates, Loose Ends, Ledger, Anki,
Files recents, Recall status, build info)."""
import os
import time
from datetime import datetime

from fastapi import APIRouter

from modules.paths_config import get_path

router = APIRouter(prefix="/api/today", tags=["today"])

BACKUP_LOG = os.path.join(get_path("ag_history_backup"), "backup_log.tsv")
BACKUP_SCRIPT = os.path.join(get_path("ag_history_backup"), "backup_ag_history.py")
WARN_HOURS = 72


def backup_status(log_path=None, now=None):
    """Age of the last Antigravity history backup, from the last line of backup_log.tsv.
    Antigravity silently deletes its oldest conversations past ~515, so a stale backup is lost history."""
    p = log_path or BACKUP_LOG
    now = now or time.time()
    out = {"log": p, "script": BACKUP_SCRIPT, "warn_hours": WARN_HOURS}
    try:
        with open(p, encoding="utf-8") as fh:
            lines = [ln for ln in fh.read().splitlines() if ln.strip()]
    except OSError:
        return dict(out, state="missing", message="No backup has ever been run.")
    if not lines:
        return dict(out, state="missing", message="The backup log is empty.")
    last = lines[-1].split("\t")
    try:
        ts = datetime.strptime(last[0], "%Y%m%d-%H%M%S").timestamp()
    except ValueError:
        return dict(out, state="unknown", message="Could not read the last backup line.")
    fields = dict(x.split("=", 1) for x in last[1:] if "=" in x)
    age = (now - ts) / 3600
    state = "ok" if age <= WARN_HOURS and fields.get("failed", "0") == "0" else "warn"
    msg = (f"Last backup {age:.0f} h ago" if age >= 1 else "Backed up within the hour")
    if fields.get("failed", "0") != "0":
        msg += f", but {fields['failed']} file(s) failed to copy"
    return dict(out, state=state, last=datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M"), age_hours=round(age, 1),
                sessions_live=fields.get("sessions_live"), sessions_in_backup=fields.get("sessions_in_backup"),
                runs=len(lines), message=msg)


_run = {"state": "idle", "started": 0, "output": "", "code": None}


def _run_backup():
    import subprocess
    import sys
    try:
        r = subprocess.run([sys.executable, BACKUP_SCRIPT], capture_output=True, text=True, timeout=3600,
                           encoding="utf-8", errors="replace")
        _run.update(state="done", code=r.returncode, output=(r.stdout + r.stderr)[-2000:])
    except Exception as e:  # noqa: BLE001
        _run.update(state="done", code=-1, output=f"{type(e).__name__}: {e}")


@router.get("/backup")
def backup():
    return dict(backup_status(), run={k: _run[k] for k in ("state", "code", "output")})


@router.post("/backup/run")
def backup_run():
    """Run the copy-only backup once, now (the same script James can run by hand). Not scheduled; ends when done."""
    import threading
    if not os.path.exists(BACKUP_SCRIPT):
        return {"state": "missing", "output": "backup script not found: " + BACKUP_SCRIPT}
    if _run["state"] != "running":
        _run.update(state="running", started=time.time(), output="", code=None)
        threading.Thread(target=_run_backup, daemon=True, name="ag-backup-once").start()
    return {k: _run[k] for k in ("state", "code", "output")}
