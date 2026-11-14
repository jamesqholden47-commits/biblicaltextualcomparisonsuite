"""Lazy-loading SQLite + FTS5 API routes for Plenary Logos Suite.

Replaces monolithic 116 MB JSON/HTML parsing with sub-10ms per-chapter
retrieval and BM25 full-text search across verses, study notes, and
text-critical apparatus.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/plenary", tags=["plenary-db"])

_HERE = Path(__file__).resolve()
_DEFAULT_DB = _HERE.parents[3] / "web_app" / "plenary_logos.sqlite"


def get_db_path() -> Path:
    env_override = os.environ.get("PLENARY_SQLITE_PATH", "").strip()
    return Path(env_override) if env_override else _DEFAULT_DB


def _connect() -> sqlite3.Connection:
    db_path = get_db_path()
    if not db_path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Plenary SQLite database not found at {db_path}. Run web_app/build_plenary_sqlite.py.",
        )
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_FTS_SAFE_RE = re.compile(r"[^\w\s\u0370-\u03FF\u1F00-\u1FFF\u0590-\u05FF\"*]+", re.UNICODE)


def _sanitize_fts_query(q: str) -> str:
    cleaned = _FTS_SAFE_RE.sub(" ", q).strip()
    if not cleaned:
        return ""
    tokens = [t for t in cleaned.split() if t]
    return " ".join(tokens)


@router.get("/status")
def plenary_db_status():
    db_path = get_db_path()
    if not db_path.exists():
        return {"available": False, "db_path": str(db_path)}
    conn = _connect()
    try:
        meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM meta")}
        return {
            "available": True,
            "db_path": str(db_path),
            "size_bytes": db_path.stat().st_size,
            "meta": meta,
        }
    finally:
        conn.close()


@router.get("/books")
def plenary_books():
    conn = _connect()
    try:
        books = [
            dict(r)
            for r in conn.execute(
                "SELECT id, name, abbr, division, testament, lang, deuterocanon, chapter_count FROM books ORDER BY sort_order"
            )
        ]
        translations = [
            dict(r)
            for r in conn.execute(
                "SELECT id, short, name, lang, scope, approval, tier_badge, grp FROM translations"
            )
        ]
        return {"books": books, "translations": translations}
    finally:
        conn.close()


@router.get("/chapter/{book_id}/{chapter}")
def plenary_chapter(
    book_id: str,
    chapter: int,
    translations: Optional[str] = Query(
        default=None,
        description="Comma-separated translation IDs (e.g. he,gr,vul,dra,rsv2ce). Omit for all.",
    ),
):
    conn = _connect()
    try:
        book_row = conn.execute(
            "SELECT id, name, abbr, testament, lang, chapter_count FROM books WHERE id = ?",
            (book_id,),
        ).fetchone()
        if not book_row:
            raise HTTPException(status_code=404, detail=f"Unknown book_id: {book_id}")
        if chapter < 1 or chapter > int(book_row["chapter_count"]):
            raise HTTPException(
                status_code=404,
                detail=f"Chapter {chapter} out of range for {book_id} (1..{book_row['chapter_count']})",
            )

        tr_filter = [t.strip() for t in translations.split(",") if t.strip()] if translations else []
        if tr_filter:
            placeholders = ",".join("?" for _ in tr_filter)
            v_rows = conn.execute(
                f"SELECT verse, translation_id, text FROM verses "
                f"WHERE book_id = ? AND chapter = ? AND translation_id IN ({placeholders}) "
                f"ORDER BY verse, translation_id",
                (book_id, chapter, *tr_filter),
            ).fetchall()
        else:
            v_rows = conn.execute(
                "SELECT verse, translation_id, text FROM verses "
                "WHERE book_id = ? AND chapter = ? ORDER BY verse, translation_id",
                (book_id, chapter),
            ).fetchall()

        verses_by_num: dict[int, dict[str, str]] = {}
        for r in v_rows:
            v_num = int(r["verse"])
            verses_by_num.setdefault(v_num, {})[r["translation_id"]] = r["text"]

        note_counts = {
            int(r["verse"]): int(r["cnt"])
            for r in conn.execute(
                "SELECT verse, COUNT(*) AS cnt FROM notes WHERE book_id = ? AND chapter = ? GROUP BY verse",
                (book_id, chapter),
            )
        }

        apparatus_items = [
            json.loads(r["payload_json"])
            for r in conn.execute(
                "SELECT payload_json FROM apparatus WHERE book_id = ? AND chapter = ?",
                (book_id, chapter),
            )
        ]

        vorlagen_items = [
            json.loads(r["payload_json"])
            for r in conn.execute(
                "SELECT payload_json FROM bibcrit_vorlagen WHERE book_id = ? AND chapter = ?",
                (book_id, chapter),
            )
        ]

        return {
            "book": dict(book_row),
            "chapter": chapter,
            "verses": verses_by_num,
            "note_counts": note_counts,
            "apparatus": apparatus_items,
            "bibcrit_vorlagen": vorlagen_items,
        }
    finally:
        conn.close()


@router.get("/verse_notes/{book_id}/{chapter}/{verse}")
def plenary_verse_notes(book_id: str, chapter: int, verse: int):
    conn = _connect()
    try:
        notes = [
            dict(r)
            for r in conn.execute(
                "SELECT src, tier, kind, marker, anchor_word, title, body "
                "FROM notes WHERE book_id = ? AND chapter = ? AND verse = ? ORDER BY src, id",
                (book_id, chapter, verse),
            )
        ]
        apparatus = [
            json.loads(r["payload_json"])
            for r in conn.execute(
                "SELECT payload_json FROM apparatus WHERE book_id = ? AND chapter = ? AND verse = ?",
                (book_id, chapter, verse),
            )
        ]
        vorlagen = [
            json.loads(r["payload_json"])
            for r in conn.execute(
                "SELECT payload_json FROM bibcrit_vorlagen "
                "WHERE book_id = ? AND chapter = ? AND verse_start <= ? AND verse_end >= ?",
                (book_id, chapter, verse, verse),
            )
        ]
        return {
            "book_id": book_id,
            "chapter": chapter,
            "verse": verse,
            "notes": notes,
            "apparatus": apparatus,
            "bibcrit_vorlagen": vorlagen,
        }
    finally:
        conn.close()


@router.get("/search")
def plenary_search(
    q: str = Query(..., min_length=2),
    scope: str = Query(default="all", pattern="^(all|verses|notes|apparatus)$"),
    translation: Optional[str] = Query(default=None),
    limit: int = Query(default=40, ge=1, le=200),
):
    fts_q = _sanitize_fts_query(q)
    if not fts_q:
        raise HTTPException(status_code=400, detail="Search query contains no indexable tokens.")

    conn = _connect()
    try:
        results: dict[str, list[dict]] = {}
        if scope in ("all", "verses"):
            if translation:
                rows = conn.execute(
                    "SELECT book_id, chapter, verse, translation_id, "
                    "snippet(verses_fts, 4, '[', ']', '...', 18) AS snippet, bm25(verses_fts) AS rank "
                    "FROM verses_fts WHERE verses_fts MATCH ? AND translation_id = ? "
                    "ORDER BY rank LIMIT ?",
                    (fts_q, translation, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT book_id, chapter, verse, translation_id, "
                    "snippet(verses_fts, 4, '[', ']', '...', 18) AS snippet, bm25(verses_fts) AS rank "
                    "FROM verses_fts WHERE verses_fts MATCH ? "
                    "ORDER BY rank LIMIT ?",
                    (fts_q, limit),
                ).fetchall()
            results["verses"] = [dict(r) for r in rows]

        if scope in ("all", "notes"):
            rows = conn.execute(
                "SELECT book_id, chapter, verse, src, title, "
                "snippet(notes_fts, 5, '[', ']', '...', 20) AS snippet, bm25(notes_fts) AS rank "
                "FROM notes_fts WHERE notes_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (fts_q, limit),
            ).fetchall()
            results["notes"] = [dict(r) for r in rows]

        if scope in ("all", "apparatus"):
            rows = conn.execute(
                "SELECT apparatus_id, book_id, chapter, verse, title, "
                "snippet(apparatus_fts, 5, '[', ']', '...', 20) AS snippet, bm25(apparatus_fts) AS rank "
                "FROM apparatus_fts WHERE apparatus_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (fts_q, limit),
            ).fetchall()
            results["apparatus"] = [dict(r) for r in rows]

        return {"query": q, "fts_query": fts_q, "scope": scope, "results": results}
    finally:
        conn.close()
