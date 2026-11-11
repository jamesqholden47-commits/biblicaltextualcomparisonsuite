"""
Episodes module HTTP routes (module id "episodes"). Task C005.
app.py includes this router automatically.

  GET  /api/episodes                list all episodes with live computed gate status
  GET  /api/episodes/{id}/fidelity  detailed fidelity report (flags, reviewed exceptions, stale reviews)
  POST /api/episodes/{id}/build     trigger episode audio build
"""
import os
import sys
import json
from fastapi import APIRouter, HTTPException

from modules.paths_config import get_path

FIDELITY_CHECK_DIR = os.path.join(
    get_path("dissertation_project"), "09_APPS_CATHOLICJARVIS", "_LOG_ANALYSIS_2026-10-03"
)
if FIDELITY_CHECK_DIR not in sys.path:
    sys.path.insert(0, FIDELITY_CHECK_DIR)

from tools import build_episode as builder

router = APIRouter(prefix="/api/episodes", tags=["episodes"])

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(HERE, "data", "podcast_scripts")
EPISODES_DIR = os.path.join(HERE, "data", "podcast_episodes")


@router.get("")
def list_episodes():
    """List every podcast script and generated episode with live fidelity gate status."""
    if not os.path.exists(SCRIPTS_DIR):
        return {"episodes": [], "count": 0}

    results = []
    script_files = sorted([f for f in os.listdir(SCRIPTS_DIR) if f.endswith(".script.json")])

    for sf in script_files:
        path = os.path.join(SCRIPTS_DIR, sf)
        try:
            with open(path, "r", encoding="utf-8") as f:
                script = json.load(f)
            ep_id = script.get("id") or sf.replace(".script.json", "")
            has_audio = os.path.exists(os.path.join(EPISODES_DIR, f"{ep_id}.mp3"))
            has_manifest = os.path.exists(os.path.join(EPISODES_DIR, f"{ep_id}.json"))

            # Run live gate check
            try:
                passed, kept, cleared, stale, ok = builder.run_gate(script, path)
                status = "PASS" if passed else ("STALE" if stale else "FLAGS")
            except Exception as e:
                status = "ERROR"
                kept, cleared, stale = [], [], []

            results.append({
                "id": ep_id,
                "title": script.get("title", ep_id),
                "script_file": sf,
                "total_turns": len(script.get("turns", [])),
                "has_audio": has_audio,
                "has_manifest": has_manifest,
                "gate_status": status,
                "open_flags": len(kept),
                "cleared_flags": len(cleared),
                "stale_reviews": len(stale)
            })
        except Exception:
            pass

    return {"episodes": results, "count": len(results)}


@router.get("/{ep_id}/fidelity")
def episode_fidelity(ep_id: str):
    """Detailed fidelity status for an episode."""
    script_path = os.path.join(SCRIPTS_DIR, f"{ep_id}.script.json")
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"Script for episode {ep_id} not found")

    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    try:
        passed, kept, cleared, stale, ok = builder.run_gate(script, script_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fidelity gate error: {e}")

    return {
        "id": ep_id,
        "title": script.get("title", ep_id),
        "source_document": script.get("source_path"),
        "passed": passed,
        "open_flags": [
            {"turn_id": f[0], "kind": f[1], "figure": f[2], "podcast_sentence": f[3], "source_line": f[4]}
            for f in kept
        ],
        "cleared_exceptions": [
            {"turn_id": f[0], "kind": f[1], "figure": f[2], "podcast_sentence": f[3]}
            for f in cleared
        ],
        "stale_reviews": stale
    }


@router.post("/{ep_id}/build")
def build_ep(ep_id: str, dry_run: bool = False, mock_tts: bool = False):
    """Build episode audio."""
    script_path = os.path.join(SCRIPTS_DIR, f"{ep_id}.script.json")
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail=f"Script for episode {ep_id} not found")

    try:
        res = builder.build_episode(script_path, dry_run=dry_run, mock_tts=mock_tts)
        return {"status": "success", "result": res}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
