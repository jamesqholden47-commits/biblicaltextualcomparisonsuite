"""
verbum_routes.py - Verbum / Logos API Routes for CatholicJarvis
Path: 09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/modules/verbum_routes.py
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from . import verbum_bridge

router = APIRouter(prefix="/api/verbum", tags=["verbum"])


class LaunchRequest(BaseModel):
    passage: str
    resource: Optional[str] = "gntmorph"


@router.get("/launch")
def launch_passage(passage: str = Query("Luke 1:1-4"), resource: str = Query("gntmorph")):
    """Launch Desktop Verbum/Logos directly to the requested passage and resource."""
    milestone = verbum_bridge.resolve_logos_milestone(passage) or f"Bible.{passage}"
    return verbum_bridge.launch_verbum(milestone, resource)


@router.post("/launch")
def post_launch_passage(req: LaunchRequest):
    milestone = verbum_bridge.resolve_logos_milestone(req.passage) or f"Bible.{req.passage}"
    return verbum_bridge.launch_verbum(milestone, req.resource or "gntmorph")


@router.get("/clipboard")
def get_clipboard_status():
    """Get the latest detected scripture/patristic reference from the Windows clipboard."""
    watcher = verbum_bridge.get_watcher()
    return {
        "watching": watcher.running,
        "latest": watcher.latest_result
    }


@router.post("/clipboard/poll")
def poll_clipboard():
    """Force an immediate poll of the Windows clipboard."""
    text = verbum_bridge.get_windows_clipboard()
    ms = verbum_bridge.resolve_logos_milestone(text)
    strike = None
    if ms:
        from modules import debate_fast_strike
        strike = debate_fast_strike.generate_strike(text)
    return {
        "raw_clipboard": text[:100],
        "milestone": ms,
        "strike": strike
    }
