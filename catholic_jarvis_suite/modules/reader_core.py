r"""
Reader module core logic (module id "reader"). Task C004, 2026-10-03.

Provides chapter listing, markdown-to-HTML rendering with badge-tagged evidence,
'still needs checking' extraction, and tier loading for The Catholic Case (Reader's Edition).
READ-ONLY with respect to the source chapters in C:\Users\Elation\Mexico_Protestantism_Study\05_READERS_EDITION\chapters.
"""
from __future__ import annotations

import html
import json
import os
import re

from modules.paths_config import get_path

CHAPTERS_DIR = os.path.join(get_path("mexico_study"), "05_READERS_EDITION", "chapters")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIERS_DIR = os.path.join(HERE, "data", "tiers")

# Tag regex handling [V], [V: ...], [R], [R: ...], [S], [S: ...], [V/S], and tags with nested parens
TAG_RE = re.compile(r'\[(?P<kind>[VRS](?:/[VRS])?)(?P<rest>:[^\]]+)?\]')


def set_chapters_dir(path: str):
    global CHAPTERS_DIR
    CHAPTERS_DIR = path


def set_tiers_dir(path: str):
    global TIERS_DIR
    TIERS_DIR = path


def list_chapters() -> list[dict]:
    """List all chapter markdown files with chapter number, title, and file size."""
    if not os.path.exists(CHAPTERS_DIR):
        return []
    files = sorted([f for f in os.listdir(CHAPTERS_DIR) if f.endswith(".md")])
    chapters = []
    for f in files:
        full_path = os.path.join(CHAPTERS_DIR, f)
        stem = os.path.splitext(f)[0]
        title = stem.replace("_", " ").title()
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                first_lines = [fh.readline() for _ in range(10)]
            for line in first_lines:
                line_s = line.strip()
                if line_s.startswith("# "):
                    title = line_s[2:].strip()
                    break
        except OSError:
            pass
        chapters.append({
            "filename": f,
            "stem": stem,
            "title": title,
            "size": os.path.getsize(full_path),
            "path": full_path
        })
    return chapters


def count_tags(text: str) -> dict[str, int]:
    """Count [V...], [R...], [S...] tags in text."""
    counts = {"V": 0, "R": 0, "S": 0, "other": 0}
    for m in TAG_RE.finditer(text):
        kind = m.group("kind").upper()
        if "V" in kind and "S" in kind:
            counts["V"] += 1
            counts["S"] += 1
        elif kind.startswith("V"):
            counts["V"] += 1
        elif kind.startswith("R"):
            counts["R"] += 1
        elif kind.startswith("S"):
            counts["S"] += 1
        else:
            counts["other"] += 1
    return counts


