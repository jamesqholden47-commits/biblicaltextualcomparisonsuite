# -*- coding: utf-8 -*-
"""
Builds web_app/notes_shards/<book_id>.js — one file://-safe JSONP shard per book, each calling
window.__PLENARY_LOAD_BOOK_NOTES(book_id, {book_id, chapters}) so the lazy loader added to
logos_suite_template.html in Pass 2 (Feature A) has real data to load with LRU eviction.

Pass 2 scope (per James's 4-pass handoff relay, 2026-11-10): NET Bible 2.1 tn/tc/sn notes AND
Ignatius Catholic Study Bible NT commentary, across the 27 New Testament books. BSB is the third
Pass 2 target named in the handoff; BSB (Downloads\\bsb.txt) carries verse TEXT only (the handoff
itself notes no footnote/interlinear table exists for it yet), so it is out of scope for a *notes*
shard builder and is left for the translation-registry work in build_plenary_logos_suite.py.

Ignatius NT source note (added in a follow-up pass to the initial NET-only version of this file):
the EPUB's commentary is NOT keyed by the same `<sup>`/`filepos` footnote-marker system used for
its sparser word-study callouts — ground-truthed before writing the parser, not assumed from the
handoff's description. The real per-verse commentary (6,478 notes total, census-counted before any
extraction code was written) lives in each book's "Commentary on ..." section as one <p><b>REF</b>
TEXT...</p> per note, REF being a chapter:verse (or verse-range) reference, e.g. "<b>1:1 In the
beginning:</b> John traces...". A REF is sometimes prefixed with another book's abbreviation
("Mk 1:1:") when a note is a synoptic cross-reference parked inside a different book's commentary
section — those notes are routed to the book the reference actually names, not the book whose
section physically contains them (audited: 28 distinct abbreviation spellings in use, all mapped).
Section headers with no verse (book intros: "Author", "Date", "Word Study", "Themes and
Characteristics", etc.) are skipped here — they belong to a future book_intros.js drawer, not a
per-verse note, and are not silently merged into verse 1's notes to avoid misattributing them.

Verified schema (ground-truth checked against the live epub before writing this, not assumed):
  - OEBPS/fileN.xhtml (1255 of them) hold the running Scripture text. Verse boundaries are marked
    inline as <span class="verse">C:V</span> — this is the chapter:verse of record, independent of
    which physical file/heading the text sits under (files do not split exactly on chapter lines).
  - Each verse's footnote markers are <sup><a id="nXXXXX" href="fileN_notes.xhtml#nXXXXX">NUM</a></sup>.
  - OEBPS/fileN_notes.xhtml holds the matching notes: <p id="nXXXXX"><a href="...">NUM</a>
    <p><b>KIND</b> HTML...</p></p> where KIND is one of tn (translator note), tc (text-critical
    note), or sn (study note). Audited across all 1255 notes files: 60,595 note ids, 60,595 matched
    by the <b>KIND</b> extraction regex, 0 unmatched (tn 48,886 / tc 2,736 / sn 8,973) — the schema
    is template-generated and fully consistent, not a sampled guess.
  - OEBPS/toc.ncx navMap gives book -> starting file; OEBPS/content.opf spine gives the full
    ordered file sequence, so a book's file range is [its navPoint's file, the next navPoint's
    file). Used instead of trying to parse book names out of chapter titles for every file.
"""
import html as html_mod
import json
import os
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, 'notes_shards')
os.makedirs(OUT_DIR, exist_ok=True)

NET_EPUB_PATH = r"C:\Users\Elation\Downloads\NETBIBLE21.epub"

# NET Bible 2.1 navMap book label -> this project's canonical book id (verified against
# plenary_logos_data.json's 73-book list). Only the 3 NT labels that don't match the project's
# `name` field verbatim need remapping; every other NT/OT label is identical and included anyway
# so this table is reusable, untouched, for the OT ingestion pass later.
NET_LABEL_TO_BOOK_ID = {
    'Genesis': 'gen', 'Exodus': 'exod', 'Leviticus': 'lev', 'Numbers': 'num', 'Deuteronomy': 'deut',
    'Joshua': 'josh', 'Judges': 'judg', 'Ruth': 'ruth', '1 Samuel': '1sam', '2 Samuel': '2sam',
    '1 Kings': '1kgs', '2 Kings': '2kgs', '1 Chronicles': '1chr', '2 Chronicles': '2chr',
    'Ezra': 'ezra', 'Nehemiah': 'neh', 'Esther': 'esth', 'Job': 'job', 'Psalms': 'ps',
    'Proverbs': 'prov', 'Ecclesiastes': 'eccl', 'Song of Solomon': 'song', 'Isaiah': 'isa',
    'Jeremiah': 'jer', 'Lamentations': 'lam', 'Ezekiel': 'ezek', 'Daniel': 'dan', 'Hosea': 'hos',
    'Joel': 'joel', 'Amos': 'amos', 'Obadiah': 'obad', 'Jonah': 'jonah', 'Micah': 'mic',
    'Nahum': 'nah', 'Habakkuk': 'hab', 'Zephaniah': 'zeph', 'Haggai': 'hag', 'Zechariah': 'zech',
    'Malachi': 'mal',
    'Matthew': 'matt', 'Mark': 'mark', 'Luke': 'luke', 'John': 'john', 'Acts': 'acts',
    'Romans': 'rom', '1 Corinthians': '1cor', '2 Corinthians': '2cor', 'Galatians': 'gal',
    'Ephesians': 'eph', 'Philippians': 'phil', 'Colossians': 'col', '1 Thessalonians': '1thess',
    '2 Thessalonians': '2thess', '1 Timothy': '1tim', '2 Timothy': '2tim', 'Titus': 'titus',
    'Philemon': 'phlm', 'Hebrews': 'heb', 'James': 'jas', '1 Peter': '1pet', '2 Peter': '2pet',
    '1 John': '1john', '2 John': '2john', '3 John': '3john', 'Jude': 'jude', 'Revelation': 'rev',
}
NT_BOOK_IDS = {
    'matt', 'mark', 'luke', 'john', 'acts', 'rom', '1cor', '2cor', 'gal', 'eph', 'phil', 'col',
    '1thess', '2thess', '1tim', '2tim', 'titus', 'phlm', 'heb', 'jas', '1pet', '2pet', '1john',
    '2john', '3john', 'jude', 'rev',
}

VERSE_OR_NOTE_RE = re.compile(r'<span class="verse">(?P<verse>\d+:\d+)</span>|<a id="(?P<note>n\d+)"')
NOTE_BODY_RE = re.compile(r'<p id="(n\d+)">(.*?)</p>\s*</p>', re.S)
KIND_RE = re.compile(r'<b>([a-z]+)</b>\s*(.*)', re.S)
KIND_LABEL = {'tn': 'Translator Note', 'tc': 'Text-Critical Note', 'sn': 'Study Note'}


def load_net_book_file_ranges(zf):
    """Returns ordered [(book_id, [file_names_in_order]), ...] for every NET navMap book."""
    opf = zf.read('OEBPS/content.opf').decode('utf-8', 'ignore')
    spine_ids = re.findall(r'<itemref idref="(.*?)"', opf)
    manifest = dict(re.findall(r'<item id="([^"]+)" href="([^"]+)"', opf))
    spine_files = [manifest[s] for s in spine_ids if manifest.get(s) and re.match(r'file\d+\.xhtml$', manifest[s])]

    ncx = zf.read('OEBPS/toc.ncx').decode('utf-8', 'ignore')
    navs = re.findall(
        r'<navPoint[^>]*>\s*<navLabel>\s*<text>(.*?)</text>\s*</navLabel>\s*<content src="(.*?)"\s*/>',
        ncx, re.S,
    )
    book_navs = [(label, src) for label, src in navs if label in NET_LABEL_TO_BOOK_ID]
    if len(book_navs) != len(NET_LABEL_TO_BOOK_ID):
        missing = set(NET_LABEL_TO_BOOK_ID) - {label for label, _ in book_navs}
        raise AssertionError(f'NET navMap label set changed — missing: {missing}')

    file_index = {f: i for i, f in enumerate(spine_files)}
    ranges = []
    for i, (label, src) in enumerate(book_navs):
        start = file_index[src]
        end = file_index[book_navs[i + 1][1]] if i + 1 < len(book_navs) else len(spine_files)
        ranges.append((NET_LABEL_TO_BOOK_ID[label], spine_files[start:end]))
    return ranges


def extract_net_notes_for_book(zf, chapter_files):
    """Returns {chapter_num: {verse_num: [note_dict, ...]}} for one book's chapter files, in order."""
    chapters = {}
    last_ref = None  # (chap, verse) carried across this book's own files only
    for fname in chapter_files:
        ch_html = zf.read(f'OEBPS/{fname}').decode('utf-8', 'ignore')
        notes_fname = fname.replace('.xhtml', '_notes.xhtml')
        notes_path = f'OEBPS/{notes_fname}'
        note_bodies = {}
        if notes_path in zf.namelist():
            notes_html = zf.read(notes_path).decode('utf-8', 'ignore')
            for note_id, body in NOTE_BODY_RE.findall(notes_html):
                note_bodies[note_id] = body

        prev_end = 0
        for m in VERSE_OR_NOTE_RE.finditer(ch_html):
            if m.group('verse'):
                chap_s, verse_s = m.group('verse').split(':')
                last_ref = (int(chap_s), int(verse_s))
                prev_end = m.end()
                continue
            note_id = m.group('note')
            # The anchor word James asked for: the real English word NET's own <sup> marker sits
            # directly after in the primary text, not a synthetic label of our own invention. Taken
            # from the running text between the previous marker/verse-span and this <a id=...>, with
            # tags/entities stripped, keeping the last word token (NET wraps the marker right after
            # the word it foots, e.g. "Then<sup><a id=...>51</a></sup> Jesus...").
            preceding_raw = ch_html[prev_end:m.start()]
            preceding_text = html_mod.unescape(re.sub(r'<[^>]+>', '', preceding_raw)).strip()
            # Allow trailing punctuation between the word and the marker (NET commonly foots a word
            # that is itself followed by a comma/period before the <sup>, e.g. "with God,<sup>...").
            word_match = re.search(r'([A-Za-zÀ-ɏ‘’\'—-]+)[\s,;:.!?)\]"’”]*$', preceding_text)
            anchor_word = word_match.group(1).strip('‘’\'') if word_match else ''
            prev_end = m.end()
            if last_ref is None or note_id not in note_bodies:
                continue  # no verse context yet, or marker had no matching note body (none observed in audit)
            body = note_bodies[note_id]
            # Strip the leading "<a href=...>NUM</a> " backlink the note body opens with.
            body = re.sub(r'^\s*<a\b[^>]*>.*?</a>\s*', '', body, count=1, flags=re.S)
            km = KIND_RE.search(body)
            kind = km.group(1) if km else 'sn'
            html = (km.group(2) if km else body).strip()
            chap, verse = last_ref
            title = f'NET {KIND_LABEL.get(kind, "Note")} — ‘{anchor_word}’' if anchor_word else f'NET {KIND_LABEL.get(kind, "Note")}'
            chapters.setdefault(str(chap), {}).setdefault(str(verse), []).append({
                'src': 'net21',
                'tier': 'PROTESTANT/CRITICAL',
                'kind': kind,
                'marker': note_id,
                'anchor_word': anchor_word,
                'title': title,
                'html': html,
            })
    return chapters


IGNATIUS_NT_EPUB_PATH = (
    r"C:\Users\Elation\PDFS\01_Biblical_Studies_and_Canon"
    r"\_AA_ Curtis Mitch & Scott Hahn - Ignatius Catholic Study Bible New Testament (2009).epub"
)

