"""Bookbinder API (/api/books). See modules/books_core.py for the pipeline."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from modules import books_core as core

router = APIRouter(prefix="/api/books", tags=["books"])


class Move(BaseModel):
    source_ids: List[str]
    volume: Optional[str] = None
    chapter: Optional[str] = None


class Exclude(BaseModel):
    source_ids: List[str]
    excluded: bool = True


class Rename(BaseModel):
    kind: str
    id: str
    title: str


class Final(BaseModel):
    final: bool = True
    note: Optional[str] = ""


def _plan():
    p = core.load_plan()
    if not p:
        raise HTTPException(503, "no plan yet: POST /api/books/replan")
    return p


@router.get("/summary")
def summary():
    return core.plan_summary(_plan())


@router.get("/search")
def search(q: str = Query("", description="words that must all appear in the chapter or volume title"),
           limit: int = Query(20, ge=1, le=200)):
    """Chapters whose title (or volume title) contains every word of q. Used by the Ctrl+K palette."""
    words = [w for w in q.lower().split() if w]
    out, total = [], 0
    for v in _plan()["volumes"]:
        for c in v["chapters"]:
            hay = (c["title"] + " " + v.get("title", "") + " " + c["id"]).lower()
            if words and all(w in hay for w in words):
                total += 1
                if len(out) < limit:
                    out.append({"id": c["id"], "title": c["title"], "volume": v["id"], "volume_title": v.get("title", ""),
                                "status": c.get("state", ""), "n_sources": c["n_sources"], "words": c["words"]})
    return {"q": q, "total": total, "chapters": out}


@router.get("/volume/{vid}")
def volume(vid: str):
    p = _plan()
    v = next((x for x in p["volumes"] if x["id"] == vid), None)
    if not v:
        raise HTTPException(404, vid)
    return {k: v[k] for k in v if k != "chapters"} | {"chapters": [{k: c[k] for k in c if k != "sources"} for c in v["chapters"]]}


@router.get("/chapter/{cid}")
def chapter(cid: str):
    p = _plan()
    v, c = core.find_chapter(p, cid)
    if not c:
        raise HTTPException(404, cid)
    srcs = [dict(p["sources"][s], id=s) for s in c["sources"] if s in p["sources"]]
    return {"volume": {"id": v["id"], "title": v["title"]}, "chapter": c, "sources": srcs, "dir": core.chapter_dir(c)}


@router.get("/unsorted")
def unsorted(text: Optional[str] = None, origin: Optional[str] = None, limit: int = Query(60, ge=1, le=500),
             offset: int = Query(0, ge=0)):
    p = _plan()
    words = [w.lower() for w in (text or "").split()]
    rows = []
    for sid in p["unsorted"]:
        s = p["sources"].get(sid)
        if not s or (origin and s["origin"] != origin):
            continue
        if words and not all(w in (s["title"] + " " + (s.get("folder") or "")).lower() for w in words):
            continue
        rows.append(dict(s, id=sid))
    rows.sort(key=lambda s: -(s.get("score") or 0))
    return {"total": len(rows), "items": rows[offset:offset + limit],
            "volumes": [{"id": v["id"], "title": v["title"]} for v in p["volumes"]]}


@router.post("/replan")
def replan():
    p = core.build_plan()
    return {"ok": True, "seconds": p["seconds"], "summary": core.plan_summary(p)}


@router.post("/move")
def move(m: Move):
    errors = []
    for sid in m.source_ids:
        try:
            core.move_source(sid, m.volume, m.chapter)
        except ValueError as e:
            errors.append({"id": sid, "error": str(e)})
    return {"ok": not errors, "moved": len(m.source_ids) - len(errors), "errors": errors,
            "note": "Moves apply on the next re-plan (POST /api/books/replan)."}


@router.post("/accept_suggestions")
def accept_suggestions(min_score: int = Query(3, ge=1, le=50), limit: int = Query(500, ge=1, le=20000)):
    """Unsorted sources whose best candidate volume scores >= min_score and leads the runner-up are
    moved to that volume (as overrides James can undo one by one)."""
    p = _plan()
    n = 0
    for sid in p["unsorted"]:
        s = p["sources"].get(sid) or {}
        cands = sorted((s.get("candidates") or {}).items(), key=lambda kv: -kv[1])
        if not cands or cands[0][1] < min_score or (len(cands) > 1 and cands[0][1] == cands[1][1]):
            continue
        core.move_source(sid, cands[0][0])
        n += 1
        if n >= limit:
            break
    return {"ok": True, "moved": n, "note": "Re-plan to see them placed in chapters."}


@router.post("/exclude")
def exclude(e: Exclude):
    for sid in e.source_ids:
        core.exclude_source(sid, e.excluded)
    return {"ok": True}


@router.post("/rename")
def rename(r: Rename):
    if r.kind not in ("chapter", "volume"):
        raise HTTPException(400, "kind must be chapter or volume")
    core.rename(r.kind, r.id, r.title)
    return {"ok": True}


@router.post("/chapter/{cid}/approve")
def approve(cid: str):
    try:
        return {"ok": True, "frozen": core.approve(cid)}
    except KeyError:
        raise HTTPException(404, cid)


@router.post("/chapter/{cid}/unapprove")
def unapprove(cid: str):
    try:
        return {"ok": core.unapprove(cid)}
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.post("/chapter/{cid}/brief")
def brief(cid: str, overwrite: bool = False):
    try:
        return core.write_brief(cid, overwrite=overwrite)
    except KeyError:
        raise HTTPException(404, cid)
    except ValueError as e:
        raise HTTPException(409, str(e))
    except FileExistsError as e:
        raise HTTPException(409, f"brief exists: {e} (pass overwrite=true to rewrite it)")


@router.post("/chapter/{cid}/check")
def check(cid: str):
    try:
        return core.run_checks(cid)
    except KeyError:
        raise HTTPException(404, cid)
    except FileNotFoundError as e:
        raise HTTPException(409, f"no draft yet: {e}")


@router.post("/chapter/{cid}/final")
def final(cid: str, f: Final):
    p = _plan()
    v, c = core.find_chapter(p, cid)
    if not c:
        raise HTTPException(404, cid)
    if f.final and c["state"] not in ("checked", "judged", "final"):
        raise HTTPException(409, f"chapter is '{c['state']}': run the checks first")
    core.set_final(cid, f.final, f.note or "")
    return {"ok": True}


@router.post("/volume/{vid}/assemble")
def assemble(vid: str):
    try:
        return core.assemble_volume(vid)
    except KeyError:
        raise HTTPException(404, vid)


@router.get("/oversized")
def oversized():
    p = _plan()
    return {"items": p.get("oversized", []), "words": p["pool"].get("oversized_words", 0)}


@router.post("/split_oversized")
def split_oversized(limit: int = Query(100, ge=1, le=1000)):
    """Split every held-back oversized file into verbatim parts (proved lossless by sha256), then re-plan."""
    p = _plan()
    done = []
    for o in p.get("oversized", [])[:limit]:
        r = core.split_source(o["path"], o["title"], o["origin"])
        r["verified"] = core.verify_split(r["folder"])
        done.append(dict(r, source=o["path"]))
    plan = core.build_plan()
    return {"split": len(done), "all_verified": all(d["verified"] for d in done), "items": done,
            "summary": core.plan_summary(plan)}


@router.get("/where")
def where(ids: str = Query(..., description="comma-separated source ids (Loose Ends ids work)")):
    """Which volume and chapter each source is planned into (or unsorted / not in the pool)."""
    p = _plan()
    want = set(i for i in ids.split(",") if i)
    out = {i: {"state": "not in pool"} for i in want}
    for sid in p["unsorted"]:
        if sid in want:
            out[sid] = {"state": "unsorted"}
    for v in p["volumes"]:
        for c in v["chapters"]:
            for sid in c["sources"]:
                if sid in want:
                    out[sid] = {"state": c["state"], "volume": v["id"], "volume_title": v["title"],
                                "chapter": c["id"], "chapter_title": c["title"]}
    for sid in want:
        s = p["sources"].get(sid)
        if s and s.get("integrated") and out[sid]["state"] == "not in pool":
            out[sid] = {"state": "already in a book"}
    return out


@router.get("/next")
def next_up(n: int = Query(5, ge=1, le=50)):
    """What to do next, in order: chapters that are drafted but unchecked, briefed but undrafted,
    approved but unbriefed, then the largest proposed chapters of the earliest volumes."""
    p = _plan()
    order = {"drafted": 0, "drafting": 1, "briefed": 2, "approved": 3, "checked": 4, "proposed": 5}
    rows = []
    for vi, v in enumerate(p["volumes"]):
        for c in v["chapters"]:
            if c["state"] in order:
                rows.append((order[c["state"]], vi, -c["words"], c, v))
    rows.sort(key=lambda r: r[:3])
    action = {"drafted": "run checks", "drafting": "continue the draft (launch the brief again)", "briefed": "launch the brief",
              "approved": "write the brief", "checked": "judge read, then mark final", "proposed": "review sources and approve"}
    return {"items": [{"chapter": c["id"], "title": c["title"], "volume": v["title"], "state": c["state"],
                       "action": action[c["state"]], "sources": c["n_sources"], "words": c["words"]} for *_, c, v in rows[:n]]}
