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

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse

from . import auth_routes, licensing

router = APIRouter(prefix="/api/plenary", tags=["plenary-db"])

_HERE = Path(__file__).resolve()
_WEB_APP_DIR = _HERE.parents[3] / "web_app"
_DEFAULT_DB = _WEB_APP_DIR / "plenary_logos.sqlite"
_STUDY_MEDIA_DIR = _WEB_APP_DIR / "study_media"


def _is_saas_mode() -> bool:
    return os.environ.get("PLENARY_SAAS_MODE", "0").strip().lower() in ("1", "true", "yes")


def _effective_tier(user: dict | None) -> str:
    if not _is_saas_mode():
        return "institutional"
    return licensing.normalize_tier((user or {}).get("tier") or "free")


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
    response: Response,
    translations: Optional[str] = Query(
        default=None,
        description="Comma-separated translation IDs (e.g. he,gr,vul,dra,rsv2ce). Omit for all.",
    ),
    user: dict | None = Depends(auth_routes.get_current_user_optional),
):
    tier = _effective_tier(user)
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
        if _is_saas_mode() and tr_filter:
            denied = [t for t in tr_filter if not licensing.is_translation_allowed(tier, t)]
            if denied:
                raise HTTPException(
                    status_code=403,
                    detail=f"Tier '{tier}' does not include translation(s): {', '.join(denied)}",
                )
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
            tr_id = r["translation_id"]
            if _is_saas_mode() and not licensing.is_translation_allowed(tier, tr_id):
                continue
            v_num = int(r["verse"])
            verses_by_num.setdefault(v_num, {})[tr_id] = r["text"]

        response.headers["Cache-Control"] = "private, max-age=300" if user else "public, max-age=300"

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


def _schaff_pdf_vol(series: str | None, volume: int | None) -> str | None:
    if not series or series.upper() != "SCHAFF" or volume is None:
        return None
    if 1 <= volume <= 99:
        return f"anf{volume:02d}"
    if 101 <= volume <= 199:
        return f"npnf1{volume - 100:02d}"
    if 201 <= volume <= 299:
        return f"npnf2{volume - 200:02d}"
    return None


def _parse_page_num(page_or_col: str | None) -> int | None:
    if not page_or_col:
        return None
    import re
    m = re.search(r"p\.\s*(\d+)", page_or_col, re.IGNORECASE)
    return int(m.group(1)) if m else None


@router.get("/patristics")
def plenary_patristics(
    response: Response,
    q: Optional[str] = Query(default=None),
    series: Optional[str] = Query(default=None, description="PL, PG, or SCHAFF"),
    book_id: Optional[str] = Query(default=None),
    book: Optional[str] = Query(default=None),
    chapter: Optional[int] = Query(default=None),
    verse: Optional[int] = Query(default=None),
    limit: int = Query(default=120, ge=1, le=500),
):
    conn = _connect()
    try:
        response.headers["Cache-Control"] = "public, max-age=300"
        has_fts = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name='patristic_fts'"
        ).fetchone()
        eff_book = (book_id or book or "").strip() or None

        if q and q.strip() and has_fts:
            fts_q = _sanitize_fts_query(q)
            if not fts_q:
                return {"items": [], "count": 0}
            sql = (
                "SELECT p.id, p.series, p.volume, p.author, p.work_title, "
                "p.book_id, p.chapter, p.verse, p.page_or_col, "
                "snippet(patristic_fts, 5, '[', ']', '...', 28) AS snippet "
                "FROM patristic_fts "
                "JOIN patristic_index p ON p.id = patristic_fts.patristic_id "
                "WHERE patristic_fts MATCH ?"
            )
            params: list = [fts_q]
            if series:
                sql += " AND p.series = ?"
                params.append(series.strip().upper())
            if eff_book:
                sql += " AND p.book_id = ?"
                params.append(eff_book)
            if chapter is not None:
                sql += " AND p.chapter = ?"
                params.append(chapter)
            sql += " ORDER BY bm25(patristic_fts) LIMIT ?"
            params.append(limit)
            items = []
            for r in conn.execute(sql, params).fetchall():
                d = dict(r)
                d["pdf_vol"] = _schaff_pdf_vol(d.get("series"), d.get("volume"))
                d["page_num"] = _parse_page_num(d.get("page_or_col"))
                items.append(d)
            return {"items": items, "count": len(items)}

        sql = (
            "SELECT id, series, volume, author, work_title, book_id, chapter, verse, "
            "page_or_col, substr(excerpt, 1, 600) AS snippet "
            "FROM patristic_index WHERE 1=1"
        )
        params = []
        if series:
            sql += " AND series = ?"
            params.append(series.strip().upper())
        if eff_book:
            sql += " AND book_id = ?"
            params.append(eff_book)
        if chapter is not None:
            sql += " AND chapter = ?"
            params.append(chapter)
        if verse is not None:
            sql += " AND (verse = ? OR verse IS NULL)"
            params.append(verse)
            sql += " ORDER BY CASE WHEN verse = ? THEN 0 ELSE 1 END, series, volume, id LIMIT ?"
            params.append(verse)
        else:
            sql += " ORDER BY series, volume, id LIMIT ?"
        params.append(limit)
        items = []
        for r in conn.execute(sql, params).fetchall():
            d = dict(r)
            d["pdf_vol"] = _schaff_pdf_vol(d.get("series"), d.get("volume"))
            d["page_num"] = _parse_page_num(d.get("page_or_col"))
            items.append(d)
        return {"items": items, "count": len(items)}
    finally:
        conn.close()


@router.get("/media")
def plenary_media(
    book_id: Optional[str] = Query(default=None),
    chapter: Optional[int] = Query(default=None),
    limit: int = Query(default=40, ge=1, le=200),
):
    conn = _connect()
    try:
        has_tbl = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name='media_assets'"
        ).fetchone()
        if not has_tbl:
            return {"items": [], "count": 0}
        sql = (
            "SELECT id, source_id, book_id, chapter, title, rel_path, width, height, mime "
            "FROM media_assets WHERE 1=1"
        )
        params: list = []
        if book_id:
            sql += " AND book_id = ?"
            params.append(book_id.strip())
        if chapter is not None:
            sql += " AND chapter = ?"
            params.append(chapter)
        sql += " ORDER BY id LIMIT ?"
        params.append(limit)
        items = [dict(r) for r in conn.execute(sql, params).fetchall()]
        return {"items": items, "count": len(items)}
    finally:
        conn.close()


@router.get("/media/file/{asset_id}")
def plenary_media_file(asset_id: str):
    conn = _connect()
    try:
        has_tbl = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name='media_assets'"
        ).fetchone()
        if not has_tbl:
            raise HTTPException(status_code=404, detail="media_assets table not initialized")
        row = conn.execute(
            "SELECT rel_path, mime FROM media_assets WHERE id = ?", (asset_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Media asset not found: {asset_id}")
        media_root = _STUDY_MEDIA_DIR.resolve()
        candidate = (media_root / row["rel_path"]).resolve()
        if not candidate.is_relative_to(media_root) or not candidate.is_file():
            raise HTTPException(status_code=404, detail="Media file missing or invalid path")
        return FileResponse(str(candidate), media_type=row["mime"] or "application/octet-stream")
    finally:
        conn.close()