# Abbreviation spellings actually in use for cross-referenced notes ("Mk 1:1:" parked inside a
# different book's own Commentary section) — audited across all 27 books' commentary text before
# writing this table; every spelling that appeared is mapped, none guessed.
IGNATIUS_REF_PREFIX_TO_BOOK_ID = {
    'Mt': 'matt', 'Mk': 'mark', 'Lk': 'luke', 'Jn': 'john', 'Acts': 'acts', 'Rom': 'rom',
    '1 Cor': '1cor', '2 Cor': '2cor', 'Gal': 'gal', 'Eph': 'eph', 'Phil': 'phil', 'Col': 'col',
    '1 Thess': '1thess', '2 Thess': '2thess', '1 Tim': '1tim', '2 Tim': '2tim', 'Tit': 'titus',
    'Philem': 'phlm', 'Heb': 'heb', 'Jas': 'jas', '1 Pet': '1pet', '1 Peter': '1pet', '2 Pet': '2pet',
    '1 Jn': '1john', '2 Jn': '2john', '3 Jn': '3john', 'Jude': 'jude', 'Rev': 'rev',
}

NOTE_PARA_RE = re.compile(r'<p[^>]*>(?:<[^>]+>)*<b>([^<]{1,40})</b>(.*?)</p>', re.S)
IGNATIUS_REF_RE = re.compile(r'^(?:([1-3]?\s?[A-Za-z]+\.?)\s+)?(\d+):(\d+)(?:-\d+(?::\d+)?)?')
BACK_TO_TEXT_RE = re.compile(r'\s*<a\b[^>]*>\s*<span>\s*<span>\s*Back to text\.\s*</span>\s*</span>\s*</a>\s*$', re.S)
# Every other <a href="#filepos...">...</a> in a note body is an intra-epub cross-reference link
# (e.g. "Gen 1:1; 1 Jn 1:1; ...") — a dead link once extracted out of the original single-page
# epub's own DOM (the filepos ids it points at do not exist in the standalone shard file), so the
# anchor text is kept but the <a>/</a> wrapper is dropped rather than shipping a href to nowhere.
DEAD_INTERNAL_LINK_RE = re.compile(r'<a\b[^>]*href="#filepos\d+"[^>]*>(.*?)</a>', re.S)

# Hahn/Mitch's own inline lemma convention: within ONE <p> note, additional phrases from the same
# verse each get their own bolded "<b>phrase:</b>" header before their gloss (sample, real text:
# "<b>1:1 In the beginning:</b> John traces the origin... <b>was with God:</b> Distinguishes the
# Word... <b>was God:</b> Or, 'was divine'..."). These are the actual per-word/phrase indicators
# the primary material uses — not something invented here — so each one is split into its own note
# rather than left buried inside a single paragraph under only the first phrase's heading.
SUBGLOSS_RE = re.compile(r'<b>([^<]{1,60}):</b>')


def split_ignatius_subglosses(html_body):
    """Splits a cleaned note body on its own internal <b>phrase:</b> sub-headers. Returns
    [(label_or_None, text), ...] — label is None for the lead-in text before the first sub-header
    (it belongs to the note's own opening phrase, handled by the caller), a string for every
    phrase Hahn/Mitch bolded after that. Empty chunks (a sub-header with no following text, rare)
    are dropped rather than emitted as a blank note."""
    parts = SUBGLOSS_RE.split(html_body)
    chunks = [(None, parts[0].strip())]
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        text = parts[i + 1].strip() if i + 1 < len(parts) else ''
        chunks.append((label, text))
    return [(label, text) for label, text in chunks if text]


def _ignatius_pos_after(raw, filepos_id):
    """Position right after the closing '>' of the tag carrying id="filepos_id", or -1 if absent."""
    p = raw.find(f'id="{filepos_id}"')
    if p < 0:
        return -1
    gt = raw.find('>', p)
    return (gt + 1) if gt >= 0 else -1


def load_ignatius_nt_book_sections(raw):
    """Returns ordered [(book_id, text_start, commentary_start), ...] using the EPUB's own
    'THE NEW TESTAMENT' TOC block (Text/Commentary filepos anchors per book) — the same technique
    already proven out in parse_ignatius_rsv2ce.py for this exact file, reused here rather than
    re-deriving a second, possibly-inconsistent way of slicing the same 27 books."""
    toc_start = raw.find('THE NEW TESTAMENT')
    toc_chunk = raw[toc_start:toc_start + 22000]
    blocks = re.findall(r'<b>([^<]{8,80})</b></p>(.*?)(?=<b>(?:The |Index )|</p>\s*<div>|$)', toc_chunk, re.S)
    nt_ids = [
        'matt', 'mark', 'luke', 'john', 'acts', 'rom', '1cor', '2cor', 'gal', 'eph',
        'phil', 'col', '1thess', '2thess', '1tim', '2tim', 'titus', 'phlm', 'heb',
        'jas', '1pet', '2pet', '1john', '2john', '3john', 'jude', 'rev',
    ]
    book_slices = []
    for title, rest in blocks:
        m_t = re.search(r'<a href="#(filepos\d+)"><i><span><span>Text</span></span></i></a>', rest)
        m_c = re.search(r'<a href="#(filepos\d+)"><i><span><span>Commentary</span></span></i></a>', rest)
        if m_t and m_c:
            book_slices.append((m_t.group(1), m_c.group(1)))
    if len(book_slices) != len(nt_ids):
        raise AssertionError(f'Ignatius NT TOC changed shape: expected {len(nt_ids)} books, found {len(book_slices)}')
    return [(bid, t_id, c_id) for bid, (t_id, c_id) in zip(nt_ids, book_slices)]


def extract_ignatius_nt_notes(raw):
    """Returns {book_id: {chapter: {verse: [note_dict, ...]}}}, plus (paragraphs_kept,
    notes_after_split, skipped_non_verse, skipped_unknown_prefix) counts for the ground-truth
    check in main(). Cross-book refs are routed to the book they name. One source <p> commonly
    yields more than one note (see split_ignatius_subglosses) \u2014 paragraphs_kept is the figure that
    cross-checks against the independent raw-file anchor count; notes_after_split is the real
    total written to the shards."""
    sections = load_ignatius_nt_book_sections(raw)
    out = {}
    paragraphs_kept = 0
    notes_after_split = 0
    skipped_non_verse = 0
    skipped_unknown_prefix = 0
    for i, (book_id, t_id, c_id) in enumerate(sections):
        c_start = _ignatius_pos_after(raw, c_id)
        c_end = _ignatius_pos_after(raw, sections[i + 1][1]) if i + 1 < len(sections) else len(raw)
        c_end_adj = raw.rfind('<', c_start, c_end + 1) if c_end > c_start else c_end
        section = raw[c_start:c_end_adj]

        for ref_text, body in NOTE_PARA_RE.findall(section):
            rm = IGNATIUS_REF_RE.match(ref_text.strip())
            if not rm:
                skipped_non_verse += 1
                continue
            prefix, chap_s, verse_s = rm.groups()
            if prefix:
                prefix = prefix.strip().rstrip('.')
                target_book = IGNATIUS_REF_PREFIX_TO_BOOK_ID.get(prefix)
                if target_book is None:
                    skipped_unknown_prefix += 1
                    continue
            else:
                target_book = book_id
            # The real anchor phrase Hahn/Mitch printed after the verse number itself, e.g. "1:1 In
            # the beginning:" -> "In the beginning" \u2014 this is the lead note's own indicator text,
            # parallel to each later sub-header split_ignatius_subglosses() finds in the body.
            main_anchor = ref_text.strip()[rm.end():].strip().rstrip(':').strip()
            paragraphs_kept += 1

            html = BACK_TO_TEXT_RE.sub('', body).strip()
            html = DEAD_INTERNAL_LINK_RE.sub(r'\1', html)
            html = re.sub(r'<img\b[^>]*/?>', '', html)
            html = re.sub(r'<a\b[^>]*>\s*</a>', '', html)

            chapters = out.setdefault(target_book, {})
            verses = chapters.setdefault(str(int(chap_s)), {})
            notes = verses.setdefault(str(int(verse_s)), [])
            for sub_label, sub_text in split_ignatius_subglosses(html):
                anchor_word = sub_label if sub_label is not None else main_anchor
                if anchor_word:
                    title = f'Ignatius CSB \u2014 {chap_s}:{verse_s} \u2018{anchor_word}\u2019'
                else:
                    title = f'Ignatius CSB \u2014 {ref_text.strip()}'
                if prefix:
                    title += f' (cross-ref from {book_id})'
                notes.append({
                    'src': 'ignatius',
                    'tier': 'CATHOLIC IMPRIMATUR',
                    'kind': 'study',
                    'marker': ref_text.strip() + (f' / {sub_label}' if sub_label else ''),
                    'anchor_word': anchor_word,
                    'title': title,
                    'html': sub_text,
                })
                notes_after_split += 1
    return out, paragraphs_kept, notes_after_split, skipped_non_verse, skipped_unknown_prefix


SBL_EPUB_PATH = (
    r"C:\Users\Elation\Downloads\The SBL Study Bible_ Fully Revised and Updated by the -- "
    r"Society of Biblical Literature -- 1, 2023 -- HarperCollins -- "
    "011d7f89ac0cbc703cb0c8755dd6b73b -- Anna" + "\u2019" + "s Archive.epub"
)

# Ground-truthed against the live epub before writing any extraction logic (Rule 5): commentary
# entries are <span class="bcv" id="comBBCCCVVV[a-z]?">...</span> immediately followed, where the
# note glosses a specific word, by the SBL editors' own <i>lemma</i> markup (same convention as
# Ignatius's bolded phrases) — e.g. com43001001a is followed by "<i>In the beginning</i>. See Gen
# 1.1...". BB/CCC/VVV is the book/chapter/verse encoded directly in the id itself (standard 66-book
# numbering, confirmed against 3 known cross-reference links in the live text: book 43 = John,
# book 62 = 1 John, book 20 = Proverbs — all matched before trusting the table below). Census before
# writing the parser: 19,910 total <span class="bcv"> commentary entries across the whole Bible,
# 5,873 of them in the 27 NT books (40-66) this extractor targets, matching this project's existing
# NT-only scope for NET/Ignatius. Books 67+ (Deuterocanon, numbered past the standard 66 in this
# source) remains out of scope (its own numbering, not yet mapped) — but the 1-39 OT books use the
# same standard numbering as the NT and are included: NOAB/SBL/NIV's note systems turned out to be
# testament-agnostic once the NT-only filter was lifted, unlike Ignatius OT's per-book hand-parsing
# (see the Rule 12 ledger entry for why those two situations differ).
SBL_COM_SPAN_RE = re.compile(r'<span class="bcv" id="com(\d{2})(\d{3})(\d{3})([a-z]?)">.*?</span>', re.S)
SBL_LEMMA_RE = re.compile(r'^\s*<i>([^<]{1,80})</i>')
SBL_XBR_LINK_RE = re.compile(r'<a class="xbr"[^>]*>(.*?)</a>', re.S)

STANDARD_66_BOOK_ORDER = [
    'gen', 'exod', 'lev', 'num', 'deut', 'josh', 'judg', 'ruth', '1sam', '2sam', '1kgs', '2kgs',
    '1chr', '2chr', 'ezra', 'neh', 'esth', 'job', 'ps', 'prov', 'eccl', 'song', 'isa', 'jer', 'lam',
    'ezek', 'dan', 'hos', 'joel', 'amos', 'obad', 'jonah', 'mic', 'nah', 'hab', 'zeph', 'hag', 'zech', 'mal',
    'matt', 'mark', 'luke', 'john', 'acts', 'rom', '1cor', '2cor', 'gal', 'eph', 'phil', 'col',
    '1thess', '2thess', '1tim', '2tim', 'titus', 'phlm', 'heb', 'jas', '1pet', '2pet',
    '1john', '2john', '3john', 'jude', 'rev',
]
SBL_BOOK_NUM_TO_ID = {i + 1: bid for i, bid in enumerate(STANDARD_66_BOOK_ORDER)}


