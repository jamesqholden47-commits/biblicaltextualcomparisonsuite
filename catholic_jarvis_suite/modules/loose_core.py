"""
Loose Ends: one register of everything the AIs produced, and which of it is still loose.
(Claude GUI, Opus 5.5, 2026-10-06. Integrator-owned module.)

The question it answers: "Of the hundreds of reports, dossiers and dissertations we made, which ones
never made it anywhere, what do they still owe, and which of them are really the same thing twice?"

For every document under the roots (markdown, HTML, Word, PDF) it records:
  - what it is: title, area, kind (SUBJECT / INFRASTRUCTURE / PROVENANCE, Rule 13), size, dates;
  - who made it: the Antigravity or Claude session whose write call created or edited it;
  - what it still owes: the items under its own "still needs checking", "FETCH LIST", "OPEN QUESTIONS",
    "TODO", "next steps", "pending", "unresolved" headings;
  - whether it went anywhere: is its content found inside a canonical book (sampled passages searched
    in the master dissertation, the Mexico books, the Scriptorium), is it referenced by name in another
    document, and was it mentioned again in a later conversation;
  - its variants: byte-identical copies and same-title versions;
  - its thread: documents that share rare title words are grouped, and the Question Ledger's questions
    with the same words are attached, so one topic shows its documents and its open questions together.
A priority score ranks SUBJECT documents that are not integrated, carry open items, have variants and
are recent. James's own marks (open, merged, superseded, parked, done, ignore, with a note) are stored
by a stable id and survive every rebuild.

Nothing here writes outside data/loose_*.json. Nothing is deleted or moved. No network, no LLM.
"""
import datetime
import hashlib
import json
import math
import os
import re
import threading
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_HERE, "data")
REGISTRY_FILE = os.path.join(DATA_DIR, "loose_registry.json")
STATUS_FILE = os.path.join(DATA_DIR, "loose_status.json")
CONFIG_FILE = os.path.join(DATA_DIR, "loose_config.json")

PROJECT = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism"
DEFAULT_CONFIG = {
    "roots": [
        [PROJECT, "Project"],
        [r"C:\Users\Elation\Mexico_Protestantism_Study", "Mexico study"],
        [r"C:\Users\Elation\Scholar_Decade_Plan", "Scriptorium"],
        [r"C:\Users\Elation\.gemini\antigravity\brain", "Antigravity artifacts"],
    ],
    # Canonical books: a document whose sampled passages are found inside one of these is "integrated".
    "targets": [
        PROJECT + r"\01_MASTER_DISSERTATION\Master_Dissertation_History_Proves_Catholicism_2026-07-04.md",
        r"C:\Users\Elation\Mexico_Protestantism_Study\05_READERS_EDITION\THE_CATHOLIC_CASE_Readers_Edition.md",
        r"C:\Users\Elation\Mexico_Protestantism_Study\04_CONSOLIDATED\THE_CATHOLIC_CASE_Consolidated_Dissertation.md",
        r"C:\Users\Elation\Mexico_Protestantism_Study\04_CONSOLIDATED\APPENDIX_Source_Dossiers_Verbatim.md",
        r"C:\Users\Elation\Scholar_Decade_Plan\The_Ten_Year_Scriptorium.md",
    ],
    # Lower-case path fragments never registered (archives, backups, raw downloads, code, caches).
    "skip": ["\\_session_transcripts", "\\07_archive_old_process", "backup", "\\_build_scripts_", "\\_previous_",
             "superseded", "\\raw\\", "\\_raw\\", "\\__pycache__", "\\.system_generated", "\\node_modules", "\\.git",
             "\\98_archives", "\\rabbinic_corpus_sefaria", "catholic_jarvis_suite\\data", "catholic_jarvis_suite\\static",
             "catholic_jarvis_suite\\tests", "\\audio_cache", "\\scratch\\",
             "\\10_volumes\\"],   # the Bookbinder's own outputs; assembled volumes are targets instead
    "exts": [".md", ".html", ".docx", ".pdf"],
}

