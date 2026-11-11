"""
Bookbinder: turn thousands of loose files into volumes of natural-language books, one checked chapter
at a time. (Claude GUI, Opus 5.5, 2026-10-06. Integrator-owned module.)

THE PIPELINE (each step is visible in the Volumes tab, and every state is read from disk, never from a
worker's claim):

  1. POOL      Every source that could go into a book: the subject documents in the Loose Ends register
               (AI-made reports, dossiers, dissertations) and the notes in the AA1 Obsidian vault (from the
               vault concordance: one copy per identical file, newest version of each drifted file, stubs
               and archives left out unless switched on).
  2. PLAN      Each source is scored against an editable taxonomy of volumes (data/books_taxonomy.json):
               title words count 3, folder names 2, the opening text 1. Within a volume, sources sharing
               core title words become chapters (the same leader clustering Loose Ends uses), and any chapter
               over PART_WORDS of sources is split into parts. Sources with no clear volume wait in
               "Unsorted" for James to place.
  3. APPROVE   James approves a chapter. Approval FREEZES its source list and folder, so later re-planning
               can never shuffle work that has started. Moves, renames, exclusions are stored as overrides.
  4. BRIEF     For an approved chapter, a WORKER_CONTRACT v1 brief is written to its folder in 10_VOLUMES:
               a lossless natural-language synthesis of all its sources (every fact, quotation and evidence
               tag kept; machinery removed; conflicts shown side by side; open items collected). The brief
               must pass worker_gates.py brief.
  5. DRAFT     A worker (Sonnet 5.5, cleared 2026-10-03; or Opus) writes CHAPTER.md in the chapter folder and
               ends it with the completion marker. Partial drafts are continued, never restarted.
  6. CHECK     The integrator runs: worker_gates.py handback --class reader, and the Mexico study's
               data_check.py of EVERY source against the draft (numbers, references, sigla, Greek, Hebrew,
               quotations, tags). Results go to CHECK.json. data_check alone is not proof (the 2026-10-02
               test), so an Opus judge read writes JUDGE.md.
  7. FINAL     James marks the chapter final. Its sources are marked "merged" in Loose Ends, and the
               assembled volume becomes one of Loose Ends' canonical books, so the loose count falls.
  8. ASSEMBLE  The volume file is rebuilt from its drafted chapters with a table of contents and a source
               appendix (what went in, from where).

Nothing here deletes or moves a source file. Outputs live only under 10_VOLUMES. No network, no LLM.
"""
import datetime
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import threading
from collections import Counter, defaultdict

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(_HERE, "data")
PROJECT = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism"
VOLUMES_DIR = os.path.join(PROJECT, "10_VOLUMES")
TAXONOMY_FILE = os.path.join(DATA_DIR, "books_taxonomy.json")
PLAN_FILE = os.path.join(DATA_DIR, "books_plan.json")
OVERRIDES_FILE = os.path.join(DATA_DIR, "books_overrides.json")
CLASSIFY_CACHE = os.path.join(DATA_DIR, "books_classify_cache.json")
VAULT_CONCORDANCE = os.path.join(DATA_DIR, "vault_concordance.json")
LOOSE_REGISTRY = os.path.join(DATA_DIR, "loose_registry.json")
WORKER_SPEC = os.path.join(PROJECT, "02_CONTROL_AND_STATE", "_WORKER_SPEC")
DATA_CHECK = r"C:\Users\Elation\Mexico_Protestantism_Study\04_CONSOLIDATED\data_check.py"
MARKER_RE = re.compile(r"<!-- WORKER COMPLETE: (\S+) -->\s*$")
PART_WORDS = 40000            # most source words one synthesis job is given
MIN_VAULT_WORDS = 120          # vault stubs below this are not book material
_LOCK = threading.RLock()

