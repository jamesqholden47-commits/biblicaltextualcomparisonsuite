"""
Corpus Indexer for CatholicJarvis Work Suite
Scans the project root, aa1, and brain artifacts.
Extracts metadata, scripture references, patristic sources, and classifies by SUBJECT/INFRASTRUCTURE/PROVENANCE.
Adheres strictly to Rule 13 (Subject vs Infrastructure) and Rule 14 (Strip code spans).
"""

import os
import re
import sys
import time
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

PROJECT_ROOT = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism"
AA1_ROOT = r"C:\Users\Elation\aa1"
BRAIN_ROOT = r"C:\Users\Elation\.gemini\antigravity\brain"

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "09_APPS_CATHOLICJARVIS", "catholic_jarvis_suite", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "corpus_index.json")

# 120 days cutoff
CUTOFF_SECONDS = 120 * 86400

# Classification markers (from 02_CONTROL_AND_STATE\_TOOLS_ARCHIVE\classify_dossiers.py)
INFRA_MARKERS = [
    "ostep", "ext4", "amat", "checksum", "raid", "sqlite", "ripgrep", "pdftotext",
    "tesseract", "ocr", "vlm", "gpu", "cuda", "embedding model", "vector search",
    "sharex", "screenshot", "hotkey", "registerhotkey", "subprocess", "stdout",
    "daemon", "tray icon", "pidfile", "ghidra", "frida", "screenpipe", "webview",
    "latency", "throughput", "tokens/sec", "cache hit", "prompt cache", "api key",
    "npm ", "pytest", "regex", "filesystem", "inode", "b-tree", "hash table",
    "thrumble", "elevenlabs", "piper", "tts", "text-to-speech", "transcription",
    "barge-in", "screen capture", "window handle", "pywin32", "tkinter", "startup folder",
    "fastapi", "uvicorn", "subagent", "gemini-3", "copilot", "electron"
]

THEO_MARKERS = [
    "catholic", "patristic", "talmud", "mishnah", "sanhedrin", "torah", "magisterium",
    "bishop", "eucharist", "papal", "apostolic", "qumran", "halakh", "sifrei",
    "irenaeus", "augustine", "cyprian", "sola scriptura", "church fathers", "rabbi",
    "pharisee", "second temple", "deuterocanon", "nicaea", "councils", "scripture",
    "exegesis", "josephus", "rambam", "mekhilta", "christ", "gospel", "covenant",
    "dikaio", "justification", "righteousness", "pauline", "romans", "galatians",
    "septuagint", "lxx", "vulgate", "reformation", "luther", "trent", "grace",
    "soteriolog", "forensic", "imputed", "newman", "development of doctrine",
    "ignatius", "polycarp", "clement", "tertullian", "optatus", "chrysostom",
    "hishtachavah", "nasrani", "malabar", "hormisdas", "elvira", "aquinas"
]

# Source abbreviations pattern
SOURCE_ABBR_PAT = re.compile(
    r'\b(PG\s*\d+|PL\s*\d+|CSEL\s*\d+|CCSL\s*\d+|Mansi\s*[I|V|X|L|C|D|M]+|Denzinger|DH\s*\d+|ST\s+[I|V|X]+|GCS\s*\d+|CSCO\s*\d+|PTS\s*\d+|Sefaria|Bede|Victorinus)\b',
    re.IGNORECASE
)

# Scripture pattern
SCRIPTURE_PAT = re.compile(
    r'\b(?:(?:1|2|3)\s*(?:Chron|Chr|Sam|Kgs|Kings|Cor|Corinthians|Thess|Thessalonians|Tim|Timothy|Pet|Peter|John)|'
    r'Gen|Genesis|Exod?|Exodus|Lev|Leviticus|Num|Numbers|Deut|Deuteronomy|Josh|Joshua|Judg|Judges|Ruth|'
    r'Ps|Psalm|Psalms|Prov|Proverbs|Eccl|Ecclesiastes|Song|Isa|Isaiah|Jer|Jeremiah|Lam|Lamentations|'
    r'Ezek|Ezekiel|Dan|Daniel|Hos|Hosea|Joel|Amos|Obad|Obadiah|Jon|Jonah|Mic|Micah|Nah|Nahum|Hab|Habakkuk|'
    r'Zeph|Zephaniah|Hag|Haggai|Zech|Zechariah|Mal|Malachi|Matt?|Matthew|Mark|Luke|John|Acts|'
    r'Rom|Romans|Gal|Galatians|Eph|Ephesians|Phil|Philippians|Col|Colossians|Titus|Phlm|Philemon|'
    r'Heb|Hebrews|Jas|James|Jude|Rev|Revelation)\.?\s*(\d+):(\d+(?:-\d+)?)\b',
    re.IGNORECASE
)