STATUSES = ("open", "merged", "superseded", "parked", "done", "ignore")
OPEN_HEADING = re.compile(
    r"^(?:#{1,6}\s*)?(?:\d+[.)]\s*)?\**\s*(before using this in public|what still needs checking|still needs checking|"
    r"needs checking|fetch list|open questions|open issues|to ?do|next steps|next actions|pending|unresolved|"
    r"what remains|loose ends|follow[- ]?ups?|still to do|remaining work|gaps)\b[^\n]*$", re.I)
ANY_HEADING = re.compile(r"^(#{1,6})\s+\S|^[A-Z][A-Z /&-]{3,40}:\s*$")
ITEM_LINE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)")
NONE_ITEM = re.compile(r"^\s*(none|n/?a|nothing( pending)?|—|-)\s*\.?\s*$", re.I)
FILENAME_RE = re.compile(r"[A-Za-z0-9_\-.()\[\]]{3,160}\.(?:md|html|docx|pdf)\b", re.I)
WORD_RE = re.compile(r"[a-záéíóúñüα-ωא-ת]{4,}", re.I)
TITLE_STOP = set("""
dossier dossiers report reports chapter chapters edition editions natural language dissertation dissertations final
draft drafts synthesis master analysis research catholic readers reader response responses debate debates
complete full version update updated notes note session sessions summary overview study guide guides part parts
section sections index readme file files exhaustive beyond basics academic deep dive answer answers against
from with into over under about this that these those their there what when where which while your ours mine
history proves catholicism project review reviews verify verified verification audit audits plan plans
workflow subagent subagents fleet track tracks prompt prompts claude gemini antigravity opus sonnet flash
2026 2025 july august september october consolidated appendix front matter readme handoff
""".split())
_LOCK = threading.RLock()


# ----------------------------------------------------------------------------- small helpers

def _replace_retry(tmp, path, tries=8):
    """os.replace with a short retry: on Windows an antivirus or indexer can hold the target for a
    moment and the replace fails with PermissionError (seen once in tests/test_ledger, 2026-10-06)."""
    import time as _t
    for i in range(tries):
        try:
            return os.replace(tmp, path)
        except PermissionError:
            if i == tries - 1:
                raise
            _t.sleep(0.05 * (i + 1))

def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def doc_id(path):
    return hashlib.sha1(os.path.normcase(os.path.abspath(path)).encode("utf-8")).hexdigest()[:16]


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if os.path.exists(CONFIG_FILE):
        try:
            cfg.update(_read_json(CONFIG_FILE))
        except Exception:
            pass
    return cfg


def _atomic_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as w:
        json.dump(obj, w, ensure_ascii=False, indent=1)
    _replace_retry(tmp, path)


def norm_text(s):
    s = s.lower()
    s = re.sub(r"[*_`#>\[\]()|]", " ", s)
    s = re.sub(r"[“”\"'’‘]", "", s)
    return re.sub(r"\s+", " ", s)


def read_text(path, limit=None):
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".md", ".html", ".txt"):
        return ""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            t = fh.read(limit) if limit else fh.read()
    except OSError:
        return ""
    if ext == ".html":
        t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S | re.I)
        t = re.sub(r"<[^>]+>", " ", t)
    return t


def title_of(path, text):
    for line in text.splitlines()[:40]:
        m = re.match(r"^#\s+(.+)", line.strip())
        if m:
            return re.sub(r"[*_`]", "", m.group(1)).strip()[:200]
    m = re.search(r"<title>(.*?)</title>", text[:3000], re.I | re.S)
    if m:
        return m.group(1).strip()[:200]
    return os.path.splitext(os.path.basename(path))[0].replace("_", " ")


