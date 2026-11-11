"""
Question Ledger routes (module id "ledger"). app.py auto-includes `router`.

  GET  /api/ledger/questions   filters: status, surface, date_from, date_to, text, missed, strong, limit, offset
  GET  /api/ledger/stats       totals, per-status counts, missed counts, build info
  POST /api/ledger/mark        {"id": <stable id>, "status": open|answered|dropped|not-a-question|unreviewed, "note": ""}
  POST /api/ledger/rebuild     re-extract from the logs (about 1 s warm, 4 s cold); marks are never touched
  GET  /api/ledger/export.md   same filters as /questions, returned as a Markdown checklist
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from modules import ledger_core as core

router = APIRouter(prefix="/api/ledger", tags=["ledger"])


class MarkIn(BaseModel):
    id: str
    status: str
    note: Optional[str] = None


def _filtered(status, surface, date_from, date_to, text, missed, strong=None):
    items, doc, orphans = core.merged_items()
    out = core.filter_items(items, status=status, surface=surface, date_from=date_from,
                            date_to=date_to, text=text, missed=missed, strong=strong)
    return out, items, doc, orphans


@router.get("/questions")
def questions(status: Optional[str] = None, surface: Optional[str] = None,
              date_from: Optional[str] = None, date_to: Optional[str] = None,
              text: Optional[str] = None, missed: Optional[bool] = None,
              strong: Optional[bool] = None, limit: int = 100, offset: int = 0):
    out, items, doc, orphans = _filtered(status, surface, date_from, date_to, text, missed, strong)
    limit = max(1, min(limit, 1000))
    offset = max(0, offset)
    return {"total": len(out), "all_total": len(items), "counts": core.counts(out),
            "offset": offset, "limit": limit, "items": out[offset:offset + limit]}


@router.get("/stats")
def stats():
    items, doc, orphans = core.merged_items()
    return {"built": doc.get("built", ""), "n_ledger": len(items),
            "n_missed": sum(1 for q in items if q["missed"]),
            "n_missed_strong": sum(1 for q in items if any(s["strength"] == "strong" for s in q["signals"])),
            "counts": core.counts(items), "orphan_marks": orphans,
            "extraction": doc.get("stats", {}), "missed_signals": doc.get("missed_signals", [])}


@router.post("/mark")
def mark(body: MarkIn):
    try:
        res = core.set_mark(body.id, body.status, body.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": body.id, **res}


@router.post("/rebuild")
def rebuild():
    doc = core.rebuild()
    items, _, orphans = core.merged_items()
    return {"built": doc["built"], "stats": doc["stats"], "orphan_marks": orphans,
            "counts": core.counts(items)}


@router.get("/export.md", response_class=PlainTextResponse)
def export_md(status: Optional[str] = None, surface: Optional[str] = None,
              date_from: Optional[str] = None, date_to: Optional[str] = None,
              text: Optional[str] = None, missed: Optional[bool] = None,
              strong: Optional[bool] = None):
    out, _, _, _ = _filtered(status, surface, date_from, date_to, text, missed, strong)
    return PlainTextResponse(core.to_markdown(out), media_type="text/markdown; charset=utf-8")
