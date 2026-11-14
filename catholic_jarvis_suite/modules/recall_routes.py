"""
Recall routes: "where did X go?" search over every conversation and every project markdown file.
Mounted by app.py at /api/recall (auto-included: any modules/*_routes.py that defines `router`).

  GET    /api/recall/search?q=&surface=&role=&scope=&kind=&mode=&sort=&limit=&offset=
  GET    /api/recall/export?q=&surface=&role=&scope=&kind=&mode=&sort=  (CSV download, 2026-11-12)
  GET    /api/recall/status
  POST   /api/recall/rebuild[?force=true]
  GET    /api/recall/saved                 (2026-11-12) list saved searches, newest first
  POST   /api/recall/saved                 save the current filter set under a name
  DELETE /api/recall/saved/{id}

The engine lives in modules/recall_index.py; this file is only the HTTP shell. Search never
rebuilds the index (a rebuild of stale data is an explicit action), and user query text can
never produce a 500: it is turned into quoted FTS5 terms before it reaches SQLite.
"""
import csv
import io
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from modules import recall_index

router = APIRouter(prefix="/api/recall", tags=["recall"])

EXPORT_MAX_ROWS = 2000  # a CSV someone actually opens, not an accidental full-corpus dump
SAVED_SEARCHES_PATH = os.path.join(recall_index.DATA_DIR, "recall_saved_searches.json")


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


@router.get("/export")
def recall_export(
    q: str = Query("", description="same query language as /search"),
    surface: Optional[str] = Query(None, description="CL (Claude), AG (Antigravity) or FILE"),
    role: Optional[str] = Query(None, description="user | assistant (conversations only)"),
    scope: str = Query("all", description="all | conversations | files"),
    kind: Optional[str] = Query(None, description="files only: SUBJECT | INFRASTRUCTURE | PROVENANCE"),
    mode: str = Query("all", description="all (every word) | any | phrase"),
    sort: str = Query("rank", description="rank | newest | oldest"),
):
    """Same search as /search, as a downloadable CSV -- for pulling a result set into a spreadsheet
    or pasting into a dossier, which the JSON-only /search endpoint never offered.

    recall_index.search() itself hard-caps `limit` at 200 per call (confirmed by reading its own
    source, not assumed) -- passing a bigger limit silently gets clamped, not honored. An export
    is exactly the case where more than 200 rows is the point, so this pages internally (offset
    0, 200, 400, ...) up to EXPORT_MAX_ROWS total, rather than quietly handing back the same 200
    rows /search already gives for free."""
    try:
        all_results = []
        total = 0
        offset = 0
        page_size = 200  # recall_index.search()'s own hard cap
        while len(all_results) < EXPORT_MAX_ROWS:
            page = recall_index.search(q, surface=surface, role=role, scope=scope, fkind=kind,
                                        mode=mode, sort=sort, limit=page_size, offset=offset)
            total = page.get("total", 0)
            rows = page.get("results", [])
            all_results.extend(rows)
            if len(rows) < page_size or len(all_results) >= total:
                break
            offset += page_size
        all_results = all_results[:EXPORT_MAX_ROWS]
    except recall_index.IndexMissing:
        return JSONResponse(status_code=409, content={
            "error": "index_missing", "hint": "POST /api/recall/rebuild to build the Recall index"})

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["type", "surface", "role", "date", "title", "rel_path", "line", "score", "snippet"])
    for r in all_results:
        writer.writerow([
            r.get("type", ""), r.get("surface", ""), r.get("role", ""), r.get("date", ""),
            r.get("title", ""), r.get("rel_path", ""), r.get("line", ""), r.get("score", ""),
            (r.get("snippet") or "").replace("\n", " ").strip(),
        ])
    data = {"total": total, "results": all_results}
    truncated = total > len(all_results)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    safe_q = "".join(c if c.isalnum() else "_" for c in (q or "all"))[:40] or "all"
    filename = f"recall_{safe_q}_{stamp}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Recall-Export-Total-Matches": str(data.get("total", 0)),
        "X-Recall-Export-Rows-Included": str(len(data.get("results", []))),
        "X-Recall-Export-Truncated": "true" if truncated else "false",
    }
    return Response(content=buf.getvalue(), media_type="text/csv", headers=headers)


class SavedSearch(BaseModel):
    name: str
    q: str = ""
    surface: Optional[str] = None
    role: Optional[str] = None
    scope: str = "all"
    kind: Optional[str] = None
    mode: str = "all"
    sort: str = "rank"


def _load_saved():
    try:
        with open(SAVED_SEARCHES_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return []


def _write_saved(rows):
    os.makedirs(os.path.dirname(SAVED_SEARCHES_PATH), exist_ok=True)
    tmp = SAVED_SEARCHES_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, SAVED_SEARCHES_PATH)


@router.get("/saved")
def list_saved_searches():
    """A small, local, hand-picked list James builds himself -- not auto-generated from search
    history. Newest first, same convention as every other list in this app."""
    rows = _load_saved()
    return {"searches": sorted(rows, key=lambda r: r.get("created", ""), reverse=True)}


@router.post("/saved")
def save_search(body: SavedSearch):
    if not body.name.strip():
        raise HTTPException(400, "name is required")
    rows = _load_saved()
    row = body.model_dump()
    row["id"] = uuid.uuid4().hex[:12]
    row["created"] = datetime.now(timezone.utc).isoformat()
    rows.append(row)
    _write_saved(rows)
    return row


@router.delete("/saved/{search_id}")
def delete_saved_search(search_id: str):
    rows = _load_saved()
    kept = [r for r in rows if r.get("id") != search_id]
    if len(kept) == len(rows):
        raise HTTPException(404, "no saved search with that id")
    _write_saved(kept)
    return {"deleted": search_id}


@router.get("/status")
def recall_status():
    return recall_index.status()


@router.post("/rebuild")
def recall_rebuild(force: bool = Query(False, description="rebuild even if the fingerprints are unchanged")):
    """Rebuilds only what changed (conversation rows when the log fingerprint moved; file rows
    per changed file). Returns rebuilt=false when nothing changed and force is not set."""
    return recall_index.refresh(force=force)
