"""
Organizer: every document, book, note and code file in C:\\Users\\Elation, sorted into buckets
(Claude GUI, Opus 5.5, 2026-10-14). Read-only: it sorts the LIST, it never moves a file.

Input: data\\drive_inventory.json (tools\\drive_inventory.py). The rules below decide, for each file:
  bucket    Vault & archives | Books | Dissertation project | Other projects | Loose notes | Saved web pages | Code elsewhere
  shelf     the sub-group inside the bucket (which vault copy, which project, which project folder, which book subject)
  kind      note | document | book | web page | code | data
  dupes     how many other files have the same fingerprint, and where they are

THE RULES, in order (first match wins; each is unit-tested in tests/test_organizer.py):
  1. Vault & archives: the AA1 Obsidian vault; older vault copies (aadesktop, the Downloads AA1 backup, Desktop\\Easy);
     the sorting clone; AI-history backups and Google Takeouts; old sorts and recoveries; and any folder named
     98_Archives, Catacombs, 07_ARCHIVE_OLD_PROCESS, _TIMECAPSULE*, *_ARCHIVE*, Archive(s).
  2. Dissertation project: DXM\\Clippings\\_PROJECT_HistoryProvesCatholicism, shelved by its numbered folder (its
     source PDFs stay with it); the rest of the DXM vault goes to rule 1.
  3. Other projects: a known project folder (Mexico study, Scriptorium, CS2 codex, the warriors sites ...).
  4. Saved web pages: a page saved into the home folder, and everything inside its *_files folder.
  5. Books: any .pdf/.epub/.mobi/.azw/.djvu left, shelved by subject from the title words; James's own papers
     (forms, resume, letters) and saved articles get their own shelves.
  6. Code elsewhere: code not inside a project above.
  7. Loose notes: everything else (Desktop, Downloads, Documents, NOTES ...).
"""
import gc
import json
import os
import re
import threading
import time

from modules.paths_config import get_path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INVENTORY = os.path.join(BASE, "data", "drive_inventory.json")
BOOK_SHELVES = os.path.join(BASE, "data", "book_shelves.json")
PLACEMENTS = os.path.join(BASE, "data", "organizer_placements.json")   # James's virtual filing: path -> folder / hidden
PROGRAM_BUCKET = "Program files (hidden)"
HOME = get_path("home")
PROJECT_REL = r"DXM\Clippings\_PROJECT_HistoryProvesCatholicism"

BOOK_EXT = {".pdf", ".epub", ".mobi", ".azw3", ".azw", ".djvu", ".cbz"}
CODE_EXT = {".py", ".pyw", ".js", ".ts", ".ps1", ".bat", ".cmd", ".sh", ".ipynb", ".css", ".vbs", ".ahk"}
DATA_EXT = {".csv", ".tsv", ".xlsx", ".xls"}
WEB_EXT = {".html", ".htm", ".mhtml"}
NOTE_EXT = {".md", ".txt"}

VAULT_SHELVES = [   # (path prefix relative to HOME, lowercase) -> shelf
    ("aa1\\98_archives", "AA1 vault: 98_Archives"),
    ("aa1", "AA1 Obsidian vault (the live one)"),
    ("aadesktop", "Older vault copy: aadesktop"),
    ("downloads\\obsidian_vaults_backup_contingency", "Older vault copy: Downloads vault backup"),
    ("desktop\\vault_review_2026-10-08", "Vault review folder (notes moved off the vault)"),
    ("desktop\\easy", "Older vault copy: Desktop Easy"),
    ("clone_for_sorting_2026-10-08__copies_not_originals", "Sorting clone (copies, safe to delete)"),
    ("ag_history_backup", "AI history: Antigravity backup"),
    ("takeout", "AI history: Google Takeout"),
    ("easter\\gemini_takeout_temp", "AI history: Google Takeout"),
    ("sarahai_grok_handover", "AI history: Grok handover"),
    ("_sorted_2026-07-22", "Old sorts and recoveries"),
    ("bravetabrecovery", "Old sorts and recoveries"),
    ("extraction_results", "Old sorts and recoveries"),
    ("archives_and_installers", "Old sorts and recoveries"),
    ("desktop\\ag_pre_dissertation_archive", "Project archives"),
    ("documents\\_timecapsule", "Project archives"),
]
ARCHIVE_DIR = re.compile(r"\\(98_archives|catacombs|07_archive_old_process|_timecapsule[^\\]*|[^\\]*_archive[^\\]*|archives?)\\", re.I)

