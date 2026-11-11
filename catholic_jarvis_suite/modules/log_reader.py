"""
Shared, read-only reader for James's AI conversation logs (Claude Code + Antigravity).
Owned by the integrator (Claude GUI). Workers IMPORT this; they do not edit it.

  from modules.log_reader import load_messages, load_sessions
  msgs = load_messages()      # list of dicts, chronological
  # each: {"ts", "surface": "CL"|"AG", "sid", "role": "user"|"assistant", "text", "file"}

Sources (both read in binary, line by line; nothing is ever written to them):
  Claude:      C:\\Users\\Elation\\.claude\\projects\\**\\*.jsonl   (subagent transcripts skipped)
  Antigravity: C:\\Users\\Elation\\.gemini\\antigravity\\brain\\<id>\\.system_generated\\logs\\transcript_full.jsonl

Harness noise (slash-command echoes, interrupts, task notifications, compaction summaries,
system reminders) is dropped from the user side, the same filters used for the 2026-10-03 log
analysis (COVERAGE.json there proved byte-complete reading).

Antigravity prunes its own live `brain\\` folder (oldest conversations past ~515 are deleted
with no recycle bin -- see memory note ag-history-rolling-cap), so the live folder alone
undercounts real history. 2026-11-11: found 623 AG sessions existed ONLY in
AG_HISTORY_BACKUP\\readable\\*.md (a human-readable per-session export,
`backup_ag_history.py`'s own output) and nowhere live -- more than the 503 sessions still
live. load_messages() now also reads any backup .md whose session id isn't covered by a live
transcript, so pruned-but-backed-up conversations stay visible to Debate/Recall/Today instead
of silently disappearing. Timestamps recovered this way are minute-precision only (the backup
format doesn't keep seconds/timezone), good enough for chronological sort and "how long ago."

Cache: data/_log_cache.json, keyed by (path, size, mtime) of every source file, so a changed
or new log invalidates only by fingerprint mismatch -> full rebuild (simple and correct).
"""
import glob
import hashlib
import json
import os
import re

from modules.paths_config import get_path

CL_ROOT = get_path("claude_projects")
AG_ROOT = get_path("gemini_antigravity_brain")
AG_BACKUP_READABLE = os.path.join(get_path("ag_history_backup"), "readable")
_SUB = os.sep + "subagents" + os.sep
_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(_HERE, "data", "_log_cache.json")

_BACKUP_FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_([0-9a-f]+)\.md$")
_BACKUP_HEADER_RE = re.compile(r"^\*\*(James|Antigravity)\*\* . (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})$", re.M)
_BACKUP_TITLE_RE = re.compile(r"^# Antigravity session ([0-9a-f-]+)", re.M)

_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
_HARNESS = ("<command-", "<local-command", "Caveat: The messages below", "[Request interrupted",
            "<task-notification>", "This session is being continued from a previous conversation",
            "<bash-", "<user-memory-input>")


def _sources():
    cl = [f for f in glob.glob(os.path.join(CL_ROOT, "**", "*.jsonl"), recursive=True) if _SUB not in f]
    ag = glob.glob(os.path.join(AG_ROOT, "*", ".system_generated", "logs", "transcript_full.jsonl"))
    live_sids = {f.split(os.sep)[-4] for f in ag}
    ag_backup = []
    for f in glob.glob(os.path.join(AG_BACKUP_READABLE, "*.md")):
        m = _BACKUP_FILENAME_RE.match(os.path.basename(f))
        if not m:
            continue
        short_sid = m.group(1)
        if any(sid.startswith(short_sid) for sid in live_sids):
            continue  # this session is also live -- the live transcript is the fuller source
        ag_backup.append(f)
    return sorted(cl), sorted(ag), sorted(ag_backup)


def _fingerprint(files):
    h = hashlib.sha1()
    for f in files:
        try:
            st = os.stat(f)
            h.update(f"{f}|{st.st_size}|{int(st.st_mtime)}\n".encode("utf-8"))
        except OSError:
            pass
    return h.hexdigest()


def _claude(f, out):
    sid = os.path.basename(f)[:-6]
    with open(f, "rb") as fh:
        for raw in fh:
            try:
                d = json.loads(raw)
            except Exception:
                continue
            m = d.get("message") if isinstance(d.get("message"), dict) else None
            if not m:
                continue
            ts, t = d.get("timestamp") or "", d.get("type")
            if t == "assistant":
                txt = "\n".join(b.get("text", "") for b in (m.get("content") or [])
                                if isinstance(b, dict) and b.get("type") == "text").strip()
                if txt:
                    out.append({"ts": ts, "surface": "CL", "sid": sid, "role": "assistant", "text": txt, "file": f})
            elif t == "user" and m.get("role") == "user":
                if d.get("isMeta") or d.get("isSidechain") or d.get("isCompactSummary"):
                    continue
                c = m.get("content")
                if isinstance(c, str):
                    txt = c
                elif isinstance(c, list):
                    txt = "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
                else:
                    continue
                if not txt or txt.lstrip().startswith(_HARNESS):
                    continue
                txt = _REMINDER.sub("", txt).strip()
                if txt:
                    out.append({"ts": ts, "surface": "CL", "sid": sid, "role": "user", "text": txt, "file": f})


