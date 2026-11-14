"""Catalog tab API (/api/catalog). Claude GUI, Opus 5.5, 2026-10-13.

Two lists, both built from the AI logs by scripts in tools\\ (read-only on the logs):
  /files     every research file Antigravity or Claude wrote (tools\\ag_output_catalog.py -> data\\ag_output_catalog.json)
  /hanging   every request James made that was left unfinished (tools\\hanging_turns.py -> data\\hanging_turns.json)
  /rebuild   re-runs both scripts once (about a minute); nothing runs in the background.
"""
import csv
import glob
import io
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from modules.paths_config import get_path

router = APIRouter(prefix="/api/catalog", tags=["catalog"])

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
FILES_JSON = os.path.join(DATA, "ag_output_catalog.json")
HANGING_JSON = os.path.join(DATA, "hanging_turns.json")
SCRIPTS = [os.path.join(BASE, "tools", "ag_output_catalog.py"), os.path.join(BASE, "tools", "hanging_turns.py")]
AG_READABLE = os.path.join(get_path("ag_history_backup"), "readable")

# requests that are not work: account and app commands typed into a session that had run out
NOISE = re.compile(r"^\s*(?:/?(?:claude\s+)?log(?:in|out|oit)|--resume|winget\s+upgrade\b.*|test\.?|online back|"
                   r"opus max .*|raise it.*|login|logout)\s*$", re.I)

_lock = threading.Lock()
_state = {"running": False, "started": 0, "finished": 0, "error": ""}


# Per-path (mtime, size)-keyed cache, not a single slot: _load() is called with two different
# files (FILES_JSON, HANGING_JSON) and a single-slot cache would thrash between them every time
# the two routes are hit alternately, defeating the point.
_LOAD_CACHE: dict = {}


def _load(path):
    """ag_output_catalog.json alone is 11.3 MB, and /api/catalog/files re-parsed it from disk on
    every single call (122.6ms measured under tools/stress_suite.py) with no caching at all --
    same bug class as navigator_cache.json and recall's load_corpus_files() fixed elsewhere this
    session."""
    try:
        st = os.stat(path)
        key = (st.st_mtime, st.st_size)
    except OSError:
        return None
    cached = _LOAD_CACHE.get(path)
    if cached is not None and cached[0] == key:
        return cached[1]
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    _LOAD_CACHE[path] = (key, data)
    return data


def _ag_readable(sid):
    hits = glob.glob(os.path.join(AG_READABLE, f"*_{sid[:8]}.md"))
    return hits[0] if hits else ""


FILES_KEEP = ("path", "rel", "writers", "kind", "side", "era", "words", "bytes", "exists", "first", "last", "request",
              "description", "sessions")


def _files_rows(infra):
    d = _load(FILES_JSON)
    if d is None:
        return None, None
    rows = [r for r in d["rows"] if infra or r.get("side") == "subject"]
    return d, [{k: (r.get(k)[:600] if k == "request" and r.get(k) else r.get(k)) for k in FILES_KEEP} for r in rows]


@router.get("/files")
def files(infra: int = 0):
    d, out = _files_rows(infra)
    if d is None:
        raise HTTPException(503, "No catalog yet. Press Rebuild (or run tools\\ag_output_catalog.py).")
    return {"made": d.get("made"), "total": len(d["rows"]), "rows": out}


@router.get("/files/export")
def files_export(infra: int = 0):
    """CSV download of /files -- same filter, same columns, for pulling the AI-output catalog into
    a spreadsheet. Added 2026-11-12, same pattern as /api/recall/export."""
    d, out = _files_rows(infra)
    if d is None:
        raise HTTPException(503, "No catalog yet. Press Rebuild (or run tools\\ag_output_catalog.py).")
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(FILES_KEEP)
    for r in out:
        writer.writerow([(r.get(k) if r.get(k) is not None else "") for k in FILES_KEEP])
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    filename = f"catalog_files_{stamp}.csv"
    return Response(content=buf.getvalue(), media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Catalog-Export-Rows": str(len(out)),
    })


def _portfolio_data():
    """Summarize the SUBJECT-side (Rule 13) research corpus into something James could actually
    hand to a scholarship committee or academic reference as evidence of independent research
    output: total word count, a breakdown by kind and by era, and the largest works by name.
    Infrastructure/provenance files (code, logs, AI working notes) are excluded by construction --
    this is a scholarly portfolio, not a file count."""
    d, rows = _files_rows(infra=0)
    if d is None:
        return None
    existing = [r for r in rows if r.get("exists")]
    total_words = sum(r.get("words") or 0 for r in existing)
    by_kind = {}
    by_era = {}
    for r in existing:
        k = r.get("kind") or "unknown"
        by_kind[k] = by_kind.get(k, 0) + 1
        e = r.get("era") or "undated"
        by_era[e] = by_era.get(e, 0) + (r.get("words") or 0)
    top = sorted(existing, key=lambda r: r.get("words") or 0, reverse=True)[:20]

    def title_of(r):
        name = r["rel"].replace("\\", "/").split("/")[-1]
        name = re.sub(r"\.(md|txt|docx?)$", "", name, flags=re.I)
        return name.replace("_", " ").replace("-", " ").strip()

    return {
        "made": d.get("made"),
        "total_files": len(existing),
        "total_words": total_words,
        "by_kind": by_kind,
        "by_era": by_era,
        "top_works": [{"title": title_of(r), "rel": r["rel"], "kind": r.get("kind"), "words": r.get("words") or 0,
                        "last": r.get("last")} for r in top],
    }