def strip_code_spans(text: str) -> str:
    """Rule 14: Strip code blocks and inline code spans before extracting references."""
    # Strip multiline code blocks
    text = re.sub(r'```[\s\S]*?```', ' ', text)
    # Strip inline code spans
    text = re.sub(r'`[^`]*`', ' ', text)
    return text

def classify_file(path: str, content: str) -> str:
    """Classify file kind as PROVENANCE, INFRASTRUCTURE, or SUBJECT."""
    norm_path = path.replace("\\", "/").lower()
    
    # Provenance paths
    if any(p in norm_path for p in [
        "_session_transcripts", "_session_logs", "transcript", "_autosave",
        "_ag_session_log", "conversation_log", "_return_from_cli", "_cli_passoff"
    ]):
        return "PROVENANCE"

    # Infrastructure paths
    if any(p in norm_path for p in [
        "_tools_archive", "09_apps_catholicjarvis", "node_modules", "scripts",
        "tests", "build_system_log", "write_boot_header", "write_ag_handoff",
        "cli_bridge", "drift_check", "loss_check", "integrity_check"
    ]):
        # Check if it has overwhelming theological content (e.g. sample files inside app)
        lo_content = content.lower()
        theo_count = sum(lo_content.count(m) for m in THEO_MARKERS)
        if theo_count > 40 and "dossier" in norm_path:
            return "SUBJECT"
        return "INFRASTRUCTURE"

    # Brain scratch or task logs
    if "scratch" in norm_path or ".system_generated" in norm_path:
        return "INFRASTRUCTURE"

    # Content-based scoring for other files
    lo = content.lower()
    infra_score = sum(lo.count(m) for m in INFRA_MARKERS)
    theo_score = sum(lo.count(m) for m in THEO_MARKERS)

    if infra_score >= 8 and infra_score > theo_score * 2:
        return "INFRASTRUCTURE"
    if theo_score >= 4 or "dissertation" in norm_path or "theolog" in norm_path:
        return "SUBJECT"
    if infra_score > theo_score:
        return "INFRASTRUCTURE"
    return "SUBJECT"

def extract_metadata(path: str, root_label: str) -> Dict[str, Any]:
    stat = os.stat(path)
    mtime = stat.st_mtime
    size = stat.st_size
    mtime_iso = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        content = ""

    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    words = len(content.split())

    # Title extraction
    title = ""
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break
    if not title:
        title = os.path.splitext(os.path.basename(path))[0].replace("_", " ")

    # Headings extraction (H2/H3 up to 40)
    headings = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            h_text = stripped.lstrip("#").strip()
            if h_text and len(h_text) < 120:
                headings.append(h_text)
            if len(headings) >= 40:
                break

    # Strip code spans per Rule 14 before matching scripture & sources
    clean_text = strip_code_spans(content)

    # Scripture matches
    scripture_matches = list(set([m.group(0).strip() for m in SCRIPTURE_PAT.finditer(clean_text)]))
    scripture_matches.sort()

    # Source hits
    source_hits = list(set([m.group(0).strip() for m in SOURCE_ABBR_PAT.finditer(clean_text)]))
    source_hits.sort()

    kind = classify_file(path, content)

    # Friendly relative path
    rel_path = os.path.relpath(path, PROJECT_ROOT) if path.startswith(PROJECT_ROOT) else path

    return {
        "path": path,
        "rel_path": rel_path.replace("\\", "/"),
        "root": root_label,
        "title": title,
        "headings": headings,
        "mtime": mtime,
        "mtime_iso": mtime_iso,
        "size": size,
        "sha256": sha,
        "word_count": words,
        "scripture_refs": scripture_matches,
        "source_hits": source_hits,
        "kind": kind
    }

