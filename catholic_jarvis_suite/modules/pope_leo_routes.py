"""
Pope Leo XIV Tracker HTTP routes (module id "pope_leo").
Included automatically in CatholicJarvis Master Work Suite via modules/*_routes.py discovery.

Endpoints:
  GET  /api/pope-leo/feed           Returns complete papal feed and latest status
  GET  /api/pope-leo/today          Returns today's (4 Oct 2026) full liturgical tracking
  GET  /api/pope-leo/processions    Returns today's tracked processions & pilgrimages
  GET  /api/pope-leo/videos         Returns Vatican media live streams and replays
  GET  /api/pope-leo/documents      Returns encyclicals, exhortations, motu proprios, DDF notes
  GET  /api/pope-leo/moves          Returns appointments, consistories, and curial actions
  GET  /api/pope-leo/abraccio       Returns unscripted/airplane press conference remarks
  GET  /api/pope-leo/analytics      Returns 4-tier magisterial assent analytics & pattern detection
  GET  /api/pope-leo/homilies       Returns list of major homilies & liturgies with filter
  POST /api/pope-leo/refresh        Trigger live verification against vatican.va
"""

import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from . import pope_leo_core as core

router = APIRouter(prefix="", tags=["pope_leo"])


@router.get("/api/pope-leo/feed")
def get_pope_leo_feed():
    """Return complete papal feed for Pope Leo XIV."""
    return core.get_feed()


@router.get("/api/pope-leo/today")
def get_pope_leo_today():
    """Return detailed tracking for today's celebrations (4 October 2026)."""
    feed = core.get_feed()
    return {
        "pontiff": feed.get("pontiff"),
        "date": feed.get("current_date"),
        "liturgical_day": feed.get("liturgical_day"),
        "calendar_note": feed.get("calendar_note"),
        "events": feed.get("today_events", [])
    }


@router.get("/api/pope-leo/processions")
def get_today_processions():
    """Extract and return all processions, pilgrimages, and public blessings tracked for today."""
    feed = core.get_feed()
    events = feed.get("today_events", [])
    processions = []
    for ev in events:
        for p in ev.get("processions_and_pilgrimages", []):
            item = dict(p)
            item["parent_event"] = ev.get("title")
            item["parent_location"] = ev.get("location")
            processions.append(item)
    return {
        "date": feed.get("current_date"),
        "count": len(processions),
        "processions": processions
    }


@router.get("/api/pope-leo/videos")
def get_pope_leo_videos():
    """Return Vatican media live streams, today's liturgy video replays, and backup links."""
    return core.get_video_streams()


@router.get("/api/pope-leo/backups")
def get_pope_leo_backups():
    """Return verified working stream backup URLs and broadcast launch links."""
    backups = core.get_backup_urls()
    streams = core.get_video_streams()
    return {
        "count": len(backups),
        "backups": backups,
        "troubleshooting": streams.get("troubleshooting_advisory", {})
    }


@router.get("/api/pope-leo/documents")
def get_pope_leo_documents(level: Optional[str] = Query(None)):
    """Return major magisterial documents, encyclicals, exhortations, and motu proprios."""
    feed = core.get_feed()
    docs = feed.get("magisterial_documents", [])
    if level:
        lvl = level.lower()
        docs = [d for d in docs if lvl in d.get("level", "").lower()]
    return {"count": len(docs), "documents": docs}


@router.get("/api/pope-leo/moves")
def get_pope_leo_moves():
    """Return appointments, consistories, diplomatic actions, and curial moves."""
    feed = core.get_feed()
    moves = feed.get("ecclesial_moves", [])
    return {"count": len(moves), "moves": moves}


@router.get("/api/pope-leo/abraccio")
def get_pope_leo_abraccio():
    """Return 'A Braccio' unscripted remarks and in-flight press conferences log."""
    feed = core.get_feed()
    remarks = feed.get("abraccio_log", [])
    return {"count": len(remarks), "remarks": remarks}


@router.get("/api/pope-leo/analytics")
def get_pope_leo_analytics():
    """Return 4-tier magisterial assent analytics and emerging doctrinal pattern detection."""
    feed = core.get_feed()
    return feed.get("doctrinal_analytics", {})


@router.get("/api/pope-leo/homilies")
def get_tracked_homilies(query: Optional[str] = Query(None)):
    """List tracked homilies and liturgies with optional search filter."""
    feed = core.get_feed()
    all_liturgies = []

    # Include today's events
    for ev in feed.get("today_events", []):
        all_liturgies.append({
            "date": ev.get("date"),
            "title": ev.get("title"),
            "type": ev.get("type"),
            "location": ev.get("location"),
            "url": ev.get("url_en") or ev.get("url_it")
        })

    # Include recent major liturgies
    for lit in feed.get("recent_major_liturgies", []):
        all_liturgies.append(lit)

    if query:
        q = query.lower()
        all_liturgies = [
            l for l in all_liturgies
            if q in l.get("title", "").lower() or q in l.get("date", "").lower()
        ]

    return {"count": len(all_liturgies), "homilies": all_liturgies}


@router.post("/api/pope-leo/refresh")
def refresh_vatican_feed():
    """Trigger dynamic live check against Vatican channels."""
    updated = core.refresh_feed_from_vatican()
    return {"status": "refreshed", "feed": updated}
