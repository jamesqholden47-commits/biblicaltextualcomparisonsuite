#!/usr/bin/env python3
"""Compile Plenary Logos Suite JSON + study-note shards into an indexed SQLite + FTS5 database.

Designed for sub-10ms lazy chapter loading, full-text BM25 search across
25 translations, study notes, and critical apparatus, and portable reuse
by FastAPI, Browser WASM/OPFS, or a future Rust (Tauri/Axum) backend.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_JSON = SCRIPT_DIR / "plenary_logos_data.json"
NOTES_DIR = SCRIPT_DIR / "notes_shards"
DB_OUT = SCRIPT_DIR / "plenary_logos.sqlite"
SCHEMA_VERSION = "1.0.0"

_SHARD_PREFIX_RE = re.compile(r'^window\.__PLENARY_LOAD_BOOK_NOTES\("[^"]+",\s*')
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _parse_note_shard(path: Path) -> dict | None:
    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return None
    m = _SHARD_PREFIX_RE.match(raw)
    if m:
        raw = raw[m.end() :]
        if raw.endswith(");"):
            raw = raw[:-2]
        elif raw.endswith(")"):
            raw = raw[:-1]
    return json.loads(raw)


def _create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;
        PRAGMA temp_store = MEMORY;
        PRAGMA cache_size = -64000;

        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE books (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            abbr TEXT NOT NULL,
            division TEXT,
            testament TEXT,
            lang TEXT,
            deuterocanon INTEGER NOT NULL DEFAULT 0,
            chapter_count INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE translations (
            id TEXT PRIMARY KEY,
            short TEXT NOT NULL,
            name TEXT NOT NULL,
            lang TEXT,
            scope TEXT,
            approval TEXT,
            tier_badge TEXT,
            grp TEXT
        );

        CREATE TABLE verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            translation_id TEXT NOT NULL,
            text TEXT NOT NULL
        );

        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            src TEXT,
            tier TEXT,
            kind TEXT,
            marker TEXT,
            anchor_word TEXT,
            title TEXT,
            body TEXT NOT NULL
        );

        CREATE TABLE apparatus (
            id TEXT PRIMARY KEY,
            testament TEXT,
            book_id TEXT,
            chapter INTEGER,
            verse INTEGER,
            verse_range TEXT,
            title TEXT,
            metzger_rating TEXT,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE bibcrit_vorlagen (
            id TEXT PRIMARY KEY,
            book_id TEXT,
            chapter INTEGER,
            verse_start INTEGER,
            verse_end INTEGER,
            title TEXT,
            ref TEXT,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE theological_revisions (
            id TEXT PRIMARY KEY,
            category TEXT,
            ref TEXT,
            title TEXT,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE chiasms (
            id TEXT PRIMARY KEY,
            ref TEXT,
            title TEXT,
            apex TEXT,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE patristic_index (
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

        CREATE VIRTUAL TABLE verses_fts USING fts5(
            book_id UNINDEXED,
            chapter UNINDEXED,
            verse UNINDEXED,
            translation_id UNINDEXED,
            text,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE VIRTUAL TABLE notes_fts USING fts5(
            book_id UNINDEXED,
            chapter UNINDEXED,
            verse UNINDEXED,
            src UNINDEXED,
            title,
            body,
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE VIRTUAL TABLE apparatus_fts USING fts5(
            apparatus_id UNINDEXED,
            book_id UNINDEXED,
            chapter UNINDEXED,
            verse UNINDEXED,
            title,
            body,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def build_sqlite(
    data_json_path: Path = DATA_JSON,
    notes_dir: Path = NOTES_DIR,
    db_out: Path = DB_OUT,
) -> dict[str, int | float | str]:
    t0 = time.perf_counter()
    with data_json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    tmp_db = db_out.with_suffix(".sqlite.tmp")
    if tmp_db.exists():
        tmp_db.unlink()

    conn = sqlite3.connect(str(tmp_db))
    try:
        _create_schema(conn)
        cur = conn.cursor()

        # 1. Translations
        tr_rows = []
        for tr in data.get("translation_registry", []):
            tr_rows.append(
                (
                    tr.get("id", ""),
                    tr.get("short", tr.get("id", "")),
                    tr.get("name", ""),
                    tr.get("lang", ""),
                    tr.get("scope", ""),
                    tr.get("approval", ""),
                    tr.get("tier_badge", ""),
                    tr.get("group", ""),
                )
            )
        cur.executemany(
            "INSERT INTO translations (id, short, name, lang, scope, approval, tier_badge, grp) VALUES (?,?,?,?,?,?,?,?)",
            tr_rows,
        )

        # 2. Books & Verses
        book_rows = []
        verse_rows = []
        canonical_book_ids: set[str] = set()

        stream_map = {
            "verses_en": "dra",
            "verses_la": "vul",
            "verses_gr": "gr",
            "verses_he": "he",
        }

        for idx, b in enumerate(data.get("books", [])):
            bid = b["id"]
            canonical_book_ids.add(bid)
            book_rows.append(
                (
                    bid,
                    b.get("name", bid),
                    b.get("abbr", bid),
                    b.get("division", ""),
                    b.get("testament", ""),
                    b.get("lang", ""),
                    1 if b.get("deuterocanon") else 0,
                    int(b.get("chapter_count", 0)),
                    idx,
                )
            )

            for field_name, tr_id in stream_map.items():
                chapters_list = b.get(field_name) or []
                for c_idx, ch_verses in enumerate(chapters_list, 1):
                    if not isinstance(ch_verses, list):
                        continue
                    for v_idx, txt in enumerate(ch_verses, 1):
                        if txt:
                            verse_rows.append((bid, c_idx, v_idx, tr_id, str(txt)))

            for tr_id, chapters_list in (b.get("tr") or {}).items():
                if not isinstance(chapters_list, list):
                    continue
                for c_idx, ch_verses in enumerate(chapters_list, 1):
                    if not isinstance(ch_verses, list):
                        continue
                    for v_idx, txt in enumerate(ch_verses, 1):
                        if txt:
                            verse_rows.append((bid, c_idx, v_idx, tr_id, str(txt)))

        cur.executemany(
            "INSERT INTO books (id, name, abbr, division, testament, lang, deuterocanon, chapter_count, sort_order) VALUES (?,?,?,?,?,?,?,?,?)",
            book_rows,
        )
        cur.executemany(
            "INSERT INTO verses (book_id, chapter, verse, translation_id, text) VALUES (?,?,?,?,?)",
            verse_rows,
        )
        cur.executemany(
            "INSERT INTO verses_fts (book_id, chapter, verse, translation_id, text) VALUES (?,?,?,?,?)",
            verse_rows,
        )

        # 3. Study Notes from canonical shards
        note_rows = []
        note_fts_rows = []
        if notes_dir.exists():
            for shard_file in sorted(notes_dir.glob("*.js")):
                stem = shard_file.stem
                if stem not in canonical_book_ids:
                    continue
                parsed = _parse_note_shard(shard_file)
                if not parsed:
                    continue
                bid = parsed.get("book_id", stem)
                chapters = parsed.get("chapters") or {}
                for ch_str, verses_dict in chapters.items():
                    try:
                        ch_num = int(ch_str)
                    except ValueError:
                        continue
                    if not isinstance(verses_dict, dict):
                        continue
                    for v_str, items in verses_dict.items():
                        try:
                            v_num = int(v_str)
                        except ValueError:
                            continue
                        if not isinstance(items, list):
                            continue
                        for item in items:
                            if not isinstance(item, dict):
                                continue
                            body = str(item.get("html") or item.get("text") or item.get("body") or "").strip()
                            if not body:
                                continue
                            plain_body = _HTML_TAG_RE.sub(" ", body)
                            plain_body = " ".join(plain_body.split())
                            title = str(item.get("title") or "")
                            src = str(item.get("src") or "")
                            note_rows.append(
                                (
                                    bid,
                                    ch_num,
                                    v_num,
                                    src,
                                    str(item.get("tier") or ""),
                                    str(item.get("kind") or ""),
                                    str(item.get("marker") or ""),
                                    str(item.get("anchor_word") or ""),
                                    title,
                                    body,
                                )
                            )
                            note_fts_rows.append((bid, ch_num, v_num, src, title, plain_body))

        cur.executemany(
            "INSERT INTO notes (book_id, chapter, verse, src, tier, kind, marker, anchor_word, title, body) VALUES (?,?,?,?,?,?,?,?,?,?)",
            note_rows,
        )
        cur.executemany(
            "INSERT INTO notes_fts (book_id, chapter, verse, src, title, body) VALUES (?,?,?,?,?,?)",
            note_fts_rows,
        )

        # 4. Text-Critical Apparatus
        app_rows = []
        app_fts_rows = []
        for idx, item in enumerate(data.get("text_critical_apparatus", [])):
            aid = str(item.get("id") or f"tc_{idx}")
            bid = str(item.get("book") or item.get("book_id") or "")
            ch = int(item.get("chapter") or 0)
            vs = int(item.get("verse") or 0)
            title = str(item.get("title") or "")
            rating = str(item.get("metzger_rating") or item.get("rating") or "")
            payload = json.dumps(item, ensure_ascii=False)
            app_rows.append(
                (
                    aid,
                    str(item.get("testament") or ""),
                    bid,
                    ch,
                    vs,
                    str(item.get("verse_range") or ""),
                    title,
                    rating,
                    payload,
                )
            )
            body_text = " ".join(
                str(x)
                for x in (
                    item.get("verse_range", ""),
                    item.get("summary", ""),
                    item.get("commentary", ""),
                    item.get("scholarly_consensus", ""),
                )
                if x
            )
            app_fts_rows.append((aid, bid, ch, vs, title, body_text or payload[:500]))

        cur.executemany(
            "INSERT INTO apparatus (id, testament, book_id, chapter, verse, verse_range, title, metzger_rating, payload_json) VALUES (?,?,?,?,?,?,?,?,?)",
            app_rows,
        )
        cur.executemany(
            "INSERT INTO apparatus_fts (apparatus_id, book_id, chapter, verse, title, body) VALUES (?,?,?,?,?,?)",
            app_fts_rows,
        )

        # 5. BibCrit Vorlagen
        vor_entries = (data.get("bibcrit_vorlagen") or {}).get("entries", [])
        vor_rows = []
        for idx, item in enumerate(vor_entries):
            vid = str(item.get("id") or f"vor_{idx}")
            vor_rows.append(
                (
                    vid,
                    str(item.get("book_id") or ""),
                    int(item.get("chapter") or 0),
                    int(item.get("verse_start") or item.get("verse") or 0),
                    int(item.get("verse_end") or item.get("verse") or 0),
                    str(item.get("title") or ""),
                    str(item.get("ref") or ""),
                    json.dumps(item, ensure_ascii=False),
                )
            )
        cur.executemany(
            "INSERT INTO bibcrit_vorlagen (id, book_id, chapter, verse_start, verse_end, title, ref, payload_json) VALUES (?,?,?,?,?,?,?,?)",
            vor_rows,
        )

        # 6. Theological Revisions
        rev_entries = (data.get("theological_revisions") or {}).get("entries", [])
        rev_rows = []
        for idx, item in enumerate(rev_entries):
            rid = str(item.get("id") or f"rev_{idx}")
            rev_rows.append(
                (
                    rid,
                    str(item.get("category") or ""),
                    str(item.get("ref") or ""),
                    str(item.get("title") or ""),
                    json.dumps(item, ensure_ascii=False),
                )
            )
        cur.executemany(
            "INSERT INTO theological_revisions (id, category, ref, title, payload_json) VALUES (?,?,?, ?,?)",
            rev_rows,
        )

        # 7. Chiasms
        chi_entries = (data.get("biblical_chiasms") or {}).get("entries", [])
        chi_rows = []
        for idx, item in enumerate(chi_entries):
            cid = str(item.get("id") or f"chi_{idx}")
            chi_rows.append(
                (
                    cid,
                    str(item.get("ref") or ""),
                    str(item.get("title") or ""),
                    str(item.get("apex") or ""),
                    json.dumps(item, ensure_ascii=False),
                )
            )
        cur.executemany(
            "INSERT INTO chiasms (id, ref, title, apex, payload_json) VALUES (?,?,?,?,?)",
            chi_rows,
        )

        # 8. Indexes (created after bulk insert for speed)
        cur.executescript(
            """
            CREATE INDEX idx_verses_bcv ON verses(book_id, chapter, verse);
            CREATE INDEX idx_verses_bct ON verses(book_id, chapter, translation_id);
            CREATE INDEX idx_notes_bcv ON notes(book_id, chapter, verse);
            CREATE INDEX idx_notes_src ON notes(src);
            CREATE INDEX idx_apparatus_bcv ON apparatus(book_id, chapter, verse);
            CREATE INDEX idx_vorlagen_bc ON bibcrit_vorlagen(book_id, chapter);
            CREATE INDEX idx_patristic_bcv ON patristic_index(book_id, chapter, verse);
            """
        )

        elapsed = round(time.perf_counter() - t0, 3)
        meta_rows = [
            ("schema_version", SCHEMA_VERSION),
            ("built_utc", datetime.now(timezone.utc).isoformat()),
            ("books_count", str(len(book_rows))),
            ("translations_count", str(len(tr_rows))),
            ("verses_count", str(len(verse_rows))),
            ("notes_count", str(len(note_rows))),
            ("apparatus_count", str(len(app_rows))),
            ("vorlagen_count", str(len(vor_rows))),
            ("revisions_count", str(len(rev_rows))),
            ("chiasms_count", str(len(chi_rows))),
            ("build_seconds", str(elapsed)),
        ]
        cur.executemany("INSERT INTO meta (key, value) VALUES (?,?)", meta_rows)
        conn.commit()
    finally:
        conn.close()

    os.replace(tmp_db, db_out)
    size_bytes = db_out.stat().st_size
    return {
        "db_path": str(db_out),
        "size_bytes": size_bytes,
        "books": len(book_rows),
        "translations": len(tr_rows),
        "verses": len(verse_rows),
        "notes": len(note_rows),
        "apparatus": len(app_rows),
        "vorlagen": len(vor_rows),
        "revisions": len(rev_rows),
        "chiasms": len(chi_rows),
        "build_seconds": elapsed,
    }


if __name__ == "__main__":
    stats = build_sqlite()
    print(json.dumps(stats, indent=2))
