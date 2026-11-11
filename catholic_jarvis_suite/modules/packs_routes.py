"""Argument packs and objection drills API (/api/packs, /api/drill). See modules/packs_core.py."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from modules import packs_core as core

router = APIRouter(tags=["packs"])


class Grade(BaseModel):
    id: str
    grade: int


@router.get("/api/packs")
def packs():
    return core.list_packs()


@router.get("/api/packs/{pid}")
def pack(pid: str):
    try:
        return core.get_pack(pid)
    except KeyError:
        raise HTTPException(404, "no such pack")


@router.get("/api/drill/queue")
def queue(topic: Optional[str] = None, limit: int = Query(20, ge=1, le=200)):
    return core.drill_queue(topic or None, limit)


@router.post("/api/drill/grade")
def grade(g: Grade):
    try:
        return core.grade(g.id, g.grade)
    except KeyError:
        raise HTTPException(404, "no such card")
    except ValueError as e:
        raise HTTPException(400, str(e))