PROJECTS = [        # (path prefix relative to HOME, lowercase) -> project name
    ("mexico_protestantism_study", "Mexico Protestantism study"),
    ("scholar_decade_plan", "The Ten-Year Scriptorium"),
    ("desktop\\scholar_decade_plan", "The Ten-Year Scriptorium (Desktop copy)"),
    ("cs2_dust2_codex", "CS2 Dust2 Codex"),
    ("q_corpus_analysis", "Q corpus analysis"),
    ("cannabis_moral_theology", "Cannabis moral theology"),
    ("canoncouncil", "Canon council"),
    ("canon-wiki-fixed", "Canon wiki"),
    ("catenastudio", "Catena studio"),
    ("pope-leo-hub", "Pope Leo hub"),
    ("warriors-", "Warriors business sites"),
    ("theological_thread", "Theological thread"),
    ("desktop\\natural_language_catholic_book_project", "Natural-language Catholic book (Desktop)"),
    ("desktop\\synthesized_volume_sandbox", "Synthesized volume sandbox (Desktop)"),
    ("desktop\\hardfactscholar_geminipack", "HardFactScholar Gemini pack (Desktop)"),
    ("desktop\\talents_research_export", "Talents research export (Desktop)"),
    ("voiceperf", "Voice tests"),
    ("face-detection-laser-system", "Face detection project"),
    ("fitness", "Fitness"),
    ("sarahai_public_tent_door_plan", "SarahAI"),
    ("harness-engineering", "Harness engineering"),
    ("rvbbit", "rvbbit"),
    ("perlego-download", "Perlego downloader"),
    ("fl-database", "Forgotten Languages database"),
    ("grok_deepresearch_sandbox", "Grok deep research"),
    ("master\\", "Master research parts"),
    ("easter\\", "Easter (Antigravity workspace vault)"),
    ("academia", "Academia vault"),
    ("source\\repos", "Code repositories"),
    ("mcps", "MCP servers"),
]
PROJECT_FOLDERS = {
    "01_master_dissertation": "Master dissertation", "02_control_and_state": "Control and state (project plumbing)",
    "03_research_dossiers": "Research dossiers", "04_bibliographies_and_fetch": "Bibliographies",
    "05_drafts": "Drafts and books", "06_source_material": "Source material", "07_archive_old_process": "Archive",
    "08_intake": "Intake", "09_apps_catholicjarvis": "Work suite (code)", "10_volumes": "Volumes (the book sandbox)",
}
BOOK_SUBJECTS = [   # first match on the file name, lowercase
    ("Bible and translations", r"bible|testament|gospel|septuagint|vulgate|psalm|genesis|exodus|isaiah|romans|"
                               r"matthew|john|revelation|apocalypse|torah|scripture|hebrew bible|lxx|commentary on"),
    ("Church Fathers and patristics", r"father|patristic|augustine|chrysostom|irenaeus|ignatius|jerome|origen|"
                                      r"tertullian|cyprian|athanasius|eusebius|ambrose|clement|basil|gregory|ante-nicene|nicene"),
    ("Papacy and church history", r"pope|papa|peter|rome|roman|church history|council|reformation|trent|vatican|"
                                  r"inquisition|crusade|medieval|history of the church|bishop"),
    ("Theology and doctrine", r"theolog|doctrine|dogma|catechism|summa|aquinas|thomist|grace|justification|eucharist|"
                              r"mary|marian|sacrament|trinity|christolog|ecclesiolog|apologetic|catholic|protestant"),
    ("Judaism and rabbinics", r"jew|judais|rabbi|talmud|mishnah|midrash|qumran|dead sea|second temple|halakh|targum"),
    ("Philosophy", r"philosoph|plato|aristotle|metaphysic|logic|ethic|epistemolog|kant|hegel|nietzsche"),
    ("Languages and grammar", r"grammar|greek|latin|hebrew|aramaic|syriac|lexicon|dictionary|vocabulary|koine|syntax"),
    ("Islam and other religions", r"islam|quran|koran|shia|sunni|buddh|hindu|mormon|jehovah"),
    ("Science, health and practical", r"science|physics|biology|health|nutrition|fitness|programming|python|linux|"
                                      r"security|business|finance|career|military"),
]
_BOOK_RX = [(s, re.compile(p, re.I)) for s, p in BOOK_SUBJECTS]
# James's own papers, kept apart from books (listed so he can find them; never opened by any tool here)
_PERSONAL = re.compile(r"resume|\bcv\b|affidavit|ab540|tax|w-?2\b|1099|form_accepted|receipt|invoice|statement|"
                       r"license|insurance|lease|transcript|dd-?214|fafsa|application|benefit|payment|bill\b|eligib", re.I)
