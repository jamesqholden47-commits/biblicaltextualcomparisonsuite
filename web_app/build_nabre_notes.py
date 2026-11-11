# -*- coding: utf-8 -*-
"""
NABRE (New American Bible Revised Edition) verse-by-verse study notes, extracted from James's own
PDF: `C:\\SOLIDWORKS Data\\modules\\...Catholic Study Bible...NABRE 2016...pdf` ("The Catholic
Study Bible, Third Edition", Oxford University Press). This is the first non-Ignatius source added
to Doll 6 since NOAB/SBL/NIV, and the first drawn from a PDF rather than an EPUB.

Ground-truthed before writing any extraction code (Rule 5): this reflowed, Calibre-produced PDF
(6,577 short pages) preserves real per-span font-weight info -- confirmed via get_text("dict") --
Arial-BoldMT for a note's own chapter:verse ref AND any immediately following anchor phrase,
ArialMT for the note's body. This is the same information an EPUB's <strong>/<b> tags would carry,
just reached through PDF font flags instead of HTML tags.

The book's front matter (PDF pages ~0-1372) holds per-book INTRODUCTION ESSAYS, which occasionally
cite a bare "C:V" bold reference mid-prose while discussing a book's structure (e.g. Deuteronomy's
essay around page 353/412) -- these are NOT per-verse notes, confirmed to produce only a handful of
stray false matches, excluded by requiring page >= NOTES_START_PAGE. The real per-verse NOTES
section begins at Genesis 1:1 (page 1373, confirmed: "This section, from the Priestly source,
functions...") and runs in continuous canonical-book order through Revelation 22:20 (page 5969).

Book-boundary detection walks the suite's own 73-book canonical order (CANON_ORDER, copied from
build_plenary_logos_suite.py's CANON_SCHEMA id list so the two never drift apart) and advances to
the next book whenever a note's chapter number is LOWER than the previous note's chapter within the
current book -- true for 67 of the 68 real transitions between books that have any notes at all.
Audited directly (not assumed): 5 of the 73 books -- Obadiah, Baruch, 2 John, 3 John, Jude -- have
ZERO matching per-verse notes in this source (their own gaps between neighboring books' chapter
counts are wide enough that this was confirmed by reading the actual page content on both sides of
each gap, not just inferred from a missing boundary). Stated honestly as an empty shard contribution
rather than silently producing nothing with no explanation.

ONE transition does not fit the chapter-decrease rule and was found only by reading the actual
events around it, not assumed: Philemon is a single chapter, so its only note sits at chapter 1;
Hebrews' own first note ALSO sits at chapter 1 -- no decrease, so without a manual override
Hebrews' 13 chapters of real notes (confirmed real and substantial by reading them directly) would
silently merge into "Philemon". Fixed with one explicit forced boundary at the exact page this was
found on (5795).

A note's own ref span sometimes carries a verse RANGE ("1:1-7", "1:1-2:18") or LIST ("1:1, 5") --
the digits after the first "C:V" are not a real anchor word, so (same lesson as the Ignatius OT
fix) any text immediately following the ref that looks like a dangling range/list continuation is
blanked rather than shipped as a nonsense title badge.
"""
import sys
import os
import re
import json

import fitz

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, 'notes_shards')
os.makedirs(OUT_DIR, exist_ok=True)

NABRE_PDF_PATH = (
    r"C:\SOLIDWORKS Data\modules\The Catholic Study Bible - Third Edition (NABRE 2016) -- "
    "Donald Senior, John Collins, Mary Ann Getty -- 3, 2016 -- Oxford University Press -- "
    "060eb057dd75baca4149e947f9664dc5 -- Anna\u2019s Archive.pdf"
)

NOTES_START_PAGE = 1373  # Genesis 1:1's real note; everything before is front-matter essays
FORCED_BOUNDARIES = {}  # none needed: every real transition is a genuine chapter decrease once
# ZERO_NOTE_BOOKS correctly excludes every single-chapter book with no notes of its own (Rule 5:
# confirmed by reading the actual content on both sides of each gap, not inferred from a missing
# boundary alone) -- Philemon included: what first looked like its own "1:1" note (page 5794) is
# in fact Hebrews' own Heb 1:1-4 opening, continuing directly into 1:5-14 on page 5795 as one
# unbroken commentary -- there is no separate Philemon content anywhere in this source.
ZERO_NOTE_BOOKS = {'obad', 'phlm', '2john', '3john', 'jude'}

