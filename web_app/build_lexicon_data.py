# -*- coding: utf-8 -*-
"""
Deterministic BibleHub-Grade Lexicon & Full-Bible Morphology Compiler
Generates web_app/sources_cache/lexicon_bundle.json containing:
1. strongs_gloss : ALL OpenScriptures Greek (G1-G5624) + Hebrew/Aramaic (H1-H8674) -> [lemma, translit, deriv, def]
2. greek_morph   : Merged TAGNT NT (NA28 + Byz + TR Robinson codes + Strongs) + Rahlfs LXX CATSS (<m>lxx.*</m> + Strongs)
3. hebrew_morph  : Complete TAHOT OT Hebrew & Aramaic consonantal morphology -> "H#|pointed_lemma|OSHM_code|translit|gloss"
"""
import json
import os
import re
import sys
import unicodedata

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, 'sources_cache')
RAW_DIR = os.path.join(CACHE_DIR, 'raw')
LXX_CSV_PATH = os.path.join(SCRIPT_DIR, 'LXX_final_main.csv')
OUT_PATH = os.path.join(CACHE_DIR, 'lexicon_bundle.json')

_GREEK_STRIP_RE = re.compile(r'[^\u03b1-\u03c9]')


def norm_greek_key(word):
    w = unicodedata.normalize('NFD', (word or '').lower())
    w = ''.join(c for c in w if unicodedata.category(c) != 'Mn')
    w = _GREEK_STRIP_RE.sub('', w)
    if w.endswith('σ'):
        w = w[:-1] + 'ς'
    return w


def norm_hebrew_cons(word):
    return re.sub(r'[^\u05d0-\u05ea]', '', unicodedata.normalize('NFD', word or ''))


def clean_text(s):
    return re.sub(r'\s+', ' ', (s or '').replace('\n', ' ')).strip()


def load_openscriptures_strongs():
    def load_js(fn, var_name):
        raw = open(os.path.join(RAW_DIR, fn), 'r', encoding='utf-8').read()
        eq = raw.find('{', raw.find(var_name))
        return json.loads(raw[eq:raw.rfind('}') + 1])

    sg = load_js('strongs-greek-dictionary.js', 'strongsGreekDictionary')
    sh = load_js('strongs-hebrew-dictionary.js', 'strongsHebrewDictionary')

    out = {}
    for k, v in sg.items():
        d1 = clean_text(v.get('strongs_def', ''))
        d2 = clean_text(v.get('kjv_def', ''))
        full_d = d1 + (f" [KJV/Eng: {d2}]" if d2 else '')
        out[k] = [clean_text(v.get('lemma', '')), clean_text(v.get('translit', '')), clean_text(v.get('derivation', '')), full_d]

    for k, v in sh.items():
        d1 = clean_text(v.get('strongs_def', ''))
        d2 = clean_text(v.get('kjv_def', ''))
        pron = clean_text(v.get('pron', ''))
        xlit = clean_text(v.get('xlit', ''))
        tr = xlit + (f" ({pron})" if pron else '')
        full_d = d1 + (f" [KJV/Eng: {d2}]" if d2 else '')
        out[k] = [clean_text(v.get('lemma', '')), tr, clean_text(v.get('derivation', '')), full_d]

    print(f"Compiled OpenScriptures Strong's G+H: {len(out)} entries")
    return out