_ARTICLE = re.compile(r"reddit|_ r_|stack ?exchange|stackoverflow|news|abc news|screenshot|deepseek|chatgpt|gemini|"
                      r"^\d{4}\.\d{4,5}|wikipedia|documentation|guide|manual|readme|preset|browser", re.I)

_lock = threading.Lock()
_cache = {"mtime": None, "data": None}


def kind_of(ext):
    if ext in BOOK_EXT:
        return "book"
    if ext in CODE_EXT:
        return "code"
    if ext in DATA_EXT:
        return "data"
    if ext in WEB_EXT:
        return "web page"
    if ext in NOTE_EXT:
        return "note"
    return "document"


def _rel(path):
    p = os.path.normpath(path)
    h = os.path.normpath(HOME)
    return p[len(h) + 1:] if p.lower().startswith(h.lower() + "\\") else p


def classify(path, ext, program=""):
    """-> (bucket, shelf). Pure function of the path, extension and (from the inventory) the program folder it is in."""
    rel = _rel(path)
    low = rel.lower()
    kind = kind_of(ext)
    for pre, shelf in VAULT_SHELVES:
        if low == pre or low.startswith(pre + "\\") or (pre.endswith("_") and low.startswith(pre)) or \
                (pre == "takeout" and low.startswith("takeout")):
            return "Vault & archives", shelf
    if program:                                   # SolidWorks, Tor Browser, a browser add-on, a downloaded repo
        return PROGRAM_BUCKET, _rel(program)
    if ARCHIVE_DIR.search("\\" + low):
        return "Vault & archives", "Project archives"
    proj = PROJECT_REL.lower()
    if low.startswith(proj + "\\"):
        rest = low[len(proj) + 1:]
        first = rest.split("\\", 1)[0] if "\\" in rest else ""
        if first.startswith((".", "_")) or first in ("web_app",):
            return "Dissertation project", "Project plumbing (indexes, AI working folders)"
        return "Dissertation project", PROJECT_FOLDERS.get(first, "Project root files" if not first else first)
    if low.startswith("dxm\\"):
        return "Vault & archives", "DXM parent vault (around the project)"
    for pre, name in PROJECTS:
        if low.startswith(pre):
            return "Other projects", name
    # a page saved from the browser: the .html and everything in its *_files folder belong together
    if re.search(r"_files\\", low) or low.startswith("sites\\") or (kind == "web page" and "\\" not in low):
        return "Saved web pages", "Saved web pages"
    if kind == "book":
        name = os.path.basename(low)
        if _PERSONAL.search(name):
            return "Books", "Personal papers (forms, letters, resume)"
        for subject, rx in _BOOK_RX:
            if rx.search(name):
                return "Books", subject
        if _ARTICLE.search(name):
            return "Books", "Articles and saved pages (PDF)"
        return "Books", "Other books"
    if kind == "code":
        top = rel.split("\\", 1)[0] if "\\" in rel else "(home folder)"
        return "Code elsewhere", top
    top = rel.split("\\", 1)[0] if "\\" in rel else "(home folder)"
    return "Loose notes", top


