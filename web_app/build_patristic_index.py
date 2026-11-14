#!/usr/bin/env python3
"""Index Migne Patrologia Latina (PL), Patrologia Graeca (PG), and Schaff ANF/NPNF PDFs
into `patristic_index` and `patristic_fts` in `plenary_logos.sqlite`.

Extracts:
  1. Volume/TOC catalog rows for Migne PL (193 vols), Migne PG (161 vols), and Schaff ANF/NPNF.
  2. Verse-by-verse Patristic citations across all 38 Schaff ANF/NPNF PDFs (~47,700 pages),
     attributing Father author + treatise title from the PDF TOC, capturing rich surrounding
     commentary excerpts and exact PDF page numbers (`p. {page_num}`).

Idempotent: clears and rebuilds `patristic_index` and `patristic_fts` without
touching `verses`, `notes`, or any other tables.
"""

from __future__ import annotations

import re
import sqlite3
import time
from bisect import bisect_right
from pathlib import Path

import fitz  # PyMuPDF

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "plenary_logos.sqlite"
PATRISTICS_ROOT = Path(r"C:\Users\Elation\PDFS\02_Patristics_and_Church_Fathers")

PL_DIR = PATRISTICS_ROOT / "Migne_Patrologia_Latina"
PG_DIR = PATRISTICS_ROOT / "Migne_Patrologia_Graeca"
SCHAFF_DIR = PATRISTICS_ROOT / "Schaff_ANF_NPNF"

_PL_RE = re.compile(
    r"Patrologia_Latina_(\d+)(?:_\(([^)]+)\))?(?:_(.+?))?(?:,_MLT)?\.pdf$",
    re.IGNORECASE,
)
_PG_RE = re.compile(
    r"PG_(\d+)_(?:\(([^)]+)\)|\[([^\]]+)\])_(.+?)(?:,_[A-Z]+)?\.pdf$",
    re.IGNORECASE,
)
_SCHAFF_RE = re.compile(r"^(anf|npnf1|npnf2)(\d+)\.pdf$", re.IGNORECASE)

# Single-author volumes -> guaranteed Father attribution
_SCHAFF_VOL_DEFAULT_AUTHOR: dict[str, str] = {
    "anf03": "Tertullian",
    "npnf101": "St. Augustine of Hippo",
    "npnf102": "St. Augustine of Hippo",
    "npnf103": "St. Augustine of Hippo",
    "npnf104": "St. Augustine of Hippo",
    "npnf105": "St. Augustine of Hippo",
    "npnf106": "St. Augustine of Hippo",
    "npnf107": "St. Augustine of Hippo",
    "npnf108": "St. Augustine of Hippo",
    "npnf109": "St. John Chrysostom",
    "npnf110": "St. John Chrysostom",
    "npnf111": "St. John Chrysostom",
    "npnf112": "St. John Chrysostom",
    "npnf113": "St. John Chrysostom",
    "npnf114": "St. John Chrysostom",
    "npnf201": "Eusebius of Caesarea",
    "npnf204": "St. Athanasius of Alexandria",
    "npnf205": "St. Gregory of Nyssa",
    "npnf206": "St. Jerome",
    "npnf208": "St. Basil the Great",
    "npnf210": "St. Ambrose of Milan",
    "npnf214": "Seven Ecumenical Councils",
}