def render_markdown(text: str) -> str:
    """
    Safely render chapter markdown to HTML without external dependencies.
    Escapes all text first, then renders headings, paragraphs, lists, bold, italics, blockquotes,
    and replaces evidence tags with interactive badges.
    """
    lines = text.replace("\r", "").split("\n")
    rendered_blocks = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^(?:---|\*\*\*|___)$', line):
            rendered_blocks.append('<hr class="reader-hr"/>')
            i += 1
            continue

        # Heading (always single line)
        h_match = re.match(r'^(#{1,6})\s+(.*)$', line)
        if h_match:
            level = len(h_match.group(1))
            h_text = h_match.group(2).strip()
            escaped_h = html.escape(h_text)
            inline_h = _render_inline(escaped_h)
            rendered_blocks.append(f'<h{level} class="reader-h reader-h{level}">{inline_h}</h{level}>')
            i += 1
            continue

        # Blockquote (lines starting with >)
        if line.startswith(">"):
            q_lines = []
            while i < n and (lines[i].strip().startswith(">") or (lines[i].strip() and q_lines)):
                if lines[i].strip().startswith(">"):
                    q_lines.append(lines[i].strip()[1:].strip())
                elif not lines[i].strip():
                    break
                else:
                    q_lines.append(lines[i].strip())
                i += 1
            escaped_q = html.escape("\n".join(q_lines))
            inline_q = _render_inline(escaped_q).replace("\n", "<br/>")
            rendered_blocks.append(f'<blockquote class="reader-quote">{inline_q}</blockquote>')
            continue

        # Unordered list
        if re.match(r'^[-*•]\s+', line):
            items = []
            while i < n and re.match(r'^\s*[-*•]\s+', lines[i].strip()):
                item_text = re.sub(r'^\s*[-*•]\s+', '', lines[i].strip())
                items.append(f'<li>{_render_inline(html.escape(item_text))}</li>')
                i += 1
            rendered_blocks.append(f'<ul class="reader-list">{"".join(items)}</ul>')
            continue

        # Ordered list
        if re.match(r'^\d+[.)]\s+', line):
            items = []
            while i < n and re.match(r'^\s*\d+[.)]\s+', lines[i].strip()):
                item_text = re.sub(r'^\s*\d+[.)]\s+', '', lines[i].strip())
                items.append(f'<li>{_render_inline(html.escape(item_text))}</li>')
                i += 1
            rendered_blocks.append(f'<ol class="reader-list">{"".join(items)}</ol>')
            continue

        # Regular paragraph (gather consecutive non-blank, non-special lines)
        p_lines = []
        while i < n:
            curr = lines[i].strip()
            if not curr:
                break
            if re.match(r'^(?:#{1,6}\s+|---|\*\*\*|___|>|[-*•]\s+|\d+[.)]\s+)', curr):
                break
            p_lines.append(curr)
            i += 1

        if not p_lines:
            # C007: a line such as "***bold*** text" or "--- note" starts like a rule but is not one, and no
            # earlier branch took it. Before this guard the loop never advanced and hung the request forever.
            p_lines.append(lines[i].strip())
            i += 1

        if p_lines:
            full_p = " ".join(p_lines)
            escaped_p = html.escape(full_p)
            inline_p = _render_inline(escaped_p)
            is_spanish = bool(re.search(r'\b(hermano|iglesia|inquisición|quemaron|indígenas|cuarenta|personas|biblia|dios|jesús|santos|fe|católica)\b', full_p, re.I))
            lang_attr = ' data-lang="es"' if is_spanish else ' data-lang="en"'
            rendered_blocks.append(f'<p class="reader-p"{lang_attr}>{inline_p}</p>')

    return "\n".join(rendered_blocks)


def _render_inline(escaped_text: str) -> str:
    """Format bold, italics, code, and evidence tag badges on already HTML-escaped text."""
    # Bold **text**
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped_text)
    # Italics *text* or _text_
    t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', t)
    # Inline code `code`
    t = re.sub(r'`([^`]+)`', r'<code class="reader-code">\1</code>', t)

    # Badges for tags [V...], [R...], [S...]
    def badge_repl(m):
        raw_tag = m.group(0)
        kind = m.group("kind").upper()
        css_class = "badge-v" if "V" in kind else ("badge-r" if "R" in kind else "badge-s")
        # Tooltip content is the raw tag text
        return f'<span class="reader-badge {css_class}" title="{raw_tag}">{raw_tag}</span>'

    t = TAG_RE.sub(badge_repl, t)
    return t


def extract_checking_items(text: str, chapter_stem: str = "") -> list[dict]:
    """
    Extract bullet items and questions from 'Before using this in public: what still needs checking'.
    """
    items = []
    # Find checking section (stops at next level-2 heading or EOF)
    m = re.search(r'##\s+(?:\d+\.\s*)?Before using this in public:\s*what still needs checking\b(.*?)(?=\n##\s+[^\n#]|\Z)', text, re.DOTALL | re.I)
    if not m:
        return []

    sec_text = m.group(1).strip()
    subheading = ""
    for line in sec_text.split("\n"):
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith("### "):
            subheading = line_s[4:].strip()
            continue
        if line_s.startswith("- ") or line_s.startswith("* "):
            item_text = line_s[2:].strip()
            items.append({
                "chapter": chapter_stem,
                "category": subheading or "General",
                "text": item_text
            })
    return items