DEFAULT_TAXONOMY = {
    "version": 1,
    "note": ("Edit freely. Each volume: id, title, purpose, keywords (lower-case words or short phrases). "
             "Existing books are listed so their material is recognised, not re-synthesised."),
    "volumes": [
        {"id": "V01", "title": "The Church: Authority, Succession and the Papacy",
         "purpose": "Why the visible, apostolic Church with Peter's successor is the Church Christ founded.",
         "keywords": ["church", "ecclesiology", "ecclesiological", "papacy", "papal", "pope", "popes", "peter", "petrine",
                      "primacy", "roman", "rome", "succession", "apostolic", "bishop", "bishops", "episcopacy",
                      "monoepiscopacy", "magisterium", "magisterial", "infallibility", "infallible", "council", "councils",
                      "conciliar", "keys", "cathedra", "schism", "orthodox", "ecumenism", "ecumenical", "indefectibility",
                      "hormisdas", "clement", "ignatius", "irenaeus", "optatus", "honorius", "synod", "synodality"]},
        {"id": "V02", "title": "Scripture, Tradition and Canon",
         "purpose": "What the Bible is, who handed it on, and what that does to sola scriptura.",
         "keywords": ["scripture", "scriptures", "bible", "biblical", "canon", "canonical", "deuterocanon", "deuterocanonical",
                      "apocrypha", "sola scriptura", "tradition", "inspiration", "inerrancy", "septuagint", "lxx", "masoretic",
                      "vulgate", "translation", "translations", "manuscript", "manuscripts", "textual", "variant", "variants",
                      "qumran", "dead sea", "scrolls", "gospels", "synoptic", "codex", "sirach", "maccabees", "esdras",
                      "reina", "valera", "pluriform", "ulrich"]},
        {"id": "V03", "title": "Israel and the Church: Halakha, Midrash and Jewish Roots",
         "purpose": "The Jewish matrix of the Church's authority, liturgy and interpretation.",
         "keywords": ["jewish", "judaism", "jews", "rabbinic", "rabbi", "rabbis", "halakha", "halakhic", "midrash", "midrashic",
                      "talmud", "talmudic", "mishnah", "targum", "temple", "synagogue", "sanhedrin", "pharisees", "pharisee",
                      "sadducees", "essenes", "zadokite", "second temple", "torah", "kabbalah", "binding", "loosing",
                      "philo", "josephus", "nasi", "zugot", "sefaria", "aggadah", "pesher", "middot"]},
        {"id": "V04", "title": "God, Christ and the Trinity",
         "purpose": "The God of Israel revealed as Father, Son and Spirit, against Oneness and its cousins.",
         "keywords": ["trinity", "trinitarian", "oneness", "modalism", "modalist", "christology", "christological",
                      "incarnation", "deity", "divinity", "theotes", "homoousios", "nicaea", "nicene", "arian", "arius",
                      "arianism", "chalcedon", "filioque", "hypostatic", "two wills", "logos", "two powers", "unitarian",
                      "unitarios", "theosis", "gethsemane", "isaiah 9", "john 10"]},
        {"id": "V05", "title": "Grace, Justification and the Sacraments",
         "purpose": "How grace reaches us: baptism, Eucharist, confession, orders, marriage, and justification.",
         "keywords": ["sacrament", "sacraments", "sacramental", "baptism", "baptismal", "eucharist", "eucharistic", "mass",
                      "liturgy", "liturgical", "confession", "penance", "priesthood", "priest", "ordination", "marriage",
                      "divorce", "annulment", "justification", "faith alone", "sola fide", "grace", "merit", "salvation",
                      "osas", "purgatory", "indulgences", "indulgence", "mortal", "venial", "dikaioo", "dikaio", "sacrifice",
                      "good thief", "infant baptism", "transubstantiation", "real presence"]},
        {"id": "V06", "title": "Mary, the Saints and Sacred Images",
         "purpose": "Mary, the communion of saints, intercession, icons and relics.",
         "keywords": ["mary", "marian", "virgin", "theotokos", "immaculate", "assumption", "perpetual virginity", "saints",
                      "saint", "intercession", "invocation", "icons", "icon", "iconography", "images", "statues", "relics",
                      "veneration", "idolatry", "hishtachavah", "guadalupe", "apparition", "apparitions", "fatima",
                      "prototype", "adelphoi", "brothers of jesus", "co-redemptrix", "mediatrix", "rosary"]},
        {"id": "V07", "title": "The Last Things",
         "purpose": "Death, judgment, heaven, hell, purgatory and the end of history, with the speculations sorted.",
         "keywords": ["eschatology", "eschatological", "apocalypse", "apocalyptic", "antichrist", "rapture", "dispensationalism",
                      "millennium", "millenarian", "tribulation", "judgment", "resurrection", "heaven", "hell", "second coming",
                      "parousia", "darkness", "prophecy", "prophecies", "signs", "leviathan", "behemoth", "baruch", "daniel",
                      "preterism", "end times", "conflagration", "two witnesses", "beatific"]},
        {"id": "V08", "title": "History and Its Myths",
         "purpose": "What really happened: Inquisition, Crusades, Reformation, persecution, and the legends.",
         "keywords": ["inquisition", "crusades", "crusade", "reformation", "luther", "calvin", "zwingli", "black legend",
                      "galileo", "medieval", "middle ages", "cristero", "cristeros", "witch", "persecution", "pornocracy",
                      "borgia", "constantine", "trent", "history", "historical", "historiography", "church history",
                      "templar", "halloween", "prohibition"]},
        {"id": "V09", "title": "Faith and Reason",
         "purpose": "The philosophy beneath the faith: God's existence, nature, evil, freedom, science.",
         "keywords": ["philosophy", "philosophical", "metaphysics", "metaphysical", "existence of god", "cosmological",
                      "contingency", "natural law", "evolution", "adam", "science", "epistemology", "epistemic", "atheism",
                      "atheist", "theodicy", "evil", "free will", "determinism", "molinism", "thomism", "thomist", "aquinas",
                      "aristotle", "aristotelian", "logic", "fallacy", "ontology", "ontological"]},
        {"id": "V10", "title": "The Moral Life",
         "purpose": "Catholic moral theology applied: virtues, vices and the hard cases James is asked about.",
         "keywords": ["moral", "morality", "ethics", "ethical", "cannabis", "marijuana", "thc", "alcohol", "drugs", "sexuality",
                      "contraception", "abortion", "death penalty", "capital punishment", "war", "virtue", "vice", "scandal",
                      "conscience", "double effect", "bioethics", "chastity", "lust", "piracy", "usury", "gambling"]},
        {"id": "V11", "title": "The Spiritual Life",
         "purpose": "Prayer, devotion and the practice of the faith for a revert learning his own tradition.",
         "keywords": ["prayer", "pray", "spirituality", "spiritual", "devotion", "devotions", "sacramentals", "holy water",
                      "scapular", "mysticism", "mystical", "contemplation", "liturgy of the hours", "examen", "fasting",
                      "lent", "advent", "feast", "catechesis", "ocia", "rcia", "vocation", "discernment"]},
        {"id": "V12", "title": "Apologetics in Practice: Method, Debate and Witness",
         "purpose": "How to argue well and honestly: method, debate craft, common objections, witness.",
         "keywords": ["apologetics", "apologetic", "debate", "debates", "rebuttal", "refutation", "discord", "rhetoric",
                      "socratic", "evangelization", "evangelism", "witness", "objections", "objection", "polemic", "polemics",
                      "conversion", "convert", "testimony", "method", "methodology", "steelman", "burden of proof",
                      "protestant", "protestants", "pentecostal", "evangelical", "jw", "mormon", "lds", "islam", "muslim"]},
    ],
    "existing_books": [
        {"id": "B-HPC", "title": "History Proves Catholicism (master dissertation)",
         "path": PROJECT + r"\01_MASTER_DISSERTATION\Master_Dissertation_History_Proves_Catholicism_2026-07-04.md"},
        {"id": "B-MEX", "title": "The Catholic Case (Mexico study, Reader's Edition)",
         "path": r"C:\Users\Elation\Mexico_Protestantism_Study\05_READERS_EDITION\THE_CATHOLIC_CASE_Readers_Edition.md"},
        {"id": "B-SCR", "title": "The Ten-Year Scriptorium",
         "path": r"C:\Users\Elation\Scholar_Decade_Plan\The_Ten_Year_Scriptorium.md"},
    ],
    "vault": {
        "include": True,
        "vault_ids": ["aa1_live"],
        "exclude_folders": ["98_Archives", "96_Variant_aa_Merge", "97_Variant_dr_Merge", "99_Meta_and_System",
                            "21_Personal_and_Life", "23_Health_and_Biohacking", "26_Finance_and_Economics",
                            "50_Science_and_Technology", "60_Social_Sciences", "vaultb"],
        "min_words": MIN_VAULT_WORDS,
    },
    "assign_min_score": 4,
    "assign_margin": 1.25,
}


# ----------------------------------------------------------------------------- io helpers

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

def _read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as w:
        json.dump(obj, w, ensure_ascii=False, indent=1)
    _replace_retry(tmp, path)


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def slug(s, n=48):
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s[:n].rstrip("_") or "untitled"


def source_id(path):
    """Same id scheme as Loose Ends, so marks and moves line up across both tabs."""
    return hashlib.sha1(os.path.normcase(os.path.abspath(path)).encode("utf-8")).hexdigest()[:16]


def load_taxonomy():
    t = _read_json(TAXONOMY_FILE)
    if not t:
        t = json.loads(json.dumps(DEFAULT_TAXONOMY))
        os.makedirs(DATA_DIR, exist_ok=True)
        _write_json(TAXONOMY_FILE, t)
    return t


def load_overrides():
    o = _read_json(OVERRIDES_FILE) or {}
    for k, v in (("moves", {}), ("excluded", []), ("chapter_titles", {}), ("volume_titles", {}), ("frozen", {}),
                 ("final", {}), ("notes", {})):
        o.setdefault(k, v)
    return o


def save_overrides(o):
    with _LOCK:
        _write_json(OVERRIDES_FILE, o)


# ----------------------------------------------------------------------------- pool
# ----------------------------------------------------------------------------- the working clone (2026-10-08)
# James: "dont mess with the original notes ... clone". Sorting and chapter writing read the clone made by
# tools\make_sorting_clone.py, never the originals. The planner still identifies each source by its original path.
HOME_DIR = r"C:\Users\Elation"
CLONE_DIR = os.path.join(HOME_DIR, "CLONE_FOR_SORTING_2026-10-08__COPIES_NOT_ORIGINALS")


def working_copy(path):
    """The clone's copy of an original file (falls back to the original only if no copy exists yet)."""
    try:
        c = os.path.join(CLONE_DIR, os.path.relpath(path, HOME_DIR))
    except ValueError:
        return path
    return c if os.path.isfile(c) else path