def extract_sbl_notes():
    """Returns ({book_id: {chapter: {verse: [note_dict, ...]}}}, total_spans_found) for the
    ground-truth check in main(). Covers the full 66-book standard canon (Deuterocanon, numbered
    67+ in this source, is out of scope — see the module-level comment above)."""
    out = {}
    total_spans = 0
    with zipfile.ZipFile(SBL_EPUB_PATH) as zf:
        for name in [n for n in zf.namelist() if n.endswith('.xhtml')]:
            txt = zf.read(name).decode('utf-8', 'ignore')
            matches = list(SBL_COM_SPAN_RE.finditer(txt))
            if not matches:
                continue
            body_end_cap = txt.find('</body>')
            file_end = body_end_cap if body_end_cap >= 0 else len(txt)
            for i, m in enumerate(matches):
                bb, cc, vv = int(m.group(1)), int(m.group(2)), int(m.group(3))
                book_id = SBL_BOOK_NUM_TO_ID.get(bb)  # None for bb outside 1-66 (e.g. Deuterocanon 67+) — skipped
                if not book_id:
                    continue
                seg_start = m.end()
                seg_end = matches[i + 1].start() if i + 1 < len(matches) else file_end
                raw_segment = txt[seg_start:seg_end]
                lm = SBL_LEMMA_RE.match(raw_segment)
                anchor_word = lm.group(1).strip() if lm else ''
                body_source = raw_segment[lm.end():] if lm else raw_segment
                body = SBL_XBR_LINK_RE.sub(r'\1', body_source).strip()
                body = re.sub(r'^[.:\s]+', '', body)
                if not body:
                    continue
                total_spans += 1
                title = f'SBL Study Note \u2014 \u2018{anchor_word}\u2019' if anchor_word else 'SBL Study Note'
                chapters = out.setdefault(book_id, {})
                verses = chapters.setdefault(str(cc), {})
                notes = verses.setdefault(str(vv), [])
                notes.append({
                    'src': 'sbl',
                    'tier': 'ACADEMIC/ECUMENICAL',
                    'kind': 'study',
                    'marker': m.group(0)[:60],
                    'anchor_word': anchor_word,
                    'title': title,
                    'html': body,
                })
    return out, total_spans


NOAB_EPUB_PATH = (
    r"C:\Users\Elation\Downloads\The New Oxford Annotated Bible_ New Revised Standard Version -- "
    r"Michael D_ Coogan, Marc Z_ Brettler, Julia M_ O'Brien, Emma -- 6, 2026 -- IRL Press at -- "
    r"isbn13 9780197633564 -- d5138d2c9cb5dbef18e39c48e2eb584c.epub"
)

# Ground-truthed directly against the live epub before writing any extraction code (Rule 5): one
# OEBPS/ChNN_Coogan_Bible.xhtml file per BOOK (not per chapter, despite the filename — confirmed by
# counting <h1> and notegroup occurrences per file: exactly one of each), holding that whole book's
# scripture text AND every one of its notes together in a single <div class="notegroup"> block of
# well-formed <div class="note" id="...">...</div> siblings (no next-marker-boundary guessing
# needed, unlike NET/Ignatius/SBL — each note div closes itself). Each note opens with
# <span class="enumer">...</span> (a backlink letter, a/b/c.../z then presumably aa/ab... — not
# used here since the per-verse letter sigil is computed client-side anyway) then a <b>C.V</b> verse
# reference, then the note's own "Or <i>alternate reading</i>" or explanatory text — translation and
# text-critical notes, not full prose commentary like SBL/Ignatius, matching NOAB's citation in the
# handoff as a critical-apparatus-style source.
#
# Correction kept per Rule 11/16 (the wrong first read stays on record, not silently replaced):
# this file's own ChNN sequence jumps straight from "INTRODUCTION TO THE LETTERS" (Ch64) to 1
# Corinthians (Ch65), and from the Pastoral Epistles introduction (Ch73) to 2 Timothy (Ch74) with
# no separate Romans or 1 Timothy file in between — which first read as those two books being
# missing from this epub copy (matching the filename search turning up nothing). That read was
# wrong: Romans and 1 Timothy are bundled INSIDE those two "introduction" files, the same way
# Matthew turned out to be bundled inside Ch59 "INTRODUCTION TO THE GOSPELS" rather than having its
# own file — caught by searching file CONTENT (not filenames) for "THE LETTER OF PAUL TO THE
# ROMANS" and finding it inside Ch64. The per-file "search every <h1>, not just the first" fix
# below (the same fix Matthew needed) resolves both books correctly; nothing is actually missing.
NOAB_NOTE_DIV_RE = re.compile(r'<div class="note" id="([^"]+)">(.*?)</div>', re.S)
NOAB_REF_RE = re.compile(r'^\s*<span class="enumer">.*?</span>\s*<b>(.*?)</b>(.*)$', re.S)

NOAB_TITLE_TO_BOOK_ID = {
    'THE GOSPEL ACCORDING TO MATTHEW': 'matt',
    'THE GOSPEL ACCORDING TO MARK': 'mark', 'THE GOSPEL ACCORDING TO LUKE': 'luke',
    'THE GOSPEL ACCORDING TO JOHN': 'john', 'THE ACTS OF THE APOSTLES': 'acts',
    'THE FIRST LETTER OF PAUL TO THE CORINTHIANS': '1cor', 'THE SECOND LETTER OF PAUL TO THE CORINTHIANS': '2cor',
    'THE LETTER OF PAUL TO THE GALATIANS': 'gal', 'THE LETTER OF PAUL TO THE EPHESIANS': 'eph',
    'THE LETTER OF PAUL TO THE PHILIPPIANS': 'phil', 'THE LETTER OF PAUL TO THE COLOSSIANS': 'col',
    'THE FIRST LETTER OF PAUL TO THE THESSALONIANS': '1thess', 'THE SECOND LETTER OF PAUL TO THE THESSALONIANS': '2thess',
    'THE SECOND LETTER OF PAUL TO TIMOTHY': '2tim', 'THE LETTER OF PAUL TO TITUS': 'titus',
    'THE LETTER OF PAUL TO PHILEMON': 'phlm', 'THE LETTER TO THE HEBREWS': 'heb',
    'THE LETTER OF JAMES': 'jas', 'THE FIRST LETTER OF PETER': '1pet', 'THE SECOND LETTER OF PETER': '2pet',
    'THE FIRST LETTER OF JOHN': '1john', 'THE SECOND LETTER OF JOHN': '2john', 'THE THIRD LETTER OF JOHN': '3john',
    'THE LETTER OF JUDE': 'jude', 'THE REVELATION TO JOHN': 'rev',
    # Bundled inside "introduction" files rather than having their own (see the correction above):
    'THE LETTER OF PAUL TO THE ROMANS': 'rom', 'THE FIRST LETTER OF PAUL TO TIMOTHY': '1tim',
    # OT (added once the NT-only scope was lifted — same title-casing inconsistency as the NT
    # table, taken verbatim from each file's own <h1>, not normalized to a single style). GENESIS,
    # JOSHUA and JOB are bundled inside their section-introduction files the same way Matthew/
    # Romans/1 Timothy are on the NT side — verified with the same zero-verse-markers-before-the-
    # heading check before trusting the attribution.
    # NOTE: the lookup below always uppercases the extracted <h1> text first (titles in this epub
    # mix styles — "Esther" vs "JUDGES" vs "The Song of Songs" in the raw source), so every key
    # here must be upper-cased regardless of how the source itself styled that title — caught by
    # testing this table immediately after writing it, not assumed correct from matching the
    # source's own casing.
    'GENESIS': 'gen', 'EXODUS': 'exod', 'LEVITICUS': 'lev', 'NUMBERS': 'num', 'DEUTERONOMY': 'deut',
    'JOSHUA': 'josh', 'JUDGES': 'judg', 'RUTH': 'ruth', '1 SAMUEL': '1sam', '2 SAMUEL': '2sam',
    '1 KINGS': '1kgs', '2 KINGS': '2kgs', '1 CHRONICLES': '1chr', '2 CHRONICLES': '2chr',
    'EZRA': 'ezra', 'NEHEMIAH': 'neh', 'ESTHER': 'esth', 'JOB': 'job', 'PSALMS': 'ps',
    'PROVERBS': 'prov', 'ECCLESIASTES': 'eccl', 'THE SONG OF SONGS': 'song', 'JEREMIAH': 'jer',
    'LAMENTATIONS': 'lam', 'EZEKIEL': 'ezek', 'DANIEL': 'dan', 'HOSEA': 'hos', 'JOEL': 'joel',
    'AMOS': 'amos', 'OBADIAH': 'obad', 'JONAH': 'jonah', 'MICAH': 'mic', 'NAHUM': 'nah',
    'HABAKKUK': 'hab', 'ZEPHANIAH': 'zeph', 'HAGGAI': 'hag', 'ZECHARIAH': 'zech', 'MALACHI': 'mal',
    # Deuterocanon (James, 2026-11-10: "i want a plenary bible in the fullest definition of
    # plenary" — this epub is in fact the full "with the Apocrypha" NOAB edition (confirmed by
    # listing every OEBPS/ChNN_Coogan_Bible.xhtml file's own <h1>s: Ch40-Ch58 are a dedicated
    # Apocrypha/Deuterocanon section, not absent from this copy as the earlier NT-only/then-66-book
    # passes assumed without checking). Only the 6 of those 18 Apocrypha-section books that need NO
    # chapter-offset remapping onto the suite's existing 73-book numbering are added here — each
    # maps 1:1 onto its own standalone NOAB chapter-file and the suite's own book_id with the exact
    # same bundled-intro-file pattern already proven for Genesis/Joshua/Job/Matthew/Romans/1Tim
    # (Tobit's own "TOBIT" h1 sits deeper in Ch40, after the Apocrypha section intro essay, found by
    # iterating every h1 in the file rather than trusting the first one — confirmed by grep for the
    # word "Tobit" in Ch40's raw text before assuming the bundling pattern held here too). Esther
    # (Greek)/Ch42 and the three Daniel-addition files (Ch48-50) are NOT added here: NOAB numbers
    # them as their own separate chapter-1 works, while the suite's 'esth'/'dan' books fold those
    # same additions in at specific offset chapters/verses (Vulgate convention) — that alignment
    # needs its own careful verse-by-verse check, not a guess, so it is left for a dedicated pass.
    'TOBIT': 'tob', 'JUDITH': 'jdt', 'THE WISDOM OF SOLOMON': 'wis',
    'ECCLESIASTICUS, OR THE WISDOM OF JESUS, SON OF SIRACH': 'sir',
    '1 MACCABEES': '1macc', '2 MACCABEES': '2macc',
}