def _antigravity(f, out):
    sid = f.split(os.sep)[-4]
    with open(f, "rb") as fh:
        for raw in fh:
            try:
                d = json.loads(raw)
            except Exception:
                continue
            ts, src, ty = d.get("created_at") or "", d.get("source"), d.get("type")
            if src == "USER_EXPLICIT" and ty == "USER_INPUT":
                txt = (d.get("content") or "").strip()
                txt = re.sub(r"^<USER_REQUEST>\s*|\s*</USER_REQUEST>.*$", "", txt, flags=re.S).strip() or txt
                if txt:
                    out.append({"ts": ts, "surface": "AG", "sid": sid, "role": "user", "text": txt, "file": f})
            elif src == "MODEL" and ty == "PLANNER_RESPONSE":
                txt = (d.get("content") or "").strip()
                if txt:
                    out.append({"ts": ts, "surface": "AG", "sid": sid, "role": "assistant", "text": txt, "file": f})


def _antigravity_backup(f, out):
    """Parses a backup_ag_history.py readable export for a session that's been pruned from the
    live brain\\ folder (or never had a live transcript at all). Format ground-truthed directly
    against an actual file, not assumed: an H1 title line carrying the full session UUID, then
    repeating **Speaker** . YYYY-MM-DD HH:MM blocks (speaker is "James" or "Antigravity"; "." is
    the literal middle-dot the export writes, matched by regex as any single char) each followed
    by that turn's text, separated by horizontal rules. Timestamps are minute-precision only, so
    the recovered "ts" sorts correctly against full-precision ISO timestamps from the live
    sources but can't be compared at second granularity within the same minute.
    """
    with open(f, encoding="utf-8") as fh:
        text = fh.read()
    tm = _BACKUP_TITLE_RE.search(text)
    sid = tm.group(1) if tm else _BACKUP_FILENAME_RE.match(os.path.basename(f)).group(1)
    matches = list(_BACKUP_HEADER_RE.finditer(text))
    for i, hm in enumerate(matches):
        speaker, date, hhmm = hm.group(1), hm.group(2), hm.group(3)
        start = hm.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body.endswith("---"):
            body = body[:-3].strip()
        if not body:
            continue
        role = "user" if speaker == "James" else "assistant"
        if role == "user":
            if body.lstrip().startswith(_HARNESS):
                continue
            body = _REMINDER.sub("", body).strip()
            if not body:
                continue
        out.append({"ts": f"{date}T{hhmm}:00", "surface": "AG", "sid": sid, "role": role, "text": body, "file": f})


def load_messages(use_cache=True):
    """Every user and assistant text message from both surfaces, sorted by timestamp.
    Replayed user prompts (resume/fork) longer than 40 chars are de-duplicated by content."""
    cl, ag, ag_backup = _sources()
    fp = _fingerprint(cl + ag + ag_backup)
    if use_cache and os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as fh:
                c = json.load(fh)
            if c.get("fingerprint") == fp:
                return c["messages"]
        except Exception:
            pass
    out = []
    for f in cl:
        _claude(f, out)
    for f in ag:
        _antigravity(f, out)
    for f in ag_backup:
        _antigravity_backup(f, out)
    out.sort(key=lambda m: m["ts"])
    seen, dedup = set(), []
    for m in out:
        if m["role"] == "user" and len(m["text"]) > 40:
            h = hashlib.sha1(m["text"].encode("utf-8", "replace")).hexdigest()
            if h in seen:
                continue
            seen.add(h)
        dedup.append(m)
    tmp = CACHE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as w:
        json.dump({"fingerprint": fp, "messages": dedup}, w, ensure_ascii=False)
    os.replace(tmp, CACHE)
    return dedup


def load_sessions(messages=None):
    """Per-session summary: surface, sid, first/last ts, user/assistant message counts, first user prompt, file."""
    msgs = messages if messages is not None else load_messages()
    S = {}
    for m in msgs:
        k = (m["surface"], m["sid"])
        s = S.setdefault(k, {"surface": m["surface"], "sid": m["sid"], "first": m["ts"], "last": m["ts"],
                             "n_user": 0, "n_assistant": 0, "first_prompt": "", "file": m["file"]})
        s["first"] = min(s["first"] or m["ts"], m["ts"]) if m["ts"] else s["first"]
        s["last"] = max(s["last"] or m["ts"], m["ts"])
        if m["role"] == "user":
            s["n_user"] += 1
            if not s["first_prompt"]:
                s["first_prompt"] = m["text"][:300]
        else:
            s["n_assistant"] += 1
    return sorted(S.values(), key=lambda s: s["last"] or "", reverse=True)


if __name__ == "__main__":
    import sys
    import time
    t0 = time.time()
    ms = load_messages(use_cache="--rebuild" not in sys.argv)
    ss = load_sessions(ms)
    u = sum(1 for m in ms if m["role"] == "user")
    print(f"messages {len(ms)} (user {u}), sessions {len(ss)} "
          f"(CL {sum(1 for s in ss if s['surface'] == 'CL')}, AG {sum(1 for s in ss if s['surface'] == 'AG')}), "
          f"{time.time() - t0:.1f}s")
