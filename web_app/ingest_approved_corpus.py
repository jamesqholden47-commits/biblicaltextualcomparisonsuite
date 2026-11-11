# -*- coding: utf-8 -*-
"""
Deterministic downloader, cache manager, and verifier for approved Catholic
and primary textual-witness Scripture datasets.
Caches raw downloads in web_app/sources_cache/raw/ and emits clean normalized JSONs.
"""
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, 'sources_cache')
RAW_DIR = os.path.join(CACHE_DIR, 'raw')
NV_RAW_DIR = os.path.join(RAW_DIR, 'nv')
os.makedirs(NV_RAW_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) PlenaryWorkstation/2.0'}

REMOTE_FILES = {
    'eng-dra.usfx.xml': 'https://raw.githubusercontent.com/seven1m/open-bibles/master/eng-dra.usfx.xml',
    'eng-web-c_vpl.zip': 'https://ebible.org/Scriptures/eng-web-c_vpl.zip',
    'eng-Brenton_vpl.zip': 'https://ebible.org/Scriptures/eng-Brenton_vpl.zip',
    'KJVA.json': 'https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/KJVA.json',
    'ASV.json': 'https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/ASV.json',
    'Byz.json': 'https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/Byz.json',
    'TR.json': 'https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json/TR.json',
    'strongs-greek-dictionary.js': 'https://raw.githubusercontent.com/openscriptures/strongs/master/greek/strongs-greek-dictionary.js',
    'strongs-hebrew-dictionary.js': 'https://raw.githubusercontent.com/openscriptures/strongs/master/hebrew/strongs-hebrew-dictionary.js',
    'TAGNT_Mat-Jhn.txt': 'https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Translators%20Amalgamated%20OT%2BNT/TAGNT%20Mat-Jhn%20-%20Translators%20Amalgamated%20Greek%20NT%20-%20STEPBible.org%20CC-BY.txt',
    'TAGNT_Act-Rev.txt': 'https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Translators%20Amalgamated%20OT%2BNT/TAGNT%20Act-Rev%20-%20Translators%20Amalgamated%20Greek%20NT%20-%20STEPBible.org%20CC-BY.txt',
    'TAHOT_Gen-Deu.txt': 'https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Translators%20Amalgamated%20OT%2BNT/TAHOT%20Gen-Deu%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt',
    'TAHOT_Jos-Est.txt': 'https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Translators%20Amalgamated%20OT%2BNT/TAHOT%20Jos-Est%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt',
    'TAHOT_Job-Sng.txt': 'https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Translators%20Amalgamated%20OT%2BNT/TAHOT%20Job-Sng%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt',
    'TAHOT_Isa-Mal.txt': 'https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Translators%20Amalgamated%20OT%2BNT/TAHOT%20Isa-Mal%20-%20Translators%20Amalgamated%20Hebrew%20OT%20-%20STEPBible.org%20CC%20BY.txt',
}

def download_if_missing(filename, url, folder=RAW_DIR):
    dest = os.path.join(folder, filename)
    if os.path.exists(dest) and os.path.getsize(dest) > 400:
        return dest
    print(f"Downloading {filename}...")
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = resp.read()
    with open(dest, 'wb') as f:
        f.write(data)
    return dest

# Map 73 canonical USFX / eBible codes -> our canonical book IDs (supports USFM + VPL aliases)
USFX_TO_CANON_ID = {
    'GEN': 'gen', 'EXO': 'exod', 'LEV': 'lev', 'NUM': 'num', 'DEU': 'deut',
    'JOS': 'josh', 'JDG': 'judg', 'RUT': 'ruth', '1SA': '1sam', '2SA': '2sam',
    '1KI': '1kgs', '2KI': '2kgs', '1CH': '1chr', '2CH': '2chr', 'EZR': 'ezra', 'NEH': 'neh',
    'TOB': 'tob', 'JDT': 'jdt', 'EST': 'esth', 'ESG': 'esth', '1MA': '1macc', '2MA': '2macc',
    'JOB': 'job', 'PSA': 'ps', 'PRO': 'prov', 'ECC': 'eccl', 'SNG': 'song', 'SOL': 'song',
    'WIS': 'wis', 'SIR': 'sir',
    'ISA': 'isa', 'JER': 'jer', 'LAM': 'lam', 'BAR': 'bar', 'EZK': 'ezek', 'EZE': 'ezek',
    'DAN': 'dan', 'DNG': 'dan',
    'HOS': 'hos', 'JOL': 'joel', 'JOE': 'joel', 'AMO': 'amos', 'OBA': 'obad', 'JON': 'jonah',
    'MIC': 'mic', 'NAM': 'nah', 'NAH': 'nah', 'HAB': 'hab', 'ZEP': 'zeph', 'HAG': 'hag', 'ZEC': 'zech', 'MAL': 'mal',
    'MAT': 'matt', 'MRK': 'mark', 'MAR': 'mark', 'LUK': 'luke', 'JHN': 'john', 'JOH': 'john', 'ACT': 'acts',
    'ROM': 'rom', '1CO': '1cor', '2CO': '2cor', 'GAL': 'gal', 'EPH': 'eph',
    'PHP': 'phil', 'PHI': 'phil', 'COL': 'col', '1TH': '1thess', '2TH': '2thess', '1TI': '1tim',
    '2TI': '2tim', 'TIT': 'titus', 'PHM': 'phlm', 'HEB': 'heb', 'JAS': 'jas', 'JAM': 'jas',
    '1PE': '1pet', '2PE': '2pet', '1JN': '1john', '1JO': '1john', '2JN': '2john', '2JO': '2john',
    '3JN': '3john', '3JO': '3john', 'JUD': 'jude', 'REV': 'rev',
}