def extract_noab_notes():
    """Returns ({book_id: {chapter: {verse: [note_dict, ...]}}}, total_notes, missing_books) for
    the ground-truth check in main(). Covers the 66-book canon plus 6 Deuterocanon books that need
    no chapter-offset remapping (Tobit, Judith, Wisdom, Sirach, 1-2 Maccabees — see the Deuterocanon
    comment on NOAB_TITLE_TO_BOOK_ID for why Esther-Greek/Daniel-additions are deliberately not
    included here). missing_books lists any book this epub copy turned out not to contain (expected:
    none, once rom/1tim's real bundled-file location was found — see the correction above)."""
    out = {}
    total_notes = 0
    found_books = set()
    with zipfile.ZipFile(NOAB_EPUB_PATH) as zf:
        ch_files = sorted(
            (n for n in zf.namelist() if re.match(r'OEBPS/Ch\d+_Coogan_Bible\.xhtml$', n)),
            key=lambda n: int(re.search(r'Ch(\d+)', n).group(1)),
        )
        for name in ch_files:
            txt = zf.read(name).decode('utf-8', 'ignore')
            # Checked every h1 in the file, not just the first: Ch59_Coogan_Bible.xhtml's first h1
            # is "INTRODUCTION TO THE GOSPELS" (a shared intro essay for all four Gospels), with
            # "THE GOSPEL ACCORDING TO MATTHEW" as a LATER h1 in the same file — Matthew has no
            # file of its own the way Mark/Luke/John each do. Matching only the first h1 would have
            # silently dropped Matthew entirely; this was caught by cross-checking the file's own
            # text for "Blessed are the poor" (Matt 5:3) before trusting any book-list conclusion.
            book_id = None
            for hm in re.finditer(r'<h1[^>]*>(.*?)</h1>', txt, re.S):
                title = html_mod.unescape(re.sub(r'<[^>]+>', '', hm.group(1))).strip().upper()
                candidate = NOAB_TITLE_TO_BOOK_ID.get(title)
                if candidate:
                    book_id = candidate
                    break
            if book_id is None:
                continue
            found_books.add(book_id)

            for note_id, note_inner in NOAB_NOTE_DIV_RE.findall(txt):
                rm = NOAB_REF_RE.match(note_inner)
                if not rm:
                    continue
                ref_raw = html_mod.unescape(re.sub(r'<[^>]+>', '', rm.group(1))).strip()
                # Single-chapter books (Phlm, 2/3 John, Jude) print the ref as a bare verse number
                # with no "C." prefix — caught by diffing this extractor's per-book output against
                # an independent raw note-div count, which flagged exactly these 4 books at zero.
                refm = re.match(r'^(\d+)\.(\d+)', ref_raw)
                if refm:
                    chap_s, verse_s = refm.groups()
                else:
                    bare_m = re.match(r'^(\d+)$', ref_raw)
                    if not bare_m:
                        continue
                    chap_s, verse_s = '1', bare_m.group(1)
                body = rm.group(2)
                # The source nests koboSpan/xref/footnote-backlink spans several layers deep and
                # inconsistently (a note can embed a second, unrelated footnote marker mid-sentence
                # — e.g. John 1:4's note carries its own internal "<sup><i>3</i></sup>" aside).
                # Surgical tag-by-tag unwrapping left mismatched leftover tags in a few notes
                # (caught by reading this exact rendered output, not assumed safe); stripping every
                # tag to plain text guarantees valid, uncorrupted output at the cost of italics.
                body = re.sub(r'<[^>]+>', ' ', body)
                body = html_mod.unescape(body)
                body = re.sub(r'\s+', ' ', body).strip()
                body = re.sub(r'^[.:\s]+', '', body)
                if not body:
                    continue
                total_notes += 1
                chapters = out.setdefault(book_id, {})
                verses = chapters.setdefault(str(int(chap_s)), {})
                notes = verses.setdefault(str(int(verse_s)), [])
                notes.append({
                    'src': 'noab',
                    'tier': 'ACADEMIC/ECUMENICAL',
                    'kind': 'tc',
                    'marker': note_id,
                    'anchor_word': '',
                    'title': f'NOAB Note \u2014 {chap_s}.{verse_s}',
                    'html': body,
                })
    all_mapped_book_ids = set(NOAB_TITLE_TO_BOOK_ID.values())
    missing_books = sorted(all_mapped_book_ids - found_books)
    return out, total_notes, missing_books


# Esther-Greek (Ch42) and the three Daniel-addition files (Ch48-50), left out of
# NOAB_TITLE_TO_BOOK_ID with the comment above explaining why -- each needed its own verse-by-verse
# ground-truth check against the suite's own DRA.json before a line of extraction code, not a guess
# (James, 2026-11-10: "i want a plenary bible in the fullest definition of plenary").
#
# Esther-Greek (Ch42): NO offset needed. NOAB's own notes in this file are self-documenting --
# "11.2-12.6 corresponds to A 1-17 in some translations", "16.1-24 corresponds to E 1-24" -- which
# confirms NOAB's own chapter.verse numbering for this material (11-16) is ALREADY the same
# continuous Vulgate/DRA scheme the suite's 'esth' book uses (chapters 11-16 after the 10-chapter
# Hebrew text), not the alternative lettered A-F scheme the notes merely gloss for readers who know
# that convention instead. Confirmed directly: NOAB ch16 runs 1-24, and DRA's own ch16 also has
# exactly 24 verses.
#
# Susanna (Ch49): NO offset. This file's own verse 1 ("There was a man living in Babylon whose name
# was Joakim") is word-for-word the same opening as DRA dan ch13 verse 1 ("Now there was a man that
# dwelt in Babylon, and his name was Joakim") -- confirmed by reading both, not assumed from the
# single shared "13" placement in CANON_ORDER.
#
# Bel and the Dragon (Ch50): OFFSET -1. NOAB's own verse 1 ("When King Astyages was laid to rest...
# Cyrus the Persian succeeded to his kingdom") has NO equivalent in DRA's ch14 at all -- DRA follows
# the Vulgate/Theodotion recension, which omits that historical preamble sentence entirely and
# opens directly with "And Daniel was the king's guest" (DRA 14:1). Confirmed across 7 independent
# verse-content matches, not just the opening: NOAB 8/23/26/27/28/36/42 ("his priests" / dragon-
# slaying scene / "by the power of his spirit" / final verses) match DRA 7/22/25/26/27/35/41 exactly
# in content, a consistent off-by-one throughout.
#
# Prayer of Azariah and the Song of the Three Jews (Ch48): OFFSET +23, landing inside dan ch3, not
# its own chapter. The source text itself states this outright -- "(Additions to Daniel, inserted
# between 3.23 and 3.24)" -- and NOAB's own verse 1 ("They walked around in the midst of the
# flames, singing hymns to God") is the Vulgate's own 3:24, confirmed by DRA ch3 having exactly 100
# verses (expanded from the ~30-verse Hebrew original specifically to hold this interpolation).
NOAB_ADDITION_FILES = [
    # (file_num, book_id, fixed_chapter_or_None, verse_offset)
    (42, 'esth', None, 0),   # None chapter = use NOAB's own chapter.verse ref as-is
    (49, 'dan', 13, 0),
    (50, 'dan', 14, -1),
    (48, 'dan', 3, 23),
]


def extract_noab_greek_additions():
    """Returns ({book_id: {chapter: {verse: [note_dict, ...]}}}, total_notes) for Esther-Greek and
    the three Daniel additions, each aligned to the suite's own DRA-based chapter/verse scheme per
    the offsets ground-truthed in the comment above. Reuses NOAB_NOTE_DIV_RE/NOAB_REF_RE -- these
    four files are the same epub, same markup family as the rest of NOAB."""
    out = {}
    total_notes = 0
    with zipfile.ZipFile(NOAB_EPUB_PATH) as zf:
        for file_num, book_id, fixed_chap, offset in NOAB_ADDITION_FILES:
            name = f'OEBPS/Ch{file_num}_Coogan_Bible.xhtml'
            txt = zf.read(name).decode('utf-8', 'ignore')
            for note_id, note_inner in NOAB_NOTE_DIV_RE.findall(txt):
                rm = NOAB_REF_RE.match(note_inner)
                if not rm:
                    continue
                ref_raw = html_mod.unescape(re.sub(r'<[^>]+>', '', rm.group(1))).strip()
                refm = re.match(r'^(\d+)\.(\d+)', ref_raw)
                if refm:
                    noab_chap, noab_verse = int(refm.group(1)), int(refm.group(2))
                else:
                    bare_m = re.match(r'^(\d+)', ref_raw)
                    if not bare_m:
                        continue
                    noab_chap, noab_verse = 1, int(bare_m.group(1))

                if fixed_chap is None:
                    out_chap, out_verse = noab_chap, noab_verse
                else:
                    out_chap, out_verse = fixed_chap, noab_verse + offset
                if out_verse < 1:
                    continue  # NOAB-only preamble verse with no DRA equivalent (Bel's own v.1)

                body = rm.group(2)
                body = re.sub(r'<[^>]+>', ' ', body)
                body = html_mod.unescape(body)
                body = re.sub(r'\s+', ' ', body).strip()
                body = re.sub(r'^[.:\s]+', '', body)
                if not body:
                    continue
                total_notes += 1
                chapters = out.setdefault(book_id, {})
                verses = chapters.setdefault(str(out_chap), {})
                notes = verses.setdefault(str(out_verse), [])
                notes.append({
                    'src': 'noab',
                    'tier': 'ACADEMIC/ECUMENICAL',
                    'kind': 'tc',
                    'marker': note_id,
                    'anchor_word': '',
                    'title': f'NOAB Note — {out_chap}.{out_verse}',
                    'html': body,
                })
    return out, total_notes


NIV_EPUB_PATH = (
    r"C:\Users\Elation\Downloads\NIV Study Bible, Fully Revised -- HarperCollins Christian "
    "Publishing -- Zondervan -- f67e480ceca371deaee30527d7f2a2d2 -- Anna" + "\u2019" + "s Archive.epub"
)

# Ground-truthed against the live epub before writing any extraction code (Rule 5). Two SEPARATE
# note systems share this source (the handoff doc named only one): "com" ids are verse-keyed Study
# Notes, one self-contained <p class="com" id="comBBCCCVVV">...</p> per verse (same BBCCCVVV
# standard-66-book numbering as SBL, confirmed against John=43 again) — no next-marker-boundary
# guessing needed, the </p> closes it. "enref"/"x" ids are a SEPARATE lettered textual-footnote
# system (<a class="enref" href="...#x43001001a">a</a> in the running text -> an endnote file) —
# out of scope for this pass; only the "com" Study Notes are extracted here, consistent with this
# project's "study commentary" framing for the other 3 sources already merged.
# Census before writing the parser: 19,760 total "com" notes across the whole Bible (standard
# numbering tops out at 66 in this source — no deuterocanon offset like SBL's 67+ scheme), 5,718 of
# them in the 27 NT books initially targeted; the NT-only filter was lifted once NOAB/SBL both
# turned out to generalize cleanly to the OT, covering the full 66-book canon here too.
# Like Ignatius and SBL, NIV's own study-note convention bolds (here: italicizes) each phrase it
# glosses inline within one note — e.g. com43001001 reads "<i>In the beginning.</i> A deliberate
# echo of Ge 1:1... <i>Word.</i> See article. <i>with God.</i> The Word was distinct... <i>was
# God.</i> Jesus was God..." — four real per-phrase indicators bundled in one verse's note, split
# into separate notes the same way Ignatius's <b>phrase:</b> sub-headers were.
NIV_COM_RE = re.compile(r'<p class="com" id="com(\d{2})(\d{3})(\d{3})">(.*?)</p>', re.S)
NIV_LEMMA_SPLIT_RE = re.compile(r'<i>([^<]{1,60})\.</i>')
NIV_BCV_BACKLINK_RE = re.compile(r'^\s*(?:<img\b[^>]*/?>\s*)?<span class="bcv">.*?</span>\s*', re.S)
NIV_XBR_XREF_RE = re.compile(r'<a class="(?:xbr|xref)"[^>]*>(.*?)</a>', re.S)


