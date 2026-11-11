"""
Audit module HTTP routes (module id "audit").
app.py automatically includes this router.

  GET  /api/audit/campaigns       list 8 laser deduplication campaigns
  POST /api/audit/matrix          compute visual audit matrix (JSON)
  POST /api/audit/matrix/html     compute visual audit matrix (rendered HTML)
  POST /api/audit/verify_loss     fast Rule 11 lossless verification
"""

import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from . import audit_matrix_core as core

router = APIRouter(prefix="/api/audit", tags=["audit"])


class AuditRequest(BaseModel):
    source_text: Optional[str] = None
    target_text: Optional[str] = None
    source_path: Optional[str] = None
    target_path: Optional[str] = None
    title: Optional[str] = "Visual Audit & Comparison Matrix"


def _resolve_text(text: Optional[str], path: Optional[str]) -> str:
    """Helper to resolve raw text or read from disk path safely."""
    if text is not None and text.strip():
        return text
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file {path}: {e}")
    if path:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return ""


@router.get("/campaigns")
def get_campaigns():
    """List the 8 laser deduplication campaigns with cluster counts and target anchors."""
    campaigns = core.list_campaigns()
    return {"campaigns": campaigns, "count": len(campaigns)}


@router.post("/matrix")
def compute_matrix(req: AuditRequest):
    """
    Compute full Visual Audit and Comparison Matrix.
    Verifies Rule 11 (zero dropped sentences) and Rule 13 (infrastructure filter).
    """
    src = _resolve_text(req.source_text, req.source_path)
    tgt = _resolve_text(req.target_text, req.target_path)

    if not src and not tgt:
        raise HTTPException(status_code=400, detail="Either source or target text/path must be provided.")

    result = core.compute_audit_matrix(src, tgt)
    return result


@router.post("/matrix/html", response_class=HTMLResponse)
def compute_matrix_html(req: AuditRequest):
    """
    Compute Visual Audit Matrix and return high-contrast Red/Green HTML view.
    """
    src = _resolve_text(req.source_text, req.source_path)
    tgt = _resolve_text(req.target_text, req.target_path)

    if not src and not tgt:
        raise HTTPException(status_code=400, detail="Either source or target text/path must be provided.")

    result = core.compute_audit_matrix(src, tgt)
    html = core.render_html_diff_matrix(result, title=req.title or "Visual Audit Matrix")
    return HTMLResponse(content=html)


@router.post("/verify_loss")
def verify_loss(req: AuditRequest):
    """
    Fast programmatic Rule 11 verification.
    Returns status: PASS/FAIL, omitted count, and preservation percentage.
    """
    src = _resolve_text(req.source_text, req.source_path)
    tgt = _resolve_text(req.target_text, req.target_path)

    result = core.compute_audit_matrix(src, tgt)
    return {
        "rule_11_passed": result["summary"]["rule_11_passed"],
        "verdict": result["summary"]["verdict"],
        "preservation_rate": result["summary"]["preservation_rate"],
        "total_source_sentences": result["summary"]["total_source_sentences"],
        "preserved_count": result["summary"]["preserved_count"],
        "omitted_count": result["summary"]["omitted_count"],
        "omitted_sentences": result["omitted_sentences"],
    }
