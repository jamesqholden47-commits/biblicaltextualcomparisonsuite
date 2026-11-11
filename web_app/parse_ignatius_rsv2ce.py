# -*- coding: utf-8 -*-
"""
Deterministic parser for James's local Ignatius Catholic Study Bible (RSV-2CE, Imprimatur)
for private in-house use ONLY:
- 27 NT books from born-digital Ignatius NT EPUB (2009)
- 16 OT books from born-digital Ignatius OT EPUBs (Deut, Josh, Judg, Ruth, 1-2 Kgs, Tob, Jdt, Esth, Prov, Eccl, Song, Isa, Dan, 1-2 Macc)
-  2 OT books from born-digital vector PDFs (Genesis, Exodus)
Total: 45 born-digital RSV-2CE books (scanned OCR volumes 1-2 Samuel & Job excluded to preserve clean text; fallback to DRA Imprimatur).
"""
import html
import json
import os
import re
import sys
import urllib.parse
import zipfile
import fitz

sys.stdout.reconfigure(encoding='utf-8')

ROOT_PDF = r"C:\Users\Elation\PDFS\01_Biblical_Studies_and_Canon"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, 'sources_cache')
os.makedirs(CACHE_DIR, exist_ok=True)
OUT_JSON = os.path.join(CACHE_DIR, 'RSV2CE.json')

def clean_verse_text(s):
    s = html.unescape(s)
    s = s.replace('\u00a0', ' ').replace('\u200b', '')
    s = re.sub(r'^/sup>\s*', '', s)
    s = re.sub(r'\s*/sup>\s*', ' ', s)
    s = re.sub(r'\s*\[Map\]\s*', ' ', s)
    s = re.sub(r'<[a-zA-Z]*$', '', s)
    s = re.sub(r'\bL\s*ORD\b', 'LORD', s)
    s = re.sub(r'\bG\s*OD\b', 'GOD', s)
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s+([,.;:?!\)\]\u201d\u2019])', r'\1', s)
    s = re.sub(r'([\(\[\u201c\u2018])\s+', r'\1', s)
    return s.strip()

def _parse_verse_num_token(inner):
    """Strip nested footnote letters/asterisks from a <sup> or bold span and extract clean verse number(s)."""
    raw_txt = html.unescape(re.sub(r'<[^>]+>', ' ', inner)).replace('\u00a0', ' ').strip()
    raw_txt = re.sub(r'\s+', ' ', raw_txt)
    if not raw_txt or re.match(r'^[*†‡a-zA-Z,\s]+$', raw_txt):
        return ('footnote', 0)
    # Now strip pure footnote anchor/span tags attached beside a digit (e.g. "2 q" or "h 27")
    cleaned = re.sub(r'<(?:a|span)\b[^>]*>\s*(?:<[^>]+>\s*)*[*†‡a-zA-Z]\s*(?:</[^>]+>\s*)*</(?:a|span)>', ' ', inner, flags=re.S)
    txt = html.unescape(re.sub(r'<[^>]+>', ' ', cleaned)).replace('\u00a0', ' ').strip()
    txt = re.sub(r'\s+', ' ', txt)
    if not txt:
        return ('footnote', 0)
    # Single integer or identical duplicated integer ("20 20" -> 20)
    parts = txt.split()
    if all(p.isdigit() for p in parts) and (len(parts) == 1 or len(set(parts)) == 1):
        return ('single', int(parts[0]))
    # Combined verse range like "7, 8" or "7-8" or "7–8"
    mr = re.match(r'^(\d+)\s*[,\-–]\s*(\d+)$', txt)
    if mr:
        a, b = int(mr.group(1)), int(mr.group(2))
        if b == a + 1:
            return ('range', a, b)
    if re.match(r'^[*†‡a-zA-Z,\s]+$', txt):
        return ('footnote', 0)
    return None

def strip_footnotes_calibre(raw_html):
    h = raw_html.replace('<b>sup&gt;</b>', '')
    def repl_sup(m):
        inner = m.group(0)
        parsed = _parse_verse_num_token(inner)
        if parsed:
            if parsed[0] == 'single':
                return f' \x00V:{parsed[1]}\x00 '
            if parsed[0] == 'range':
                return f' \x00V:{parsed[1]}\x00 \x00VR:{parsed[1]}-{parsed[2]}\x00 '
            if parsed[0] == 'footnote':
                return ''
        return inner

    h = re.sub(r'<sup[^>]*>.*?</sup>', repl_sup, h, flags=re.S | re.I)

    def repl_a(m):
        inner = m.group(0)
        txt = re.sub(r'<[^>]+>', '', inner).replace('\u00a0', ' ').strip()
        if re.match(r'^[*†‡]$', txt):
            return ''
        return inner

    return re.sub(r'<a\b[^>]*>.*?</a>', repl_a, h, flags=re.S | re.I)

