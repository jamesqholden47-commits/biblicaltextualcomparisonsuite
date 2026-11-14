"""Automated end-to-end verification for the Plenary Logos SQLite + FastAPI pipeline.

Runs:
1. Direct SQLite status and schema integrity check on web_app/plenary_logos.sqlite.
2. Direct FTS5 BM25 query checks across verses_fts, notes_fts, and apparatus_fts.
3. FastAPI TestClient smoke checks on /api/plenary/status, /api/plenary/books,
   /api/plenary/chapter/gen/1, and /api/plenary/search.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = WEB_APP_DIR.parent
SUITE_DIR = PROJECT_ROOT / "09_APPS_CATHOLICJARVIS" / "catholic_jarvis_suite"
DB_PATH = WEB_APP_DIR / "plenary_logos.sqlite"


def check_sqlite_status(db_path: Path) -> None:
    if not db_path.exists():
        raise AssertionError(f"SQLite database missing: {db_path}")
    size_bytes = db_path.stat().st_size
    if size_bytes <= 0:
        raise AssertionError(f"SQLite database is empty: {db_path}")

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM meta")}
        books_count = int(meta["books_count"])
        translations_count = int(meta["translations_count"])
        verses_count = int(meta["verses_count"])
        notes_count = int(meta["notes_count"])

        assert books_count == 73, f"Expected 73 books, got {books_count}"
        assert translations_count >= 22, f"Expected >=22 translations, got {translations_count}"
        assert verses_count > 700_000, f"Expected >700000 verses, got {verses_count}"
        assert notes_count > 10_000, f"Expected >10000 notes, got {notes_count}"

        print(
            f"[PASS] SQLite status: {size_bytes:,} bytes | "
            f"books={books_count}, translations={translations_count}, "
            f"verses={verses_count:,}, notes={notes_count:,}"
        )
    finally:
        conn.close()


def check_fts5_queries(db_path: Path) -> None:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        v_rows = conn.execute(
            "SELECT book_id, chapter, verse, translation_id, bm25(verses_fts) AS rank "
            "FROM verses_fts WHERE verses_fts MATCH 'Logos' ORDER BY rank LIMIT 5"
        ).fetchall()
        assert len(v_rows) >= 1, "verses_fts MATCH 'Logos' returned 0 rows"

        n_rows = conn.execute(
            "SELECT book_id, chapter, verse, src, bm25(notes_fts) AS rank "
            "FROM notes_fts WHERE notes_fts MATCH 'Bereshith' ORDER BY rank LIMIT 5"
        ).fetchall()
        assert len(n_rows) >= 1, "notes_fts MATCH 'Bereshith' returned 0 rows"

        a_rows = conn.execute(
            "SELECT apparatus_id, book_id, chapter, verse, bm25(apparatus_fts) AS rank "
            "FROM apparatus_fts WHERE apparatus_fts MATCH 'Adulterae' ORDER BY rank LIMIT 5"
        ).fetchall()
        assert len(a_rows) >= 1, "apparatus_fts MATCH 'Adulterae' returned 0 rows"

        print(
            f"[PASS] FTS5 queries: verses={len(v_rows)}, "
            f"notes={len(n_rows)}, apparatus={len(a_rows)}"
        )
    finally:
        conn.close()


def check_fastapi_smoke() -> None:
    if str(SUITE_DIR) not in sys.path:
        sys.path.insert(0, str(SUITE_DIR))

    from fastapi.testclient import TestClient
    from app import app

    client = TestClient(app)

    r_status = client.get("/api/plenary/status")
    assert r_status.status_code == 200, f"/api/plenary/status -> {r_status.status_code}"
    status_data = r_status.json()
    assert status_data.get("available") is True, f"Status not available: {status_data}"

    r_books = client.get("/api/plenary/books")
    assert r_books.status_code == 200, f"/api/plenary/books -> {r_books.status_code}"
    books_data = r_books.json()
    assert len(books_data["books"]) == 73, f"Expected 73 books, got {len(books_data['books'])}"
    assert any(b["id"] == "gen" for b in books_data["books"]), "Missing 'gen' in books"

    r_chap = client.get("/api/plenary/chapter/gen/1?translations=he,gr,vul,dra")
    assert r_chap.status_code == 200, f"/api/plenary/chapter/gen/1 -> {r_chap.status_code}"
    chap_data = r_chap.json()
    assert chap_data["book"]["id"] == "gen"
    assert chap_data["chapter"] == 1
    v1 = chap_data["verses"].get("1") or chap_data["verses"].get(1)
    assert v1 and all(k in v1 for k in ("he", "gr", "vul", "dra")), "Missing translations in Gen 1:1"
    assert "beginning" in v1["dra"].lower(), "Unexpected DRA text in Gen 1:1"

    r_search_v = client.get("/api/plenary/search?q=Logos&scope=verses&translation=dra&limit=5")
    assert r_search_v.status_code == 200, f"/api/plenary/search (verses) -> {r_search_v.status_code}"
    assert "verses" in r_search_v.json()["results"]

    r_search_n = client.get("/api/plenary/search?q=Bereshith&scope=notes&limit=5")
    assert r_search_n.status_code == 200, f"/api/plenary/search (notes) -> {r_search_n.status_code}"
    assert len(r_search_n.json()["results"]["notes"]) >= 1

    r_search_a = client.get("/api/plenary/search?q=Adulterae&scope=apparatus&limit=5")
    assert r_search_a.status_code == 200, f"/api/plenary/search (apparatus) -> {r_search_a.status_code}"
    assert len(r_search_a.json()["results"]["apparatus"]) >= 1

    print("[PASS] FastAPI TestClient smoke checks: /status, /books, /chapter/gen/1, /search")


def main() -> int:
    try:
        check_sqlite_status(DB_PATH)
        check_fts5_queries(DB_PATH)
        check_fastapi_smoke()
    except Exception as exc:
        print(f"[FAIL] Plenary pipeline verification failed: {exc}")
        return 1
    print("[PASS] Plenary pipeline verification complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
