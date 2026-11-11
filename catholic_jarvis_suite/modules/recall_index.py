"""
Recall index: one SQLite FTS5 full-text index over

  * every Claude and Antigravity message (user AND assistant), from modules.log_reader, and
  * every markdown file listed in data/corpus_index.json (split into paragraph chunks).

so a single query answers "where did X go?": the conversation where it was discussed AND the
file it ended up in.

Database: data/recall_fts.sqlite
    docs(id, kind, surface, sid, role, ts, path, rel_path, line, title, fkind, text)
        kind    'msg' | 'file'
        surface 'CL' | 'AG' | 'FILE'
        role    'user' | 'assistant' | 'file'
        line    1-based line where the chunk starts (files); message ordinal in session (msgs)
        fkind   corpus_index kind (SUBJECT / INFRASTRUCTURE / PROVENANCE) for files
    recall  FTS5 external-content table over docs(text, title)   (porter + unicode61)
    meta(key, value)   fingerprints, built_at, counts
    file_state(path, size, mtime, nchunks)   per-file change detection

Rebuild policy (nothing runs in the background; search never rebuilds):
    refresh() computes the log_reader fingerprint (path|size|mtime of every source log, the very
    function log_reader uses for its own cache) and a files fingerprint, and does nothing when
    both equal the stored values. Conversation rows are replaced wholesale when the log
    fingerprint changed; file rows are replaced per file whose (size, mtime) changed.

Not read, by design: corpus entries under 06_SOURCE_MATERIAL\\_SESSION_TRANSCRIPTS (raw transcripts
that duplicate the conversation logs; CLAUDE.md section X marks them prohibited auto-reads).
"""
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_HERE, "data")
DB_PATH = os.path.join(DATA_DIR, "recall_fts.sqlite")
CORPUS_INDEX = os.path.join(DATA_DIR, "corpus_index.json")

EXCLUDED_DIR_FRAGMENTS = ("_SESSION_TRANSCRIPTS",)
# 2026-10-06 (integrator): archive, backup and build-copy folders were 60+ MB of near-identical
# old masters (the index had grown to 435 MB and returned the same paragraph five times).
# Matched case-insensitively against the full path. Exact duplicate files are also indexed once.
EXCLUDED_PATH_FRAGMENTS_CI = ("\\07_archive_old_process\\", "\\_backups", "backup", "\\_build_scripts_",
                              "\\_previous_", "_superseded", "\\raw\\", "\\_pre_consolidation")
CHUNK_MAX = 1200          # characters per file chunk
CHUNK_MIN = 80            # shorter blocks (headings, one-liners) are merged into the next block
SNIPPET_TOKENS = 36