# ----------------------------------------------------------------------------- open items
def extract_open_items(text, max_items=40):
    """Items listed under a document's own 'still needs checking / FETCH LIST / OPEN QUESTIONS / TODO /
    next steps / pending / unresolved' headings. Code blocks are ignored (Rule 14)."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    lines = text.splitlines()
    items, i = [], 0
    while i < len(lines):
        line = lines[i].strip()
        m = OPEN_HEADING.match(line)
        if m and len(line) < 140:
            label = m.group(1).lower()
            level = len(re.match(r"^(#*)", line).group(1)) or 9
            # inline content after "FETCH LIST:" on the same line
            tail = line.split(":", 1)[1].strip() if ":" in line and not line.startswith("#") else ""
            if tail and not NONE_ITEM.match(tail):
                items.append({"section": label, "text": tail[:400]})
            j = i + 1
            while j < len(lines):
                l2 = lines[j]
                h = re.match(r"^(#{1,6})\s+\S", l2)
                if (h and len(h.group(1)) <= level) or (level == 9 and (h or re.match(r"^[A-Z][A-Z /&-]{3,40}:\s*$", l2.strip()))):
                    break
                im = ITEM_LINE.match(l2)
                if im and not NONE_ITEM.match(im.group(1)):
                    items.append({"section": label, "text": im.group(1)[:400]})
                j += 1
            i = j
            if len(items) >= max_items:
                break
            continue
        i += 1
    return items[:max_items]


# ----------------------------------------------------------------------------- integration check
def sample_passages(text, n=6, words=12):
    """Distinctive word windows from evenly spaced prose paragraphs (not headings, tables or lists)."""
    paras = [p for p in re.split(r"\n\s*\n", text)
             if len(p) > 200 and not p.lstrip().startswith(("#", "|", "-", "*", ">", "```", "<"))]
    if not paras:
        return []
    step = max(1, len(paras) // n)
    out = []
    for p in paras[::step][:n]:
        w = norm_text(p).split()
        if len(w) >= words + 8:
            mid = len(w) // 2
            out.append(" ".join(w[mid:mid + words]))
    return out


def load_targets(cfg):
    """The canonical books, plus every volume the Bookbinder has assembled (10_VOLUMES/<V>/VOLUME_*.md),
    so a source synthesised into a volume stops counting as loose."""
    import glob
    paths = list(cfg["targets"]) + sorted(glob.glob(os.path.join(PROJECT, "10_VOLUMES", "*", "VOLUME_*.md")))
    blobs = {}
    for t in paths:
        if os.path.exists(t):
            blobs[t] = norm_text(read_text(t))
    return blobs


def integration_of(passages, targets, own_path):
    """Which canonical book contains at least two of this document's sampled passages."""
    hits = []
    if len(passages) < 2:
        return hits
    for tpath, blob in targets.items():
        if os.path.normcase(tpath) == os.path.normcase(own_path):
            continue
        found = sum(1 for p in passages if p in blob)
        if found >= 2:
            hits.append({"target": tpath, "found": found, "of": len(passages)})
    return hits


# ----------------------------------------------------------------------------- producers
def scan_producers():
    """path(normcase) -> {surface, sessions, first, last, edits} from Antigravity write tool calls and
    Claude Write/Edit tool uses. Read from the raw logs (both stores), written nowhere."""
    import glob
    prod = defaultdict(lambda: {"sessions": set(), "surfaces": set(), "first": None, "last": None, "edits": 0})

    def add(p, surface, sid, ts):
        if not p:
            return
        k = os.path.normcase(p.replace("file:///", "").replace("/", "\\"))
        r = prod[k]
        r["sessions"].add(f"{surface}:{sid[:8]}")
        r["surfaces"].add(surface)
        if ts:
            r["first"] = min(r["first"] or ts, ts)
            r["last"] = max(r["last"] or ts, ts)
        r["edits"] += 1

    ag = r"C:\Users\Elation\.gemini\antigravity\brain"
    for f in glob.glob(os.path.join(ag, "*", ".system_generated", "logs", "transcript_full.jsonl")):
        sid = f.split(os.sep)[-4]
        with open(f, "rb") as fh:
            for raw in fh:
                if b"TargetFile" not in raw:
                    continue
                try:
                    d = json.loads(raw)
                except Exception:
                    continue
                for tc in d.get("tool_calls") or []:
                    if tc.get("name") in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
                        add((tc.get("args") or {}).get("TargetFile"), "AG", sid, d.get("created_at"))
    cl = r"C:\Users\Elation\.claude\projects"
    for f in glob.glob(os.path.join(cl, "**", "*.jsonl"), recursive=True):
        sid = os.path.basename(f)[:-6]
        with open(f, "rb") as fh:
            for raw in fh:
                if b'"file_path"' not in raw or b'"tool_use"' not in raw:
                    continue
                try:
                    d = json.loads(raw)
                except Exception:
                    continue
                m = d.get("message") if isinstance(d.get("message"), dict) else {}
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit", "NotebookEdit"):
                        add((b.get("input") or {}).get("file_path"), "CL", sid, d.get("timestamp"))
    return {k: {"sessions": sorted(v["sessions"]), "surfaces": sorted(v["surfaces"]), "first": v["first"],
                "last": v["last"], "edits": v["edits"]} for k, v in prod.items()}