# Canonical + Deuterocanonical book aliases -> `books.id`
# Case-insensitive keys normalized by stripping spaces/dots where appropriate inside regex
_BOOK_ALIASES: list[tuple[str, tuple[str, ...]]] = [
    ("gen", ("Genesis", "Gen", "Gn")),
    ("exod", ("Exodus", "Exod", "Ex")),
    ("lev", ("Leviticus", "Lev", "Lv")),
    ("num", ("Numbers", "Num", "Numb", "Nm")),
    ("deut", ("Deuteronomy", "Deut", "Deu", "Dt")),
    ("josh", ("Joshua", "Josh", "Jos")),
    ("judg", ("Judges", "Judg", "Jdg")),
    ("ruth", ("Ruth", "Ru")),
    ("1sam", ("1 Samuel", "1 Sam", "I Samuel", "I Sam", "1 Sa", "I Sa", "1 Kings LXX")),
    ("2sam", ("2 Samuel", "2 Sam", "II Samuel", "II Sam", "2 Sa", "II Sa")),
    ("1kgs", ("1 Kings", "1 Kgs", "1 Ki", "I Kings", "I Kgs", "I Ki", "3 Kings", "III Kings")),
    ("2kgs", ("2 Kings", "2 Kgs", "2 Ki", "II Kings", "II Kgs", "II Ki", "4 Kings", "IV Kings")),
    ("1chr", ("1 Chronicles", "1 Chron", "1 Chr", "1 Ch", "I Chronicles", "I Chron", "I Chr", "1 Paralipomenon", "1 Par")),
    ("2chr", ("2 Chronicles", "2 Chron", "2 Chr", "2 Ch", "II Chronicles", "II Chron", "II Chr", "2 Paralipomenon", "2 Par")),
    ("ezra", ("Ezra", "Ezr", "1 Esdras")),
    ("neh", ("Nehemiah", "Neh", "Ne", "2 Esdras")),
    ("tob", ("Tobit", "Tobias", "Tob")),
    ("jdt", ("Judith", "Jdt")),
    ("esth", ("Esther", "Esth", "Est")),
    ("1macc", ("1 Maccabees", "1 Macc", "1 Mac", "I Maccabees", "I Macc", "I Mac", "1 Machabees")),
    ("2macc", ("2 Maccabees", "2 Macc", "2 Mac", "II Maccabees", "II Macc", "II Mac", "2 Machabees")),
    ("job", ("Job", "Jb")),
    ("ps", ("Psalms", "Psalm", "Pss", "Ps")),
    ("prov", ("Proverbs", "Prov", "Prv", "Pr")),
    ("eccl", ("Ecclesiastes", "Eccles", "Eccl", "Qoh")),
    ("song", ("Song of Solomon", "Song of Songs", "Canticles", "Cant", "Song", "Canticle")),
    ("wis", ("Wisdom of Solomon", "Wisdom", "Wisd", "Wis", "Sapientia", "Sap")),
    ("sir", ("Ecclesiasticus", "Ecclus", "Sirach", "Sir", "Eccli")),
    ("isa", ("Isaiah", "Isa", "Isaias", "Is")),
    ("jer", ("Jeremiah", "Jeremias", "Jer", "Jr")),
    ("lam", ("Lamentations", "Lam", "La")),
    ("bar", ("Baruch", "Bar")),
    ("ezek", ("Ezekiel", "Ezek", "Ezechiel", "Ezech", "Ez")),
    ("dan", ("Daniel", "Dan", "Dn")),
    ("hos", ("Hosea", "Hos", "Osee")),
    ("joel", ("Joel", "Jl")),
    ("amos", ("Amos", "Am")),
    ("obad", ("Obadiah", "Obad", "Ob", "Abdias")),
    ("jonah", ("Jonah", "Jonas", "Jon")),
    ("mic", ("Micah", "Mic", "Micheas")),
    ("nah", ("Nahum", "Nah", "Na")),
    ("hab", ("Habakkuk", "Hab", "Habacuc")),
    ("zeph", ("Zephaniah", "Zeph", "Sophonias", "Zep")),
    ("hag", ("Haggai", "Hag", "Aggeus")),
    ("zech", ("Zechariah", "Zech", "Zacharias", "Zach", "Zec")),
    ("mal", ("Malachi", "Mal", "Malachias")),
    ("matt", ("Matthew", "St. Matthew", "S. Matthew", "Matt", "Mat", "Mt")),
    ("mark", ("Mark", "St. Mark", "S. Mark", "Mk", "Mr")),
    ("luke", ("Luke", "St. Luke", "S. Luke", "Lk", "Lc")),
    ("john", ("John", "St. John", "S. John", "Jn", "Joh")),
    ("acts", ("Acts of the Apostles", "Acts", "Act")),
    ("rom", ("Romans", "Rom", "Ro", "Rm")),
    ("1cor", ("1 Corinthians", "1 Cor", "1 Co", "I Corinthians", "I Cor", "I Co")),
    ("2cor", ("2 Corinthians", "2 Cor", "2 Co", "II Corinthians", "II Cor", "II Co")),
    ("gal", ("Galatians", "Gal", "Ga")),
    ("eph", ("Ephesians", "Eph", "Ephes")),
    ("phil", ("Philippians", "Phil", "Php")),
    ("col", ("Colossians", "Col")),
    ("1thess", ("1 Thessalonians", "1 Thess", "1 Thes", "1 Th", "I Thessalonians", "I Thess", "I Thes")),
    ("2thess", ("2 Thessalonians", "2 Thess", "2 Thes", "2 Th", "II Thessalonians", "II Thess", "II Thes")),
    ("1tim", ("1 Timothy", "1 Tim", "1 Ti", "I Timothy", "I Tim", "I Ti")),
    ("2tim", ("2 Timothy", "2 Tim", "2 Ti", "II Timothy", "II Tim", "II Ti")),
    ("titus", ("Titus", "Tit")),
    ("phlm", ("Philemon", "Philem", "Phlm", "Phm")),
    ("heb", ("Hebrews", "Heb")),
    ("jas", ("James", "Jas", "Jam", "Jac")),
    ("1pet", ("1 Peter", "1 Pet", "1 Pe", "1 Pt", "I Peter", "I Pet", "I Pe")),
    ("2pet", ("2 Peter", "2 Pet", "2 Pe", "2 Pt", "II Peter", "II Pet", "II Pe")),
    ("1john", ("1 John", "1 Jn", "1 Joh", "I John", "I Jn", "I Joh")),
    ("2john", ("2 John", "2 Jn", "2 Joh", "II John", "II Jn", "II Joh")),
    ("3john", ("3 John", "3 Jn", "3 Joh", "III John", "III Jn", "III Joh")),
    ("jude", ("Jude", "Jud")),
    ("rev", ("Revelation", "Apocalypse", "Apoc", "Rev", "Rv")),
]

