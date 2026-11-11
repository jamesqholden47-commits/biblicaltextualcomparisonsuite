"""Files API (/api/files): read-only file and Markdown viewer. See modules/files_core.py."""
import mimetypes
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from modules import files_core as core

router = APIRouter(prefix="/api/files", tags=["files"])


def _warm():
    """Walk the roots once at server start (about 6 s) so the first file search or wiki link isn't the slow one.
    One short background thread; it ends when the walk is done."""
    try:
        core.names()
    except Exception:  # noqa: BLE001 — a missing root must never stop the server
        pass


import threading as _threading  # noqa: E402
_threading.Thread(target=_warm, daemon=True, name="files-name-index-warm").start()


def _guard(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except core.Forbidden as e:
        raise HTTPException(403, str(e))
    except FileNotFoundError:
        raise HTTPException(404, "not found")
    except core.TooLarge as e:
        raise HTTPException(413, str(e))
    except IndexError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))


class Pin(BaseModel):
    path: str
    pinned: bool = True


class Note(BaseModel):
    path: str
    text: str


@router.get("/roots")
def roots():
    return {"roots": core.roots(), "state": core.get_state()}


@router.get("/list")
def list_dir(path: str = Query(...)):
    return _guard(core.list_dir, path)


@router.get("/view")
def view(path: str = Query(...), part: int = Query(0, ge=0)):
    return _guard(core.view, path, part)


@router.get("/raw")
def raw(path: str = Query(...)):
    ap = _guard(core.raw, path)
    media = mimetypes.guess_type(ap)[0] or "application/octet-stream"
    headers = {"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"}
    if media in ("text/html", "image/svg+xml", "application/xhtml+xml"):
        # shown in a sandboxed frame by the viewer; the header keeps scripts off even if opened directly
        headers["Content-Security-Policy"] = "sandbox; default-src 'none'; img-src * data:; style-src 'unsafe-inline' *; font-src *"
    return FileResponse(ap, media_type=media, headers=headers)


@router.get("/find")
def find(q: str = Query(""), limit: int = Query(60, ge=1, le=300)):
    return core.find(q, limit)


@router.get("/where")
def where(path: str = Query(...)):
    return _guard(core.where, path)


@router.get("/backlinks")
def backlinks(path: str = Query(...)):
    return _guard(core.backlinks, path)


@router.get("/links/status")
def links_status():
    return core.links_status()


@router.post("/links/build")
def links_build():
    return core.build_links()


@router.post("/reindex")
def reindex():
    n = core.names(force=True)
    return {"files": len(n["all"]), "notes": len(n["by_stem"])}


@router.get("/diff")
def diff(a: str = Query(...), b: str = Query(...)):
    return _guard(core.diff, a, b)


@router.get("/state")
def state():
    return core.get_state()


@router.post("/pin")
def pin(p: Pin):
    return {"pins": _guard(core.set_pin, p.path, p.pinned)}


@router.get("/notes")
def notes(path: str = Query(...)):
    return {"notes": _guard(core.get_notes, path)}


@router.post("/notes")
def add_note(n: Note):
    return {"notes": _guard(core.add_note, n.path, n.text)}


@router.delete("/notes")
def delete_note(path: str = Query(...), id: Optional[str] = Query(None)):
    return {"notes": _guard(core.delete_note, path, id)}
