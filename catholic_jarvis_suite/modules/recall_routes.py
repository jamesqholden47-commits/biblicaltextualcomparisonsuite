"""
Recall routes: "where did X go?" search over every conversation and every project markdown file.
Mounted by app.py at /api/recall (auto-included: any modules/*_routes.py that defines `router`).

  GET  /api/recall/search?q=&surface=&role=&scope=&kind=&mode=&sort=&limit=&offset=
  GET  /api/recall/status
  POST /api/recall/rebuild[?force=true]

The engine lives in modules/recall_index.py; this file is only the HTTP shell. Search never
rebuilds the index (a rebuild of stale data is an explicit action), and user query text can
never produce a 500: it is turned into quoted FTS5 terms before it reaches SQLite.
"""
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from modules import recall_index

router = APIRouter(prefix="/api/recall", tags=["recall"])


@router.get("/search")
def recall_search(
    q: str = Query("", description="words to find; \"quoted text\" is a phrase; term* is a prefix"),
    surface: Optional[str] = Query(None, description="CL (Claude), AG (Antigravity) or FILE"),
    role: Optional[str] = Query(None, description="user | assistant (conversations only)"),
    scope: str = Query("all", description="all | conversations | files"),
    kind: Optional[str] = Query(None, description="files only: SUBJECT | INFRASTRUCTURE | PROVENANCE"),
    mode: str = Query("all", description="all (every word) | any | phrase"),
    sort: str = Query("rank", description="rank | newest | oldest"),
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        return recall_index.search(q, surface=surface, role=role, scope=scope, fkind=kind, mode=mode,
                                   sort=sort, limit=limit, offset=offset)
    except recall_index.IndexMissing:
        return JSONResponse(status_code=409, content={
            "error": "index_missing", "hint": "POST /api/recall/rebuild to build the Recall index",
            "q": q, "total": 0, "results": []})


@router.get("/status")
def recall_status():
    return recall_index.status()


@router.post("/rebuild")
def recall_rebuild(force: bool = Query(False, description="rebuild even if the fingerprints are unchanged")):
    """Rebuilds only what changed (conversation rows when the log fingerprint moved; file rows
    per changed file). Returns rebuilt=false when nothing changed and force is not set."""
    return recall_index.refresh(force=force)