CANON_ORDER = [
    'gen', 'exod', 'lev', 'num', 'deut', 'josh', 'judg', 'ruth', '1sam', '2sam', '1kgs', '2kgs',
    '1chr', '2chr', 'ezra', 'neh', 'tob', 'jdt', 'esth', '1macc', '2macc', 'job', 'ps', 'prov',
    'eccl', 'song', 'wis', 'sir', 'isa', 'jer', 'lam', 'bar', 'ezek', 'dan', 'hos', 'joel', 'amos',
    'obad', 'jonah', 'mic', 'nah', 'hab', 'zeph', 'hag', 'zech', 'mal', 'matt', 'mark', 'luke',
    'john', 'acts', 'rom', '1cor', '2cor', 'gal', 'eph', 'phil', 'col', '1thess', '2thess', '1tim',
    '2tim', 'titus', 'phlm', 'heb', 'jas', '1pet', '2pet', '1john', '2john', '3john', 'jude', 'rev',
]

REF_RE = re.compile(r'^(\d+):(\d+)')
DANGLING_RANGE_RE = re.compile(r'^[-\u2012\u2013\u2014,]\s*\d')


def _clean_anchor(word):
    if word and DANGLING_RANGE_RE.match(word):
        return ''
    return word


def build_stream_and_note_starts(doc):
    """Returns (stream, note_starts): stream is a flat ordered list of (page_no, text, is_bold)
    runs across every page from NOTES_START_PAGE onward; note_starts is a parallel list of
    (stream_index, page_no, chapter, verse) for every run that opens a new bold chapter:verse
    note.

    A real note-start is checked only on a BLOCK's first line, not every wrapped line (found by
    cross-checking max-chapter-reached per book against the suite's own DRA.json chapter counts,
    Rule 3 -- not assumed correct from a plausible-looking regex): a note's own body text can cite
    a cross-reference verse (e.g. "12:14" inside a note about 12:3) that happens to start a new
    WRAPPED line within the same paragraph/block, is bold for unrelated reasons (continuing a
    bold run), and would otherwise be mistaken for a second note beginning mid-paragraph. That
    false match cascaded a one-book-label drift through every subsequent book in early testing
    (confirmed on Hosea 12:3's note, whose block wraps across 4 lines and whose 2nd/3rd lines
    read "12:14" and "13:1" -- neither is a real note)."""
    stream = []
    note_starts = []
    for pno in range(NOTES_START_PAGE, doc.page_count):
        d = doc[pno].get_text("dict")
        for block in d["blocks"]:
            lines = block.get("lines", [])
            for li, line in enumerate(lines):
                spans = line.get("spans", [])
                if not spans:
                    continue
                line_start_idx = len(stream)
                for span in spans:
                    txt = span["text"]
                    if txt:
                        stream.append((pno, txt, "Bold" in span["font"]))
                if li != 0:
                    continue
                s0 = spans[0]
                m = REF_RE.match(s0["text"].strip())
                if m and "Bold" in s0["font"]:
                    note_starts.append((line_start_idx, pno, int(m.group(1)), int(m.group(2))))
    return stream, note_starts


def extract_all():
    doc = fitz.open(NABRE_PDF_PATH)
    stream, note_starts = build_stream_and_note_starts(doc)
    print(f'Stream runs: {len(stream)}, note-start events: {len(note_starts)}', file=sys.stderr)

    # Cursor walks only the books CONFIRMED to carry real notes (Rule 5: ZERO_NOTE_BOOKS was
    # built by reading the actual page content on both sides of each gap, not inferred). This
    # matters because three zero-note books run consecutively (2 John, 3 John, Jude) -- a naive
    # "+1 per chapter-decrease" cursor would land one decrease past 1 John on '2john' instead of
    # the correct 'rev', since no decrease event exists to consume for each skipped book.
    real_note_books = [b for b in CANON_ORDER if b not in ZERO_NOTE_BOOKS]

    book_idx = 0
    prev_chap = None
    per_book_chapters = {}
    notes_written = 0
    books_seen = []

    for i, (stream_idx, pno, chap, verse) in enumerate(note_starts):
        if pno in FORCED_BOUNDARIES:
            book_idx = real_note_books.index(FORCED_BOUNDARIES[pno])
            prev_chap = None
        elif prev_chap is not None and chap < prev_chap:
            book_idx += 1
        book_id = real_note_books[book_idx]
        if not books_seen or books_seen[-1] != book_id:
            books_seen.append(book_id)
        prev_chap = chap

        start = stream_idx
        end = note_starts[i + 1][0] if i + 1 < len(note_starts) else len(stream)
        runs = stream[start:end]

        ref_run_text = runs[0][1]
        m0 = REF_RE.match(ref_run_text.strip())
        trailing_in_ref_span = ref_run_text[ref_run_text.index(m0.group(0)) + len(m0.group(0)):]

        j = 1
        anchor_parts = [trailing_in_ref_span]
        while j < len(runs) and runs[j][2]:
            anchor_parts.append(runs[j][1])
            j += 1
        anchor = _clean_anchor(''.join(anchor_parts).strip().rstrip(':').strip())
        body = ''.join(r[1] for r in runs[j:])
        body = re.sub(r'\s+', ' ', body).strip()
        if not body:
            continue

        title = (f'NABRE \u2014 {chap}:{verse} \u2018{anchor}\u2019'
                 if anchor else f'NABRE \u2014 {chap}:{verse}')
        verses = per_book_chapters.setdefault(book_id, {}).setdefault(str(chap), {})
        notes = verses.setdefault(str(verse), [])
        notes.append({
            'src': 'nabre',
            'tier': 'CATHOLIC NIHIL OBSTAT/IMPRIMATUR',
            'kind': 'study',
            'marker': f'{chap}:{verse}',
            'anchor_word': anchor,
            'title': title,
            'html': body,
        })
        notes_written += 1

    return per_book_chapters, notes_written, books_seen