_SINGLE_CHAPTER_BOOKS = {"obad", "phlm", "2john", "3john", "jude"}

# Build alias lookup & compiled regex (longest aliases first so "1 John" beats "John")
_ALIAS_TO_ID: dict[str, str] = {}
_ALL_ALIASES: list[str] = []
for bid, names in _BOOK_ALIASES:
    for n in names:
        key = re.sub(r"\s+", " ", n.replace(".", "").strip().lower())
        _ALIAS_TO_ID[key] = bid
        # Regex fragment allowing optional dots after tokens like "St.", "1", "Matt."
        frag = r"\s+".join(re.escape(tok) + r"\.?" for tok in n.replace(".", "").split())
        _ALL_ALIASES.append((len(n), frag))

_ALL_ALIASES.sort(key=lambda x: -x[0])
_BOOK_ALT_PATTERN = "|".join(frag for _, frag in _ALL_ALIASES)

# Matches e.g.:
#   Matt. xvi. 18
#   Matt. xvi. 18, 19
#   1 Cor. xi. 24-26
#   John 6:53
#   Gen. 1. 1
#   Jude 3
_CIT_RE = re.compile(
    rf"(?<![A-Za-z0-9])(?P<book>{_BOOK_ALT_PATTERN})\s+"
    rf"(?P<c1>[ivxlcdm]+|\d+)"
    rf"(?:\s*(?:[:.]\s*|\s+)(?P<v1>\d+)(?:\s*[-–]\s*(?P<v2>\d+))?)?"
    rf"(?![A-Za-z])",
    re.IGNORECASE,
)

_ROMAN_RE = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)
_ROMAN_VALS = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}

