"""
Catalog every file Antigravity wrote, from its own logs (Claude GUI, Opus 5.5, 2026-10-13).

    python tools\\ag_output_catalog.py

Why from the logs and not from the disk: a folder listing can tell you a file is new, not who made it or why.
AG's transcripts record every write it made (write_to_file / replace_file_content targets, and the
"Created file file:///..." lines its tools print), with the session and the request that caused it.

Each file gets: the AG sessions that wrote it, first and last write time, the request James had made just before
the first write, whether it still exists, its size and word count, a kind (book / dissertation / dossier / report /
plan / code / control / other) and whether it is dissertation SUBJECT or project INFRASTRUCTURE (Rule 13).

Read-only on AG's backup and on every file it lists. Writes data\\ag_output_catalog.json and
<project>\\02_CONTROL_AND_STATE\\_AG_OUTPUT_CATALOG.md.
"""
import datetime
import glob
import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
import re
import sys
import urllib.parse

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.abspath(os.path.join(BASE, "..", ".."))
AG_BRAIN = r"C:\Users\Elation\AG_HISTORY_BACKUP\brain"
OUT_JSON = os.path.join(BASE, "data", "ag_output_catalog.json")
# The day James first asked for "natural language" prose (Claude session 24fcff95, 2026-09-21 10:18 UTC: "figuring out how
# to make you sound more natural language without information loss"; Antigravity 0d003160 the next day: "wheres the
# natural language exposition"). Found by searching all his Claude, Antigravity and Gemini messages on 2026-10-14.
NATURAL_LANGUAGE_START = "2026-09-21T10:18"
OUT_MD = os.path.join(HERE, "..", "data", "_AG_OUTPUT_CATALOG.md")

CREATED = re.compile(r"(?:Created|Edited|Updated|Wrote|Overwrote) (?:the )?file (file:///[^\s`'\")]+)")
WRITE_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content"}
INFRA_DIRS = ("09_APPS_CATHOLICJARVIS", "02_CONTROL_AND_STATE", "07_ARCHIVE_OLD_PROCESS", "AG_HISTORY_BACKUP",
              "\\.gemini\\", "\\.claude\\", "_SESSION_TRANSCRIPTS", "\\brain\\")
INFRA_WORDS = re.compile(r"(?i)workflow|handoff|session_log|_log_|checkpoint|ocr|benchmark|token|harness|agentic|"
                         r"suite|spec_|implementation|ergonomic|pipeline|subagent_report|task\.md|walkthrough")


def _norm(p):
    if p.startswith("file:///"):
        p = urllib.parse.unquote(p[8:])
    p = p.replace("/", "\\").strip().rstrip(".,;:")
    return os.path.normpath(p)


def _kind(path):
    n = os.path.basename(path).lower()
    ext = os.path.splitext(n)[1]
    if ext in (".py", ".js", ".html", ".css", ".ps1", ".bat", ".pyw", ".ts", ".vbs"):
        return "code"
    if ext in (".json", ".csv", ".tsv", ".jsonl", ".txt") and "dossier" not in n:
        return "data"
    if "\\brain\\" in path.lower() or n in ("task.md", "implementation_plan.md", "walkthrough.md"):
        return "ag-working-note"
    if re.search(r"book|volume|chapter|_ch\d|prologue|epilogue", n) or "\\05_drafts\\book" in path.lower():
        return "book"
    if "dissertation" in n or "01_master_dissertation" in path.lower():
        return "dissertation"
    if re.search(r"dossier|lane_|^[a-z]_|deep_dive|encyclopedia|chronicle|registry|arsenal", n):
        return "dossier"
    if re.search(r"plan|roadmap|spec|blueprint|battleplan|prospectus|curriculum", n):
        return "plan"
    if re.search(r"log|handoff|checkpoint|state|readme|index|manifest", n):
        return "control"
    if re.search(r"report|audit|analysis|synthesis|summary|verification|review", n):
        return "report"
    return "other"


RESEARCH_EXTS = (".md", ".txt", ".docx", ".pdf", ".epub")
RESEARCH_HOMES = (PROJECT.lower(), r"c:\users\elation\mexico_protestantism_study", r"c:\users\elation\desktop",
                  r"c:\users\elation\scholar_decade_plan", r"c:\users\elation\easter")


def _subject(path, kind):
    low = path.lower()
    if kind in ("code", "ag-working-note", "control", "data"):
        return "infrastructure"
    if not low.endswith(RESEARCH_EXTS) or not low.startswith(RESEARCH_HOMES):
        return "infrastructure"
    if os.path.basename(low).startswith("_") and os.path.dirname(low) == PROJECT.lower():
        return "infrastructure"                       # the project's own control files (_RESUME_CORE.md, _GUI_TASK_BRIEF...)
    if os.path.basename(low) in ("claude.md", "gemini.md", "agents.md", "memory.md"):
        return "infrastructure"
    if any(d.lower() in low for d in INFRA_DIRS) or INFRA_WORDS.search(os.path.basename(path)):
        return "infrastructure"
    return "subject"