PRODUCERS_FILE = os.path.join(DATA_DIR, "loose_producers.json")


def cached_producers():
    """scan_producers() reads ~800 MB of logs; reuse the last result while the log fingerprint
    (path|size|mtime of every source log, the same key log_reader uses) is unchanged."""
    try:
        from modules import log_reader
        cl, ag = log_reader._sources()
        fp = log_reader._fingerprint(cl + ag)
    except Exception:
        fp = None
    if fp and os.path.exists(PRODUCERS_FILE):
        try:
            c = _read_json(PRODUCERS_FILE)
            if c.get("fingerprint") == fp:
                return c["producers"]
        except Exception:
            pass
    try:
        prod = scan_producers()
    except Exception:
        return {}
    if fp:
        _atomic_json(PRODUCERS_FILE, {"fingerprint": fp, "producers": prod})
    return prod


# ----------------------------------------------------------------------------- kind (Rule 13)
_INFRA_HINTS = ("catholic_jarvis_suite", "09_apps_catholicjarvis", "02_control_and_state", "_worker_inbox",
                "_log_analysis", "_worker_spec", "web_app", "ocr", "pdf inventory", "handoff", "boot_header",
                "taskboard", "routing_doctrine", "checkpoint", "runlog", "battleplan", "overnight", "implementation_plan",
                "drift", "gemini.md", "claude.md", "readme", "walkthrough", "task.md")


_PROVENANCE_HINTS = ("\\_session_transcripts", "\\06_source_material\\", "mexico_protestantism_study\\_sources\\",
                     "\\04_consolidated\\_sources\\", "transcript")
_INFRA_DIRS = ("\\02_control_and_state\\", "\\_handoffs_archive\\", "\\.claude\\", "\\04_bibliographies_and_fetch\\",
               "\\_cowork_synthesis", "\\08_intake\\")


def kind_of(path, corpus_kinds, not_dissertation):
    """Rule 13 kind. Path evidence first (it is unambiguous), then the Rule 13 manifest and the corpus
    index, then infrastructure word hints. Content words like 'subagent' are never used (Rule 13)."""
    pl = path.lower()
    base = os.path.basename(pl)
    if any(h in pl for h in _PROVENANCE_HINTS) or base.startswith(("antigravity conversation", "ag_conversation", "claude_session")):
        return "PROVENANCE"
    if os.path.normcase(path) in not_dissertation or any(h in pl for h in _INFRA_DIRS):
        return "INFRASTRUCTURE"
    parent = os.path.basename(os.path.dirname(pl))
    if parent == "_project_historyprovescatholicism" and base.startswith("_"):
        return "INFRASTRUCTURE"   # root control files: _AG_HANDOFF, _BOOT_HEADER, _LIVE_CHECKPOINT ...
    k = corpus_kinds.get(os.path.normcase(path))
    if k:
        return k
    if any(h in pl for h in _INFRA_HINTS):
        return "INFRASTRUCTURE"
    return "SUBJECT"


def _corpus_kinds():
    p = os.path.join(DATA_DIR, "corpus_index.json")
    out = {}
    try:
        for f in _read_json(p).get("files", []):
            if f.get("path") and f.get("kind"):
                out[os.path.normcase(f["path"])] = f["kind"]
    except Exception:
        pass
    return out


