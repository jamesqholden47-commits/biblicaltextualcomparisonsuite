"""Unit tests for the Plenary SQLite + FTS5 lazy-loading database and FastAPI routes."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

SUITE_DIR = Path(__file__).resolve().parents[1]
if str(SUITE_DIR) not in sys.path:
    sys.path.insert(0, str(SUITE_DIR))

from app import app  # noqa: E402
from modules.plenary_db_routes import get_db_path  # noqa: E402

client = TestClient(app)


def test_plenary_db_status():
    resp = client.get("/api/plenary/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert Path(data["db_path"]) == get_db_path()
    meta = data["meta"]
    assert int(meta["books_count"]) == 73
    assert int(meta["translations_count"]) >= 22
    assert int(meta["verses_count"]) > 700000
    assert int(meta["notes_count"]) > 10000


def test_plenary_books_and_lazy_chapter():
    b_resp = client.get("/api/plenary/books")
    assert b_resp.status_code == 200
    b_data = b_resp.json()
    assert len(b_data["books"]) == 73
    assert any(b["id"] == "gen" for b in b_data["books"])

    c_resp = client.get("/api/plenary/chapter/gen/1?translations=he,gr,vul,dra")
    assert c_resp.status_code == 200
    c_data = c_resp.json()
    assert c_data["book"]["id"] == "gen"
    assert c_data["chapter"] == 1
    assert "1" in c_data["verses"] or 1 in c_data["verses"]
    v1 = c_data["verses"].get("1") or c_data["verses"].get(1)
    assert "he" in v1 and "gr" in v1 and "vul" in v1 and "dra" in v1
    assert "beginning" in v1["dra"].lower()


def test_plenary_verse_notes():
    resp = client.get("/api/plenary/verse_notes/gen/1/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["book_id"] == "gen"
    assert data["chapter"] == 1
    assert data["verse"] == 1
    assert len(data["notes"]) >= 1


def test_plenary_fts5_search():
    v_resp = client.get("/api/plenary/search?q=Logos&scope=verses&translation=dra&limit=10")
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert "verses" in v_data["results"]

    n_resp = client.get("/api/plenary/search?q=Bereshith&scope=notes&limit=10")
    assert n_resp.status_code == 200
    n_data = n_resp.json()
    assert len(n_data["results"]["notes"]) >= 1

    a_resp = client.get("/api/plenary/search?q=Adulterae&scope=apparatus&limit=5")
    assert a_resp.status_code == 200
    a_data = a_resp.json()
    assert len(a_data["results"]["apparatus"]) >= 1


def test_plenary_chapter_bounds():
    bad_book = client.get("/api/plenary/chapter/notabook/1")
    assert bad_book.status_code == 404
    bad_chap = client.get("/api/plenary/chapter/gen/999")
    assert bad_chap.status_code == 404