NT_BOOK_IDS = {
    'matt','mark','luke','john','acts','rom','1cor','2cor','gal','eph','phil','col',
    '1thess','2thess','1tim','2tim','titus','phlm','heb','jas','1pet','2pet',
    '1john','2john','3john','jude','rev'
}

def align_mt_to_catholic_chapters(books_dict):
    """
    Align Protestant/MT/Greek chapter boundaries (Psalms, Joel 1-4 -> 1-3, Mal 1-3 -> 1-4,
    plus Baruch EpJer=ch6, Dan Sus=ch13 Bel=ch14 if split) onto Catholic 73-book numbering.
    """
    # Psalms (only if Psalms uses MT numbering: check Ps 115 len vs Ps 116; actually MT Ps 116 has 19v, Vulgate Ps 114=9v & Ps 115=10v; wait MT Ps 9 has 20v & Ps 10 has 18v vs Vulgate Ps 9=39v! Check len(ch 9) < 25)
    if 'ps' in books_dict and len(books_dict['ps']) >= 150:
        ps = books_dict['ps'][:150]  # drop Psalm 151 in Brenton if present
        # MT numbering heuristic: Hebrew Ps 9 has <= 21 verses, Vulgate Ps 9 has 39 verses
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
                else:
                    aligned_ps.append(ps[vc - 1])
            books_dict['ps'] = aligned_ps
        else:
            books_dict['ps'] = ps  # already Catholic/LXX 150-psalm numbering (trimmed Ps 151)

    # Fill Proverbs 30/31 LXX ordering gaps in Brenton cleanly
    if 'prov' in books_dict and len(books_dict['prov']) == 31 and not books_dict['prov'][29]:
        books_dict['prov'][29] = ["[LXX Brenton Ordering: Proverbs 30:1–14 appears at Ch. 24:23–36 and Prov 30:15–33 at Ch. 24:50–68 in the Septuagint.]"]
        if len(books_dict['prov'][30]) >= 9:
            for i in range(9):
                if not books_dict['prov'][30][i].strip():
                    books_dict['prov'][30][i] = f"[LXX Brenton Ordering: Proverbs 31:{i+1} appears at Ch. 24:{37+i} in the Septuagint.]"

    # Joel: some witnesses use 4 chapters (ch2 + ch3 = Catholic ch2; ch4 = Catholic ch3)
    if 'joel' in books_dict and len(books_dict['joel']) == 4:
        j = books_dict['joel']
        books_dict['joel'] = [j[0], j[1] + j[2], j[3]]

    # Malachi: if 3 chapters (MT/LXX/NV): split ch 3 (24 vv) into ch 3 (18 vv) + ch 4 (6 vv)
    if 'mal' in books_dict and len(books_dict['mal']) == 3 and len(books_dict['mal'][2]) >= 22:
        m = books_dict['mal']
        books_dict['mal'] = [m[0], m[1], m[2][:18], m[2][18:]]

    return books_dict

