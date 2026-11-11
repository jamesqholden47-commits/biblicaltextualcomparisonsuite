# -*- coding: utf-8 -*-
"""
James's bug report: NET and NIV can't be selected in the Parallel-view translation dropdowns.
Root cause, confirmed by reading build_plenary_logos_suite.py directly (Rule 5): NET and NIV were
only ever ingested as notes_shards STUDY NOTES (build_notes_shards.py) — their actual verse TEXT
was never extracted into a translation stream, so TRANSLATION_REGISTRY has no 'net21'/'niv_sb'
entry for the Parallel dropdown to list. This script builds that missing verse-text stream, in the
exact {book_id: [[verse_text, ...], ...]} schema build_plenary_logos_suite.py's other secondary
English streams (WEBC.json etc.) already use — confirmed by reading sources_cache/WEBC.json
directly before writing a schema from guesswork.

NET 2.1: reuses the book/file-range discovery already proven out in build_notes_shards.py
(load_net_book_file_ranges) rather than re-deriving it. Verse text is NOT simply "the chunk between
two verse spans" — NET's own file boundaries do not align with verse boundaries (a verse can start
in one physical file and finish in the next, e.g. Mark 8:34 spanning file1006->file1007), so the
running verse reference is carried across file boundaries the same way build_notes_shards.py's
extract_net_notes_for_book() already does, not reset per file. One real hazard found while
ground-truthing this: some files in a book's own file range are pure chapter-index tables (e.g.
file1040.xhtml for John — a <table> of chapter links with zero verse content) sitting between real
chapter-text files; appending such a file's HTML to whatever verse happened to be open would
corrupt that verse with table markup, so any file containing a <table> is skipped entirely rather
than accumulated.

NIV: the NIV Study Bible's own hcp-nivsb20-*.xhtml files carry the running NIV text itself (verse
spans id="vBBCCCVVV"), not a separate "plain NIV" edition — confirmed by inspecting one of these
files directly rather than assuming a separate text-only source exists. Text runs from each verse
span to the next, is NOT split across files the way NET is (this source's own file boundaries
appear to follow its own logical page breaks, not interrupt the Scripture text of a given chapter),
but still strips study-note/endnote/footnote-reference apparatus baked into the running text.
"""
import html as html_mod
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_notes_shards import load_net_book_file_ranges, NET_EPUB_PATH, SBL_BOOK_NUM_TO_ID  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, 'sources_cache')
os.makedirs(CACHE_DIR, exist_ok=True)
NET21_OUT_PATH = os.path.join(CACHE_DIR, 'NET21.json')
NIV11_OUT_PATH = os.path.join(CACHE_DIR, 'NIV11.json')

NIV_EPUB_PATH = (
    r"C:\Users\Elation\Downloads\NIV Study Bible, Fully Revised -- HarperCollins Christian "
    "Publishing -- Zondervan -- f67e480ceca371deaee30527d7f2a2d2 -- Anna" + "\u2019" + "s Archive.epub"
)

VERSE_SPAN_RE = re.compile(r'<span class="verse">(\d+):(\d+)</span>')


def _clean_net_chunk(raw):
    text = re.sub(r'<sup>.*?</sup>', '', raw, flags=re.S)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _verses_dict_to_chapter_list(verses):
    """verses: {(chap, verse): text}. Returns [[v1,v2,...], ...] 0-indexed chapters/verses, with
    any genuinely absent verse (never produced by the source at all) as an empty string rather
    than silently shortening the chapter array — downstream code indexes by position."""
    if not verses:
        return []
    max_chap = max(c for c, v in verses)
    chapters = []
    for c in range(1, max_chap + 1):
        vnums = [v for (cc, v) in verses if cc == c]
        if not vnums:
            chapters.append([])
            continue
        max_v = max(vnums)
        chapters.append([verses.get((c, v), '') for v in range(1, max_v + 1)])
    return chapters


