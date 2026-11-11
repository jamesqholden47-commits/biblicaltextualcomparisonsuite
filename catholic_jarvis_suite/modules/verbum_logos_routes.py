"""
modules/verbum_logos_routes.py — FastAPI Routes for Verbum & Logos Catholic Study Suite
Part of CatholicJarvis Master Work Suite.
"""

from fastapi import APIRouter, Query, HTTPException, Body
from typing import Dict, Any, Optional

from modules.verbum_logos_core import (
    get_passage_data,
    get_interlinear_data,
    get_passage_guide,
    get_text_comparison,
    list_available_presets,
    export_clipping
)

router = APIRouter(prefix="/api/verbum", tags=["verbum_logos"])


@router.get("/presets")
async def get_presets():
    """Returns list of curated debate and study passages available in the suite."""
    return {"presets": list_available_presets()}


@router.get("/passage")
async def get_passage(ref: str = Query("luke_1_1_4", description="Scripture reference or slug")):
    """Returns multi-translation parallel scripture data for a reference."""
    data = get_passage_data(ref)
    if not data:
        raise HTTPException(status_code=404, detail=f"Passage not found: {ref}")
    return data


@router.get("/interlinear")
async def get_interlinear(ref: str = Query("luke_1_1_4", description="Scripture reference or slug")):
    """Returns word-by-word morphological parsing, lemma, Strong's, and definitions."""
    data = get_interlinear_data(ref)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/guide")
async def get_guide(ref: str = Query("luke_1_1_4", description="Scripture reference or slug")):
    """Generates complete Catholic Passage Guide (Catena Aurea, CCC, Denzinger, Manuscripts)."""
    data = get_passage_guide(ref)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/compare")
async def get_compare(ref: str = Query("luke_1_1_4", description="Scripture reference or slug")):
    """Generates side-by-side text comparison matrix with difference and doctrinal highlights."""
    data = get_text_comparison(ref)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data


@router.get("/export")
async def get_export_clipping(
    ref: str = Query("luke_1_1_4", description="Scripture reference or slug"),
    fmt: str = Query("markdown", description="Export format: markdown or discord")
):
    """Generates Faithlife/Logos personal book clippings or Discord debate cards."""
    text = export_clipping(ref, format_type=fmt)
    return {"reference": ref, "format": fmt, "clipping": text}


@router.post("/export")
async def post_export_clipping(payload: Dict[str, Any] = Body(...)):
    """POST endpoint for exporting clippings."""
    ref = payload.get("ref", "luke_1_1_4")
    fmt = payload.get("format", "markdown")
    text = export_clipping(ref, format_type=fmt)
    return {"reference": ref, "format": fmt, "clipping": text}
