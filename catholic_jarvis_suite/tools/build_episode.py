"""
tools/build_episode.py  (Task C005, 2026-10-03)

Builds a podcast episode from a script JSON file (data/podcast_scripts/<id>.script.json)
after running the podcast fidelity gate.
REFUSES to render audio if any unreviewed/stale fidelity flags exist against the source document.
Writes <id>.json and <id>.mp3 into data/podcast_episodes/ in the exact schema used by the suite.
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

# Add log analysis directory to import podcast_fidelity_check by path
FIDELITY_CHECK_DIR = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\09_APPS_CATHOLICJARVIS\_LOG_ANALYSIS_2026-10-03"
if FIDELITY_CHECK_DIR not in sys.path:
    sys.path.insert(0, FIDELITY_CHECK_DIR)

import podcast_fidelity_check as fidelity

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(HERE, "data")
PODCAST_DIR = os.path.join(DATA_DIR, "podcast_episodes")
SCRIPTS_DIR = os.path.join(DATA_DIR, "podcast_scripts")
os.makedirs(PODCAST_DIR, exist_ok=True)
os.makedirs(SCRIPTS_DIR, exist_ok=True)


def load_script(script_path: str) -> dict:
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script file not found: {script_path}")
    with open(script_path, "r", encoding="utf-8") as f:
        raw_content = f.read()
    clean_content = re.sub(r'<!--\s*WORKER COMPLETE:.*?-->', '', raw_content).strip()
    clean_content = re.sub(r'^TESTS:\s*.*$', '', clean_content, flags=re.M).strip()
    return json.loads(clean_content)


def run_gate(script: dict, script_path: str) -> tuple[bool, list, list, list, dict]:
    """
    Run fidelity check against the script's source_path and any associated reviewed json.
    Returns (passed, kept_flags, cleared_flags, stale_reviews, ok_map).
    """
    source_path = script.get("source_path")
    if not source_path or not os.path.exists(source_path):
        raise FileNotFoundError(f"Source document not found: {source_path}")

    with open(source_path, "r", encoding="utf-8", errors="replace") as f:
        book_text = f.read()

    turns = script.get("turns", [])
    nc, raw_flags = fidelity.check(turns, book_text)

    # Check for reviews file
    base_id = script.get("id") or os.path.splitext(os.path.basename(script_path))[0].replace(".script", "")
    rev_path = os.path.join(PODCAST_DIR, f"{base_id}.fidelity_reviewed.json")
    reviews = []
    if os.path.exists(rev_path):
        try:
            with open(rev_path, "r", encoding="utf-8") as f:
                reviews = json.load(f)
        except Exception:
            reviews = []

    kept, cleared, stale, ok = fidelity.apply_reviews(raw_flags, turns, reviews)
    passed = (len(kept) == 0 and len(stale) == 0)
    return passed, kept, cleared, stale, ok


async def synthesize_line_edge_tts(item: dict) -> bytes:
    import edge_tts
    text = item["text"]
    voice = item.get("voice", "en-US-AvaNeural")
    rate = item.get("rate", "+0%")
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    stream = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            stream.write(chunk["data"])
    return stream.getvalue()


async def render_episode_audio(script: dict, audio_out: str, manifest_out: str, mock_tts=False):
    turns = script.get("turns", [])
    combined_audio = io.BytesIO()
    transcript_manifest = []
    current_time_offset = 0.0
    total_lines = len(turns)

    for i, item in enumerate(turns):
        speaker = item.get("speaker", "Speaker")
        text = item.get("text", "")
        words_count = len(text.split())
        est_duration = round(max(1.8, words_count / 2.65), 2)

        if mock_tts:
            line_bytes = b"MOCK_AUDIO_FRAME_" + str(i).encode()
        else:
            line_bytes = await synthesize_line_edge_tts(item)

        combined_audio.write(line_bytes)
        start_time = round(current_time_offset, 2)
        end_time = round(current_time_offset + est_duration, 2)
        current_time_offset = end_time + 0.35

        transcript_manifest.append({
            "turn_id": item.get("turn_id", i + 1),
            "speaker": speaker,
            "voice": item.get("voice", "en-US-AvaNeural"),
            "start_s": start_time,
            "end_s": end_time,
            "text": text,
            "bytes_size": len(line_bytes)
        })

    total_bytes = combined_audio.tell()
    with open(audio_out, "wb") as f:
        f.write(combined_audio.getvalue())

    total_duration_s = round(current_time_offset, 1)
    base_audio_filename = os.path.basename(audio_out)

    manifest_data = {
        "title": script.get("title", "Podcast Episode"),
        "subtitle": script.get("subtitle", "NotebookLM-Style Audio Overview"),
        "source_document": os.path.basename(script.get("source_path", "")),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_turns": total_lines,
        "total_duration_seconds": total_duration_s,
        "duration_formatted": f"{int(total_duration_s // 60)}:{int(total_duration_s % 60):02d}",
        "audio_file": base_audio_filename,
        "audio_size_bytes": total_bytes,
        "speakers": [
            {"name": k, "voice": v} for k, v in (script.get("speakers") or {}).items()
        ],
        "turns": transcript_manifest
    }

    with open(manifest_out, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    return manifest_data


def build_episode(script_path: str, dry_run=False, mock_tts=False) -> dict:
    script = load_script(script_path)
    base_id = script.get("id") or os.path.splitext(os.path.basename(script_path))[0].replace(".script", "")
    audio_out = os.path.join(PODCAST_DIR, f"{base_id}.mp3")
    manifest_out = os.path.join(PODCAST_DIR, f"{base_id}.json")

    print(f"[Builder] Running fidelity check for episode: {base_id}")
    passed, kept, cleared, stale, ok = run_gate(script, script_path)

    if not passed:
        print(f"[Builder ERROR] Episode '{base_id}' FAILED fidelity check!")
        if stale:
            print(f"  {len(stale)} stale review(s) found (turn text changed since review):")
            for r in stale:
                print(f"    Turn {r.get('turn_id')}: figure {r.get('figure')}")
        if kept:
            print(f"  {len(kept)} unreviewed flag(s) found:")
            for tid, kind, what, sent, line in kept:
                print(f"    Turn {tid} [{kind}] '{what}': {sent[:100]}")
        raise PermissionError(f"Fidelity gate refused audio build for '{base_id}'. Resolve flags or add human review first.")

    print(f"[Builder] Fidelity check PASSED (0 open flags, {len(cleared)} reviewed).")

    if dry_run:
        print("[Builder] Dry-run enabled: skipping audio synthesis.")
        return {"status": "fidelity_passed_dry_run", "id": base_id}

    print(f"[Builder] Rendering episode audio to {audio_out}...")
    manifest = asyncio.run(render_episode_audio(script, audio_out, manifest_out, mock_tts=mock_tts))
    print(f"[Builder SUCCESS] Episode built: {manifest_out}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Build podcast episode from script with fidelity gate")
    parser.add_argument("script", help="Path to script JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Run fidelity gate only without audio synthesis")
    parser.add_argument("--mock-tts", action="store_true", help="Generate mock audio frames (offline test mode)")
    args = parser.parse_args()

    try:
        build_episode(args.script, dry_run=args.dry_run, mock_tts=args.mock_tts)
        return 0
    except PermissionError as e:
        print(f"REFUSAL: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
