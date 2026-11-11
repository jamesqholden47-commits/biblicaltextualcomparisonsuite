"""
AI Session Intelligence & Breakthrough Navigator
Indexes all historical research sessions across Antigravity brain logs,
Claude transcripts, and Gemini exports.
Extracts timestamps, core topics, theological breakthroughs, and artifact links.
Allows rapid navigation of 500+ sessions without context bloat or token exhaustion.
"""

import os
import io
import re
import sys
import json
import time
from collections import defaultdict
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

BRAIN_DIR = r"C:\Users\Elation\.gemini\antigravity\brain"
PROJECT_TRANSCRIPTS_DIR = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\06_SOURCE_MATERIAL\_SESSION_TRANSCRIPTS"
PROJECT_LOGS_DIR = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\02_CONTROL_AND_STATE\_SESSION_LOGS"

OUTPUT_JSON = os.path.join(DATA_DIR, "ai_session_index.json")
OUTPUT_MD = os.path.join(DATA_DIR, "ai_session_index.md")

TOPIC_KEYWORDS = [
    "nasrani", "malabar", "diamper", "chandy", "hishtachavah", "1 chron 29:20",
    "bowing", "nicaea", "elvira", "statue", "icon", "gold streets", "rev 21",
    "hormisdas", "acacian", "primacy", "asar", "keys", "dikaio", "justification",
    "sprinkling", "affusion", "baptism", "purgatory", "incense", "thurificati",
    "kiss of peace", "dura", "qumran", "didache", "augustine", "aquinas", "wallace",
    "john 1:1", "anki", "monetiz", "career", "substack", "popes", "marriage"
]

# Keywords that are deliberately STEMS (Greek/Latin word families): matched as a word PREFIX,
# so "dikaiosyne" counts for "dikaio". Every other keyword is matched as a WHOLE WORD
# (optionally with a plural -s/-es), so "dura" no longer matches "duration" or "endure".
STEM_KEYWORDS = {"dikaio", "monetiz", "thurificati"}

# Word boundaries that treat "_" as a separator (so file names like anki_cards.json or
# dura_europos.md still count) but letters/digits as word characters.
_LB = r"(?<![^\W_])"
_RB = r"(?![^\W_])"

def _build_topic_patterns():
    pats = []
    for kw in TOPIC_KEYWORDS:
        body = re.escape(kw).replace(r"\ ", r"\s+")
        if kw in STEM_KEYWORDS:
            rx = _LB + body + r"[^\W_]*"
        else:
            rx = _LB + body + r"(?:s|es)?" + _RB
        pats.append((kw, re.compile(rx, re.I)))
    return pats

_TOPIC_PATTERNS = _build_topic_patterns()
_PREFILTER = {kw: max(kw.split(), key=len) for kw in TOPIC_KEYWORDS}

def match_topics(text: str, hits: Optional[set] = None) -> set:
    """Whole-word topic tagging. `hits` is updated in place (and returned) so callers can
    accumulate over many lines; keywords already in `hits` are skipped."""
    if hits is None:
        hits = set()
    lo = text.lower()
    for kw, rx in _TOPIC_PATTERNS:
        if kw in hits:
            continue
        # cheap substring prefilter (the whole-word regex runs only where the substring occurs)
        if _PREFILTER[kw] in lo and rx.search(text):
            hits.add(kw)
    return hits