@router.get("/portfolio")
def portfolio():
    """JSON summary of the subject-side research corpus (see _portfolio_data). Added 2026-11-12
    for James's scholarship/academic-credibility push -- a structured view of independent
    research output, not just a file count."""
    data = _portfolio_data()
    if data is None:
        raise HTTPException(503, "No catalog yet. Press Rebuild (or run tools\\ag_output_catalog.py).")
    return data


@router.get("/portfolio/export")
def portfolio_export():
    """The same summary as a plain-English Markdown document, formatted to be attachable to a
    scholarship application, grant letter, or academic CV as evidence of sustained independent
    research -- word counts and a dated list of the largest completed works, not raw file paths."""
    data = _portfolio_data()
    if data is None:
        raise HTTPException(503, "No catalog yet. Press Rebuild (or run tools\\ag_output_catalog.py).")
    stamp_human = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# Independent Research Portfolio",
        "",
        f"Generated {stamp_human} from the author's own research corpus "
        f"(catalog last rebuilt {str(data.get('made') or '?')[:16].replace('T', ' ')} UTC).",
        "",
        f"**Total independent research output:** {data['total_words']:,} words across {data['total_files']} completed works.",
        "",
        "## Breakdown by kind",
        "",
    ]
    for k, n in sorted(data["by_kind"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- {k}: {n} works")
    lines += ["", "## Output over time (words written, by period)", ""]
    for era, words in sorted(data["by_era"].items()):
        lines.append(f"- {era}: {words:,} words")
    lines += ["", "## Largest completed works", ""]
    for w in data["top_works"]:
        date = (w.get("last") or "")[:10]
        lines.append(f"- **{w['title']}** ({w['kind']}, {w['words']:,} words, {date})")
    content = "\n".join(lines) + "\n"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Response(content=content, media_type="text/markdown; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="research_portfolio_{stamp}.md"',
    })


RIGOR_KINDS = ("dossier", "dissertation", "report")
_TAG_RX = re.compile(r"(?<![\w\[])\[(V|R|S)\](?![\w\]])")
_CODE_SPAN_RX = re.compile(r"```.*?```|`[^`\n]*`", re.S)
_LEGEND_LINE_RX = re.compile(r"^.*\*\*Legend:?\*\*.*$", re.I | re.M)
_TAG_CACHE: dict = {}  # path -> ((mtime, size), {"V": n, "R": n, "S": n})


def _count_tags_in_file(path):
    """Rule 2 of this project's own Charter requires every claim be tagged [V]/[R]/[S] -- this
    counts them per file as a visible rigor metric. Rule 14 (a checker must skip quoted/code
    spans) applies here too: a dossier that quotes CLAUDE.md's own Rule 2 legend ("[V] = ...")
    would otherwise inflate its own tag count by citing the RULE about tags, not making a tagged
    claim -- so code spans and any line containing the literal word "Legend" are stripped first."""
    try:
        st = os.stat(path)
        key = (st.st_mtime, st.st_size)
    except OSError:
        return {"V": 0, "R": 0, "S": 0}
    cached = _TAG_CACHE.get(path)
    if cached is not None and cached[0] == key:
        return cached[1]
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return {"V": 0, "R": 0, "S": 0}
    text = _CODE_SPAN_RX.sub(" ", text)
    text = _LEGEND_LINE_RX.sub("", text)
    counts = {"V": 0, "R": 0, "S": 0}
    for m in _TAG_RX.finditer(text):
        counts[m.group(1)] += 1
    _TAG_CACHE[path] = (key, counts)
    return counts


@router.get("/rigor")
def rigor():
    """Aggregate [V]/[R]/[S] citation-tier counts across every existing dossier/dissertation/
    report in the subject-side corpus -- a quantitative rigor metric a scholarly reader can
    check (what fraction of this corpus's claims are independently verified vs. unsourced),
    added 2026-11-12 under James's "more impressive to scientists/scholars" goal. Per-file
    results are cached by (mtime, size), so a rebuild only re-scans files that actually changed."""
    d, rows = _files_rows(infra=0)
    if d is None:
        raise HTTPException(503, "No catalog yet. Press Rebuild (or run tools\\ag_output_catalog.py).")
    targets = [r for r in rows if r.get("exists") and r.get("kind") in RIGOR_KINDS]
    totals = {"V": 0, "R": 0, "S": 0}
    per_file = []
    for r in targets:
        c = _count_tags_in_file(r["path"])
        tagged = c["V"] + c["R"] + c["S"]
        if tagged == 0:
            continue
        for k in totals:
            totals[k] += c[k]
        per_file.append({"rel": r["rel"], "kind": r["kind"], "V": c["V"], "R": c["R"], "S": c["S"], "tagged": tagged})
    total_tagged = sum(totals.values())
    per_file.sort(key=lambda x: x["tagged"], reverse=True)
    return {
        "made": d.get("made"),
        "files_scanned": len(targets),
        "files_with_tags": len(per_file),
        "totals": totals,
        "verified_rate": round(100 * totals["V"] / total_tagged, 1) if total_tagged else None,
        "sourced_rate": round(100 * (totals["V"] + totals["R"]) / total_tagged, 1) if total_tagged else None,
        "top_files": per_file[:20],
    }


def _title_of_rel(rel):
    name = rel.replace("\\", "/").split("/")[-1]
    name = re.sub(r"\.(md|txt|docx?)$", "", name, flags=re.I)
    return name.replace("_", " ").replace("-", " ").strip()


@router.get("/cite")
def cite(rel: str):
    """SBL/Chicago/BibTeX citation for one of James's own subject-side works -- the same three
    formats `manuscripts_core.format_citation()` already generates for manuscript folios,
    generalized to his own dossiers/dissertation/reports/books. Added 2026-11-12 so any piece of
    independent research in the Catalog tab can be dropped into a reference manager (Zotero,
    EndNote, BibTeX) exactly as a scholarship committee or academic reviewer would expect.
    Author is left as a bracketed placeholder -- this project has never been told James's legal
    surname, and a citation tool that guesses one is worse than one that is honest it doesn't
    know."""
    d, rows = _files_rows(infra=1)
    if d is None:
        raise HTTPException(503, "No catalog yet. Press Rebuild (or run tools\\ag_output_catalog.py).")
    row = next((r for r in rows if r["rel"] == rel), None)
    if row is None:
        raise HTTPException(404, "no catalog row with that rel path")
    title = _title_of_rel(rel)
    year = (row.get("last") or row.get("first") or "")[:4] or "n.d."
    author_placeholder = "[Author Surname, First Name]"
    kind_label = {"dossier": "research dossier", "dissertation": "dissertation draft",
                  "report": "research report", "book": "manuscript"}.get(row.get("kind"), "manuscript")
    sbl = f"{author_placeholder}, \"{title}\" (unpublished {kind_label}, {year})."
    chicago = f"{author_placeholder}. \"{title}.\" Unpublished {kind_label}, {year}."
    key = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")[:40] or "untitled"
    bibtex = (f"@unpublished{{{key}_{year},\n"
              f"  author = {{{author_placeholder}}},\n"
              f"  title = {{{{{title}}}}},\n"
              f"  note = {{Unpublished {kind_label}, {row.get('words') or 0} words}},\n"
              f"  year = {{{year}}}\n"
              f"}}")
    return {"title": title, "year": year, "kind": row.get("kind"), "words": row.get("words") or 0,
            "sbl": sbl, "chicago": chicago, "bibtex": bibtex}


@router.get("/hanging")
def hanging(noise: int = 0):
    d = _load(HANGING_JSON)
    if d is None:
        raise HTTPException(503, "No list yet. Press Rebuild (or run tools\\hanging_turns.py).")
    out = []
    for r in d["rows"]:
        is_noise = bool(NOISE.match(r.get("request") or ""))
        if is_noise and not noise:
            continue
        x = dict(r, noise=is_noise, request=(r.get("request") or "")[:3000], last_answer=(r.get("last_answer") or "")[:1500])
        if r.get("source") == "Antigravity":
            x["readable"] = _ag_readable(r.get("session", ""))
        out.append(x)
    return {"made": d.get("made"), "claude_logs": d.get("claude_logs"), "ag_sessions": d.get("ag_sessions"), "rows": out}


def _run():
    try:
        for s in SCRIPTS:
            p = subprocess.run([sys.executable, s], capture_output=True, text=True, timeout=900, cwd=BASE)
            if p.returncode != 0:
                _state["error"] = f"{os.path.basename(s)} failed: {(p.stderr or p.stdout)[-400:]}"
                break
        else:
            _state["error"] = ""
    except Exception as e:                       # noqa: BLE001 - reported to the page, not swallowed
        _state["error"] = str(e)
    finally:
        _state["running"], _state["finished"] = False, time.time()


@router.post("/rebuild")
def rebuild():
    with _lock:
        if _state["running"]:
            return dict(_state, already=True)
        _state.update(running=True, started=time.time(), error="")
    threading.Thread(target=_run, daemon=True).start()
    return dict(_state)


@router.get("/rebuild")
def rebuild_status():
    return dict(_state)