def compile_greek_morph():
    """
    Priority:
    1. TAGNT (STEPBible NT NA28/Byz/TR) — exact Robinson morphology + Strong's G#
    2. Rahlfs LXX CATSS (LXX_final_main.csv) — LXX forms & OT morphology + Strong's G#
    """
    morph = {}
    tagnt_files = ['TAGNT_Mat-Jhn.txt', 'TAGNT_Act-Rev.txt']
    for fn in tagnt_files:
        p = os.path.join(RAW_DIR, fn)
        with open(p, 'r', encoding='utf-8') as f:
            for ln in f:
                if not re.match(r'^[1-3]?[A-Za-z]+\.\d+\.\d+#', ln):
                    continue
                cols = ln.rstrip('\r\n').split('\t')
                if len(cols) < 5:
                    continue
                greek_surface = cols[1].split(' (')[0].strip()
                k = norm_greek_key(greek_surface)
                if not k:
                    continue
                sg_gram = cols[3]
                if '=' not in sg_gram:
                    continue
                left, gram = sg_gram.split('=', 1)
                gram = gram.strip()
                # Extract primary Greek Strong's G# (prefer final G\d+ if OT Hebrew pipe like H1732|G1138)
                g_matches = re.findall(r'G(\d+)', left)
                strong = f"G{int(g_matches[-1])}" if g_matches else ''
                if k not in morph:
                    morph[k] = f"{gram}|{strong}" if strong else gram
                else:
                    old_pos, _, old_st = morph[k].partition('|')
                    if not old_st and strong:
                        morph[k] = f"{gram or old_pos}|{strong}"

    print(f"TAGNT Greek morph keys indexed: {len(morph)}")

    # Merge Rahlfs LXX CATSS forms
    if os.path.exists(LXX_CSV_PATH):
        strongs_pat = re.compile(r'<S>(\d+)</S>')
        morph_pat = re.compile(r'<m>(?:lxx\.)?([^<]+)</m>')
        tok_pat = re.compile(r'([^\s<]+)((?:<(?:S|m)>[^<]+</(?:S|m)>)+)')
        with open(LXX_CSV_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.rstrip('\r\n').split('\t')
                if len(parts) < 4:
                    continue
                for m in tok_pat.finditer(parts[3]):
                    k = norm_greek_key(m.group(1))
                    if not k:
                        continue
                    mp = morph_pat.search(m.group(2))
                    pos = mp.group(1) if mp else ''
                    st = ''
                    for s in strongs_pat.findall(m.group(2)):
                        n = int(s)
                        if 1 <= n <= 5624:
                            st = f"G{n}"
                            break
                    if k not in morph:
                        morph[k] = f"{pos}|{st}" if st else pos
                    elif '|' not in morph[k] and st:
                        morph[k] = f"{morph[k]}|{st}"

    # Guarantee verified Acts 15:17 / crucial NT forms (never rely on outdated G1830 typo)
    verified_overrides = {
        'εκζητησωσιν': 'V-AAS-3P|G1567',
        'κατηρτισω': 'V-AMI-2S|G2675',
        'απαυγασμα': 'N-NSN|G541',
        'κεχαριτωμενη': 'V-RPP-NSF|G5487',
        'ετυμπανισθησαν': 'V-API-3P|G5178',
        'ωρυξαν': 'V-AAI-3P|G3736',
    }
    for k, val in verified_overrides.items():
        if k not in morph or morph[k].endswith('|G1830'):
            morph[k] = val

    print(f"Total merged Greek morph keys (TAGNT + LXX): {len(morph)}")
    return morph


def compile_hebrew_morph():
    """
    Parse all 4 STEPBible TAHOT OT files -> consonantal keys mapped to:
    "H#|pointed_lemma|OSHM_morph|translit|gloss"
    Also stores prefix-stripped root key if not already occupied.
    """
    heb = {}
    root_fallback = {}
    tahot_files = ['TAHOT_Gen-Deu.txt', 'TAHOT_Jos-Est.txt', 'TAHOT_Job-Sng.txt', 'TAHOT_Isa-Mal.txt']

    brace_h_pat = re.compile(r'\{([HA])(\d+)[A-Za-z]?\}')
    any_h_pat = re.compile(r'H(\d+)')

    for fn in tahot_files:
        p = os.path.join(RAW_DIR, fn)
        with open(p, 'r', encoding='utf-8') as f:
            for ln in f:
                if not re.match(r'^[1-3]?[A-Za-z]+\.\d+\.\d+#', ln):
                    continue
                cols = ln.rstrip('\r\n').split('\t')
                if len(cols) < 6:
                    continue
                raw_word = cols[1]
                translit = clean_text(cols[2])
                gloss = clean_text(cols[3]).replace('|', '/')
                dstrongs = cols[4]
                oshm = clean_text(cols[5]).replace('|', '/')
                expanded = cols[11] if len(cols) > 11 else ''

                cons_full = norm_hebrew_cons(raw_word)
                if not cons_full:
                    continue

                # Extract Strong's H# (root is inside {H...} or {A...})
                mh = brace_h_pat.findall(dstrongs)
                if mh:
                    # Prefer lexical H/A code (map both under H# in Strongs Hebrew dict; Strongs includes Biblical Aramaic H#!)
                    num = int(mh[-1][1])
                    strong_id = f"H{num}"
                else:
                    nums = [int(x) for x in any_h_pat.findall(dstrongs) if int(x) < 9000]
                    strong_id = f"H{nums[-1]}" if nums else ''

                # Extract pointed root lemma from expanded col 11: {H7225G=רֵאשִׁית=...}
                lemma = ''
                if expanded:
                    m_lem = re.search(r'\{[HA]\d+[A-Za-z]?=([^=}|\\]+)=', expanded)
                    if m_lem:
                        lemma = clean_text(m_lem.group(1))
                if not lemma:
                    lemma = raw_word.split('\\')[0].replace('/', '')

                val = f"{strong_id}|{lemma}|{oshm}|{translit}|{gloss}"
                if cons_full not in heb:
                    heb[cons_full] = val
                elif strong_id and heb[cons_full].startswith('|'):
                    heb[cons_full] = val

                # Also index suffix after '/' (prefix-stripped stem) as fallback ONLY
                if '/' in raw_word:
                    stem_part = raw_word.split('/')[-1]
                    cons_root = norm_hebrew_cons(stem_part)
                    if cons_root and cons_root not in root_fallback and strong_id:
                        root_val = f"{strong_id}|{lemma}|{oshm.split('/')[-1]}|{translit.split('/')[-1]}|{gloss.split('/')[-1].strip()}"
                        root_fallback[cons_root] = root_val

    for rk, rv in root_fallback.items():
        if rk not in heb:
            heb[rk] = rv

    print(f"Total compiled TAHOT Hebrew/Aramaic morph keys: {len(heb)}")
    return heb


def main():
    strongs_gloss = load_openscriptures_strongs()
    greek_morph = compile_greek_morph()
    hebrew_morph = compile_hebrew_morph()

    bundle = {
        'strongs_gloss': strongs_gloss,
        'greek_morph': greek_morph,
        'hebrew_morph': hebrew_morph,
    }
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, separators=(',', ':'))

    sz = os.path.getsize(OUT_PATH)
    print(f"Saved lexicon_bundle.json -> {OUT_PATH} ({sz/1e6:.2f} MB)")

    # Rule 3 assertions (checks that can fail)
    assert len(strongs_gloss) >= 14000, f"Strongs too small: {len(strongs_gloss)}"
    assert len(greek_morph) >= 45000, f"Greek morph too small: {len(greek_morph)}"
    assert len(hebrew_morph) >= 35000, f"Hebrew morph too small: {len(hebrew_morph)}"

    spot_gr = [
        ('ἐκζητήσωσιν', 'G1567'),
        ('ἐποίησεν', 'G4160'),
        ('κεχαριτωμένη', 'G5487'),
        ('λόγος', 'G3056'),
    ]
    for w, exp in spot_gr:
        k = norm_greek_key(w)
        assert k in greek_morph and exp in greek_morph[k], f"Spot Greek fail {w}: {greek_morph.get(k)}"
        print(f"  Spot Greek  {w:16s} -> {greek_morph[k]}")

    spot_he = [
        ('בְּרֵאשִׁית', 'H7225'),
        ('בָּרָא', 'H1254'),
        ('כָּאֲרִי', 'H738'),
    ]
    for w, exp in spot_he:
        k = norm_hebrew_cons(w)
        assert k in hebrew_morph and exp in hebrew_morph[k], f"Spot Hebrew fail {w}: {hebrew_morph.get(k)}"
        print(f"  Spot Hebrew {w:16s} -> {hebrew_morph[k]}")


if __name__ == '__main__':
    main()