def _not_dissertation():
    for p in (PROJECT + r"\02_CONTROL_AND_STATE\_MEASUREMENTS\_NOT_DISSERTATION_CONTENT.json",
              PROJECT + r"\02_CONTROL_AND_STATE\_NOT_DISSERTATION_CONTENT.json"):
        if os.path.exists(p):
            try:
                d = _read_json(p)
                ex = d.get("exclude", d if isinstance(d, list) else [])
                return {os.path.normcase(x if os.path.isabs(x) else os.path.join(PROJECT, x)) for x in ex if isinstance(x, str)}
            except Exception:
                return set()
    return set()


# ----------------------------------------------------------------------------- threads
def title_tokens(title, path):
    base = os.path.splitext(os.path.basename(path))[0]
    words = {w.lower() for w in WORD_RE.findall(f"{title} {base.replace('_', ' ')}")}
    return {w for w in words if w not in TITLE_STOP and not w.isdigit()}


def build_threads(docs, questions, sim=0.30, top=8, max_df_frac=0.06):
    """Leader clustering, oldest document first: a document joins the thread whose top words it most
    resembles (idf-weighted Jaccard >= sim), otherwise it starts a new thread. Unlike linking any two
    documents that share words, this cannot chain unrelated topics into one giant group (the first
    version did: 298 documents in one thread). Only SUBJECT documents are threaded. Questions attach
    when they contain >= 2 of a thread's top 4 words."""
    pool = [d for d in docs if d["kind"] == "SUBJECT"]
    df = Counter()
    for d in pool:
        df.update(d["_tokens"])
    n = max(1, len(pool))
    useful = {w for w, c in df.items() if 2 <= c <= max(3, int(n * max_df_frac))}
    idf = {w: math.log(n / df[w]) for w in useful}
    threads = []                      # each: {"counter": Counter, "members": [doc]}
    for d in sorted(pool, key=lambda d: d["mtime"]):
        toks = d["_tokens"] & useful
        if len(toks) < 2:
            continue
        best, best_s = None, 0.0
        for t in threads:
            # Compare against the thread's CORE: words held by a strict majority of its members.
            # Comparing against everything the members ever used lets a chain of overlapping topics
            # walk the thread away from its subject (caught by test_FALSIFY_threads_do_not_chain).
            m = len(t["members"])
            tops = {w for w, c in t["counter"].items() if c * 2 > m} or {w for w, _ in t["counter"].most_common(4)}
            inter = sum(idf[w] for w in toks & tops)
            union = sum(idf[w] for w in toks | tops)
            s = inter / union if union else 0.0
            if s > best_s:
                best, best_s = t, s
        if best is not None and best_s >= sim:
            best["counter"].update(toks)
            best["members"].append(d)
        else:
            threads.append({"counter": Counter(toks), "members": [d]})
    out = []
    for t in threads:
        if len(t["members"]) < 2:
            continue
        ids = [m["id"] for m in t["members"]]
        label = [w for w, _ in t["counter"].most_common(4)]
        out.append({"id": hashlib.sha1("|".join(sorted(ids)).encode()).hexdigest()[:12], "label": label, "doc_ids": ids})
    for t in out:
        lab = set(t["label"])
        t["question_ids"] = [q["id"] for q in questions
                             if len(lab & {w.lower() for w in WORD_RE.findall(q.get("text", ""))}) >= 2][:60]
    return out


def _ledger_questions():
    p = os.path.join(DATA_DIR, "ledger_questions.json")
    try:
        d = _read_json(p)
        qs = (d.get("items") or d.get("questions") or []) if isinstance(d, dict) else d
        return [{"id": q.get("id"), "text": q.get("text", "")[:600], "ts": q.get("ts"), "surface": q.get("surface"),
                 "missed": q.get("missed", False)} for q in qs if isinstance(q, dict)]
    except Exception:
        return []