def extract_verses_from_chapter_html(ch_html, expected_ch_num=None):
    h = ch_html
    h = re.sub(r'<h[1-6][^>]*>.*?</h[1-6]>', ' ', h, flags=re.S | re.I)
    # Drop pure italic footnote/note blocks or heading paragraphs with no digits
    h = re.sub(r'<p\b[^>]*class="[^"]*(?:subhd|chapOp|center|Bible_H|calibre18)[^"]*"[^>]*>.*?</p>', ' ', h, flags=re.S | re.I)
    # Also drop Calibre section headings: short <p><span class="bold">Title...</span></p> with no digits
    h = re.sub(r'<p\b[^>]*>\s*(?:<span[^>]*>){0,4}\s*<(?:b|span class="bold")>[^<\d]{3,90}</(?:b|span)>(?:\s*</span>){0,4}\s*</p>', ' ', h, flags=re.S | re.I)

    h = strip_footnotes_calibre(h)

    def clean_bold_num(m):
        inner = m.group(1)
        if '\x00V:' in inner:
            return inner
        parsed = _parse_verse_num_token(inner)
        if parsed:
            if parsed[0] == 'single':
                return f' \x00N:{parsed[1]}\x00 '
            if parsed[0] == 'range':
                return f' \x00N:{parsed[1]}\x00 \x00VR:{parsed[1]}-{parsed[2]}\x00 '
            if parsed[0] == 'footnote':
                return ''
        return inner

    h = re.sub(r'<(?:b|strong)>(.*?)</(?:b|strong)>', clean_bold_num, h, flags=re.S | re.I)
    h = re.sub(r'<span\b[^>]*class="[^"]*bold[^"]*"[^>]*>(.*?)</span>', clean_bold_num, h, flags=re.S | re.I)

    h = re.sub(r'</?(?:p|div|blockquote|br|li|tr)[^>]*>', ' ', h, flags=re.I)
    h = re.sub(r'<[^>]+>', '', h)
    h = clean_verse_text(h)

    # Strip header block at very top of Chapter 1 books
    if expected_ch_num == 1:
        m1 = re.search(r'\x00[NV]:1\x00', h)
        if m1 and m1.start() < 900:
            pre = h[:m1.start()]
            if any(k in pre for k in ('Chapters', 'Essays', 'THE ', 'BOOK OF', 'GOSPEL', 'LETTER')):
                h = h[m1.start():]

    tokens = re.split(r'(\x00(?:[VN]:\d+|VR:\d+-\d+)\x00)', h)
    verses = {}
    combined_pairs = []
    cur_v = None
    seen_any_prose = False
    for tok in tokens:
        mvr = re.match(r'^\x00VR:(\d+)-(\d+)\x00$', tok)
        if mvr:
            combined_pairs.append((int(mvr.group(1)), int(mvr.group(2))))
            continue
        mt = re.match(r'^\x00([VN]):(\d+)\x00$', tok)
        if mt:
            kind, num = mt.group(1), int(mt.group(2))
            if cur_v is None and not seen_any_prose:
                if expected_ch_num is not None and num == expected_ch_num:
                    cur_v = 1
                    verses.setdefault(1, [])
                    continue
                elif num == 1:
                    cur_v = 1
                    verses.setdefault(1, [])
                    continue
                elif num <= 5:
                    cur_v = num
                    verses.setdefault(num, [])
                    continue
            else:
                if cur_v is not None and num > cur_v and num <= cur_v + 5:
                    cur_v = num
                    verses.setdefault(cur_v, [])
                    continue
                elif cur_v is None and num <= 3:
                    cur_v = num
                    verses.setdefault(cur_v, [])
                    continue
        else:
            t = tok.strip()
            if not t:
                continue
            if cur_v is None:
                seen_any_prose = True
                cur_v = 1
                verses.setdefault(1, []).append(t)
            else:
                seen_any_prose = True
                verses.setdefault(cur_v, []).append(t)

    if not verses:
        return []
    for a, b in combined_pairs:
        if verses.get(a) and not verses.get(b):
            verses[a] = ['[vv. ' + f'{a}-{b} combined in RSV-2CE]'] + verses[a]
            verses[b] = [f'[Combined in v.{a} above (RSV-2CE)]']
    max_v = max(verses.keys())
    return [clean_verse_text(' '.join(verses.get(i, []))) for i in range(1, max_v + 1)]

def after_tag_close(text, aid):
    """Return index immediately AFTER the closing '>' of the tag containing id="aid"."""
    pos = text.find(f'id="{aid}"')
    if pos < 0:
        return -1
    gt = text.find('>', pos)
    return (gt + 1) if gt >= 0 else pos