def analyze_brain_session(conv_id: str, conv_dir: str) -> Optional[Dict[str, Any]]:
    # 1. Check for artifacts
    artifacts = []
    try:
        for f in os.listdir(conv_dir):
            if f.endswith(".md") and not f.endswith(".metadata.json"):
                full_p = os.path.join(conv_dir, f)
                artifacts.append({
                    "name": f,
                    "path": full_p,
                    "size": os.path.getsize(full_p)
                })
    except Exception:
        pass

    # 2. Inspect transcript.jsonl
    transcript_file = os.path.join(conv_dir, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(transcript_file):
        return None

    try:
        mtime = os.path.getmtime(transcript_file)
        mtime_iso = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except Exception:
        mtime = time.time()
        mtime_iso = ""

    first_prompt = ""
    turns_count = 0
    words_total = 0
    topic_hits = set()

    try:
        with open(transcript_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.strip():
                    continue
                turns_count += 1
                try:
                    step = json.loads(line)
                    content = str(step.get("content", ""))
                    words_total += len(content.split())
                    match_topics(content, topic_hits)

                    if not first_prompt and step.get("type") == "USER_INPUT":
                        first_prompt = content[:250].strip().replace("\n", " ")
                except Exception:
                    pass
    except Exception:
        pass

    if turns_count == 0 and not artifacts:
        return None

    title = ""
    if artifacts:
        title = artifacts[0]["name"].replace(".md", "").replace("_", " ")
    elif first_prompt:
        title = first_prompt[:60] + "..."
    else:
        title = f"Antigravity Session {conv_id[:8]}"

    return {
        "id": conv_id,
        "platform": "Antigravity",
        "title": title,
        "mtime": mtime,
        "mtime_iso": mtime_iso,
        "first_prompt": first_prompt,
        "turns_count": turns_count,
        "approx_words": words_total,
        "artifacts_count": len(artifacts),
        "artifacts": artifacts,
        "topics": sorted(list(topic_hits)),
        "transcript_path": transcript_file
    }

def analyze_claude_transcript(file_path: str) -> Optional[Dict[str, Any]]:
    fname = os.path.basename(file_path)
    try:
        st = os.stat(file_path)
        mtime = st.st_mtime
        mtime_iso = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except Exception:
        return None

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        content = ""

    words_total = len(content.split())
    lines = content.splitlines()

    title = fname.replace(".md", "").replace("_", " ")
    for line in lines[:20]:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break

    topic_hits = sorted(match_topics(content))

    return {
        "id": fname,
        "platform": "Claude Transcript",
        "title": title,
        "mtime": mtime,
        "mtime_iso": mtime_iso,
        "first_prompt": lines[0][:200] if lines else "",
        "turns_count": len([l for l in lines if l.startswith("## Turn") or l.startswith("###")]),
        "approx_words": words_total,
        "artifacts_count": 0,
        "artifacts": [],
        "topics": topic_hits,
        "transcript_path": file_path
    }

def _iso_to_epoch(ts: str) -> float:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0

def analyze_claude_sessions(messages: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """One index entry for EVERY Claude session that modules.log_reader.load_sessions() returns
    (the ~/.claude/projects/**/*.jsonl logs), with topics tagged from the full text of every
    user and assistant message in that session. Keys match the Antigravity entries so that
    GET /api/sessions in app.py reads both kinds the same way."""
    from modules.log_reader import load_messages, load_sessions
    msgs = messages if messages is not None else load_messages()
    cl_msgs = [m for m in msgs if m["surface"] == "CL"]
    words = defaultdict(int)
    topics = defaultdict(set)
    for m in cl_msgs:
        words[m["sid"]] += len(m["text"].split())
        match_topics(m["text"], topics[m["sid"]])
    out = []
    for s in load_sessions(cl_msgs):
        if s["surface"] != "CL":
            continue
        last_ts = s["last"] or s["first"] or ""
        mtime = _iso_to_epoch(last_ts)
        fp = " ".join((s.get("first_prompt") or "").split())
        out.append({
            "id": s["sid"],
            "platform": "Claude Transcript",
            "title": (fp[:60] + ("..." if len(fp) > 60 else "")) if fp else f"Claude Session {s['sid'][:8]}",
            "mtime": mtime,
            "mtime_iso": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat() if mtime else "",
            "first_prompt": fp[:250],
            "turns_count": s["n_user"] + s["n_assistant"],
            "approx_words": words[s["sid"]],
            "artifacts_count": 0,
            "artifacts": [],
            "topics": sorted(topics[s["sid"]]),
            "transcript_path": s["file"],
            "source": "claude_jsonl",
            "first_ts": s["first"],
            "last_ts": s["last"],
        })
    return out

def run_session_indexer(include_exports: bool = False) -> Dict[str, Any]:
    print("[Session Indexer] Scanning Antigravity & Claude sessions...")
    t0 = time.time()
    sessions = []

    # 1. Antigravity Brain Sessions
    if os.path.exists(BRAIN_DIR):
        for cid in os.listdir(BRAIN_DIR):
            cdir = os.path.join(BRAIN_DIR, cid)
            if os.path.isdir(cdir) and not cid.startswith("."):
                sess = analyze_brain_session(cid, cdir)
                if sess:
                    sessions.append(sess)

    # 2. Claude sessions: every ~/.claude/projects/**/*.jsonl session log_reader returns
    sessions.extend(analyze_claude_sessions())

    # 3. (opt-in) the hand-exported markdown transcripts. These were the ONLY Claude source before
    # 2026-10-03; they are exports of sessions already covered by step 2, and the folder holds
    # multi-megabyte raw logs, so they are no longer scanned unless asked (--include-exports).
    if include_exports and os.path.exists(PROJECT_TRANSCRIPTS_DIR):
        for f in os.listdir(PROJECT_TRANSCRIPTS_DIR):
            if f.endswith(".md"):
                full_p = os.path.join(PROJECT_TRANSCRIPTS_DIR, f)
                sess = analyze_claude_transcript(full_p)
                if sess:
                    sessions.append(sess)

    # Sort sessions by mtime descending (newest first)
    sessions.sort(key=lambda s: s["mtime"], reverse=True)

    # Compute global stats
    total_sessions = len(sessions)
    total_turns = sum(s.get("turns_count", 0) for s in sessions)
    total_words = sum(s.get("approx_words", 0) for s in sessions)
    total_artifacts = sum(s.get("artifacts_count", 0) for s in sessions)

    topic_counter = {}
    for s in sessions:
        for top in s.get("topics", []):
            topic_counter[top] = topic_counter.get(top, 0) + 1

    top_topics = sorted(topic_counter.items(), key=lambda x: -x[1])[:25]
    counts_by_platform = {}
    for s in sessions:
        counts_by_platform[s["platform"]] = counts_by_platform.get(s["platform"], 0) + 1

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.time() - t0, 2),
        "total_sessions": total_sessions,
        "total_turns": total_turns,
        "total_words": total_words,
        "total_artifacts": total_artifacts,
        "top_topics": top_topics,
        "all_topic_counts": dict(sorted(topic_counter.items(), key=lambda x: -x[1])),
        "counts_by_platform": counts_by_platform,
        "topic_matching": "whole-word (optional plural); stems: " + ", ".join(sorted(STEM_KEYWORDS)),
        "sessions": sessions
    }

    # Atomic write to JSON
    tmp_json = OUTPUT_JSON + ".tmp"
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    os.replace(tmp_json, OUTPUT_JSON)

    # Markdown Summary
    md_lines = [
        "# 🧠 AI SESSION INTELLIGENCE & BREAKTHROUGH TIMELINE",
        "",
        f"**Generated:** {result['generated_at']} | **Total Sessions Indexed:** {total_sessions:,}",
        f"**Total Dialog Turns:** {total_turns:,} | **Total Conversation Words:** {total_words:,} | **Artifacts Produced:** {total_artifacts:,}",
        "",
        "## 🔥 Top Breakthrough Research Topics",
        "| Topic / Keyword | Session Count |",
        "|---|---:|"
    ]
    for top, cnt in top_topics:
        md_lines.append(f"| **{top}** | {cnt} sessions |")

    md_lines.extend([
        "",
        "---",
        "## 📜 Recent Research Sessions Timeline",
        "| Date | Platform | Title / Core Inquiry | Artifacts | Turns | Top Breakthroughs |",
        "|---|---|---|:---:|---:|---|"
    ])

    for s in sessions[:35]:
        date_str = s["mtime_iso"][:10] if s["mtime_iso"] else "Unknown"
        tops = ", ".join(s.get("topics", [])[:4])
        md_lines.append(f"| {date_str} | `{s['platform']}` | **{s['title'].replace('|', '/')}** | {s['artifacts_count']} | {s['turns_count']} | {tops} |")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"[Session Indexer] Completed in {result['duration_seconds']}s:")
    print(f"  Sessions indexed: {total_sessions:,}  {counts_by_platform}")
    print(f"  Total words: {total_words:,}")
    print(f"  Artifacts: {total_artifacts:,}")
    return result

if __name__ == "__main__":
    run_session_indexer(include_exports="--include-exports" in sys.argv)