def extract_niv_notes():
    """Returns ({book_id: {chapter: {verse: [note_dict, ...]}}}, total_notes_after_split,
    total_paragraphs) for the ground-truth check in main(). Covers the full 66-book canon."""
    out = {}
    total_after_split = 0
    total_paragraphs = 0
    with zipfile.ZipFile(NIV_EPUB_PATH) as zf:
        for name in [n for n in zf.namelist() if n.endswith('.xhtml') and 'hcp-nivsb20' in n]:
            txt = zf.read(name).decode('utf-8', 'ignore')
            for bb_s, cc_s, vv_s, inner in NIV_COM_RE.findall(txt):
                bb = int(bb_s)
                book_id = SBL_BOOK_NUM_TO_ID.get(bb)  # same standard-66 table SBL uses; None skips out-of-range bb
                if not book_id:
                    continue
                total_paragraphs += 1
                body_source = NIV_BCV_BACKLINK_RE.sub('', inner, count=1)
                for sub_label, sub_text in _niv_split_lemmas(body_source):
                    html_body = NIV_XBR_XREF_RE.sub(r'\1', sub_text)
                    html_body = re.sub(r'<!--.*?-->', '', html_body, flags=re.S)
                    # The lemma-split regex only fires on "<i>phrase.</i>" (trailing period); a
                    # lemma phrased as a question ("<i>Is Christ divided?</i>") or a typographic
                    # span ("<span class=\"ac\">ad</span>" for small-caps AD) isn't a sub-header
                    # and was never meant to be caught by it, but it still leaves a tag in the
                    # body text — caught by scanning every extracted note's own html for leftover
                    # tags (550 of 8,926), not assumed clean from the split alone. Same resolution
                    # as NOAB: strip to plain text rather than chase every tag variant by hand.
                    html_body = re.sub(r'<[^>]+>', ' ', html_body)
                    html_body = html_mod.unescape(html_body)
                    html_body = re.sub(r'\s+', ' ', html_body).strip()
                    html_body = re.sub(r'^[.:\s]+', '', html_body)
                    if not html_body:
                        continue
                    chap_s, verse_s = str(int(cc_s)), str(int(vv_s))
                    title = f'NIV Study Note \u2014 \u2018{sub_label}\u2019' if sub_label else 'NIV Study Note'
                    chapters = out.setdefault(book_id, {})
                    verses = chapters.setdefault(chap_s, {})
                    notes = verses.setdefault(verse_s, [])
                    notes.append({
                        'src': 'niv_sb',
                        'tier': 'EVANGELICAL',
                        'kind': 'study',
                        'marker': f'com{bb_s}{cc_s}{vv_s}',
                        'anchor_word': sub_label or '',
                        'title': title,
                        'html': html_body,
                    })
                    total_after_split += 1
    return out, total_after_split, total_paragraphs


def _niv_split_lemmas(body):
    """Same technique as split_ignatius_subglosses but keyed on NIV's own "<i>phrase.</i>"
    convention instead of Ignatius's "<b>phrase:</b>" — kept as a separate function (not a shared
    helper taking a regex argument) because the trailing punctuation differs (". " vs ": ") and
    conflating them risks a subtle cross-source regression neither source's own tests would catch."""
    parts = NIV_LEMMA_SPLIT_RE.split(body)
    chunks = [(None, parts[0].strip())]
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        text = parts[i + 1].strip() if i + 1 < len(parts) else ''
        chunks.append((label, text))
    return [(label, text) for label, text in chunks if text]


IGNATIUS_DANIEL_EPUB_PATH = (
    r"C:\Users\Elation\PDFS\01_Biblical_Studies_and_Canon"
    r"\_AA_ Hahn Ph D , Scott, Mitch, Curtis - Daniel Ignatius Catholic Study Bible.epub"
)
# Ground-truthed directly, not assumed from the NT epub's schema (Rule 5): this OT book was
# converted by a different Calibre pipeline than page-1.html (hash-named split files, not one
# single-page document), and its commentary lives in several of those split files interleaved with
# unrelated "Study Questions" sections — found by searching every .html file in the archive for the
# verse-ref pattern rather than trusting the scripture-text file list parse_ignatius_rsv2ce.py
# already had (that manifest only covers the Text anchor, never needed the Commentary one).
# Confirmed empirically which 8 of the 25 split files carry real commentary (split_008/010/012/013/
# 015/017/019/021 — 225 note openers total, independently counted before writing any extraction
# code) rather than assuming "the biggest files must be it."
#
# IMPORTANT — verified NOT to generalize to other Ignatius OT books: Isaiah's commentary (a
# DIFFERENT Calibre conversion, index_split_*.html naming) wraps its verse ref in a nested
# <a href="...">C:V</a> inside the bold span and carries zero plain "<span class=\"bold\">C:V"
# matches of Daniel's exact shape — checked directly before assuming the convention carried over,
# and it does not. Each of the 16 remaining Ignatius OT books needs this same individual
# ground-truth pass; Daniel is the first one completed, not a template that mechanically repeats.
IGNATIUS_DANIEL_COMMENTARY_FILES = [
    'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_008.html', 'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_010.html',
    'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_012.html', 'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_013.html',
    'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_015.html', 'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_017.html',
    'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_019.html', 'CR!XKGJ2DPDHX45X8D9RTXSTZR1G8J6_split_021.html',
]
IGNATIUS_DAN_SPAN_RE = re.compile(r'<span class="bold">(\d+):(\d+)([^<]{0,60})</span>')
IGNATIUS_DAN_SUBGLOSS_RE = re.compile(r'<span class="bold">([^<]{1,60}?):\s*</span>')


def _dan_split_subglosses(body):
    """Same technique as split_ignatius_subglosses/_niv_split_lemmas, keyed on Daniel's own
    "<span class=\"bold\">phrase:</span>" convention (this Calibre conversion's equivalent of the
    NT epub's <b>phrase:</b> — a different tag because it is a different converter, not a different
    authorial convention). Kept separate from the NT version rather than sharing one parameterized
    function, consistent with the same decision made for NIV's lemma splitter."""
    parts = IGNATIUS_DAN_SUBGLOSS_RE.split(body)
    chunks = [(None, parts[0].strip())]
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        text = parts[i + 1].strip() if i + 1 < len(parts) else ''
        chunks.append((label, text))
    return [(label, text) for label, text in chunks if text]


def extract_ignatius_daniel_notes():
    """Returns ({'dan': {chapter: {verse: [note_dict, ...]}}}, paragraphs_kept, notes_after_split)
    for the ground-truth check in main()."""
    chapters = {}
    paragraphs_kept = 0
    notes_after_split = 0
    with zipfile.ZipFile(IGNATIUS_DANIEL_EPUB_PATH) as zf:
        for fname in IGNATIUS_DANIEL_COMMENTARY_FILES:
            txt = zf.read(fname).decode('utf-8', 'ignore')
            spans = list(IGNATIUS_DAN_SPAN_RE.finditer(txt))
            for i, m in enumerate(spans):
                chap_s, verse_s, lemma_tail = m.group(1), m.group(2), m.group(3)
                seg_start = m.end()
                seg_end = spans[i + 1].start() if i + 1 < len(spans) else min(seg_start + 4000, len(txt))
                raw_segment = txt[seg_start:seg_end]
                # Cut at the next note's own opening <p ...> if one intervenes before the next
                # bold-span ref (keeps a trailing note from swallowing the next paragraph's lead-in).
                p_cut = re.search(r'</p>\s*<p\b', raw_segment)
                if p_cut:
                    raw_segment = raw_segment[:p_cut.start()]
                paragraphs_kept += 1

                main_anchor = _clean_ignatius_anchor(re.sub(r'<[^>]+>', '', lemma_tail).strip().rstrip(':').strip())
                for sub_label, sub_text in _dan_split_subglosses(raw_segment):
                    anchor_word = sub_label if sub_label is not None else main_anchor
                    html_body = DEAD_INTERNAL_LINK_RE.sub(r'\1', sub_text) if sub_text else ''
                    # This conversion's "Back to text." backlink is a plain <a href="file#filepos">
                    # (a filename prefix before the fragment, unlike the NT epub's bare "#filepos"
                    # href DEAD_INTERNAL_LINK_RE targets) — stripping the <a> tag alone leaves the
                    # link TEXT behind, caught by reading an actual extracted note's full text
                    # rather than trusting the regex chain covered it.
                    html_body = re.sub(r'\s*Back to text\.?\s*$', '', html_body)
                    html_body = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', html_body, flags=re.S)
                    html_body = re.sub(r'<[^>]+>', ' ', html_body)
                    html_body = html_mod.unescape(html_body)
                    html_body = re.sub(r'\s+', ' ', html_body).strip()
                    html_body = re.sub(r'^[.:\s]+', '', html_body)
                    html_body = re.sub(r'\s*Back to text\.?\s*$', '', html_body).strip()
                    if not html_body:
                        continue
                    title = f'Ignatius CSB \u2014 Dan {chap_s}:{verse_s} \u2018{anchor_word}\u2019' if anchor_word else f'Ignatius CSB \u2014 Dan {chap_s}:{verse_s}'
                    verses = chapters.setdefault(str(int(chap_s)), {})
                    notes = verses.setdefault(str(int(verse_s)), [])
                    notes.append({
                        'src': 'ignatius',
                        'tier': 'CATHOLIC IMPRIMATUR',
                        'kind': 'study',
                        'marker': f'{chap_s}:{verse_s}' + (f' / {sub_label}' if sub_label else ''),
                        'anchor_word': anchor_word,
                        'title': title,
                        'html': html_body,
                    })
                    notes_after_split += 1
    return {'dan': chapters}, paragraphs_kept, notes_after_split


def extract_ignatius_boldplain_notes(epub_path, commentary_files, book_id):
    """Generalizes extract_ignatius_daniel_notes() to any book sharing Daniel's exact shape
    (bare "<span class=\"bold\">C:V anchor:</span>" with no href wrapping the ref) -- confirmed on
    Proverbs/Ecclesiastes/Song of Solomon by reading real samples (Rule 5), not assumed from
    Daniel carrying over. Kept as a separate function from Daniel's rather than refactoring
    Daniel's own call site, so the original proof-of-concept entry stays byte-for-byte reproducible."""
    chapters = {}
    paragraphs_kept = 0
    notes_after_split = 0
    with zipfile.ZipFile(epub_path) as zf:
        for fname in commentary_files:
            txt = zf.read(fname).decode('utf-8', 'ignore')
            spans = list(IGNATIUS_DAN_SPAN_RE.finditer(txt))
            for i, m in enumerate(spans):
                chap_s, verse_s, lemma_tail = m.group(1), m.group(2), m.group(3)
                seg_start = m.end()
                seg_end = spans[i + 1].start() if i + 1 < len(spans) else min(seg_start + 4000, len(txt))
                raw_segment = txt[seg_start:seg_end]
                p_cut = re.search(r'</p>\s*<p\b', raw_segment)
                if p_cut:
                    raw_segment = raw_segment[:p_cut.start()]
                paragraphs_kept += 1

                main_anchor = _clean_ignatius_anchor(re.sub(r'<[^>]+>', '', lemma_tail).strip().rstrip(':').strip())
                for sub_label, sub_text in _dan_split_subglosses(raw_segment):
                    anchor_word = sub_label if sub_label is not None else main_anchor
                    html_body = sub_text or ''
                    html_body = re.sub(r'\s*Back to text\.?\s*$', '', html_body)
                    html_body = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', html_body, flags=re.S)
                    html_body = re.sub(r'<[^>]+>', ' ', html_body)
                    html_body = html_mod.unescape(html_body)
                    html_body = re.sub(r'\s+', ' ', html_body).strip()
                    html_body = re.sub(r'^[.:\s]+', '', html_body)
                    html_body = re.sub(r'\s*Back to text\.?\s*$', '', html_body).strip()
                    if not html_body:
                        continue
                    title = (f'Ignatius CSB \u2014 {chap_s}:{verse_s} \u2018{anchor_word}\u2019'
                             if anchor_word else f'Ignatius CSB \u2014 {chap_s}:{verse_s}')
                    verses = chapters.setdefault(str(int(chap_s)), {})
                    notes = verses.setdefault(str(int(verse_s)), [])
                    notes.append({
                        'src': 'ignatius',
                        'tier': 'CATHOLIC IMPRIMATUR',
                        'kind': 'study',
                        'marker': f'{chap_s}:{verse_s}' + (f' / {sub_label}' if sub_label else ''),
                        'anchor_word': anchor_word,
                        'title': title,
                        'html': html_body,
                    })
                    notes_after_split += 1
    return {book_id: chapters}, paragraphs_kept, notes_after_split


def _clean_ignatius_anchor(word):
    """A note's header text is sometimes a verse-RANGE continuation ("-7", "\u20132:18") rather
    than a real anchor word/phrase -- e.g. Proverbs 1:1's commentary opens "1:1-7 The prologue...",
    and this family's own regexes capture the "-7 " tail as if it were an anchor. Found by auditing
    real output across every OT book built so far (164 cases, 16 pre-existing in Daniel's own
    original pass): a dangling anchor is cosmetic (the note's real commentary text is unaffected),
    but ships a nonsense title badge like "'-7'" to the UI, so it is blanked here rather than left."""
    if word and re.match(r'^[-\u2012\u2013\u2014]\s*\d', word):
        return ''
    return word