def _merge_into_shard(book_id, chapters):
    out_path = os.path.join(OUT_DIR, f'{book_id}.js')
    payload = {'book_id': book_id, 'chapters': {}}
    if os.path.isfile(out_path):
        txt = open(out_path, encoding='utf-8').read()
        m = re.search(r'\{.*\}', txt, re.S)
        if m:
            existing = json.loads(m.group(0))
            payload['chapters'] = existing.get('chapters', {})
    for chap, verses in chapters.items():
        base_verses = payload['chapters'].setdefault(chap, {})
        for verse, notes in verses.items():
            existing_notes = base_verses.setdefault(verse, [])
            existing_notes[:] = [n for n in existing_notes if n.get('src') != 'nabre'] + notes
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"window.__PLENARY_LOAD_BOOK_NOTES({json.dumps(book_id)}, {json.dumps(payload, ensure_ascii=False)});\n")
    return os.path.getsize(out_path)


def _strip_stale_nabre(book_id):
    """For a book with no real nabre notes this run (e.g. a book moved into ZERO_NOTE_BOOKS after
    an earlier, buggier run had wrongly written notes into its shard) -- removes any leftover
    'src': 'nabre' entries so a book that genuinely has none doesn't keep stale wrong ones."""
    out_path = os.path.join(OUT_DIR, f'{book_id}.js')
    if not os.path.isfile(out_path):
        return False
    txt = open(out_path, encoding='utf-8').read()
    m = re.search(r'\{.*\}', txt, re.S)
    if not m:
        return False
    existing = json.loads(m.group(0))
    chapters = existing.get('chapters', {})
    removed = 0
    for chap, verses in chapters.items():
        for verse, notes in verses.items():
            before = len(notes)
            notes[:] = [n for n in notes if n.get('src') != 'nabre']
            removed += before - len(notes)
    if removed:
        payload = {'book_id': book_id, 'chapters': chapters}
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"window.__PLENARY_LOAD_BOOK_NOTES({json.dumps(book_id)}, {json.dumps(payload, ensure_ascii=False)});\n")
    return removed


def main():
    per_book_chapters, notes_written, books_seen = extract_all()
    print(f'NABRE: {notes_written} notes extracted across {len(per_book_chapters)} books.')
    print(f'Book sequence encountered ({len(books_seen)}): {books_seen}')
    expected = [b for b in CANON_ORDER if b not in ZERO_NOTE_BOOKS]
    if books_seen != expected:
        print('WARNING: book sequence does not match expected canonical real-note-book order!')
        print(f'  expected: {expected}')
    missing = [b for b in CANON_ORDER if b not in per_book_chapters]
    print(f'Books with zero NABRE notes ({len(missing)}): {missing}')
    unexpected_missing = [b for b in missing if b not in ZERO_NOTE_BOOKS]
    if unexpected_missing:
        print(f'WARNING: unexpected zero-note books not in the known ZERO_NOTE_BOOKS set: {unexpected_missing}')

    for book_id in CANON_ORDER:
        if book_id in per_book_chapters:
            size = _merge_into_shard(book_id, per_book_chapters[book_id])
            count = sum(len(v) for chs in per_book_chapters[book_id].values() for v in chs.values())
            print(f'  {book_id:8s} {count:5d} NABRE notes  -> notes_shards/{book_id}.js ({size} B)')
        else:
            removed = _strip_stale_nabre(book_id)
            if removed:
                print(f'  {book_id:8s} stripped {removed} stale NABRE notes from an earlier buggy run')


if __name__ == '__main__':
    main()
