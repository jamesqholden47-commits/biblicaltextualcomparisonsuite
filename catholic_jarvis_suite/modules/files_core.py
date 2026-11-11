"""Files: the suite's file and Markdown viewer (Phase 1, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).

READ-ONLY. Nothing here writes to a viewed file. The only files this module writes are its own state files in
data\\ (pins, recents, notes, link index), always atomically.

Security boundary: every path goes through resolve(), which accepts only paths inside a configured root (after
realpath, so a junction or symlink cannot point outside). Roots: data\\files_roots.json if present, else DEFAULT_ROOTS.

Main entry points
  roots()                  configured roots
  list_dir(path)           one folder (dirs first), hidden/system folders left out
  view(path, part)         a file rendered for its type (markdown via files_md, text/code, docx text, or a raw URL)
  find(q)                  file-name search across all roots (cached name index)
  where(path)              Volumes chapter, Loose Ends entry, drifted variants, exact copies
  backlinks(path)          notes that [[link]] here (needs the link index; build_links() makes it)
  diff(a, b)               side-by-side line diff of two text files
  pins / recents / notes   small per-user state in data\\files_state.json
"""
import difflib
import hashlib
import json
import os
import re
import threading
import time
import zipfile
from xml.etree import ElementTree

from modules import files_md
from modules.paths_config import get_path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROJECT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
ROOTS_FILE = os.path.join(DATA_DIR, "files_roots.json")
STATE_FILE = os.path.join(DATA_DIR, "files_state.json")
LINKS_FILE = os.path.join(DATA_DIR, "files_links.json")
CONCORDANCE_FILE = os.path.join(DATA_DIR, "vault_concordance.json")

DEFAULT_ROOTS = [
    [PROJECT, "Project"],
    [os.path.join(PROJECT, "10_VOLUMES"), "Volumes"],
    [os.path.join(PROJECT, "06_SOURCE_MATERIAL", "RABBINIC_CORPUS_SEFARIA"), "Sefaria"],
    [get_path("aa1_vault"), "AA1 vault"],
    [get_path("mexico_study"), "Mexico study"],
    [get_path("scholar_decade_plan"), "Scriptorium"],
    [os.path.join(get_path("ag_history_backup"), "readable"), "Antigravity history"],
    [get_path("pdfs_dir"), "Books (PDFS)"],
    [get_path("downloads"), "Downloads"],
]
HIDDEN_DIRS = {"__pycache__", "node_modules", ".git", ".obsidian", ".trash", ".venv", "venv", ".pytest_cache"}
LINK_ROOT_SKIP = {"Downloads", "Antigravity history", "Books (PDFS)"}     # not note collections: no link index, no wiki resolution