def parse_ignatius_nt_epub():
    nt_ep = os.path.join(ROOT_PDF, r"_AA_ Curtis Mitch & Scott Hahn - Ignatius Catholic Study Bible New Testament (2009).epub")
    with zipfile.ZipFile(nt_ep) as z:
        raw = z.read("OEBPS/page-1.html").decode("utf-8", errors="ignore")

    # Apply exact anchor-pinned fixes for 7 verified typesetting defects in the 2009 Ignatius NT EPUB
    nt_fixes = [
        ('id="filepos160097"/></div><p>', 'id="filepos160097"/></div><p><b>4</b> '),  # Matt 5:4 omitted verse number
        ('id="filepos707078"/><small><a href="#filepos5383600"><span><b><span><span>1</span></span></b></span></a></small>',
         'id="filepos707078"/><small><a href="#filepos5383600"><span><b><span><span>23</span></span></b></span></a></small>'),  # Mark 1:23 typo '1'
        ('<b><span>55</span></b></span><a id="filepos1337055"/>',
         '<b><span>5</span></b></span><a id="filepos1337055"/>'),  # Luke 24:5 typo '55'
        ('id="filepos1778466"/><small><span><b><span>15</span></b></span></small>',
         'id="filepos1778466"/><small><span><b><span>2</span></b></span></small>'),  # John 15:2 typo '15'
        ('id="filepos2247023"/><small/>', 'id="filepos2247023"/><small><b>35</b></small>'),  # Acts 19:35 empty <small/>
        ('id="filepos2943509"/><small><a href="#filepos5876623"><span><b><span><span>1</span></span></b></span></a></small>',
         'id="filepos2943509"/><small><a href="#filepos5876623"><span><b><span><span>23</span></span></b></span></a></small>'),  # 1Cor 16:23 typo '1'
        ('id="filepos3155227"/><small/>', 'id="filepos3155227"/><small><b>10</b></small>'),  # 2Cor 10:10 empty <small/>
        ('id="filepos4621659"/><small><a href="#filepos6009087"><span><b><span><span>1</span></span></b></span></a></small>',
         'id="filepos4621659"/><small><a href="#filepos6009087"><span><b><span><span>6</span></span></b></span></a></small>'),  # Rev 9:6 typo '1'
    ]
    for old_s, new_s in nt_fixes:
        assert old_s in raw, f"NT EPUB anchor fix missing: {old_s[:40]}"
        raw = raw.replace(old_s, new_s, 1)

    NT_IDS = [
        'matt', 'mark', 'luke', 'john', 'acts', 'rom', '1cor', '2cor', 'gal', 'eph',
        'phil', 'col', '1thess', '2thess', '1tim', '2tim', 'titus', 'phlm', 'heb',
        'jas', '1pet', '2pet', '1john', '2john', '3john', 'jude', 'rev'
    ]
    toc_start = raw.find("THE NEW TESTAMENT")
    toc_chunk = raw[toc_start:toc_start + 22000]
    blocks = re.findall(r'<b>([^<]{8,80})</b></p>(.*?)(?=<b>(?:The |Index )|</p>\s*<div>|$)', toc_chunk, re.S)
    book_slices = []
    for title, rest in blocks:
        m_t = re.search(r'<a href="#(filepos\d+)"><i><span><span>Text</span></span></i></a>', rest)
        m_c = re.search(r'<a href="#(filepos\d+)"><i><span><span>Commentary</span></span></i></a>', rest)
        if m_t and m_c:
            book_slices.append((title.strip(), m_t.group(1), m_c.group(1)))
    assert len(book_slices) == 27

    nt_out = {}
    for bid, (title, t_id, c_id) in zip(NT_IDS, book_slices):
        p_t = after_tag_close(raw, t_id)
        raw_pc = raw.find(f'id="{c_id}"')
        p_c = raw.rfind('<', 0, raw_pc + 1) if raw_pc >= 0 else len(raw)
        sec = raw[p_t:p_c]
        chap_links = []
        idx_ch = sec.find('Chapters</p>')
        if idx_ch >= 0:
            # Scan strictly within the Chapters anchor paragraph(s) up to the next section/verse content!
            sub = sec[idx_ch:idx_ch + 2800]
            end_markers = [sub.find(k) for k in ('Essays', 'Study Questions', '</div><p><a', '<p><b>') if sub.find(k) > 20]
            if end_markers:
                sub = sub[:min(end_markers)]
            for aid, n in re.findall(r'<a href="#(filepos\d+)"[^>]*>(?:<[^>]+>)*(\d+)(?:</[^>]+>)*</a>', sub):
                num = int(n)
                # Only keep strictly sequential 1, 2, 3... matching actual Chapters bar!
                if num == len(chap_links) + 1:
                    chap_links.append((num, aid))
                elif chap_links:
                    break

        if chap_links:
            chaps = []
            for ci, (cnum, aid) in enumerate(chap_links):
                start = after_tag_close(raw, aid)
                if ci + 1 < len(chap_links):
                    next_p = raw.find(f'id="{chap_links[ci+1][1]}"')
                else:
                    next_p = p_c
                # Back up before `<a id="next"` opening tag if mid-tag
                end = raw.rfind('<', start, next_p + 1) if next_p > start else next_p
                ch_html = raw[start:end]
                ch_html = re.sub(r'<p>(?!.*?(?:<b>|<sup|<a href=))[^<]{1,90}</p>', ' ', ch_html, flags=re.S)
                chaps.append(extract_verses_from_chapter_html(ch_html, expected_ch_num=cnum))
            nt_out[bid] = chaps
        else:
            # Single-chapter book
            m1 = re.search(r'<a[^>]*><b><span><span>1</span></span></b></a>|<div><a id="filepos\d+"/></div><p>.*?<b>1</b>', sec, re.S)
            start = m1.start() if m1 else 0
            ch_html = re.sub(r'<p>(?!.*?(?:<b>|<sup|<a href=))[^<]{1,90}</p>', ' ', sec[start:], flags=re.S)
            nt_out[bid] = [extract_verses_from_chapter_html(ch_html, expected_ch_num=1)]
    return nt_out

