# -*- coding: utf-8 -*-
"""
Berean Standard Bible (BSB) verse-text stream.

Source: C:\\Users\\Elation\\Downloads\\bsb.txt, James's own file from BereanBible.com (public domain,
confirmed by the file's own header line). Format is dead simple compared to NET/NIV: one line per
verse, tab-separated "Book Chapter:Verse<TAB>Verse text", no HTML, no study notes at all -- BSB is a
plain translation, not a study bible, so unlike NET/NIV/SBL/NOAB/Ignatius there is nothing here for
build_notes_shards.py to extract. This script only builds the translation-TEXT stream, in the same
{book_id: [[verse_text, ...], ...]} schema build_net_niv_text_streams.py already proved out (confirmed
by reading that script before writing this one, not re-deriving the schema from scratch).

Book-name mapping, checked rather than assumed: extracted the 66 distinct book names from the file in
their first-appearance order and confirmed by eye they are already in standard canonical order
(Genesis...Revelation) with exactly one entry per STANDARD_66_BOOK_ORDER id -- so name->id is a
positional zip, not a hand-written lookup table that could silently drift from the file's real names
(e.g. this file says "Psalm" singular and "Song of Solomon", not "Psalms"/"Song of Songs").
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_notes_shards import STANDARD_66_BOOK_ORDER  # noqa: E402

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, 'sources_cache')
os.makedirs(CACHE_DIR, exist_ok=True)
BSB_SRC_PATH = r"C:\Users\Elation\Downloads\bsb.txt"
BSB_OUT_PATH = os.path.join(CACHE_DIR, 'BSB.json')

REF_RE = re.compile(r'^(.*?)\s+(\d+):(\d+)$')


def _book_name_order():
    """Ground-truth the file's own book order before trusting the positional zip (Rule 3)."""
    names = []
    seen = set()
    with io.open(BSB_SRC_PATH, encoding='utf-8-sig') as f:
        for line in f:
            line = line.rstrip('\n')
            if '\t' not in line:
                continue
            left = line.split('\t', 1)[0]
            m = REF_RE.match(left)
            if not m:
                continue
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                names.append(name)
    return names


def extract_bsb_full_bible_text():
    names_in_order = _book_name_order()
    if len(names_in_order) != 66:
        raise RuntimeError(
            f"Expected 66 distinct book names in bsb.txt, found {len(names_in_order)}: "
            f"{names_in_order} -- mapping aborted rather than guessed."
        )
    name_to_id = dict(zip(names_in_order, STANDARD_66_BOOK_ORDER))

    per_book_verses = {}  # book_id -> {(chap, verse): text}
    total_lines = 0
    with io.open(BSB_SRC_PATH, encoding='utf-8-sig') as f:
        for line in f:
            line = line.rstrip('\n')
            if '\t' not in line:
                continue
            left, text = line.split('\t', 1)
            m = REF_RE.match(left)
            if not m:
                continue
            name, chap, verse = m.group(1), int(m.group(2)), int(m.group(3))
            book_id = name_to_id.get(name)
            if not book_id:
                continue
            total_lines += 1
            per_book_verses.setdefault(book_id, {})[(chap, verse)] = text.strip()

    out = {}
    for book_id, verses in per_book_verses.items():
        max_chap = max(c for c, v in verses)
        chapters = []
        for c in range(1, max_chap + 1):
            vnums = [v for (cc, v) in verses if cc == c]
            if not vnums:
                chapters.append([])
                continue
            max_v = max(vnums)
            chapters.append([verses.get((c, v), '') for v in range(1, max_v + 1)])
        out[book_id] = chapters
    return out, total_lines


def main():
    print('Extracting Berean Standard Bible (BSB) full-Bible verse text...')
    books, total_lines = extract_bsb_full_bible_text()
    verse_total = sum(len(ch) for chs in books.values() for ch in chs)
    with open(BSB_OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False)
    print(f'  {len(books)} books, {verse_total} verse slots ({total_lines} source lines) -> {BSB_OUT_PATH}')
    # Ground-truth spot check (Rule 3): Genesis 1:1 and John 1:1 must be real text, not empty.
    assert books['gen'][0][0], "Genesis 1:1 came back empty"
    assert books['john'][0][0], "John 1:1 came back empty"
    print(f"  Spot check -- Gen 1:1: {books['gen'][0][0]!r}")
    print(f"  Spot check -- John 1:1: {books['john'][0][0]!r}")


if __name__ == '__main__':
    main()