def parse_dra_usfx(xml_path):
    """
    Parse eng-dra.usfx.xml (73 Catholic books) into chapters -> verse strings,
    PLUS extract compact English word -> Strong's index per verse.
    """
    out = {}
    word_links = {}
    with open(xml_path, 'rb') as f:
        root = ET.fromstring(f.read())

    SKIP_HEAD_TAGS = {'f', 'x', 'note', 'rq', 'fig', 'h', 'id', 'toc1', 'toc2', 'toc3', 'mt', 'ms', 's', 's1', 's2', 'r', 'd'}
    STOP_EN = {'the','and','for','that','with','unto','from','shall','were','was','are','his','her','him','not','but','all','you','who','had','has','have','they','this','them','their','thy','thee','thou'}

    for book_el in root.findall('book'):
        usfx_id = book_el.attrib.get('id', '')
        bid = USFX_TO_CANON_ID.get(usfx_id)
        if not bid:
            continue
        chapters = {}
        cur_c = None
        cur_v = None
        cur_buf = []
        cur_links = {}

        def flush_verse():
            nonlocal cur_c, cur_v, cur_buf, cur_links
            if cur_c is not None and cur_v is not None:
                txt = re.sub(r'\s+', ' ', ''.join(cur_buf)).strip()
                txt = re.sub(r'\s+([,.;:?!\)\]])', r'\1', txt)
                if txt:
                    chapters.setdefault(cur_c, {})[cur_v] = txt
                    if cur_links:
                        word_links[f"{bid}.{cur_c}.{cur_v}"] = cur_links
            cur_v = None
            cur_buf = []
            cur_links = {}

        def walk(el, in_skip=False):
            nonlocal cur_c, cur_v, cur_buf, cur_links
            tag = el.tag.split('}')[-1]
            if tag == 'c':
                flush_verse()
                cid = el.attrib.get('id', '').strip()
                if cid.isdigit():
                    cur_c = int(cid)
            elif tag == 'v':
                flush_verse()
                vid = el.attrib.get('id', '').strip()
                m_v = re.match(r'^(\d+)', vid)
                if m_v and cur_c is not None:
                    cur_v = int(m_v.group(1))
            elif tag == 've':
                flush_verse()

            if tag in SKIP_HEAD_TAGS:
                if el.tail and not in_skip and cur_v is not None:
                    cur_buf.append(el.tail)
                return

            if not in_skip and cur_v is not None and el.text:
                cur_buf.append(el.text)
                if tag == 'w' and el.attrib.get('s'):
                    st = el.attrib['s'].strip().upper()
                    if re.match(r'^[GH]\d+$', st):
                        st_norm = st[0] + str(int(st[1:]))
                        for wt in re.findall(r"[a-zA-Z]+", el.text.lower()):
                            if len(wt) >= 3 and wt not in STOP_EN:
                                cur_links.setdefault(wt, st_norm)

            for child in el:
                walk(child, in_skip)

            if not in_skip and cur_v is not None:
                if tag in ('p', 'q', 'q1', 'q2', 'q3', 'm', 'li', 'li1'):
                    cur_buf.append(' ')
                if el.tail:
                    cur_buf.append(el.tail)

        for child in book_el:
            walk(child, False)
        flush_verse()

        if chapters:
            max_c = max(chapters.keys())
            ch_list = []
            for c_i in range(1, max_c + 1):
                vd = chapters.get(c_i, {})
                ch_list.append([vd.get(v_i, '') for v_i in range(1, max(vd.keys()) + 1)] if vd else [])
            out[bid] = ch_list

    return out, word_links

def parse_vpl_zip(zip_path, merge_extras=False):
    out = {}
    extras = {}
    with zipfile.ZipFile(zip_path) as z:
        txt_names = [n for n in z.namelist() if n.endswith('_vpl.txt') or n.endswith('.txt')]
        raw = z.read(txt_names[0]).decode('utf-8-sig', errors='ignore')

    temp = {}
    for line in raw.splitlines():
        m = re.match(r'^([1-3A-Z]{2,4})\s+(\d+):(\d+)\s+(.*)$', line.strip())
        if not m:
            continue
        code, ch, vs, body = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4).strip()
        body = re.sub(r'\s+', ' ', body.replace('¶', '')).strip()
        if merge_extras and code in ('EPJ', 'SUS', 'BEL'):
            extras.setdefault(code, {}).setdefault(ch, {})[vs] = body
            continue
        bid = USFX_TO_CANON_ID.get(code)
        if not bid:
            continue
        # If book appears twice (rare e.g. EST vs ESG), prefer longer/Greek ESG in Catholic/Brenton
        if code == 'ESG' or bid not in temp or code not in ('EST',):
            temp.setdefault(bid, {}).setdefault(ch, {})[vs] = body

    for bid, chd in temp.items():
        max_c = max(chd.keys())
        out[bid] = [[chd[ci].get(vi, '') for vi in range(1, max(chd[ci].keys()) + 1)] if ci in chd else [] for ci in range(1, max_c + 1)]

    # Merge Brenton separate EpJer/Susanna/Bel into Baruch ch.6 & Daniel ch.13-14
    if merge_extras:
        if 'EPJ' in extras and 'bar' in out:
            vd = extras['EPJ'][1]
            out['bar'].append([vd.get(vi, '') for vi in range(1, max(vd.keys()) + 1)])
        if 'dan' in out:
            for code in ('SUS', 'BEL'):
                if code in extras:
                    vd = extras[code][1]
                    out['dan'].append([vd.get(vi, '') for vi in range(1, max(vd.keys()) + 1)])

    # Label omitted/reordered verse gaps cleanly rather than leaving empty strings
    empty_label = "[— Omitted or reordered in Brenton Septuagint / Alexandrinus]" if merge_extras else "[— Absent in WEBC / Rahlfs Greek witness]"
    for bid, chs in out.items():
        for ch in chs:
            for vi, v in enumerate(ch):
                if not v.strip():
                    ch[vi] = empty_label

    return align_mt_to_catholic_chapters(out)