def parse_maccabees_epub():
    ep = os.path.join(ROOT_PDF, r"_AA_ Hahn, Scott;Mitch, Curtis;Walters, Dennis K ;Thomas, - The First and Second Books of the Maccabees (Ignatius (2023).epub")
    out = {}
    with zipfile.ZipFile(ep) as z:
        for bid, fname in [('1macc', 'OEBPS/1-Maccabees.xhtml'), ('2macc', 'OEBPS/2-Maccabees.xhtml')]:
            raw = z.read(fname).decode('utf-8', errors='ignore')
            raw = re.sub(r'<p[^>]*class="(?:chapOp|center|subhd)"[^>]*>.*?</p>', ' ', raw, flags=re.S)
            raw = re.sub(r'<span class="fnr">.*?</span>', '', raw, flags=re.S)
            # Note id="cv2-20-22" has an optional range suffix (-\d+), and <p id="cv15-33">32 ... has printed verse 32 right inside!
            raw_marked = re.sub(
                r'(?:<span class="(?:dc|vn)"[^>]*>)?<(?P<tag>p|span|a)[^>]*\bid="cv(\d+)-(\d+)(?:-\d+)?"[^>]*>',
                lambda m: f'\x00CV:{m.group(2)}-{m.group(3)}:{m.group("tag")}\x00',
                raw, flags=re.S
            )
            parts = re.split(r'\x00CV:(\d+)-(\d+):(p|span|a)\x00', raw_marked)
            ch_dict = {}
            for i in range(1, len(parts), 4):
                c, v, tag, body = int(parts[i]), int(parts[i+1]), parts[i+2], parts[i+3]
                body = re.sub(r'^(?:\s*(?:<a\b[^>]*>)?\s*</?(?:a|span)[^>]*>)+', '', body)
                body = re.sub(r'</?(?:p|div|blockquote|br)[^>]*>', ' ', body)
                body = re.sub(r'<[^>]+>', '', body)
                txt = clean_verse_text(body)
                # Strip leading verse number, OR handle EPUB id="cv15-33" whose leading printed digit is "32 "!
                m_lead = re.match(r'^(\d+)\s+(.+)$', txt)
                if m_lead:
                    lead_n = int(m_lead.group(1))
                    if lead_n == v:
                        txt = m_lead.group(2).strip()
                    elif tag == 'p' and lead_n == v - 1 and lead_n not in ch_dict.get(c, {}):
                        v = lead_n
                        txt = m_lead.group(2).strip()
                if txt:
                    ch_dict.setdefault(c, {})[v] = txt
            max_c = max(ch_dict.keys())
            out[bid] = [[ch_dict[c].get(v, '') for v in range(1, max(ch_dict[c].keys()) + 1)] for c in range(1, max_c + 1)]
    return out

def parse_deut_epub():
    ep = os.path.join(ROOT_PDF, r"_AA_ Hahn, Scott;Mitch, Curtis;Walters, Dennis;Barber, Michael; - Deuteronomy (Ignatius Catholic Study Bible).epub")
    with zipfile.ZipFile(ep) as z:
        raw = z.read("OEBPS/deuteronomy_0008.xhtml").decode("utf-8", errors="ignore")
    raw = re.sub(r'<p class="Bible_H[^"]*"[^>]*>.*?</p>', ' ', raw, flags=re.S)
    raw = re.sub(r'<sup>.*?</sup>', '', raw, flags=re.S)
    raw = re.sub(r'<span class="CharOverride-18"[^>]*>.*?</span>', '', raw, flags=re.S)
    # Strip asterisk/letter footnote anchors immediately after verse numbers (e.g. Deut 6:4 * )
    raw = re.sub(r'<a\b[^>]*href="[^"]*#fn[^"]*"[^>]*>.*?</a>', '', raw, flags=re.S)

    drops = list(re.finditer(r'<span class="_idGenDropcap[^"]*"[^>]*>(?:<[^>]+>)*(\d+)(?:</[^>]+>)*</span>', raw, re.S))
    assert len(drops) == 34, f"Deut dropcaps expected 34, got {len(drops)}"
    chaps = []
    for i, m in enumerate(drops):
        chunk = raw[m.end():(drops[i + 1].start() if i + 1 < len(drops) else len(raw))]
        chunk = re.sub(r'<span class="CharOverride-4"[^>]*>(?:<[^>]+>)*(\d+)(?:</[^>]+>)*</span>', lambda mm: f' \x00V:{mm.group(1)}\x00 ', chunk, flags=re.S)
        # Paragraph-initial verse numbers in Deut are often wrapped in <a href="...#note...">9</a> right after <p ...>!
        chunk = re.sub(r'(<p\b[^>]*>)\s*(?:<a\b[^>]*>)?(\d+)(?:</a>)?(?=[\s\u00a0“"\'\(A-Za-z*])', lambda mm: f'{mm.group(1)}\x00V:{mm.group(2)}\x00 ', chunk)
        chunk = re.sub(r'</?(?:p|div|blockquote|br)[^>]*>', ' ', chunk)
        chunk = re.sub(r'<[^>]+>', '', chunk)
        chunk = clean_verse_text(chunk)
        parts = re.split(r'(\x00V:\d+\x00)', chunk)
        vdict = {1: []}
        cur_v = 1
        for p in parts:
            mv = re.match(r'^\x00V:(\d+)\x00$', p)
            if mv:
                nv = int(mv.group(1))
                if nv > cur_v and nv <= cur_v + 5:
                    cur_v = nv
                    vdict.setdefault(cur_v, [])
            elif p.strip():
                vdict.setdefault(cur_v, []).append(p.strip())
        chaps.append([clean_verse_text(' '.join(vdict.get(v, []))) for v in range(1, max(vdict.keys()) + 1)])
    return chaps

