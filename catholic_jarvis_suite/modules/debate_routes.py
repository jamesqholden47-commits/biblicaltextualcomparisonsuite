"""Debate threads API (/api/debate). See modules/debate_core.py."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from modules import debate_core as core, desk_core

router = APIRouter(prefix="/api/debate", tags=["debate"])


class Drop(BaseModel):
    point_id: str
    dropped: bool = True
    note: Optional[str] = ""


class Title(BaseModel):
    title: str = ""


class Hide(BaseModel):
    hidden: bool = True


class Join(BaseModel):
    a: str
    b: str


class Split(BaseModel):
    snap: str


class Text(BaseModel):
    text: str


def _get(tid):
    try:
        return core.get_thread(tid)
    except KeyError:
        raise HTTPException(404, "no such thread (the logs may have been re-harvested)")


@router.get("/threads")
def threads(hidden: int = 0):
    return core.list_threads(include_hidden=bool(hidden))


@router.post("/harvest")
def harvest():
    h = core.harvest(force=True)
    return {"seconds": h["seconds"], "n_snapshots": h["n_snapshots"], "n_threads": h["n_threads"]}


@router.get("/threads/{tid}")
def thread(tid: str):
    """The thread, with each point's Markdown rendered (files_md: escaped, safe) and the claims in their latest."""
    from modules import files_md
    t = dict(_get(tid))
    t["points"] = [dict(p, html=files_md.render(p.get("unsent_text") or p["text"], with_frontmatter=False)["html"])
                   for p in t["points"]]
    tl = t.get("their_latest")
    if tl:
        text = "\n".join(t["messages"][i]["text"] for i in tl["messages"])
        claims = []
        for c in desk_core.extract_claims(text)[:40]:
            sig = [f"{k}: {', '.join(map(str, c[k]))}" for k in ("refs", "quotes", "numbers", "dates") if c.get(k)]
            claims.append({"text": c.get("text", ""), "signals": sig})
        tl = dict(tl, claims=claims)
        t["their_latest"] = tl
    return t


@router.get("/threads/{tid}/brief")
def brief(tid: str, socratic: int = 0, tail: int = Query(40, ge=5, le=400)):
    _get(tid)
    return {"text": core.brief(tid, socratic=bool(socratic), tail=tail)}


@router.post("/threads/{tid}/drop")
def drop(tid: str, d: Drop):
    t = _get(tid)
    if not any(p["id"] == d.point_id for p in t["points"]):
        raise HTTPException(404, "no such point in this thread")
    core.set_mark("dropped", d.point_id, ({"note": d.note or "", "thread": tid} if d.dropped else None))
    return _get(tid)


@router.post("/threads/{tid}/title")
def title(tid: str, t: Title):
    _get(tid)
    core.set_mark("titles", tid, t.title.strip() or None)
    return _get(tid)


@router.post("/threads/{tid}/hide")
def hide(tid: str, h: Hide):
    _get(tid)
    core.set_mark("hidden", tid, True if h.hidden else None)
    return {"ok": True}


@router.post("/join")
def join(j: Join):
    core.join(j.a, j.b)
    return {"n_threads": core.harvest()["n_threads"]}


@router.post("/split")
def split(s: Split):
    core.split_at(s.snap)
    return {"n_threads": core.harvest()["n_threads"]}


@router.post("/discord")
def discord(t: Text):
    """A reply made Discord-ready: formatting Discord can't show is simplified, then split under 2,000 characters."""
    text, changes = desk_core.discordify(t.text)
    parts = desk_core.split_for_discord(text)
    return {"text": text, "changes": changes, "parts": parts, "problems": desk_core.paste_problems(text)}


@router.get("/fast_strike")
def get_fast_strike(q: str = Query("ehrman", description="Topic or interlocutor assertion")):
    """Instant 3-part Discord-ready markdown payload for debates."""
    from modules import debate_fast_strike
    return debate_fast_strike.generate_strike(q)


@router.post("/fast_strike")
def post_fast_strike(t: Text):
    """Instant 3-part Discord-ready markdown payload for debates via POST."""
    from modules import debate_fast_strike
    return debate_fast_strike.generate_strike(t.text)


@router.get("/fast_strike/list")
def list_fast_strikes():
    """List available debate fast-strike defeater topics."""
    from modules import debate_fast_strike
    return [{"id": s["id"], "title": s["title"], "keywords": s["keywords"]} for s in debate_fast_strike.STRIKE_REGISTRY]