def get_bookwide_checking_items() -> list[dict]:
    """Aggregate 'still needs checking' items across all 35 chapters."""
    all_items = []
    for ch in list_chapters():
        try:
            with open(ch["path"], "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            items = extract_checking_items(content, ch["stem"])
            all_items.extend(items)
        except OSError:
            pass
    return all_items


def get_chapter_data(stem: str) -> dict:
    """Read and parse a full chapter: raw markdown, HTML, tag counts, sections, checking items, and tiers."""
    filename = f"{stem}.md" if not stem.endswith(".md") else stem
    # C007: a stem is a bare file name. Separators, drive letters and NULs would let
    # os.path.join walk out of CHAPTERS_DIR (a stem like "..\..\x" on Windows).
    if (not stem or "\x00" in stem or "/" in stem or "\\" in stem or ":" in stem
            or os.path.basename(filename) != filename or filename in (".md", "..md")):
        raise FileNotFoundError(f"Chapter file {stem} not found")
    full_path = os.path.join(CHAPTERS_DIR, filename)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Chapter file {full_path} not found")

    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
        raw_text = f.read()

    # Extract sections
    sections = []
    for line in raw_text.split("\n"):
        m = re.match(r'^(#{1,3})\s+(.*)$', line.strip())
        if m:
            sections.append({
                "level": len(m.group(1)),
                "title": m.group(2).strip()
            })

    counts = count_tags(raw_text)
    checking = extract_checking_items(raw_text, stem)
    html_content = render_markdown(raw_text)

    # Check for tiers in data/tiers/<stem>/
    tiers_path = os.path.join(TIERS_DIR, stem.replace(".md", ""))
    available_tiers = []
    if os.path.exists(tiers_path):
        for f in sorted(os.listdir(tiers_path)):
            if f.endswith(".json"):
                available_tiers.append(f)

    return {
        "stem": stem.replace(".md", ""),
        "filename": filename,
        "title": sections[0]["title"] if sections else stem,
        "tag_counts": counts,
        "sections": sections,
        "checking_items": checking,
        "checking_count": len(checking),
        "available_tiers": available_tiers,
        "html": html_content
    }


def get_section_tier(stem: str, section_num: str) -> dict:
    """Load tiered explanations (plain, working, expert, spanish) for a chapter section."""
    tier_file = os.path.join(TIERS_DIR, stem, f"{section_num}.json")
    if not os.path.exists(tier_file):
        return {
            "stem": stem,
            "section": section_num,
            "status": "not_generated",
            "message": f"Tiers not generated yet for {stem} section {section_num}."
        }
    try:
        with open(tier_file, "r", encoding="utf-8") as f:
            raw_content = f.read()
        # Clean any trailing HTML comments or worker completion markers
        clean_content = re.sub(r'<!--\s*WORKER COMPLETE:.*?-->', '', raw_content).strip()
        data = json.loads(clean_content)
        return {
            "stem": stem,
            "section": section_num,
            "status": "ready",
            "data": data
        }
    except Exception as e:
        return {
            "stem": stem,
            "section": section_num,
            "status": "error",
            "message": str(e)
        }


# =====================================================================================
# C007 (2026-10-06): open ANY allowed document, not only the 35 chapters.
#
# SECURITY BOUNDARY. resolve_doc_path() is the only gate. A path is readable only if, after
# os.path.abspath + os.path.normcase, it is
#   (a) a .md/.html file inside CHAPTERS_DIR (the Reader's Edition chapters) or the assembled
#       Reader's Edition file,
#   (b) a .md/.html file inside VOLUMES_DIR (10_VOLUMES; may not exist yet), or
#   (c) exactly one of the "path" values listed in data/loose_registry.json (read-only here;
#       the Loose Ends module regenerates it) and with a renderable extension.
# Everything else raises DocForbidden (the route turns it into HTTP 403). Relative paths,
# "..", other drives, NUL bytes, and non-document extensions (.py, .json, .pdf ...) are refused.
# Folder prefixes are also checked after os.path.realpath so a junction/symlink inside an
# allowed folder cannot lead outside it.
# =====================================================================================
import threading
from html.parser import HTMLParser

PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))   # ...\_PROJECT_HistoryProvesCatholicism
VOLUMES_DIR = os.path.join(PROJECT_ROOT, "10_VOLUMES")
REGISTRY_PATH = os.path.join(HERE, "data", "loose_registry.json")
ASSEMBLED_FILE = os.path.join(os.path.dirname(CHAPTERS_DIR), "THE_CATHOLIC_CASE_Readers_Edition.md")