def parse_calibre_epub_book(epub_path, specs):
    out = {}
    with zipfile.ZipFile(epub_path) as z:
        opf_name = [n for n in z.namelist() if n.endswith('.opf')][0]
        opf = z.read(opf_name).decode('utf-8', errors='ignore')
        opf_dir = os.path.dirname(opf_name)
        id_to_href = dict(re.findall(r'<item[^>]+id="([^"]+)"[^>]+href="([^"]+)"', opf))
        if not id_to_href:
            id_to_href = {i: h for h, i in re.findall(r'<item[^>]+href="([^"]+)"[^>]+id="([^"]+)"', opf)}
        spine_ids = re.findall(r'<itemref[^>]+idref="([^"]+)"', opf)
        spine_files = []
        for sid in spine_ids:
            href = id_to_href.get(sid, '')
            if href:
                full = (opf_dir + '/' + href).lstrip('/') if opf_dir else href
                full = html.unescape(full)
                full_dec = urllib.parse.unquote(full)
                if full_dec in z.namelist():
                    spine_files.append(full_dec)
                elif full in z.namelist():
                    spine_files.append(full)

        file_texts = {}
        concat = []
        file_offset = {}
        cur_pos = 0
        for sf in spine_files:
            txt = z.read(sf).decode('utf-8', errors='ignore')
            file_texts[sf] = txt
            file_offset[sf] = cur_pos
            concat.append(txt)
            cur_pos += len(txt)
        full_html = ''.join(concat)

        def resolve_anchor(base_sf, href):
            if '#' not in href:
                return None
            fpart, aid = href.split('#', 1)
            fpart = urllib.parse.unquote(fpart)
            if fpart:
                matches = [sf for sf in spine_files if sf.endswith(fpart) or os.path.basename(sf) == os.path.basename(fpart)]
                target_sf = matches[0] if matches else base_sf
            else:
                target_sf = base_sf
            base_idx = file_offset[target_sf]
            ft = file_texts[target_sf]
            pos = ft.find(f'id="{aid}"')
            if pos < 0:
                return None
            # Advance PAST closing '>' so `id="filepos..."/>` is never left inside slice!
            gt = ft.find('>', pos)
            return base_idx + (gt + 1 if gt >= 0 else pos)

        stop_markers = []
        for sf in spine_files:
            ft = file_texts[sf]
            if re.search(r'<title[^>]*>.*?(?:Commentary|Study Questions)', ft, re.I) or re.search(r'>\s*(?:COMMENTARY|Commentary on|Study Questions|STUDY QUESTIONS)\s*<', ft[:2500]):
                stop_markers.append(file_offset[sf])
        ncx_names = [n for n in z.namelist() if n.endswith('.ncx')]
        if ncx_names:
            ncx = z.read(ncx_names[0]).decode('utf-8', errors='ignore')
            for lbl, src in re.findall(r'<text>([^<]+)</text>\s*</navLabel>\s*<content src="([^"]+)"', ncx):
                if any(k in lbl.lower() for k in ['commentary', 'study question', 'introduction to ', 'outline of ', 'word study', 'topical essay', 'map:', 'chart:']):
                    pos = resolve_anchor(spine_files[0], src if '#' in src else src + '#TOP')
                    if pos is None:
                        sp = urllib.parse.unquote(src.split('#')[0])
                        for sf in spine_files:
                            if sf.endswith(sp) or os.path.basename(sf) == os.path.basename(sp):
                                stop_markers.append(file_offset[sf])
                                break
                    else:
                        stop_markers.append(pos)
        stop_markers = sorted(set(stop_markers))

        for bid, chap_file_hint, expected_ch in specs:
            sf_match = [sf for sf in spine_files if sf.endswith(chap_file_hint) or os.path.basename(sf) == chap_file_hint]
            assert sf_match, f"File {chap_file_hint} not found in {os.path.basename(epub_path)}"
            sf0 = sf_match[0]
            ft0 = file_texts[sf0]
            idx_ch = ft0.find('Chapters')
            assert idx_ch >= 0, f"Chapters heading not found in {sf0}"
            chunk = ft0[idx_ch:idx_ch + 6000]
            raw_refs = re.findall(r'<a href="([^"]+)"[^>]*>(?:<[^>]+>)*(\d+)(?:</[^>]+>)*</a>', chunk)
            chap_anchors = []
            seen_nums = set()
            for href, num_s in raw_refs:
                n = int(num_s)
                if n == len(chap_anchors) + 1 and n not in seen_nums:
                    abs_pos = resolve_anchor(sf0, href)
                    if abs_pos is not None:
                        chap_anchors.append((n, abs_pos))
                        seen_nums.add(n)
                if len(chap_anchors) >= expected_ch:
                    break

            assert len(chap_anchors) == expected_ch, f"{bid}: expected {expected_ch} chap anchors, got {len(chap_anchors)}"
            all_phys = sorted(set([pos for _, pos in chap_anchors] + stop_markers))

            def next_phys_end(pos):
                for b in all_phys:
                    if b > pos:
                        return full_html.rfind('<', pos, b + 1) if b > pos else b
                return len(full_html)

            if bid == 'esth':
                # Greek Esther interleaves Additions A–F across Chapters 1..10. Map exact physical segments!
                anc = dict(chap_anchors)
                p_11_2 = resolve_anchor(sf0, 'part0018_split_001.html#filepos530442')
                p_13_1 = resolve_anchor(sf0, 'part0018_split_001.html#filepos549394')
                p_3_14 = resolve_anchor(sf0, 'part0018_split_001.html#filepos552016')
                p_8_13 = resolve_anchor(sf0, 'part0018_split_001.html#filepos584787')
                chaps = []
                for cnum in range(1, 17):
                    st = anc[cnum]
                    if cnum == 3:
                        sl = full_html[st:full_html.rfind('<', st, p_13_1)] + ' ' + full_html[p_3_14:next_phys_end(st if False else p_3_14)]
                    elif cnum == 8:
                        sl = full_html[st:next_phys_end(st)] + ' ' + full_html[p_8_13:next_phys_end(p_8_13)]
                    elif cnum == 11:
                        sl = full_html[st:next_phys_end(st)] + ' ' + full_html[p_11_2:next_phys_end(p_11_2)]
                    elif cnum == 13:
                        sl = full_html[p_13_1:full_html.rfind('<', p_13_1, p_3_14)] + ' ' + full_html[st:next_phys_end(st)]
                    elif cnum == 16:
                        sl = full_html[st:full_html.rfind('<', st, p_8_13)]
                    else:
                        sl = full_html[st:next_phys_end(st)]
                    vs = extract_verses_from_chapter_html(sl, expected_ch_num=cnum)
                    if cnum == 5:
                        # Greek Esther places Addition D (ch 15:1-16) before 5:3; EPUB starts Ch 5 at "[5] 3 And the king..."
                        # Shift v.1..v.N (3..14) properly so v1, v2 cross-reference Ch 15 and v3 starts "And the king said..."
                        note = "[See Greek Esther 15:1-16 (Addition D), placed before 5:3 in RSV-2CE]"
                        if len(vs) >= 3 and vs[0].startswith('[5]') and vs[2].startswith('And the king said'):
                            vs[0] = note
                            vs[1] = note
                    chaps.append(vs)
                out[bid] = chaps
                continue

            chaps = []
            for ci, (cnum, st_pos) in enumerate(chap_anchors):
                en_pos = next_phys_end(st_pos)
                sl = full_html[st_pos:en_pos]
                if bid == 'dan' and cnum == 11:
                    sl = sl.replace('<a id="filepos171283"></a>', '<a id="filepos171283"></a><b>7</b> ', 1)
                chaps.append(extract_verses_from_chapter_html(sl, expected_ch_num=cnum))
            out[bid] = chaps
    return out

