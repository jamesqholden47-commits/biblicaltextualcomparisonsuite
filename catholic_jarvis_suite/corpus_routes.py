"""
Corpus Routes for CatholicJarvis Master Work Suite
Provides API endpoints for querying, searching, filtering, and viewing the indexed corpus.
Enforces Rule 13 (Subject/Infra distinction) and Rule 14 (Code-span stripping).
Strictly restricts file reading to paths verified in the corpus index.
"""

import os
import re
import json
import time
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Query, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse

router = APIRouter(prefix="/api/corpus", tags=["corpus"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_FILE = os.path.join(DATA_DIR, "corpus_index.json")

_CACHED_INDEX: Optional[Dict[str, Any]] = None
_CACHED_MTIME: float = 0
_KNOWN_PATHS_SET: set = set()

def load_index(force: bool = False) -> Dict[str, Any]:
    global _CACHED_INDEX, _CACHED_MTIME, _KNOWN_PATHS_SET
    if not os.path.exists(INDEX_FILE):
        return {
            "total_files": 0,
            "total_words": 0,
            "counts_by_kind": {},
            "counts_by_root": {},
            "top_scriptures": [],
            "top_sources": [],
            "files": []
        }

    mtime = os.path.getmtime(INDEX_FILE)
    if force or _CACHED_INDEX is None or mtime > _CACHED_MTIME:
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            _CACHED_INDEX = data
            _CACHED_MTIME = mtime
            _KNOWN_PATHS_SET = {
                os.path.normcase(os.path.abspath(doc["path"]))
                for doc in data.get("files", [])
                if "path" in doc
            }
        except Exception as e:
            print(f"Error loading corpus index: {e}")
            if _CACHED_INDEX is None:
                return {"files": [], "total_files": 0}
    return _CACHED_INDEX

@router.get("")
async def get_corpus(
    q: Optional[str] = Query(None, description="Search query for title or path"),
    kind: Optional[str] = Query(None, description="Filter by kind: SUBJECT, INFRASTRUCTURE, PROVENANCE"),
    root: Optional[str] = Query(None, description="Filter by root: PROJECT, AA1, BRAIN"),
    scripture: Optional[str] = Query(None, description="Filter by scripture reference"),
    source: Optional[str] = Query(None, description="Filter by patristic source"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Query and filter indexed markdown documents across the dissertation and research corpus."""
    idx = load_index()
    files = idx.get("files", [])

    filtered = files

    if kind and kind.upper() != "ALL":
        target_kind = kind.upper()
        filtered = [f for f in filtered if f.get("kind") == target_kind]

    if root and root.upper() != "ALL":
        target_root = root.upper()
        filtered = [f for f in filtered if f.get("root") == target_root]

    if scripture:
        s_query = scripture.lower()
        filtered = [
            f for f in filtered
            if any(s_query in s.lower() for s in f.get("scripture_refs", []))
        ]

    if source:
        src_query = source.lower()
        filtered = [
            f for f in filtered
            if any(src_query in s.lower() for s in f.get("source_hits", []))
        ]

    if q:
        q_lower = q.lower()
        filtered = [
            f for f in filtered
            if (
                q_lower in f.get("title", "").lower()
                or q_lower in f.get("rel_path", "").lower()
                or any(q_lower in h.lower() for h in f.get("headings", []))
            )
        ]

    total_matches = len(filtered)
    paged = filtered[offset : offset + limit]

    return {
        "total": total_matches,
        "offset": offset,
        "limit": limit,
        "count": len(paged),
        "results": paged
    }

@router.get("/stats")
async def get_corpus_stats():
    """Returns global stats about the indexed corpus."""
    idx = load_index()
    return {
        "generated_at": idx.get("generated_at"),
        "total_files": idx.get("total_files", 0),
        "total_words": idx.get("total_words", 0),
        "counts_by_kind": idx.get("counts_by_kind", {}),
        "counts_by_root": idx.get("counts_by_root", {}),
        "top_scriptures": idx.get("top_scriptures", []),
        "top_sources": idx.get("top_sources", [])
    }

@router.get("/file")
async def get_corpus_file(path: str = Query(..., description="Absolute path to file")):
    """
    Safely read and return file content.
    SECURITY: Rejects any path not strictly present in the indexed corpus.
    """
    load_index()
    norm_req = os.path.normcase(os.path.abspath(path))

    if norm_req not in _KNOWN_PATHS_SET:
        raise HTTPException(
            status_code=403,
            detail="Access forbidden: file is not part of the verified corpus index."
        )

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on disk.")

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {
            "path": path,
            "filename": os.path.basename(path),
            "size": os.path.getsize(path),
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

@router.post("/reindex")
async def reindex_corpus():
    """Triggers a re-index of the corpus and refreshes cache."""
    try:
        import indexer
        res = indexer.run_indexer()
        load_index(force=True)
        return {
            "status": "ok",
            "total_files": res.get("total_files", 0),
            "total_words": res.get("total_words", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")

@router.get("/search")
async def fulltext_search(
    q: str = Query(..., min_length=2, description="Text to search for"),
    max_matches: int = Query(50, ge=1, le=200)
):
    """
    Performs full-text search across all indexed files.
    Returns matched files with line numbers and snippets.
    Rule 14: ignores matches inside code blocks if requested.
    """
    idx = load_index()
    files = idx.get("files", [])
    results = []
    q_lower = q.lower()

    for item in files:
        fpath = item.get("path")
        if not fpath or not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            for line_idx, line in enumerate(lines):
                if q_lower in line.lower():
                    # Strip code spans per Rule 14
                    clean_line = re.sub(r'`[^`]*`', '', line).strip()
                    results.append({
                        "path": fpath,
                        "rel_path": item.get("rel_path", fpath),
                        "title": item.get("title", ""),
                        "root": item.get("root", ""),
                        "kind": item.get("kind", ""),
                        "line_num": line_idx + 1,
                        "snippet": clean_line[:200]
                    })
                    if len(results) >= max_matches:
                        return {"query": q, "total_matches": len(results), "matches": results}
        except Exception:
            continue

    return {"query": q, "total_matches": len(results), "matches": results}