MD_EXTS = (".md", ".markdown")
HTML_EXTS = (".html", ".htm")
RENDERABLE_EXTS = MD_EXTS + HTML_EXTS
MAX_DOC_BYTES = 40 * 1024 * 1024        # refuse to load anything bigger than this (HTTP 413)
SINGLE_PART_CHARS = 150_000             # up to this many characters: one part, whole HTML
PART_CHARS = 120_000                    # larger documents are cut into parts of about this size
HEAD12_RE = re.compile(r'^#{1,2}\s+\S')
HEAD13_RE = re.compile(r'^(#{1,3})\s+(.*)$')


class DocForbidden(PermissionError):
    """The path is not one the Reader may open (route: HTTP 403)."""


class DocTooLarge(ValueError):
    """The file exceeds MAX_DOC_BYTES (route: HTTP 413)."""


def set_volumes_dir(path: str):
    global VOLUMES_DIR
    VOLUMES_DIR = path


def set_registry_path(path: str):
    global REGISTRY_PATH
    REGISTRY_PATH = path
    _REGISTRY_CACHE["key"] = None


def set_assembled_file(path: str):
    global ASSEMBLED_FILE
    ASSEMBLED_FILE = path


def _norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p))


def _under(norm_path: str, norm_folder: str) -> bool:
    return norm_path.startswith(norm_folder.rstrip("\\/") + os.sep)


_REGISTRY_CACHE: dict = {"key": None, "paths": frozenset(), "docs": []}
_REGISTRY_LOCK = threading.Lock()


def _registry():
    """Return (set of normalised registry paths, list of registry docs). Never raises; a missing or
    corrupt registry simply allows nothing. Cached on (mtime_ns, size) so a regenerated file is seen."""
    try:
        st = os.stat(REGISTRY_PATH)
        key = (REGISTRY_PATH, st.st_mtime_ns, st.st_size)
    except OSError:
        return frozenset(), []
    with _REGISTRY_LOCK:
        if _REGISTRY_CACHE["key"] == key:
            return _REGISTRY_CACHE["paths"], _REGISTRY_CACHE["docs"]
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            docs = data.get("docs") if isinstance(data, dict) else data
            docs = [d for d in (docs or []) if isinstance(d, dict) and isinstance(d.get("path"), str)]
        except (OSError, ValueError):
            return frozenset(), []
        paths = frozenset(_norm(d["path"]) for d in docs if os.path.isabs(d["path"]))
        _REGISTRY_CACHE.update({"key": key, "paths": paths, "docs": docs})
        return paths, docs


# (d) 2026-10-06 integrator: every source listed in the Bookbinder plan (data/books_plan.json), which
#     includes the Obsidian vault notes; (e) the Sefaria rabbinic corpus folder (read-only source text).
BOOKS_PLAN_PATH = os.path.join(HERE, "data", "books_plan.json")
SEFARIA_DIR = os.path.join(PROJECT_ROOT, "06_SOURCE_MATERIAL", "RABBINIC_CORPUS_SEFARIA")
DOSSIERS_DIR = os.path.join(PROJECT_ROOT, "03_RESEARCH_DOSSIERS")
MASTER_DIR = os.path.join(PROJECT_ROOT, "01_MASTER_DISSERTATION")
_PLAN_CACHE: dict = {"key": None, "paths": frozenset()}


