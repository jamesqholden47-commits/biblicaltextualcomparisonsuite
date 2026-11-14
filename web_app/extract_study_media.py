#!/usr/bin/env python3
"""Extract embedded maps, diagrams, and plates (>=200x200px, max 300 assets)
from Study Bible PDFs and ePubs in `web_app/sources_cache/` into
`web_app/study_media/` and register them in `media_assets` in `plenary_logos.sqlite`.

Idempotent: clears and rebuilds `media_assets` without touching `verses`, `notes`,
or `patristic_index`.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
import zipfile
from pathlib import Path

import fitz  # PyMuPDF

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "plenary_logos.sqlite"
SOURCES_CACHE = SCRIPT_DIR / "sources_cache"
MEDIA_DIR = SCRIPT_DIR / "study_media"

MIN_DIM = 200
MAX_ASSETS = 300
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;

        CREATE TABLE IF NOT EXISTS media_assets (
            id TEXT PRIMARY KEY,
            source_id TEXT,
            book_id TEXT,
            chapter INTEGER,
            title TEXT,
            rel_path TEXT,
            width INTEGER,
            height INTEGER,
            mime TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_media_source
            ON media_assets(source_id);
        """
    )


def _mime_for_ext(ext: str) -> str:
    e = ext.lower().lstrip(".")
    if e == "jpg":
        e = "jpeg"
    return f"image/{e}"


def _make_asset_id(source_id: str, tag: str) -> str:
    digest = hashlib.sha1(f"{source_id}::{tag}".encode("utf-8")).hexdigest()[:12]
    safe_src = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in source_id)[:24]
    return f"{safe_src}_{digest}"


def _extract_from_pdf(pdf_path: Path, source_id: str, rows: list[tuple], remaining: int) -> int:
    extracted = 0
    seen_xrefs: set[int] = set()
    with fitz.open(str(pdf_path)) as doc:
        for page_idx in range(doc.page_count):
            if extracted >= remaining:
                break
            page = doc[page_idx]
            for img_info in page.get_images(full=True):
                if extracted >= remaining:
                    break
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                try:
                    info = doc.extract_image(xref)
                except Exception:
                    continue
                if not info:
                    continue
                w = int(info.get("width") or 0)
                h = int(info.get("height") or 0)
                if w < MIN_DIM or h < MIN_DIM:
                    continue
                ext = (info.get("ext") or "png").lower()
                img_bytes = info.get("image")
                if not img_bytes:
                    continue

                asset_id = _make_asset_id(source_id, f"p{page_idx + 1}_x{xref}")
                out_name = f"{asset_id}.{ext}"
                out_path = MEDIA_DIR / out_name
                out_path.write_bytes(img_bytes)

                rows.append(
                    (
                        asset_id,
                        source_id,
                        None,
                        None,
                        f"{pdf_path.stem} (p. {page_idx + 1})",
                        f"study_media/{out_name}",
                        w,
                        h,
                        _mime_for_ext(ext),
                    )
                )
                extracted += 1
    return extracted


def _extract_from_epub(epub_path: Path, source_id: str, rows: list[tuple], remaining: int) -> int:
    extracted = 0
    with zipfile.ZipFile(str(epub_path), "r") as zf:
        for member in sorted(zf.namelist()):
            if extracted >= remaining:
                break
            ext = Path(member).suffix.lower()
            if ext not in IMAGE_EXTS:
                continue
            try:
                data = zf.read(member)
                pix = fitz.Pixmap(data)
                w, h = pix.width, pix.height
            except Exception:
                continue
            if w < MIN_DIM or h < MIN_DIM:
                continue

            asset_id = _make_asset_id(source_id, member)
            clean_ext = ext.lstrip(".")
            out_name = f"{asset_id}.{clean_ext}"
            out_path = MEDIA_DIR / out_name
            out_path.write_bytes(data)

            rows.append(
                (
                    asset_id,
                    source_id,
                    None,
                    None,
                    f"{epub_path.stem} — {Path(member).name}",
                    f"study_media/{out_name}",
                    w,
                    h,
                    _mime_for_ext(clean_ext),
                )
            )
            extracted += 1
    return extracted


def extract_study_media(db_path: Path = DB_PATH) -> dict[str, int | float]:
    t0 = time.perf_counter()
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[tuple] = []
    files_scanned = 0

    if SOURCES_CACHE.is_dir():
        candidates = sorted(
            p
            for p in SOURCES_CACHE.rglob("*")
            if p.is_file() and p.suffix.lower() in (".pdf", ".epub")
        )
        for src_path in candidates:
            remaining = MAX_ASSETS - len(rows)
            if remaining <= 0:
                break
            files_scanned += 1
            source_id = src_path.stem
            if src_path.suffix.lower() == ".pdf":
                _extract_from_pdf(src_path, source_id, rows, remaining)
            else:
                _extract_from_epub(src_path, source_id, rows, remaining)

    conn = sqlite3.connect(str(db_path))
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("DELETE FROM media_assets")
        if rows:
            cur.executemany(
                """
                INSERT INTO media_assets
                    (id, source_id, book_id, chapter, title, rel_path, width, height, mime)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        conn.commit()
        total_assets = cur.execute("SELECT COUNT(*) FROM media_assets").fetchone()[0]
    finally:
        conn.close()

    elapsed = time.perf_counter() - t0
    return {
        "files_scanned": files_scanned,
        "media_assets_rows": total_assets,
        "elapsed_sec": round(elapsed, 2),
    }


if __name__ == "__main__":
    stats = extract_study_media()
    print(
        f"Study media extraction finished in {stats['elapsed_sec']}s: "
        f"files_scanned={stats['files_scanned']}, "
        f"media_assets={stats['media_assets_rows']} rows"
    )
