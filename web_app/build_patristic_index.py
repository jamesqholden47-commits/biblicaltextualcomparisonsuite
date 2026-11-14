#!/usr/bin/env python3
"""Index Migne Patrologia Latina (PL), Patrologia Graeca (PG), and Schaff ANF/NPNF PDFs
into `patristic_index` and `patristic_fts` in `plenary_logos.sqlite`.

Idempotent: clears and rebuilds `patristic_index` and `patristic_fts` without
touching `verses`, `notes`, or any other tables.
"""

from __future__ import annotations

import os
import re
import sqlite3
import time
from pathlib import Path

import fitz  # PyMuPDF

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "plenary_logos.sqlite"
PATRISTICS_ROOT = Path(r"C:\Users\Elation\PDFS\02_Patristics_and_Church_Fathers")

PL_DIR = PATRISTICS_ROOT / "Migne_Patrologia_Latina"
PG_DIR = PATRISTICS_ROOT / "Migne_Patrologia_Graeca"
SCHAFF_DIR = PATRISTICS_ROOT / "Schaff_ANF_NPNF"

_PL_RE = re.compile(
    r"Patrologia_Latina_(\d+)(?:_\(([^)]+)\))?(?:_(.+?))?(?:,_MLT)?\.pdf$",
    re.IGNORECASE,
)
_PG_RE = re.compile(
    r"PG_(\d+)_(?:\(([^)]+)\)|\[([^\]]+)\])_(.+?)(?:,_[A-Z]+)?\.pdf$",
    re.IGNORECASE,
)
_SCHAFF_RE = re.compile(r"^(anf|npnf1|npnf2)(\d+)\.pdf$", re.IGNORECASE)


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;

        CREATE TABLE IF NOT EXISTS patristic_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series TEXT NOT NULL,
            volume INTEGER NOT NULL,
            author TEXT,
            work_title TEXT,
            book_id TEXT,
            chapter INTEGER,
            verse INTEGER,
            page_or_col TEXT,
            excerpt TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_patristic_bcv
            ON patristic_index(book_id, chapter, verse);

        CREATE VIRTUAL TABLE IF NOT EXISTS patristic_fts USING fts5(
            patristic_id UNINDEXED,
            series UNINDEXED,
            volume UNINDEXED,
            author,
            work_title,
            excerpt,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def _clean_underscores(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("_", " ")).strip(" ,._-")


def _infer_pg_author(title_str: str) -> str:
    """Heuristically extract the Father/author name from a PG filename title."""
    # Common patterns: "SS Clementis I Opera Omnia", "Origenes. Opera Omnia",
    # "Athanasii Opera Omnia", "Joannes Chrysostomus. Opera Omnia"
    if "." in title_str:
        head = title_str.split(".", 1)[0].strip()
        if head:
            return head
    for marker in (" Opera ", " Epistolae", " Homiliae", " Commentarii", " et Aliorum"):
        idx = title_str.find(marker)
        if idx > 0:
            return title_str[:idx].strip(" ,.")
    return title_str


def _inspect_pdf(pdf_path: Path) -> tuple[int, dict[str, str], list]:
    """Open a PDF with PyMuPDF and return (page_count, metadata, toc)."""
    with fitz.open(str(pdf_path)) as doc:
        page_count = doc.page_count
        meta = {k: (v or "").strip() for k, v in (doc.metadata or {}).items() if v}
        toc = doc.get_toc(simple=True) or []
    return page_count, meta, toc


def _scan_migne_pl(rows: list[tuple]) -> int:
    if not PL_DIR.is_dir():
        print(f"[WARN] Missing PL directory: {PL_DIR}")
        return 0
    count = 0
    for pdf_path in sorted(PL_DIR.glob("*.pdf")):
        m = _PL_RE.search(pdf_path.name)
        if not m:
            continue
        vol = int(m.group(1))
        year_tag = _clean_underscores(m.group(2) or "")
        prov_tag = _clean_underscores(m.group(3) or "")
        page_count, meta, toc = _inspect_pdf(pdf_path)

        author = meta.get("author") or "Jacques-Paul Migne (ed.)"
        title_parts = [f"Patrologia Latina, Vol. {vol:03d}"]
        if year_tag:
            title_parts.append(f"({year_tag})")
        if prov_tag:
            title_parts.append(f"— {prov_tag}")
        work_title = " ".join(title_parts)

        excerpt_parts = [
            f"Series: Migne Patrologia Latina (PL {vol:03d})",
            f"File: {pdf_path.name}",
            f"Pages: {page_count}",
        ]
        if meta.get("title"):
            excerpt_parts.append(f"Title: {meta['title']}")
        if toc:
            toc_titles = [t[1].strip() for t in toc[:25] if len(t) >= 2 and t[1].strip()]
            if toc_titles:
                excerpt_parts.append("Contents: " + "; ".join(toc_titles))

        rows.append(
            (
                "PL",
                vol,
                author,
                work_title,
                None,
                None,
                None,
                f"{page_count} pp.",
                " | ".join(excerpt_parts),
            )
        )
        count += 1
    return count


def _scan_migne_pg(rows: list[tuple]) -> int:
    if not PG_DIR.is_dir():
        print(f"[WARN] Missing PG directory: {PG_DIR}")
        return 0
    count = 0
    for pdf_path in sorted(PG_DIR.glob("*.pdf")):
        m = _PG_RE.search(pdf_path.name)
        if not m:
            continue
        vol = int(m.group(1))
        subpart = (m.group(2) or m.group(3) or "").strip()
        raw_title = _clean_underscores(m.group(4) or "")
        page_count, meta, toc = _inspect_pdf(pdf_path)

        author = _infer_pg_author(raw_title) if raw_title else (meta.get("author") or "Jacques-Paul Migne (ed.)")
        sub_label = f", {subpart}" if subpart else ""
        work_title = f"{raw_title} (PG {vol:03d}{sub_label})" if raw_title else f"Patrologia Graeca, Vol. {vol:03d}{sub_label}"

        excerpt_parts = [
            f"Series: Migne Patrologia Graeca (PG {vol:03d}{sub_label})",
            f"Author/Work: {raw_title}",
            f"File: {pdf_path.name}",
            f"Pages: {page_count}",
        ]
        if meta.get("title"):
            excerpt_parts.append(f"Metadata Title: {meta['title']}")
        if toc:
            toc_titles = [t[1].strip() for t in toc[:25] if len(t) >= 2 and t[1].strip()]
            if toc_titles:
                excerpt_parts.append("Contents: " + "; ".join(toc_titles))

        rows.append(
            (
                "PG",
                vol,
                author,
                work_title,
                None,
                None,
                None,
                f"{page_count} pp.",
                " | ".join(excerpt_parts),
            )
        )
        count += 1
    return count


def _scan_schaff(rows: list[tuple]) -> int:
    if not SCHAFF_DIR.is_dir():
        print(f"[WARN] Missing Schaff directory: {SCHAFF_DIR}")
        return 0
    vol_files = 0
    for pdf_path in sorted(SCHAFF_DIR.glob("*.pdf")):
        m = _SCHAFF_RE.match(pdf_path.name)
        if not m:
            continue
        subseries = m.group(1).lower()
        num = int(m.group(2))
        if subseries == "anf":
            vol = num
            label = f"ANF {num:02d}"
        elif subseries == "npnf1":
            vol = 100 + num
            label = f"NPNF1 {num:02d}"
        else:
            vol = 200 + num
            label = f"NPNF2 {num:02d}"

        page_count, meta, toc = _inspect_pdf(pdf_path)
        author = meta.get("author") or "Philip Schaff (ed.)"
        work_title = meta.get("title") or f"{label} ({pdf_path.name})"

        l1_entries = [
            (t[1].strip(), int(t[2]))
            for t in toc
            if len(t) >= 3 and t[0] == 1 and t[1].strip()
        ]
        toc_summary = "; ".join(title for title, _ in l1_entries[:25])

        excerpt_parts = [
            f"Series: Schaff {label}",
            f"File: {pdf_path.name}",
            f"Pages: {page_count}",
        ]
        if toc_summary:
            excerpt_parts.append(f"Treatises: {toc_summary}")

        # Volume-level entry
        rows.append(
            (
                "SCHAFF",
                vol,
                author,
                work_title,
                None,
                None,
                None,
                f"{page_count} pp.",
                " | ".join(excerpt_parts),
            )
        )

        # Level-1 treatise entries from TOC for direct FTS5 lookup
        for sec_title, sec_page in l1_entries:
            rows.append(
                (
                    "SCHAFF",
                    vol,
                    author,
                    f"[{label}] {sec_title}",
                    None,
                    None,
                    None,
                    f"p. {sec_page}",
                    f"{work_title} — {sec_title} (p. {sec_page}, {pdf_path.name})",
                )
            )
        vol_files += 1
    return vol_files


def build_patristic_index(db_path: Path = DB_PATH) -> dict[str, int | float]:
    t0 = time.perf_counter()
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    rows: list[tuple] = []
    pl_count = _scan_migne_pl(rows)
    pg_count = _scan_migne_pg(rows)
    schaff_files = _scan_schaff(rows)

    conn = sqlite3.connect(str(db_path))
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("DELETE FROM patristic_index")
        cur.execute("DELETE FROM patristic_fts")

        cur.executemany(
            """
            INSERT INTO patristic_index
                (series, volume, author, work_title, book_id, chapter, verse, page_or_col, excerpt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

        cur.execute(
            """
            INSERT INTO patristic_fts (patristic_id, series, volume, author, work_title, excerpt)
            SELECT id, series, volume, COALESCE(author, ''), COALESCE(work_title, ''), COALESCE(excerpt, '')
            FROM patristic_index
            """
        )

        conn.commit()
        total_idx = cur.execute("SELECT COUNT(*) FROM patristic_index").fetchone()[0]
        total_fts = cur.execute("SELECT COUNT(*) FROM patristic_fts").fetchone()[0]
    finally:
        conn.close()

    elapsed = time.perf_counter() - t0
    return {
        "pl_pdfs": pl_count,
        "pg_pdfs": pg_count,
        "schaff_pdfs": schaff_files,
        "patristic_index_rows": total_idx,
        "patristic_fts_rows": total_fts,
        "elapsed_sec": round(elapsed, 2),
    }


if __name__ == "__main__":
    stats = build_patristic_index()
    print(
        f"Patristic index rebuilt in {stats['elapsed_sec']}s: "
        f"PL={stats['pl_pdfs']} PDFs, PG={stats['pg_pdfs']} PDFs, "
        f"SCHAFF={stats['schaff_pdfs']} PDFs | "
        f"patristic_index={stats['patristic_index_rows']} rows, "
        f"patristic_fts={stats['patristic_fts_rows']} rows"
    )