def _line_set(path):
    """The note's non-blank lines, whitespace-normalised, for "is every line of A inside B?" (None if unreadable)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return {re.sub(r"\s+", " ", ln).strip() for ln in fh if ln.strip()}
    except OSError:
        return None


# ----------------------------------------------------------------------------- screenshot text (2026-10-08)
# Many of James's notes are a pasted screenshot plus a line. The text inside those screenshots is already extracted
# by his screenshot search index (C:\Users\Elation\.ocr_index: _manifest.json maps each image file to <hash>.txt).
# It now counts as part of the note: for the word count, for sorting, and as an input the drafter must read.
OCR_DIR = r"C:\Users\Elation\.ocr_index"
OCR_CACHE = os.path.join(DATA_DIR, "books_ocr_cache.json")
EMBED_RE = re.compile(r"!\[\[([^\]|#]+?\.(?:png|jpe?g|webp|gif|bmp))(?:[|#][^\]]*)?\]\]"
                      r"|!\[[^\]]*\]\(([^)]+?\.(?:png|jpe?g|webp|gif|bmp))\)", re.I)
_OCR = {"mtime": None, "by_name": {}, "cache": None, "dirty": False}


def _ocr_names():
    man = os.path.join(OCR_DIR, "_manifest.json")
    try:
        m = os.path.getmtime(man)
    except OSError:
        return {}
    if _OCR["mtime"] != m:
        d = _read_json(man) or {}
        _OCR["by_name"] = {os.path.basename(k).lower(): v[2] for k, v in d.items() if isinstance(v, list) and len(v) > 2}
        _OCR["mtime"] = m
    return _OCR["by_name"]


def screenshot_files(path):
    """The extracted-text files of the screenshots embedded in a note ([] when none)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            t = fh.read()
    except OSError:
        return []
    names = _ocr_names()
    out = []
    for a, b in EMBED_RE.findall(t):
        h = names.get(os.path.basename((a or b).replace("%20", " ")).lower())
        p = os.path.join(OCR_DIR, h + ".txt") if h else None
        if p and os.path.isfile(p) and p not in out:
            out.append(p)
    return out


def screenshot_words(path):
    """Words of screenshot text in a note, cached per (path, modification time) in books_ocr_cache.json."""
    if _OCR["cache"] is None:
        _OCR["cache"] = _read_json(OCR_CACHE) or {}
    try:
        m = int(os.path.getmtime(path))
    except OSError:
        return 0
    _ocr_names()                                    # refreshes the index's modification time
    hit = _OCR["cache"].get(path)
    if hit and hit[0] == m and hit[2] == _OCR["mtime"]:
        return hit[1]
    n = 0
    for p in screenshot_files(path):
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                n += len(fh.read().split())
        except OSError:
            pass
    _OCR["cache"][path] = [m, n, _OCR["mtime"]]
    _OCR["dirty"] = True
    return n


def screenshot_text(path, limit=1500):
    out = []
    for p in screenshot_files(path):
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                out.append(fh.read())
        except OSError:
            pass
    return "\n".join(out)[:limit]


def _flush_ocr_cache():
    if _OCR["dirty"] and _OCR["cache"] is not None:
        _write_json(OCR_CACHE, _OCR["cache"])
        _OCR["dirty"] = False


# ----------------------------------------------------------------------------- James's earlier writing (2026-10-08)
# James began researching in 2025, before the AA1 vault took its present shape. Notes that survive only in older vault
# copies (USB backup, the DXM parent vault, Desktop Easy...) and his plain-text notes are original sources too.
EARLIER_VAULT_IDS = ["usb_backup_elation", "dxm_parent", "desktop_easy", "aadesktop_dxm", "usb_backup_protocol",
                     "downloads_backup"]
TEXT_ROOTS = [r"C:\Users\Elation\Research_Imports\Text_and_Notes"]


def _earlier_pool(tax, d, excl):
    """Earlier-vault notes whose text is NOT wholly inside a same-name AA1 note, plus plain-text note folders."""
    vc = tax.get("vault", {})
    # read only from the taxonomy file (data\books_taxonomy.json lists EARLIER_VAULT_IDS and TEXT_ROOTS); never
    # defaulted here, so a test's own taxonomy can't reach James's real folders
    ids = set(vc.get("earlier_vault_ids") or [])
    aa1_by_name = defaultdict(list)
    for u in d.get("unique_documents", []):
        if u.get("vault_id") == "aa1_live":
            aa1_by_name[(u.get("filename") or "").lower()].append(u["path"])
    out, skipped = [], Counter()
    for u in d.get("unique_documents", []):
        if u.get("vault_id") not in ids or not u["path"].lower().endswith((".md", ".txt")):
            continue
        if (u.get("rel_path") or "").split("/")[0] in excl or "/.obsidian/" in "/" + (u.get("rel_path") or ""):
            skipped["earlier copy in an excluded folder"] += 1
            continue
        mine = _line_set(u["path"])
        if not mine:
            skipped["earlier copy, empty or unreadable"] += 1
            continue
        if any((lambda t: t is not None and mine <= t)(_line_set(p)) for p in aa1_by_name.get((u.get("filename") or "").lower(), [])):
            skipped["earlier copy whose every line is in AA1"] += 1
            continue
        out.append({"id": source_id(u["path"]), "path": u["path"], "title": u.get("title") or u.get("filename"),
                    "origin": "vault", "area": "Earlier vault copy: " + (u.get("vault_name") or ""),
                    "folder": "/".join((u.get("rel_path") or "").split("/")[:-1]), "words": u.get("words") or 0,
                    "mtime": (u.get("mtime_iso") or "")[:16], "kind": "SUBJECT", "integrated": False})
    for entry in tax.get("text_roots") or []:
        # an entry is a folder path, or [folder path, label], e.g. ["...\\Historical_Harvest_Mar2026\\Archive",
        # "Gemini conversations"] (James 2026-10-08: the conversations hold valuable information)
        root, label = (entry, "James's text notes") if isinstance(entry, str) else (entry[0], entry[1])
        for dp, dn, fn in os.walk(root):
            for f in fn:
                if not f.lower().endswith((".txt", ".md")):
                    continue
                p = os.path.join(dp, f)
                try:
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        w = len(fh.read().split())
                    mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%dT%H:%M")
                except OSError:
                    continue
                if not w:
                    skipped["text note, empty"] += 1
                    continue
                out.append({"id": source_id(p), "path": p, "title": os.path.splitext(f)[0], "origin": "vault",
                            "area": label, "folder": os.path.relpath(dp, root).replace("\\", "/").strip("."),
                            "words": w, "mtime": mt, "kind": "SUBJECT", "integrated": False})
    return out, skipped