def _plan_paths():
    try:
        st = os.stat(BOOKS_PLAN_PATH)
        key = (BOOKS_PLAN_PATH, st.st_mtime_ns, st.st_size)
    except OSError:
        return frozenset()
    with _REGISTRY_LOCK:
        if _PLAN_CACHE["key"] == key:
            return _PLAN_CACHE["paths"]
        try:
            with open(BOOKS_PLAN_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            srcs = (data.get("sources") or {}).values() if isinstance(data, dict) else []
            paths = frozenset(_norm(s["path"]) for s in srcs if isinstance(s, dict) and isinstance(s.get("path"), str) and os.path.isabs(s["path"]))
        except (OSError, ValueError):
            return frozenset()
        _PLAN_CACHE.update({"key": key, "paths": paths})
        return paths


def resolve_doc_path(path: str):
    """Validate a user-supplied path. Returns (absolute_path, source) with source in
    'chapter' | 'volume' | 'registry'. Raises DocForbidden if the path is not allowed and
    FileNotFoundError if it is allowed but the file is not there."""
    if not isinstance(path, str):
        raise DocForbidden("path must be text")
    p = path.strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in ('"', "'"):    # Explorer "Copy as path" adds quotes
        p = p[1:-1].strip()
    if not p or chr(0) in p or len(p) > 1000:
        raise DocForbidden("empty or invalid path")
    if not os.path.isabs(p):
        raise DocForbidden("an absolute path is required")
    ap = os.path.abspath(p)
    norm = os.path.normcase(ap)
    if os.path.splitext(norm)[1] not in RENDERABLE_EXTS:
        raise DocForbidden("only markdown and HTML documents can be opened in the Reader")

    source = None
    real_folder = None
    if _under(norm, _norm(CHAPTERS_DIR)):
        source, real_folder = "chapter", CHAPTERS_DIR
    elif norm == _norm(ASSEMBLED_FILE):
        source = "chapter"
    elif _under(norm, _norm(VOLUMES_DIR)):
        source, real_folder = "volume", VOLUMES_DIR
    elif norm in _registry()[0]:
        source = "registry"
    elif norm in _plan_paths():
        source = "books"
    elif _under(norm, _norm(SEFARIA_DIR)):
        source, real_folder = "sefaria", SEFARIA_DIR
    elif _under(norm, _norm(DOSSIERS_DIR)):
        source, real_folder = "dossier", DOSSIERS_DIR
    elif _under(norm, _norm(MASTER_DIR)):
        source, real_folder = "master", MASTER_DIR
    if source is None:
        raise DocForbidden("this path is not in the Reader's allowed set")

    if real_folder is not None:
        # A junction or symlink inside an allowed folder must not lead out of it.
        real = os.path.normcase(os.path.realpath(ap))
        if not _under(real, os.path.normcase(os.path.realpath(real_folder))):
            raise DocForbidden("path resolves outside the allowed folder")
    if not os.path.isfile(ap):
        raise FileNotFoundError(f"{ap} not found")
    return ap, source


def list_dossiers() -> list[dict]:
    """List subject research dossiers and master study guides, respecting Rule 13 exclusions."""
    items = []
    exclude_set = set()
    not_diss_file = os.path.join(PROJECT_ROOT, "02_CONTROL_AND_STATE", "_NOT_DISSERTATION_CONTENT.json")
    if os.path.exists(not_diss_file):
        try:
            with open(not_diss_file, "r", encoding="utf-8") as f:
                ex_data = json.load(f)
                exclude_set = set(os.path.normcase(os.path.basename(x)) for x in ex_data.get("exclude", []))
        except Exception:
            pass

    # 1. Master dissertation files
    if os.path.exists(MASTER_DIR):
        for f in sorted(os.listdir(MASTER_DIR)):
            if f.endswith(".md"):
                p = os.path.join(MASTER_DIR, f)
                items.append({
                    "category": "Master Text",
                    "filename": f,
                    "stem": os.path.splitext(f)[0],
                    "title": f.replace("_", " ").replace(".md", ""),
                    "path": p,
                    "size": os.path.getsize(p)
                })

    # 2. Research Dossiers
    if os.path.exists(DOSSIERS_DIR):
        for root, dirs, files in os.walk(DOSSIERS_DIR):
            for f in sorted(files):
                if f.endswith(".md"):
                    base_low = os.path.normcase(f)
                    if base_low in exclude_set:
                        continue
                    p = os.path.join(root, f)
                    rel = os.path.relpath(p, DOSSIERS_DIR)
                    title = f.replace("_", " ").replace(".md", "")
                    items.append({
                        "category": "Research Dossier",
                        "filename": f,
                        "stem": os.path.splitext(f)[0],
                        "relpath": rel,
                        "title": title,
                        "path": p,
                        "size": os.path.getsize(p)
                    })
    return items


class _TextFromHTML(HTMLParser):
    """Reduce an HTML file to markdown-ish text (headings, paragraphs, list items). Scripts, styles
    and <head> are dropped. The text is escaped later by render_markdown, so nothing here is trusted."""
    BLOCK = {"p", "div", "br", "tr", "section", "article", "table", "ul", "ol", "blockquote", "pre", "li"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.heading = None
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "head", "noscript", "template"):
            self.skip += 1
        elif tag == "title":
            self._in_title = True
        elif len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
            self.heading = tag
        elif tag == "li":
            self.out.append("\n- ")
        elif tag in self.BLOCK:
            self.out.append("\n\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "head", "noscript", "template"):
            self.skip = max(0, self.skip - 1)
        elif tag == "title":
            self._in_title = False
        elif tag == self.heading:
            self.out.append("\n\n")
            self.heading = None
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if self._in_title and self.title is None:
            self.title = data.strip()
        if self.skip:
            return
        self.out.append(re.sub(r"\s+", " ", data))

    def text(self):
        t = "".join(self.out)
        t = re.sub(r"[ \t]+\n", "\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        # inside paragraphs, fold the soft line breaks of the source file into spaces
        return t.strip()


def html_to_markdown_text(raw_html: str) -> str:
    parser = _TextFromHTML()
    try:
        parser.feed(raw_html)
        parser.close()
    except Exception:
        pass
    body = parser.text()
    if parser.title and not re.search(r"^#\s", body, re.M):
        body = "# " + parser.title + "\n\n" + body
    return body


def _split_parts(text: str) -> list:
    """Cut a large document into parts at level-1/2 headings, about PART_CHARS each. A single
    heading-less stretch longer than PART_CHARS is cut at blank lines. Concatenating the parts with
    newlines gives back the original text exactly (nothing is dropped)."""
    if len(text) <= SINGLE_PART_CHARS:
        return [text]
    lines = text.split("\n")
    segs, cur = [], []
    for ln in lines:
        if cur and HEAD12_RE.match(ln.strip()):
            segs.append(cur)
            cur = []
        cur.append(ln)
    if cur:
        segs.append(cur)
    pieces = []
    for seg in segs:
        if sum(len(x) + 1 for x in seg) <= PART_CHARS * 2:
            pieces.append(seg)
            continue
        chunk, size = [], 0
        for ln in seg:
            if size >= PART_CHARS and not ln.strip():
                pieces.append(chunk)
                chunk, size = [], 0
            chunk.append(ln)
            size += len(ln) + 1
        if chunk:
            pieces.append(chunk)
    parts, cur, size = [], [], 0
    for pc in pieces:
        psize = sum(len(x) + 1 for x in pc)
        if cur and size + psize > PART_CHARS:
            parts.append(cur)
            cur, size = [], 0
        cur.extend(pc)
        size += psize
    if cur:
        parts.append(cur)
    return ["\n".join(p) for p in parts]


_DOC_CACHE: dict = {}
_DOC_CACHE_ORDER: list = []
_DOC_CACHE_MAX = 3
_DOC_LOCK = threading.Lock()


def _load_doc(ap: str, source: str) -> dict:
    """Read and analyse a document once; cached on (path, mtime_ns, size) so the part requests of a
    big file do not re-read or re-scan it."""
    st = os.stat(ap)
    if st.st_size > MAX_DOC_BYTES:
        raise DocTooLarge(f"{ap} is {st.st_size} bytes; the Reader limit is {MAX_DOC_BYTES}")
    key = (os.path.normcase(ap), st.st_mtime_ns, st.st_size)
    with _DOC_LOCK:
        hit = _DOC_CACHE.get(key)
        if hit is not None:
            _DOC_CACHE_ORDER.remove(key)
            _DOC_CACHE_ORDER.append(key)
            return hit
    with open(ap, "r", encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    ext = os.path.splitext(ap)[1].lower()
    fmt = "html" if ext in HTML_EXTS else "markdown"
    text = html_to_markdown_text(raw) if fmt == "html" else raw.replace("\r", "")
    parts = _split_parts(text)
    sections = []
    for pi, ptxt in enumerate(parts):
        for line in ptxt.split("\n"):
            m = HEAD13_RE.match(line.strip())
            if m:
                sections.append({"level": len(m.group(1)), "title": m.group(2).strip(), "part": pi})
    stem = os.path.splitext(os.path.basename(ap))[0]
    part_info = []
    for pi, ptxt in enumerate(parts):
        first = next((s["title"] for s in sections if s["part"] == pi), None)
        part_info.append({"index": pi, "title": first or f"Part {pi + 1}", "chars": len(ptxt)})
    doc = {
        "path": ap, "stem": stem, "filename": os.path.basename(ap), "source": source, "format": fmt,
        "bytes": st.st_size, "chars": len(text),
        "title": sections[0]["title"] if sections else stem,
        "tag_counts": count_tags(text),
        "sections": sections,
        "checking_items": extract_checking_items(text, stem),
        "parts": parts, "part_info": part_info,
    }
    with _DOC_LOCK:
        _DOC_CACHE[key] = doc
        _DOC_CACHE_ORDER.append(key)
        while len(_DOC_CACHE_ORDER) > _DOC_CACHE_MAX:
            _DOC_CACHE.pop(_DOC_CACHE_ORDER.pop(0), None)
    return doc


def get_doc_data(path: str, part: int = 0) -> dict:
    """Same structure as get_chapter_data (stem, filename, title, tag_counts, sections, checking items,
    available_tiers, html) plus: path, source, format, bytes, parts (table of contents), part, part_count.
    html is only the requested part; for a small file that is the whole file."""
    ap, source = resolve_doc_path(path)
    doc = _load_doc(ap, source)
    n = len(doc["parts"])
    if part < 0 or part >= n:
        raise IndexError(f"part {part} out of range (0..{n - 1})")
    tiers_path = os.path.join(TIERS_DIR, doc["stem"])
    available_tiers = []
    if source == "chapter" and os.path.isdir(tiers_path):
        available_tiers = [f for f in sorted(os.listdir(tiers_path)) if f.endswith(".json")]
    return {
        "path": doc["path"], "stem": doc["stem"], "filename": doc["filename"], "source": source,
        "format": doc["format"], "bytes": doc["bytes"], "chars": doc["chars"], "title": doc["title"],
        "tag_counts": doc["tag_counts"], "sections": doc["sections"],
        "checking_items": doc["checking_items"], "checking_count": len(doc["checking_items"]),
        "available_tiers": available_tiers,
        "parts": doc["part_info"], "part": part, "part_count": n,
        "html": render_markdown(doc["parts"][part]),
    }


def list_volumes() -> list:
    """Markdown/HTML files under VOLUMES_DIR. Empty list (not an error) when the folder is absent."""
    out = []
    if not os.path.isdir(VOLUMES_DIR):
        return out
    for root, dirs, files in os.walk(VOLUMES_DIR):
        dirs.sort()
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in RENDERABLE_EXTS:
                full = os.path.join(root, f)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    continue
                out.append({"path": full, "title": os.path.splitext(f)[0].replace("_", " "),
                            "rel": os.path.relpath(full, VOLUMES_DIR), "size": size})
    return out


def search_library(q: str = "", limit: int = 40) -> dict:
    """Registry documents (renderable types only) whose title or path contains every word of q."""
    words = [w for w in (q or "").lower().split() if w]
    docs = _registry()[1]
    hits = []
    total = 0
    for d in docs:
        if os.path.splitext(d["path"])[1].lower() not in RENDERABLE_EXTS:
            continue
        hay = ((d.get("title") or "") + " " + d["path"]).lower()
        if all(w in hay for w in words):
            total += 1
            if len(hits) < limit:
                hits.append({"path": d["path"], "title": d.get("title") or os.path.basename(d["path"]),
                             "kind": d.get("kind"), "area": d.get("area")})
    return {"docs": hits, "total": total, "volumes": list_volumes()}