def run_indexer() -> Dict[str, Any]:
    now = time.time()
    cutoff = now - CUTOFF_SECONDS
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    skip_dirs = {"node_modules", ".obsidian", ".trash", "__pycache__", ".git", ".venv", "venv", ".system_generated"}
    indexed_files = []

    # 1. Project Root
    if os.path.exists(PROJECT_ROOT):
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".md"):
                    full_p = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(full_p)
                        if mtime >= cutoff:
                            meta = extract_metadata(full_p, "PROJECT")
                            indexed_files.append(meta)
                    except Exception:
                        pass

    # 2. AA1 Root
    if os.path.exists(AA1_ROOT):
        for root, dirs, files in os.walk(AA1_ROOT):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for file in files:
                if file.endswith(".md"):
                    full_p = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(full_p)
                        if mtime >= cutoff:
                            meta = extract_metadata(full_p, "AA1")
                            indexed_files.append(meta)
                    except Exception:
                        pass

    # 3. Brain Artifacts (top-level .md only in each conv dir)
    if os.path.exists(BRAIN_ROOT):
        try:
            for conv_id in os.listdir(BRAIN_ROOT):
                conv_dir = os.path.join(BRAIN_ROOT, conv_id)
                if not os.path.isdir(conv_dir) or conv_id.startswith("."):
                    continue
                # Top level of conv dir only
                for item in os.listdir(conv_dir):
                    if item.endswith(".md") and not item.endswith(".metadata.json"):
                        full_p = os.path.join(conv_dir, item)
                        try:
                            mtime = os.path.getmtime(full_p)
                            if mtime >= cutoff:
                                meta = extract_metadata(full_p, "BRAIN")
                                indexed_files.append(meta)
                        except Exception:
                            pass
        except Exception as e:
            print(f"Brain scan error: {e}")

    # Sort by mtime desc
    indexed_files.sort(key=lambda x: x["mtime"], reverse=True)

    # Compute statistics
    kind_counts = {"SUBJECT": 0, "INFRASTRUCTURE": 0, "PROVENANCE": 0}
    root_counts = {"PROJECT": 0, "AA1": 0, "BRAIN": 0}
    total_words = 0
    scripture_counter: Dict[str, int] = {}
    source_counter: Dict[str, int] = {}

    for doc in indexed_files:
        k = doc.get("kind", "SUBJECT")
        r = doc.get("root", "PROJECT")
        kind_counts[k] = kind_counts.get(k, 0) + 1
        root_counts[r] = root_counts.get(r, 0) + 1
        total_words += doc.get("word_count", 0)

        for s in doc.get("scripture_refs", []):
            scripture_counter[s] = scripture_counter.get(s, 0) + 1
        for sh in doc.get("source_hits", []):
            source_counter[sh] = source_counter.get(sh, 0) + 1

    top_scriptures = sorted(scripture_counter.items(), key=lambda x: -x[1])[:20]
    top_sources = sorted(source_counter.items(), key=lambda x: -x[1])[:20]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(indexed_files),
        "total_words": total_words,
        "counts_by_kind": kind_counts,
        "counts_by_root": root_counts,
        "top_scriptures": top_scriptures,
        "top_sources": top_sources,
        "files": indexed_files
    }

    # Atomic write to disk
    tmp_path = OUTPUT_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, OUTPUT_FILE)
    print(f"Indexed {len(indexed_files)} files to {OUTPUT_FILE}")
    return result

if __name__ == "__main__":
    t0 = time.time()
    res = run_indexer()
    dt = time.time() - t0
    print(f"Completed indexing in {dt:.2f}s:")
    print(f"  Total files: {res['total_files']}")
    print(f"  Total words: {res['total_words']:,}")
    print(f"  By Kind: {res['counts_by_kind']}")
    print(f"  By Root: {res['counts_by_root']}")