def load():
    try:
        mt = (os.path.getmtime(INVENTORY), os.path.getmtime(BOOK_SHELVES) if os.path.exists(BOOK_SHELVES) else 0)
    except OSError:
        return None
    with _lock:
        if _cache["mtime"] == mt:
            return _cache["data"]
        with open(INVENTORY, encoding="utf-8") as fh:
            inv = json.load(fh)
        rows = inv["rows"]
        # the sorting clone is a copy of the vault by design, so its files are not counted as duplicates
        clone = os.path.join(HOME, "CLONE_FOR_SORTING_2026-10-08__COPIES_NOT_ORIGINALS").lower() + "\\"
        groups = {}
        for r in rows:
            if r.get("fp") and r["bytes"] > 0 and not r["path"].lower().startswith(clone):
                groups.setdefault(r["fp"], []).append(r["path"])
        # book files the keyword rules left on "Other books", shelved by the checked AI pass (tools\organizer_ai_merge.py)
        try:
            with open(BOOK_SHELVES, encoding="utf-8") as fh:
                ai_shelf = json.load(fh)
        except (OSError, ValueError):
            ai_shelf = {}
        out = []
        for r in rows:
            b, s = classify(r["path"], r["ext"], r.get("program", ""))
            if b == "Books" and s == "Other books":
                s = ai_shelf.get(r.get("fp") or r["path"], s)
            same = [] if r["path"].lower().startswith(clone) else groups.get(r.get("fp"), [])
            out.append(dict(r, rel=_rel(r["path"]), bucket=b, shelf=s, kind=kind_of(r["ext"]),
                            dupes=len(same) - 1 if len(same) > 1 else 0))
        data = {"made": inv.get("made"), "rows": out}
        _cache.update(mtime=mt, data=data)
        return data


def summary():
    d = load()
    if not d:
        return None
    buckets = {}
    for r in d["rows"]:
        b = buckets.setdefault(r["bucket"], {"files": 0, "bytes": 0, "shelves": {}, "kinds": {}})
        b["files"] += 1
        b["bytes"] += r["bytes"]
        sh = b["shelves"].setdefault(r["shelf"], {"files": 0, "bytes": 0})
        sh["files"] += 1
        sh["bytes"] += r["bytes"]
        b["kinds"][r["kind"]] = b["kinds"].get(r["kind"], 0) + 1
    dup_groups = {}
    for r in d["rows"]:
        if r["dupes"]:
            dup_groups.setdefault(r["fp"], []).append(r)
    wasted = sum(sum(x["bytes"] for x in g[1:]) for g in dup_groups.values())
    return {"made": d["made"], "files": len(d["rows"]), "buckets": buckets,
            "duplicate_groups": len(dup_groups), "duplicate_bytes": wasted}