def _transcript(sdir):
    for n in (os.path.join(".system_generated", "logs", "transcript_full.jsonl"), "transcript_full.jsonl",
              os.path.join(".system_generated", "logs", "transcript.jsonl"), "transcript.jsonl"):
        p = os.path.join(sdir, n)
        if os.path.exists(p):
            return p
    return None


def _args(tc):
    a = tc.get("args") or tc.get("arguments") or {}
    if isinstance(a, str):
        try:
            a = json.loads(a)
        except ValueError:
            a = {}
    return a if isinstance(a, dict) else {}


def _add(files, path, sid, ts, req, desc, writer):
    r = files.setdefault(path.lower(), {"path": path, "sessions": [], "first": ts, "last": ts, "request": req,
                                        "description": desc, "writes": 0, "writers": []})
    r["writes"] += 1
    if sid not in r["sessions"]:
        r["sessions"].append(sid)
    if writer not in r["writers"]:
        r["writers"].append(writer)
    if ts and (not r["first"] or ts < r["first"]):
        r["first"], r["request"] = ts, req or r["request"]
    if ts and (not r["last"] or ts > r["last"]):
        r["last"] = ts
    if not r["description"] and desc:
        r["description"] = desc


CLAUDE_PROJECTS = r"C:\Users\Elation\.claude\projects"