def extract_net_full_bible_text():
    """Returns {book_id: [[verse, ...], ...]} for every book NET 2.1 covers (66 standard books;
    this source has no Deuterocanon)."""
    out = {}
    with zipfile.ZipFile(NET_EPUB_PATH) as zf:
        all_ranges = load_net_book_file_ranges(zf)
        for book_id, files in all_ranges:
            verses = {}
            last_ref = None
            for fname in files:
                ch_html = zf.read(f'OEBPS/{fname}').decode('utf-8', 'ignore')
                if '<table' in ch_html:
                    continue  # chapter-index navigation page, not Scripture content — see module docstring
                pos = 0
                for m in VERSE_SPAN_RE.finditer(ch_html):
                    if last_ref is not None:
                        chunk = _clean_net_chunk(ch_html[pos:m.start()])
                        if chunk:
                            verses[last_ref] = (verses.get(last_ref, '') + ' ' + chunk).strip()
                    last_ref = (int(m.group(1)), int(m.group(2)))
                    pos = m.end()
                if last_ref is not None:
                    chunk = _clean_net_chunk(ch_html[pos:])
                    if chunk:
                        verses[last_ref] = (verses.get(last_ref, '') + ' ' + chunk).strip()
            chapters = _verses_dict_to_chapter_list(verses)
            if chapters:
                out[book_id] = chapters
    return out


NIV_VERSE_SPAN_RE = re.compile(r'<span class="ver[a-z-]*" id="v(\d{2})(\d{3})(\d{3})">')


def _clean_niv_chunk(raw):
    text = re.sub(r'<a class="(?:enref|fnref|xref|xbr)"[^>]*>.*?</a>', '', raw, flags=re.S)
    text = re.sub(r'<[^>]+>', '', text)
    text = html_mod.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_niv_full_bible_text():
    """Returns {book_id: [[verse, ...], ...]}. NIV uses the same standard-66 BBCCCVVV numbering
    already verified for its Study Notes (SBL_BOOK_NUM_TO_ID, shared with SBL — both confirmed
    against the same John=43 cross-reference before trusting either)."""
    per_book_verses = {}
    with zipfile.ZipFile(NIV_EPUB_PATH) as zf:
        for name in [n for n in zf.namelist() if n.endswith('.xhtml') and 'hcp-nivsb20' in n]:
            txt = zf.read(name).decode('utf-8', 'ignore')
            matches = list(NIV_VERSE_SPAN_RE.finditer(txt))
            if not matches:
                continue
            for i, m in enumerate(matches):
                bb, cc, vv = int(m.group(1)), int(m.group(2)), int(m.group(3))
                book_id = SBL_BOOK_NUM_TO_ID.get(bb)
                if not book_id:
                    continue
                seg_start = m.end()
                seg_end = matches[i + 1].start() if i + 1 < len(matches) else min(seg_start + 2000, len(txt))
                chunk = _clean_niv_chunk(txt[seg_start:seg_end])
                if not chunk:
                    continue
                verses = per_book_verses.setdefault(book_id, {})
                key = (cc, vv)
                # A verse can appear more than once across overlapping file boundaries in this
                # source (adjacent chapter files sometimes both carry the tail of one file's last
                # verse) — keep the longer extraction rather than concatenating a duplicate.
                if key not in verses or len(chunk) > len(verses[key]):
                    verses[key] = chunk
    return {bid: _verses_dict_to_chapter_list(verses) for bid, verses in per_book_verses.items()}


def main():
    print('Extracting NET 2.1 full-Bible verse text (for the Parallel-view translation stream)...')
    net_books = extract_net_full_bible_text()
    net_verse_total = sum(len(ch) for chs in net_books.values() for ch in chs)
    with open(NET21_OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(net_books, f, ensure_ascii=False)
    print(f'  {len(net_books)} books, {net_verse_total} verses -> {NET21_OUT_PATH}')

    print('Extracting NIV Study Bible full-Bible verse text...')
    niv_books = extract_niv_full_bible_text()
    niv_verse_total = sum(len(ch) for chs in niv_books.values() for ch in chs)
    with open(NIV11_OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(niv_books, f, ensure_ascii=False)
    print(f'  {len(niv_books)} books, {niv_verse_total} verses -> {NIV11_OUT_PATH}')


if __name__ == '__main__':
    main()