SCROLL_NAME_TO_ID = {
    'Genesis': 'gen', 'Exodus': 'exod', 'Leviticus': 'lev', 'Numbers': 'num', 'Deuteronomy': 'deut',
    'Joshua': 'josh', 'Judges': 'judg', 'Ruth': 'ruth', 'I Samuel': '1sam', 'II Samuel': '2sam',
    'I Kings': '1kgs', 'II Kings': '2kgs', 'I Chronicles': '1chr', 'II Chronicles': '2chr',
    'Ezra': 'ezra', 'Nehemiah': 'neh', 'Tobit': 'tob', 'Judith': 'jdt', 'Esther': 'esth',
    'I Maccabees': '1macc', 'II Maccabees': '2macc',
    'Job': 'job', 'Psalms': 'ps', 'Proverbs': 'prov', 'Ecclesiastes': 'eccl', 'Song of Solomon': 'song',
    'Wisdom': 'wis', 'Sirach': 'sir',
    'Isaiah': 'isa', 'Jeremiah': 'jer', 'Lamentations': 'lam', 'Baruch': 'bar', 'Ezekiel': 'ezek', 'Daniel': 'dan',
    'Hosea': 'hos', 'Joel': 'joel', 'Amos': 'amos', 'Obadiah': 'obad', 'Jonah': 'jonah',
    'Micah': 'mic', 'Nahum': 'nah', 'Habakkuk': 'hab', 'Zephaniah': 'zeph', 'Haggai': 'hag',
    'Zechariah': 'zech', 'Malachi': 'mal',
    'Matthew': 'matt', 'Mark': 'mark', 'Luke': 'luke', 'John': 'john', 'Acts': 'acts',
    'Romans': 'rom', 'I Corinthians': '1cor', 'II Corinthians': '2cor', 'Galatians': 'gal',
    'Ephesians': 'eph', 'Philippians': 'phil', 'Colossians': 'col',
    'I Thessalonians': '1thess', 'II Thessalonians': '2thess', 'I Timothy': '1tim', 'II Timothy': '2tim',
    'Titus': 'titus', 'Philemon': 'phlm', 'Hebrews': 'heb', 'James': 'jas',
    'I Peter': '1pet', 'II Peter': '2pet', 'I John': '1john', 'II John': '2john', 'III John': '3john',
    'Jude': 'jude', 'Revelation of John': 'rev',
}