# Author detection keywords inside anthology L1/L2 headings
_FATHER_HINTS: list[tuple[str, str]] = [
    ("clement of rome", "St. Clement of Rome"),
    ("mathetes", "Epistle to Diognetus (Mathetes)"),
    ("polycarp", "St. Polycarp of Smyrna"),
    ("ignatius", "St. Ignatius of Antioch"),
    ("barnabas", "Epistle of Barnabas"),
    ("papias", "Papias of Hierapolis"),
    ("justin martyr", "St. Justin Martyr"),
    ("justin", "St. Justin Martyr"),
    ("irenaeus", "St. Irenaeus of Lyons"),
    ("irenæus", "St. Irenaeus of Lyons"),
    ("hermas", "Shepherd of Hermas"),
    ("tatian", "Tatian the Assyrian"),
    ("theophilus", "St. Theophilus of Antioch"),
    ("athenagoras", "Athenagoras of Athens"),
    ("clement of alexandria", "Clement of Alexandria"),
    ("tertullian", "Tertullian"),
    ("minucius felix", "Minucius Felix"),
    ("commodian", "Commodianus"),
    ("origen", "Origen of Alexandria"),
    ("hippolytus", "St. Hippolytus of Rome"),
    ("cyprian", "St. Cyprian of Carthage"),
    ("caius", "Caius of Rome"),
    ("novatian", "Novatian"),
    ("gregory thaumaturgus", "St. Gregory Thaumaturgus"),
    ("dionysius", "St. Dionysius of Alexandria"),
    ("julius africanus", "Julius Africanus"),
    ("anatolius", "St. Anatolius of Laodicea"),
    ("methodius", "St. Methodius of Olympus"),
    ("arnobius", "Arnobius of Sicca"),
    ("lactantius", "Lactantius"),
    ("venantius", "Venantius"),
    ("asterius", "Asterius Urbanus"),
    ("victorinus", "St. Victorinus of Pettau"),
    ("apostolic teaching", "Didache / Apostolic Constitutions"),
    ("apostolic constitutions", "Apostolic Constitutions"),
    ("teaching of the twelve", "Didache"),
    ("aristides", "Aristides of Athens"),
    ("socrates", "Socrates Scholasticus"),
    ("sozomen", "Sozomen"),
    ("theodoret", "Theodoret of Cyrus"),
    ("jerome", "St. Jerome"),
    ("gennadius", "Gennadius of Massilia"),
    ("rufinus", "Rufinus of Aquileia"),
    ("cyril", "St. Cyril of Jerusalem"),
    ("gregory nazianzen", "St. Gregory of Nazianzus"),
    ("hilary", "St. Hilary of Poitiers"),
    ("john of damascus", "St. John of Damascus"),
    ("sulpitius severus", "Sulpicius Severus"),
    ("vincent of lerins", "St. Vincent of Lérins"),
    ("vincent of lérins", "St. Vincent of Lérins"),
    ("john cassian", "St. John Cassian"),
    ("leo the great", "Pope St. Leo the Great"),
    ("gregory the great", "Pope St. Gregory the Great"),
    ("ephraim", "St. Ephrem the Syrian"),
    ("ephraim", "St. Ephrem the Syrian"),
    ("aphrahat", "Aphrahat the Persian Sage"),
    ("athanasius", "St. Athanasius of Alexandria"),
    ("augustin", "St. Augustine of Hippo"),
    ("chrysostom", "St. John Chrysostom"),
    ("ambrose", "St. Ambrose of Milan"),
    ("basil", "St. Basil the Great"),
    ("gregory of nyssa", "St. Gregory of Nyssa"),
    ("eusebius", "Eusebius of Caesarea"),
]

_SKIP_TOC_LOWER = (
    "cover",
    "about this book",
    "table of contents",
    "title page",
    "second title page",
    "series title page",
    "related books",
    "editorial preface",
    "preface to the american edition",
    "preface",
    "credits",
    "indexes",
    "index of subjects",
    "index of texts",
    "index of scripture",
    "a comprehensive general index",
    "general indexes",
    "subject index",
    "subject indexes",
)


def _roman_to_int(s: str) -> int | None:
    s = s.strip().lower()
    if not s or not _ROMAN_RE.match(s):
        return None
    total = 0
    prev = 0
    for ch in reversed(s):
        v = _ROMAN_VALS[ch]
        if v < prev:
            total -= v
        else:
            total += v
            prev = v
    if total <= 0 or total > 176:
        return None
    return total


