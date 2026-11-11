"""Obsidian-aware Markdown -> HTML for the Files viewer (Phase 1, SUITE_OVERHAUL_PLAN_2026-10-07; Claude GUI, Opus 5.5).

Safe by construction: every piece of source text is HTML-escaped; the only markup that reaches the page is markup
this module writes. Links can only be http(s)/mailto (opened in a new tab) or internal (data-path, handled by the
viewer). No raw HTML from the note is ever passed through.

Covers: YAML frontmatter (shown as properties), headings with anchors, fenced code, tables, nested and task lists,
blockquotes, Obsidian callouts (> [!note] Title, foldable +/-), horizontal rules, [[wiki links]] (with |alias and
#heading), ![[embeds]] (images inline, notes as a link card), Markdown links and images, bare URLs, **bold**,
*italic*, ~~strike~~, ==highlight==, `code`, #tags, and the project's [V]/[R]/[S] verification tags.

render(text, resolve=None, raw_url=None) -> {"html", "frontmatter", "tags", "links", "headings"}
  resolve(target) -> absolute path or None   (wiki-link / relative-link resolution, supplied by files_core)
  raw_url(path)   -> URL that serves the file (for images)
"""
import html
import re

from modules.reader_core import TAG_RE

FENCE_RE = re.compile(r"^(\s*)(```+|~~~+)\s*([\w+#.-]*)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
HR_RE = re.compile(r"^\s{0,3}(?:-{3,}|\*{3,}|_{3,})\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
CALLOUT_RE = re.compile(r"^\[!([A-Za-z-]+)\]([+-]?)\s*(.*)$")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")
OBS_TAG_RE = re.compile(r"(?<![\w&/#])#([A-Za-z_][\w/-]*)")


def _slug(s):
    s = re.sub(r"[^\w\s-]", "", s.lower(), flags=re.U)
    return re.sub(r"\s+", "-", s).strip("-")[:80]


def parse_frontmatter(text):
    """Return (dict, body). Accepts simple YAML: key: value, key: [a, b], and '- item' lists under a key."""
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    if lines[0].strip() != "---":
        return {}, text
    for end in range(1, min(len(lines), 200)):
        if lines[end].strip() in ("---", "..."):
            break
    else:
        return {}, text
    fm, key = {}, None
    for ln in lines[1:end]:
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        m = re.match(r"^([\w .-]+):\s*(.*)$", ln)
        if m and not ln.startswith((" ", "\t", "-")):
            key, val = m.group(1).strip(), m.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                fm[key] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            elif val:
                fm[key] = val.strip("'\"")
            else:
                fm[key] = []
        elif key is not None and ln.strip().startswith("- "):
            if not isinstance(fm.get(key), list):
                fm[key] = [fm[key]] if fm.get(key) else []
            fm[key].append(ln.strip()[2:].strip().strip("'\""))
    return fm, "\n".join(lines[end + 1:])


class _Ctx:
    def __init__(self, resolve, raw_url):
        self.resolve = resolve or (lambda t: None)
        self.raw_url = raw_url or (lambda p: "")
        self.tags, self.links, self.headings = set(), [], []


def _safe_url(u):
    u = u.strip()
    return u if re.match(r"^(https?://|mailto:)", u, re.I) else None


def _inline(text, ctx):
    """Inline markdown on RAW text. Generated markup is parked in placeholders so escaping can't touch it."""
    slots = []

    def park(markup):
        slots.append(markup)
        return f"\x00{len(slots) - 1}\x00"

    # code spans first: nothing inside them is markdown
    text = re.sub(r"(`+)(.+?)\1", lambda m: park(f'<code class="md-code">{html.escape(m.group(2))}</code>'), text)

    def wiki(m):
        embed, inner = m.group(1), m.group(2)
        target, alias = (inner.split("|", 1) + [None])[:2]
        name, _, heading = target.partition("#")
        label = alias or (name + (" › " + heading if heading else "") if name else heading)
        if embed and name.lower().endswith(IMAGE_EXTS):
            p = ctx.resolve(name.strip())
            ctx.links.append(name.strip())
            if p:
                width = f' width="{int(alias)}"' if alias and alias.isdigit() else ""
                return park(f'<img class="md-embed-img" src="{html.escape(ctx.raw_url(p), quote=True)}" alt="{html.escape(name)}"{width} loading="lazy">')
            return park(f'<span class="md-unresolved" title="No file named {html.escape(name, quote=True)}">⚠ {html.escape(name)}</span>')
        p = ctx.resolve(name.strip()) if name.strip() else None
        if name.strip():
            ctx.links.append(name.strip())
        cls = "md-wikilink" + (" md-embed-note" if embed else "") + ("" if p or not name.strip() else " md-unresolved")
        attrs = f' data-path="{html.escape(p, quote=True)}"' if p else ""
        if heading:
            attrs += f' data-heading="{html.escape(_slug(heading), quote=True)}"'
        title = ("Embedded note: " if embed else "") + (p or ("No note named " + name if name.strip() else "this note"))
        return park(f'<a class="{cls}" href="#"{attrs} title="{html.escape(title, quote=True)}">'
                    f'{"↪ " if embed else ""}{html.escape(label.strip())}</a>')

    text = re.sub(r"(!?)\[\[([^\]\n]+?)\]\]", wiki, text)

    def mdimg(m):
        alt, url = m.group(1), m.group(2).split(" ")[0].strip("<>")
        su = _safe_url(url)
        if su:
            return park(f'<img class="md-embed-img" src="{html.escape(su, quote=True)}" alt="{html.escape(alt)}" loading="lazy">')
        p = ctx.resolve(url.replace("%20", " "))
        if p:
            return park(f'<img class="md-embed-img" src="{html.escape(ctx.raw_url(p), quote=True)}" alt="{html.escape(alt)}" loading="lazy">')
        return park(f'<span class="md-unresolved">⚠ {html.escape(alt or url)}</span>')

    text = re.sub(r"!\[([^\]\n]*)\]\(([^)\n]+)\)", mdimg, text)

    def mdlink(m):
        label, url = m.group(1), m.group(2).split(" ")[0].strip("<>")
        su = _safe_url(url)
        if su:
            return park(f'<a class="md-ext" href="{html.escape(su, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a>')
        if url.startswith("#"):
            return park(f'<a class="md-wikilink" href="#" data-heading="{html.escape(_slug(url[1:]), quote=True)}">{html.escape(label)}</a>')
        p = ctx.resolve(url.replace("%20", " ").split("#")[0])
        ctx.links.append(url)
        if p:
            return park(f'<a class="md-wikilink" href="#" data-path="{html.escape(p, quote=True)}">{html.escape(label)}</a>')
        return park(f'<span class="md-unresolved" title="{html.escape(url, quote=True)}">{html.escape(label)}</span>')

    text = re.sub(r"(?<!!)\[([^\]\n]+)\]\(([^)\n]+)\)", mdlink, text)
    text = re.sub(r"(?<![\"'=(])\bhttps?://[^\s<>()\"']+[^\s<>()\"'.,;:!?]",
                  lambda m: park(f'<a class="md-ext" href="{html.escape(m.group(0), quote=True)}" target="_blank" '
                                 f'rel="noopener noreferrer">{html.escape(m.group(0))}</a>'), text)

    t = html.escape(text, quote=False)
    t = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"__(?=\S)(.+?)(?<=\S)__", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*(?=\S)(.+?)(?<=\S)\*(?![\*\w])", r"<em>\1</em>", t)
    t = re.sub(r"(?<![\w_])_(?=\S)(.+?)(?<=\S)_(?![\w_])", r"<em>\1</em>", t)
    t = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"<del>\1</del>", t)
    t = re.sub(r"==(?=\S)(.+?)(?<=\S)==", r'<mark class="md-mark">\1</mark>', t)

    def evid(m):
        kind = m.group("kind").upper()
        cls = "v" if "V" in kind else ("r" if "R" in kind else "s")
        return f'<span class="j-tag {cls}" title="{m.group(0)}">{m.group(0)}</span>'

    t = TAG_RE.sub(evid, t)

    def otag(m):
        ctx.tags.add(m.group(1))
        return f'<span class="md-tag">#{m.group(1)}</span>'

    t = OBS_TAG_RE.sub(otag, t)
    return re.sub(r"\x00(\d+)\x00", lambda m: slots[int(m.group(1))], t)


def _table(rows, ctx):
    def cells(r):
        r = r.strip()
        if r.startswith("|"):
            r = r[1:]
        if r.endswith("|") and not r.endswith("\\|"):
            r = r[:-1]
        return [c.strip() for c in re.split(r"(?<!\\)\|", r)]
    head = cells(rows[0])
    aligns = []
    for c in cells(rows[1]):
        aligns.append("center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "")
    out = ['<div class="md-table-wrap"><table class="md-table"><thead><tr>']
    for i, c in enumerate(head):
        a = f' style="text-align:{aligns[i]}"' if i < len(aligns) and aligns[i] else ""
        out.append(f"<th{a}>{_inline(c, ctx)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows[2:]:
        out.append("<tr>" + "".join(f"<td>{_inline(c, ctx)}</td>" for c in cells(r)) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def _list(lines, ctx):
    """Nested lists by indentation. lines: raw list lines (with continuation lines already joined)."""
    out, stack = [], []           # stack of (indent, tag)
    for ln in lines:
        m = LIST_RE.match(ln)
        indent = len(m.group(1).replace("\t", "    "))
        tag = "ol" if m.group(2)[0].isdigit() else "ul"
        while stack and indent < stack[-1][0]:
            out.append(f"</li></{stack.pop()[1]}>")
        if not stack or indent > stack[-1][0]:
            start = ""
            if tag == "ol" and m.group(2)[:-1].isdigit() and m.group(2)[:-1] != "1":
                start = f' start="{int(m.group(2)[:-1])}"'
            out.append(f'<{tag} class="md-list"{start}>')
            stack.append((indent, tag))
        else:
            out.append("</li>")
        body = m.group(3)
        task = re.match(r"^\[( |x|X)\]\s+(.*)$", body)
        if task:
            checked = " checked" if task.group(1) in "xX" else ""
            out.append(f'<li class="md-task"><input type="checkbox" disabled{checked}> {_inline(task.group(2), ctx)}')
        else:
            out.append(f"<li>{_inline(body, ctx)}")
    while stack:
        out.append(f"</li></{stack.pop()[1]}>")
    return "".join(out)


def _blocks(lines, ctx):
    out, i, n = [], 0, len(lines)
    while i < n:
        raw = lines[i]
        line = raw.strip()
        if not line:
            i += 1
            continue
        fm = FENCE_RE.match(raw)
        if fm:
            fence, lang, body = fm.group(2), fm.group(3), []
            i += 1
            while i < n and not lines[i].strip().startswith(fence[0] * len(fence)):
                body.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{html.escape(lang, quote=True)}"' if lang else ""
            out.append(f'<pre class="md-pre"><code{cls}>{html.escape(chr(10).join(body))}</code></pre>')
            continue
        hm = HEADING_RE.match(line)
        if hm and not line.startswith("#!"):
            lvl, txt = len(hm.group(1)), hm.group(2)
            sid = _slug(txt)
            ctx.headings.append({"level": lvl, "text": txt, "id": sid})
            out.append(f'<h{lvl} class="md-h" id="h-{sid}">{_inline(txt, ctx)}</h{lvl}>')
            i += 1
            continue
        if HR_RE.match(raw):
            out.append('<hr class="md-hr">')
            i += 1
            continue
        if line.startswith(">"):
            q = []
            while i < n and lines[i].strip().startswith(">"):
                s = lines[i].strip()[1:]
                q.append(s[1:] if s.startswith(" ") else s)
                i += 1
            co = CALLOUT_RE.match(q[0].strip()) if q else None
            if co:
                kind = co.group(1).lower()
                title = co.group(3) or kind.capitalize()
                inner = _blocks(q[1:], ctx)
                fold = co.group(2)
                if fold:
                    out.append(f'<details class="md-callout md-callout-{html.escape(kind, quote=True)}"{" open" if fold == "+" else ""}>'
                               f'<summary class="md-callout-title">{_inline(title, ctx)}</summary>{inner}</details>')
                else:
                    out.append(f'<div class="md-callout md-callout-{html.escape(kind, quote=True)}">'
                               f'<div class="md-callout-title">{_inline(title, ctx)}</div>{inner}</div>')
            else:
                out.append(f'<blockquote class="md-quote">{_blocks(q, ctx)}</blockquote>')
            continue
        if "|" in line and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            rows = [lines[i], lines[i + 1]]
            i += 2
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(lines[i])
                i += 1
            out.append(_table(rows, ctx))
            continue
        if LIST_RE.match(raw):
            items = []
            while i < n and lines[i].strip():
                if LIST_RE.match(lines[i]):
                    items.append(lines[i].rstrip())
                elif items and (lines[i].startswith((" ", "\t"))):
                    items[-1] += " " + lines[i].strip()           # continuation of the previous item
                else:
                    break
                i += 1
            # a blank line followed by another list item continues the same list
            while i + 1 < n and not lines[i].strip() and LIST_RE.match(lines[i + 1]):
                i += 1
                while i < n and lines[i].strip() and (LIST_RE.match(lines[i]) or lines[i].startswith((" ", "\t"))):
                    if LIST_RE.match(lines[i]):
                        items.append(lines[i].rstrip())
                    else:
                        items[-1] += " " + lines[i].strip()
                    i += 1
            out.append(_list(items, ctx))
            continue
        para = []
        while i < n and lines[i].strip():
            s = lines[i]
            if para and (FENCE_RE.match(s) or HEADING_RE.match(s.strip()) or s.strip().startswith(">")
                         or LIST_RE.match(s) or HR_RE.match(s)):
                break
            para.append(s.strip())
            i += 1
        if not para:                      # a line no branch took (never loop forever)
            para.append(line)
            i += 1
        if len(para) == 1 and re.fullmatch(r"!\[\[[^\]]+\]\]", para[0]):
            out.append(f'<div class="md-embed">{_inline(para[0], ctx)}</div>')
        else:
            out.append(f'<p class="md-p">{"<br>".join(_inline(p, ctx) for p in para)}</p>')
    return "".join(out)


def _frontmatter_html(fm, ctx):
    if not fm:
        return ""
    rows = []
    for k, v in fm.items():
        if k.lower() in ("tags", "tag") and v:
            vals = v if isinstance(v, list) else re.split(r"[,\s]+", v)
            for t in vals:
                if t:
                    ctx.tags.add(t.lstrip("#"))
            val = " ".join(f'<span class="md-tag">#{html.escape(t.lstrip("#"))}</span>' for t in vals if t)
        elif isinstance(v, list):
            val = ", ".join(_inline(x, ctx) for x in v)
        else:
            val = _inline(str(v), ctx)
        rows.append(f'<tr><th>{html.escape(k)}</th><td>{val}</td></tr>')
    return f'<table class="md-props">{"".join(rows)}</table>'


def render(text, resolve=None, raw_url=None, with_frontmatter=True):
    ctx = _Ctx(resolve, raw_url)
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    fm, body = parse_frontmatter(text) if with_frontmatter else ({}, text)
    head = _frontmatter_html(fm, ctx)
    body_html = _blocks(body.split("\n"), ctx)
    return {"html": head + body_html, "frontmatter": fm, "tags": sorted(ctx.tags),
            "links": ctx.links, "headings": ctx.headings}


def wiki_targets(text):
    """Every [[target]] (and ![[embed]]) name in raw text, lower-cased, without |alias or #heading. For the link index."""
    out = []
    for m in re.finditer(r"!?\[\[([^\]\n]+?)\]\]", text or ""):
        name = m.group(1).split("|", 1)[0].split("#", 1)[0].strip()
        if name:
            out.append(name.replace("\\", "/").split("/")[-1].lower().removesuffix(".md"))
    return out