PDFS_IGNATIUS_DIR = r"C:\Users\Elation\PDFS\01_Biblical_Studies_and_Canon"

# The second Ignatius OT Calibre-conversion family (Joshua, Judges+Ruth, 1&2 Kings,
# Tobit+Judith+Esther, Isaiah all ground-truthed to share this shape; Proverbs/Ecclesiastes/
# Song of Solomon, Deuteronomy, and 1-2 Maccabees do NOT -- checked individually, not assumed,
# per the standing warning on IGNATIUS_DANIEL_COMMENTARY_FILES above). Unlike Daniel's bare
# "<span class=\"bold\">1:1 anchor:</span>", this family wraps the chapter:verse ref itself in
# its own <a href="...#filepos...">, with any immediately-following anchor word still inside the
# same outer bold span but outside the <a> -- e.g. Joshua's
# "<span class=\"bold\"><a href=\"index_split_009.html#filepos56350\">1:1</a> death of Moses:
# </span>Narrated in Deut 34:1-8...". Confirmed by reading real samples from all five books, not
# assumed from Joshua alone (Rule 5) -- the sub-gloss convention inside a note's body
# ("<span class=\"bold\">servant of the Lord: </span>") is nonetheless IDENTICAL to Daniel's, so
# _dan_split_subglosses is reused rather than reimplemented.
IGNATIUS_BOLDLINK_OPENER_RE = re.compile(
    r'<span class="bold"><a href="[^"]*#filepos\d+">(\d+):(\d+)</a>([^<]{0,80})</span>'
)


def extract_ignatius_boldlink_notes(epub_path, commentary_files, book_id):
    """Generic extractor for one book of the 'ref-wrapped-in-its-own-<a>' Ignatius OT family.
    commentary_files must be the book's own verified commentary file(s) -- every book in this
    family also has a back-of-chapter Study Questions file using the IDENTICAL bold-span+<a>
    wrapper (confirmed on Joshua's index_split_016.html: real text is a numbered list of
    "What/Who/How" questions, not commentary), so file selection is a ground-truth decision
    made once per book by reading actual content, never "every file with a match in it"."""
    chapters = {}
    paragraphs_kept = 0
    notes_after_split = 0
    with zipfile.ZipFile(epub_path) as zf:
        for fname in commentary_files:
            txt = zf.read(fname).decode('utf-8', 'ignore')
            spans = list(IGNATIUS_BOLDLINK_OPENER_RE.finditer(txt))
            for i, m in enumerate(spans):
                chap_s, verse_s, lead_tail = m.group(1), m.group(2), m.group(3)
                seg_start = m.end()
                seg_end = spans[i + 1].start() if i + 1 < len(spans) else min(seg_start + 4000, len(txt))
                raw_segment = txt[seg_start:seg_end]
                p_cut = re.search(r'</p>\s*<p\b', raw_segment)
                if p_cut:
                    raw_segment = raw_segment[:p_cut.start()]
                paragraphs_kept += 1

                main_anchor = _clean_ignatius_anchor(re.sub(r'<[^>]+>', '', lead_tail).strip().rstrip(':').strip())
                for sub_label, sub_text in _dan_split_subglosses(raw_segment):
                    anchor_word = sub_label if sub_label is not None else main_anchor
                    html_body = sub_text or ''
                    html_body = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', html_body, flags=re.S)
                    html_body = re.sub(r'<[^>]+>', ' ', html_body)
                    html_body = html_mod.unescape(html_body)
                    html_body = re.sub(r'\s+', ' ', html_body).strip()
                    html_body = re.sub(r'^[.:\s]+', '', html_body)
                    if not html_body:
                        continue
                    title = (f'Ignatius CSB \u2014 {chap_s}:{verse_s} \u2018{anchor_word}\u2019'
                             if anchor_word else f'Ignatius CSB \u2014 {chap_s}:{verse_s}')
                    verses = chapters.setdefault(str(int(chap_s)), {})
                    notes = verses.setdefault(str(int(verse_s)), [])
                    notes.append({
                        'src': 'ignatius',
                        'tier': 'CATHOLIC IMPRIMATUR',
                        'kind': 'study',
                        'marker': f'{chap_s}:{verse_s}' + (f' / {sub_label}' if sub_label else ''),
                        'anchor_word': anchor_word,
                        'title': title,
                        'html': html_body,
                    })
                    notes_after_split += 1
    return {book_id: chapters}, paragraphs_kept, notes_after_split


# Per-book commentary-file lists, each one read and confirmed by hand (never "every file that
# matches the regex") before being added here -- see the per-epub Rule 12 ledger entries for the
# reconnaissance that produced each list.
IGNATIUS_JOSHUA_EPUB_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Scott Hahn; Curtis Mitch - Joshua Ignatius Catholic Study Bible (The Ignatius Catholic (2017).epub"
)
IGNATIUS_JOSHUA_COMMENTARY_FILES = ['index_split_010.html', 'index_split_013.html', 'index_split_015.html']

IGNATIUS_JUDGES_RUTH_EPUB_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Scott Hahn; Curtis Mitch - Judges and Ruth (Ignatius Catholic Study Bible) (2015).epub"
)
IGNATIUS_JUDGES_COMMENTARY_FILES = ['index_split_015.html']
IGNATIUS_RUTH_COMMENTARY_FILES = ['index_split_016.html']

IGNATIUS_ISAIAH_EPUB_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Scott Hahn; Curtis Mitch - The Ignatius Catholic Study Bible Isaiah.epub"
)
# Confirmed continuous 1:1 -> 66:24 across exactly these five files (each file's first/last ref
# picks up exactly where the previous one left off); index_split_018.html was excluded after
# reading it directly -- it is the back-of-book Study Questions file ("What is Isaiah's
# signature epithet...", restarting at 1:4), not commentary, despite matching the same regex.
IGNATIUS_ISAIAH_COMMENTARY_FILES = [
    'index_split_009.html', 'index_split_011.html', 'index_split_013.html',
    'index_split_015.html', 'index_split_017.html',
]

IGNATIUS_KINGS_EPUB_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Hahn, Scott & Mitch, Curtis - Ignatius Catholic Study Bible 1 & 2 Kings (The Ignatius (2017).epub"
)
# 1 Kings: part0011-0025 (odd-numbered) run continuously 1:1 -> 22:52; part0026 excluded (Study
# Questions, restarts at 1:5). 2 Kings: part0031-0041 run continuously 1:1 -> 25:30; part0042
# excluded (Study Questions, restarts at 1:2) -- both confirmed by reading first/last match in
# every file with a hit, not assumed from the marker alone.
IGNATIUS_1KGS_COMMENTARY_FILES = [
    'text/part0011.html', 'text/part0013.html', 'text/part0015.html', 'text/part0017.html',
    'text/part0019.html', 'text/part0021.html', 'text/part0023.html', 'text/part0025.html',
]
IGNATIUS_2KGS_COMMENTARY_FILES = [
    'text/part0031.html', 'text/part0033.html', 'text/part0035.html',
    'text/part0037.html', 'text/part0039.html', 'text/part0041.html',
]

IGNATIUS_TJE_EPUB_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Scott Hahn & Curtis Mitch - Tobit, Judith, and Esther Ignatius Catholic Study Bible (2019).epub"
)
# Tobit: part0007/0009/0011 continuous 1:1->14:15 (part0012 is Study Questions, restarts 1:6).
# Judith: part0015_split_000/001/002 continuous 1:1->16:25 (part0016 is Study Questions, restarts
# 1:1). Esther: part0019 alone, 1:1->10:3 (part0020 is Study Questions, restarts 1:1).
# NOT YET RESOLVED, stated plainly rather than silently assumed covered: this volume's Esther
# commentary stops at 10:3 in this scan; whether Hahn/Mitch's Catholic-canon Esther (with the
# Greek additions the suite's own 'esth' book carries at Vulgate-convention offset
# chapters/verses beyond MT's 10 chapters) has further commentary under a different reference
# convention (lettered sections, e.g.) has not been checked -- same open question NOAB's own
# Esther-Greek gap already raised, left for that same follow-up rather than guessed here.
IGNATIUS_TOB_COMMENTARY_FILES = ['text/part0007.html', 'text/part0009.html', 'text/part0011.html']
IGNATIUS_JDT_COMMENTARY_FILES = ['text/part0015_split_000.html', 'text/part0015_split_001.html', 'text/part0015_split_002.html']
IGNATIUS_ESTH_COMMENTARY_FILES = ['text/part0019.html']

IGNATIUS_PES_EPUB_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Scott Hahn; Curtis Mitch; Dennis Walters - Proverbs, Ecclesiastes, and Song of Solomon Ignatius (2013).epub"
)
# A FOURTH distinct shape, ground-truthed before assuming anything carried over from the first
# three families (Rule 5): this epub uses Daniel's bare bold-span convention (no href around the
# ref) for its REAL commentary, and the Joshua-family ref-in-<a> convention for its Study
# Questions -- the OPPOSITE assignment from the Joshua-family books, where ref-in-<a> was the
# commentary. Confirmed per book by reading first/last match in each candidate file: the
# bold-plain files run continuous chapter:verse commentary start-to-end; the bold_a files restart
# at chapter 1 and read as "What does Proverbs teach..." questions.
IGNATIUS_PROV_COMMENTARY_FILES = ['index_split_010.html']
IGNATIUS_ECCL_COMMENTARY_FILES = ['index_split_016.html']
IGNATIUS_SONG_COMMENTARY_FILES = ['index_split_021.html']

# Deuteronomy: a FIFTH, completely different shape -- an InDesign/Adobe export (CharOverride-N
# classes, noteNNNN ids), not a Calibre conversion at all, ground-truthed from scratch rather than
# assumed to share anything with the four families above. Commentary lives entirely in one file
# (deuteronomy_0015.xhtml, verified -- 0014/0016 on either side have zero matches), one note per
# <p class="Commentary_AN-TX" id="noteNNNN">, as "Commentary: <span class=\"AN-Syntax-T...\">C:V
# anchor:</span>body". A note's own secondary sub-glosses use a stable class, CharOverride-21
# ("Moses spoke:", "beyond the Jordan:") -- but that SAME class is also used for plain italicized
# emphasis inside a note's body with no trailing colon ("the L[ORD]", a quoted Scripture phrase
# split by small-caps styling) -- confirmed by sampling real spans (26 of 178 CharOverride-21
# spans do not end in ':'), so the split only fires on a colon-terminated span, not every
# occurrence of the class.
IGNATIUS_DEUT_EPUB_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Hahn, Scott;Mitch, Curtis;Walters, Dennis;Barber, Michael; - Deuteronomy (Ignatius Catholic Study Bible).epub"
)
IGNATIUS_DEUT_COMMENTARY_FILE = 'OEBPS/deuteronomy_0015.xhtml'
IGNATIUS_DEUT_NOTE_RE = re.compile(
    r'<p class="Commentary_AN-TX" id="note\d+">Commentary:\s*<span[^>]*>(\d+):(\d+)([^<]*)</span>(.*?)</p>', re.S
)
IGNATIUS_DEUT_SUBGLOSS_RE = re.compile(r'<span class="CharOverride-21">([^<]+?):\s*</span>')


def _deut_split_subglosses(body):
    """Same technique as _dan_split_subglosses, keyed on Deuteronomy's own colon-terminated
    CharOverride-21 spans only -- a CharOverride-21 span with no trailing colon is left as plain
    emphasis inside whichever chunk it falls in, not treated as a split point."""
    parts = IGNATIUS_DEUT_SUBGLOSS_RE.split(body)
    chunks = [(None, parts[0].strip())]
    for i in range(1, len(parts), 2):
        label = parts[i].strip()
        text = parts[i + 1].strip() if i + 1 < len(parts) else ''
        chunks.append((label, text))
    return [(label, text) for label, text in chunks if text]