# ----------------------------------------------------------------------------- scan
def scan_documents(cfg):
    skip = [s.lower() for s in cfg["skip"]]
    exts = set(cfg["exts"])
    out = []
    for root, area in cfg["roots"]:
        if not os.path.isdir(root):
            continue
        brain = "antigravity\\brain" in root.lower()
        for dp, dns, fns in os.walk(root):
            dpl = dp.lower() + "\\"
            if any(s in dpl for s in skip):
                dns[:] = []
                continue
            if brain and dp.count(os.sep) - root.count(os.sep) > 1:
                dns[:] = []   # only top-level artifacts of each Antigravity conversation
                continue
            for fn in fns:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in exts or fn.endswith((".metadata.json",)):
                    continue
                p = os.path.join(dp, fn)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                sub = os.path.relpath(dp, root).split(os.sep)[0] if dp != root else ""
                out.append({"path": p, "area": area, "subarea": sub if not brain else "", "ext": ext,
                            "bytes": st.st_size, "mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="minutes")})
    return out


def rebuild(cfg=None, producers=None, messages=None, targets=None):
    """Full rebuild of data/loose_registry.json. Never touches data/loose_status.json."""
    import time
    t0 = time.time()
    cfg = cfg or load_config()
    docs = scan_documents(cfg)
    corpus_kinds, not_diss = _corpus_kinds(), _not_dissertation()
    if producers is None:
        producers = cached_producers()
    targets = load_targets(cfg) if targets is None else targets
    if messages is None:
        try:
            from modules.log_reader import load_messages
            messages = load_messages()
        except Exception:
            messages = []

    names = {}
    hashes = defaultdict(list)
    for d in docs:
        d["id"] = doc_id(d["path"])
        names.setdefault(os.path.basename(d["path"]).lower(), []).append(d["id"])
        text = read_text(d["path"])
        d["title"] = title_of(d["path"], text) if text else os.path.splitext(os.path.basename(d["path"]))[0].replace("_", " ")
        d["kind"] = kind_of(d["path"], corpus_kinds, not_diss)
        d["open_items"] = extract_open_items(text) if text else []
        d["tags"] = {"V": len(re.findall(r"\[V\b", text)), "R": len(re.findall(r"\[R\b", text)), "S": len(re.findall(r"\[S\b", text))}
        d["words"] = len(text.split()) if text else None
        d["partial"] = bool(text) and "WORKER COMPLETE" not in text[-400:] and "_WORKER_INBOX" in d["path"] and d["path"].lower().endswith("_report.md")
        d["_text"] = text
        d["_passages"] = sample_passages(text) if text else []
        d["_tokens"] = title_tokens(d["title"], d["path"])
        if d["bytes"] < 30_000_000:
            try:
                with open(d["path"], "rb") as fh:
                    hashes[hashlib.sha1(fh.read()).hexdigest()].append(d["id"])
            except OSError:
                pass
        pr = producers.get(os.path.normcase(d["path"]))
        d["producer"] = pr or None

    by_id = {d["id"]: d for d in docs}
    # references by file name, in other documents and in conversations
    refs_in_docs = defaultdict(set)
    for d in docs:
        if not d["_text"]:
            continue
        for m in set(x.lower() for x in FILENAME_RE.findall(d["_text"])):
            for tid in names.get(os.path.basename(m), []):
                if tid != d["id"]:
                    refs_in_docs[tid].add(d["id"])
    chat_refs = defaultdict(list)
    for m in messages:
        t = m.get("text", "")
        if "." not in t:
            continue
        for fnm in set(x.lower() for x in FILENAME_RE.findall(t)):
            for tid in names.get(os.path.basename(fnm), []):
                chat_refs[tid].append(m.get("ts") or "")
    # variants: same normalised title
    def tnorm(t):
        t = t.lower().replace("'", "").replace("’", "")
        t = re.sub(r"\b(19|20)\d\d[-_.]?\d\d[-_.]?\d\d\b|\bv\d+\b|\b(final|draft|copy|natural language|readers? edition|consolidated|expanded|revised|updated)\b", " ", t)
        return re.sub(r"[^a-z0-9א-תα-ω]+", " ", t).strip()
    title_groups = defaultdict(list)
    for d in docs:
        k = tnorm(d["title"])
        if len(k) >= 12:
            title_groups[k].append(d["id"])

    for d in docs:
        d["integrated_into"] = integration_of(d["_passages"], targets, d["path"]) if d["kind"] == "SUBJECT" else []
        d["referenced_by"] = sorted(refs_in_docs.get(d["id"], ()))[:30]
        cr = sorted(x for x in chat_refs.get(d["id"], []) if x)
        d["chat_mentions"] = {"count": len(cr), "last": cr[-1] if cr else None}
        dup = []
        for h, ids in hashes.items():
            if d["id"] in ids and len(ids) > 1:
                dup = [i for i in ids if i != d["id"]]
        d["exact_copies"] = dup
        d["title_variants"] = [i for i in title_groups.get(tnorm(d["title"]), []) if i != d["id"]][:20]

    questions = _ledger_questions()
    threads = build_threads(docs, questions)
    thread_of = {}
    for t in threads:
        for i in t["doc_ids"]:
            thread_of[i] = t["id"]
    now = datetime.datetime.now()
    for d in docs:
        d["thread"] = thread_of.get(d["id"])
        d["score"] = priority(d, now)
        for k in ("_text", "_passages", "_tokens"):
            d.pop(k, None)
    for t in threads:
        mem = [by_id[i] for i in t["doc_ids"]]
        t["n_docs"] = len(mem)
        t["n_integrated"] = sum(1 for m in mem if m["integrated_into"])
        t["n_open_items"] = sum(len(m["open_items"]) for m in mem)
        t["first"] = min(m["mtime"] for m in mem)
        t["last"] = max(m["mtime"] for m in mem)
        t["n_questions"] = len(t["question_ids"])
        t["n_missed_questions"] = sum(1 for q in questions if q["id"] in set(t["question_ids"]) and q.get("missed"))
        # A thread is loose when its documents are not in any book and its questions look missed. Items
        # still owed count, but less: a fully integrated chapter pair with a checklist is not a loose end.
        n_loose = len(mem) - t["n_integrated"]
        t["score"] = round(2.0 * n_loose + 0.04 * min(t["n_open_items"], 60) + 1.5 * t["n_missed_questions"]
                           + 0.3 * min(t["n_questions"], 10) + math.log2(1 + len(mem)), 2)
    threads.sort(key=lambda t: -t["score"])
    reg = {"built_at": _now(), "seconds": round(time.time() - t0, 1), "config": cfg,
           "targets_found": sorted(targets), "n_docs": len(docs), "docs": docs, "threads": threads,
           "questions": {q["id"]: q for q in questions if any(q["id"] in t["question_ids"] for t in threads)}}
    os.makedirs(DATA_DIR, exist_ok=True)
    with _LOCK:
        _atomic_json(REGISTRY_FILE, reg)
    return reg


def priority(d, now):
    """Higher = looser. Only SUBJECT documents get a full score; infrastructure and provenance are
    tracked but never pushed to the top."""
    s = 0.0
    if d["kind"] != "SUBJECT":
        return round(-1 + min(len(d["open_items"]), 5) * 0.1, 2)
    if not d["integrated_into"]:
        s += 3
    if not d["referenced_by"]:
        s += 1
    s += min(len(d["open_items"]), 12) * 0.35
    if d["exact_copies"] or d["title_variants"]:
        s += 1
    try:
        age = (now - datetime.datetime.fromisoformat(d["mtime"])).days
    except Exception:
        age = 999
    s += 2 if age <= 7 else 1 if age <= 30 else 0
    s += min(math.log10(max(d["bytes"], 1)) - 3, 2) if d["bytes"] > 1000 else 0
    if d.get("partial"):
        s += 1.5
    return round(s, 2)


# ----------------------------------------------------------------------------- read side
def load_registry(build_if_missing=True):
    with _LOCK:
        if os.path.exists(REGISTRY_FILE):
            return _read_json(REGISTRY_FILE)
    return rebuild() if build_if_missing else {"docs": [], "threads": [], "n_docs": 0}


def load_status():
    if os.path.exists(STATUS_FILE):
        try:
            return _read_json(STATUS_FILE)
        except Exception:
            pass
    return {"version": 1, "marks": {}}


def set_mark(did, status, note="", merged_into=""):
    if not re.fullmatch(r"[0-9a-f]{16}", did or ""):
        raise ValueError("bad id")
    if status not in STATUSES + ("unreviewed",):
        raise ValueError("bad status")
    with _LOCK:
        st = load_status()
        if status == "unreviewed":
            st["marks"].pop(did, None)
        else:
            st["marks"][did] = {"status": status, "note": (note or "")[:1000],
                                "merged_into": (merged_into or "")[:500], "at": _now()}
        _atomic_json(STATUS_FILE, st)
        return st["marks"].get(did)


def query(reg, status_marks, area=None, kind=None, text=None, mark=None, signal=None, thread=None,
          changed_since=None, sort="score", limit=100, offset=0):
    docs = reg.get("docs", [])
    words = [w.lower() for w in (text or "").split() if w]
    out = []
    for d in docs:
        m = status_marks.get(d["id"], {})
        st = m.get("status", "unreviewed")
        if area and d["area"] != area:
            continue
        if kind and d["kind"] != kind:
            continue
        if mark and st not in mark.split(","):
            continue
        if thread and d.get("thread") != thread:
            continue
        if changed_since and d["mtime"] < changed_since:
            continue
        if signal == "not_integrated" and (d["kind"] != "SUBJECT" or d["integrated_into"]):
            continue
        if signal == "open_items" and not d["open_items"]:
            continue
        if signal == "variants" and not (d["exact_copies"] or d["title_variants"]):
            continue
        if signal == "never_mentioned" and (d["referenced_by"] or d["chat_mentions"]["count"]):
            continue
        if signal == "partial" and not d.get("partial"):
            continue
        if words:
            hay = f"{d['title']} {d['path']} " + " ".join(i["text"] for i in d["open_items"])
            hay = hay.lower()
            if not all(w in hay for w in words):
                continue
        out.append(dict(d, status=st, mark=m or None))
    key = {"score": lambda d: -d["score"], "newest": lambda d: d["mtime"], "oldest": lambda d: d["mtime"],
           "size": lambda d: -d["bytes"], "open_items": lambda d: -len(d["open_items"])}.get(sort, lambda d: -d["score"])
    out.sort(key=key, reverse=(sort == "newest"))
    return {"total": len(out), "items": out[offset:offset + limit]}


def summary(reg, marks):
    docs = reg.get("docs", [])
    subj = [d for d in docs if d["kind"] == "SUBJECT"]
    st = Counter(marks.get(d["id"], {}).get("status", "unreviewed") for d in docs)
    week = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat(timespec="minutes")
    return {
        "built_at": reg.get("built_at"), "seconds": reg.get("seconds"), "n_docs": len(docs),
        "by_kind": Counter(d["kind"] for d in docs), "by_area": Counter(d["area"] for d in docs),
        "subject_not_integrated": sum(1 for d in subj if not d["integrated_into"]),
        "subject_integrated": sum(1 for d in subj if d["integrated_into"]),
        "with_open_items": sum(1 for d in docs if d["open_items"]),
        "open_items_total": sum(len(d["open_items"]) for d in docs),
        "with_variants": sum(1 for d in docs if d["exact_copies"] or d["title_variants"]),
        "never_mentioned": sum(1 for d in docs if not d["referenced_by"] and not d["chat_mentions"]["count"]),
        "changed_last_7_days": sum(1 for d in docs if d["mtime"] >= week),
        "partial_worker_reports": sum(1 for d in docs if d.get("partial")),
        "threads": len(reg.get("threads", [])), "marks": st, "targets_found": reg.get("targets_found", []),
    }


def export_md(reg, marks, limit=300):
    q = query(reg, marks, kind="SUBJECT", signal="not_integrated", limit=limit)
    lines = [f"# Loose ends ({_now()[:10]})", "",
             f"{q['total']} subject documents are not found inside any canonical book. Highest priority first.", ""]
    for d in q["items"]:
        box = "[x]" if d["status"] in ("merged", "superseded", "done", "ignore") else "[ ]"
        lines.append(f"- {box} **{d['title']}** ({d['area']}, {d['mtime'][:10]}, {d['bytes']//1024} KB, score {d['score']}, {d['status']})")
        lines.append(f"  `{d['path']}`")
        for it in d["open_items"][:5]:
            lines.append(f"  - owes ({it['section']}): {it['text'][:200]}")
        if d["title_variants"] or d["exact_copies"]:
            lines.append(f"  - variants: {len(d['title_variants'])} same-title, {len(d['exact_copies'])} identical copies")
    return "\n".join(lines) + "\n"
