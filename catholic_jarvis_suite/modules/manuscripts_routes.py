"""
manuscripts_routes.py - FastAPI Routes for CatholicJarvis Manuscript Paleography Suite
Path: 09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/modules/manuscripts_routes.py
Author: Antigravity Autonomous Academic Fleet
Date: 2026-10-09
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from modules import manuscripts_core as core

router = APIRouter(tags=["manuscripts"])


class CiteRequest(BaseModel):
    ms_id: str
    folio_id: str
    style: Optional[str] = "sbl"


@router.get("/api/manuscripts")
def get_manuscripts():
    """List all registered biblical and patristic manuscripts."""
    return core.list_manuscripts()


@router.get("/api/manuscripts/search")
def search_manuscripts(q: str = Query(..., min_length=1)):
    """Search manuscripts, passages, and words for matching keywords."""
    return core.search_manuscripts(q)


@router.get("/api/manuscripts/{ms_id}")
def get_manuscript(ms_id: str):
    """Retrieve full record for a specific manuscript."""
    try:
        return core.get_manuscript(ms_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api/manuscripts/{ms_id}/folio/{folio_id}")
def get_folio(ms_id: str, folio_id: str):
    """Retrieve detailed folio record with transcriptions and morphological alignment."""
    try:
        return core.get_folio(ms_id, folio_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/api/manuscripts/cite")
def generate_citation(req: CiteRequest):
    """Generate academic citations in SBL, Chicago, or BibTeX format with IIIF deep links."""
    try:
        return core.format_citation(req.ms_id, req.folio_id, req.style or "sbl")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