def _vault_pool(tax):
    vc = tax.get("vault", {})
    if not vc.get("include"):
        return [], {}
    d = _read_json(VAULT_CONCORDANCE)
    if not d:
        return [], {"vault": "vault_concordance.json missing"}
    ids = set(vc.get("vault_ids") or ["aa1_live"])
    excl = set(vc.get("exclude_folders") or [])
    minw = int(vc.get("min_words") or MIN_VAULT_WORDS)
    # Same-name copies (fixed 2026-10-08, James's go-ahead). The old rule kept the newest copy by date and dropped
    # the rest; dates come from bulk moves, the "newest" copy was usually in an excluded folder (96_/97_/98_), and
    # 61 "older versions" were different notes, so their text vanished from the plan. New rule: dates are ignored.
    # Only copies in included folders compete, and one is dropped ONLY if every line of it is found in another
    # included copy (identical copies: the shortest path is kept). Anything with even one unique line stays.
    older = set()
    for f in d.get("version_drift_files", []):
        vs = [v for v in f.get("variants", []) if v.get("vault_id") in ids
              and (v.get("rel_path") or "").split("/")[0] not in excl]
        if len(vs) < 2:
            continue
        lines = {v["path"]: _line_set(v["path"]) for v in vs}
        for v in vs:
            mine = lines[v["path"]]
            if mine is None:
                continue
            for k in vs:
                if k is v or os.path.normcase(k["path"]) in older or lines[k["path"]] is None:
                    continue
                theirs = lines[k["path"]]
                if mine <= theirs and (mine != theirs or (len(k["path"]), k["path"]) < (len(v["path"]), v["path"])):
                    older.add(os.path.normcase(v["path"]))
                    break
    out, skipped = [], Counter()
    for u in d.get("unique_documents", []):
        if u.get("vault_id") not in ids:
            continue
        top = (u.get("rel_path") or "").split("/")[0]
        if top in excl:
            skipped["excluded folder"] += 1
            continue
        if os.path.normcase(u["path"]) in older:
            skipped["copy whose every line is in another copy"] += 1
            continue
        if not u["path"].lower().endswith(".md"):
            skipped["not markdown"] += 1
            continue
        shot = screenshot_words(u["path"])          # text inside the note's screenshots counts as its words
        if (u.get("words") or 0) + shot < minw:
            skipped[f"under {minw} words (screenshot text included)"] += 1
            continue
        mt = u.get("mtime_iso") or ""
        out.append({"id": source_id(u["path"]), "path": u["path"], "title": u.get("title") or u.get("filename"),
                    "origin": "vault", "area": "Obsidian " + (u.get("vault_name") or "vault"),
                    "folder": "/".join((u.get("rel_path") or "").split("/")[:-1]),
                    "words": (u.get("words") or 0) + shot, "screenshot_words": shot,
                    "mtime": mt[:16], "kind": "SUBJECT", "integrated": False})
    earlier, sk2 = _earlier_pool(tax, d, excl)
    out += earlier
    skipped.update(sk2)
    _flush_ocr_cache()
    return out, dict(skipped)


MAX_SOURCE_WORDS = 60000   # bigger single files are compilations or book renderings, not sources


def book_paths(tax=None):
    """Every canonical book: the taxonomy's existing books AND every target Loose Ends checks against
    (which includes the Mexico study's verbatim source appendix). A first split run cut that appendix
    into parts and planned them into Volume 4, i.e. re-synthesising a book that already exists."""
    paths = {os.path.normcase(b["path"]) for b in (tax or load_taxonomy()).get("existing_books", [])}
    try:
        from modules import loose_core
        paths |= {os.path.normcase(t) for t in loose_core.load_config().get("targets", [])}
    except Exception:
        pass
    return paths


def _ai_pool(tax=None, skipped=None):
    """Subject documents from Loose Ends, minus the existing books and their renderings (the master
    dissertation folder, the assembled Mexico books, pandoc HTML exports). On the first plan these
    were 15.6 M of 41 M words: synthesising them would have re-written the books into themselves."""
    reg = _read_json(LOOSE_REGISTRY) or {}
    skipped = skipped if skipped is not None else Counter()
    books = book_paths(tax)
    out = []
    for d in reg.get("docs", []):
        if d.get("kind") != "SUBJECT" or d.get("ext") not in (".md", ".html"):
            continue
        pl = os.path.normcase(d["path"])
        if pl in books or "\\01_master_dissertation\\" in pl or pl.endswith(("_readers_edition.md", "_consolidated_dissertation.md")):
            skipped["part of an existing book"] += 1
            continue
        if d.get("ext") == ".html" and (d.get("words") or 0) > 20000:
            skipped["HTML rendering of a book or document"] += 1
            continue
        out.append({"id": d["id"], "path": d["path"], "title": d.get("title") or os.path.basename(d["path"]),
                    "origin": "ai", "area": d.get("area", ""), "folder": d.get("subarea", ""),
                    "words": d.get("words") or 0, "mtime": d.get("mtime", ""), "kind": "SUBJECT",
                    "integrated": bool(d.get("integrated_into")),
                    "integrated_into": [t.get("target") for t in d.get("integrated_into", [])],
                    "open_items": len(d.get("open_items", []))})
    return out


def _opening_text(path, limit=3000):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            t = fh.read(limit + 2000)
    except OSError:
        return ""
    t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S)   # Obsidian front matter
    t = re.sub(r"!\[\[[^\]]*\]\]|!\[[^\]]*\]\([^)]*\)", " ", t)
    t = t[:limit]
    if len(t.split()) < 200:                               # a screenshot note: sort it by what the screenshot says
        t += "\n" + screenshot_text(path, limit)
    return t[:limit].lower()


# ----------------------------------------------------------------------------- oversized: lossless split
SPLIT_TARGET = 15000      # words per part, cut at the next heading
SPLIT_HARD = 25000        # cut at the next blank line if no heading came


def split_dir():
    return os.path.join(VOLUMES_DIR, "_split_sources")


