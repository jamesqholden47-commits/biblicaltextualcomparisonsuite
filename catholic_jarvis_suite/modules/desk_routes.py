"""
"Did I Cook?" debate desk: HTTP routes (module id "desk").  Logic lives in desk_core.py.
app.py includes this router automatically (modules/<name>_routes.py defining `router`).

  GET    /api/desk/threads                       list threads
  POST   /api/desk/threads                       create {title, position, handles, opponent, log, seen_sources}
  GET    /api/desk/threads/{id}                  the stored thread
  PUT    /api/desk/threads/{id}                  edit title/position/handles/opponent/seen_sources/log/archived
  POST   /api/desk/threads/{id}/drafts           add a draft {text, label}
  PUT    /api/desk/threads/{id}/drafts/{did}     edit text/label; status "draft" | "dropped" (never "sent")
  GET    /api/desk/threads/{id}/state            reconstructed state (parse + draft matches); ?check=1 adds claim check
  POST   /api/desk/threads/{id}/report           the five debate sections  {paste: stack|dN|custom, text, kinds}
  POST   /api/desk/threads/{id}/brief            brief for Claude/Antigravity {target, socratic, recent, kinds}
  POST   /api/desk/parse                         stateless: {log, handles} -> messages
  POST   /api/desk/check                         stateless: {text, kinds} -> claim-by-claim check
There is no delete route: drafts are dropped, threads archived, nothing is erased.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import desk_core as core

router = APIRouter(prefix="/api/desk", tags=["desk"])

ALL_KINDS = ["SUBJECT", "INFRASTRUCTURE", "PROVENANCE"]


def _kinds(k):
    """None -> SUBJECT only (Rule 13). ['ALL'] -> every kind. The scan stats always say what was scanned."""
    if not k:
        return ("SUBJECT",)
    if any(str(x).upper() == "ALL" for x in k):
        return tuple(ALL_KINDS)
    return tuple(str(x).upper() for x in k)


class NewThread(BaseModel):
    title: str = "Untitled thread"
    position: str = ""
    handles: Optional[List[str]] = None
    opponent: str = ""
    log: str = ""
    seen_sources: Optional[List[str]] = None


class EditThread(BaseModel):
    title: Optional[str] = None
    position: Optional[str] = None
    handles: Optional[List[str]] = None
    opponent: Optional[str] = None
    seen_sources: Optional[List[str]] = None
    log: Optional[str] = None
    archived: Optional[bool] = None


class NewDraft(BaseModel):
    text: str
    label: str = ""


class EditDraft(BaseModel):
    text: Optional[str] = None
    label: Optional[str] = None
    status: Optional[str] = None


class ReportReq(BaseModel):
    paste: str = "stack"
    text: str = ""
    kinds: Optional[List[str]] = None


class BriefReq(BaseModel):
    target: str = "claude"
    socratic: bool = False
    recent: int = 0
    kinds: Optional[List[str]] = None


class ParseReq(BaseModel):
    log: str
    handles: Optional[List[str]] = None


class CheckReq(BaseModel):
    text: str
    kinds: Optional[List[str]] = None


def _thread(tid):
    try:
        return core.get_thread(tid)
    except KeyError:
        raise HTTPException(404, f"no thread {tid}")


@router.get("/threads")
async def threads():
    return {"threads": core.list_threads(), "default_handles": core.DEFAULT_HANDLES}


@router.post("/threads")
async def new_thread(req: NewThread):
    try:
        return core.create_thread(req.title, req.position, req.handles, req.opponent, req.log, req.seen_sources)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/threads/{tid}")
async def get_thread(tid: str):
    return _thread(tid)


@router.put("/threads/{tid}")
async def edit_thread(tid: str, req: EditThread):
    _thread(tid)
    try:
        return core.update_thread(tid, req.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/threads/{tid}/drafts")
async def new_draft(tid: str, req: NewDraft):
    _thread(tid)
    try:
        return core.add_draft(tid, req.text, req.label)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/threads/{tid}/drafts/{did}")
async def edit_draft(tid: str, did: str, req: EditDraft):
    _thread(tid)
    try:
        return core.update_draft(tid, did, req.text, req.label, req.status)
    except KeyError:
        raise HTTPException(404, f"no draft {did} in thread {tid}")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/threads/{tid}/state")
def state(tid: str, check: int = 0, kinds: Optional[str] = None):
    t = _thread(tid)
    ks = _kinds(kinds.split(",") if kinds else None)
    return core.reconstruct(t, ks, check=bool(check))


@router.post("/threads/{tid}/report")
def report(tid: str, req: ReportReq):
    t = _thread(tid)
    try:
        return core.build_report(t, req.paste, req.text, _kinds(req.kinds))
    except KeyError:
        raise HTTPException(404, f"no draft {req.paste} in thread {tid}")


@router.post("/threads/{tid}/brief")
def brief(tid: str, req: BriefReq):
    t = _thread(tid)
    try:
        return core.build_brief(t, req.target, req.socratic, _kinds(req.kinds), req.recent)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))


@router.post("/parse")
async def parse(req: ParseReq):
    return core.parse_log(req.log, req.handles)


@router.post("/check")
def check(req: CheckReq):
    claims = core.extract_claims(req.text)
    if not claims:
        return {"claims": [], "stats": {"files_total": 0}, "note": "no factual-looking sentence found"}
    res, stats = core.check_claims(claims, _kinds(req.kinds))
    for r in res:
        r["suffix"] = core.provenance_suffix(r)
    return {"claims": res, "stats": stats}