def parse_gen_exod_pdf(bid, pdf_path, start_p1, end_p1, expected_ch):
    """Parse Genesis / Exodus born-digital vector PDF pages using exact font metrics + span gap spacing."""
    doc = fitz.open(pdf_path)
    cur_ch = 0
    cur_v = 0
    chaps = {}

    for pno in range(start_p1 - 1, end_p1):
        blocks = doc[pno].get_text('dict')['blocks']
        for b in blocks:
            for l in b.get('lines', []):
                spans = l.get('spans', [])
                line_txt = ''.join(s['text'] for s in spans).strip()
                if not line_txt:
                    continue
                y0 = l['bbox'][1]
                if y0 < 62 and len(line_txt) < 40:
                    continue
                max_sz = max(s['size'] for s in spans)
                # Skip top chapter index lines (size ~15 and pure numbers) and bold section headings (size >= 14 and bold)
                if all(abs(s['size'] - 15.0) < 0.8 or abs(s['size'] - 16.9) < 0.8 for s in spans):
                    if line_txt[0].isdigit() or line_txt in ('Chapters', 'GENESIS', 'EXODUS') or (spans[0]['flags'] & 16):
                        continue
                if len(spans) == 1 and max_sz >= 13.5 and (spans[0]['flags'] & 16):
                    continue

                prev_x1 = None
                for s in spans:
                    sz = s['size']
                    fl = s['flags']
                    t = s['text']
                    ts = t.strip()
                    is_bold = bool(fl & 16)
                    # Insert space if bounding box gap indicates word break (e.g. small-caps "God" + "said")
                    if prev_x1 is not None and (s['bbox'][0] - prev_x1) > 1.2:
                        if cur_ch > 0 and cur_v > 0 and chaps.get(cur_ch, {}).get(cur_v):
                            last_piece = chaps[cur_ch][cur_v][-1]
                            if not last_piece.endswith((' ', '“', '‘', '(')) and not t.startswith((' ', ',', '.', ';', ':', '?', '!', '”', '’', ')')):
                                chaps[cur_ch][cur_v].append(' ')
                    prev_x1 = s['bbox'][2]

                    if sz >= 17.5 and ts.isdigit():
                        n = int(ts)
                        if n == cur_ch + 1:
                            cur_ch = n
                            cur_v = 1
                            chaps.setdefault(cur_ch, {}).setdefault(1, [])
                            continue
                    # Skip bold headings & chapter titles >= 13.5pt, KEEP poetic 15.0pt non-bold Bible text!
                    if sz >= 16.5 or (sz >= 13.5 and is_bold):
                        continue
                    if is_bold and ts.isdigit():
                        nv = int(ts)
                        if cur_ch > 0 and ((nv > cur_v and nv <= cur_v + 4) or (nv not in chaps.get(cur_ch, {}) and abs(nv - cur_v) <= 4)):
                            cur_v = nv
                            chaps[cur_ch].setdefault(cur_v, [])
                            continue
                    if is_bold and re.match(r'^[*†‡a-z]{1,2}$', ts):
                        continue
                    if ts in ('*', '†', '‡') and len(spans) > 1:
                        continue
                    if cur_ch > 0 and cur_v > 0:
                        chaps[cur_ch].setdefault(cur_v, []).append(t)
                # New line spacing between lines of the same verse
                if cur_ch > 0 and cur_v > 0 and chaps.get(cur_ch, {}).get(cur_v):
                    if not chaps[cur_ch][cur_v][-1].endswith((' ', '-', '—')):
                        chaps[cur_ch][cur_v].append(' ')

    assert len(chaps) == expected_ch, f"{bid}: expected {expected_ch} chapters from PDF, got {len(chaps)}"
    return [
        [clean_verse_text(''.join(chaps[c].get(v, []))) for v in range(1, max(chaps[c].keys()) + 1)]
        for c in range(1, expected_ch + 1)
    ]

