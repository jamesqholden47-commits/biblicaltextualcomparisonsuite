#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Ingestion for Newly Downloaded Bibles & Study Bibles (2026-11-13/14):
  1. NASB 1995 (EPUB) -> sources_cache/NASB95.json (66 books aligned to Catholic 73-book canon)
  2. CSB Christian Standard Bible (EPUB) -> sources_cache/CSB.json (66 books aligned to Catholic 73-book canon)
  3. Baker Illustrated Study Bible Notes -> notes_shards/<book>.js (src='baker_csb')
  4. Knox Bible (PDF) -> sources_cache/KNOX.json (Catholic 73 books)
  5. Verifies Haydock (1859) & MacArthur Study Bible notes in notes_shards/
"""
import glob
import html as html_mod
import json
import os
import re
import sys
import zipfile
import fitz

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

WEB_APP = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(WEB_APP, "sources_cache")
SHARDS_DIR = os.path.join(WEB_APP, "notes_shards")
DL_DIR = r"C:\Users\Elation\Downloads"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(SHARDS_DIR, exist_ok=True)

DRA_PATH = os.path.join(CACHE_DIR, "DRA.json")
with open(DRA_PATH, "r", encoding="utf-8") as f:
    DRA = json.load(f)

# Canonical 73-book keys in DRA order
DRA_73_ORDER = list(DRA.keys())

# Standard 66 Protestant books mapped to DRA lowercase keys
PROT_66_DRA = [
    'gen', 'exod', 'lev', 'num', 'deut', 'josh', 'judg', 'ruth', '1sam', '2sam',
    '1kgs', '2kgs', '1chr', '2chr', 'ezra', 'neh', 'esth', 'job', 'ps', 'prov',
    'eccl', 'song', 'isa', 'jer', 'lam', 'ezek', 'dan', 'hos', 'joel', 'amos',
    'obad', 'jonah', 'mic', 'nah', 'hab', 'zeph', 'hag', 'zech', 'mal',
    'matt', 'mark', 'luke', 'john', 'acts', 'rom', '1cor', '2cor', 'gal', 'eph',
    'phil', 'col', '1thess', '2thess', '1tim', '2tim', 'titus', 'phlm', 'heb',
    'jas', '1pet', '2pet', '1john', '2john', '3john', 'jude', 'rev',
]

BOOK_NAME_TO_DRA = {
    "GENESIS": "gen", "EXODUS": "exod", "LEVITICUS": "lev", "NUMBERS": "num",
    "DEUTERONOMY": "deut", "JOSHUA": "josh", "JUDGES": "judg", "RUTH": "ruth",
    "1 SAMUEL": "1sam", "2 SAMUEL": "2sam", "1 KINGS": "1kgs", "2 KINGS": "2kgs",
    "1 CHRONICLES": "1chr", "2 CHRONICLES": "2chr", "EZRA": "ezra", "NEHEMIAH": "neh",
    "TOBIT": "tob", "TOBIAS": "tob", "JUDITH": "jdt", "ESTHER": "esth",
    "1 MACCABEES": "1macc", "2 MACCABEES": "2macc", "1 MACHABEES": "1macc", "2 MACHABEES": "2macc",
    "JOB": "job", "PSALM": "ps", "PSALMS": "ps", "PROVERBS": "prov",
    "ECCLESIASTES": "eccl", "SONG OF SOLOMON": "song", "SONG OF SONGS": "song",
    "CANTICLE OF CANTICLES": "song", "WISDOM": "wis", "SIRACH": "sir", "ECCLESIASTICUS": "sir",
    "ISAIAH": "isa", "ISAIAS": "isa", "JEREMIAH": "jer", "JEREMIAS": "jer",
    "LAMENTATIONS": "lam", "BARUCH": "bar", "EZEKIEL": "ezek", "EZECHIEL": "ezek",
    "DANIEL": "dan", "HOSEA": "hos", "OSEE": "hos", "JOEL": "joel", "AMOS": "amos",
    "OBADIAH": "obad", "ABDIAS": "obad", "JONAH": "jonah", "JONAS": "jonah",
    "MICAH": "mic", "MICHEAS": "mic", "NAHUM": "nah", "HABAKKUK": "hab", "HABACUC": "hab",
    "ZEPHANIAH": "zeph", "SOPHONIAS": "zeph", "HAGGAI": "hag", "AGGEUS": "hag",
    "ZECHARIAH": "zech", "ZACHARIAS": "zech", "MALACHI": "mal", "MALACHIAS": "mal",
    "MATTHEW": "matt", "MARK": "mark", "LUKE": "luke", "JOHN": "john", "ACTS": "acts",
    "ROMANS": "rom", "1 CORINTHIANS": "1cor", "2 CORINTHIANS": "2cor",
    "GALATIANS": "gal", "EPHESIANS": "eph", "PHILIPPIANS": "phil", "COLOSSIANS": "col",
    "1 THESSALONIANS": "1thess", "2 THESSALONIANS": "2thess",
    "1 TIMOTHY": "1tim", "2 TIMOTHY": "2tim", "TITUS": "titus", "PHILEMON": "phlm",
    "HEBREWS": "heb", "JAMES": "jas", "1 PETER": "1pet", "2 PETER": "2pet",
    "1 JOHN": "1john", "2 JOHN": "2john", "3 JOHN": "3john", "JUDE": "jude",
    "REVELATION": "rev", "APOCALYPSE": "rev",
}

def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = html_mod.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def align_mt_to_catholic_chapters(books_dict: dict) -> dict:
    """
    Align Protestant/MT chapter boundaries (Psalms, Joel 1-4 -> 1-3, Mal 1-3 -> 1-4)
    onto Catholic 73-book numbering.
    """
    out = dict(books_dict)
    # Psalms alignment if MT numbering is detected
    if 'ps' in out and len(out['ps']) >= 150:
        ps = out['ps'][:150]
        # Check if MT Psalm 9 has <= 22 verses
        if len(ps[8]) <= 22 and len(ps[9]) >= 16:
            aligned_ps = []
            for vc in range(1, 151):
                if vc <= 8:
                    aligned_ps.append(ps[vc - 1])
                elif vc == 9:
                    aligned_ps.append(ps[8] + ps[9])
                elif 10 <= vc <= 112:
                    aligned_ps.append(ps[vc])
                elif vc == 113:
                    aligned_ps.append(ps[113] + ps[114])
                elif vc == 114:
                    aligned_ps.append(ps[115][:9])
                elif vc == 115:
                    aligned_ps.append(ps[115][9:])
                elif 116 <= vc <= 145:
                    aligned_ps.append(ps[vc])
                elif vc == 146:
                    aligned_ps.append(ps[146][:11])
                elif vc == 147:
                    aligned_ps.append(ps[146][11:])
                elif 148 <= vc <= 150:
                    aligned_ps.append(ps[vc - 1])
            out['ps'] = aligned_ps

    # Joel alignment: MT 1-4 -> Catholic 1-3
    if 'joel' in out and len(out['joel']) == 4:
        out['joel'] = [
            out['joel'][0],
            out['joel'][1] + out['joel'][2],
            out['joel'][3]
        ]

    # Malachi alignment: MT 1-3 -> Catholic 1-4 (MT ch 3:19-24 -> ch 4:1-6)
    if 'mal' in out and len(out['mal']) == 3 and len(out['mal'][2]) >= 24:
        ch3_all = out['mal'][2]
        out['mal'] = [
            out['mal'][0],
            out['mal'][1],
            ch3_all[:18],
            ch3_all[18:]
        ]

    return out

def align_parsed_to_73_books(parsed: dict, is_protestant_66: bool = True) -> dict:
    """
    Given {bid: {chap_int: {verse_int: text}}}, convert into
    {bid: [[verse_1, verse_2, ...], [chap2...]]}
    aligned to DRA's 73-book chapter/verse slots.
    """
    raw_dict = {}
    target_books = PROT_66_DRA if is_protestant_66 else DRA_73_ORDER

    for b in target_books:
        if b not in parsed:
            continue
        b_data = parsed[b]
        max_ch = max(b_data.keys()) if b_data else 0
        ch_list = []
        for c in range(1, max_ch + 1):
            c_map = b_data.get(c, {})
            max_v = max(c_map.keys()) if c_map else 0
            v_list = [c_map.get(v, "") for v in range(1, max_v + 1)]
            ch_list.append(v_list)
        raw_dict[b] = ch_list

    if is_protestant_66:
        raw_dict = align_mt_to_catholic_chapters(raw_dict)

    # Now pad or trim to match exact DRA 73-book structure
    out = {}
    for b in DRA_73_ORDER:
        dra_chaps = DRA[b]
        if b not in raw_dict:
            out[b] = [[""] * len(vc) for vc in dra_chaps]
            continue
        b_chaps = raw_dict[b]
        ch_list = []
        for c_idx, dra_verses in enumerate(dra_chaps):
            c_data = b_chaps[c_idx] if c_idx < len(b_chaps) else []
            v_list = []
            for v_idx in range(len(dra_verses)):
                v_text = c_data[v_idx] if v_idx < len(c_data) else ""
                v_list.append(v_text)
            ch_list.append(v_list)
        out[b] = ch_list

    return out

def merge_notes_into_shards(new_notes: dict, src_key: str, tier: str, kind: str, title_prefix: str):
    """Merge {book_id: {chap_str: {verse_str: [html_str, ...]}}} into notes_shards/<book>.js."""
    merged_count = 0
    for b_id, chaps in new_notes.items():
        shard_path = os.path.join(SHARDS_DIR, f"{b_id}.js")
        if os.path.exists(shard_path):
            with open(shard_path, "r", encoding="utf-8") as f:
                raw = f.read()
            m = re.search(r'window\.__PLENARY_LOAD_BOOK_NOTES\([^,]+,\s*(\{.*\})\s*\);\s*$', raw, re.S)
            data = json.loads(m.group(1)) if m else {"book_id": b_id, "chapters": {}}
        else:
            data = {"book_id": b_id, "chapters": {}}

        chapters_obj = data.setdefault("chapters", {})
        for c_str, v_map in chaps.items():
            c_obj = chapters_obj.setdefault(c_str, {})
            for v_str, html_list in v_map.items():
                v_arr = [item for item in c_obj.get(v_str, []) if item.get("src") != src_key]
                for h_txt in html_list:
                    v_arr.append({
                        "src": src_key,
                        "tier": tier,
                        "kind": kind,
                        "title": f"{title_prefix} ({b_id.upper()} {c_str}:{v_str})",
                        "html": h_txt,
                    })
                    merged_count += 1
                c_obj[v_str] = v_arr

        payload = f"window.__PLENARY_LOAD_BOOK_NOTES({json.dumps(b_id)}, {json.dumps(data, ensure_ascii=False)});\n"
        with open(shard_path, "w", encoding="utf-8") as f:
            f.write(payload)
    print(f"  [SHARDS] Merged {merged_count} {src_key} notes across {len(new_notes)} books")

def build_nasb95():
    print("=== INGESTING NASB 1995 (EPUB) ===")
    files = glob.glob(os.path.join(DL_DIR, "*NASB 1995*.epub"))
    if not files:
        print("  Error: NASB95 epub not found")
        return
    parsed = {}
    with zipfile.ZipFile(files[0]) as z:
        htmls = sorted(n for n in z.namelist() if n.endswith((".html", ".xhtml", ".htm")))
        for name in htmls:
            raw = z.read(name).decode("utf-8", "ignore")
            # Match both uppercase books (GENESIS 1) and mixed case (Psalm 1)
            m_head = re.search(r'<p class="head">\s*([123]?\s*[A-Za-z ]+?)\s+(\d+)\s*(?:<|&nbsp;|\xa0)', raw)
            if not m_head:
                continue
            b_name = re.sub(r"\s+", " ", m_head.group(1).strip().upper())
            chap = int(m_head.group(2))
            b_id = BOOK_NAME_TO_DRA.get(b_name)
            if not b_id:
                continue

            body = raw[m_head.end():]
            # Strip footnote and xref anchors
            body = re.sub(r'<sup[^>]*>\s*<a[^>]*>.*?</a>\s*</sup>', '', body, flags=re.S)
            body = re.sub(r'<p class="head2">.*?</p>', ' ', body, flags=re.S)
            # Mark verse numbers
            body = re.sub(r'<span class="small1">\s*<b[^>]*>(\d+)</b>\s*</span>', r'\n@@V\1@@ ', body)
            body = re.sub(r'<small[^>]*>\s*<sup[^>]*>(\d+)</sup>\s*</small>', r'\n@@V\1@@ ', body)
            text = strip_tags(body)
            parts = re.split(r'@@V(\d+)@@', text)
            cmap = parsed.setdefault(b_id, {}).setdefault(chap, {})
            for i in range(1, len(parts) - 1, 2):
                vnum = int(parts[i])
                vtxt = parts[i + 1].strip()
                if vtxt:
                    cmap[vnum] = vtxt

    aligned = align_parsed_to_73_books(parsed, is_protestant_66=True)
    non_empty = sum(1 for b in aligned.values() for c in b for v in c if v)
    out_path = os.path.join(CACHE_DIR, "NASB95.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(aligned, f, ensure_ascii=False)
    print(f"  NASB95.json written: {non_empty} verses across {len(parsed)} books")

def build_csb_and_baker():
    print("=== INGESTING CSB & BAKER ILLUSTRATED STUDY BIBLE (EPUB) ===")
    files = glob.glob(os.path.join(DL_DIR, "*Baker*Illustrated*.epub*"))
    if not files:
        print("  Error: CSB Baker Illustrated Study Bible epub not found")
        return
    epub_path = files[0]

    parsed_verses = {}
    parsed_notes = {}

    with zipfile.ZipFile(epub_path) as z:
        xhtmls = [n for n in z.namelist() if n.endswith(('.xhtml', '.html'))]

        for n in xhtmls:
            # Check chapter files: OEBPS/Text/018_Genesis_032.xhtml
            m_file = re.search(r'Text/\d+_([A-Za-z0-9\-]+)_(\d+)\.xhtml', n)
            if not m_file:
                m_single = re.search(r'Text/\d+_([A-Za-z0-9\-]+)\.xhtml', n)
                if m_single and m_single.group(1).replace('-', ' ').upper() in BOOK_NAME_TO_DRA:
                    raw_book = m_single.group(1).replace('-', ' ').upper()
                    b_id = BOOK_NAME_TO_DRA[raw_book]
                    chap = 1
                else:
                    continue
            else:
                raw_book = m_file.group(1).replace('-', ' ').upper()
                b_id = BOOK_NAME_TO_DRA.get(raw_book)
                if not b_id:
                    continue
                chap = int(m_file.group(2))

            raw = z.read(n).decode('utf-8', 'ignore')

            # Extract CSB verse text
            txt_proc = re.sub(r'<span class="script">\s*<a[^>]*>(?:<a[^>]*/>)?(\d+)</a>\s*</span>', r'\n@@V\1@@ ', raw)
            txt_proc = re.sub(r'<span class="script">\s*<a[^>]*/>\s*(\d+)\s*</span>', r'\n@@V\1@@ ', txt_proc)
            txt_proc = re.sub(r'<span class="sup">.*?</span>', '', txt_proc, flags=re.S)
            txt_proc = re.sub(r'<span class="cross">.*?</span>', '', txt_proc, flags=re.S)
            txt_proc = re.sub(r'<h4 class="chapnum">.*?</h4>', '', txt_proc, flags=re.S)
            txt_proc = re.sub(r'<p class="h\d">.*?</p>', '', txt_proc, flags=re.S)

            clean = strip_tags(txt_proc)
            parts = re.split(r'@@V(\d+)@@', clean)
            cmap = parsed_verses.setdefault(b_id, {}).setdefault(chap, {})
            for i in range(1, len(parts) - 1, 2):
                vnum = int(parts[i])
                vtxt = parts[i + 1].strip()
                vtxt = re.sub(r'^\s*[\xa0\s]+', '', vtxt)
                if vtxt:
                    cmap[vnum] = vtxt

        # Extract Baker Study Notes from 101_Ancillary_Materials_*.xhtml
        ancillary_files = [n for n in xhtmls if 'Ancillary_Materials' in n]
        for af in ancillary_files:
            raw_anc = z.read(af).decode('utf-8', 'ignore')
            # Extract notes keyed by book and verse anchor:
            # Pattern: <p class="study-head">BookName</p> ... id="{Book}_{Chap}_{Verse}">{Chap}:{Verse}.</a></span> Note Text
            # Or <span class="verse-range"><a href="..." id="...">C:V.</a></span>
            cur_anc_bid = None
            for part in re.split(r'(<p class="study-head">.*?</p>)', raw_anc):
                if part.startswith('<p class="study-head">'):
                    bname_clean = strip_tags(part).upper()
                    cur_anc_bid = BOOK_NAME_TO_DRA.get(bname_clean)
                    continue
                if not cur_anc_bid:
                    continue
                # Find all note paragraphs in this section
                for p_match in re.finditer(r'<p class="outline">(.*?)</p>', part, re.S):
                    p_txt = p_match.group(1)
                    # Match verse anchor: e.g. 1:1–2 or 1:1. or 3:16.
                    m_vref = re.search(r'(\d+):(\d+)(?:[–\-]\d+)?\.\s*(?:</a></span>)?\s*(.*)$', p_txt, re.S)
                    if m_vref:
                        c_str = str(int(m_vref.group(1)))
                        v_str = str(int(m_vref.group(2)))
                        body = strip_tags(m_vref.group(3))
                        if len(body) > 15:
                            parsed_notes.setdefault(cur_anc_bid, {}).setdefault(c_str, {}).setdefault(v_str, []).append(html_mod.escape(body))

        # Also extract footnotes from 099_Footnotes_*.xhtml
        fn_files = [n for n in xhtmls if 'Footnotes' in n]
        for ff in fn_files:
            raw_fn = z.read(ff).decode('utf-8', 'ignore')
            for fn_p in re.finditer(r'<p class="footnote"><span class="sup"><a href="[^"]*Text/\d+_([A-Za-z0-9\-]+)_(\d+)\.xhtml[^"]*">.*?</a></span>\s*<span class="bold">(\d+):(\d+)</span>\s*(.*?)</p>', raw_fn, re.S):
                b_raw = fn_p.group(1).replace('-', ' ').upper()
                fn_bid = BOOK_NAME_TO_DRA.get(b_raw)
                if not fn_bid:
                    continue
                c_str = str(int(fn_p.group(3)))
                v_str = str(int(fn_p.group(4)))
                body = strip_tags(fn_p.group(5))
                if body:
                    parsed_notes.setdefault(fn_bid, {}).setdefault(c_str, {}).setdefault(v_str, []).append(f"<b>CSB Footnote:</b> {html_mod.escape(body)}")

    # Write CSB.json
    aligned_csb = align_parsed_to_73_books(parsed_verses, is_protestant_66=True)
    csb_verses = sum(1 for b in aligned_csb.values() for c in b for v in c if v)
    out_path = os.path.join(CACHE_DIR, "CSB.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(aligned_csb, f, ensure_ascii=False)
    print(f"  CSB.json written: {csb_verses} verses across {len(parsed_verses)} books")

    # Merge Baker Study Notes into Shards
    merge_notes_into_shards(parsed_notes, "baker_csb", "Protestant Study Bible", "study_note", "Baker Illustrated Study Bible")

def build_knox():
    print("=== INGESTING THE KNOX BIBLE (BARONIUS PRESS PDF) ===")
    files = glob.glob(os.path.join(DL_DIR, "*Knox Bible*.pdf"))
    if not files:
        print("  Error: Knox PDF not found")
        return
    doc = fitz.open(files[0])
    parsed = {}
    cur_book = None
    cur_chap = 1
    cur_verse = 0

    # Book headers in running top line
    for pno in range(14, len(doc) - 20):
        page = doc[pno]
        w = page.rect.width
        # Knox uses two columns
        mid = w / 2.0
        blocks = page.get_text("blocks")
        left_b = []
        right_b = []
        for b in blocks:
            x0, y0, x1, y1, txt, *_ = b
            txt_clean = txt.strip()
            if not txt_clean:
                continue
            if y0 < 50:
                # Running header: check book name
                up = re.sub(r"\s+", " ", txt_clean.upper())
                for k, bid in BOOK_NAME_TO_DRA.items():
                    if k in up:
                        if bid != cur_book:
                            cur_book = bid
                            cur_chap = 1
                            cur_verse = 0
                        break
                continue
            # Column sorting
            if (x0 + x1) / 2 < mid:
                left_b.append((y0, txt_clean))
            else:
                right_b.append((y0, txt_clean))

        left_b.sort(key=lambda t: t[0])
        right_b.sort(key=lambda t: t[0])

        if not cur_book:
            continue

        for y, text in left_b + right_b:
            lines = text.splitlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Check chapter marker: standalone number <= 150
                m_ch = re.match(r'^(\d{1,3})$', line)
                if m_ch:
                    cnum = int(m_ch.group(1))
                    if 1 <= cnum <= 150 and (cnum == cur_chap + 1 or (cnum == 1 and cur_chap == 1)):
                        cur_chap = cnum
                        cur_verse = 1
                        continue
                # Check verse marker at line start: e.g. "2 created heaven and earth."
                m_v = re.match(r'^(\d{1,3})\s+(.*)$', line)
                if m_v:
                    vnum = int(m_v.group(1))
                    rest = m_v.group(2).strip()
                    if 1 <= vnum <= 176 and (vnum == cur_verse + 1 or vnum <= cur_verse + 4):
                        cur_verse = vnum
                        cmap = parsed.setdefault(cur_book, {}).setdefault(cur_chap, {})
                        cmap[cur_verse] = (cmap.get(cur_verse, "") + " " + rest).strip()
                        continue
                # Normal verse continuation text
                if cur_verse > 0:
                    cmap = parsed.setdefault(cur_book, {}).setdefault(cur_chap, {})
                    cmap[cur_verse] = (cmap.get(cur_verse, "") + " " + line).strip()

    aligned = align_parsed_to_73_books(parsed, is_protestant_66=False)
    non_empty = sum(1 for b in aligned.values() for c in b for v in c if v)
    out_path = os.path.join(CACHE_DIR, "KNOX.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(aligned, f, ensure_ascii=False)
    print(f"  KNOX.json written: {non_empty} verses across {len(parsed)} books")

if __name__ == "__main__":
    build_nasb95()
    build_csb_and_baker()
    build_knox()