TYPES = {
    "markdown": (".md", ".markdown"),
    "text": (".txt", ".log", ".csv", ".tsv", ".rst"),
    "code": (".py", ".js", ".ts", ".json", ".jsonl", ".ps1", ".bat", ".cmd", ".sh", ".css", ".yml", ".yaml",
             ".toml", ".ini", ".cfg", ".xml", ".sql", ".r", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs"),
    "html": (".html", ".htm"),
    "pdf": (".pdf",),
    "image": (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico"),
    "docx": (".docx",),
    "epub": (".epub",),
    "audio": (".mp3", ".wav", ".m4a", ".ogg", ".flac"),
    "video": (".mp4", ".webm", ".mov", ".mkv"),
}
MAX_TEXT_BYTES = 40 * 1024 * 1024      # refuse to render bigger text files (raw download still possible)
CODE_PART_CHARS = 400_000
RECENT_MAX = 30


class Forbidden(Exception):
    pass


class TooLarge(Exception):
    pass


_lock = threading.Lock()


def _read_json(p, default=None):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _replace_retry(tmp, dst):
    for k in range(8):
        try:
            os.replace(tmp, dst)
            return
        except PermissionError:
            time.sleep(0.05 * (k + 1))
    os.replace(tmp, dst)


def _write_json(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    _replace_retry(tmp, p)


# ----------------------------------------------------------------------------- roots and the boundary
def roots():
    cfg = _read_json(ROOTS_FILE)
    rs = cfg if isinstance(cfg, list) and cfg else DEFAULT_ROOTS
    out = []
    for p, lab in rs:
        ap = os.path.abspath(p)
        role = classify_role(ap, is_dir=True)
        out.append({
            "path": ap,
            "label": lab,
            "exists": os.path.isdir(p),
            "role": role,
            "role_label": ROLE_LABELS.get(role, "SUBJECT"),
            "status_badge": "",
        })
    return out


def _norm(p):
    return os.path.normcase(os.path.realpath(os.path.abspath(p)))


def _under(p, root):
    return p == root or p.startswith(root.rstrip("\\/") + os.sep)


def root_of(path):
    """The most specific root containing path (so a Volumes file reports 'Volumes', not 'Project')."""
    np_ = _norm(path)
    best = None
    for r in roots():
        nr = _norm(r["path"])
        if _under(np_, nr) and (best is None or len(nr) > len(_norm(best["path"]))):
            best = r
    return best


def resolve(path):
    if not path or "\x00" in path:
        raise Forbidden("no path")
    ap = os.path.abspath(path)
    if not root_of(ap):
        raise Forbidden("outside the Files roots: " + path)
    return ap


def file_type(name):
    ext = os.path.splitext(name)[1].lower()
    for t, exts in TYPES.items():
        if ext in exts:
            return t
    return "other"


ROLE_LABELS = {
    "master": "MASTER",
    "subject": "SUBJECT",
    "source": "SOURCE",
    "draft": "DRAFT",
    "infra": "INFRA",
    "archive": "ARCHIVE",
}

_excludes_cache = {"mtime": 0, "paths": set(), "names": set()}


def _not_dissertation_excludes():
    cands = [
        os.path.join(PROJECT, "02_CONTROL_AND_STATE", "_NOT_DISSERTATION_CONTENT.json"),
        os.path.join(PROJECT, "02_CONTROL_AND_STATE", "_MEASUREMENTS", "_NOT_DISSERTATION_CONTENT.json"),
    ]
    target = next((p for p in cands if os.path.isfile(p)), None)
    if not target:
        return _excludes_cache
    try:
        m = os.path.getmtime(target)
    except OSError:
        return _excludes_cache
    if m != _excludes_cache["mtime"]:
        d = _read_json(target, {}) or {}
        paths = set()
        names = set()
        for x in d.get("exclude", []):
            x_norm = x.replace("\\", "/").lower().strip()
            paths.add(x_norm)
            names.add(os.path.basename(x_norm))
        _excludes_cache.update(mtime=m, paths=paths, names=names)
    return _excludes_cache


_loose_cache = {"mtime": 0, "status": {}}


def _loose_status_map():
    reg_path = os.path.join(DATA_DIR, "loose_registry.json")
    try:
        m = os.path.getmtime(reg_path)
    except OSError:
        return _loose_cache["status"]
    if m != _loose_cache["mtime"]:
        d = _read_json(reg_path, {}) or {}
        st = {}
        for doc in d.get("docs", []):
            p = doc.get("path")
            if p:
                if doc.get("integrated_into"):
                    st[os.path.normcase(p)] = "IN BOOK"
                elif doc.get("kind") == "SUBJECT" or doc.get("open_items"):
                    st[os.path.normcase(p)] = "LOOSE END"
        _loose_cache.update(mtime=m, status=st)
    return _loose_cache["status"]


def status_badge_for(path, is_dir=False):
    if is_dir:
        return ""
    return _loose_status_map().get(os.path.normcase(path), "")


def classify_role(path, is_dir=False):
    if not path:
        return "subject"
    p_norm = path.replace("\\", "/").lower()
    base = os.path.basename(path).lower()
    ext = os.path.splitext(base)[1].lower() if not is_dir else ""

    # 1. Archive
    if "07_archive_old_process" in p_norm or "_superseded" in p_norm or "_backups" in p_norm or base.endswith(".bak"):
        return "archive"

    # 2. Master
    if "01_master_dissertation" in p_norm or base.startswith("master_dissertation") or base.startswith("the_catholic_case") or base.startswith("the_unbroken_witness"):
        return "master"

    # 3. Infra
    exc = _not_dissertation_excludes()
    if p_norm in exc["paths"] or base in exc["names"] or any(e in p_norm for e in exc["paths"]):
        return "infra"
    if "02_control_and_state" in p_norm or "08_intake" in p_norm or "09_apps_catholicjarvis" in p_norm or "_rescued_cli_agents" in p_norm:
        return "infra"
    if not is_dir and ext in (".py", ".pyw", ".js", ".ts", ".bat", ".cmd", ".ps1", ".sh"):
        return "infra"

    # 4. Draft
    if "05_drafts" in p_norm or "book_successors" in p_norm or "mexico_protestantism_study" in p_norm:
        return "draft"

    # 5. Source
    if "06_source_material" in p_norm or "/pdfs" in p_norm or "\\pdfs" in p_norm or "04_bibliographies_and_fetch" in p_norm or (not is_dir and ext in (".pdf", ".epub", ".mobi", ".djvu", ".azw", ".azw3")):
        return "source"

    # 6. Subject
    if "03_research_dossiers" in p_norm:
        return "subject"

    # Fallbacks
    if "10_volumes" in p_norm:
        return "master"
    if not is_dir and ext in (".pdf", ".epub"):
        return "source"
    if not is_dir and ext in (".py", ".js", ".bat", ".cmd", ".sh", ".ps1"):
        return "infra"
    return "subject"


def list_dir(path):
    ap = resolve(path)
    if not os.path.isdir(ap):
        raise FileNotFoundError(path)
    r = root_of(ap)
    dirs, files = [], []
    with os.scandir(ap) as it:
        for e in it:
            if e.name.startswith(".") or e.name in HIDDEN_DIRS:
                continue
            try:
                if e.is_dir():
                    role = classify_role(e.path, is_dir=True)
                    dirs.append({
                        "name": e.name,
                        "path": e.path,
                        "role": role,
                        "role_label": ROLE_LABELS.get(role, "SUBJECT"),
                        "status_badge": "",
                    })
                elif e.is_file():
                    st = e.stat()
                    role = classify_role(e.path, is_dir=False)
                    badge = status_badge_for(e.path, is_dir=False)
                    files.append({
                        "name": e.name,
                        "path": e.path,
                        "size": st.st_size,
                        "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
                        "type": file_type(e.name),
                        "role": role,
                        "role_label": ROLE_LABELS.get(role, "SUBJECT"),
                        "status_badge": badge,
                    })
            except OSError:
                continue
    dirs.sort(key=lambda d: d["name"].lower())
    files.sort(key=lambda f: f["name"].lower())
    parent = os.path.dirname(ap)
    crumbs, cur = [], ap
    while True:
        crumbs.append({"name": os.path.basename(cur) or cur, "path": cur})
        if _norm(cur) == _norm(r["path"]):
            break
        nxt = os.path.dirname(cur)
        if nxt == cur:
            break
        cur = nxt
    crumbs.reverse()
    crumbs[0]["name"] = r["label"]
    limit = 3000
    return {"path": ap, "root": r["label"], "crumbs": crumbs,
            "parent": parent if _norm(ap) != _norm(r["path"]) else None,
            "dirs": dirs[:limit], "files": files[:limit], "n_dirs": len(dirs), "n_files": len(files),
            "truncated": len(dirs) > limit or len(files) > limit}


# ----------------------------------------------------------------------------- name index (wiki links, find)
_names = {"built": 0, "by_stem": {}, "by_name": {}, "all": [], "building": False}
NAMES_TTL = 900
NAMES_STALE_ON_MISS = 120


def _build_names():
    by_stem, by_name, allf = {}, {}, []
    for r in roots():
        if not r["exists"]:
            continue
        link_ok = r["label"] not in LINK_ROOT_SKIP
        for dp, dns, fns in os.walk(r["path"]):
            dns[:] = [d for d in dns if not d.startswith(".") and d not in HIDDEN_DIRS]
            for f in fns:
                p = os.path.join(dp, f)
                allf.append((f.lower(), p, r["label"]))
                if link_ok:
                    by_name.setdefault(f.lower(), []).append(p)
                    if f.lower().endswith(".md"):
                        by_stem.setdefault(f[:-3].lower(), []).append(p)
    # nested roots (Volumes inside Project) are walked twice; keep one entry per path
    seen, uniq = set(), []
    for t in allf:
        k = os.path.normcase(t[1])
        if k not in seen:
            seen.add(k)
            uniq.append(t)
    for d in (by_stem, by_name):
        for k in d:
            d[k] = sorted(set(d[k]), key=lambda p: (len(p), p))
    _names.update(built=time.time(), by_stem=by_stem, by_name=by_name, all=uniq)


def names(force=False):
    with _lock:
        if force or not _names["built"] or time.time() - _names["built"] > NAMES_TTL:
            _build_names()
    return _names


def resolver_for(from_path):
    """Resolve a wiki target or relative link the way Obsidian does: exact relative path first, then a note with
    that name, preferring one in the same root (then the nearest folder)."""
    base = os.path.dirname(from_path)
    r = root_of(from_path)
    rnorm = _norm(r["path"]) if r else ""

    def pick(cands):
        if not cands:
            return None
        same = [c for c in cands if rnorm and _under(_norm(c), rnorm)]
        pool = same or cands

        def closeness(c):
            common = os.path.commonpath([os.path.normcase(c), os.path.normcase(from_path)])
            return (-len(common), len(c))
        return sorted(pool, key=closeness)[0]

    def resolve_target(t):
        t = t.strip().replace("/", os.sep)
        if not t:
            return None
        for cand in (os.path.join(base, t), os.path.join(base, t + ".md")):
            if os.path.isfile(cand) and root_of(cand):
                return os.path.abspath(cand)
        n = names()
        leaf = os.path.basename(t).lower()
        if "." in leaf and not leaf.endswith(".md"):
            return pick(n["by_name"].get(leaf))
        stem = leaf[:-3] if leaf.endswith(".md") else leaf
        hits = n["by_stem"].get(stem)
        if hits and os.sep in t:          # [[folder/note]]: prefer the path that ends with it
            want = os.path.normcase(t if t.lower().endswith(".md") else t + ".md")
            ends = [h for h in hits if os.path.normcase(h).endswith(want)]
            hits = ends or hits
        return pick(hits)
    return resolve_target


def raw_url(path):
    from urllib.parse import quote
    return "/api/files/raw?path=" + quote(path)


def find(q, limit=60):
    words = [w for w in (q or "").lower().split() if w]
    if not words:
        return {"q": q, "total": 0, "files": []}
    out, total = [], 0
    for name, p, label in names()["all"]:
        if all(w in name for w in words):
            total += 1
            if len(out) < limit * 4:
                out.append((name, p, label))
    # names that start with the query first, then shorter paths
    out.sort(key=lambda t: (not t[0].startswith(words[0]), len(t[1])))
    f_list = []
    for _, p, lab in out[:limit]:
        role = classify_role(p, is_dir=False)
        badge = status_badge_for(p, is_dir=False)
        f_list.append({
            "name": os.path.basename(p),
            "path": p,
            "root": lab,
            "type": file_type(p),
            "role": role,
            "role_label": ROLE_LABELS.get(role, "SUBJECT"),
            "status_badge": badge,
        })
    return {"q": q, "total": total, "files": f_list}


# ----------------------------------------------------------------------------- viewing
def _read_text(ap):
    size = os.path.getsize(ap)
    if size > MAX_TEXT_BYTES:
        raise TooLarge(f"{size:,} bytes is more than the {MAX_TEXT_BYTES // (1024 * 1024)} MB render limit")
    with open(ap, "rb") as fh:
        data = fh.read()
    for enc in ("utf-8-sig", "utf-16") if data[:2] in (b"\xff\xfe", b"\xfe\xff") else ("utf-8-sig",):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")


def docx_text(ap):
    """Paragraph text of a .docx (stdlib only): word/document.xml, one line per paragraph."""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(ap) as z:
        root = ElementTree.fromstring(z.read("word/document.xml"))
    paras = []
    for p in root.iter(ns + "p"):
        paras.append("".join(t.text or "" for t in p.iter(ns + "t")))
    return "\n\n".join(x for x in paras if x.strip())


def epub_sections(ap):
    """Chapters of an .epub in reading order (stdlib only): [(title, text)]. Paragraph breaks kept, markup
    stripped, entities decoded. Sections with almost no text (cover, title page) are skipped."""
    import html as _html
    import posixpath
    with zipfile.ZipFile(ap) as z:
        names = set(z.namelist())
        opf = None
        if "META-INF/container.xml" in names:
            m = re.search(r'full-path="([^"]+)"', z.read("META-INF/container.xml").decode("utf-8", "replace"))
            opf = m.group(1) if m else None
        opf = opf or next((n for n in names if n.endswith(".opf")), None)
        if not opf:
            raise ValueError("not an EPUB (no package file)")
        o = z.read(opf).decode("utf-8", "replace")
        base = posixpath.dirname(opf)
        items = {}
        for tag in re.findall(r"<item\b[^>]*>", o):
            i, h = re.search(r'\bid="([^"]+)"', tag), re.search(r'\bhref="([^"]+)"', tag)
            if i and h:
                items[i.group(1)] = h.group(1)
        out = []
        for idref in re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', o):
            href = items.get(idref)
            if not href:
                continue
            path = posixpath.normpath(posixpath.join(base, _html.unescape(href).split("#")[0]))
            if path not in names:
                continue
            raw = z.read(path).decode("utf-8", "replace")
            raw = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", raw)
            heads = [re.sub(r"<[^>]+>|\s+", " ", _html.unescape(h)).strip()
                     for h in re.findall(r"(?is)<h[1-3]\b[^>]*>(.*?)</h[1-3]>", raw)]
            body = re.sub(r"(?i)<br\s*/?>", "\n", raw)
            body = re.sub(r"(?i)</(p|div|h[1-6]|li|blockquote|tr)>", "\n\n", body)
            body = _html.unescape(re.sub(r"<[^>]+>", " ", body))
            paras = [re.sub(r"[ \t ]+", " ", x).strip() for x in re.split(r"\n\s*\n", body)]
            text = "\n\n".join(x for x in paras if x)
            if len(text.split()) < 15:
                continue
            heads = [h for h in heads if h]
            title = heads[0] if heads else ""
            if heads and len(title) <= 4 and len(heads) > 1:          # "1" then "Peter the Rock" -> "1. Peter the Rock"
                title = title.rstrip(".:") + ". " + heads[1]
            if not title or len(title) <= 4:
                lines = [x for x in text.split("\n") if x.strip()]
                first = lines[0].strip() if lines else ""
                nxt = lines[1].strip() if len(lines) > 1 else ""
                title = (first.rstrip(".:") + ". " + nxt[:70]) if len(first) <= 4 and nxt else first[:80]
            out.append((title, text))
        return out


def _parts_of(text, chunk):
    from modules.reader_core import _split_parts
    if chunk is None:
        return _split_parts(text)
    lines, parts, cur, size = text.split("\n"), [], [], 0
    for ln in lines:
        if size >= chunk and cur:
            parts.append("\n".join(cur))
            cur, size = [], 0
        cur.append(ln)
        size += len(ln) + 1
    parts.append("\n".join(cur))
    return parts


def view(path, part=0, record=True):
    ap = resolve(path)
    if not os.path.isfile(ap):
        raise FileNotFoundError(path)
    st = os.stat(ap)
    t = file_type(ap)
    r = root_of(ap)
    out = {"path": ap, "name": os.path.basename(ap), "type": t, "size": st.st_size, "root": r["label"],
           "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)), "raw_url": raw_url(ap),
           "part": 0, "part_count": 1}
    if t in ("markdown", "text", "code", "docx", "epub"):
        if t == "epub":
            text = "\n\n".join("## " + title + "\n\n" + body for title, body in epub_sections(ap))
        else:
            text = docx_text(ap) if t == "docx" else _read_text(ap)
        parts = _parts_of(text, None if t in ("markdown", "docx", "epub") else CODE_PART_CHARS)
        if part < 0 or part >= len(parts):
            raise IndexError(f"part {part} out of range (0..{len(parts) - 1})")
        out.update(part=part, part_count=len(parts), chars=len(text), words=len(text.split()))
        if t in ("markdown", "docx", "epub"):
            res = files_md.render(parts[part], resolve=resolver_for(ap), raw_url=raw_url, with_frontmatter=(part == 0))
            # a note created after the name index was built would show as unresolved; refresh at most every 2 minutes
            if "md-unresolved" in res["html"] and time.time() - _names["built"] > NAMES_STALE_ON_MISS:
                names(force=True)
                res = files_md.render(parts[part], resolve=resolver_for(ap), raw_url=raw_url, with_frontmatter=(part == 0))
            out.update(html=res["html"], frontmatter=res["frontmatter"], tags=res["tags"], headings=res["headings"],
                       n_links=len(res["links"]))
            if len(parts) > 1:
                out["parts"] = [_part_title(p, i) for i, p in enumerate(parts)]
        else:
            out["text"] = parts[part]
            out["first_line"] = 1 + sum(p.count("\n") + 1 for p in parts[:part])
    if record and part == 0:
        add_recent(ap)
    return out


def _part_title(text, i):
    for ln in text.split("\n"):
        m = re.match(r"^#{1,3}\s+(.*)", ln.strip())
        if m:
            return m.group(1)[:80]
    return f"Part {i + 1}"


def raw(path):
    ap = resolve(path)
    if not os.path.isfile(ap):
        raise FileNotFoundError(path)
    return ap


# ----------------------------------------------------------------------------- where is this going?
_conc = {"mtime": 0, "drift": {}, "dups": {}}


def _concordance():
    try:
        m = os.path.getmtime(CONCORDANCE_FILE)
    except OSError:
        return _conc
    if m != _conc["mtime"]:
        d = _read_json(CONCORDANCE_FILE, {}) or {}
        drift, dups = {}, {}
        for f in d.get("version_drift_files", []):
            vs = [{"path": v["path"], "vault": v.get("vault_name"), "rel": v.get("rel_path"), "size": v.get("size"),
                   "mtime": (v.get("mtime_iso") or "")[:16]} for v in f.get("variants", [])]
            for v in vs:
                drift[os.path.normcase(v["path"])] = vs
        for c in d.get("exact_duplicate_clusters", []):
            members = [c.get("canonical")] + list(c.get("instances") or [])
            paths = [x["path"] for x in members if isinstance(x, dict) and x.get("path")]
            for p in paths:
                dups[os.path.normcase(p)] = paths
        _conc.update(mtime=m, drift=drift, dups=dups)
    return _conc


def where(path):
    ap = resolve(path)
    key = os.path.normcase(ap)
    out = {"path": ap}
    try:
        from modules import books_core, books_routes
        sid = books_core.source_id(ap)
        out["volumes"] = books_routes.where(ids=sid).get(sid)
        out["source_id"] = sid
    except Exception as e:  # noqa: BLE001 — no plan yet, or Volumes not loaded
        out["volumes"] = {"state": "unknown", "note": str(e)[:200]}
    reg = _read_json(os.path.join(DATA_DIR, "loose_registry.json"), {}) or {}
    doc = next((d for d in reg.get("docs", []) if os.path.normcase(d.get("path", "")) == key), None)
    if doc:
        marks = (_read_json(os.path.join(DATA_DIR, "loose_status.json"), {}) or {}).get("marks", {})
        out["loose"] = {"id": doc.get("id"), "kind": doc.get("kind"), "integrated_into": doc.get("integrated_into"),
                        "open_items": len(doc.get("open_items") or []), "thread": doc.get("thread"),
                        "mark": marks.get(doc.get("id"))}
    c = _concordance()
    vs = c["drift"].get(key)
    if vs:
        out["variants"] = [v for v in vs if os.path.normcase(v["path"]) != key]
    dp = c["dups"].get(key)
    if dp:
        out["exact_copies"] = [p for p in dp if os.path.normcase(p) != key]
    return out


# ----------------------------------------------------------------------------- backlinks (link index)
_links = {"state": "idle", "done": 0, "total": 0, "started": 0, "error": "", "inverse": None, "mtime": 0}


def _md_files_for_links():
    for name, p, label in names(force=True)["all"]:
        if label not in LINK_ROOT_SKIP and name.endswith(".md"):
            yield p


def _build_links_worker():
    try:
        old = (_read_json(LINKS_FILE, {}) or {}).get("files", {})
        files = list(_md_files_for_links())
        _links.update(total=len(files), done=0)
        new, reread = {}, 0
        for p in files:
            try:
                m = int(os.path.getmtime(p))
            except OSError:
                continue
            prev = old.get(p)
            if prev and prev[0] == m:
                new[p] = prev
            else:
                try:
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        targets = sorted(set(files_md.wiki_targets(fh.read())))
                except OSError:
                    targets = []
                new[p] = [m, targets]
                reread += 1
            _links["done"] += 1
        _write_json(LINKS_FILE, {"built_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "n_files": len(new),
                                 "reread": reread, "files": new})
        _links.update(state="done", inverse=None, error="")
    except Exception as e:  # noqa: BLE001
        _links.update(state="error", error=f"{type(e).__name__}: {e}")


def build_links():
    """Start (or report) a link-index build. Runs in a thread of this server process and ends when done; only
    notes whose modification time changed are re-read, so later builds are quick."""
    with _lock:
        if _links["state"] == "running":
            return links_status()
        _links.update(state="running", started=time.time(), done=0, total=0, error="")
    threading.Thread(target=_build_links_worker, daemon=True).start()
    return links_status()


def links_status():
    d = _read_json(LINKS_FILE, None) if _links["state"] != "running" else None
    s = {k: _links[k] for k in ("state", "done", "total", "error")}
    if d:
        s.update(built_at=d.get("built_at"), n_files=d.get("n_files"), reread=d.get("reread"))
    elif _links["state"] != "running" and not os.path.exists(LINKS_FILE):
        s["state"] = "missing"
    return s


def _inverse():
    try:
        m = os.path.getmtime(LINKS_FILE)
    except OSError:
        return None
    if _links["inverse"] is None or _links["mtime"] != m:
        inv = {}
        for p, (_, targets) in ((_read_json(LINKS_FILE, {}) or {}).get("files", {})).items():
            for t in targets:
                inv.setdefault(t, []).append(p)
        _links.update(inverse=inv, mtime=m)
    return _links["inverse"]


def backlinks(path):
    ap = resolve(path)
    inv = _inverse()
    if inv is None:
        return {"path": ap, "state": "missing", "backlinks": []}
    stem = os.path.splitext(os.path.basename(ap))[0].lower()
    srcs = [p for p in inv.get(stem, []) if os.path.normcase(p) != os.path.normcase(ap)]
    srcs.sort(key=lambda p: os.path.basename(p).lower())
    return {"path": ap, "state": "ok", "total": len(srcs),
            "backlinks": [{"path": p, "name": os.path.basename(p)[:-3]} for p in srcs[:300]]}


# ----------------------------------------------------------------------------- diff
def diff(a, b, max_rows=6000):
    pa, pb = resolve(a), resolve(b)
    ta = _read_text(pa).replace("\r\n", "\n").split("\n")
    tb = _read_text(pb).replace("\r\n", "\n").split("\n")
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    rows = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            span = i2 - i1
            if span > 6:      # fold long unchanged stretches, keep 3 lines of context each side
                for k in range(3):
                    rows.append({"op": "equal", "a_no": i1 + k + 1, "a": ta[i1 + k], "b_no": j1 + k + 1, "b": tb[j1 + k]})
                rows.append({"op": "fold", "n": span - 6})
                for k in range(span - 3, span):
                    rows.append({"op": "equal", "a_no": i1 + k + 1, "a": ta[i1 + k], "b_no": j1 + k + 1, "b": tb[j1 + k]})
            else:
                for k in range(span):
                    rows.append({"op": "equal", "a_no": i1 + k + 1, "a": ta[i1 + k], "b_no": j1 + k + 1, "b": tb[j1 + k]})
        else:
            for k in range(max(i2 - i1, j2 - j1)):
                ia, jb = i1 + k, j1 + k
                rows.append({"op": op, "a_no": ia + 1 if ia < i2 else None, "a": ta[ia] if ia < i2 else None,
                             "b_no": jb + 1 if jb < j2 else None, "b": tb[jb] if jb < j2 else None})
        if len(rows) > max_rows:
            break
    only_a = sum(i2 - i1 for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("delete", "replace"))
    only_b = sum(j2 - j1 for op, i1, i2, j1, j2 in sm.get_opcodes() if op in ("insert", "replace"))
    return {"a": pa, "b": pb, "similarity": round(sm.ratio(), 3), "lines_a": len(ta), "lines_b": len(tb),
            "changed_a": only_a, "changed_b": only_b, "rows": rows[:max_rows], "truncated": len(rows) > max_rows}


# ----------------------------------------------------------------------------- pins, recents, notes
def _state():
    s = _read_json(STATE_FILE, {}) or {}
    s.setdefault("version", 1)
    s.setdefault("pins", [])
    s.setdefault("recent", [])
    s.setdefault("notes", {})
    return s


def get_state():
    s = _state()
    pins = []
    for p in s.get("pins", []):
        p_copy = dict(p)
        if "role" not in p_copy:
            is_d = p_copy.get("dir", False)
            p_copy["role"] = classify_role(p_copy.get("path", ""), is_dir=is_d)
            p_copy["role_label"] = ROLE_LABELS.get(p_copy["role"], "SUBJECT")
            p_copy["status_badge"] = status_badge_for(p_copy.get("path", ""), is_dir=is_d)
        pins.append(p_copy)
    recent = []
    for r in s.get("recent", []):
        r_copy = dict(r)
        if "role" not in r_copy:
            r_copy["role"] = classify_role(r_copy.get("path", ""), is_dir=False)
            r_copy["role_label"] = ROLE_LABELS.get(r_copy["role"], "SUBJECT")
            r_copy["status_badge"] = status_badge_for(r_copy.get("path", ""), is_dir=False)
        recent.append(r_copy)
    return {"pins": pins, "recent": recent,
            "notes_count": sum(len(v) for v in s["notes"].values())}


def add_recent(ap):
    with _lock:
        s = _state()
        s["recent"] = [r for r in s["recent"] if os.path.normcase(r["path"]) != os.path.normcase(ap)]
        role = classify_role(ap, is_dir=False)
        badge = status_badge_for(ap, is_dir=False)
        s["recent"].insert(0, {
            "path": ap,
            "name": os.path.basename(ap),
            "at": time.strftime("%Y-%m-%d %H:%M"),
            "role": role,
            "role_label": ROLE_LABELS.get(role, "SUBJECT"),
            "status_badge": badge,
        })
        del s["recent"][RECENT_MAX:]
        _write_json(STATE_FILE, s)


def set_pin(path, pinned=True):
    ap = resolve(path)
    with _lock:
        s = _state()
        s["pins"] = [p for p in s["pins"] if os.path.normcase(p["path"]) != os.path.normcase(ap)]
        if pinned:
            is_d = os.path.isdir(ap)
            role = classify_role(ap, is_dir=is_d)
            badge = status_badge_for(ap, is_dir=is_d)
            s["pins"].append({
                "path": ap,
                "name": os.path.basename(ap) or ap,
                "dir": is_d,
                "role": role,
                "role_label": ROLE_LABELS.get(role, "SUBJECT"),
                "status_badge": badge,
            })
        _write_json(STATE_FILE, s)
    return s["pins"]


def get_notes(path):
    ap = resolve(path)
    return _state()["notes"].get(os.path.normcase(ap), [])


def add_note(path, text):
    ap = resolve(path)
    text = (text or "").strip()
    if not text:
        raise ValueError("empty note")
    with _lock:
        s = _state()
        lst = s["notes"].setdefault(os.path.normcase(ap), [])
        lst.append({"id": hashlib.sha1(f"{ap}{time.time()}{text}".encode()).hexdigest()[:10],
                    "at": time.strftime("%Y-%m-%d %H:%M"), "text": text, "path": ap})
        _write_json(STATE_FILE, s)
    return lst


def delete_note(path, note_id):
    """Removes one of James's own margin notes from the suite's state file (the viewed file is never touched)."""
    ap = resolve(path)
    with _lock:
        s = _state()
        k = os.path.normcase(ap)
        s["notes"][k] = [n for n in s["notes"].get(k, []) if n["id"] != note_id]
        _write_json(STATE_FILE, s)
    return s["notes"][k]