def main():
    rsv = {}
    print("1. Parsing Ignatius NT EPUB (27 books)...")
    rsv.update(parse_ignatius_nt_epub())
    print(f"   NT done: 27 books, {sum(sum(len(c) for c in rsv[b]) for b in rsv)} verses")

    print("2. Parsing Ignatius Maccabees EPUB (2 books)...")
    rsv.update(parse_maccabees_epub())

    print("3. Parsing Ignatius Deuteronomy EPUB (1 book)...")
    rsv['deut'] = parse_deut_epub()

    calibre_jobs = [
        (r"_AA_ Scott Hahn; Curtis Mitch - Joshua Ignatius Catholic Study Bible (The Ignatius Catholic (2017).epub",
         [('josh', 'index_split_009.html', 24)]),
        (r"_AA_ Scott Hahn; Curtis Mitch - Judges and Ruth (Ignatius Catholic Study Bible) (2015).epub",
         [('judg', 'index_split_008.html', 21), ('ruth', 'index_split_012.html', 4)]),
        (r"_AA_ Hahn, Scott & Mitch, Curtis - Ignatius Catholic Study Bible 1 & 2 Kings (The Ignatius (2017).epub",
         [('1kgs', 'part0009.html', 22), ('2kgs', 'part0030.html', 25)]),
        (r"_AA_ Scott Hahn & Curtis Mitch - Tobit, Judith, and Esther Ignatius Catholic Study Bible (2019).epub",
         [('tob', 'part0006_split_001.html', 14), ('jdt', 'part0014_split_001.html', 16), ('esth', 'part0018_split_001.html', 16)]),
        (r"_AA_ Scott Hahn; Curtis Mitch; Dennis Walters - Proverbs, Ecclesiastes, and Song of Solomon Ignatius (2013).epub",
         [('prov', 'index_split_008.html', 31), ('eccl', 'index_split_014.html', 12), ('song', 'index_split_019.html', 8)]),
        (r"_AA_ Scott Hahn; Curtis Mitch - The Ignatius Catholic Study Bible Isaiah.epub",
         [('isa', 'index_split_006.html', 66)]),
        (r"_AA_ Hahn Ph D , Scott, Mitch, Curtis - Daniel Ignatius Catholic Study Bible.epub",
         [('dan', 'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_007.html', 14)]),
    ]
    print("4. Parsing 13 OT Calibre EPUB books...")
    for fn, specs in calibre_jobs:
        rsv.update(parse_calibre_epub_book(os.path.join(ROOT_PDF, fn), specs))

    print("5. Parsing Ignatius Genesis & Exodus born-digital PDFs...")
    rsv['gen'] = parse_gen_exod_pdf('gen', os.path.join(ROOT_PDF, r"_AA_ Hahn, Scott & Mitch, Curtis - The Ignatius Catholic Study Bible Genesis (2011).pdf"), 27, 90, 50)
    rsv['exod'] = parse_gen_exod_pdf('exod', os.path.join(ROOT_PDF, r"_AA_ Hahn, Scott & Mitch, Curtis - The Ignatius Catholic Study Bible Exodus.pdf"), 27, 85, 40)

    # Label authentic RSV-2CE critical-text (NA28) verse omissions vs Clementine Vulgate / Douay-Rheims
    NA28_CRITICAL_OMISSIONS = {
        ('matt', 12, 47), ('matt', 17, 21), ('matt', 18, 11), ('matt', 23, 14),
        ('mark', 7, 16), ('mark', 9, 44), ('mark', 9, 46), ('mark', 11, 26), ('mark', 15, 28),
        ('luke', 17, 36), ('luke', 23, 17),
        ('john', 5, 4),
        ('acts', 8, 37), ('acts', 15, 34), ('acts', 24, 7), ('acts', 28, 29),
        ('rom', 16, 24),
    }
    for (bid, ch, v) in NA28_CRITICAL_OMISSIONS:
        if bid in rsv and ch <= len(rsv[bid]) and v <= len(rsv[bid][ch-1]):
            if not rsv[bid][ch-1][v-1]:
                rsv[bid][ch-1][v-1] = "[— Omitted from main text in RSV-2CE (follows critical Greek base NA28/UBS; see Douay-Rheims & Sixto-Clementine Vulgate)]"

    # Also ensure Acts 28:29 or Rom 16:24 trailing chapter verses exist up to DRA length if omitted at chapter end
    dra = json.load(open(os.path.join(CACHE_DIR, 'DRA.json'), encoding='utf-8'))
    for (bid, ch, v) in sorted(NA28_CRITICAL_OMISSIONS):
        if bid in rsv and ch <= len(rsv[bid]):
            while len(rsv[bid][ch-1]) < v and v <= len(dra[bid][ch-1]):
                rsv[bid][ch-1].append("[— Omitted from main text in RSV-2CE (follows critical Greek base NA28/UBS; see Douay-Rheims & Sixto-Clementine Vulgate)]")

    # Audit against DRA.json
    total_empty = 0
    bad_empties = []
    for bid in sorted(rsv.keys()):
        rc, dc = len(rsv[bid]), len(dra[bid])
        rv, dv = sum(len(c) for c in rsv[bid]), sum(len(c) for c in dra[bid])
        empties = [(ci+1, vi+1) for ci, c in enumerate(rsv[bid]) for vi, v in enumerate(c) if not v]
        ch_empties = [ci+1 for ci, c in enumerate(rsv[bid]) if not c]
        total_empty += len(empties)
        if empties or ch_empties:
            bad_empties.append((bid, empties, ch_empties))
        if rc != dc or empties or ch_empties or abs(rv - dv) > 15:
            print(f"  [AUDIT] {bid:6s}: ch {rc}/{dc} | v {rv}/{dv} | empty_v={len(empties)} {empties[:6]} | empty_ch={ch_empties}")

    assert not bad_empties, f"Unexpected empty slots in RSV-2CE: {bad_empties}"
    assert len(rsv) == 45, f"Expected 45 RSV-2CE books, got {len(rsv)}"

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(rsv, f, ensure_ascii=False, separators=(',', ':'))
    print(f"\nSaved {len(rsv)} RSV-2CE books ({sum(sum(len(c) for c in chs) for chs in rsv.values())} verses, empty={total_empty}) -> {OUT_JSON}")
    for check in [('gen',0,0), ('exod',21,1), ('exod',21,2), ('deut',0,8), ('deut',5,3), ('dan',10,6), ('1macc',14,31), ('matt',4,3), ('acts',18,34), ('jas',0,6), ('esth',4,2), ('esth',7,12), ('esth',10,0), ('esth',15,0)]:
        bid, ci, vi = check
        chs = rsv.get(bid, [])
        txt = chs[ci][vi][:85] if ci < len(chs) and vi < len(chs[ci]) else 'MISSING'
        print(f"  Spot {bid} {ci+1}:{vi+1} -> {txt}")

if __name__ == '__main__':
    main()