def _james_requests():
    """session id -> [(timestamp, what James asked)], from the main Claude logs (uses hanging_turns' reader, which
    already knows a real message from a tool result, a task notice or a relayed system line)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import hanging_turns
    out = {}
    for p in glob.glob(os.path.join(CLAUDE_PROJECTS, "*", "*.jsonl")):
        try:
            _, turns, _, _ = hanging_turns.claude_session(p)
        except Exception:                                  # noqa: BLE001 - one unreadable log must not stop the catalog
            continue
        # a plain "try again" or the app's "limit has reset" line is not a request: keep the one it was retrying
        out[os.path.splitext(os.path.basename(p))[0]] = [
            (t["ts"], t["text"]) for t in turns
            if t["ts"] and not hanging_turns.CONTINUE.match(t["text"]) and hanging_turns.RESET not in t["text"]]
    return out


def _asked_before(reqs, ts):
    best = ""
    for t, text in reqs:
        if t <= ts:
            best = text
        else:
            break
    return best


def scan_claude(files):
    """Every file a Claude session or Claude subagent wrote with Write (Edit-only files are left out: they existed already).
    For a subagent's file, 'asked for' is what James had last asked the session that launched it, not the agent's brief."""
    asked = _james_requests()
    for p in glob.glob(os.path.join(CLAUDE_PROJECTS, "**", "*.jsonl"), recursive=True):
        sid = os.path.splitext(os.path.basename(p))[0]
        parent = None
        if os.sep + "subagents" + os.sep in p:
            parent = os.path.basename(os.path.dirname(os.path.dirname(p)))
            sid = parent + "/" + sid
        last_req = ""
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"Write"' not in line and '"type":"user"' not in line:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                m = o.get("message") or {}
                c = m.get("content") if isinstance(m, dict) else None
                if o.get("type") == "user" and isinstance(c, str) and not c.lstrip().startswith("<") and not parent:
                    last_req = c
                    continue
                if o.get("type") != "assistant" or not isinstance(c, list):
                    continue
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Write":
                        fp = (b.get("input") or {}).get("file_path")
                        if isinstance(fp, str) and re.match(r"^[A-Za-z]:[\\/]", fp):
                            ts = o.get("timestamp", "")
                            req = _asked_before(asked.get(parent, []), ts) if parent else \
                                (_asked_before(asked.get(sid, []), ts) or last_req)
                            _add(files, os.path.normpath(fp), sid, ts, req, "", "Claude")


def scan():
    files = {}
    for sid in sorted(os.listdir(AG_BRAIN)):
        p = _transcript(os.path.join(AG_BRAIN, sid))
        if not p:
            continue
        last_req = ""
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                ts = o.get("created_at", "")
                typ, content = o.get("type"), o.get("content")
                if typ == "USER_INPUT" and isinstance(content, str):
                    m = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.S)
                    last_req = (m.group(1) if m else content).strip()
                    continue
                targets = []
                tcs = o.get("tool_calls")
                if isinstance(tcs, list):
                    for tc in tcs:
                        if isinstance(tc, dict) and tc.get("name") in WRITE_TOOLS:
                            a = _args(tc)
                            if a.get("TargetFile"):
                                targets.append((a["TargetFile"], tc.get("name"), a.get("Description", "")))
                if typ == "GENERIC" and isinstance(content, str):
                    targets += [(u, "created", "") for u in CREATED.findall(content)]
                for raw, how, desc in targets:
                    path = _norm(raw)
                    if not re.match(r"^[A-Za-z]:\\", path):
                        continue
                    _add(files, path, sid, ts, last_req, desc, "Antigravity")
    scan_claude(files)
    # research files on disk that neither log claims (AG or Claude wrote them through a script, or James did)
    cutoff = datetime.datetime(2026, 9, 1).timestamp()
    for root in (os.path.join(PROJECT, "03_RESEARCH_DOSSIERS"), os.path.join(PROJECT, "05_DRAFTS"),
                 os.path.join(PROJECT, "01_MASTER_DISSERTATION"), r"C:\Users\Elation\Mexico_Protestantism_Study",
                 r"C:\Users\Elation\Scholar_Decade_Plan"):
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if not re.search(r"(?i)_sources|extracted_sources|raw|__pycache__|_backups?", d)]
            for f in fn:
                p = os.path.join(dp, f)
                if f.lower().endswith(RESEARCH_EXTS) and p.lower() not in files:
                    try:
                        mt = os.path.getmtime(p)
                    except OSError:
                        continue
                    if mt >= cutoff:
                        ts = datetime.datetime.fromtimestamp(mt, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                        _add(files, p, "", ts, "", "", "not in any AI log")
    rows = []
    for r in files.values():
        p = r["path"]
        if os.path.isdir(p):
            continue
        r["exists"] = os.path.isfile(p)
        r["bytes"] = os.path.getsize(p) if r["exists"] else 0
        r["words"] = 0
        if r["exists"] and p.lower().endswith((".md", ".txt")) and r["bytes"] < 20_000_000:
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    r["words"] = len(fh.read().split())
            except OSError:
                pass
        r["era"] = ("after natural language" if (r["first"] or "") >= NATURAL_LANGUAGE_START
                     else "before natural language")
        r["kind"] = _kind(p)
        r["side"] = _subject(p, r["kind"])
        r["in_project"] = p.lower().startswith(PROJECT.lower())
        r["rel"] = os.path.relpath(p, PROJECT) if r["in_project"] else p
        rows.append(r)
    rows.sort(key=lambda r: r["last"] or "", reverse=True)
    return rows


def _short(s, n):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n] + " …"


def write_md(rows):
    sub = [r for r in rows if r["side"] == "subject" and r["kind"] not in ("data",)]
    infra = [r for r in rows if r not in sub]
    gone = sum(1 for r in rows if not r["exists"])
    L = ["# Research catalog — every file Antigravity and Claude wrote, newest first", "",
         f"*Made {datetime.datetime.now():%Y-%m-%d %H:%M} by `09_APPS_CATHOLICJARVIS\\catholic_jarvis_suite\\tools\\ag_output_catalog.py` "
         f"from AG's own logs (the backup in `C:\\Users\\Elation\\AG_HISTORY_BACKUP`, which keeps sessions AG has deleted). "
         f"Regenerate rather than edit. The same data is in the work suite: Files → AG Catalog.*", "",
         f"**{len(rows)} files** written by Antigravity: **{len(sub)} research** (books, dossiers, reports, plans about the "
         f"subject) and **{len(infra)} infrastructure** (code, logs, AG's own working notes, data). "
         f"**{gone}** no longer exist at the path AG wrote them to (moved, renamed, or deleted).", "",
         "Words are counted with spaces, so they are a rough size, not a page count.", "",
         "## Research files", ""]
    month = None
    for r in sub:
        m = (r["last"] or "")[:7]
        if m != month:
            L += ["", f"### {m or 'undated'}", "", "| last written | written by | kind | words | file | asked for |", "|---|---|---|---|---|---|"]
            month = m
        name = r["rel"].replace("|", "\\|")
        state = "" if r["exists"] else " **(missing)**"
        who = " + ".join(r["writers"])
        L.append(f"| {r['last'][:10]} | {who} | {r['kind']} | {r['words']:,} | `{name}`{state} | {_short(r['request'], 140).replace('|', '/')} |")
    L += ["", "## Infrastructure files (code, logs, AG working notes, data)", "",
          "| last written | kind | file |", "|---|---|---|"]
    for r in infra:
        state = "" if r["exists"] else " (missing)"
        L.append(f"| {r['last'][:10]} | {r['kind']} | `{r['rel']}`{state} |")
    with open(OUT_MD + ".tmp", "w", encoding="utf-8") as w:
        w.write("\n".join(L) + "\n")
    os.replace(OUT_MD + ".tmp", OUT_MD)


def main():
    rows = scan()
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON + ".tmp", "w", encoding="utf-8") as w:
        json.dump({"made": datetime.datetime.now().isoformat(timespec="seconds"), "rows": rows}, w, ensure_ascii=False, indent=1)
    os.replace(OUT_JSON + ".tmp", OUT_JSON)
    write_md(rows)
    kinds = {}
    for r in rows:
        kinds[(r["side"], r["kind"])] = kinds.get((r["side"], r["kind"]), 0) + 1
    print(f"{len(rows)} files written by Antigravity or Claude (or new on disk); {sum(r['exists'] for r in rows)} still exist")
    for k, v in sorted(kinds.items()):
        print(f"  {k[0]:15} {k[1]:16} {v}")
    print("wrote", OUT_JSON)
    print("wrote", OUT_MD)
    print("AG-CATALOG-END")


if __name__ == "__main__":
    main()