def clean_byz_tr_verse(txt, bid=None, ch=0, vs=0):
    """Strip Scrollmapper Strong digits, {morph} tags, and mangled inline RP variant markers."""
    t = re.sub(r'\{[^}]*\}', '', txt)
    t = re.sub(r'\b\d+\b', '', t)
    t = t.replace('>', '').replace(':END', '').replace(':OMIT', '')
    # Remove duplicate variant alternatives marked OMIT: ... or OMIT word
    t = re.sub(r'\s+OMIT:\s+.*$', '', t)
    t = re.sub(r'\s+OMIT\s+\S+', '', t)
    # Keep primary reading on X OR Y inline pairs
    while ' OR ' in t:
        t_new = re.sub(r'(\S+)\s+OR\s+\S+', r'\1', t)
        if t_new == t:
            t = t.split(' OR ', 1)[0]
            break
        t = t_new
    t = re.sub(r'\(\d+:\d+\)\s*', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def parse_scrollmapper_json(path, nt_only=False, edition_tag=''):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    out = {}
    extras = {}
    for b in data.get('books', []):
        name = b.get('name', '')
        bid = SCROLL_NAME_TO_ID.get(name)
        if not bid:
            extras[name] = [[v['text'].strip() for v in c['verses']] for c in b['chapters']]
            continue
        if nt_only and bid not in NT_BOOK_IDS:
            continue
        out[bid] = [[v['text'].strip() for v in c['verses']] for c in b['chapters']]

    # Fix RP/Byz & TR special embedded splits & variant annotations cleanly
    if nt_only:
        if 'john' in out and len(out['john']) >= 8:
            j8 = out['john'][7]
            if len(j8) >= 10 and 'v 10 ' in j8[8]:
                part9, part10 = j8[8].split('v 10 ', 1)
                j8[8] = part9.split(' οι δε ακουσαντες OMIT:', 1)[0].strip()
                j8[9] = part10.split(' ανακυψας δε ο ιησους OMIT', 1)[0].strip()
        if 'acts' in out and len(out['acts']) >= 24:
            a24 = out['acts'][23]
            if len(a24) >= 8 and '(24:7)' in a24[5]:
                m7 = re.search(r'\(24:7\)\s*(.*?)(?:\(24:8\)\s*(.*))?$', a24[5])
                a24[5] = a24[5].split('(24:7)', 1)[0].strip()
                if m7 and m7.group(1) and not a24[6].strip():
                    a24[6] = m7.group(1).strip()
        if 'rom' in out and len(out['rom']) >= 16:
            r14 = out['rom'][13]
            r16 = out['rom'][15]
            if len(r14) >= 23 and '(16:25)' in r14[22]:
                main14, dox = r14[22].split('(16:25)', 1)
                r14[22] = main14.strip() + ' [RP Doxology at 14:24–26]'
                p25_26 = dox.split('(16:26)')
                v25 = p25_26[0].strip()
                if len(p25_26) > 1:
                    p26_27 = p25_26[1].split('(16:27)')
                    v26 = p26_27[0].strip()
                    v27 = p26_27[1].strip() if len(p26_27) > 1 else ''
                else:
                    v26, v27 = '', ''
                if len(r16) >= 27:
                    if v25 and not r16[24].strip(): r16[24] = '[RP placed at Rom 14:24] ' + v25
                    if v26 and not r16[25].strip(): r16[25] = '[RP placed at Rom 14:25] ' + v26
                    if v27 and not r16[26].strip(): r16[26] = '[RP placed at Rom 14:26] ' + v27

        for bid, chs in out.items():
            for ci, ch in enumerate(chs):
                for vi, v in enumerate(ch):
                    cleaned = clean_byz_tr_verse(v, bid, ci + 1, vi + 1)
                    if not cleaned:
                        cleaned = f"[— Omitted in {edition_tag or 'this Greek NT stream'}]"
                    ch[vi] = cleaned

    # Fill empty critical slots in ASV cleanly
    if edition_tag == 'ASV 1901':
        for bid, chs in out.items():
            for ch in chs:
                for vi, v in enumerate(ch):
                    if not v.strip():
                        ch[vi] = "[— Omitted in ASV 1901 Critical Text; present in DRA / TR]"

    # Merge KJVA Apocrypha extras onto Catholic Baruch/Daniel/Esther
    if not nt_only:
        if 'Letter of Jeremiah' in extras and 'bar' in out and len(out['bar']) == 5:
            out['bar'].append(extras['Letter of Jeremiah'][0])
        if 'dan' in out and len(out['dan']) == 12:
            if 'Susanna' in extras:
                out['dan'].append(extras['Susanna'][0])
            if 'Bel and the Dragon' in extras:
                out['dan'].append(extras['Bel and the Dragon'][0])
        esth_extra = extras.get('Additions to Esther') or extras.get('Esther (Greek)')
        if esth_extra and 'esth' in out and len(out['esth']) == 10:
            # Canonical Ch 10 has v.1-3; Additions Ch 10 has v.4-13 (first 3 are stubs '…'), plus Ch 11-16
            if len(esth_extra) >= 16:
                add10 = [v for v in esth_extra[9][3:] if v and v != '…']
                out['esth'][9] = out['esth'][9][:3] + add10
                for ci in range(10, 16):
                    out['esth'].append(esth_extra[ci])
    return align_mt_to_catholic_chapters(out)

NV_FILENAME_TO_ID = {
    'nova-vulgata_vt_genesis_lt.html': 'gen',
    'nova-vulgata_vt_exodus_lt.html': 'exod',
    'nova-vulgata_vt_leviticus_lt.html': 'lev',
    'nova-vulgata_vt_numeri_lt.html': 'num',
    'nova-vulgata_vt_deuteronomii_lt.html': 'deut',
    'nova-vulgata_vt_iosue_lt.html': 'josh',
    'nova-vulgata_vt_iudicum_lt.html': 'judg',
    'nova-vulgata_vt_ruth_lt.html': 'ruth',
    'nova-vulgata_vt_i-samuelis_lt.html': '1sam',
    'nova-vulgata_vt_ii-samuelis_lt.html': '2sam',
    'nova-vulgata_vt_i-regum_lt.html': '1kgs',
    'nova-vulgata_vt_ii-regum_lt.html': '2kgs',
    'nova-vulgata_vt_i-paralipomenon_lt.html': '1chr',
    'nova-vulgata_vt_ii-paralipomenon_lt.html': '2chr',
    'nova-vulgata_vt_esdrae_lt.html': 'ezra',
    'nova-vulgata_vt_nehemiae_lt.html': 'neh',
    'nova-vulgata_vt_thobis_lt.html': 'tob',
    'nova-vulgata_vt_iudith_lt.html': 'jdt',
    'nova-vulgata_vt_esther_lt.html': 'esth',
    'nova-vulgata_vt_iob_lt.html': 'job',
    'nova-vulgata_vt_psalmorum_lt.html': 'ps',
    'nova-vulgata_vt_proverbiorum_lt.html': 'prov',
    'nova-vulgata_vt_ecclesiastes_lt.html': 'eccl',
    'nova-vulgata_vt_canticum-canticorum_lt.html': 'song',
    'nova-vulgata_vt_sapientiae_lt.html': 'wis',
    'nova-vulgata_vt_ecclesiasticus_lt.html': 'sir',
    'nova-vulgata_vt_isaiae_lt.html': 'isa',
    'nova-vulgata_vt_ieremiae_lt.html': 'jer',
    'nova-vulgata_vt_lamentationes_lt.html': 'lam',
    'nova-vulgata_vt_baruch_lt.html': 'bar',
    'nova-vulgata_vt_ezechielis_lt.html': 'ezek',
    'nova-vulgata_vt_danielis_lt.html': 'dan',
    'nova-vulgata_vt_osee_lt.html': 'hos',
    'nova-vulgata_vt_ioel_lt.html': 'joel',
    'nova-vulgata_vt_amos_lt.html': 'amos',
    'nova-vulgata_vt_abdiae_lt.html': 'obad',
    'nova-vulgata_vt_ionae_lt.html': 'jonah',
    'nova-vulgata_vt_michaeae_lt.html': 'mic',
    'nova-vulgata_vt_nahum_lt.html': 'nah',
    'nova-vulgata_vt_habacuc_lt.html': 'hab',
    'nova-vulgata_vt_sophoniae_lt.html': 'zeph',
    'nova-vulgata_vt_aggaei_lt.html': 'hag',
    'nova-vulgata_vt_zachariae_lt.html': 'zech',
    'nova-vulgata_vt_malachiae_lt.html': 'mal',
    'nova-vulgata_vt_i-maccabaeorum_lt.html': '1macc',
    'nova-vulgata_vt_ii-maccabaeorum_lt.html': '2macc',
    'nova-vulgata_nt_evang-matthaeum_lt.html': 'matt',
    'nova-vulgata_nt_evang-marcum_lt.html': 'mark',
    'nova-vulgata_nt_evang-lucam_lt.html': 'luke',
    'nova-vulgata_nt_evang-ioannem_lt.html': 'john',
    'nova-vulgata_nt_actus-apostolorum_lt.html': 'acts',
    'nova-vulgata_nt_epist-romanos_lt.html': 'rom',
    'nova-vulgata_nt_epist-i-corinthios_lt.html': '1cor',
    'nova-vulgata_nt_epist-ii-corinthios_lt.html': '2cor',
    'nova-vulgata_nt_epist-galatas_lt.html': 'gal',
    'nova-vulgata_nt_epist-ephesios_lt.html': 'eph',
    'nova-vulgata_nt_epist-philippenses_lt.html': 'phil',
    'nova-vulgata_nt_epist-colossenses_lt.html': 'col',
    'nova-vulgata_nt_epist-i-thessalonicenses_lt.html': '1thess',
    'nova-vulgata_nt_epist-ii-thessalonicenses_lt.html': '2thess',
    'nova-vulgata_nt_epist-i-timotheum_lt.html': '1tim',
    'nova-vulgata_nt_epist-ii-timotheum_lt.html': '2tim',
    'nova-vulgata_nt_epist-titum_lt.html': 'titus',
    'nova-vulgata_nt_epist-philemonem_lt.html': 'phlm',
    'nova-vulgata_nt_epist-hebraeos_lt.html': 'heb',
    'nova-vulgata_nt_epist-iacobi_lt.html': 'jas',
    'nova-vulgata_nt_epist-i-petri_lt.html': '1pet',
    'nova-vulgata_nt_epist-ii-petri_lt.html': '2pet',
    'nova-vulgata_nt_epist-i-ioannis_lt.html': '1john',
    'nova-vulgata_nt_epist-ii-ioannis_lt.html': '2john',
    'nova-vulgata_nt_epist-iii-ioannis_lt.html': '3john',
    'nova-vulgata_nt_epist-iudae_lt.html': 'jude',
    'nova-vulgata_nt_apocalypsis-ioannis_lt.html': 'rev',
}

def parse_nova_vulgata_page(bid, page_html):
    txt = html.unescape(page_html)
    txt = re.sub(r'<head.*?</head>', '', txt, flags=re.S | re.I)
    txt = re.sub(r'<script.*?</script>', '', txt, flags=re.S | re.I)
    txt = re.sub(r'<style.*?</style>', '', txt, flags=re.S | re.I)

    # IMPORTANT: match FULL <a name="..."> tag including closing '>'!
    if bid == 'ps':
        chap_pat = re.compile(r'<a\b[^>]*\bname=["\']PSALMUS\s+(\d+)["\'][^>]*>', re.I)
    else:
        chap_pat = re.compile(r'<a\b[^>]*\bname=["\'](\d+)["\'][^>]*>', re.I)

    matches = list(chap_pat.finditer(txt))
    slices = []
    if matches:
        for i, m in enumerate(matches):
            ch_num = int(m.group(1))
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(txt)
            slices.append((ch_num, txt[start:end]))
    else:
        # Single-chapter book (Obadiah, Philemon, 2 John, 3 John, Jude): start right before verse 1
        m_v1 = re.search(r'(?:<p>|<br\s*/?>)\s*1(?:&nbsp;|\s+)[A-Z]', txt)
        start = m_v1.start() if m_v1 else 0
        slices.append((1, txt[start:]))

    chapters = {}
    for ch_num, raw_chunk in slices:
        chunk = re.sub(r'<br\s*/?>', '\n', raw_chunk, flags=re.I)
        chunk = re.sub(r'</?(?:p|div|td|tr|table|center|blockquote)[^>]*>', '\n', chunk, flags=re.I)
        chunk = re.sub(r'<[^>]+>', '', chunk)
        lines = [re.sub(r'\s+', ' ', l).strip() for l in chunk.splitlines()]
        verses = []
        cur_v = ''
        for line in lines:
            if not line:
                continue
            if line.startswith(('Previous', 'Next')) or 'Copyright' in line or 'Libreria Editrice' in line:
                break
            if re.match(rf'^(?:PSALMUS\s+)?{ch_num}(?:\s*\(\d+\))?$', line, re.I) and not verses:
                continue
            # If line starts with ch_num followed by verse 1 on same line (happens when <a> wasn't closed)
            line = re.sub(rf'^{ch_num}\s+(?=1[a-z]?\s+)', '', line)
            # Notice Psalm 23 has "1 PSALMUS. David." then line 2 "Dominus pascit..."
            mv = re.match(r'^(\d+[a-z]?)\s+(.+)$', line)
            if mv:
                vtag, vbody = mv.group(1), mv.group(2).strip()
                if vtag == '1' and bid == 'ps' and not verses and cur_v == '':
                    cur_v = vbody
                    continue
                if cur_v:
                    verses.append(cur_v.strip())
                cur_v = f"[{vtag}] {vbody}" if (bid == 'esth' and re.match(r'^\d+[a-z]$', vtag)) else vbody
            else:
                if cur_v and not re.match(r'^(?:LIBER|PSALMUS|Capitulum)\b', line):
                    cur_v += ' ' + line
        if cur_v:
            verses.append(cur_v.strip())
        if bid == 'deut' and ch_num == 32:
            verses = [x.replace(': >Manus nostra', ': «Manus nostra') for x in verses]
        if verses:
            chapters[ch_num] = verses

    max_c = max(chapters.keys()) if chapters else 0
    return [chapters.get(c, []) for c in range(1, max_c + 1)]

def load_all_nova_vulgata():
    base = 'https://www.vatican.va/archive/bible/nova_vulgata/documents/'
    nv = {}
    for fn, bid in NV_FILENAME_TO_ID.items():
        local_p = os.path.join(NV_RAW_DIR, fn)
        if not os.path.exists(local_p) or os.path.getsize(local_p) < 500:
            download_if_missing(fn, base + fn, folder=NV_RAW_DIR)
        raw_bytes = open(local_p, 'rb').read()
        enc = 'utf-8' if b'utf-8' in raw_bytes[:600].lower() else 'latin-1'
        page_html = raw_bytes.decode(enc, errors='ignore')
        nv[bid] = parse_nova_vulgata_page(bid, page_html)
    # Nova Vulgata Esther chapters 1..10 embed [1a],[3a],[4a],[5a],[8a],[10a] inside canonical slots.
    # Also pad Esther up to ch.16 by extracting prefixed Greek additions if present, or note inline placement.
    return align_mt_to_catholic_chapters(nv)

def main():
    paths = {}
    for fname, url in REMOTE_FILES.items():
        paths[fname] = download_if_missing(fname, url)

    print("\n--- Parsing & Caching Core Datasets ---")
    dra, dra_links = parse_dra_usfx(paths['eng-dra.usfx.xml'])
    with open(os.path.join(CACHE_DIR, 'DRA.json'), 'w', encoding='utf-8') as f:
        json.dump(dra, f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(CACHE_DIR, 'dra_strongs_links.json'), 'w', encoding='utf-8') as f:
        json.dump(dra_links, f, ensure_ascii=False, separators=(',', ':'))
    print(f"DRA: {len(dra)} books, {sum(sum(len(c) for c in chs) for chs in dra.values())} verses, {len(dra_links)} verse Strong links")

    webc = parse_vpl_zip(paths['eng-web-c_vpl.zip'], merge_extras=False)
    with open(os.path.join(CACHE_DIR, 'WEBC.json'), 'w', encoding='utf-8') as f:
        json.dump(webc, f, ensure_ascii=False, separators=(',', ':'))
    print(f"WEBC: {len(webc)} books, {sum(sum(len(c) for c in chs) for chs in webc.values())} verses")

    brenton = parse_vpl_zip(paths['eng-Brenton_vpl.zip'], merge_extras=True)
    with open(os.path.join(CACHE_DIR, 'BrentonLXX.json'), 'w', encoding='utf-8') as f:
        json.dump(brenton, f, ensure_ascii=False, separators=(',', ':'))
    print(f"BrentonLXX: {len(brenton)} books, {sum(sum(len(c) for c in chs) for chs in brenton.values())} verses")

    for name, nt_only, tag in [('KJVA', False, 'KJVA'), ('ASV', False, 'ASV 1901'), ('Byz', True, 'Robinson-Pierpont Byz NT'), ('TR', True, 'Textus Receptus')]:
        parsed = parse_scrollmapper_json(paths[f'{name}.json'], nt_only=nt_only, edition_tag=tag)
        with open(os.path.join(CACHE_DIR, f'{name}.json'), 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, separators=(',', ':'))
        print(f"{name}: {len(parsed)} books, {sum(sum(len(c) for c in chs) for chs in parsed.values())} verses")

    nv = load_all_nova_vulgata()
    with open(os.path.join(CACHE_DIR, 'NovaVulgata.json'), 'w', encoding='utf-8') as f:
        json.dump(nv, f, ensure_ascii=False, separators=(',', ':'))
    empty_nv = [b for b, chs in nv.items() if sum(len(c) for c in chs) == 0]
    print(f"Nova Vulgata: {len(nv)} books, {sum(sum(len(c) for c in chs) for chs in nv.values())} verses | empty={empty_nv}")
    assert len(nv) == 73 and not empty_nv, f"Nova Vulgata incomplete: empty={empty_nv}"

    for label, ds in [('DRA', dra), ('WEBC', webc), ('KJVA', json.load(open(os.path.join(CACHE_DIR, 'KJVA.json'), encoding='utf-8'))), ('NV', nv)]:
        print(f"  Spot [{label}] Gen 1:1 -> {ds['gen'][0][0][:60]} | VulPs 22(23):1 -> {ds['ps'][21][0][:50]} | Esth chs={len(ds.get('esth',[]))} | Dan chs={len(ds.get('dan',[]))} | 2Macc 12:45 -> {ds.get('2macc', [[]]*12)[11][43][:45] if len(ds.get('2macc',[]))>=12 and len(ds['2macc'][11])>=44 else 'N/A'}")

if __name__ == '__main__':
    main()