def extract_ignatius_deut_notes():
    """Returns ({'deut': {chapter: {verse: [note_dict, ...]}}}, paragraphs_kept, notes_after_split)."""
    chapters = {}
    paragraphs_kept = 0
    notes_after_split = 0
    with zipfile.ZipFile(IGNATIUS_DEUT_EPUB_PATH) as zf:
        txt = zf.read(IGNATIUS_DEUT_COMMENTARY_FILE).decode('utf-8', 'ignore')
        for m in IGNATIUS_DEUT_NOTE_RE.finditer(txt):
            chap_s, verse_s, lead_tail, body = m.group(1), m.group(2), m.group(3), m.group(4)
            paragraphs_kept += 1
            main_anchor = _clean_ignatius_anchor(re.sub(r'<[^>]+>', '', lead_tail).strip().rstrip(':').strip())
            for sub_label, sub_text in _deut_split_subglosses(body):
                anchor_word = sub_label if sub_label is not None else main_anchor
                html_body = sub_text or ''
                html_body = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', html_body, flags=re.S)
                html_body = re.sub(r'<[^>]+>', ' ', html_body)
                html_body = html_mod.unescape(html_body)
                html_body = re.sub(r'\s+', ' ', html_body).strip()
                html_body = re.sub(r'^[.:\s]+', '', html_body)
                if not html_body:
                    continue
                title = (f'Ignatius CSB — {chap_s}:{verse_s} ‘{anchor_word}’'
                         if anchor_word else f'Ignatius CSB — {chap_s}:{verse_s}')
                verses = chapters.setdefault(str(int(chap_s)), {})
                notes = verses.setdefault(str(int(verse_s)), [])
                notes.append({
                    'src': 'ignatius',
                    'tier': 'CATHOLIC IMPRIMATUR',
                    'kind': 'study',
                    'marker': f'{chap_s}:{verse_s}' + (f' / {sub_label}' if sub_label else ''),
                    'anchor_word': anchor_word,
                    'title': title,
                    'html': html_body,
                })
                notes_after_split += 1
    return {'deut': chapters}, paragraphs_kept, notes_after_split


# 1-2 Maccabees: a SIXTH shape, and the cleanest of the six -- a modern (2023) EPUB with
# self-documenting filenames (1-commentary.xhtml / 1-mac-study-q.xhtml, no guessing needed to
# separate commentary from Study Questions). One <p id="cvC-V"> per note, ref and any anchor word
# both inside a single <strong>C:V anchor:</strong>, body following in the same paragraph, closed
# with its own "<a href='...'>Back to text</a>." backlink -- ground-truthed: 0 duplicate ids in
# either book, chapter coverage 1-16 (1 Macc) and 1-15 (2 Macc) confirmed continuous. No
# secondary sub-gloss convention inside one note (unlike the other five families) -- each term
# that elsewhere would be a sub-gloss already gets its own separate <p>, confirmed by the id
# count already matching one id per distinct anchor rather than several packed into one paragraph.
IGNATIUS_MACC_EPUB_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Hahn, Scott;Mitch, Curtis;Walters, Dennis K ;Thomas, - The First and Second Books of the Maccabees (Ignatius (2023).epub"
)
IGNATIUS_MACC_NOTE_RE = re.compile(r'<p id="cv[^"]*"><strong>(\d+):(\d+)(?:[–-]\d+)?\s*([^<]*)</strong>(.*?)</p>', re.S)


def extract_ignatius_maccabees_notes(epub_path, commentary_file, book_id):
    chapters = {}
    paragraphs_kept = 0
    with zipfile.ZipFile(epub_path) as zf:
        txt = zf.read(commentary_file).decode('utf-8', 'ignore')
        for m in IGNATIUS_MACC_NOTE_RE.finditer(txt):
            chap_s, verse_s, lead_tail, body = m.group(1), m.group(2), m.group(3), m.group(4)
            paragraphs_kept += 1
            anchor_word = _clean_ignatius_anchor(re.sub(r'<[^>]+>', '', lead_tail).strip().rstrip(':').strip())
            html_body = re.sub(r'<a\b[^>]*>Back to text</a>\.?', '', body, flags=re.S)
            html_body = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', html_body, flags=re.S)
            html_body = re.sub(r'<[^>]+>', ' ', html_body)
            html_body = html_mod.unescape(html_body)
            html_body = re.sub(r'\s+', ' ', html_body).strip()
            html_body = re.sub(r'^[.:\s]+', '', html_body)
            if not html_body:
                continue
            title = (f'Ignatius CSB — {chap_s}:{verse_s} ‘{anchor_word}’'
                     if anchor_word else f'Ignatius CSB — {chap_s}:{verse_s}')
            verses = chapters.setdefault(str(int(chap_s)), {})
            notes = verses.setdefault(str(int(verse_s)), [])
            notes.append({
                'src': 'ignatius',
                'tier': 'CATHOLIC IMPRIMATUR',
                'kind': 'study',
                'marker': f'{chap_s}:{verse_s}',
                'anchor_word': anchor_word,
                'title': title,
                'html': html_body,
            })
    return {book_id: chapters}, paragraphs_kept, paragraphs_kept


# Genesis and Exodus ship as standalone Ignatius CSB volumes in PDF, not EPUB like every other
# book above -- so there's no <strong> tag to key a note-start off. Font name is the signal
# instead, same method as build_nabre_notes.py's bold-line-start detection. Page ranges verified
# by hand 2026-11-10 (see the Rule 12 session log entry): each volume's running Bible text is
# followed by a 'COMMENTARY' section (the real verse-by-verse notes we want), which is in turn
# followed by 'PARALLEL NOTES' / 'DOCTRINAL NOTES' / 'EXEGETICAL NOTES' sections -- cross-reference
# lists and RSV textual-variant apparatus, not Hahn/Mitch's own exegesis, so those are excluded by
# simply not including their pages in the range.
IGNATIUS_GEN_PDF_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Hahn, Scott & Mitch, Curtis - The Ignatius Catholic Study Bible Genesis (2011).pdf"
)
IGNATIUS_GEN_COMMENTARY_PAGES = (132, 217)  # [start, end) 0-indexed; page 132 'COMMENTARY' -> Gen 50:26 on page 216; page 217 is 'NOTES'/'PARALLEL NOTES'
IGNATIUS_EXOD_PDF_PATH = os.path.join(
    PDFS_IGNATIUS_DIR, "_AA_ Hahn, Scott & Mitch, Curtis - The Ignatius Catholic Study Bible Exodus.pdf"
)
IGNATIUS_EXOD_COMMENTARY_PAGES = (117, 176)  # page 117 'COMMENTARY' -> Exod 35-40 on page 175; page 177 is 'PARALLEL NOTES'

IGNATIUS_PDF_REF_RE = re.compile(r'^(\d+):(\d+)')
IGNATIUS_PDF_WORDSTUDY_REF_RE = re.compile(r'\((\d+):(\d+)\)')


def extract_ignatius_pdf_commentary(pdf_path, page_range, book_id):
    """Generic extractor for the Ignatius CSB standalone-volume PDFs (Genesis, Exodus so far).
    Each note opens with a bold chapter:verse, optionally a verse range (e.g. '1:1\u20142:25'),
    at the start of its paragraph, or a bold 'Word Study <lemma> (C:V)' box heading. Keys notes to
    the FIRST chapter:verse of any range, same simplification every other extractor in this file
    already makes."""
    import fitz
    start_page, end_page = page_range
    doc = fitz.open(pdf_path)
    stream = []  # (page, text, is_bold)
    note_starts = []  # (stream_idx, chap, verse, kind)
    for pno in range(start_page, min(end_page, doc.page_count)):
        d = doc[pno].get_text("dict")
        for block in d["blocks"]:
            for li, line in enumerate(block.get("lines", [])):
                spans = line.get("spans", [])
                if not spans:
                    continue
                line_start_idx = len(stream)
                for span in spans:
                    txt = span["text"]
                    if txt:
                        stream.append((txt, "Bold" in span["font"]))
                # PDF line-wraps don't carry a trailing space in the span text itself (e.g. "...
                # consists" / "of a wordplay..." on consecutive lines) -- without this the stream
                # join below would glue them into "consistsof". A run of whitespace already at the
                # line's own end (normal mid-sentence spacing PyMuPDF does preserve) just gets
                # collapsed by the final re.sub(r'\s+', ' ', ...) pass, so this is safe either way.
                stream.append((' ', False))
                if li != 0:
                    continue
                s0 = spans[0]
                if "Bold" not in s0["font"]:
                    continue
                m = IGNATIUS_PDF_REF_RE.match(s0["text"].strip())
                if m:
                    note_starts.append((line_start_idx, int(m.group(1)), int(m.group(2)), 'study'))
                    continue
                line_text = ''.join(s['text'] for s in spans).strip()
                if line_text.startswith('Word Study'):
                    wm = IGNATIUS_PDF_WORDSTUDY_REF_RE.search(line_text)
                    if wm:
                        note_starts.append((line_start_idx, int(wm.group(1)), int(wm.group(2)), 'word_study'))
    doc.close()

    chapters = {}
    for i, (start_idx, chap, verse, kind) in enumerate(note_starts):
        end_idx = note_starts[i + 1][0] if i + 1 < len(note_starts) else len(stream)
        segment = stream[start_idx:end_idx]
        body_text = ''.join(t for (t, _) in segment)
        lead_bold_len = 0
        for (t, is_bold) in segment:
            if is_bold:
                lead_bold_len += len(t)
            else:
                break
        if kind == 'word_study':
            # Only the "Word Study" label itself is bold on these headings -- the lemma and the
            # (C:V) that follow it on the same line are normal weight, so lead_bold_len can't be
            # trusted to find the lemma boundary here. Match the whole heading in body_text instead.
            hm = re.match(r'^\s*Word Study\s+(.*?)\s*\(\s*\d+\s*:\s*\d+\s*\)\s*', body_text)
            if hm:
                anchor_word = hm.group(1).strip()
                rest = body_text[hm.end():].strip()
            else:
                anchor_word = ''
                rest = re.sub(r'^\s*Word Study\s*', '', body_text).strip()
            title = f'Ignatius CSB Word Study — ‘{anchor_word}’' if anchor_word else 'Ignatius CSB Word Study'
        else:
            lead_bold_len = 0
            for (t, is_bold) in segment:
                if is_bold:
                    lead_bold_len += len(t)
                else:
                    break
            lemma_raw = body_text[:lead_bold_len].strip()
            rest = body_text[lead_bold_len:].strip()
            lemma_m = re.match(r'^[\d:\u2012\u2013\u2014,\s-]+(.*)$', lemma_raw)
            anchor_word = (lemma_m.group(1).strip(' :') if lemma_m else '').strip()
            title = (f'Ignatius CSB — {chap}:{verse} ‘{anchor_word}’'
                     if anchor_word else f'Ignatius CSB — {chap}:{verse}')
        rest = re.sub(r'\s*Back to\s*text\.?\s*$', '', rest).strip()
        rest = re.sub(r'\s+', ' ', rest)
        if not rest:
            continue
        chapters.setdefault(str(chap), {}).setdefault(str(verse), []).append({
            'src': 'ignatius',
            'tier': 'CATHOLIC IMPRIMATUR',
            'kind': kind,
            'marker': f'{book_id}-{chap}-{verse}-{i}',
            'anchor_word': anchor_word,
            'title': title,
            'html': rest,
        })
    return chapters


def _merge_chapters(base, extra):
    """Merge extra's {chapter: {verse: [notes]}} into base in place."""
    for chap, verses in extra.items():
        base_verses = base.setdefault(chap, {})
        for verse, notes in verses.items():
            base_verses.setdefault(verse, []).extend(notes)