def files(bucket=None, shelf=None, kind=None, q=None, dupes_only=False, limit=500, offset=0, sort="mtime",
          folder=None, show_hidden=False):
    d = load()
    if not d:
        return None
    ql = (q or "").lower().split()
    pl = placements()
    rows = []
    for r in d["rows"]:
        e = pl.get(r["path"], {})
        if e.get("hidden") and not show_hidden:
            continue
        if folder is not None and not (e.get("folder") == folder or (e.get("folder") or "").startswith(folder + "/")):
            continue
        if bucket == PROGRAM_BUCKET or r["bucket"] != PROGRAM_BUCKET or show_hidden:
            pass
        elif not bucket and folder is None:
            continue                                   # program files only show when asked for
        if e:
            r = dict(r, placed=e.get("folder", ""), hidden=bool(e.get("hidden")))
        if bucket and r["bucket"] != bucket:
            continue
        if shelf and r["shelf"] != shelf:
            continue
        if kind and r["kind"] != kind:
            continue
        if dupes_only and not r["dupes"]:
            continue
        if ql:
            hay = (r["rel"] + " " + (r.get("title") or "")).lower()
            if not all(w in hay for w in ql):
                continue
        rows.append(r)
    key = {"mtime": lambda r: -r["mtime"], "size": lambda r: -r["bytes"], "name": lambda r: r["rel"].lower()}[sort]
    rows.sort(key=key)
    return {"total": len(rows), "rows": rows[offset:offset + limit]}


def duplicates(limit=300, bucket=None):
    d = load()
    if not d:
        return None
    groups = {}
    for r in d["rows"]:
        if r["dupes"]:
            groups.setdefault(r["fp"], []).append(r)
    out = []
    for fp, g in groups.items():
        if bucket and not any(x["bucket"] == bucket for x in g):
            continue
        g.sort(key=lambda r: (r["bucket"] == "Vault & archives", r["rel"]))
        out.append({"fp": fp, "copies": len(g), "bytes": g[0]["bytes"], "wasted": g[0]["bytes"] * (len(g) - 1),
                    "files": [{"path": x["path"], "rel": x["rel"], "bucket": x["bucket"], "shelf": x["shelf"]} for x in g]})
    out.sort(key=lambda x: -x["wasted"])
    return {"groups": len(out), "rows": out[:limit]}


# ---------------------------------------------------------------- virtual filing ("quasi-moved", James 2026-10-14)
# Nothing on disk moves. James files a file under a folder name of his own, or hides it; the Organizer then shows
# his folders as if the files lived there. Stored in data\organizer_placements.json as {path: {"folder": "...",
# "hidden": true}}; deleting that file undoes all of it.
_plock = threading.Lock()


def placements():
    try:
        with open(PLACEMENTS, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _atomic_replace(src, dst):
    """Atomically replace dst with src, retrying transient Windows file locks."""
    for i in range(10):
        try:
            os.replace(src, dst)
            return
        except (PermissionError, OSError):
            if i == 9:
                gc.collect()
                os.replace(src, dst)
                return
            time.sleep(0.02 * (i + 1))


def _save_placements(d):
    tmp = PLACEMENTS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as w:
        json.dump(d, w, ensure_ascii=False, indent=1)
    _atomic_replace(tmp, PLACEMENTS)


def _clean_folder(folder):
    parts = [p.strip() for p in re.split(r"[\\/]+", folder or "") if p.strip() and p.strip() not in (".", "..")]
    return "/".join(parts)[:200]


def place(path, folder=None, hidden=None):
    """File `path` under `folder` ('' removes it from any folder) and/or set hidden. Returns the entry or None."""
    with _plock:
        d = placements()
        e = dict(d.get(path, {}))
        if folder is not None:
            f = _clean_folder(folder)
            if f:
                e["folder"] = f
            else:
                e.pop("folder", None)
        if hidden is not None:
            if hidden:
                e["hidden"] = True
            else:
                e.pop("hidden", None)
        if e:
            d[path] = e
        else:
            d.pop(path, None)
        _save_placements(d)
        return e or None


def my_folders():
    """Folder -> number of files in it, counting its sub-folders (written as 'Career/Schools'); a parent folder is
    listed even when only its sub-folders hold files."""
    out = {}
    for e in placements().values():
        parts = (e.get("folder") or "").split("/")
        for i in range(1, len(parts) + 1):
            if parts[0]:
                k = "/".join(parts[:i])
                out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))