HL_OPEN, HL_CLOSE = "\x02", "\x03"
_CTRL = re.compile("[\x02\x03]")
_LOCK = threading.RLock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs(
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL, surface TEXT NOT NULL, sid TEXT, role TEXT, ts TEXT,
    path TEXT, rel_path TEXT, line INTEGER, title TEXT, fkind TEXT, text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS docs_kind ON docs(kind);
CREATE INDEX IF NOT EXISTS docs_path ON docs(path);
CREATE VIRTUAL TABLE IF NOT EXISTS recall USING fts5(
    text, title, content='docs', content_rowid='id', tokenize='porter unicode61 remove_diacritics 2'
);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS file_state(path TEXT PRIMARY KEY, size INTEGER, mtime REAL, nchunks INTEGER);
"""


class IndexMissing(Exception):
    """The FTS database does not exist (or has no schema) yet."""


# --------------------------------------------------------------------------- connection / meta
def _connect(db_path=None, create=False):
    db_path = db_path or DB_PATH
    if not create and not os.path.exists(db_path):
        raise IndexMissing(db_path)
    con = sqlite3.connect(db_path, timeout=60, check_same_thread=False)
    con.row_factory = sqlite3.Row
    if create:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
    return con


def _meta_get(con, key, default=None):
    r = con.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return r[0] if r else default


def _meta_set(con, key, value):
    con.execute("INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)))


# --------------------------------------------------------------------------- fingerprints
def conversation_fingerprint():
    """Fingerprint of the conversation log sources: the same function log_reader keys its own
    cache on (path|size|mtime of every source log). Cheap: stat() only, no log is read."""
    from modules import log_reader
    cl, ag = log_reader._sources()
    return log_reader._fingerprint(cl + ag)


def load_corpus_files(corpus_index_path=None):
    """Corpus entries to index: those listed in corpus_index.json that still exist and are not
    under an excluded directory. Returns (entries, skipped_excluded, skipped_missing)."""
    path = corpus_index_path or CORPUS_INDEX
    try:
        with open(path, encoding="utf-8") as fh:
            files = json.load(fh).get("files", [])
    except Exception:
        return [], 0, 0
    keep, excl, missing = [], 0, 0
    for f in files:
        p = f.get("path")
        if not p:
            continue
        pl = p.lower()
        if any(frag in p for frag in EXCLUDED_DIR_FRAGMENTS) or any(frag in pl for frag in EXCLUDED_PATH_FRAGMENTS_CI):
            excl += 1
            continue
        try:
            st = os.stat(p)
        except OSError:
            missing += 1
            continue
        keep.append({"path": p, "rel_path": f.get("rel_path") or p, "title": f.get("title") or "",
                     "kind": f.get("kind") or "", "size": st.st_size, "mtime": st.st_mtime})
    # Exact duplicates (same bytes): keep the shortest path, count the rest as excluded.
    by_size = {}
    for e in keep:
        by_size.setdefault(e["size"], []).append(e)
    dup_ids = set()
    for group in by_size.values():
        if len(group) < 2:
            continue
        seen = {}
        for e in sorted(group, key=lambda e: (len(e["path"]), e["path"])):
            try:
                with open(e["path"], "rb") as fh:
                    h = hashlib.sha1(fh.read()).hexdigest()
            except OSError:
                continue
            if h in seen:
                dup_ids.add(id(e))
            else:
                seen[h] = e
    if dup_ids:
        excl += len(dup_ids)
        keep = [e for e in keep if id(e) not in dup_ids]
    return keep, excl, missing


def files_fingerprint(entries):
    h = hashlib.sha1()
    for e in sorted(entries, key=lambda e: e["path"]):
        h.update(f"{e['path']}|{e['size']}|{int(e['mtime'])}\n".encode("utf-8", "replace"))
    return h.hexdigest()


# --------------------------------------------------------------------------- chunking
def chunk_text(text):
    """Split a markdown file into (start_line, chunk_text) pairs. start_line is 1-based.
    Blocks are separated by blank lines; a block over CHUNK_MAX chars is split at line breaks
    (a single over-long line is hard-split, keeping that line's number); a block shorter than
    CHUNK_MIN chars (a heading, a one-liner) is joined to the block that follows it."""
    lines = text.splitlines()
    blocks = []                       # (start_line, [lines])
    cur, cur_start = [], None
    for i, ln in enumerate(lines, 1):
        if ln.strip():
            if cur_start is None:
                cur_start = i
            cur.append(ln)
        elif cur:
            blocks.append((cur_start, cur))
            cur, cur_start = [], None
    if cur:
        blocks.append((cur_start, cur))

    pieces = []                       # (start_line, text) each <= CHUNK_MAX-ish
    for start, blk in blocks:
        buf, buf_len, buf_start = [], 0, start
        for off, ln in enumerate(blk):
            lineno = start + off
            while len(ln) > CHUNK_MAX:                  # hard-split a huge single line
                if buf:
                    pieces.append((buf_start, "\n".join(buf)))
                    buf, buf_len = [], 0
                pieces.append((lineno, ln[:CHUNK_MAX]))
                ln = ln[CHUNK_MAX:]
            if buf and buf_len + len(ln) > CHUNK_MAX:
                pieces.append((buf_start, "\n".join(buf)))
                buf, buf_len = [], 0
            if not buf:
                buf_start = lineno
            buf.append(ln)
            buf_len += len(ln) + 1
        if buf:
            pieces.append((buf_start, "\n".join(buf)))

    out, carry = [], None             # merge tiny pieces forward
    for start, txt in pieces:
        if carry:
            start, txt = carry[0], carry[1] + "\n" + txt
            carry = None
        if len(txt) < CHUNK_MIN:
            carry = (start, txt)
            continue
        out.append((start, txt))
    if carry:
        out.append(carry)
    return out


def _read_file(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace")


# --------------------------------------------------------------------------- build / refresh
def _delete_where(con, where, params):
    """Remove rows from docs AND the external-content FTS index (the FTS 'delete' command needs
    the original column values, so read them first)."""
    rows = con.execute(f"SELECT id, text, title FROM docs WHERE {where}", params).fetchall()
    for r in rows:
        con.execute("INSERT INTO recall(recall, rowid, text, title) VALUES('delete', ?, ?, ?)",
                    (r["id"], r["text"], r["title"] or ""))
    con.execute(f"DELETE FROM docs WHERE {where}", params)
    return len(rows)


def _insert_docs(con, rows):
    """rows: tuples (kind, surface, sid, role, ts, path, rel_path, line, title, fkind, text)."""
    n = 0
    for r in rows:
        cur = con.execute(
            "INSERT INTO docs(kind,surface,sid,role,ts,path,rel_path,line,title,fkind,text) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)", r)
        con.execute("INSERT INTO recall(rowid, text, title) VALUES(?, ?, ?)", (cur.lastrowid, r[10], r[8] or ""))
        n += 1
    return n


def _message_rows(messages):
    ordinal = {}
    for m in messages:
        text = _CTRL.sub("", m.get("text") or "")
        if not text.strip():
            continue
        k = (m["surface"], m["sid"])
        ordinal[k] = ordinal.get(k, 0) + 1
        yield ("msg", m["surface"], m["sid"], m["role"], m.get("ts") or "", m.get("file") or "", "",
               ordinal[k], "", "", text)


def _file_rows(entry):
    text = _CTRL.sub("", _read_file(entry["path"]))
    mtime_iso = datetime.fromtimestamp(entry["mtime"], tz=timezone.utc).isoformat()
    for line, chunk in chunk_text(text):
        yield ("file", "FILE", "", "file", mtime_iso, entry["path"], entry["rel_path"], line,
               entry["title"], entry["kind"], chunk)


def refresh(db_path=None, force=False, messages=None, files=None, conv_fp=None, corpus_index_path=None):
    """Bring the index up to date. Returns a dict describing what happened.

    messages / files / conv_fp can be injected (tests do this); by default the messages come from
    modules.log_reader.load_messages() and the files from corpus_index.json."""
    with _LOCK:
        t0 = time.time()
        db_path = db_path or DB_PATH
        con = _connect(db_path, create=True)
        try:
            cur_conv_fp = conv_fp if conv_fp is not None else conversation_fingerprint()
            if files is None:
                files, excl, missing = load_corpus_files(corpus_index_path)
            else:
                excl = missing = 0
            cur_files_fp = files_fingerprint(files)
            old_conv_fp, old_files_fp = _meta_get(con, "conv_fp"), _meta_get(con, "files_fp")
            conv_changed = force or cur_conv_fp != old_conv_fp
            files_changed = force or cur_files_fp != old_files_fp
            res = {"rebuilt": False, "conversations_reindexed": False, "files_reindexed": 0,
                   "files_removed": 0, "reason": "fingerprints unchanged"}
            if not (conv_changed or files_changed):
                res["seconds"] = round(time.time() - t0, 3)
                res.update(status(db_path, _con=con))
                return res

            if conv_changed:
                msgs = messages if messages is not None else _load_messages()
            con.execute("BEGIN IMMEDIATE")
            try:
                if conv_changed:
                    _delete_where(con, "kind='msg'", ())
                    n = _insert_docs(con, _message_rows(msgs))
                    _meta_set(con, "conv_fp", cur_conv_fp)
                    _meta_set(con, "n_messages", n)
                    res["conversations_reindexed"] = True
                if files_changed:
                    state = {r["path"]: (r["size"], r["mtime"]) for r in con.execute("SELECT * FROM file_state")}
                    wanted = {e["path"] for e in files}
                    for p in list(state):
                        if p not in wanted:
                            _delete_where(con, "kind='file' AND path=?", (p,))
                            con.execute("DELETE FROM file_state WHERE path=?", (p,))
                            res["files_removed"] += 1
                    for e in files:
                        if not force and state.get(e["path"]) == (e["size"], e["mtime"]):
                            continue
                        _delete_where(con, "kind='file' AND path=?", (e["path"],))
                        try:
                            n = _insert_docs(con, _file_rows(e))
                        except OSError:
                            n = 0
                        con.execute("INSERT OR REPLACE INTO file_state(path,size,mtime,nchunks) VALUES(?,?,?,?)",
                                    (e["path"], e["size"], e["mtime"], n))
                        res["files_reindexed"] += 1
                    _meta_set(con, "files_fp", cur_files_fp)
                    _meta_set(con, "skipped_excluded", excl)
                    _meta_set(con, "skipped_missing", missing)
                n_files = con.execute("SELECT count(DISTINCT path) FROM docs WHERE kind='file'").fetchone()[0]
                n_chunks = con.execute("SELECT count(*) FROM docs WHERE kind='file'").fetchone()[0]
                _meta_set(con, "n_files", n_files)
                _meta_set(con, "n_file_chunks", n_chunks)
                _meta_set(con, "built_at", datetime.now(timezone.utc).isoformat())
                con.execute("COMMIT")
            except BaseException:
                con.execute("ROLLBACK")
                raise
            if conv_changed or files_changed:
                con.execute("INSERT INTO recall(recall) VALUES('optimize')")
            res["rebuilt"] = True
            res["reason"] = "forced" if force else "fingerprint changed"
            res["seconds"] = round(time.time() - t0, 3)
            res.update(status(db_path, _con=con))
            return res
        finally:
            con.close()


def _load_messages():
    from modules.log_reader import load_messages
    return load_messages()


def status(db_path=None, _con=None, check_current=True):
    """Index size, build time and fingerprints; `stale` is True when the live conversation logs
    or corpus files differ from what the index was built from."""
    db_path = db_path or DB_PATH
    if _con is None and not os.path.exists(db_path):
        return {"exists": False, "stale": True, "db_path": db_path}
    con = _con or _connect(db_path)
    try:
        g = lambda k, d=None: _meta_get(con, k, d)
        out = {
            "exists": True,
            "db_path": db_path,
            "db_bytes": os.path.getsize(db_path),
            "built_at": g("built_at"),
            "fingerprint": f"{g('conv_fp', '')[:12]}:{g('files_fp', '')[:12]}",
            "conversation_fingerprint": g("conv_fp"),
            "files_fingerprint": g("files_fp"),
            "messages": int(g("n_messages", 0) or 0),
            "files": int(g("n_files", 0) or 0),
            "file_chunks": int(g("n_file_chunks", 0) or 0),
            "skipped_excluded_files": int(g("skipped_excluded", 0) or 0),
            "skipped_missing_files": int(g("skipped_missing", 0) or 0),
            "stale": False,
        }
        if check_current:
            try:
                cur_conv = conversation_fingerprint()
                entries, _, _ = load_corpus_files()
                cur_files = files_fingerprint(entries)
                out["current_conversation_fingerprint"] = cur_conv
                out["conversations_stale"] = cur_conv != g("conv_fp")
                out["files_stale"] = cur_files != g("files_fp")
                out["stale"] = out["conversations_stale"] or out["files_stale"]
            except Exception as e:  # noqa: BLE001
                out["stale_check_error"] = f"{type(e).__name__}: {e}"
        return out
    finally:
        if _con is None:
            con.close()


# --------------------------------------------------------------------------- query building
_QCTRL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TOKEN = re.compile(r'"([^"]*)"|(\S+)')


def build_match(q, mode="all"):
    """Turn raw user text into a safe FTS5 MATCH expression, or None if nothing searchable.

    Every term becomes an FTS5 quoted string, so operators and syntax characters typed by the
    user (AND OR NOT NEAR ( ) : ^ - + ") are literals and can never raise a syntax error.
    "double quoted text" stays a phrase; a bare term ending in * is a prefix search.
    Terms without any letter or digit are dropped. mode='all' ANDs the terms, 'any' ORs them,
    'phrase' treats the whole query as one exact phrase."""
    q = _QCTRL.sub(" ", q or "")          # NUL and other control characters break FTS5 strings
    if mode == "phrase":
        body = q.replace('"', " ").strip()
        return f'"{body}"' if re.search(r"\w", body) else None
    terms = []
    for m in _TOKEN.finditer(q):
        phrase, bare = m.group(1), m.group(2)
        if phrase is not None:
            body = phrase.strip()
            prefix = False
        else:
            body = bare
            prefix = body.endswith("*")
            body = body.rstrip("*")
        if not re.search(r"\w", body):
            continue
        body = body.replace('"', '""')
        terms.append(f'"{body}"' + ("*" if prefix else ""))
    if not terms:
        return None
    return (" OR " if mode == "any" else " AND ").join(terms)


def _parse_snippet(marked):
    """FTS5 snippet with \\x02/\\x03 markers -> (plain text, [[start, end], ...])."""
    plain, ranges, start, i = [], [], None, 0
    for ch in marked:
        if ch == HL_OPEN:
            start = i
        elif ch == HL_CLOSE:
            if start is not None:
                ranges.append([start, i])
                start = None
        else:
            plain.append(ch)
            i += 1
    return "".join(plain), ranges


_SURFACES = {"cl": "CL", "claude": "CL", "ag": "AG", "antigravity": "AG", "file": "FILE", "files": "FILE"}


def search(q, surface=None, role=None, scope="all", fkind=None, mode="all", sort="rank",
           limit=25, offset=0, db_path=None):
    """Run a Recall search. Raises IndexMissing if the database has not been built."""
    t0 = time.time()
    db_path = db_path or DB_PATH
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    resp = {"q": q or "", "total": 0, "offset": offset, "limit": limit, "results": [], "note": None}
    match = build_match(q, mode)
    if match is None:
        resp["note"] = "empty or unsearchable query (needs at least one letter or digit)"
        resp["took_ms"] = round((time.time() - t0) * 1000, 2)
        return resp
    resp["match"] = match

    where, params = ["recall MATCH ?"], [match]
    scope = (scope or "all").lower()
    if scope in ("conversations", "conversation", "msg", "messages"):
        where.append("d.kind='msg'")
    elif scope in ("files", "file"):
        where.append("d.kind='file'")
    if surface and surface.strip():
        s = _SURFACES.get(surface.strip().lower())
        if s is None:
            resp["note"] = f"unknown surface {surface!r}; use CL, AG or FILE"
            resp["took_ms"] = round((time.time() - t0) * 1000, 2)
            return resp
        where.append("d.surface=?")
        params.append(s)
    if role and role.strip() and role.strip().lower() != "any":
        where.append("d.role=?")
        params.append(role.strip().lower())
    if fkind and fkind.strip() and fkind.strip().upper() != "ALL":
        where.append("d.fkind=?")
        params.append(fkind.strip().upper())
    wsql = " AND ".join(where)
    order = {"newest": "d.ts DESC", "oldest": "d.ts ASC"}.get(sort, "rank")

    con = _connect(db_path)
    try:
        try:
            resp["total"] = con.execute(
                f"SELECT count(*) FROM recall JOIN docs d ON d.id = recall.rowid WHERE {wsql}", params).fetchone()[0]
            rows = con.execute(
                f"SELECT d.*, snippet(recall, -1, ?, ?, '…', {SNIPPET_TOKENS}) AS snip, rank AS score "
                f"FROM recall JOIN docs d ON d.id = recall.rowid WHERE {wsql} "
                f"ORDER BY {order}, d.id LIMIT ? OFFSET ?",
                [HL_OPEN, HL_CLOSE] + params + [limit, offset]).fetchall()
        except sqlite3.OperationalError as e:      # belt and braces: never a 500 for user input
            resp["note"] = f"query could not be run: {e}"
            rows = []
        for r in rows:
            snippet, hl = _parse_snippet(r["snip"] or "")
            item = {
                "type": "conversation" if r["kind"] == "msg" else "file",
                "surface": r["surface"],
                "role": r["role"],
                "ts": r["ts"],
                "date": (r["ts"] or "")[:10],
                "snippet": snippet,
                "highlights": hl,
                "score": r["score"],
            }
            if r["kind"] == "msg":
                item.update({"sid": r["sid"], "message_no": r["line"], "log_file": r["path"],
                             "copy": r["sid"]})
            else:
                item.update({"path": r["path"], "rel_path": r["rel_path"], "line": r["line"],
                             "title": r["title"], "file_kind": r["fkind"],
                             "copy": f"{r['path']}:{r['line']}"})
            resp["results"].append(item)
    finally:
        con.close()
    resp["took_ms"] = round((time.time() - t0) * 1000, 2)
    return resp


if __name__ == "__main__":
    import sys
    if "--status" in sys.argv:
        print(json.dumps(status(), indent=2))
    else:
        print(json.dumps(refresh(force="--force" in sys.argv), indent=2))
