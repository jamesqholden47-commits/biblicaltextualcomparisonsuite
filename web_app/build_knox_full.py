import fitz
import re
import json
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

WEB_APP = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\web_app"
CACHE_DIR = os.path.join(WEB_APP, "sources_cache")
DL_DIR = r"C:\Users\Elation\Downloads"

DRA_PATH = os.path.join(CACHE_DIR, "DRA.json")
with open(DRA_PATH, "r", encoding="utf-8") as f:
    DRA = json.load(f)

DRA_73_ORDER = list(DRA.keys())

BOOK_NAME_TO_DRA = {
    "GENESIS": "gen", "EXODUS": "exod", "LEVITICUS": "lev", "NUMBERS": "num",
    "DEUTERONOMY": "deut", "JOSHUA": "josh", "JOSUE": "josh", "JUDGES": "judg", "RUTH": "ruth",
    "1 KINGS": "1sam", "2 KINGS": "2sam", "3 KINGS": "1kgs", "4 KINGS": "2kgs",
    "1 PARALIPOMENA": "1chr", "2 PARALIPOMENA": "2chr", "1 ESDRAS": "ezra", "2 ESDRAS": "neh",
    "NEHEMIAS": "neh", "TOBIAS": "tob", "JUDITH": "jdt", "ESTHER": "esth",
    "1 MACHABEES": "1macc", "2 MACHABEES": "2macc", "JOB": "job", "PSALMS": "ps", "PROVERBS": "prov",
    "ECCLESIASTES": "eccl", "CANTICLE OF CANTICLES": "song", "SONG OF SONGS": "song",
    "WISDOM": "wis", "ECCLESIASTICUS": "sir", "ISAIAS": "isa", "JEREMIAS": "jer", "LAMENTATIONS": "lam",
    "BARUCH": "bar", "EZECHIEL": "ezek", "DANIEL": "dan", "OSEE": "hos", "JOEL": "joel", "AMOS": "amos",
    "ABDIAS": "obad", "JONAS": "jonah", "MICHAEAS": "mic", "NAHUM": "nah", "HABACUC": "hab",
    "SOPHONIAS": "zeph", "AGGAEUS": "hag", "ZACHARIAS": "zech", "MALACHIAS": "mal",
    "MATTHEW": "matt", "MARK": "mark", "LUKE": "luke", "JOHN": "john", "ACTS": "acts",
    "ROMANS": "rom", "1 CORINTHIANS": "1cor", "2 CORINTHIANS": "2cor", "GALATIANS": "gal",
    "EPHESIANS": "eph", "PHILIPPIANS": "phil", "COLOSSIANS": "col", "1 THESSALONIANS": "1thess",
    "2 THESSALONIANS": "2thess", "1 TIMOTHY": "1tim", "2 TIMOTHY": "2tim", "TITUS": "titus",
    "PHILEMON": "phlm", "HEBREWS": "heb", "JAMES": "jas", "1 PETER": "1pet", "2 PETER": "2pet",
    "1 JOHN": "1john", "2 JOHN": "2john", "3 JOHN": "3john", "JUDE": "jude", "APOCALYPSE": "rev",
}

pdf_path = os.path.join(DL_DIR, "The Knox Bible -- Anonymous; Ronald Knox -- Leather Bound, 2012 -- Baronius Press Ltd.pdf")
doc = fitz.open(pdf_path)
print(f"Opened Knox PDF: {len(doc)} pages")

parsed_knox = {}
cur_bid = None
cur_ch = 1
cur_v = 1

for pno in range(14, len(doc)):
    page = doc[pno]
    w = page.rect.width
    mid = w / 2.0
    words = page.get_text("words")

    # Header check
    header_words = [w for w in words if w[1] < 45]
    header_text = " ".join(w[4] for w in header_words).upper()
    for k, bid in BOOK_NAME_TO_DRA.items():
        if k in header_text:
            if bid != cur_bid:
                cur_bid = bid
                cur_ch = 1
                cur_v = 1
            break

    if not cur_bid:
        continue

    col1 = [w for w in words if w[0] < mid and w[1] >= 45]
    col2 = [w for w in words if w[0] >= mid and w[1] >= 45]

    for col_idx, col in enumerate([col1, col2]):
        col.sort(key=lambda x: (round(x[1] / 6.0), x[0]))
        for w in col:
            x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
            h = y1 - y0

            if h >= 17.5 and re.match(r'^\d+$', text):
                cnum = int(text)
                if 1 <= cnum <= 150:
                    cur_ch = cnum
                    cur_v = 1
                    continue

            is_margin = (col_idx == 0 and x0 < 44.0) or (col_idx == 1 and x1 > 344.0)
            if is_margin and re.match(r'^\d+$', text):
                vnum = int(text)
                if 1 <= vnum <= 176:
                    cur_v = vnum
                    continue

            if not is_margin and h < 17.5:
                # Filter out running page numbers or footnotes at bottom
                if y0 > 485:
                    continue
                cmap = parsed_knox.setdefault(cur_bid, {}).setdefault(cur_ch, {})
                cmap[cur_v] = (cmap.get(cur_v, "") + " " + text).strip()

print(f"Extracted {len(parsed_knox)} books from Knox Bible:")
total_v = 0
for b in parsed_knox:
    b_v = sum(len(v) for v in parsed_knox[b].values())
    total_v += b_v
print(f"Total verses extracted before alignment: {total_v}")

# Align to exact 73-book DRA structure
aligned_knox = {}
for b in DRA_73_ORDER:
    dra_chaps = DRA[b]
    if b not in parsed_knox:
        aligned_knox[b] = [[""] * len(vc) for vc in dra_chaps]
        continue
    b_chaps = parsed_knox[b]
    ch_list = []
    for c_idx, dra_verses in enumerate(dra_chaps, start=1):
        c_map = b_chaps.get(c_idx, {})
        v_list = []
        for v_idx in range(1, len(dra_verses) + 1):
            v_list.append(c_map.get(v_idx, ""))
        ch_list.append(v_list)
    aligned_knox[b] = ch_list

non_empty = sum(1 for b in aligned_knox.values() for c in b for v in c if v)
out_path = os.path.join(CACHE_DIR, "KNOX.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(aligned_knox, f, ensure_ascii=False)
print(f"KNOX.json successfully written: {non_empty} verses across {len(parsed_knox)} books")