def _parse_int_or_roman(token: str | None) -> int | None:
    if not token:
        return None
    t = token.strip()
    if t.isdigit():
        val = int(t)
        return val if 1 <= val <= 176 else None
    return _roman_to_int(t)


def _infer_father_from_heading(heading: str, fallback: str) -> str:
    low = heading.lower()
    for needle, label in _FATHER_HINTS:
        if needle in low:
            return label
    return fallback


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA synchronous = NORMAL;

        CREATE TABLE IF NOT EXISTS patristic_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series TEXT NOT NULL,
            volume INTEGER NOT NULL,
            author TEXT,
            work_title TEXT,
            book_id TEXT,
            chapter INTEGER,
            verse INTEGER,
            page_or_col TEXT,
            excerpt TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_patristic_bcv
            ON patristic_index(book_id, chapter, verse);

        CREATE VIRTUAL TABLE IF NOT EXISTS patristic_fts USING fts5(
            patristic_id UNINDEXED,
            series UNINDEXED,
            volume UNINDEXED,
            author,
            work_title,
            excerpt,
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def _clean_underscores(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("_", " ")).strip(" ,._-")


def _infer_pg_author(title_str: str) -> str:
    if "." in title_str:
        head = title_str.split(".", 1)[0].strip()
        if head:
            return head
    for marker in (" Opera ", " Epistolae", " Homiliae", " Commentarii", " et Aliorum"):
        idx = title_str.find(marker)
        if idx > 0:
            return title_str[:idx].strip(" ,.")
    return title_str


def _inspect_pdf(pdf_path: Path) -> tuple[int, dict[str, str], list]:
    with fitz.open(str(pdf_path)) as doc:
        page_count = doc.page_count
        meta = {k: (v or "").strip() for k, v in (doc.metadata or {}).items() if v}
        toc = doc.get_toc(simple=True) or []
    return page_count, meta, toc


def _scan_migne_pl(rows: list[tuple]) -> int:
    if not PL_DIR.is_dir():
        print(f"[WARN] Missing PL directory: {PL_DIR}")
        return 0
    count = 0
    for pdf_path in sorted(PL_DIR.glob("*.pdf")):
        m = _PL_RE.search(pdf_path.name)
        if not m:
            continue
        vol = int(m.group(1))
        year_tag = _clean_underscores(m.group(2) or "")
        prov_tag = _clean_underscores(m.group(3) or "")
        page_count, meta, toc = _inspect_pdf(pdf_path)

        author = meta.get("author") or "Jacques-Paul Migne (ed.)"
        title_parts = [f"Patrologia Latina, Vol. {vol:03d}"]
        if year_tag:
            title_parts.append(f"({year_tag})")
        if prov_tag:
            title_parts.append(f"— {prov_tag}")
        work_title = " ".join(title_parts)

        excerpt_parts = [
            f"Series: Migne Patrologia Latina (PL {vol:03d})",
            f"File: {pdf_path.name}",
            f"Pages: {page_count}",
        ]
        if meta.get("title"):
            excerpt_parts.append(f"Title: {meta['title']}")
        if toc:
            toc_titles = [t[1].strip() for t in toc[:25] if len(t) >= 2 and t[1].strip()]
            if toc_titles:
                excerpt_parts.append("Contents: " + "; ".join(toc_titles))

        rows.append(("PL", vol, author, work_title, None, None, None, f"{page_count} pp.", " | ".join(excerpt_parts)))
        count += 1
    return count


def _scan_migne_pg(rows: list[tuple]) -> int:
    if not PG_DIR.is_dir():
        print(f"[WARN] Missing PG directory: {PG_DIR}")
        return 0
    count = 0
    for pdf_path in sorted(PG_DIR.glob("*.pdf")):
        m = _PG_RE.search(pdf_path.name)
        if not m:
            continue
        vol = int(m.group(1))
        subpart = (m.group(2) or m.group(3) or "").strip()
        raw_title = _clean_underscores(m.group(4) or "")
        page_count, meta, toc = _inspect_pdf(pdf_path)

        author = _infer_pg_author(raw_title) if raw_title else (meta.get("author") or "Jacques-Paul Migne (ed.)")
        sub_label = f", {subpart}" if subpart else ""
        work_title = f"{raw_title} (PG {vol:03d}{sub_label})" if raw_title else f"Patrologia Graeca, Vol. {vol:03d}{sub_label}"

        excerpt_parts = [
            f"Series: Migne Patrologia Graeca (PG {vol:03d}{sub_label})",
            f"Author/Work: {raw_title}",
            f"File: {pdf_path.name}",
            f"Pages: {page_count}",
        ]
        if meta.get("title"):
            excerpt_parts.append(f"Metadata Title: {meta['title']}")
        if toc:
            toc_titles = [t[1].strip() for t in toc[:25] if len(t) >= 2 and t[1].strip()]
            if toc_titles:
                excerpt_parts.append("Contents: " + "; ".join(toc_titles))

        rows.append(("PG", vol, author, work_title, None, None, None, f"{page_count} pp.", " | ".join(excerpt_parts)))
        count += 1
    return count


def _build_page_map(toc: list, page_count: int, vol_stem: str) -> tuple[list[tuple[int, str, str]], int, int]:
    """Return sorted [(start_page_1idx, author, work_title)] and (body_start, index_start)."""
    default_author = _SCHAFF_VOL_DEFAULT_AUTHOR.get(vol_stem, "Early Church Father")
    current_author = default_author
    current_l1 = ""
    current_l2 = ""
    entries: list[tuple[int, str, str]] = []
    index_start = page_count + 1
    body_start = 1

    found_first_work = False
    for lvl, raw_title, pg in toc:
        title = re.sub(r"\s+", " ", (raw_title or "")).strip()
        pg = int(pg)
        low = title.lower().strip(" .:")
        if any(low == k or low.startswith(k + " ") for k in ("indexes", "index of subjects", "index of texts", "index of scripture", "a comprehensive general index", "general indexes", "subject index", "subject indexes")):
            if pg > 30 and pg < index_start:
                index_start = pg
            continue
        if low in _SKIP_TOC_LOWER or low.startswith("related books"):
            continue
        if not found_first_work and pg >= 8:
            body_start = pg
            found_first_work = True
        if lvl == 1:
            current_l1 = title
            current_l2 = ""
            current_author = _infer_father_from_heading(title, _SCHAFF_VOL_DEFAULT_AUTHOR.get(vol_stem, current_author))
        elif lvl == 2:
            current_l2 = title
            # Check L2 too for anthologies like Theodoret/Jerome/Rufinus
            current_author = _infer_father_from_heading(title, _infer_father_from_heading(current_l1, _SCHAFF_VOL_DEFAULT_AUTHOR.get(vol_stem, current_author)))
        else:
            current_l2 = current_l2 or current_l1
        work = f"{current_l1} — {title}" if (lvl >= 2 and current_l1 and title != current_l1) else (title or current_l1)
        if len(work) > 150:
            work = work[:147] + "..."
        entries.append((pg, current_author, work))

    # Ensure page ordering for bisect_right
    entries.sort(key=lambda x: x[0])
    return entries, body_start, index_start


def _clean_page_excerpt(page_text: str, match_start: int, match_end: int) -> str:
    """Build a crisp 320-380 char patristic quote snippet around a Scripture citation."""
    # If the citation appears in a short footnote line at the bottom (e.g. "511\nMatt. iii. 15, 16."),
    # walk upward past the footnote cluster to grab the actual Father prose paragraph above the footnotes!
    line_start = page_text.rfind("\n", 0, match_start) + 1
    line_end = page_text.find("\n", match_end)
    if line_end == -1:
        line_end = len(page_text)
    cur_line = page_text[line_start:line_end].strip()

    # Check if cur_line is short/mostly a bare citation (e.g. "Matt. xvi. 18." or "511 Matt. iii. 15, 16.")
    if len(cur_line) < 95:
        # Look backward up to 650 chars for prose lines (longer than 45 chars, not pure numbers)
        lookback = page_text[max(0, line_start - 700):line_start]
        prose_lines = []
        for ln in lookback.splitlines():
            s = ln.strip()
            if not s or s.isdigit():
                continue
            # skip bare verse reference footnote lines so we reach main body text
            if len(s) < 42 and _CIT_RE.search(s):
                continue
            prose_lines.append(s)
        prose = " ".join(prose_lines[-5:]).strip()
        if len(prose) > 300:
            prose = "..." + prose[-295:]
        if prose:
            return f"{prose} [Ref: {cur_line}]"

    # Otherwise extract balanced window around inline citation
    win_start = max(0, match_start - 180)
    win_end = min(len(page_text), match_end + 190)
    raw = page_text[win_start:win_end]
    raw = re.sub(r"\s+", " ", raw).strip()
    if win_start > 0:
        raw = "..." + raw
    if win_end < len(page_text):
        raw = raw + "..."
    return raw


def _scan_schaff(rows: list[tuple]) -> tuple[int, int]:
    if not SCHAFF_DIR.is_dir():
        print(f"[WARN] Missing Schaff directory: {SCHAFF_DIR}")
        return 0, 0
    vol_files = 0
    verse_hits = 0

    for pdf_path in sorted(SCHAFF_DIR.glob("*.pdf")):
        m = _SCHAFF_RE.match(pdf_path.name)
        if not m:
            continue
        vol_stem = pdf_path.stem.lower()
        subseries = m.group(1).lower()
        num = int(m.group(2))
        if subseries == "anf":
            vol = num
            label = f"ANF {num:02d}"
        elif subseries == "npnf1":
            vol = 100 + num
            label = f"NPNF1 {num:02d}"
        else:
            vol = 200 + num
            label = f"NPNF2 {num:02d}"

        with fitz.open(str(pdf_path)) as doc:
            page_count = doc.page_count
            meta = {k: (v or "").strip() for k, v in (doc.metadata or {}).items() if v}
            toc = doc.get_toc(simple=True) or []

            author_default = _SCHAFF_VOL_DEFAULT_AUTHOR.get(vol_stem, meta.get("author") or "Philip Schaff (ed.)")
            work_title_vol = meta.get("title") or f"{label} ({pdf_path.name})"

            l1_entries = [
                (t[1].strip(), int(t[2]))
                for t in toc
                if len(t) >= 3 and t[0] == 1 and t[1].strip()
            ]
            toc_summary = "; ".join(title for title, _ in l1_entries[:25])
            excerpt_parts = [
                f"Series: Schaff {label}",
                f"File: {pdf_path.name}",
                f"Pages: {page_count}",
            ]
            if toc_summary:
                excerpt_parts.append(f"Treatises: {toc_summary}")

            # 1. Keep Volume & L1 treatise metadata rows
            rows.append(("SCHAFF", vol, author_default, work_title_vol, None, None, None, f"{page_count} pp.", " | ".join(excerpt_parts)))
            for sec_title, sec_page in l1_entries:
                rows.append(("SCHAFF", vol, _infer_father_from_heading(sec_title, author_default), f"[{label}] {sec_title}", None, None, None, f"p. {sec_page}", f"{work_title_vol} — {sec_title} (p. {sec_page}, {pdf_path.name})"))

            # Skip anf10 (General Index volume — index entries, not primary Father prose)
            if vol_stem == "anf10":
                vol_files += 1
                continue

            toc_map, body_start, index_start = _build_page_map(toc, page_count, vol_stem)
            toc_pages = [e[0] for e in toc_map]

            # 2. Scan interior treatise pages for verse citations
            for pg_idx in range(max(0, body_start - 1), min(page_count, index_start - 1)):
                page_num = pg_idx + 1
                txt = doc[pg_idx].get_text("text")
                if not txt or len(txt) < 80:
                    continue

                # Determine Father author + treatise at this page
                idx = bisect_right(toc_pages, page_num) - 1
                if idx >= 0:
                    _, cur_author, cur_work = toc_map[idx]
                else:
                    cur_author, cur_work = author_default, work_title_vol
                full_work = f"[{label}] {cur_work}"

                seen_page_bcv: set[tuple[str, int, int]] = set()
                for cm in _CIT_RE.finditer(txt):
                    raw_book = re.sub(r"\s+", " ", cm.group("book").replace(".", "").strip().lower())
                    book_id = _ALIAS_TO_ID.get(raw_book)
                    if not book_id:
                        continue

                    c1 = _parse_int_or_roman(cm.group("c1"))
                    v1_str = cm.group("v1")
                    if book_id in _SINGLE_CHAPTER_BOOKS and v1_str is None:
                        # Single-chapter epistle written as "Jude 3" or "Philem. 10"
                        chap = 1
                        v1 = c1
                    else:
                        if v1_str is None:
                            continue  # Skip bare chapter references without verse precision
                        chap = c1
                        v1 = int(v1_str) if v1_str.isdigit() else None

                    if not chap or not v1 or v1 < 1 or v1 > 176:
                        continue

                    v2_str = cm.group("v2")
                    v2 = int(v2_str) if (v2_str and v2_str.isdigit()) else v1
                    if v2 < v1 or (v2 - v1) > 4:
                        v2 = v1

                    excerpt = _clean_page_excerpt(txt, cm.start(), cm.end())
                    for v_num in range(v1, v2 + 1):
                        key = (book_id, chap, v_num)
                        if key in seen_page_bcv:
                            continue
                        seen_page_bcv.add(key)
                        rows.append(
                            (
                                "SCHAFF",
                                vol,
                                cur_author,
                                full_work,
                                book_id,
                                chap,
                                v_num,
                                f"p. {page_num}",
                                excerpt,
                            )
                        )
                        verse_hits += 1

        vol_files += 1
        print(f"  [SCHAFF] {pdf_path.name}: {page_count} pp. | cumulative verse_hits={verse_hits}")

    return vol_files, verse_hits


def build_patristic_index(db_path: Path = DB_PATH) -> dict[str, int | float]:
    t0 = time.perf_counter()
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    rows: list[tuple] = []
    pl_count = _scan_migne_pl(rows)
    pg_count = _scan_migne_pg(rows)
    schaff_files, verse_hits = _scan_schaff(rows)

    conn = sqlite3.connect(str(db_path))
    try:
        _ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("DELETE FROM patristic_index")
        cur.execute("DELETE FROM patristic_fts")

        cur.executemany(
            """
            INSERT INTO patristic_index
                (series, volume, author, work_title, book_id, chapter, verse, page_or_col, excerpt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )

        cur.execute(
            """
            INSERT INTO patristic_fts (patristic_id, series, volume, author, work_title, excerpt)
            SELECT id, series, volume, COALESCE(author, ''), COALESCE(work_title, ''), COALESCE(excerpt, '')
            FROM patristic_index
            """
        )

        conn.commit()
        total_idx = cur.execute("SELECT COUNT(*) FROM patristic_index").fetchone()[0]
        total_fts = cur.execute("SELECT COUNT(*) FROM patristic_fts").fetchone()[0]
    finally:
        conn.close()

    elapsed = time.perf_counter() - t0
    return {
        "pl_pdfs": pl_count,
        "pg_pdfs": pg_count,
        "schaff_pdfs": schaff_files,
        "schaff_verse_hits": verse_hits,
        "patristic_index_rows": total_idx,
        "patristic_fts_rows": total_fts,
        "elapsed_sec": round(elapsed, 2),
    }


if __name__ == "__main__":
    stats = build_patristic_index()
    print(
        f"Patristic index rebuilt in {stats['elapsed_sec']}s: "
        f"PL={stats['pl_pdfs']} PDFs, PG={stats['pg_pdfs']} PDFs, "
        f"SCHAFF={stats['schaff_pdfs']} PDFs | "
        f"verse_hits={stats['schaff_verse_hits']} | "
        f"patristic_index={stats['patristic_index_rows']} rows, "
        f"patristic_fts={stats['patristic_fts_rows']} rows"
    )