def main():
    if not os.path.isfile(NET_EPUB_PATH):
        raise SystemExit(f'NET Bible epub not found at {NET_EPUB_PATH}')

    per_book_chapters = {}

    with zipfile.ZipFile(NET_EPUB_PATH) as zf:
        all_ranges = load_net_book_file_ranges(zf)
        if len(all_ranges) != len(NET_LABEL_TO_BOOK_ID):
            raise AssertionError(f'Expected {len(NET_LABEL_TO_BOOK_ID)} NET books (OT+NT), resolved {len(all_ranges)}')

        net_total = 0
        for book_id, files in all_ranges:
            chapters = extract_net_notes_for_book(zf, files)
            net_total += sum(len(notes) for chs in chapters.values() for notes in chs.values())
            per_book_chapters[book_id] = chapters
        print(f'NET 2.1: {net_total} notes extracted across {len(all_ranges)} books (OT+NT, was NT-only until 2026-11-10).')

    ignatius_total = 0
    ignatius_paragraphs = 0
    if os.path.isfile(IGNATIUS_NT_EPUB_PATH):
        with zipfile.ZipFile(IGNATIUS_NT_EPUB_PATH) as zf:
            raw = zf.read('OEBPS/page-1.html').decode('utf-8', errors='ignore')
        ig_chapters_by_book, paragraphs_kept, notes_after_split, skipped_non_verse, skipped_unknown_prefix = extract_ignatius_nt_notes(raw)
        for book_id, chapters in ig_chapters_by_book.items():
            _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters)
        ignatius_total = notes_after_split
        ignatius_paragraphs = paragraphs_kept
        print(f'Ignatius CSB NT: {paragraphs_kept} source paragraphs kept -> {notes_after_split} notes '
              f'after splitting Hahn/Mitch\'s own inline <b>phrase:</b> sub-headers into separate '
              f'indicator-able notes, {skipped_non_verse} non-verse section headers skipped '
              f'(book intros/Word Study/etc.), {skipped_unknown_prefix} unrecognized cross-ref '
              f'prefixes skipped.')
    else:
        print(f'Warning: Ignatius NT epub not found at {IGNATIUS_NT_EPUB_PATH} — NET-only shards written.')

    sbl_total = 0
    if os.path.isfile(SBL_EPUB_PATH):
        sbl_chapters_by_book, sbl_total = extract_sbl_notes()
        for book_id, chapters in sbl_chapters_by_book.items():
            _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters)
        print(f'SBL Study Bible (full 66-book canon): {sbl_total} notes extracted across {len(sbl_chapters_by_book)} books.')
    else:
        print(f'Warning: SBL Study Bible epub not found at {SBL_EPUB_PATH} — shards written without it.')

    noab_total = 0
    if os.path.isfile(NOAB_EPUB_PATH):
        noab_chapters_by_book, noab_total, noab_missing = extract_noab_notes()
        for book_id, chapters in noab_chapters_by_book.items():
            _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters)
        print(f'NOAB (New Oxford Annotated Bible, 66-book canon + 6 Deuterocanon): {noab_total} notes extracted '
              f'across {len(noab_chapters_by_book)} books. Missing from this epub copy: {noab_missing}')

        noab_addl_chapters_by_book, noab_addl_total = extract_noab_greek_additions()
        for book_id, chapters in noab_addl_chapters_by_book.items():
            _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters)
        noab_total += noab_addl_total
        print(f'NOAB Esther-Greek + Daniel additions (Prayer of Azariah/Song of Three Jews, Susanna, '
              f'Bel and the Dragon): {noab_addl_total} notes extracted, aligned to the suite\'s own '
              f'DRA-based chapter/verse scheme.')
    else:
        print(f'Warning: NOAB epub not found at {NOAB_EPUB_PATH} — shards written without it.')

    niv_total = 0
    if os.path.isfile(NIV_EPUB_PATH):
        niv_chapters_by_book, niv_total, niv_paragraphs = extract_niv_notes()
        for book_id, chapters in niv_chapters_by_book.items():
            _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters)
        print(f'NIV Study Bible (full 66-book canon): {niv_paragraphs} source paragraphs -> {niv_total} notes after '
              f'splitting inline <i>lemma.</i> sub-headers, across {len(niv_chapters_by_book)} books.')
    else:
        print(f'Warning: NIV Study Bible epub not found at {NIV_EPUB_PATH} — shards written without it.')

    dan_total = 0
    if os.path.isfile(IGNATIUS_DANIEL_EPUB_PATH):
        dan_chapters_by_book, dan_paragraphs, dan_total = extract_ignatius_daniel_notes()
        _merge_chapters(per_book_chapters.setdefault('dan', {}), dan_chapters_by_book['dan'])
        print(f'Ignatius CSB Daniel (OT, first Pass-4 OT book): {dan_paragraphs} source paragraphs '
              f'-> {dan_total} notes after splitting inline sub-headers.')
    else:
        print(f'Warning: Ignatius Daniel epub not found at {IGNATIUS_DANIEL_EPUB_PATH} — shards written without it.')

    boldlink_jobs = [
        (IGNATIUS_JOSHUA_EPUB_PATH, IGNATIUS_JOSHUA_COMMENTARY_FILES, 'josh', 'Joshua'),
        (IGNATIUS_JUDGES_RUTH_EPUB_PATH, IGNATIUS_JUDGES_COMMENTARY_FILES, 'judg', 'Judges'),
        (IGNATIUS_JUDGES_RUTH_EPUB_PATH, IGNATIUS_RUTH_COMMENTARY_FILES, 'ruth', 'Ruth'),
        (IGNATIUS_ISAIAH_EPUB_PATH, IGNATIUS_ISAIAH_COMMENTARY_FILES, 'isa', 'Isaiah'),
        (IGNATIUS_KINGS_EPUB_PATH, IGNATIUS_1KGS_COMMENTARY_FILES, '1kgs', '1 Kings'),
        (IGNATIUS_KINGS_EPUB_PATH, IGNATIUS_2KGS_COMMENTARY_FILES, '2kgs', '2 Kings'),
        (IGNATIUS_TJE_EPUB_PATH, IGNATIUS_TOB_COMMENTARY_FILES, 'tob', 'Tobit'),
        (IGNATIUS_TJE_EPUB_PATH, IGNATIUS_JDT_COMMENTARY_FILES, 'jdt', 'Judith'),
        (IGNATIUS_TJE_EPUB_PATH, IGNATIUS_ESTH_COMMENTARY_FILES, 'esth', 'Esther'),
    ]
    boldlink_total = 0
    for epub_path, files, book_id, label in boldlink_jobs:
        if not os.path.isfile(epub_path):
            print(f'Warning: {label} epub not found at {epub_path} — shards written without it.')
            continue
        chapters_by_book, paragraphs, note_count = extract_ignatius_boldlink_notes(epub_path, files, book_id)
        _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters_by_book[book_id])
        boldlink_total += note_count
        print(f'Ignatius CSB {label} (OT): {paragraphs} source paragraphs -> {note_count} notes after splitting inline sub-headers.')

    boldplain_jobs = [
        (IGNATIUS_PES_EPUB_PATH, IGNATIUS_PROV_COMMENTARY_FILES, 'prov', 'Proverbs'),
        (IGNATIUS_PES_EPUB_PATH, IGNATIUS_ECCL_COMMENTARY_FILES, 'eccl', 'Ecclesiastes'),
        (IGNATIUS_PES_EPUB_PATH, IGNATIUS_SONG_COMMENTARY_FILES, 'song', 'Song of Solomon'),
    ]
    for epub_path, files, book_id, label in boldplain_jobs:
        if not os.path.isfile(epub_path):
            print(f'Warning: {label} epub not found at {epub_path} — shards written without it.')
            continue
        chapters_by_book, paragraphs, note_count = extract_ignatius_boldplain_notes(epub_path, files, book_id)
        _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters_by_book[book_id])
        boldlink_total += note_count
        print(f'Ignatius CSB {label} (OT): {paragraphs} source paragraphs -> {note_count} notes after splitting inline sub-headers.')

    deut_total = 0
    if os.path.isfile(IGNATIUS_DEUT_EPUB_PATH):
        deut_chapters_by_book, deut_paragraphs, deut_total = extract_ignatius_deut_notes()
        _merge_chapters(per_book_chapters.setdefault('deut', {}), deut_chapters_by_book['deut'])
        print(f'Ignatius CSB Deuteronomy (OT): {deut_paragraphs} source paragraphs -> {deut_total} notes after splitting inline sub-headers.')
    else:
        print(f'Warning: Deuteronomy epub not found at {IGNATIUS_DEUT_EPUB_PATH} — shards written without it.')

    macc_total = 0
    macc_jobs = [
        (IGNATIUS_MACC_EPUB_PATH, 'OEBPS/1-commentary.xhtml', '1macc', '1 Maccabees'),
        (IGNATIUS_MACC_EPUB_PATH, 'OEBPS/2-commentary.xhtml', '2macc', '2 Maccabees'),
    ]
    for epub_path, commentary_file, book_id, label in macc_jobs:
        if not os.path.isfile(epub_path):
            print(f'Warning: {label} epub not found at {epub_path} — shards written without it.')
            continue
        chapters_by_book, paragraphs, note_count = extract_ignatius_maccabees_notes(epub_path, commentary_file, book_id)
        _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters_by_book[book_id])
        macc_total += note_count
        print(f'Ignatius CSB {label} (OT): {paragraphs} source paragraphs -> {note_count} notes (no sub-gloss splitting needed in this epub).')

    pdf_total = 0
    pdf_jobs = [
        (IGNATIUS_GEN_PDF_PATH, IGNATIUS_GEN_COMMENTARY_PAGES, 'gen', 'Genesis'),
        (IGNATIUS_EXOD_PDF_PATH, IGNATIUS_EXOD_COMMENTARY_PAGES, 'exod', 'Exodus'),
    ]
    for pdf_path, page_range, book_id, label in pdf_jobs:
        if not os.path.isfile(pdf_path):
            print(f'Warning: {label} PDF not found at {pdf_path} — shards written without it.')
            continue
        chapters = extract_ignatius_pdf_commentary(pdf_path, page_range, book_id)
        note_count = sum(len(notes) for chs in chapters.values() for notes in chs.values())
        _merge_chapters(per_book_chapters.setdefault(book_id, {}), chapters)
        pdf_total += note_count
        print(f'Ignatius CSB {label} (OT, PDF volume): {note_count} notes extracted from the bold-C:V commentary section (pages {page_range[0]}-{page_range[1]-1}).')

    written = []
    total_notes = 0
    for book_id, chapters in per_book_chapters.items():
        note_count = sum(len(notes) for chs in chapters.values() for notes in chs.values())
        total_notes += note_count
        payload = {'book_id': book_id, 'chapters': chapters}
        out_path = os.path.join(OUT_DIR, f'{book_id}.js')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"window.__PLENARY_LOAD_BOOK_NOTES({json.dumps(book_id)}, {json.dumps(payload, ensure_ascii=False)});\n")
        written.append((book_id, note_count, os.path.getsize(out_path)))

    print(f'\nCombined (NET {net_total} + Ignatius NT {ignatius_total} + SBL {sbl_total} + NOAB {noab_total} + NIV SB {niv_total} + Ignatius Dan(OT) {dan_total} + Ignatius Josh/Judg/Ruth/Isa/1-2Kgs/Tob/Jdt/Esth/Prov/Eccl/Song(OT) {boldlink_total} + Ignatius Deut(OT) {deut_total} + Ignatius 1-2Macc(OT) {macc_total} + Ignatius Gen/Exod(OT, PDF) {pdf_total}) = {total_notes} total notes across {len(written)} books.')
    for book_id, note_count, size in written:
        print(f'  {book_id:8s} {note_count:5d} notes  {size:8d} B  -> notes_shards/{book_id}.js')


if __name__ == '__main__':
    main()
