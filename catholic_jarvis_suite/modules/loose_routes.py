"""Loose Ends API (/api/loose). See modules/loose_core.py for what each signal means."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from modules import loose_core as core

router = APIRouter(prefix="/api/loose", tags=["loose"])


class Mark(BaseModel):
    id: str
    status: str
    note: Optional[str] = ""
    merged_into: Optional[str] = ""


@router.get("/summary")
def get_summary():
    reg = core.load_registry()
    return core.summary(reg, core.load_status()["marks"])


@router.get("/items")
def get_items(area: Optional[str] = None, kind: Optional[str] = None, text: Optional[str] = None,
              mark: Optional[str] = None, signal: Optional[str] = None, thread: Optional[str] = None,
              changed_since: Optional[str] = None, sort: str = "score",
              limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    reg = core.load_registry()
    return core.query(reg, core.load_status()["marks"], area=area, kind=kind, text=text, mark=mark, signal=signal,
                      thread=thread, changed_since=changed_since, sort=sort, limit=limit, offset=offset)


@router.get("/threads")
def get_threads(limit: int = Query(60, ge=1, le=500), text: Optional[str] = None):
    reg = core.load_registry()
    by_id = {d["id"]: d for d in reg.get("docs", [])}
    qs = reg.get("questions", {})
    marks = core.load_status()["marks"]
    out = []
    for t in reg.get("threads", []):
        if text and not all(w.lower() in " ".join(t["label"]) for w in text.split()):
            continue
        docs = [by_id[i] for i in t["doc_ids"] if i in by_id]
        out.append(dict(t, docs=[{"id": d["id"], "title": d["title"], "path": d["path"], "mtime": d["mtime"],
                                  "integrated": bool(d["integrated_into"]), "open_items": len(d["open_items"]),
                                  "status": marks.get(d["id"], {}).get("status", "unreviewed")}
                                 for d in sorted(docs, key=lambda d: d["mtime"])],
                        questions=[qs[q] for q in t.get("question_ids", []) if q in qs][:20]))
        if len(out) >= limit:
            break
    return {"total": len(reg.get("threads", [])), "threads": out}


@router.get("/open_items")
def get_open_items(area: Optional[str] = None, text: Optional[str] = None, limit: int = Query(300, ge=1, le=3000)):
    reg = core.load_registry()
    rows = []
    words = [w.lower() for w in (text or "").split()]
    for d in reg.get("docs", []):
        if area and d["area"] != area:
            continue
        for it in d["open_items"]:
            if words and not all(w in it["text"].lower() for w in words):
                continue
            rows.append({"doc_id": d["id"], "title": d["title"], "path": d["path"], "kind": d["kind"],
                         "mtime": d["mtime"], "section": it["section"], "text": it["text"]})
    rows.sort(key=lambda r: r["mtime"], reverse=True)
    return {"total": len(rows), "items": rows[:limit]}


@router.post("/mark")
def post_mark(m: Mark):
    try:
        return {"ok": True, "mark": core.set_mark(m.id, m.status, m.note or "", m.merged_into or "")}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rebuild")
def post_rebuild():
    reg = core.rebuild()
    return {"ok": True, "n_docs": reg["n_docs"], "seconds": reg["seconds"], "threads": len(reg["threads"])}


@router.get("/export.md", response_class=PlainTextResponse)
def get_export():
    reg = core.load_registry()
    return core.export_md(reg, core.load_status()["marks"])