def split_source(path, title="", origin="vault"):
    """Cut an oversized file into parts at its own headings (or blank lines when no heading comes).
    Nothing is dropped or rewritten: each part is a verbatim run of the original's lines, and
    manifest.json records the line ranges and the original's sha256 so the split can be proven
    lossless (concatenating the part bodies in order reproduces the original byte for byte)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    sha = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8", errors="surrogateescape")
    # Units are lines, except that a single line longer than SPLIT_HARD words is cut after sentence ends
    # (the pieces concatenate back to the exact line). Seen 2026-10-06: a 27,933-word single line.
    units = []
    for line in text.splitlines(keepends=True):
        if len(line.split()) <= SPLIT_HARD:
            units.append(line)
            continue
        buf, n = [], 0
        for piece in re.split(r"(?<=[.!?])(?=\s)", line):
            buf.append(piece)
            n += len(piece.split())
            if n >= SPLIT_TARGET:
                units.append("".join(buf))
                buf, n = [], 0
        if buf:
            units.append("".join(buf))

    def boundary(u):
        # concatenated Obsidian clippings: quoted blank lines ("> "), front-matter fences, clip headers
        stripped = re.sub(r"^[>\s]*", "", u)
        return (not stripped.strip()) or stripped.startswith("---") or stripped.startswith("### [[")

    parts, cur, words, start = [], [], 0, 0
    for i, u in enumerate(units):
        is_head = bool(re.match(r"^#{1,3}\s+\S", u))
        if cur and ((is_head and words >= SPLIT_TARGET) or (boundary(u) and words >= SPLIT_HARD)
                    or words >= int(SPLIT_HARD * 1.3)):
            parts.append((start, i, cur))
            cur, words, start = [], 0, i
        cur.append(u)
        words += len(u.split())
    if cur:
        parts.append((start, len(units), cur))
    folder = os.path.join(split_dir(), f"{slug(os.path.splitext(os.path.basename(path))[0], 50)}_{sha[:8]}")
    os.makedirs(folder, exist_ok=True)
    man = {"source": path, "sha256": sha, "title": title, "origin": origin, "split_at": _now(), "parts": []}
    for n, (a, b, body) in enumerate(parts, 1):
        head = next((re.sub(r"^#+\s*", "", l).strip() for l in body if re.match(r"^#{1,3}\s+\S", l)), "")
        fn = f"part_{n:03d}.md"
        btxt = "".join(body)
        with open(os.path.join(folder, fn), "wb") as w:
            w.write(btxt.encode("utf-8", errors="surrogateescape"))
        man["parts"].append({"file": fn, "units": [a + 1, b], "words": len(btxt.split()), "first_heading": head[:150]})
    _write_json(os.path.join(folder, "manifest.json"), man)
    return {"folder": folder, "parts": len(parts), "sha256": sha}


def verify_split(folder):
    man = _read_json(os.path.join(folder, "manifest.json"))
    joined = b"".join(open(os.path.join(folder, p["file"]), "rb").read() for p in man["parts"])
    return hashlib.sha256(joined).hexdigest() == man["sha256"]


def _split_pool():
    """Parts of split files enter the pool as ordinary sources; the originals they replace are returned
    so the planner can leave them out."""
    import glob
    out, replaced = [], set()
    books = book_paths()
    for mf in glob.glob(os.path.join(split_dir(), "*", "manifest.json")):
        man = _read_json(mf)
        if not man:
            continue
        replaced.add(os.path.normcase(man["source"]))
        if os.path.normcase(man["source"]) in books:
            continue                     # a split of an existing book is never a source
        folder = os.path.dirname(mf)
        n = len(man["parts"])
        for i, p in enumerate(man["parts"], 1):
            fp = os.path.join(folder, p["file"])
            out.append({"id": source_id(fp), "path": fp, "origin": "split",
                        "title": f"{man.get('title') or os.path.basename(man['source'])} (part {i} of {n}){': ' + p['first_heading'] if p['first_heading'] else ''}",
                        "area": "Split from " + os.path.basename(man["source"]), "folder": os.path.basename(os.path.dirname(man["source"])),
                        "words": p["words"], "mtime": man["split_at"][:16], "kind": "SUBJECT", "integrated": False})
    return out, replaced


# ----------------------------------------------------------------------------- classification
def _kw_hits(text, keywords):
    hits = set()
    for k in keywords:
        if " " in k:
            if k in text:
                hits.add(k)
        elif re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", text):
            hits.add(k)
    return hits


# Words so common in this corpus that they only mean something in a TITLE. In the opening text of a
# note they appear almost everywhere ("church", "rome") and dragged 10 M words into Volume 1 on the
# first plan (2026-10-06).
GENERIC = {"church", "roman", "rome", "history", "historical", "bible", "biblical", "scripture", "scriptures",
           "tradition", "prayer", "pray", "moral", "mass", "grace", "salvation", "saint", "saints", "council", "pope",
           "popes", "method", "protestant", "protestants", "evangelical", "logic", "science", "war", "feast",
           "spiritual", "priest", "bishop", "bishops", "apostolic", "liturgy", "liturgical", "sacrament", "sacraments",
           "witness", "evil", "virtue", "judgment", "signs", "temple", "jewish", "jews", "translation"}
CATCHALL_FOLDER = 800   # a folder holding more pool sources than this says nothing about any one note
CLASSIFIER_VERSION = 2


def classify(src, tax, open_hits, folder_counts=None):
    """open_hits: {volume id: [keywords found in the opening text]} (cached). Title words count 3,
    folder words 2 (unless the folder is a catch-all), opening words 1 (generic words never)."""
    title = (src["title"] or "").lower().replace("_", " ")
    folder = (src.get("folder") or "")
    use_folder = not folder_counts or folder_counts.get(folder, 0) <= CATCHALL_FOLDER
    folder = folder.lower().replace("_", " ") if use_folder else ""
    scores = {}
    for v in tax["volumes"]:
        kw = v["keywords"]
        oh = [k for k in open_hits.get(v["id"], []) if k not in GENERIC]
        s = 3 * len(_kw_hits(title, kw)) + 2 * len(_kw_hits(folder, kw)) + min(len(oh), 6)
        if s:
            scores[v["id"]] = s
    if not scores:
        return None, 0, {}
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])
    best, s1 = ranked[0]
    s2 = ranked[1][1] if len(ranked) > 1 else 0
    ok = s1 >= tax.get("assign_min_score", 4) and s1 >= tax.get("assign_margin", 1.25) * s2
    return (best if ok else None), s1, dict(ranked[:3])


def _classified(pool, tax):
    """The slow part (reading ~11,000 openings) is cached per (path, mtime, keyword-list hash) as the raw
    keyword hits; the scoring itself is recomputed every plan, so scoring changes cost nothing."""
    th = hashlib.sha1(json.dumps([[v["id"], v["keywords"]] for v in tax["volumes"]], sort_keys=True).encode()).hexdigest()[:10]
    cache = _read_json(CLASSIFY_CACHE) or {}
    if cache.get("tax") != th or cache.get("v") != CLASSIFIER_VERSION:
        cache = {"tax": th, "v": CLASSIFIER_VERSION, "items": {}}
    items = cache["items"]
    for s in pool:
        key = f"{s['path']}|{s['mtime']}"
        if key not in items:
            opening = _opening_text(s["path"])
            items[key] = {v["id"]: sorted(_kw_hits(opening, v["keywords"])) for v in tax["volumes"]}
            items[key] = {k: h for k, h in items[key].items() if h}
    _write_json(CLASSIFY_CACHE, cache)
    folder_counts = Counter(s.get("folder") or "" for s in pool)
    for s in pool:
        vid, score, top = classify(s, tax, items[f"{s['path']}|{s['mtime']}"], folder_counts)
        s["volume"], s["score"], s["candidates"] = vid, score, top
    return pool


# ----------------------------------------------------------------------------- plan
TITLE_STOP = set("""note notes untitled pasted image chat conversation gemini claude grok chatgpt copy final draft
md the and for with from into about what does that this your their there have been which when where while why how
analysis synthesis dossier report research study master complete full version natural language edition
vs versus part section chapter""".split())


def _tokens(title):
    words = re.findall(r"[a-záéíóúñü]{4,}", (title or "").lower().replace("_", " "))
    return {w for w in words if w not in TITLE_STOP}


def _cluster_volume(srcs):
    """Leader clustering on title words (core words held by a strict majority of a chapter's members),
    oldest first. Leftovers become one 'further material' chapter per volume."""
    df = Counter()
    for s in srcs:
        df.update(s["_tok"])
    n = max(1, len(srcs))
    useful = {w for w, c in df.items() if 2 <= c <= max(4, int(n * 0.08))}
    idf = {w: math.log(n / df[w]) for w in useful}
    chapters = []
    for s in sorted(srcs, key=lambda s: s["mtime"]):
        toks = s["_tok"] & useful
        best, bs = None, 0.0
        if len(toks) >= 1:
            for ch in chapters:
                m = len(ch["members"])
                core = {w for w, c in ch["counter"].items() if c * 2 > m} or {w for w, _ in ch["counter"].most_common(3)}
                inter = sum(idf[w] for w in toks & core)
                union = sum(idf[w] for w in toks | core)
                sim = inter / union if union else 0
                if sim > bs:
                    best, bs = ch, sim
        if best is not None and bs >= 0.34:
            best["counter"].update(toks)
            best["members"].append(s)
        else:
            chapters.append({"counter": Counter(toks), "members": [s]})
    real = [c for c in chapters if len(c["members"]) >= 2]
    rest = [m for c in chapters if len(c["members"]) < 2 for m in c["members"]]
    return real, rest


def _split_parts(members, cap=PART_WORDS):
    parts, cur, w = [], [], 0
    for m in sorted(members, key=lambda m: m["mtime"]):
        mw = max(m.get("words") or 0, 1)
        if cur and w + mw > cap:
            parts.append(cur)
            cur, w = [], 0
        cur.append(m)
        w += mw
    if cur:
        parts.append(cur)
    return parts


def build_plan():
    """Recompute the proposal from the current pool and taxonomy, then apply James's overrides.
    Frozen (approved) chapters keep their exact source lists and folders."""
    import time
    t0 = time.time()
    tax = load_taxonomy()
    ov = load_overrides()
    vault, vault_skipped = _vault_pool(tax)
    ai_skipped = Counter()
    split_parts, replaced = _split_pool()
    pool = _ai_pool(tax, ai_skipped) + vault + split_parts
    seen, uniq, oversized = set(), [], []
    # Rule 13: provenance (raw conversation logs, combined project dumps, system-log backups) is never book material.
    prov = [x.upper() for x in tax.get("exclude_name_patterns") or []]
    for s in pool:
        if s["id"] in seen:
            continue
        seen.add(s["id"])
        name = (os.path.basename(s["path"]) + " " + (s.get("title") or "")).upper()
        if any(x in name for x in prov):
            ai_skipped["provenance dump (Rule 13)"] += 1
            continue
        if os.path.normcase(s["path"]) in replaced:
            continue                       # this file has been split; its parts are in the pool instead
        if (s.get("words") or 0) > MAX_SOURCE_WORDS:
            oversized.append({"id": s["id"], "path": s["path"], "title": s["title"], "words": s["words"], "origin": s["origin"]})
            continue
        uniq.append(s)
    pool = _classified(uniq, tax)
    by_id = {s["id"]: s for s in pool}
    excluded = set(ov["excluded"])
    frozen_ids = {sid for fc in ov["frozen"].values() for sid in fc["sources"]}

    vols = {v["id"]: {"id": v["id"], "title": ov["volume_titles"].get(v["id"], v["title"]), "purpose": v.get("purpose", ""),
                      "chapters": []} for v in tax["volumes"]}
    unsorted = []
    per_vol = defaultdict(list)
    llm_sort = _read_json(os.path.join(DATA_DIR, "books_llm_sort.json")) or {}   # see modules/books_llmsort.py
    llm_not_book = Counter()
    for s in pool:
        if s["id"] in excluded or s["id"] in frozen_ids:
            continue
        mv = ov["moves"].get(s["id"])
        vid = mv.get("volume") if mv else s["volume"]
        smart = None if mv else llm_sort.get(s["id"])   # a model's sorting decision; James's own move always wins
        if smart:
            s["llm_topic"] = smart.get("topic")
            if smart["volume"] in vols:
                vid = smart["volume"]
            else:
                llm_not_book[smart["volume"]] += 1     # PERSONAL / PROJECT / NOT_USEFUL: left out, counted
                continue
        if s.get("integrated") and not mv:
            continue            # already inside one of the existing books: not re-synthesised by default
        if vid in vols:
            s["_tok"] = _tokens(s["title"])
            per_vol[vid].append(s)
        else:
            unsorted.append(s["id"])

    # frozen chapters first, exactly as approved
    for cid, fc in ov["frozen"].items():
        if fc["volume"] in vols:
            vols[fc["volume"]]["chapters"].append(_chapter_record(cid, fc["title"], fc["volume"], fc["sources"], by_id,
                                                                  frozen=True, folder=fc["folder"], ov=ov))
    for vid, srcs in per_vol.items():
        pinned = defaultdict(list)
        free = []
        for s in srcs:
            mv = ov["moves"].get(s["id"])
            if mv and mv.get("chapter"):
                pinned[mv["chapter"]].append(s)
            else:
                free.append(s)
        real, rest = _cluster_volume(free)
        groups = []
        for ch in real:
            label = [w for w, _ in ch["counter"].most_common(3)]
            groups.append((label, ch["members"]))
        if rest:
            groups.append((["further", "material"], rest))
        for label, members in groups:
            parts = _split_parts(members)
            for i, part in enumerate(parts, 1):
                base = vid + "-" + hashlib.sha1(" ".join(sorted(label)).encode()).hexdigest()[:6]
                cid = base + (f"-p{i}" if len(parts) > 1 else "")
                title = " / ".join(w.capitalize() for w in label) + (f" (part {i} of {len(parts)})" if len(parts) > 1 else "")
                if label == ["further", "material"]:
                    title = "Further material" + (f" (part {i} of {len(parts)})" if len(parts) > 1 else "")
                vols[vid]["chapters"].append(_chapter_record(cid, ov["chapter_titles"].get(cid, title), vid,
                                                             [m["id"] for m in part], by_id, ov=ov))
        for cid, members in pinned.items():
            vols[vid]["chapters"].append(_chapter_record(cid, ov["chapter_titles"].get(cid, cid), vid,
                                                         [m["id"] for m in members], by_id, ov=ov))
    for v in vols.values():
        v["chapters"].sort(key=lambda c: (not c["frozen"], c["title"].startswith("Further material"), -c["words"]))
        v["n_sources"] = sum(c["n_sources"] for c in v["chapters"])
        v["words"] = sum(c["words"] for c in v["chapters"])
        v["states"] = dict(Counter(c["state"] for c in v["chapters"]))
    plan = {"built_at": _now(), "seconds": round(time.time() - t0, 1),
            "pool": {"total": len(pool), "ai": sum(1 for s in pool if s["origin"] == "ai"),
                     "vault": sum(1 for s in pool if s["origin"] == "vault"),
                     "already_in_books": sum(1 for s in pool if s.get("integrated")),
                     "excluded_by_james": len(excluded), "unsorted": len(unsorted), "vault_skipped": vault_skipped,
                     "ai_skipped": dict(ai_skipped), "oversized": len(oversized),
                     "oversized_words": sum(o["words"] for o in oversized),
                     "smart_sorted": len(llm_sort), "smart_not_book": dict(llm_not_book)},
            "oversized": sorted(oversized, key=lambda o: -o["words"]),
            "volumes": [vols[v["id"]] for v in tax["volumes"]],
            "existing_books": tax.get("existing_books", []),
            "unsorted": unsorted,
            "sources": {s["id"]: {k: s.get(k) for k in ("path", "title", "origin", "area", "folder", "words", "mtime",
                                                       "volume", "score", "candidates", "integrated", "open_items",
                                                       "screenshot_words")}
                        for s in pool}}
    with _LOCK:
        _write_json(PLAN_FILE, plan)
    return plan


def _chapter_record(cid, title, vid, source_ids, by_id, frozen=False, folder=None, ov=None):
    srcs = [by_id[s] for s in source_ids if s in by_id]
    folder = folder or f"{cid}_{slug(title, 40)}"
    rec = {"id": cid, "title": title, "volume": vid, "frozen": frozen, "folder": folder, "sources": source_ids,
           "n_sources": len(source_ids), "missing_sources": len(source_ids) - len(srcs),
           "words": sum(s.get("words") or 0 for s in srcs),
           "origins": dict(Counter(s["origin"] for s in srcs)),
           "note": (ov or {}).get("notes", {}).get(cid, "")}
    rec.update(chapter_state(rec, ov))
    return rec


# ----------------------------------------------------------------------------- state from disk
def chapter_dir(rec):
    vdir = os.path.join(VOLUMES_DIR, rec["volume"])
    return os.path.join(vdir, rec["folder"])


def chapter_state(rec, ov=None):
    """proposed -> approved -> briefed -> drafting -> drafted -> checked -> judged -> final.
    Everything after 'approved' is read from files in the chapter folder."""
    d = chapter_dir(rec)
    st = {"state": "approved" if rec["frozen"] else "proposed", "files": {}}
    if not os.path.isdir(d):
        return st
    f = {n: os.path.join(d, n) for n in ("BRIEF.md", "CHAPTER.md", "CHECK.json", "JUDGE.md")}
    have = {n: os.path.exists(p) for n, p in f.items()}
    st["files"] = {n: f[n] for n in f if have[n]}
    if have["BRIEF.md"]:
        st["state"] = "briefed"
    if have["CHAPTER.md"]:
        try:
            with open(f["CHAPTER.md"], encoding="utf-8", errors="replace") as fh:
                txt = fh.read()
        except OSError:
            txt = ""
        st["draft_words"] = len(txt.split())
        st["state"] = "drafted" if MARKER_RE.search(txt) else "drafting"
    if have["CHECK.json"] and st["state"] == "drafted":
        chk = _read_json(f["CHECK.json"]) or {}
        st["check"] = {k: chk.get(k) for k in ("at", "gate", "sources_checked", "items", "missing", "worst")}
        st["state"] = "checked"
    if have["JUDGE.md"] and st["state"] == "checked":
        st["state"] = "judged"
    if ov and rec["id"] in ov.get("final", {}) and st["state"] in ("checked", "judged"):
        st["state"] = "final"
    return st


def load_plan(build_if_missing=True):
    p = _read_json(PLAN_FILE)
    if p:
        ov = load_overrides()
        for v in p["volumes"]:
            for c in v["chapters"]:
                fc = ov["frozen"].get(c["id"])     # approval takes effect at once, not at the next re-plan
                c["frozen"] = bool(fc)
                if fc:
                    c["sources"], c["folder"], c["title"] = list(fc["sources"]), fc["folder"], fc["title"]
                    c["n_sources"] = len(fc["sources"])
                c.update(chapter_state(c, ov))
            v["states"] = dict(Counter(c["state"] for c in v["chapters"]))
        return p
    return build_plan() if build_if_missing else None


def find_chapter(plan, cid):
    for v in plan["volumes"]:
        for c in v["chapters"]:
            if c["id"] == cid:
                return v, c
    return None, None


# ----------------------------------------------------------------------------- james's edits
def approve(cid):
    plan = load_plan()
    v, c = find_chapter(plan, cid)
    if not c:
        raise KeyError(cid)
    ov = load_overrides()
    if cid not in ov["frozen"]:
        ov["frozen"][cid] = {"volume": c["volume"], "title": c["title"], "sources": list(c["sources"]),
                             "folder": c["folder"], "at": _now()}
        save_overrides(ov)
    os.makedirs(chapter_dir(c), exist_ok=True)
    return ov["frozen"][cid]


def unapprove(cid):
    ov = load_overrides()
    fc = ov["frozen"].get(cid)
    if not fc:
        return False
    d = os.path.join(VOLUMES_DIR, fc["volume"], fc["folder"])
    if os.path.exists(os.path.join(d, "CHAPTER.md")):
        raise ValueError("a draft exists in this chapter's folder; it stays approved (nothing is ever deleted)")
    ov["frozen"].pop(cid)
    save_overrides(ov)
    return True


def move_source(sid, volume, chapter=None):
    ov = load_overrides()
    for fc in ov["frozen"].values():
        if sid in fc["sources"]:
            raise ValueError("this source belongs to an approved chapter; un-approve it first")
    if volume in (None, "", "unsorted"):
        ov["moves"].pop(sid, None)
    else:
        ov["moves"][sid] = {"volume": volume, "chapter": chapter or None}
    save_overrides(ov)


def exclude_source(sid, excluded=True):
    ov = load_overrides()
    s = set(ov["excluded"])
    (s.add if excluded else s.discard)(sid)
    ov["excluded"] = sorted(s)
    save_overrides(ov)


def rename(kind, rid, title):
    ov = load_overrides()
    key = "chapter_titles" if kind == "chapter" else "volume_titles"
    ov[key][rid] = title[:200]
    if kind == "chapter" and rid in ov["frozen"]:
        ov["frozen"][rid]["title"] = title[:200]
    save_overrides(ov)


def set_final(cid, final=True, note=""):
    ov = load_overrides()
    if final:
        ov["final"][cid] = {"at": _now(), "note": note}
    else:
        ov["final"].pop(cid, None)
    save_overrides(ov)
    if final:
        _mark_sources_merged(cid)


def _mark_sources_merged(cid):
    """Close the loop: every AI-made source of a final chapter is marked 'merged' in Loose Ends."""
    try:
        from modules import loose_core
    except Exception:
        return 0
    plan = load_plan()
    v, c = find_chapter(plan, cid)
    if not c:
        return 0
    out = os.path.join(chapter_dir(c), "CHAPTER.md")
    n = 0
    for sid in c["sources"]:
        s = plan["sources"].get(sid)
        if s and s["origin"] == "ai":
            try:
                loose_core.set_mark(sid, "merged", merged_into=out)
                n += 1
            except Exception:
                pass
    return n


# ----------------------------------------------------------------------------- brief
def write_brief(cid, overwrite=False):
    plan = load_plan()
    v, c = find_chapter(plan, cid)
    if not c:
        raise KeyError(cid)
    if not c["frozen"]:
        raise ValueError("approve the chapter first (approval freezes its sources)")
    d = chapter_dir(c)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "BRIEF.md")
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(path)
    srcs = [plan["sources"][s] for s in c["sources"] if s in plan["sources"]]
    contract = open(os.path.join(WORKER_SPEC, "WORKER_CONTRACT.md"), encoding="utf-8").read().rstrip()
    out = os.path.join(d, "CHAPTER.md")
    lines = []
    for s in srcs:
        lines.append(f"- {working_copy(s['path'])}   ({s.get('words') or '?'} words; {s['origin']}; "
                     f"a COPY in the working clone; the original stays untouched at {s['path']})")
        for p in screenshot_files(s["path"]):      # the text inside that note's screenshots is part of the source
            lines.append(f"  - screenshot text of that note: {p}")
    inputs = "\n".join(lines)
    body = f"""

---

## TASK
REWRITE-READER job, output class reader, task id {cid}: write one chapter of the book volume "{v['title']}" as a lossless natural-language synthesis of the {len(srcs)} source files listed under INPUTS (about {c['words']:,} source words).

## CONTEXT
Volume: {v['title']}. Purpose of the volume: {v.get('purpose', '')}
Chapter working title: {c['title']} (rename it to what the material is actually about).
Reader: James and the people he teaches and debates (Catholic and Protestant family, Discord): intelligent non-specialists who want the material beyond the basics, in flowing prose a learned colleague would write.
How to write it (these are the acceptance criteria; the integrator checks them):
1. Read every source completely before you plan the chapter. Write to disk section by section; if CHAPTER.md already exists without the completion marker, continue it.
2. Keep every fact, name, date, number, scripture or page reference, manuscript siglum, quotation (verbatim, in the original language and in translation), evidence tag ([V], [R], [S]) with its exact wording, concession and argument from EVERY source. Nothing may be summarised away. If two sources say the same thing in the same words, say it once; if they differ in any detail, give both and state the difference.
3. Organise by subject for a reader, not source by source: headings, a short opening that says what the chapter establishes, then the argument in a logical order, then the objections and answers.
4. Remove machinery: file names, folder paths, AI or tool names, task or track labels, "dossier", "subagent", "workflow". A mistake in an earlier source becomes "a claim found in earlier drafts".
5. Add no fact that is not in a source. Your own connective inference is allowed only where needed for flow and is tagged [S]. Some sources are conversations (James's question, then an AI's answer): James's questions show what the chapter must answer; an AI's answer is a claim, tagged [S] unless it names a source you can check.
6. Concede first: the strongest version of the opposing case appears before the answer, as the sources give it.
7. End with "What this chapter still owes": every item any source lists as still to check, fetch or answer, plus every conflict you could not settle.
After you finish, the integrator runs data_check.py of each source against your chapter (numbers, references, sigla, Greek, Hebrew, quotations, tags), and an Opus judge reads it for lost caveats and changed attributions.

## QUESTIONS
1. What, in continuous natural prose, does the combined material of all the sources under INPUTS establish about the chapter's subject, with every fact, quotation and evidence tag of every source carried over?
2. Where do the sources overlap or disagree, and what exactly does each one say?
3. Which items do the sources themselves list as still needing checking, fetching or answering?

## INPUTS
{inputs}

## OWNED FILES
- {d}\\

## OUTPUT
{out}

## FORBIDDEN
- Editing, moving or deleting any source file.
- Opening James's original files: read only the clone copies listed under INPUTS (CLONE_FOR_SORTING_...).
- Writing anywhere except the chapter folder above.
- Reading anything under {PROJECT}\\06_SOURCE_MATERIAL\\_SESSION_TRANSCRIPTS.

## STOP CONDITIONS
- Stop when the chapter covers every source and ends with its completion marker, or when a usage limit hits (leave CHAPTER.md PARTIAL; the next worker continues it).

## COMPLETION MARKER
<!-- WORKER COMPLETE: {cid} -->

## GATE
python "{os.path.join(WORKER_SPEC, 'worker_gates.py')}" handback "{out}" --class reader --task-id {cid}
"""
    with open(path, "w", encoding="utf-8", newline="\n") as w:
        w.write(contract + body)
    gate = subprocess.run([sys.executable, os.path.join(WORKER_SPEC, "worker_gates.py"), "brief", path],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    result = next((l.strip() for l in gate.stdout.splitlines() if "RESULT:" in l), "RESULT: unknown")
    return {"brief": path, "gate": result, "gate_exit": gate.returncode,
            "launch_prompt": launch_prompt(path)}


def launch_prompt(brief_path):
    return ("Your complete brief is in this file. Read it in full first and follow it exactly, including the "
            f"contract at its top:\n\n{brief_path}\n\nWrite CHAPTER.md section by section. Before finishing, run the "
            "GATE command at the bottom of the brief, fix every FAIL, and re-run until RESULT: PASS. Your final "
            "message must be exactly the section 7 format from the contract.")


# ----------------------------------------------------------------------------- checks
_DC_LINE = re.compile(r"(\d+) data items, (\d+) missing")


def run_checks(cid):
    plan = load_plan()
    v, c = find_chapter(plan, cid)
    if not c:
        raise KeyError(cid)
    d = chapter_dir(c)
    out = os.path.join(d, "CHAPTER.md")
    if not os.path.exists(out):
        raise FileNotFoundError(out)
    gate = subprocess.run([sys.executable, os.path.join(WORKER_SPEC, "worker_gates.py"), "handback", out,
                           "--class", "reader", "--task-id", cid], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    gate_res = next((l.strip() for l in gate.stdout.splitlines() if "RESULT:" in l), "RESULT: unknown")
    per = {}
    items = missing = 0
    worst = None
    for sid in c["sources"]:
        s = plan["sources"].get(sid)
        if not s or not os.path.exists(s["path"]) or not s["path"].lower().endswith((".md", ".txt")):
            per[sid] = {"path": s["path"] if s else sid, "skipped": "not a text source"}
            continue
        r = subprocess.run([sys.executable, DATA_CHECK, s["path"], out, "--list"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        m = _DC_LINE.search(r.stdout)
        if not m:
            per[sid] = {"path": s["path"], "error": (r.stdout + r.stderr)[-300:]}
            continue
        it, mi = int(m.group(1)), int(m.group(2))
        miss = [l.strip() for l in r.stdout.splitlines() if l.strip().startswith("MISSING")][:40]
        per[sid] = {"path": s["path"], "items": it, "missing": mi, "missing_list": miss}
        items += it
        missing += mi
        ratio = mi / it if it else 0
        if worst is None or ratio > worst["ratio"]:
            worst = {"path": s["path"], "ratio": round(ratio, 3), "missing": mi, "items": it}
    res = {"at": _now(), "chapter": cid, "gate": gate_res, "gate_output": gate.stdout[-3000:],
           "sources_checked": sum(1 for x in per.values() if "items" in x), "items": items, "missing": missing,
           "worst": worst, "per_source": per,
           "note": "data_check counts tokens; 'missing' includes machinery that the brief told the writer to remove. "
                   "A judge read (JUDGE.md) is still required before final."}
    _write_json(os.path.join(d, "CHECK.json"), res)
    return res


# ----------------------------------------------------------------------------- assembly
def assemble_volume(vid):
    plan = load_plan()
    vol = next((v for v in plan["volumes"] if v["id"] == vid), None)
    if not vol:
        raise KeyError(vid)
    ready = [c for c in vol["chapters"] if c["state"] in ("drafted", "checked", "judged", "final")]
    vdir = os.path.join(VOLUMES_DIR, vid)
    os.makedirs(vdir, exist_ok=True)
    out = os.path.join(vdir, f"VOLUME_{vid}_{slug(vol['title'], 60)}.md")
    lines = [f"# {vol['title']}", "", f"*{vol.get('purpose', '')}*", "",
             f"Assembled {_now()[:10]} from {len(ready)} chapter(s). Chapters not yet drafted are listed at the end.", "",
             "## Contents", ""]
    bodies = []
    for i, c in enumerate(ready, 1):
        with open(os.path.join(chapter_dir(c), "CHAPTER.md"), encoding="utf-8", errors="replace") as fh:
            txt = MARKER_RE.sub("", fh.read()).rstrip()
        m = re.search(r"^#\s+(.+)$", txt, re.M)
        title = m.group(1).strip() if m else c["title"]
        lines.append(f"{i}. {title} ({c['state']})")
        txt = re.sub(r"^#\s+.+$", "", txt, count=1, flags=re.M).strip()
        bodies.append(f"\n\n## {i}. {title}\n\n{txt}\n")
    pending = [c for c in vol["chapters"] if c not in ready]
    lines += bodies
    lines += ["", "## Sources of this volume", ""]
    for c in ready:
        lines.append(f"- Chapter \"{c['title']}\": {c['n_sources']} sources, {c['words']:,} words")
    if pending:
        lines += ["", "## Not yet drafted", ""] + [f"- {c['title']} ({c['state']}, {c['n_sources']} sources)" for c in pending]
    with open(out, "w", encoding="utf-8", newline="\n") as w:
        w.write("\n".join(lines) + "\n")
    return {"volume": out, "chapters_included": len(ready), "pending": len(pending)}


def plan_summary(plan):
    tot = Counter()
    for v in plan["volumes"]:
        for c in v["chapters"]:
            tot[c["state"]] += 1
    words_done = sum(c["words"] for v in plan["volumes"] for c in v["chapters"] if c["state"] in ("drafted", "checked", "judged", "final"))
    words_all = sum(v["words"] for v in plan["volumes"])
    return {"built_at": plan["built_at"], "seconds": plan["seconds"], "pool": plan["pool"], "chapter_states": dict(tot),
            "chapters": sum(tot.values()), "source_words": words_all, "words_synthesised": words_done,
            "percent_synthesised": round(100 * words_done / words_all, 2) if words_all else 0,
            "volumes": [{"id": v["id"], "title": v["title"], "n_sources": v["n_sources"], "words": v["words"],
                         "chapters": len(v["chapters"]), "states": v["states"]} for v in plan["volumes"]]}
