# -*- coding: utf-8 -*-
"""
Builder for the Comprehensive 73-Book Plenary Scripture Workstation:
'The Logos-Grade Russian Doll Multi-Witness Suite'
Features:
- Complete 73-book Catholic Canon (all 35,811 verses in Church-approved Imprimatur DRA + In-House Ignatius RSV-2CE + Vatican Nova Vulgata + Sixto-Clementine Vulgate + Greek Septuagint LXX + Critical GNT + Byzantine RP + Textus Receptus + Hebrew Masoretic WLC + Brenton LXX + WEB-C + KJVA + ASV 1901)
- Real 3D Three.js holographic spatial model with dynamic canvas text rendering onto up to 12+ summonable strata planes, VR Arc curved layout, WebXR readiness probe, and live 3D word-click raycasting
- Multi-pane synchronized workspace (73-book canon tree, instant full-Bible search across 73 books, Russian Dolls reader, 4-column switchable synoptic parallel viewer)
- BibleHub-grade Morphology & Strong's Inspector (14,197 OpenScriptures Greek+Hebrew/Aramaic Strong's definitions, 52k+ TAGNT/LXX Greek morph, 42k+ STEPBible TAHOT Hebrew/Aramaic morph, DRA Strong's alignment links, 73-book concordance)
- Local personal notes and highlights persistence (localStorage) + Discord Apologetics Card generator
"""

import json
import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(SCRIPT_DIR, 'sources_cache')

# Approved Catholic & Benchmark Corpora (cached offline JSONs)
DRA_PATH = os.path.join(CACHE_DIR, 'DRA.json')
RSV2CE_PATH = os.path.join(CACHE_DIR, 'RSV2CE.json')
NV_PATH = os.path.join(CACHE_DIR, 'NovaVulgata.json')
WEBC_PATH = os.path.join(CACHE_DIR, 'WEBC.json')
BRENTON_PATH = os.path.join(CACHE_DIR, 'BrentonLXX.json')
KJVA_PATH = os.path.join(CACHE_DIR, 'KJVA.json')
ASV_PATH = os.path.join(CACHE_DIR, 'ASV.json')
BYZ_PATH = os.path.join(CACHE_DIR, 'Byz.json')
TR_PATH = os.path.join(CACHE_DIR, 'TR.json')
NET21_PATH = os.path.join(CACHE_DIR, 'NET21.json')
NIV11_PATH = os.path.join(CACHE_DIR, 'NIV11.json')
BSB_PATH = os.path.join(CACHE_DIR, 'BSB.json')

# Core Primary Manuscripts
VULG_PATH = os.path.join(SCRIPT_DIR, 'VulgClementine.json')
GNT_PATH = os.path.join(SCRIPT_DIR, 'StatResGNT.json')
WLC_PATH = os.path.join(SCRIPT_DIR, 'WLC.json')
LXX_PATH = os.path.join(SCRIPT_DIR, 'LXX_clean.json')
LXX_CSV_PATH = os.path.join(SCRIPT_DIR, 'LXX_final_main.csv')

# BibleHub-grade Lexicon & Alignment Bundles
LEXICON_BUNDLE_PATH = os.path.join(CACHE_DIR, 'lexicon_bundle.json')
DRA_LINKS_PATH = os.path.join(CACHE_DIR, 'dra_strongs_links.json')

LUCIDE_JS_PATH = os.path.join(SCRIPT_DIR, 'lucide.min.js')
TAILWIND_CSS_PATH = os.path.join(SCRIPT_DIR, 'tailwind_compiled.css')
JSON_OUT = os.path.join(SCRIPT_DIR, 'plenary_logos_data.json')
HTML_OUT = os.path.join(SCRIPT_DIR, 'plenary_logos_suite.html')

TRANSLATION_REGISTRY = [
    {
        "id": "dra", "short": "DRA", "name": "Challoner Douay-Rheims (DRA)",
        "lang": "en", "scope": "73 Books", "approval": "IMPRIMATUR",
        "tier_badge": "IMPRIMATUR", "group": "catholic", "color": "#fbbf24",
        "default_3d": True, "is_master_en": True,
        "notes": "Official Challoner Douay-Rheims Catholic Bible with bishop's Imprimatur; default Master English stream."
    },
    {
        "id": "rsv2ce", "short": "RSV-2CE", "name": "Ignatius Catholic Study Bible (RSV-2CE)",
        "lang": "en", "scope": "45 Born-Digital Books", "approval": "IMPRIMATUR_INHOUSE",
        "tier_badge": "IMPRIMATUR [IN-HOUSE]", "group": "catholic", "color": "#f59e0b",
        "default_3d": False, "is_master_en": True,
        "notes": "RSV Second Catholic Edition (Ignatius Study Bible); falls back cleanly to DRA [Imprimatur] on uncovered OT books."
    },
    {
        "id": "nova_vulg", "short": "Nova Vulg.", "name": "Vatican Nova Vulgata (Editio Typica)",
        "lang": "la", "scope": "73 Books", "approval": "PAPAL_TYPICA",
        "tier_badge": "PAPAL EDITIO TYPICA", "group": "catholic", "color": "#e879f9",
        "default_3d": False, "is_master_en": False,
        "notes": "Liturgical Latin editio typica promulgata by Pope St. John Paul II (1979/1986); embeds Esther Additions inline [1a]–[10a]."
    },
    {
        "id": "vulg_clem", "short": "Clementine", "name": "Sixto-Clementine Vulgate (1592)",
        "lang": "la", "scope": "73 Books", "approval": "PAPAL_TRENT",
        "tier_badge": "PAPAL/TRENT STANDARD", "group": "catholic", "color": "#c084fc",
        "default_3d": True, "is_master_en": False,
        "notes": "Council of Trent authentic Latin standard preserving St. Jerome's Gallican Psalter and Old Testament translations."
    },
    {
        "id": "lxx_gnt", "short": "LXX + GNT", "name": "Rahlfs 1935 LXX & Critical Greek NT",
        "lang": "gr", "scope": "73 Books (OT LXX / NT GNT)", "approval": "ANCIENT_MSS",
        "tier_badge": "ANCIENT MSS", "group": "ancient", "color": "#38bdf8",
        "default_3d": True, "is_master_en": False,
        "notes": "Rahlfs-Hanhart Greek Septuagint for OT/Deuterocanon paired with Statistical Restoration Critical Greek NT."
    },
    {
        "id": "byz", "short": "Byzantine", "name": "Byzantine Majority NT (Robinson-Pierpont)",
        "lang": "gr", "scope": "27 NT Books", "approval": "ANCIENT_MSS",
        "tier_badge": "ANCIENT MSS (BYZ NT)", "group": "ancient", "color": "#22d3ee",
        "default_3d": False, "is_master_en": False,
        "notes": "Ecclesiastical Byzantine Majority textform underlying Eastern Orthodox liturgical lectionaries."
    },
    {
        "id": "tr", "short": "Textus Rec.", "name": "Textus Receptus Greek NT (Scrivener)",
        "lang": "gr", "scope": "27 NT Books", "approval": "ANCIENT_MSS",
        "tier_badge": "TRADITIONAL NT", "group": "ancient", "color": "#2dd4bf",
        "default_3d": False, "is_master_en": False,
        "notes": "16th-century printed Greek New Testament baseline (Stephanus/Scrivener) behind KJV & Protestant translations."
    },
    {
        "id": "wlc", "short": "Hebrew WLC", "name": "Westminster Leningrad Codex (MT)",
        "lang": "he", "scope": "39 OT Books", "approval": "ANCIENT_MSS",
        "tier_badge": "MASORETIC MT", "group": "ancient", "color": "#f87171",
        "default_3d": True, "is_master_en": False,
        "notes": "Pointed Masoretic Hebrew/Aramaic consonantal stream aligned to Catholic Vulgate Psalm/Joel/Malachi numbering."
    },
    {
        "id": "brenton", "short": "Brenton LXX", "name": "Brenton English Septuagint",
        "lang": "en", "scope": "46 OT+DC Books", "approval": "BENCHMARK",
        "tier_badge": "LXX BENCHMARK", "group": "benchmark", "color": "#34d399",
        "default_3d": False, "is_master_en": True,
        "notes": "English translation of Codex Vaticanus Greek Septuagint; shows LXX Vorlage readings directly in English."
    },
    {
        "id": "webc", "short": "WEB-C", "name": "World English Bible Catholic Edition",
        "lang": "en", "scope": "73 Books", "approval": "BENCHMARK",
        "tier_badge": "ECUMENICAL BENCHMARK", "group": "benchmark", "color": "#60a5fa",
        "default_3d": False, "is_master_en": True,
        "notes": "Public-domain modern English translation covering the full 73-book Catholic canon."
    },
    {
        "id": "kjva", "short": "KJVA (1611)", "name": "King James Version w/ Apocrypha",
        "lang": "en", "scope": "73 Books", "approval": "BENCHMARK",
        "tier_badge": "HISTORICAL BENCHMARK", "group": "benchmark", "color": "#a78bfa",
        "default_3d": False, "is_master_en": True,
        "notes": "Protestant Authorized Version (1611/1769) including its Apocrypha section for historical Protestant comparison."
    },
    {
        "id": "asv", "short": "ASV 1901", "name": "American Standard Version (1901)",
        "lang": "en", "scope": "66 Books", "approval": "BENCHMARK",
        "tier_badge": "66-BOOK BENCHMARK", "group": "benchmark", "color": "#94a3b8",
        "default_3d": False, "is_master_en": True,
        "notes": "Protestant 66-book formal-equivalence baseline (excludes Deuterocanon; useful to highlight Axis A canon omissions)."
    },
    {
        "id": "net21", "short": "NET 2.1", "name": "New English Translation (NET Bible 2.1)",
        "lang": "en", "scope": "66 Books", "approval": "BENCHMARK",
        "tier_badge": "66-BOOK BENCHMARK", "group": "benchmark", "color": "#67e8f9",
        "default_3d": False, "is_master_en": True,
        "notes": "Protestant/academic translation whose own tn/tc/sn translator, text-critical, and study notes are already surfaced in Doll 6 — this stream is its verse text, so the Parallel view can show the two side by side."
    },
    {
        "id": "niv_sb", "short": "NIV SB", "name": "New International Version (NIV Study Bible)",
        "lang": "en", "scope": "66 Books", "approval": "BENCHMARK",
        "tier_badge": "66-BOOK BENCHMARK", "group": "benchmark", "color": "#fda4af",
        "default_3d": False, "is_master_en": True,
        "notes": "Evangelical study-Bible translation; its own Study Notes are already surfaced in Doll 6 under the same niv_sb source."
    },
    {
        "id": "bsb", "short": "BSB", "name": "Berean Standard Bible (BSB)",
        "lang": "en", "scope": "66 Books", "approval": "BENCHMARK",
        "tier_badge": "66-BOOK BENCHMARK", "group": "benchmark", "color": "#86efac",
        "default_3d": False, "is_master_en": True,
        "notes": "Public-domain modern literal translation from BereanBible.com; plain text only, no study-note apparatus of its own."
    }
]

# 73-Book Canon Canonical Schema with LXX book numbers
CANON_SCHEMA = [
    {
        "division": "The Pentateuch / Torah",
        "testament": "OT",
        "books": [
            {"id": "gen", "name": "Genesis", "abbr": "Gen", "source_name": "Genesis", "lxx_num": 10, "lang": "Hebrew", "deuterocanon": False},
            {"id": "exod", "name": "Exodus", "abbr": "Exod", "source_name": "Exodus", "lxx_num": 20, "lang": "Hebrew", "deuterocanon": False},
            {"id": "lev", "name": "Leviticus", "abbr": "Lev", "source_name": "Leviticus", "lxx_num": 30, "lang": "Hebrew", "deuterocanon": False},
            {"id": "num", "name": "Numbers", "abbr": "Num", "source_name": "Numbers", "lxx_num": 40, "lang": "Hebrew", "deuterocanon": False},
            {"id": "deut", "name": "Deuteronomy", "abbr": "Deut", "source_name": "Deuteronomy", "lxx_num": 50, "lang": "Hebrew", "deuterocanon": False}
        ]
    },
    {
        "division": "Historical Books",
        "testament": "OT",
        "books": [
            {"id": "josh", "name": "Joshua", "abbr": "Josh", "source_name": "Joshua", "lxx_num": 60, "lang": "Hebrew", "deuterocanon": False},
            {"id": "judg", "name": "Judges", "abbr": "Judg", "source_name": "Judges", "lxx_num": 70, "lang": "Hebrew", "deuterocanon": False},
            {"id": "ruth", "name": "Ruth", "abbr": "Ruth", "source_name": "Ruth", "lxx_num": 80, "lang": "Hebrew", "deuterocanon": False},
            {"id": "1sam", "name": "1 Samuel", "abbr": "1Sam", "source_name": "I Samuel", "lxx_num": 90, "lang": "Hebrew", "deuterocanon": False},
            {"id": "2sam", "name": "2 Samuel", "abbr": "2Sam", "source_name": "II Samuel", "lxx_num": 100, "lang": "Hebrew", "deuterocanon": False},
            {"id": "1kgs", "name": "1 Kings", "abbr": "1Kgs", "source_name": "I Kings", "lxx_num": 110, "lang": "Hebrew", "deuterocanon": False},
            {"id": "2kgs", "name": "2 Kings", "abbr": "2Kgs", "source_name": "II Kings", "lxx_num": 120, "lang": "Hebrew", "deuterocanon": False},
            {"id": "1chr", "name": "1 Chronicles", "abbr": "1Chr", "source_name": "I Chronicles", "lxx_num": 130, "lang": "Hebrew", "deuterocanon": False},
            {"id": "2chr", "name": "2 Chronicles", "abbr": "2Chr", "source_name": "II Chronicles", "lxx_num": 140, "lang": "Hebrew", "deuterocanon": False},
            {"id": "ezra", "name": "Ezra", "abbr": "Ezra", "source_name": "Ezra", "lxx_num": 150, "lang": "Hebrew", "deuterocanon": False},
            {"id": "neh", "name": "Nehemiah", "abbr": "Neh", "source_name": "Nehemiah", "lxx_num": 160, "lang": "Hebrew", "deuterocanon": False},
            {"id": "tob", "name": "Tobit", "abbr": "Tob", "source_name": "Tobit", "lxx_num": 170, "lang": "Aramaic/Greek", "deuterocanon": True},
            {"id": "jdt", "name": "Judith", "abbr": "Jdt", "source_name": "Judith", "lxx_num": 180, "lang": "Hebrew/Greek", "deuterocanon": True},
            {"id": "esth", "name": "Esther (with Greek Additions)", "abbr": "Esth", "source_name": "Esther", "lxx_num": 190, "lang": "Hebrew/Greek", "deuterocanon": True},
            {"id": "1macc", "name": "1 Maccabees", "abbr": "1Macc", "source_name": "I Maccabees", "lxx_num": 462, "lang": "Hebrew/Greek", "deuterocanon": True},
            {"id": "2macc", "name": "2 Maccabees", "abbr": "2Macc", "source_name": "II Maccabees", "lxx_num": 464, "lang": "Greek", "deuterocanon": True}
        ]
    },
    {
        "division": "Wisdom & Poetry",
        "testament": "OT",
        "books": [
            {"id": "job", "name": "Job", "abbr": "Job", "source_name": "Job", "lxx_num": 220, "lang": "Hebrew", "deuterocanon": False},
            {"id": "ps", "name": "Psalms", "abbr": "Ps", "source_name": "Psalms", "lxx_num": 230, "lang": "Hebrew", "deuterocanon": False},
            {"id": "prov", "name": "Proverbs", "abbr": "Prov", "source_name": "Proverbs", "lxx_num": 240, "lang": "Hebrew", "deuterocanon": False},
            {"id": "eccl", "name": "Ecclesiastes (Qoheleth)", "abbr": "Eccl", "source_name": "Ecclesiastes", "lxx_num": 250, "lang": "Hebrew", "deuterocanon": False},
            {"id": "song", "name": "Song of Songs", "abbr": "Song", "source_name": "Song of Solomon", "lxx_num": 260, "lang": "Hebrew", "deuterocanon": False},
            {"id": "wis", "name": "Wisdom of Solomon", "abbr": "Wis", "source_name": "Wisdom", "lxx_num": 270, "lang": "Greek", "deuterocanon": True},
            {"id": "sir", "name": "Sirach (Ecclesiasticus)", "abbr": "Sir", "source_name": "Sirach", "lxx_num": 280, "lang": "Hebrew/Greek", "deuterocanon": True}
        ]
    },
    {
        "division": "The Prophets",
        "testament": "OT",
        "books": [
            {"id": "isa", "name": "Isaiah", "abbr": "Isa", "source_name": "Isaiah", "lxx_num": 290, "lang": "Hebrew", "deuterocanon": False},
            {"id": "jer", "name": "Jeremiah", "abbr": "Jer", "source_name": "Jeremiah", "lxx_num": 300, "lang": "Hebrew", "deuterocanon": False},
            {"id": "lam", "name": "Lamentations", "abbr": "Lam", "source_name": "Lamentations", "lxx_num": 310, "lang": "Hebrew", "deuterocanon": False},
            {"id": "bar", "name": "Baruch (incl. Letter of Jeremiah)", "abbr": "Bar", "source_name": "Baruch", "lxx_num": 320, "lang": "Hebrew/Greek", "deuterocanon": True},
            {"id": "ezek", "name": "Ezekiel", "abbr": "Ezek", "source_name": "Ezekiel", "lxx_num": 330, "lang": "Hebrew", "deuterocanon": False},
            {"id": "dan", "name": "Daniel (with Susanna & Bel)", "abbr": "Dan", "source_name": "Daniel", "lxx_num": 340, "lang": "Hebrew/Aramaic/Greek", "deuterocanon": True},
            {"id": "hos", "name": "Hosea", "abbr": "Hos", "source_name": "Hosea", "lxx_num": 350, "lang": "Hebrew", "deuterocanon": False},
            {"id": "joel", "name": "Joel", "abbr": "Joel", "source_name": "Joel", "lxx_num": 360, "lang": "Hebrew", "deuterocanon": False},
            {"id": "amos", "name": "Amos", "abbr": "Amos", "source_name": "Amos", "lxx_num": 370, "lang": "Hebrew", "deuterocanon": False},
            {"id": "obad", "name": "Obadiah", "abbr": "Obad", "source_name": "Obadiah", "lxx_num": 380, "lang": "Hebrew", "deuterocanon": False},
            {"id": "jonah", "name": "Jonah", "abbr": "Jonah", "source_name": "Jonah", "lxx_num": 390, "lang": "Hebrew", "deuterocanon": False},
            {"id": "mic", "name": "Micah", "abbr": "Mic", "source_name": "Micah", "lxx_num": 400, "lang": "Hebrew", "deuterocanon": False},
            {"id": "nah", "name": "Nahum", "abbr": "Nah", "source_name": "Nahum", "lxx_num": 410, "lang": "Hebrew", "deuterocanon": False},
            {"id": "hab", "name": "Habakkuk", "abbr": "Hab", "source_name": "Habakkuk", "lxx_num": 420, "lang": "Hebrew", "deuterocanon": False},
            {"id": "zeph", "name": "Zephaniah", "abbr": "Zeph", "source_name": "Zephaniah", "lxx_num": 430, "lang": "Hebrew", "deuterocanon": False},
            {"id": "hag", "name": "Haggai", "abbr": "Hag", "source_name": "Haggai", "lxx_num": 440, "lang": "Hebrew", "deuterocanon": False},
            {"id": "zech", "name": "Zechariah", "abbr": "Zech", "source_name": "Zechariah", "lxx_num": 450, "lang": "Hebrew", "deuterocanon": False},
            {"id": "mal", "name": "Malachi", "abbr": "Mal", "source_name": "Malachi", "lxx_num": 460, "lang": "Hebrew", "deuterocanon": False}
        ]
    },
    {
        "division": "The Holy Gospels & Acts",
        "testament": "NT",
        "books": [
            {"id": "matt", "name": "Matthew", "abbr": "Matt", "source_name": "Matthew", "lang": "Greek", "deuterocanon": False},
            {"id": "mark", "name": "Mark", "abbr": "Mark", "source_name": "Mark", "lang": "Greek", "deuterocanon": False},
            {"id": "luke", "name": "Luke", "abbr": "Luke", "source_name": "Luke", "lang": "Greek", "deuterocanon": False},
            {"id": "john", "name": "John", "abbr": "John", "source_name": "John", "lang": "Greek", "deuterocanon": False},
            {"id": "acts", "name": "Acts of the Apostles", "abbr": "Acts", "source_name": "Acts", "lang": "Greek", "deuterocanon": False}
        ]
    },
    {
        "division": "The Epistles & Apocalypse",
        "testament": "NT",
        "books": [
            {"id": "rom", "name": "Romans", "abbr": "Rom", "source_name": "Romans", "lang": "Greek", "deuterocanon": False},
            {"id": "1cor", "name": "1 Corinthians", "abbr": "1Cor", "source_name": "I Corinthians", "lang": "Greek", "deuterocanon": False},
            {"id": "2cor", "name": "2 Corinthians", "abbr": "2Cor", "source_name": "II Corinthians", "lang": "Greek", "deuterocanon": False},
            {"id": "gal", "name": "Galatians", "abbr": "Gal", "source_name": "Galatians", "lang": "Greek", "deuterocanon": False},
            {"id": "eph", "name": "Ephesians", "abbr": "Eph", "source_name": "Ephesians", "lang": "Greek", "deuterocanon": False},
            {"id": "phil", "name": "Philippians", "abbr": "Phil", "source_name": "Philippians", "lang": "Greek", "deuterocanon": False},
            {"id": "col", "name": "Colossians", "abbr": "Col", "source_name": "Colossians", "lang": "Greek", "deuterocanon": False},
            {"id": "1thess", "name": "1 Thessalonians", "abbr": "1Thess", "source_name": "I Thessalonians", "lang": "Greek", "deuterocanon": False},
            {"id": "2thess", "name": "2 Thessalonians", "abbr": "2Thess", "source_name": "II Thessalonians", "lang": "Greek", "deuterocanon": False},
            {"id": "1tim", "name": "1 Timothy", "abbr": "1Tim", "source_name": "I Timothy", "lang": "Greek", "deuterocanon": False},
            {"id": "2tim", "name": "2 Timothy", "abbr": "2Tim", "source_name": "II Timothy", "lang": "Greek", "deuterocanon": False},
            {"id": "titus", "name": "Titus", "abbr": "Titus", "source_name": "Titus", "lang": "Greek", "deuterocanon": False},
            {"id": "phlm", "name": "Philemon", "abbr": "Phlm", "source_name": "Philemon", "lang": "Greek", "deuterocanon": False},
            {"id": "heb", "name": "Hebrews", "abbr": "Heb", "source_name": "Hebrews", "lang": "Greek", "deuterocanon": False},
            {"id": "jas", "name": "James", "abbr": "Jas", "source_name": "James", "lang": "Greek", "deuterocanon": False},
            {"id": "1pet", "name": "1 Peter", "abbr": "1Pet", "source_name": "I Peter", "lang": "Greek", "deuterocanon": False},
            {"id": "2pet", "name": "2 Peter", "abbr": "2Pet", "source_name": "II Peter", "lang": "Greek", "deuterocanon": False},
            {"id": "1john", "name": "1 John", "abbr": "1John", "source_name": "I John", "lang": "Greek", "deuterocanon": False},
            {"id": "2john", "name": "2 John", "abbr": "2John", "source_name": "II John", "lang": "Greek", "deuterocanon": False},
            {"id": "3john", "name": "3 John", "abbr": "3John", "source_name": "III John", "lang": "Greek", "deuterocanon": False},
            {"id": "jude", "name": "Jude", "abbr": "Jude", "source_name": "Jude", "lang": "Greek", "deuterocanon": False},
            {"id": "rev", "name": "Revelation (Apocalypse)", "abbr": "Rev", "source_name": "Revelation of John", "lang": "Greek", "deuterocanon": False}
        ]
    }
]

# Master Database of 22 Forensically Grounded Cruxes
PRELOADED_CRUXES = [
    {
        "id": "acts15-amos9",
        "book_id": "acts",
        "chapter": 15,
        "verse_start": 16,
        "verse_end": 17,
        "title": "Gentiles Seeking God vs. Israel Conquering Edom",
        "ref": "Acts 15:16–17 / Amos 9:11–12",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "St. James at the Council of Jerusalem settles the circumcision controversy by quoting Amos 9 from the Septuagint. The Hebrew Masoretic Text predicts a military conquest of Edom, making James's argument impossible on the Protestant Hebrew text.",
        "english": "‘After this I will return, and I will rebuild the tent of David that has fallen; I will rebuild its ruins, and I will restore it, that the remnant of mankind may seek the Lord, and all the Gentiles who are called by my name, says the Lord, who makes these things known from of old.’",
        "vulgate": "ut requirant reliqui hominum Dominum, et omnes gentes super quas invocatum est nomen meum, dicit Dominus faciens haec.",
        "greek_hebrew": "ὅπως ἂν ἐκζητήσωσιν οἱ κατάλοιποι τῶν ἀνθρώπων τὸν Κύριον, καὶ πάντα τὰ ἔθνη ἐφ' οὓς ἐπικέκληται τὸ ὄνομά μου ἐπ' αὐτούς...",
        "interlinear": [
            {"w": "ὅπως ἄν", "t": "hopōs an", "pos": "Conj", "lemma": "ὅπως", "strong": "G3704", "m": "that / in order that"},
            {"w": "ἐκζητήσωσιν", "t": "ekzētēsōsin", "pos": "V-AAS-3P", "lemma": "ἐκζητέω", "strong": "G1567", "m": "may seek after"},
            {"w": "οἱ κατάλοιποι", "t": "hoi kataloipoi", "pos": "Adj-NMP", "lemma": "κατάλοιπος", "strong": "G2645", "m": "the remnant"},
            {"w": "τῶν ἀνθρώπων", "t": "tōn anthrōpōn", "pos": "N-GMP", "lemma": "ἄνθρωπος", "strong": "G444", "m": "of mankind"},
            {"w": "τὸν Κύριον", "t": "ton Kyrion", "pos": "N-AMS", "lemma": "Κύριος", "strong": "G2962", "m": "the Lord"}
        ],
        "apparatus": [
            {"witness": "Acts 15:17 (NA28 / Greek NT)", "text": "ὅπως ἂν ἐκζητήσωσιν οἱ κατάλοιποι τῶν ἀνθρώπων τὸν Κύριον", "note": "Remnant of mankind seeking God.", "tier": "gold"},
            {"witness": "Amos 9:12 (LXX Rahlfs / Codex B)", "text": "ὅπως ἐκζητήσωσιν οἱ κατάλοιποι τῶν ἀνθρώπων τὸν κύριον", "note": "Exact parent text of James's citation.", "tier": "gold"},
            {"witness": "Amos 9:12 (Hebrew MT / BHS)", "text": "לְמַעַן יִירְשׁוּ אֶת־שְׁאֵרִית אֱדוֹם (yirshu 'et-she'erit 'Edom)", "note": "‘That they may possess the remnant of Edom’ (Military conquest).", "tier": "gold"},
            {"witness": "Reconstructed Qumran Vorlage", "text": "למען ידרשו את־שארית אדם (yidrshu... 'Adam)", "note": "Consonantal variance: Dalet (ידרשו) vs Yod (יירשו); Adam (אדם) vs Edom (אדום).", "tier": "gold"},
            {"witness": "Spelling variant: ἄν particle", "text": "Some minuscule codices omit ἄν before ἐκζητήσωσιν", "note": "Orthographic / stylistic noise; no theological difference.", "tier": "slate"}
        ],
        "patristics": [
            {"father": "Council of Jerusalem (49 AD, Acts 15:28)", "work": "Apostolic Decree", "text": "“For it has seemed good to the Holy Spirit and to us to impose nothing further upon you than these necessary things...” Gentile reception rests on James's LXX Amos 9:11–12 proof."},
            {"father": "St. John Chrysostom", "work": "Homilies on Acts 33", "text": "Emphasizes that Bishop James delivers the binding prophetic synthesis demonstrating Gentile inclusion without Mosaic circumcision was foreordained by the prophets."}
        ],
        "strata_3d": {
            "top_text": "that the remnant of mankind may seek the Lord",
            "greek_text": "ὅπως ἂν ἐκζητήσωσιν οἱ κατάλοιποι τῶν ἀνθρώπων τὸν Κύριον",
            "uncial_text": "ΟΠΩC ΑΝ ΕΚΖΗΤΗCΩCΙΝ ΟΙ ΚΑΤΑΛΟΙΠΟΙ ΤΩΝ ΑΝΘΡΩΠΩΝ ΤΟΝ ΚΝ",
            "hebrew_mt": "לְמַעַן יִירְשׁוּ אֶת־שְׁאֵרִית אֱדוֹם (Possess Edom)",
            "vorlage_dss": "למען ידרשו את־שארית אדם (Seek mankind - 4Q/LXX)"
        }
    },
    {
        "id": "heb10-ps40",
        "book_id": "heb",
        "chapter": 10,
        "verse_start": 5,
        "verse_end": 7,
        "title": "A Body Prepared vs. Ears Dug / Pierced",
        "ref": "Hebrews 10:5–10 / Psalm 40:6–8",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "Hebrews 10 proves animal sacrifices are permanently replaced by Christ's physical body ('a body you prepared for me'). In the Hebrew Masoretic Text, the word 'body' does not exist; it reads 'ears you have dug for me.'",
        "english": "Consequently, when Christ came into the world, he said, ‘Sacrifices and offerings you have not desired, but a body you have prepared for me; in burnt offerings and sin offerings you have taken no pleasure. Then I said, Behold, I have come to do your will, O God, as it is written of me in the scroll of the book.’",
        "vulgate": "Ideo ingrediens mundum dicit: Hostiam et oblationem noluisti: corpus autem aptasti mihi...",
        "greek_hebrew": "διὸ εἰσερχόμενος εἰς τὸν κόσμον λέγει· θυσίαν καὶ προσφορὰν οὐκ ἠθέλησας, σῶμα δὲ κατηρτίσω μοι...",
        "interlinear": [
            {"w": "θυσίαν", "t": "thysian", "pos": "N-AFS", "lemma": "θυσία", "strong": "G2378", "m": "sacrifice"},
            {"w": "καὶ προσφοράν", "t": "kai prosphoran", "pos": "N-AFS", "lemma": "προσφορά", "strong": "G4376", "m": "and offering"},
            {"w": "οὐκ ἠθέλησας", "t": "ouk ēthelēsas", "pos": "V-AIA-2S", "lemma": "θέλω", "strong": "G2309", "m": "you desired not"},
            {"w": "σῶμα δέ", "t": "sōma de", "pos": "N-ANS", "lemma": "σῶμα", "strong": "G4983", "m": "but a body"},
            {"w": "κατηρτίσω", "t": "katērtisō", "pos": "V-AMI-2S", "lemma": "καταρτίζω", "strong": "G2675", "m": "you prepared / fitted"},
            {"w": "μοι", "t": "moi", "pos": "P-D1S", "lemma": "ἐγώ", "strong": "G1473", "m": "for me"}
        ],
        "apparatus": [
            {"witness": "Hebrews 10:5 (NA28 / P13, P46, Vaticanus B)", "text": "σῶμα δὲ κατηρτίσω μοι (sōma de katērtisō moi)", "note": "Physical body of Christ prepared for sacrifice.", "tier": "gold"},
            {"witness": "Psalm 39:7 (LXX Codices Vaticanus B, Sinaiticus א, Alexandrinus A)", "text": "σῶμα δὲ κατηρτίσω μοι (Rahlfs critical text emends to ὠτία; B/א/A read σῶμα)", "note": "Ancient uncial Septuagint witnesses read σῶμα ('body'), directly adopted by Hebrews 10:5.", "tier": "gold"},
            {"witness": "Psalm 40:6 (Hebrew MT / BHS)", "text": "אָזְנַיִם כָּרִיתָ לִּי ('oznayim karita li)", "note": "‘Ears you have dug for me’ (Obedience idiom; no mention of body).", "tier": "gold"},
            {"witness": "Latin Vulgate (Clementine / Gallican Psalter)", "text": "corpus autem aptasti mihi", "note": "Follows the Septuagint 'corpus' (body).", "tier": "sapphire"}
        ],
        "patristics": [
            {"father": "St. Athanasius", "work": "On the Incarnation (De Incarnatione)", "text": "Exposits Christ's assumption of a human body capable of death so that He might offer His own body as an oblation for all."},
            {"father": "St. Cyril of Alexandria & Council of Ephesus (431 AD)", "work": "Third Letter to Nestorius", "text": "Grounds Christ's saving sacrifice in the Word offering His own hypostatically united flesh in the words of Psalm 39:7 / Hebrews 10:5."}
        ],
        "strata_3d": {
            "top_text": "but a body you have prepared for me",
            "greek_text": "σῶμα δὲ κατηρτίσω μοι",
            "uncial_text": "CΩΜΑ ΔΕ ΚΑΤΗΡΤΙCΩ ΜΟΙ",
            "hebrew_mt": "אָזְנַיִם כָּרִיתָ לִּי (Ears you have dug)",
            "vorlage_dss": "Metonymic bodily oblation preserved in Old Greek vorlage"
        }
    },
    {
        "id": "heb1-deut32",
        "book_id": "heb",
        "chapter": 1,
        "verse_start": 6,
        "verse_end": 6,
        "title": "Angels Worshiping Jesus vs. Masoretic Complete Omission",
        "ref": "Hebrews 1:6 / Deuteronomy 32:43 / 4QDeut^q",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "Hebrews 1:6 quotes Scripture commanding all angels to worship Jesus ('Let all God's angels worship him'). In Protestant Bibles, Deuteronomy 32:43 completely omits this line! Dead Sea Scroll 4QDeut^q proved the Hebrew line existed and was lost by Masoretic scribes.",
        "english": "And again, when he brings the firstborn into the world, he says, ‘Let all God's angels worship him.’",
        "vulgate": "Et cum iterum introducit primogenitum in orbem terrae, dicit: Et adorent eum omnes angeli Dei.",
        "greek_hebrew": "ὅταν δὲ πάλιν εἰσαγάγῃ τὸν πρωτότοκον εἰς τὴν οἰκουμένην, λέγει· καὶ προσκυνησάτωσαν αὐτῷ πάντες ἄγγελοι Θεοῦ.",
        "interlinear": [
            {"w": "καὶ προσκυνησάτωσαν", "t": "kai proskynēsatōsan", "pos": "V-AMA-3P", "lemma": "προσκυνέω", "strong": "G4352", "m": "and let worship"},
            {"w": "αὐτῷ", "t": "autō", "pos": "P-DM3S", "lemma": "αὐτός", "strong": "G846", "m": "him"},
            {"w": "πάντες ἄγγελοι", "t": "pantes angeloi", "pos": "N-NMP", "lemma": "ἄγγελος", "strong": "G32", "m": "all angels"},
            {"w": "Θεοῦ", "t": "Theou", "pos": "N-GMS", "lemma": "Θεός", "strong": "G2316", "m": "of God"}
        ],
        "apparatus": [
            {"witness": "Hebrews 1:6 (NA28 / P46, Vaticanus)", "text": "καὶ προσκυνησάτωσαν αὐτῷ πάντες ἄγγελοι Θεοῦ", "note": "Commanding latria / divine proskynesis to the Son.", "tier": "gold"},
            {"witness": "Deuteronomy 32:43 (LXX Rahlfs)", "text": "καὶ προσκυνησάτωσαν αὐτῷ πάντες υἱοὶ θεοῦ / ἄγγελοι θεοῦ", "note": "Preserved in Greek Septuagint.", "tier": "gold"},
            {"witness": "Dead Sea Scrolls (4QDeut^q / 4Q44)", "text": "והשתחוו לו כל אלהים (wə-hish-tachawu lo kol-elohim)", "note": "1st-c BC Hebrew scroll from Qumran Cave 4 matches LXX verbatim!", "tier": "gold"},
            {"witness": "Hebrew Masoretic Text (Deut 32:43, BHS / KJV / ESV)", "text": "הַרְנִינוּ גוֹיִם עַמּוֹ כִּי דַם־עֲבָדָיו יִקּוֹם...", "note": "ENTIRE LINE MISSING. Dropped by scribal omission in Proto-MT.", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Justin Martyr", "work": "Dialogue with Trypho 71–73", "text": "Charges post-Christian rabbinic authorities with excising messianic lines from biblical codices; Deut 32:43's angelic worship clause survived in the LXX and Hebrew Qumran scroll 4QDeut^q."},
            {"father": "St. John Chrysostom", "work": "Homilies on Hebrews 3", "text": "Argues from Hebrews 1:6 that the One whom all the angels of God are commanded to worship is not a creature, but true God."}
        ],
        "strata_3d": {
            "top_text": "Let all God's angels worship him",
            "greek_text": "καὶ προσκυνησάτωσαν αὐτῷ πάντες ἄγγελοι Θεοῦ",
            "uncial_text": "ΚΑΙ ΠΡΟCΚΥΝΗCΑΤΩCΑΝ ΑΥΤΩ ΠΑΝΤΕC ΑΓΓΕΛΟΙ ΘΥ",
            "hebrew_mt": "[LINE ABSENT IN MASORETIC HEBREW]",
            "vorlage_dss": "והשתחוו לו כל אלהים (4QDeut^q restored)"
        }
    },
    {
        "id": "heb1-wis7",
        "book_id": "heb",
        "chapter": 1,
        "verse_start": 3,
        "verse_end": 3,
        "title": "Radiance of His Glory: Hebrews 1:3 Quotes Wisdom of Solomon 7:26",
        "ref": "Hebrews 1:3 / Wisdom 7:26",
        "tier": "crimson",
        "tier_name": "Tier 2: Doctrinal Crux (Catholic Canon Exclusive)",
        "summary": "Hebrews 1:3 defines the eternal deity of Christ as the 'ἀπαύγασμα τῆς δόξης' (radiance/effulgence of His glory). The Greek word apaugasma occurs NOWHERE in the entire 39-book Protestant Old Testament. Its unique pre-Christian occurrence is Wisdom of Solomon 7:26.",
        "english": "He is the radiance of the glory of God and the exact imprint of his nature, and he upholds the universe by the word of his power.",
        "vulgate": "Qui cum sit splendor gloriae, et figura substantiae ejus, portansque omnia verbo virtutis suae...",
        "greek_hebrew": "ὃς ὢν ἀπαύγασμα τῆς δόξης καὶ χαρακτὴρ τῆς ὑποστάσεως αὐτοῦ...",
        "interlinear": [
            {"w": "ἀπαύγασμα", "t": "apaugasma", "pos": "N-NNS", "lemma": "ἀπαύγασμα", "strong": "G541", "m": "radiance / effulgence (Wisdom 7:26 hapax)"},
            {"w": "τῆς δόξης", "t": "tēs doxēs", "pos": "N-GFS", "lemma": "δόξα", "strong": "G1391", "m": "of the glory"},
            {"w": "καὶ χαρακτήρ", "t": "kai charaktēr", "pos": "N-NMS", "lemma": "χαρακτήρ", "strong": "G5481", "m": "exact imprint / stamp"},
            {"w": "τῆς ὑποστάσεως", "t": "tēs hypostaseōs", "pos": "N-GFS", "lemma": "ὑπόστασις", "strong": "G5287", "m": "of His essence / hypostasis"}
        ],
        "apparatus": [
            {"witness": "Hebrews 1:3 (NA28 / P46, Vaticanus)", "text": "ὃς ὢν ἀπαύγασμα τῆς δόξης (being the radiance of glory)", "note": "Nicaea Christological cornerstone taken straight from Wisdom.", "tier": "crimson"},
            {"witness": "Wisdom of Solomon 7:26 (LXX / Sinaiticus)", "text": "ἀπαύγασμα γάρ ἐστιν φωτὸς ἀϊδίου (For she is the radiance of eternal light)", "note": "The ONLY biblical source for this term prior to Hebrews 1:3.", "tier": "crimson"},
            {"witness": "Protestant 39-Book Canon", "text": "WORD ABSENT: apaugasma does not appear anywhere in the MT or Protestant OT.", "note": "Proves the Apostle to the Hebrews immersed himself in the Deuterocanon.", "tier": "crimson"}
        ],
        "patristics": [
            {"father": "St. Athanasius", "work": "De Decretis (Defense of the Nicene Definition)", "text": "Appeals to Wisdom 7:26 and Hebrews 1:3 ('Radiance [apaugasma] of eternal Light') to demonstrate the co-eternal generation of the Son from the Father."},
            {"father": "Council of Nicaea (325 AD)", "work": "Nicene Creed", "text": "Formulates 'Light from Light' in continuity with Wisdom 7:26 and Hebrews 1:3 Christology."}
        ],
        "strata_3d": {
            "top_text": "He is the radiance of the glory of God and exact imprint of his nature",
            "greek_text": "ὃς ὢν ἀπαύγασμα τῆς δόξης καὶ χαρακτὴρ τῆς ὑποστάσεως αὐτοῦ",
            "uncial_text": "ΟC ΩΝ ΑΠΑΥΓΑCΜΑ ΤΗC ΔΟΞΗC ΚΑΙ ΧΑΡΑΚΤΗΡ",
            "hebrew_mt": "[TERM ABSENT IN 39-BOOK PROTESTANT OT]",
            "vorlage_dss": "Wisdom 7:26 (LXX) ἀπαύγασμα φωτὸς ἀϊδίου"
        }
    },
    {
        "id": "1sam11-nahash",
        "book_id": "1sam",
        "chapter": 11,
        "verse_start": 1,
        "verse_end": 2,
        "title": "Nahash Ammonite Eye-Gouging Paragraph: 4QSamª Recovery",
        "ref": "1 Samuel 11:1–2 / 4QSamª / Josephus",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "The Hebrew Masoretic Text opens 1 Samuel 11 with Nahash abruptly demanding to gouge out right eyes with no context. Qumran scroll 4QSamª and Josephus preserve a 50-word historical paragraph explaining Nahash's terror campaign, lost by Masoretic scribal homeoteleuton.",
        "english": "Now Nahash, king of the Ammonites, severely oppressed the Gadites and the Reubenites, and he gouged out the right eye of all of them, and brought terror and fear on Israel. There was not a man left among the Israelites beyond the Jordan whose right eye was not gouged out by Nahash king of the Ammonites, except that seven thousand men had fled from the Ammonites and entered Jabesh-gilead. And about a month later, Nahash the Ammonite came up and encamped against Jabesh-gilead...",
        "vulgate": "Ascendit autem Naas Ammonites, et pugnare coepit adversus Jabes Galaad...",
        "greek_hebrew": "וְנָחָשׁ מֶלֶךְ בְּנֵי־עַמּוֹן לָחַץ אֶת־בְּנֵי גָד וְאֶת־בְּנֵי רְאוּבֵן בְּחָזְקָה וְנִקֵּר לָהֶם כָּל־עֵין יָמִין...",
        "interlinear": [
            {"w": "וְנָחָשׁ מֶלֶךְ", "t": "wə-nachash melek", "pos": "Noun", "lemma": "נָחָשׁ", "strong": "H5176", "m": "And Nahash king of"},
            {"w": "בְּנֵי־עַמּוֹן", "t": "bene-'ammon", "pos": "Noun", "lemma": "עַמּוֹן", "strong": "H5983", "m": "children of Ammon"},
            {"w": "נִקֵּר", "t": "niqqer", "pos": "V-Piel-Perf-3MS", "lemma": "נָקַר", "strong": "H5365", "m": "he gouged out"},
            {"w": "כָּל־עֵין יָמִין", "t": "kol-'en yamin", "pos": "Noun", "lemma": "עַיִן", "strong": "H5869", "m": "every right eye"}
        ],
        "apparatus": [
            {"witness": "Dead Sea Scrolls (4QSamª / 4Q51, Cave 4 Qumran)", "text": "Preserves complete 50-word paragraph lost in MT.", "note": "Restores full historical motivation for the battle.", "tier": "gold"},
            {"witness": "Flavius Josephus (Antiquities 6.68–71, c. 93 AD)", "text": "Records identical narrative of eye-gouging and 7,000 refugees.", "note": "Proves 1st-century Jewish historians possessed this text.", "tier": "gold"},
            {"witness": "Hebrew Masoretic Text (BHS / KJV / ESV)", "text": "וַיַּעַל נָחָשׁ הָעַמּוֹנִי (Then Nahash the Ammonite came up...)", "note": "Omitted by homeoteleuton between 'Nahash king of Ammon' and 'Nahash Ammonite'.", "tier": "gold"}
        ],
        "patristics": [
            {"father": "Catholic Biblical Association (NABRE 2011)", "work": "Textual Apparatus on 1 Samuel 11:1", "text": "Adopts the 4QSamª opening paragraph directly into the English Catholic liturgical text based on Qumran Cave 4 Hebrew evidence corroborated by Josephus (Ant. 6.68–71)."}
        ],
        "strata_3d": {
            "top_text": "Now Nahash, king of the Ammonites, severely oppressed...",
            "greek_text": "Καὶ ἐγενήθη ὡς μετὰ μῆνα καὶ ἀνέβη Ναας ὁ Αμμανίτης...",
            "uncial_text": "ΝΑΑC ΒΑCΙΛΕΥC ΑΜΜΩΝ...",
            "hebrew_mt": "וַיַּעַל נָחָשׁ הָעַמּוֹנִי [Missing 50 words]",
            "vorlage_dss": "וְנָחָשׁ מֶלֶךְ בְּנֵי־עַמּוֹן לָחַץ (4QSamª complete)"
        }
    },
    {
        "id": "heb11-2macc7",
        "book_id": "heb",
        "chapter": 11,
        "verse_start": 35,
        "verse_end": 35,
        "title": "Tortured to Obtain a Better Resurrection",
        "ref": "Hebrews 11:35b / 2 Maccabees 7 / 2 Maccabees 6:18–31",
        "tier": "crimson",
        "tier_name": "Tier 2: Doctrinal Crux (Catholic Canon Exclusive)",
        "summary": "Hebrews 11 lists the heroes of faith who were tortured and refused release to gain a better resurrection. This narrative exists NOWHERE in the 39 books of the Protestant Old Testament; it is the verbatim story of 2 Maccabees 7.",
        "english": "Others were tortured, refusing to accept release, so that they might gain a better resurrection.",
        "vulgate": "Alii autem distenti sunt, non suscipientes redemptionem, ut meliorem invenirent resurrectionem.",
        "greek_hebrew": "ἄλλοι δὲ ἐτυμπανίσθησαν, οὐ προσδεξάμενοι τὴν ἀπολύτρωσιν, ἵνα κρείττονος ἀναστάσεως τύχωσιν.",
        "interlinear": [
            {"w": "ἄλλοι δέ", "t": "alloi de", "pos": "Adj-NMP", "lemma": "ἄλλος", "strong": "G243", "m": "and others"},
            {"w": "ἐτυμπανίσθησαν", "t": "etympanisthēsan", "pos": "V-AIP-3P", "lemma": "τυμπανίζω", "strong": "G5178", "m": "were tortured on the rack"},
            {"w": "οὐ προσδεξάμενοι", "t": "ou prosdexamenoi", "pos": "V-ANM-NMP", "lemma": "προσδέχομαι", "strong": "G4327", "m": "not accepting"},
            {"w": "τὴν ἀπολύτρωσιν", "t": "tēn apolytrōsin", "pos": "N-AFS", "lemma": "ἀπολύτρωσις", "strong": "G629", "m": "the release / redemption"},
            {"w": "ἵνα κρείττονος", "t": "hina kreittonos", "pos": "Adj-GFS", "lemma": "κρείττων", "strong": "G2909", "m": "that a better"},
            {"w": "ἀναστάσεως τύχωσιν", "t": "anastaseōs tychōsin", "pos": "N-GFS / V-ASA", "lemma": "ἀνάστασις", "strong": "G386", "m": "resurrection they might gain"}
        ],
        "apparatus": [
            {"witness": "Hebrews 11:35 (NA28 / P13, P46, Codex Vaticanus)", "text": "ἄλλοι δὲ ἐτυμπανίσθησαν, οὐ προσδεξάμενοι τὴν ἀπολύτρωσιν...", "note": "Direct intertextual witness to 2 Maccabees 6–7.", "tier": "crimson"},
            {"witness": "2 Maccabees 7:9 (Mother and Seven Sons)", "text": "‘The King of the world shall raise us up, who have died for his laws, unto everlasting life.’", "note": "The exact 'better resurrection' professed on the rack.", "tier": "crimson"},
            {"witness": "2 Maccabees 6:30 (Eleazar the Martyr)", "text": "‘Whereas I might have been delivered from death, I now endure sore pains...’", "note": "The exact refusal of release (apolytrōsis).", "tier": "crimson"},
            {"witness": "Protestant 39-Book Canon", "text": "TOTAL ABSENCE: No martyr in Genesis to Malachi undergoes this.", "note": "Proves the apostolic church utilized Second Maccabees as Scripture.", "tier": "crimson"}
        ],
        "patristics": [
            {"father": "St. Cyprian of Carthage", "work": "Exhortation to Martyrdom (Ad Fortunatum 11)", "text": "Holds up the mother and seven brothers of 2 Maccabees 7 as the Church's supreme inspired exemplar of martyrdom endured for the hope of resurrection."},
            {"father": "Council of Trent (1546)", "work": "Session IV Decree on the Sacred Books", "text": "Solemnly defines 1 and 2 Maccabees among the canonical Scriptures of the Old Testament."}
        ],
        "strata_3d": {
            "top_text": "Others were tortured, refusing to accept release...",
            "greek_text": "ἄλλοι δὲ ἐτυμπανίσθησαν, οὐ προσδεξάμενοι τὴν ἀπολύτρωσιν...",
            "uncial_text": "ΑΛΛΟΙ ΔΕ ΕΤΥΜΠΑΝΙCΘΗCΑΝ ΟΥ ΠΡΟCΔΕΞΑΜΕΝΟΙ ΤΗΝ ΑΠΟΛΥΤΡΩCΙΝ",
            "hebrew_mt": "[NO CORRESPONDING EVENT IN PROTESTANT OT]",
            "vorlage_dss": "2 Maccabees 7 Greek manuscript stream (Alexandrinus / Venetus)"
        }
    },
    {
        "id": "rev8-tobit12",
        "book_id": "rev",
        "chapter": 8,
        "verse_start": 2,
        "verse_end": 2,
        "title": "The Seven Archangels Standing Before God",
        "ref": "Revelation 8:2 / Revelation 1:4 / Tobit 12:15",
        "tier": "crimson",
        "tier_name": "Tier 2: Doctrinal Crux (Catholic Canon Exclusive)",
        "summary": "St. John sees 'the seven angels who stand before God.' The Protestant Old Testament names only Michael and Gabriel; the heavenly council of Seven Archangels exists exclusively in Tobit 12:15.",
        "english": "Then I saw the seven angels who stand before God, and seven trumpets were given to them.",
        "vulgate": "Et vidi septem angelos stantes in conspectu Dei: et datae sunt illis septem tubae.",
        "greek_hebrew": "καὶ εἶδον τοὺς ἑπτὰ ἀγγέλους οἳ ἐνώπιον τοῦ Θεοῦ ἑστήκασιν, καὶ ἐδόθησαν αὐτοῖς ἑπτὰ σάλπιγγες.",
        "interlinear": [
            {"w": "καὶ εἶδον", "t": "kai eidon", "pos": "V-AIA-1S", "lemma": "ὁράω", "strong": "G3708", "m": "and I saw"},
            {"w": "τοὺς ἑπτὰ ἀγγέλους", "t": "tous hepta angelous", "pos": "N-AMP", "lemma": "ἄγγελος", "strong": "G32", "m": "the seven angels"},
            {"w": "οἳ ἐνώπιον", "t": "hoi enōpion", "pos": "Rel-Pro / Prep", "lemma": "ἐνώπιον", "strong": "G1799", "m": "who before"},
            {"w": "τοῦ Θεοῦ", "t": "tou Theou", "pos": "N-GMS", "lemma": "Θεός", "strong": "G2316", "m": "of God"},
            {"w": "ἑστήκασιν", "t": "hestēkasin", "pos": "V-RIA-3P", "lemma": "ἵστημι", "strong": "G2476", "m": "stand / have stood"}
        ],
        "apparatus": [
            {"witness": "Revelation 8:2 (NA28 / Codex Sinaiticus, Alexandrinus)", "text": "καὶ εἶδον τοὺς ἑπτὰ ἀγγέλους οἳ ἐνώπιον τοῦ θεοῦ ἑστήκασιν", "note": "The seven archangels of the divine council.", "tier": "crimson"},
            {"witness": "Tobit 12:15 (Codex Sinaiticus / Greek Septuagint)", "text": "ἐγώ εἰμι Ραφαηλ, εἷς ἐκ τῶν ἑπτὰ ἁγίων ἀγγέλων, οἳ προσαναφέρουσιν τὰς προσευχὰς τῶν ἁγίων...", "note": "‘I am Raphael, one of the seven holy angels who present the prayers of the saints.’", "tier": "crimson"},
            {"witness": "Protestant 39-Book Canon", "text": "TOTAL ABSENCE: Never mentions a council of seven archangels presenting prayers.", "note": "Revelation adopts Tobit's angelology directly.", "tier": "crimson"}
        ],
        "patristics": [
            {"father": "Clement of Alexandria", "work": "Stromata I.21 & VI", "text": "Treats Tobit's angelic mission by Raphael as historical Scripture alongside the seven-archangel heavenly hierarchy echoed in Apocalypse 1:4 and 8:2."}
        ],
        "strata_3d": {
            "top_text": "Then I saw the seven angels who stand before God...",
            "greek_text": "καὶ εἶδον τοὺς ἑπτὰ ἀγγέλους οἳ ἐνώπιον τοῦ Θεοῦ ἑστήκασιν...",
            "uncial_text": "ΚΑΙ ΕΙΔΟΝ ΤΟΥC ΕΠΤΑ ΑΓΓΕΛΟΥC ΟΙ ΕΝΩΠΙΟΝ ΤΟΥ ΘΥ ΕCΤΗΚΑCΙΝ",
            "hebrew_mt": "[NO SEVEN ARCHANGELS IN PROTESTANT OT]",
            "vorlage_dss": "Tobit 12 Aramaic/Hebrew fragments at Qumran (4Q196–4Q200)"
        }
    },
    {
        "id": "baruch3-incarnation",
        "book_id": "bar",
        "chapter": 3,
        "verse_start": 36,
        "verse_end": 38,
        "title": "Baruch 3:36–38: The Incarnation Prophecy Cited as 'Jeremiah'",
        "ref": "Baruch 3:36–38 (Prot v.35–37) / St. Athanasius / St. Irenaeus",
        "tier": "crimson",
        "tier_name": "Tier 2: Doctrinal Crux (Patristic Canon Defense)",
        "summary": "Protestants claim St. Athanasius rejected the Deuterocanon. Yet Athanasius's 39th Festal Letter explicitly lists: 'Jeremiah, with Baruch, Lamentations, and the Epistle.' Furthermore, Baruch 3:36–38 ('After this, he was seen on earth, and he conversed with men') was universally cited as an inspired prophecy of Christ's Incarnation.",
        "english": "‘This is our God, and no other can compare to him. He invented the way of all instruction, and delivered it to Jacob his child, and to Israel his beloved. After this, he was seen on earth, and he conversed with men.’",
        "vulgate": "Hic est Deus noster, et non aestimabitur alius adversus eum... Post haec in terris visus est, et cum hominibus conversatus est.",
        "greek_hebrew": "οὗτος ὁ θεὸς ἡμῶν, οὐ λογισθήσεται ἕτερος πρὸς αὐτόν... μετὰ τοῦτο ἐπὶ τῆς γῆς ὤφθη καὶ ἐν τοῖς ἀνθρώποις συνανεστράφη.",
        "interlinear": [
            {"w": "οὗτος", "t": "houtos", "pos": "Dem-Pro", "lemma": "οὗτος", "strong": "G3778", "m": "This"},
            {"w": "ὁ θεὸς ἡμῶν", "t": "ho theos hēmōn", "pos": "Noun", "lemma": "θεός", "strong": "G2316", "m": "the God of us"},
            {"w": "ἐπὶ τῆς γῆς", "t": "epi tēs gēs", "pos": "Prep-Phrase", "lemma": "γῆ", "strong": "G1093", "m": "upon the earth"},
            {"w": "ὤφθη", "t": "ōphthē", "pos": "V-AIP-3S", "lemma": "ὁράω", "strong": "G3708", "m": "he appeared / was seen"},
            {"w": "ἐν τοῖς ἀνθρώποις", "t": "en tois anthrōpois", "pos": "Noun", "lemma": "ἄνθρωπος", "strong": "G444", "m": "among men"},
            {"w": "συνανεστράφη", "t": "synanestraphē", "pos": "V-AIP-3S", "lemma": "συναναστρέφω", "strong": "LXX", "m": "he lived / conversed"}
        ],
        "apparatus": [
            {"witness": "Septuagint (Baruch 3:36–38, Rahlfs / Codex Vaticanus)", "text": "οὗτος ὁ θεὸς ἡμῶν... μετὰ τοῦτο ἐπὶ τῆς γῆς ὤφθη καὶ ἐν τοῖς ἀνθρώποις συνανεστράφη", "note": "Primary Greek patristic text.", "tier": "crimson"},
            {"witness": "Latin Vulgate (Baruch 3:36–38)", "text": "Hic est Deus noster... post haec in terris visus est, et cum hominibus conversatus est.", "note": "Universal Roman Breviary and Advent liturgical lection.", "tier": "sapphire"},
            {"witness": "Protestant 39-Book Canon", "text": "COMPLETELY EXCISED: The entire book was dropped by Reformers.", "note": "Strips Christian apologetics of a foundational Incarnation prophecy.", "tier": "crimson"}
        ],
        "patristics": [
            {"father": "St. Athanasius of Alexandria", "work": "39th Festal Letter (367 AD) & Discourses Against the Arians II.49/53", "text": "Classifies Baruch and the Epistle as integral parts of 'Jeremiah' in his canonical list and quotes Baruch 3:36–38 against Arian subordinationism as prophetic Scripture."},
            {"father": "St. Irenaeus of Lyons", "work": "Against Heresies IV.20 & V.35.1; St. Cyprian, Testimonies II.6", "text": "Cites Baruch 3:36–38 and Baruch 4:36–5:9 directly under the prophet Jeremiah to prove the visibility and Incarnation of the one Creator God."}
        ],
        "strata_3d": {
            "top_text": "Afterward he appeared upon earth and conversed with men",
            "greek_text": "μετὰ ταῦτα ἐπὶ τῆς γῆς ὤφθη καὶ τοῖς ἀνθρώποις συνανεστράφη",
            "uncial_text": "ΜΕΤΑ ΤΑΥΤΑ ΕΠΙ ΤΗC ΓΗC ΩΦΘΗ ΚΑΙ ΤΟΙC ΑΝΘΡΩΠΟΙC CΥΝΑΝΕCΤΡΑΦΗ",
            "hebrew_mt": "[BOOK EXCISED IN PROTESTANT OT]",
            "vorlage_dss": "Letter of Jeremiah at Qumran (7Q2)"
        }
    },
    {
        "id": "luke4-isa61",
        "book_id": "luke",
        "chapter": 4,
        "verse_start": 18,
        "verse_end": 19,
        "title": "Recovery of Sight to the Blind: LXX Preserved, Masoretic Missing",
        "ref": "Luke 4:18–19 / Isaiah 61:1–2",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "When Jesus proclaims His messianic inaugural address in the Nazareth synagogue, He reads: 'and recovery of sight to the blind' (καὶ τυφλοῖς ἀνάβλεψιν). This clause is present in the Septuagint and Luke, but entirely missing from the Hebrew Masoretic Text!",
        "english": "‘The Spirit of the Lord is upon me, because he has anointed me to proclaim good news to the poor. He has sent me to proclaim liberty to the captives and recovery of sight to the blind, to set at liberty those who are oppressed, to proclaim the year of the Lord's favor.’",
        "vulgate": "Spiritus Domini super me, propter quod unxit me: evangelizare pauperibus misit me, sanare contritos corde, praedicare captivis remissionem, et caecis visum...",
        "greek_hebrew": "Πνεῦμα Κυρίου ἐπ' ἐμέ, οὗ εἵνεκεν ἔχρισέν με εὐαγγελίσασθαι πτωχοῖς... καὶ τυφλοῖς ἀνάβλεψιν...",
        "interlinear": [
            {"w": "Πνεῦμα Κυρίου", "t": "Pneuma Kyriou", "pos": "N-NNS", "lemma": "πνεῦμα", "strong": "G4151", "m": "Spirit of the Lord"},
            {"w": "ἔχρισέν με", "t": "echrisen me", "pos": "V-AIA-3S", "lemma": "χρίω", "strong": "G5548", "m": "has anointed me"},
            {"w": "καὶ τυφλοῖς", "t": "kai typhlois", "pos": "Adj-DMP", "lemma": "τυφλός", "strong": "G5185", "m": "and to the blind"},
            {"w": "ἀνάβλεψιν", "t": "anablepsin", "pos": "N-AFS", "lemma": "ἀνάβλεψις", "strong": "G309", "m": "recovery of sight"}
        ],
        "apparatus": [
            {"witness": "Luke 4:18 (NA28 / P75, Vaticanus, Sinaiticus)", "text": "καὶ τυφλοῖς ἀνάβλεψιν (and recovery of sight to the blind)", "note": "Quoted by Christ in the synagogue scroll.", "tier": "gold"},
            {"witness": "Isaiah 61:1 (LXX Rahlfs / Alexandrinus)", "text": "καὶ τυφλοῖς ἀνάβλεψιν", "note": "Preserved in the Greek Septuagint.", "tier": "gold"},
            {"witness": "Isaiah 61:1 (Hebrew MT / BHS)", "text": "וְלַאֲסוּרִים פְּקַח־קוֹחַ (and to prisoners opening/release)", "note": "Omits the healing of the blind; reads only opening of prison.", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Cyril of Alexandria", "work": "Commentary on Luke, Homily 12 (on Luke 4:18)", "text": "Interprets Christ's synagogue reading as revealing that He is the true Light who both restores bodily eyesight and frees those sitting in spiritual blindness."}
        ],
        "strata_3d": {
            "top_text": "and recovery of sight to the blind",
            "greek_text": "καὶ τυφλοῖς ἀνάβλεψιν",
            "uncial_text": "ΚΑΙ ΤΥΦΛΟΙC ΑΝΑΒΛΕΨΙΝ",
            "hebrew_mt": "וְלַאֲסוּרִים פְּקַח־קוֹחַ [Blindness clause absent]",
            "vorlage_dss": "1QIsaª reads opening/release with double gloss"
        }
    },
    {
        "id": "matt1-isa7",
        "book_id": "matt",
        "chapter": 1,
        "verse_start": 22,
        "verse_end": 23,
        "title": "The Virgin Birth Prophecy: Greek Parthenos vs MT Almah",
        "ref": "Matthew 1:22–23 / Isaiah 7:14",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "Matthew cites Isaiah 7:14 to prove Mary's virginal conception: 'Behold, the virgin shall conceive and bear a son.' Matthew explicitly follows the Septuagint's specific word 'parthenos' (virgin), whereas Masoretic Jewish polemics insist 'almah' merely meant 'young maiden'.",
        "english": "‘All this took place to fulfill what the Lord had spoken by the prophet: Behold, the virgin shall conceive and bear a son, and they shall call his name Immanuel’ (which means, God with us).",
        "vulgate": "Ecce virgo in utero habebit, et pariet filium: et vocabunt nomen ejus Emmanuel, quod est interpretatum Nobiscum Deus.",
        "greek_hebrew": "Ἰδοὺ ἡ παρθένος ἐν γαστρὶ ἕξει καὶ τέξεται υἱόν, καὶ καλέσουσιν τὸ ὄνομα αὐτοῦ Ἐμμανουήλ...",
        "interlinear": [
            {"w": "Ἰδοὺ", "t": "Idou", "pos": "Interj", "lemma": "ἰδού", "strong": "G2400", "m": "Behold"},
            {"w": "ἡ παρθένος", "t": "hē parthenos", "pos": "N-NFS", "lemma": "παρθένος", "strong": "G3933", "m": "the virgin"},
            {"w": "ἐν γαστρὶ ἕξει", "t": "en gastri hexei", "pos": "Phrase", "lemma": "γαστήρ", "strong": "G1064", "m": "shall be with child"},
            {"w": "καὶ τέξεται υἱόν", "t": "kai texetai hyion", "pos": "Phrase", "lemma": "τίκτω", "strong": "G5088", "m": "and shall bear a son"}
        ],
        "apparatus": [
            {"witness": "Matthew 1:23 (NA28 / B, ℵ, C, D)", "text": "Ἰδοὺ ἡ παρθένος ἐν γαστρὶ ἕξει καὶ τέξεται υἱόν", "note": "Unambiguous virginity of Mary.", "tier": "gold"},
            {"witness": "Isaiah 7:14 (LXX Rahlfs / 3rd-c BC)", "text": "ἰδοὺ ἡ παρθένος ἐν γαστρὶ λήμψεται καὶ τέξεται υἱόν", "note": "Pre-Christian Jewish translators rendered almah as parthenos.", "tier": "gold"},
            {"witness": "Isaiah 7:14 (Hebrew MT / BHS)", "text": "הִנֵּה הָעַלְמָה הָרָה וְיֹלֶדֶת בֵּן (hinneh ha-'almah harah)", "note": "Rabbinic scribes glossed 'almah as young woman (neanis in Aquila).", "tier": "gold"}
        ],
        "patristics": [
            {"father": "Justin Martyr", "work": "Dialogue with Trypho 68", "text": "‘You dare to distort the translation made by the seventy elders, claiming the text does not say: Behold the virgin shall conceive, but: Behold the young woman.’"},
            {"father": "St. Irenaeus", "work": "Against Heresies III.21.1", "text": "‘God was made man, and the Lord Himself saved us, giving us the sign of the Virgin, not as Theodotion and Aquila, Jewish proselytes, translate.’"}
        ],
        "strata_3d": {
            "top_text": "Behold, the virgin shall conceive and bear a son",
            "greek_text": "Ἰδοὺ ἡ παρθένος ἐν γαστρὶ ἕξει καὶ τέξεται υἱόν",
            "uncial_text": "ΙΔΟΥ Η ΠΑΡΘΕΝΟC ΕΝ ΓΑCΤΡΙ ΕΞΕΙ ΚΑΙ ΤΕΞΕΤΑΙ ΥΙΟΝ",
            "hebrew_mt": "הִנֵּה הָעַלְמָה הָרָה (ha-'almah - disputed by post-70 AD rabbinic polemic)",
            "vorlage_dss": "1QIsaª col. VII confirms ha-'almah consonantal text with matres lectionis"
        }
    },
    {
        "id": "matt21-ps8",
        "book_id": "matt",
        "chapter": 21,
        "verse_start": 16,
        "verse_end": 16,
        "title": "Perfected Praise vs. Ordained Strength: Matthew 21:16 Quoting LXX Psalm 8",
        "ref": "Matthew 21:16 / Psalm 8:2",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "When chief priests rebuke children shouting Hosanna in the Temple, Jesus answers with Scripture: 'Out of the mouth of infants and nursing babies you have perfected praise' (κατηρτίσω αἶνον). The Masoretic Text of Psalm 8:2 does NOT mention praise; it says 'you have ordained strength' (עֹז).",
        "english": "‘Yes; have you never read, “Out of the mouth of infants and nursing babies you have prepared praise”?’",
        "vulgate": "Utique: numquam legistis: Quia ex ore infantium et lactentium perfecisti laudem?",
        "greek_hebrew": "Ναί· οὐδέποτε ἀνέγνωτε ὅτι Ἐκ στόματος νηπίων καὶ θηλαζόντων κατηρτίσω αἶνον;",
        "interlinear": [
            {"w": "Ἐκ στόματος", "t": "Ek stomatos", "pos": "Prep-Phrase", "lemma": "στόμα", "strong": "G4750", "m": "Out of the mouth"},
            {"w": "νηπίων", "t": "nēpiōn", "pos": "N-GMP", "lemma": "νήπιος", "strong": "G3516", "m": "of infants / babes"},
            {"w": "κατηρτίσω", "t": "katērtisō", "pos": "V-AMI-2S", "lemma": "καταρτίζω", "strong": "G2675", "m": "you have prepared / perfected"},
            {"w": "αἶνον", "t": "ainon", "pos": "N-AMS", "lemma": "αἶνος", "strong": "G136", "m": "praise"}
        ],
        "apparatus": [
            {"witness": "Matthew 21:16 (NA28 / Vaticanus, Sinaiticus)", "text": "κατηρτίσω αἶνον (you have perfected praise)", "note": "Christ's entire temple rebuttal depends on the word 'praise'.", "tier": "gold"},
            {"witness": "Psalm 8:3 (LXX Rahlfs)", "text": "κατηρτίσω αἶνον", "note": "Direct source of Jesus's defense.", "tier": "gold"},
            {"witness": "Psalm 8:3 (Hebrew MT / BHS / KJV)", "text": "יִסַּדְתָּ עֹז (yissadta 'oz - founded strength)", "note": "‘Ordained strength’ renders Christ's quotation unintelligible on the MT alone.", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Jerome", "work": "Commentary on Matthew III (on Matt 21:16)", "text": "Notes that although the Hebrew Psalm 8:3 reads 'strength' (fortitudinem / 'oz), both the Septuagint and Matthew's Gospel render 'perfected praise' (laudem / ainon)."}
        ],
        "strata_3d": {
            "top_text": "Out of the mouth of infants and nursing babies you have prepared praise",
            "greek_text": "Ἐκ στόματος νηπίων καὶ θηλαζόντων κατηρτίσω αἶνον",
            "uncial_text": "ΕΚ CΤΟΜΑΤΟC ΝΗΠΙΩΝ ΚΑΤΗΡΤΙCΩ ΑΙΝΟΝ",
            "hebrew_mt": "מִפִּי עוֹלְלִים וְיֹנְקִים יִסַּדְתָּ עֹז (Founded strength)",
            "vorlage_dss": "LXX vorlage preserves 'praise' behind Christ's temple reply"
        }
    },
    {
        "id": "matt27-wis2",
        "book_id": "matt",
        "chapter": 27,
        "verse_start": 42,
        "verse_end": 43,
        "title": "Mockery at the Cross: Verbatim Fulfillment of Wisdom of Solomon",
        "ref": "Matthew 27:42–43 / Wisdom 2:12–20",
        "tier": "crimson",
        "tier_name": "Tier 2: Doctrinal Crux (Catholic Canon Exclusive)",
        "summary": "The chief priests, scribes, and elders mock the crucified Christ using the exact words of the wicked in Wisdom 2 ('He trusts in God; let God deliver him now if he wants him; for he said, I am the Son of God'). This prophecy exists exclusively in the Deuterocanonical Wisdom of Solomon.",
        "english": "‘He saved others; he cannot save himself. He is the King of Israel; let him come down now from the cross, and we will believe in him. He trusts in God; let God deliver him now, if he desires him; for he said, “I am the Son of God.”’",
        "vulgate": "Confidit in Deo: liberet nunc, si vult eum: dixit enim: Quia Filius Dei sum.",
        "greek_hebrew": "πέποιθεν ἐπὶ τὸν Θεόν, ῥυσάσθω νῦν εἰ θέλει αὐτόν· εἶπεν γὰρ ὅτι Θεοῦ εἰμι υἱός.",
        "interlinear": [
            {"w": "πέποιθεν", "t": "pepoithen", "pos": "V-RIA-3S", "lemma": "πείθω", "strong": "G3982", "m": "He has trusted"},
            {"w": "ἐπὶ τὸν Θεόν", "t": "epi ton Theon", "pos": "Prep-Phrase", "lemma": "θεός", "strong": "G2316", "m": "in God"},
            {"w": "ῥυσάσθω νῦν", "t": "rhysasthō nyn", "pos": "V-AMA-3S / Adv", "lemma": "ῥύομαι", "strong": "G4506", "m": "let him deliver now"},
            {"w": "εἰ θέλει αὐτόν", "t": "ei thelei auton", "pos": "Phrase", "lemma": "θέλω", "strong": "G2309", "m": "if he desires him"},
            {"w": "Θεοῦ εἰμι υἱός", "t": "Theou eimi hyios", "pos": "Phrase", "lemma": "υἱός", "strong": "G5207", "m": "I am the Son of God"}
        ],
        "apparatus": [
            {"witness": "Matthew 27:43 (NA28 / Codex Vaticanus)", "text": "πέποιθεν ἐπὶ τὸν θεόν, ῥυσάσθω νῦν εἰ θέλει αὐτόν· εἶπεν γὰρ ὅτι θεοῦ εἰμι υἱός", "note": "Crucifixion mockery by chief priests.", "tier": "crimson"},
            {"witness": "Wisdom of Solomon 2:18–20 (LXX / Codex Sinaiticus)", "text": "εἰ γάρ ἐστιν ὁ δίκαιος υἱὸς θεοῦ, ἀντιλήμψεται αὐτοῦ καὶ ῥύσεται αὐτὸν ἐκ χειρὸς ἐναντίων...", "note": "‘For if the just man be the son of God, he will help him, and deliver him... Let us condemn him to a shameful death.’", "tier": "crimson"},
            {"witness": "Protestant 39-Book Canon", "text": "TOTAL ABSENCE: Psalm 22 predicts mockery of trusting God, but only Wisdom 2 predicts the exact trial of claiming to be 'Son of God' and condemnation to a shameful death.", "note": "The Evangelist intentionally frames Christ's Passion as the fulfillment of Wisdom 2.", "tier": "crimson"}
        ],
        "patristics": [
            {"father": "St. Augustine", "work": "City of God XVII.20", "text": "Cites Wisdom 2:12–21 explicitly as a prophetic prefigurement of Christ's Passion, highlighting the ungodly condemning the Just One to a shameful death."}
        ],
        "strata_3d": {
            "top_text": "He trusts in God; let God deliver him now... for he said, I am the Son of God",
            "greek_text": "πέποιθεν ἐπὶ τὸν Θεόν, ῥυσάσθω νῦν εἰ θέλει αὐτόν· εἶπεν γὰρ ὅτι Θεοῦ εἰμι υἱός",
            "uncial_text": "ΠΕΠΟΙΘΕΝ ΕΠΙ ΤΟΝ ΘΝ ΡΥCΑCΘΩ ΝΥΝ ΕΙ ΘΕΛΕΙ ΑΥΤΟΝ",
            "hebrew_mt": "[NO WISDOM 2 IN PROTESTANT OT]",
            "vorlage_dss": "Wisdom 2 Greek codex tradition preserved in Catholic Lectionary"
        }
    },
    {
        "id": "ps22-pierced",
        "book_id": "ps",
        "chapter": 21,
        "verse_start": 17,
        "verse_end": 18,
        "title": "They Pierced My Hands and Feet vs. Like a Lion My Hands and Feet",
        "ref": "Psalm 21:17–18 (MT/Prot Ps 22:16) / Nahal Hever Scroll 5/6HevPs col. XI",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "Christian Bibles read the messianic crucifixion prophecy in Catholic/LXX Psalm 21:17 (MT/Prot Psalm 22:16): 'They pierced my hands and feet.' The Masoretic Text reads: 'Like a lion, my hands and feet' (כָּאֲרִי, ka'ari), with no verb. The Dead Sea Scroll from Nahal Hever (5/6HevPs) preserves the verbal plural form 'כארו' ('they pierced/dug'), corroborating the Septuagint and Vulgate tradition.",
        "english": "‘For many dogs have surrounded me. The council of the malicious has besieged me. They have pierced my hands and feet. They have numbered all my bones.’",
        "vulgate": "Foderunt manus meas et pedes meos: dinumeraverunt omnia ossa mea.",
        "greek_hebrew": "ὤρυξαν χεῖράς μου καὶ πόδας· ἐξηρίθμησα πάντα τὰ ὀστᾶ μου...",
        "interlinear": [
            {"w": "ὤρυξαν", "t": "ōryxan", "pos": "V-AIA-3P", "lemma": "ὀρύσσω", "strong": "G3736", "m": "they pierced / dug out"},
            {"w": "χεῖράς μου", "t": "cheiras mou", "pos": "N-AFP", "lemma": "χείρ", "strong": "G5495", "m": "my hands"},
            {"w": "καὶ πόδας", "t": "kai podas", "pos": "N-AMP", "lemma": "πούς", "strong": "G4228", "m": "and feet"}
        ],
        "apparatus": [
            {"witness": "Septuagint (Psalm 21:17, LXX Rahlfs / Vaticanus)", "text": "ὤρυξαν χεῖράς μου καὶ πόδας (they dug/pierced my hands and feet)", "note": "Clear crucifixion prophecy.", "tier": "gold"},
            {"witness": "Latin Vulgate (Clementine / Gallican Psalter)", "text": "Foderunt manus meas et pedes meos", "note": "They pierced my hands and my feet.", "tier": "sapphire"},
            {"witness": "Nahal Hever Scroll (5/6HevPs col. XI, 1st c. AD)", "text": "כארו ידי ורגלי (ka'aru yaday w-raglay)", "note": "HEBREW SCROLL PRESERVES VAV (כארו = they pierced), corroborating LXX/Vulgate over MT 'ka'ari' (like a lion)!", "tier": "gold"},
            {"witness": "Hebrew Masoretic Text (Psalm 22:17 WLC / BHS / Leningrad)", "text": "כָּאֲרִי יָדַי וְרַגְלָי (ka'ari yaday w-raglay)", "note": "‘Like a lion my hands and feet’ (verb missing; waw/yod graphic confusion).", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Justin Martyr", "work": "First Apology 35 (c. 155 AD)", "text": "“‘They pierced My hands and My feet, and for My vesture they cast lots.’ And indeed David, the king and prophet, who uttered these things, suffered none of them; but Jesus Christ stretched forth His hands, being crucified...”"},
            {"father": "Tertullian", "work": "Against Marcion III.19", "text": "Applies Psalm 21:17 ('They pierced my hands and my feet') directly to the nails of Christ's crucifixion against Marcion."}
        ],
        "strata_3d": {
            "top_text": "they have pierced my hands and feet",
            "greek_text": "ὤρυξαν χεῖράς μου καὶ πόδας μου",
            "uncial_text": "ΩΡΥΞΑΝ ΧΕΙΡΑC ΜΟΥ ΚΑΙ ΠΟΔΑC ΜΟΥ",
            "hebrew_mt": "כָּאֲרִי יָדַי וְרַגְלָי (Like a lion my hands and feet - corrupt MT)",
            "vorlage_dss": "כארו ידי ורגלי (5/6HevPs col. XI - Hebrew verb 'they pierced')"
        }
    },
    {
        "id": "ps145-nun",
        "book_id": "ps",
        "chapter": 144,
        "verse_start": 13,
        "verse_end": 14,
        "title": "The Missing Nun Acrostic: 11QPsª Restores the Lost Verse",
        "ref": "Psalm 144:13b (MT/Prot Ps 145:13) / 11QPsª / LXX",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "Catholic/LXX Psalm 144 (MT/Protestant Psalm 145) is a 22-letter Hebrew alphabetical acrostic. In the Masoretic Text, the entire verse beginning with the letter Nun (נ) is missing! Dead Sea Scroll 11QPsª, the Septuagint, Syriac Peshitta, and Latin Vulgate preserve the original Nun line intact.",
        "english": "‘Your kingdom is an everlasting kingdom, and your dominion endures throughout all generations. [The LORD is faithful in all his words, and holy in all his works.] The LORD upholds all who are falling and raises up all who are bowed down.’",
        "vulgate": "Fidelis Dominus in omnibus verbis suis, et sanctus in omnibus operibus suis. Allevat Dominus omnes qui corruunt...",
        "greek_hebrew": "Πιστὸς Κύριος ἐν τοῖς λόγοις αὐτοῦ καὶ ὅσιος ἐν πᾶσι τοῖς ἔργοις αὐτοῦ...",
        "interlinear": [
            {"w": "נֶאֱמָן יְהוָה", "t": "ne'eman YHWH", "pos": "Adj / Proper-N", "lemma": "אָמַן", "strong": "H539", "m": "Faithful is the LORD"},
            {"w": "בְּכָל־דְּבָרָיו", "t": "bə-kol-devaraw", "pos": "Prep / Noun", "lemma": "דָּבָר", "strong": "H1697", "m": "in all his words"},
            {"w": "וְחָסִיד", "t": "wə-chasid", "pos": "Adj", "lemma": "חָסִיד", "strong": "H2623", "m": "and gracious / holy"},
            {"w": "בְּכָל־מַעֲשָׂיו", "t": "bə-kol-ma'asaw", "pos": "Noun", "lemma": "מַעֲשֶׂה", "strong": "H4639", "m": "in all his works"}
        ],
        "apparatus": [
            {"witness": "Dead Sea Scrolls (11QPsª col. XVI, Cave 11 Qumran)", "text": "נאמן אלוהים בדבריו וחסיד בכול מעשיו (Nun verse complete)", "note": "Proves the Hebrew alphabetical acrostic had no missing letter!", "tier": "gold"},
            {"witness": "Septuagint (Psalm 144:13b, LXX Rahlfs)", "text": "Πιστὸς κύριος ἐν πᾶσιν τοῖς λόγοις αὐτοῦ καὶ ὅσιος ἐν πᾶσιν τοῖς ἔργοις αὐτοῦ", "note": "Faithfully translated into Greek from pre-Masoretic Vorlage.", "tier": "gold"},
            {"witness": "Hebrew Masoretic Text (Psalm 145:13, BHS / KJV)", "text": "ENTIRE VERSE MISSING", "note": "Dropped in Proto-MT by scribal parablepsis.", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Jerome", "work": "Notes & Psalter Versions (Gallicanum vs. Hebraicum)", "text": "Includes the missing Nun line ('Fidelis Dominus in omnibus verbis suis...') in the Septuagint-based Gallican Psalter while noting its omission from contemporary Hebrew MT codices."}
        ],
        "strata_3d": {
            "top_text": "The LORD is faithful in all his words, and holy in all his works",
            "greek_text": "Πιστὸς Κύριος ἐν τοῖς λόγοις αὐτοῦ καὶ ὅσιος ἐν πᾶσι τοῖς ἔργοις αὐτοῦ",
            "uncial_text": "ΠΙCΤΟC ΚC ΕΝ ΤΟΙC ΛΟΓΟΙC ΑΥΤΟΥ ΚΑΙ ΟCΙΟC ΕΝ ΠΑCΙ ΤΟΙC ΕΡΓΟΙC ΑΥΤΟΥ",
            "hebrew_mt": "[NUN VERSE COMPLETELY DROPPED IN MT]",
            "vorlage_dss": "נאמן אלוהים בדבריו וחסיד בכול מעשיו (11QPsª restored)"
        }
    },
    {
        "id": "gen4-field",
        "book_id": "gen",
        "chapter": 4,
        "verse_start": 8,
        "verse_end": 8,
        "title": "Cain's Missing Words: 'Let Us Go Into the Field'",
        "ref": "Genesis 4:8 / 4QGen-Exodª / LXX / Samaritan Pentateuch",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "In the Masoretic Text of Genesis 4:8, the text says: 'And Cain said to Abel his brother... and it came to pass when they were in the field', omitting WHAT Cain said! The Septuagint, Samaritan Pentateuch, Syriac Peshitta, and Dead Sea Scroll 4QGen-Exodª preserve Cain's spoken words: 'Let us go out into the field.'",
        "english": "‘Cain said to Abel his brother, “Let us go out into the field.” And when they were in the field, Cain rose up against his brother Abel and killed him.’",
        "vulgate": "Dixitque Cain ad Abel fratrem suum: Egrediamur foras. Cumque essent in agro, consurrexit Cain adversus fratrem suum Abel, et interfecit eum.",
        "greek_hebrew": "καὶ εἶπεν Καιν πρὸς Αβελ τὸν ἀδελφὸν αὐτοῦ Διέλθωμεν εἰς τὸ πεδίον...",
        "interlinear": [
            {"w": "וַיֹּאמֶר קַיִן", "t": "way-yomer Qayin", "pos": "V-Qal", "lemma": "אָמַר", "strong": "H559", "m": "And Cain said"},
            {"w": "אֶל־הַשָּׂדֶה", "t": "el-has-sadeh", "pos": "Noun", "lemma": "שָׂדֶה", "strong": "H7704", "m": "into the field"},
            {"w": "Egrediamur foras", "t": "Latin Vulgate", "pos": "Phrase", "lemma": "egredior", "strong": "Vulg", "m": "Let us go outside"}
        ],
        "apparatus": [
            {"witness": "Dead Sea Scrolls (4QGen-Exodª / 4Q1)", "text": "נלכה השדה (nelkah has-sadeh - Let us go to the field)", "note": "Restores original direct speech.", "tier": "gold"},
            {"witness": "Septuagint (Genesis 4:8, LXX Rahlfs)", "text": "Διέλθωμεν εἰς τὸ πεδίον (Let us go through into the plain/field)", "note": "Witness to ancient Hebrew vorlage.", "tier": "gold"},
            {"witness": "Latin Vulgate (Genesis 4:8)", "text": "Egrediamur foras (Let us go outside)", "note": "St. Jerome preserves the direct speech.", "tier": "sapphire"},
            {"witness": "Hebrew Masoretic Text (BHS / KJV / ESV)", "text": "וַיֹּאמֶר קַיִן אֶל־הֶבֶל אָחִיו וַיְהִי בִּהְיוֹתָם בַּשָּׂדֶה (Missing speech!)", "note": "Masoretic codices leave a blank space (pisqah be'emtsa pasuq) admitting the omission!", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Ambrose of Milan", "work": "On Cain and Abel (De Cain et Abel II.8)", "text": "Comments directly on the Septuagint/Old Latin clause ('Let us go into the field') showing Cain lured his brother outward into isolated terrain where no help could arrive."}
        ],
        "strata_3d": {
            "top_text": "Cain said to Abel his brother, Let us go out into the field",
            "greek_text": "Διέλθωμεν εἰς τὸ πεδίον",
            "uncial_text": "ΔΙΕΛΘΩΜΕΝ ΕΙC ΤΟ ΠΕΔΙΟΝ",
            "hebrew_mt": "וַיֹּאמֶר קַיִן [Direct speech omitted in MT]",
            "vorlage_dss": "נלכה השדה (4QGen-Exodª restores 'Let us go to the field')"
        }
    },
    {
        "id": "gen5-chronology",
        "book_id": "gen",
        "chapter": 11,
        "verse_start": 12,
        "verse_end": 13,
        "title": "The 1,386-Year Genealogies & Cainan: Luke 3 vs Masoretic Truncation",
        "ref": "Genesis 11:12–13 / Genesis 5 / Luke 3:36",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "Between the Septuagint and the Masoretic Text lies a 1,386-year gap in patriarchal genealogies. St. Luke in Luke 3:36 includes Cainan (son of Arphaxad), which exists in the Septuagint but is omitted in the Masoretic Hebrew text. Patristic scholarship documented that post-70 AD rabbinic scribes compressed patriarchal ages to deflate Christian messianic millennial calculations.",
        "english": "‘When Arphaxad had lived 35 years [LXX: 135 years], he fathered Shelah [LXX: fathered Cainan; and Cainan lived 130 years and fathered Shelah]...’ St. Luke 3:36: ‘...the son of Shelah, the son of Cainan, the son of Arphaxad, the son of Shem, the son of Noah...’",
        "vulgate": "qui fuit Sale, qui fuit Cainan, qui fuit Arphaxad, qui fuit Sem, qui fuit Noe...",
        "greek_hebrew": "τοῦ Σαλά, τοῦ Καϊνάμ, τοῦ Ἀρφαξάδ, τοῦ Σήμ, τοῦ Νῶε...",
        "interlinear": [
            {"w": "τοῦ Καϊνάμ", "t": "tou Kainan", "pos": "N-GMS", "lemma": "Καϊνάν", "strong": "G2536", "m": "of Cainan"},
            {"w": "τοῦ Ἀρφαξάδ", "t": "tou Arphaxad", "pos": "N-GMS", "lemma": "Ἀρφαξάδ", "strong": "G742", "m": "of Arphaxad"}
        ],
        "apparatus": [
            {"witness": "Luke 3:36 (NA28 / P75, Sinaiticus, Vaticanus)", "text": "τοῦ Καϊνὰμ τοῦ Ἀρφαξάδ (son of Cainan, son of Arphaxad)", "note": "Inspired Gospel author confirms the Septuagint genealogy.", "tier": "gold"},
            {"witness": "Genesis 11:12 (LXX Rahlfs / Codex B)", "text": "Καὶ ἔζησεν Ἀρφαξὰδ ἑκατὸν τριάκοντα πέντε ἔτη καὶ ἐγέννησεν τὸν Καϊναν", "note": "Preserves Cainan and the extra 100-year fatherhood ages.", "tier": "gold"},
            {"witness": "Genesis 11:12 (Hebrew MT / BHS)", "text": "וְאַרְפַּכְשַׁד חַי חָמֵשׁ וּשְׁלֹשִׁים שָׁנָה וַיּוֹלֶד אֶת־שָׁלַח (Cainan absent!)", "note": "Drops Cainan completely; shortens ages by 1,386 years.", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Augustine of Hippo", "work": "City of God XV.10–14", "text": "Defends the longer Septuagint patriarchal chronology and accepts St. Luke's inclusion of the second Cainan (Luke 3:36) as authoritative Gospel witness."},
            {"father": "Sextus Julius Africanus", "work": "Chronographiae (c. 221 AD)", "text": "Computes roughly 5,500 years from creation to the Incarnation directly on the longer Septuagint chronology."}
        ],
        "strata_3d": {
            "top_text": "the son of Shelah, the son of Cainan, the son of Arphaxad (Luke 3:36)",
            "greek_text": "τοῦ Σαλά, τοῦ Καϊνάμ, τοῦ Ἀρφαξάδ",
            "uncial_text": "ΤΟΥ CΑΛΑ ΤΟΥ ΚΑΙΝΑΜ ΤΟΥ ΑΡΦΑΞΑΔ",
            "hebrew_mt": "וַיּוֹלֶד אֶת־שָׁלַח [Cainan omitted in MT]",
            "vorlage_dss": "Jubilees 8:1–4 confirms Cainan reading in ancient Semitic tradition"
        }
    },
    {
        "id": "rom10-ps19",
        "book_id": "rom",
        "chapter": 10,
        "verse_start": 18,
        "verse_end": 18,
        "title": "Their Voice Went Out vs. Measuring Line: Romans 10 Quoting LXX Psalm 19",
        "ref": "Romans 10:18 / Psalm 19:4 (LXX 18:5)",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "St. Paul proves the universal proclamation of the Gospel by quoting Psalm 19:4: 'Their voice (ὁ φθόγγος αὐτῶν) has gone out into all the earth.' The Masoretic Text reads 'their measuring line' (קַוָּם, qaw-wam), whereas the Septuagint had 'qolam' (their voice).",
        "english": "‘But I ask, have they not heard? Indeed they have, for “Their voice has gone out to all the earth, and their words to the ends of the world.”’",
        "vulgate": "Et quidem in omnem terram exivit sonus eorum, et in fines orbis terrae verba eorum.",
        "greek_hebrew": "Εἰς πᾶσαν τὴν γῆν ἐξῆλθεν ὁ φθόγγος αὐτῶν, καὶ εἰς τὰ πέρατα τῆς οἰκουμένης τὰ ῥήματα αὐτῶν.",
        "interlinear": [
            {"w": "ὁ φθόγγος", "t": "ho phthongos", "pos": "N-NMS", "lemma": "φθόγγος", "strong": "G5353", "m": "the voice / sound"},
            {"w": "αὐτῶν", "t": "autōn", "pos": "P-G3P", "lemma": "αὐτός", "strong": "G846", "m": "of them"},
            {"w": "τὰ ῥήματα", "t": "ta rhēmata", "pos": "N-NNP", "lemma": "ῥῆμα", "strong": "G4487", "m": "the words"}
        ],
        "apparatus": [
            {"witness": "Romans 10:18 (NA28 / P46, Vaticanus)", "text": "ἐξῆλθεν ὁ φθόγγος αὐτῶν (their voice went out)", "note": "Paul adopts LXX verbatim.", "tier": "gold"},
            {"witness": "Psalm 18:5 (LXX Rahlfs)", "text": "εἰς πᾶσαν τὴν γῆν ἐξῆλθεν ὁ φθόγγος αὐτῶν", "note": "Reflects Hebrew vorlage 'qolam' (their voice).", "tier": "gold"},
            {"witness": "Psalm 19:4 (Hebrew MT / BHS / KJV)", "text": "בְּכָל־הָאָרֶץ יָצָא קַוָּם (yatsa qaw-wam - measuring line)", "note": "Missing letter lamed or scribal divergence between voice (קולם) and line (קום).", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Augustine of Hippo", "work": "Expositions on the Psalms (Enarrationes in Ps. 18)", "text": "Applies the LXX/Latin reading ('Their sound went out into all the earth') directly to the Apostolic missionary proclamation cited by Paul in Romans 10:18."}
        ],
        "strata_3d": {
            "top_text": "Their voice has gone out to all the earth, and their words to the ends of the world",
            "greek_text": "Εἰς πᾶσαν τὴν γῆν ἐξῆλθεν ὁ φθόγγος αὐτῶν",
            "uncial_text": "ΕΙC ΠΑCΑΝ ΤΗΝ ΓΗΝ ΕΞΗΛΘΕΝ Ο ΦΘΟΓΓΟC ΑΥΤΩΝ",
            "hebrew_mt": "בְּכָל־הָאָרֶץ יָצָא קַוָּם (Their measuring line went out)",
            "vorlage_dss": "Vorlage reading קולם (their voice) matches Paul and LXX"
        }
    },
    {
        "id": "gal3-deut21",
        "book_id": "gal",
        "chapter": 3,
        "verse_start": 13,
        "verse_end": 13,
        "title": "Cursed on a Tree vs. Cursed of God: Galatians 3:13 & LXX/11QTemple",
        "ref": "Galatians 3:13 / Deuteronomy 21:23",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "St. Paul argues Christ redeemed us from the curse of the Law by citing Deuteronomy 21:23: 'Cursed is everyone who is hanged on a tree' (ἐπὶ ξύλου), carefully following the Septuagint and 11QTemple Scroll order rather than the Masoretic phrasing 'cursed of God' (qillat Elohim).",
        "english": "Christ redeemed us from the curse of the law by becoming a curse for us—for it is written, ‘Cursed is everyone who is hanged on a tree.’",
        "vulgate": "Christus nos redemit de maledicto legis, factus pro nobis maledictum: quia scriptum est: Maledictus omnis qui pendet in ligno.",
        "greek_hebrew": "Χριστὸς ἡμᾶς ἐξηγόρασεν ἐκ τῆς κατάρας τοῦ νόμου... Ἐπικατάρατος πᾶς ὁ κρεμάμενος ἐπὶ ξύλου.",
        "interlinear": [
            {"w": "Ἐπικατάρατος", "t": "Epikataratos", "pos": "Adj-NMS", "lemma": "ἐπικατάρατος", "strong": "G1944", "m": "Cursed"},
            {"w": "ὁ κρεμάμενος", "t": "ho kremamenos", "pos": "V-PMP-NMS", "lemma": "κρεμάννυμι", "strong": "G2910", "m": "the one hanging"},
            {"w": "ἐπὶ ξύλου", "t": "epi xylou", "pos": "Prep-Phrase", "lemma": "ξύλον", "strong": "G3586", "m": "on a tree / wood"}
        ],
        "apparatus": [
            {"witness": "Galatians 3:13 (NA28 / P46, Vaticanus)", "text": "Ἐπικατάρατος πᾶς ὁ κρεμάμενος ἐπὶ ξύλου", "note": "Focuses curse upon crucifixion on the wood, omitting 'of God'.", "tier": "gold"},
            {"witness": "Deut 21:23 (LXX Rahlfs)", "text": "κεκατηραμένος ὑπὸ θεοῦ πᾶς κρεμάμενος ἐπὶ ξύλου", "note": "Contains the 'every' (πᾶς) found in Paul and the Temple Scroll, absent from MT.", "tier": "gold"},
            {"witness": "11QTemple Scroll (11Q19 col. 64)", "text": "כיא מקולל אלוהים ואנשים תלוי על העץ", "note": "Matches word order and 'hanged upon a tree' for Roman/Hasmonean crucifixion.", "tier": "gold"}
        ],
        "patristics": [
            {"father": "St. Justin Martyr", "work": "Dialogue with Trypho 96", "text": "Expounds Deuteronomy 21:23 in Dialogue 96, arguing the prophetic curse upon the wood points to Christ bearing Israel's curse on the Cross rather than being cursed by God."}
        ],
        "strata_3d": {
            "top_text": "Cursed is everyone who is hanged on a tree",
            "greek_text": "Ἐπικατάρατος πᾶς ὁ κρεμάμενος ἐπὶ ξύλου",
            "uncial_text": "ΕΠΙΚΑΤΑΡΑΤΟC ΠΑC Ο ΚΡΕΜΑΜΕΝΟC ΕΠΙ ΞΥΛΟΥ",
            "hebrew_mt": "קִלְלַת אֱלֹהִים תָּלוּי (omits 'every' and adds 'curse of God')",
            "vorlage_dss": "11QTemple Scroll col. 64 matches Pauline crucifixion exegesis"
        }
    },
    {
        "id": "1tim3-god-manifest",
        "book_id": "1tim",
        "chapter": 3,
        "verse_start": 16,
        "verse_end": 16,
        "title": "God Was Manifest in the Flesh: The Uncial Crux (ΘΣ vs ΟΣ)",
        "ref": "1 Timothy 3:16 / Codex Alexandrinus / Codex Sinaiticus",
        "tier": "gold",
        "tier_name": "Tier 1: Ancient Vorlage Divergence",
        "summary": "1 Timothy 3:16 contains one of the most famous textual cruxes in history: Did Paul write 'God was manifested in the flesh' (Θεός, abbreviated as the nomen sacrum ΘΣ), or 'He who was manifested' (Ὃς / ΟΣ)? In Codex Alexandrinus, scribal strokes turned ΟΣ into ΘΣ with a crossbar. The Latin Vulgate reads 'quod manifestatum est in carne' referring to the mystery.",
        "english": "‘Great indeed, we confess, is the mystery of godliness: He [or God] was manifested in the flesh, vindicated by the Spirit, seen by angels, proclaimed among the nations, believed on in the world, taken up in glory.’",
        "vulgate": "Et manifeste magnum est pietatis sacramentum, quod manifestatum est in carne, justificatum est in spiritu, apparuit angelis...",
        "greek_hebrew": "Καὶ ὁμολογουμένως μέγα ἐστὶν τὸ τῆς εὐσεβείας μυστήριον· Ὃς [Θεὸς] ἐφανερώθη ἐν σαρκί...",
        "interlinear": [
            {"w": "μέγα ἐστὶν", "t": "mega estin", "pos": "Adj / Verb", "lemma": "μέγας", "strong": "G3173", "m": "great is"},
            {"w": "τὸ τῆς εὐσεβείας", "t": "to tēs eusebeias", "pos": "Noun", "lemma": "εὐσέβεια", "strong": "G2150", "m": "of godliness"},
            {"w": "μυστήριον", "t": "mystērion", "pos": "Noun", "lemma": "μυστήριον", "strong": "G3466", "m": "the mystery"},
            {"w": "ἐφανερώθη", "t": "ephanerōthē", "pos": "V-AIP-3S", "lemma": "φανερόω", "strong": "G5319", "m": "was manifested"},
            {"w": "ἐν σαρκί", "t": "en sarki", "pos": "Prep-Phrase", "lemma": "σάρξ", "strong": "G4561", "m": "in the flesh"}
        ],
        "apparatus": [
            {"witness": "NA28 / Codex Sinaiticus (ℵ*) / Codex Vaticanus", "text": "Ὃς ἐφανερώθη ἐν σαρκί (He who was manifested)", "note": "Relative pronoun introducing an early Christian liturgical hymn.", "tier": "sapphire"},
            {"witness": "Textus Receptus / Codex Alexandrinus corrector (Ac)", "text": "Θεὸς ἐφανερώθη ἐν σαρκί (God was manifested in the flesh)", "note": "Traditional Byzantine reading; nomen sacrum ΘΣ with supralinear stroke.", "tier": "gold"},
            {"witness": "Latin Vulgate (Clementine / Codex Amiatinus)", "text": "quod manifestatum est in carne (which was manifested in the flesh)", "note": "Neuter relative pronoun referring back to sacramentum (μυστήριον).", "tier": "sapphire"}
        ],
        "patristics": [
            {"father": "St. John Chrysostom", "work": "Homilies on 1 Timothy 11", "text": "Reads 'God was manifested in the flesh' (Θεὸς ἐφανερώθη) to extol the incarnational mystery of the Creator becoming visible in human flesh."},
            {"father": "St. Gregory of Nyssa", "work": "Against Eunomius / On Christological Incarnation", "text": "Appeals to the mystery revealed in the flesh to uphold the full divine nature united to human nature against Eunomian subordinationism."}
        ],
        "strata_3d": {
            "top_text": "Great indeed is the mystery of godliness: He was manifested in the flesh",
            "greek_text": "Ὃς [Θεὸς] ἐφανερώθη ἐν σαρκί",
            "uncial_text": "ΟC / ΘC ΕΦΑΝΕΡΩΘΗ ΕΝ CΑΡΚΙ (Alexandrinus Uncial Crux)",
            "hebrew_mt": "[NEW TESTAMENT GREEK EXCLUSIVE]",
            "vorlage_dss": "Liturgical hymn on the Incarnation of the Divine Word"
        }
    },
    {
        "id": "1john5-comma",
        "book_id": "1john",
        "chapter": 5,
        "verse_start": 7,
        "verse_end": 8,
        "title": "The Comma Johanneum: The Three Heavenly Witnesses",
        "ref": "1 John 5:7–8 / Latin Vulgate / Council of Trent",
        "tier": "crimson",
        "tier_name": "Tier 2: Doctrinal Crux (Trinitarian Witness)",
        "summary": "1 John 5:7–8 in the Latin Vulgate contains the explicit confession of the Holy Trinity: 'For there are three that bear record in heaven: the Father, the Word, and the Holy Spirit; and these three are one.' Modern Greek critical editions omit the heavenly witnesses because they appear in few Greek manuscripts, but the reading was preserved in Old Latin and Vulgate patristic manuscripts from the 3rd century.",
        "english": "‘For there are three that testify in heaven: the Father, the Word, and the Holy Spirit; and these three are one. And there are three that testify on earth: the Spirit, the water, and the blood; and these three agree.’",
        "vulgate": "Quoniam tres sunt, qui testimonium dant in caelo: Pater, Verbum, et Spiritus Sanctus: et hi tres unum sunt. Et tres sunt, qui testimonium dant in terra: spiritus, et aqua, et sanguis: et hi tres unum sunt.",
        "greek_hebrew": "ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες [ἐν τῷ οὐρανῷ, ὁ Πατήρ, ὁ Λόγος, καὶ τὸ Ἅγιον Πνεῦμα, καὶ οὗτοι οἱ τρεῖς ἕν εἰσιν]...",
        "interlinear": [
            {"w": "ὁ Πατήρ", "t": "ho Patēr", "pos": "Noun", "lemma": "πατήρ", "strong": "G3962", "m": "the Father"},
            {"w": "ὁ Λόγος", "t": "ho Logos", "pos": "Noun", "lemma": "λόγος", "strong": "G3056", "m": "the Word"},
            {"w": "τὸ Ἅγιον Πνεῦμα", "t": "to Hagion Pneuma", "pos": "Noun", "lemma": "πνεῦμα", "strong": "G4151", "m": "the Holy Spirit"},
            {"w": "καὶ οὗτοι οἱ τρεῖς", "t": "kai houtoi hoi treis", "pos": "Phrase", "lemma": "τρεῖς", "strong": "G5140", "m": "and these three"},
            {"w": "ἕν εἰσιν", "t": "hen eisin", "pos": "Phrase", "lemma": "εἰμί", "strong": "G1510", "m": "are one"}
        ],
        "apparatus": [
            {"witness": "Latin Vulgate (Clementine Edition / Council of Trent)", "text": "Pater, Verbum, et Spiritus Sanctus: et hi tres unum sunt", "note": "Received liturgical text of the Western Catholic Church.", "tier": "crimson"},
            {"witness": "Old Latin (Itala / Codex Speculum, 5th c.)", "text": "Testified by St. Cyprian (c. 250 AD) and Priscillian (c. 385 AD).", "note": "Proves the reading was known in the West centuries before the Vulgate standardization.", "tier": "crimson"},
            {"witness": "NA28 / Modern Critical Greek Text", "text": "OMITS Heavenly Witnesses", "note": "Reading present in Greek only in Codex Montfortianus (16th c.) and Ottobonianus (15th c.).", "tier": "sapphire"}
        ],
        "patristics": [
            {"father": "St. Cyprian of Carthage", "work": "De Catholicae Ecclesiae Unitate 6 (c. 251 AD)", "text": "‘The Lord says: I and the Father are one; and again it is written of the Father, and of the Son, and of the Holy Spirit: And these three are one.’"},
            {"father": "Council of Carthage (484 AD)", "work": "Confession of Faith of the Bishops of Africa", "text": "Presented to the Arian Vandal king Huneric, quoting 1 John 5:7 as proof of the Trinity."}
        ],
        "strata_3d": {
            "top_text": "There are three that testify in heaven: the Father, the Word, and the Holy Spirit",
            "greek_text": "τρεῖς εἰσιν οἱ μαρτυροῦντες: ὁ Πατήρ, ὁ Λόγος, καὶ τὸ Ἅγιον Πνεῦμα",
            "uncial_text": "TRES SUNT QUI TESTIMONIUM DANT IN CAELO (Latin Vulgate Stream)",
            "hebrew_mt": "[NEW TESTAMENT EXCLUSIVE]",
            "vorlage_dss": "Old Latin African textual stream (St. Cyprian / Council of Carthage 484)"
        }
    },
    {
        "id": "luke1-kecharitomene",
        "book_id": "luke",
        "chapter": 1,
        "verse_start": 28,
        "verse_end": 28,
        "title": "Gratia Plena / Kecharitōmenē: The Angelic Salutation to Mary",
        "ref": "Luke 1:28 / St. Jerome / Papal Bull Ineffabilis Deus",
        "tier": "crimson",
        "tier_name": "Tier 2: Doctrinal Crux (Marian Dogma)",
        "summary": "Gabriel salutes the Virgin Mary as 'κεχαριτωμένη' (kecharitōmenē), a perfect passive participle denoting a permanent, abiding state of having been entirely transformed by divine grace. St. Jerome translated it into the famous Latin 'Gratia Plena' (Full of Grace), forming the scriptural cornerstone of the Immaculate Conception.",
        "english": "‘And the angel came in unto her, and said: Hail, full of grace, the Lord is with thee: blessed art thou among women.’",
        "vulgate": "Et ingressus angelus ad eam dixit: Ave gratia plena: Dominus tecum: benedicta tu in mulieribus.",
        "greek_hebrew": "καὶ εἰσελθὼν πρὸς αὐτὴν εἶπεν· Χαῖρε, κεχαριτωμένη, ὁ Κύριος μετὰ σοῦ.",
        "interlinear": [
            {"w": "Χαῖρε", "t": "Chaire", "pos": "V-PMA-2S", "lemma": "χαίρω", "strong": "G5463", "m": "Hail / Rejoice"},
            {"w": "κεχαριτωμένη", "t": "kecharitōmenē", "pos": "V-RPP-NFS", "lemma": "χαριτόω", "strong": "G5487", "m": "one transformed by grace / favored"},
            {"w": "ὁ Κύριος", "t": "ho Kyrios", "pos": "Noun", "lemma": "κύριος", "strong": "G2962", "m": "the Lord"},
            {"w": "μετὰ σοῦ", "t": "meta sou", "pos": "Prep-Phrase", "lemma": "μετά", "strong": "G3326", "m": "is with you"}
        ],
        "apparatus": [
            {"witness": "Luke 1:28 (NA28 / P75, Vaticanus, Sinaiticus)", "text": "Χαῖρε, κεχαριτωμένη, ὁ Κύριος μετὰ σοῦ", "note": "Perfect passive participle replaces her name, serving as a title.", "tier": "crimson"},
            {"witness": "Latin Vulgate (Clementine / Jerome)", "text": "Ave gratia plena: Dominus tecum: benedicta tu in mulieribus", "note": "The universal liturgical 'Hail Mary' of Catholic Christendom.", "tier": "crimson"},
            {"witness": "Syriac Peshitta", "text": "Shlam lekh malyath taybutha", "note": "Translates verbatim: 'Peace to you, full of grace.'", "tier": "sapphire"}
        ],
        "patristics": [
            {"father": "Pope Bl. Pius IX (1854)", "work": "Ineffabilis Deus (Apostolic Constitution)", "text": "Points to Gabriel's unique salutation κεχαριτωμένη / gratia plena as declaring the Mother of God uniquely endowed with the fullness of sanctifying grace from her conception."},
            {"father": "St. Ephrem the Syrian", "work": "Nisibene Hymns 27.8", "text": "Extols Christ and His Mother alone as wholly pure and free from every stain or blemish of sin."}
        ],
        "strata_3d": {
            "top_text": "Hail, full of grace, the Lord is with you: blessed are you among women",
            "greek_text": "Χαῖρε, κεχαριτωμένη, ὁ Κύριος μετὰ σοῦ",
            "uncial_text": "ΧΑΙΡΕ ΚΕΧΑΡΙΤΩΜΕΝΗ Ο ΚC ΜΕΤΑ CΟΥ",
            "hebrew_mt": "[NEW TESTAMENT GREEK EXCLUSIVE]",
            "vorlage_dss": "Perfect passive participle 'kecharitōmenē' (abiding plenitude of divine grace)"
        }
    },
    {
        "id": "2thess2-traditions",
        "book_id": "2thess",
        "chapter": 2,
        "verse_start": 15,
        "verse_end": 15,
        "title": "Apostolic Traditions: Oral & Written vs. Sola Scriptura",
        "ref": "2 Thessalonians 2:15 / Council of Trent / Vatican II Dei Verbum",
        "tier": "crimson",
        "tier_name": "Tier 2: Doctrinal Crux (Apostolic Authority)",
        "summary": "St. Paul commands the church to hold fast to apostolic traditions transmitted BOTH by word of mouth (oral Sacred Tradition) and by epistle (written Sacred Scripture). This verse directly refutes the Protestant dogma of Sola Scriptura.",
        "english": "‘Therefore, brethren, stand fast; and hold the traditions which you have learned, whether by word, or by our epistle.’",
        "vulgate": "Itaque fratres, state: et tenete traditiones, quas didicistis, sive per sermonem, sive per epistolam nostram.",
        "greek_hebrew": "ἄρα οὖν, ἀδελφοί, στήκετε, καὶ κρατεῖτε τὰς παραδόσεις ἃς ἐδιδάχθητε εἴτε διὰ λόγου εἴτε δι' ἐπιστολῆς ἡμῶν.",
        "interlinear": [
            {"w": "στήκετε", "t": "stēkete", "pos": "V-PMA-2P", "lemma": "στήκω", "strong": "G4739", "m": "stand firm"},
            {"w": "καὶ κρατεῖτε", "t": "kai krateite", "pos": "V-PMA-2P", "lemma": "κρατέω", "strong": "G2902", "m": "and hold fast to"},
            {"w": "τὰς παραδόσεις", "t": "tas paradoseis", "pos": "N-AFP", "lemma": "παράδοσις", "strong": "G3862", "m": "the traditions"},
            {"w": "εἴτε διὰ λόγου", "t": "eite dia logou", "pos": "Phrase", "lemma": "λόγος", "strong": "G3056", "m": "whether by word / oral teaching"},
            {"w": "εἴτε δι' ἐπιστολῆς", "t": "eite di' epistolēs", "pos": "Phrase", "lemma": "ἐπιστολή", "strong": "G1992", "m": "or by epistle / letter"}
        ],
        "apparatus": [
            {"witness": "2 Thessalonians 2:15 (NA28 / P30, Vaticanus, Sinaiticus)", "text": "κρατεῖτε τὰς παραδόσεις... εἴτε διὰ λόγου εἴτε δι' ἐπιστολῆς ἡμῶν", "note": "Direct apostolic command establishing dual transmission of revelation.", "tier": "crimson"},
            {"witness": "Latin Vulgate (Clementine)", "text": "tenete traditiones, quas didicistis, sive per sermonem, sive per epistolam", "note": "Unbroken Western reception of oral apostolic tradition.", "tier": "crimson"},
            {"witness": "Protestant Sola Scriptura Polemics", "text": "Attempts to restrict 'traditions' only to what was later written down.", "note": "Grammatically refuted by the disjunctive 'either... or' (εἴτε... εἴτε).", "tier": "crimson"}
        ],
        "patristics": [
            {"father": "St. John Chrysostom", "work": "Homilies on 2 Thessalonians 4", "text": "‘Hence it is manifest, that they did not deliver all things by epistle, but many things also unwritten, and in like manner both the one and the other are worthy of credit. Therefore let us think the tradition of the Church also worthy of credit.’"},
            {"father": "Council of Trent (1546)", "work": "Session IV Decree on Sacred Scripture and Traditions", "text": "‘Receives and venerates with an equal affection of piety and reverence all the books both of the Old and of the New Testament... as also the said traditions, as well those appertaining to faith as to morals.’"}
        ],
        "strata_3d": {
            "top_text": "Hold fast to the traditions which you were taught, whether by word of mouth or by our letter",
            "greek_text": "κρατεῖτε τὰς παραδόσεις ἃς ἐδιδάχθητε εἴτε διὰ λόγου εἴτε δι' ἐπιστολῆς ἡμῶν",
            "uncial_text": "ΚΡΑΤΕΙΤΕ ΤΑC ΠΑΡΑΔΟCΕΙC ΕΙΤΕ ΔΙΑ ΛΟΓΟΥ ΕΙΤΕ ΔΙ ΕΠΙCΤΟΛΗC ΗΜΩΝ",
            "hebrew_mt": "[NEW TESTAMENT EXCLUSIVE]",
            "vorlage_dss": "Apostolic depositum fidei (Sacred Tradition & Sacred Scripture co-equal)"
        }
    }
]

THREE_JS_PATH = os.path.join(SCRIPT_DIR, 'three.min.js')

# Core Clementine & Nova Vulgata Latin theological glossary (lowercased stripped stem/form keys)
LATIN_LEX = {
    "principio": ["principium", "in the beginning (Gen 1:1 / John 1:1)"],
    "verbum": ["Verbum", "Word, Divine Logos (John 1:1)"],
    "caro": ["caro", "flesh, Incarnation (John 1:14)"],
    "gratia": ["gratia", "grace, divine favor / infused life"],
    "plena": ["plenus", "full (Luke 1:28: gratia plena)"],
    "spiritus": ["Spiritus", "Spirit, Holy Spirit, breath"],
    "dominus": ["Dominus", "Lord"],
    "deus": ["Deus", "God"],
    "filius": ["filius", "Son"],
    "pater": ["pater", "Father"],
    "corpus": ["corpus", "body (Eucharist / Heb 10:5 corpus autem aptasti mihi)"],
    "sanguis": ["sanguis", "blood"],
    "hostia": ["hostia", "sacrificial victim/host (Eph 5:2 / Ps 39:7)"],
    "sacramentum": ["sacramentum", "sacrament, sacred mystery (1 Tim 3:16 / Eph 5:32)"],
    "mysterium": ["mysterium", "mystery, secret plan"],
    "justitia": ["justitia", "righteousness / justice (both moral and judicial)"],
    "iustitia": ["iustitia", "righteousness / justice (Nova Vulgata orthography)"],
    "justificatur": ["justifico", "is justified / made righteous (Rom 3:28 / Jas 2:24)"],
    "iustificatur": ["iustifico", "is justified / made righteous (Nova Vulgata)"],
    "fides": ["fides", "faith, fidelity"],
    "fide": ["fides", "by faith"],
    "opera": ["opus", "works, deeds (Jas 2:24)"],
    "operibus": ["opus", "by/from works"],
    "poenitentiam": ["poenitentia", "penance, repentance (Acts 2:38)"],
    "paenitentiam": ["paenitentia", "penance, repentance (Nova Vulgata)"],
    "traditiones": ["traditio", "traditions handed down (2 Thess 2:15)"],
    "ecclesia": ["ecclesia", "the Church (Matt 16:18)"],
    "petra": ["petra", "rock, bedrock foundation (Matt 16:18)"],
    "petrus": ["Petrus", "Peter / Rock"],
    "claves": ["clavis", "keys of authority (Isa 22:22 / Matt 16:19)"],
    "virgo": ["virgo", "virgin (Isa 7:14 / Matt 1:23)"],
    "mulier": ["mulier", "woman (Gen 3:15 / Rev 12:1)"],
    "semen": ["semen", "seed, offspring (Gen 3:15)"],
    "sanctus": ["sanctus", "holy, saint"],
    "angelus": ["angelus", "angel, messenger"],
    "caelum": ["caelum", "heaven"],
    "caelos": ["caelum", "the heavens (Gen 1:1)"],
    "terra": ["terra", "earth, land"],
    "terram": ["terra", "the earth (Gen 1:1)"],
    "lux": ["lux", "light"],
    "vita": ["vita", "life"],
    "mortem": ["mors", "death"],
    "resurrectionem": ["resurrectio", "resurrection (Heb 11:35)"],
    "peccatum": ["peccatum", "sin"],
    "eleemosynam": ["eleemosyna", "almsgiving (Luke 11:41 / Tobit / Sirach)"],
    "caritas": ["caritas", "charity, theological love"],
    "testamentum": ["testamentum", "covenant, testament"],
    "altare": ["altare", "altar"],
    "sacerdos": ["sacerdos", "priest"],
    "foderunt": ["fodio", "they pierced/dug (Vulg Ps 21:17)"],
    "ipsa": ["ipse/ipsa", "she / the offspring's mother shall crush (Vulg Gen 3:15)"],
    "egrediamur": ["egredior", "let us go outside (Vulg Gen 4:8 preserved from LXX/DSS)"],
    "fidelis": ["fidelis", "faithful (Vulg Ps 144:13b Nun acrostic)"],
    "panis": ["panis", "bread"],
    "calix": ["calix", "chalice, cup"],
    "pax": ["pax", "peace"],
    "gloria": ["gloria", "glory"],
    "regnum": ["regnum", "kingdom"],
    "veritas": ["veritas", "truth"],
    "creavit": ["creo", "created (Gen 1:1)"],
    "dixit": ["dico", "said, spoke"],
    "requirant": ["requiro", "may seek / search after (Acts 15:17)"],
    "gentes": ["gens", "nations, Gentiles"],
    "misericordia": ["misericordia", "mercy, steadfast lovingkindness"],
}

# Verified Bidirectional Canonical Cross-References across all 73 Books (aligned to DRA/Vulgate/LXX numbering)
CROSS_REFS = [
    {"id": "xr-gen1-john1", "a": ["gen", 1, 1], "b": ["john", 1, 1], "tier": "sapphire", "title": "Creation Word & Eternal Logos", "note": "John 1:1 ('En arche hen ho Logos') echoes Genesis 1:1 ('En arche epoiesen ho Theos') via the LXX opening phrase."},
    {"id": "xr-gen3-luke1", "a": ["gen", 3, 15], "b": ["luke", 1, 28], "tier": "crimson", "title": "Protoevangelium & New Eve", "note": "The enmity between the Woman and the Serpent culminates at Gabriel's greeting to Mary (Gratia Plena)."},
    {"id": "xr-gen3-rev12", "a": ["gen", 3, 15], "b": ["rev", 12, 1], "tier": "crimson", "title": "Woman & Dragon Apocalyptic Fulfilment", "note": "The Genesis 3 Woman and her Seed face the ancient Serpent in Apocalypse 12."},
    {"id": "xr-gen11-luke3", "a": ["gen", 11, 12], "b": ["luke", 3, 36], "tier": "gold", "title": "Second Cainan Genealogy (LXX vs MT)", "note": "Luke 3:36 preserves Arphaxad -> Cainan -> Shelah from the Septuagint; missing in Masoretic Gen 11:12."},
    {"id": "xr-deut21-gal3", "a": ["deut", 21, 23], "b": ["gal", 3, 13], "tier": "gold", "title": "Cursed Upon a Tree", "note": "Galatians 3:13 follows LXX & 11QTemple word order ('Cursed is everyone hanged on a tree')."},
    {"id": "xr-deut32-heb1", "a": ["deut", 32, 43], "b": ["heb", 1, 6], "tier": "gold", "title": "Let All God's Angels Worship Him (4QDeut-q)", "note": "Hebrews 1:6 quotes a Deut 32:43 line extant in LXX & 4QDeut-q but omitted in the Masoretic Text."},
    {"id": "xr-ps8-matt21", "a": ["ps", 8, 3], "b": ["matt", 21, 16], "tier": "gold", "title": "Perfected Praise vs Ordained Strength", "note": "Jesus in the Temple quotes LXX Psalm 8:3 ('perfected praise') against MT ('established strength')."},
    {"id": "xr-ps18-rom10", "a": ["ps", 18, 5], "b": ["rom", 10, 18], "tier": "gold", "title": "Their Voice Went Out to All the Earth", "note": "Paul cites LXX Psalm 18:5 ('phthongos' = voice) against MT Psalm 19:4 ('qaw-wam' = measuring line)."},
    {"id": "xr-ps21-john19", "a": ["ps", 21, 17], "b": ["john", 19, 37], "tier": "gold", "title": "Pierced Hands, Feet & Side", "note": "Catholic/LXX Psalm 21:17 ('they pierced my hands and feet', corroborated by 5/6HevPs) & John's Passion witness."},
    {"id": "xr-ps39-heb10", "a": ["ps", 39, 7], "b": ["heb", 10, 5], "tier": "gold", "title": "A Body You Prepared for Me vs Ears Dug", "note": "Hebrews 10:5 rests on the Greek body-prepared reading (Codices B/א/A Ps 39:7) vs MT ('ears you dug')."},
    {"id": "xr-isa7-matt1", "a": ["isa", 7, 14], "b": ["matt", 1, 23], "tier": "gold", "title": "Virgin Conception (Parthenos vs Almah)", "note": "Matthew quotes pre-Christian Jewish LXX 'parthenos' (virgin) for the Emmanuel prophecy."},
    {"id": "xr-isa22-matt16", "a": ["isa", 22, 22], "b": ["matt", 16, 19], "tier": "crimson", "title": "Keys of the House of David -> Petrine Keys", "note": "Christ transfers the Davidic royal steward keys (bind/loose, open/shut) from Isaiah 22:22 to St. Peter."},
    {"id": "xr-isa61-luke4", "a": ["isa", 61, 1], "b": ["luke", 4, 18], "tier": "gold", "title": "Recovery of Sight to the Blind (Nazareth Scroll)", "note": "Christ reads the blind-sight restoration clause in Luke 4:18 (present in LXX Isa 61:1, absent from MT)."},
    {"id": "xr-amos9-acts15", "a": ["amos", 9, 12], "b": ["acts", 15, 17], "tier": "gold", "title": "Seek the Lord vs Possess Edom", "note": "St. James settles Council of Jerusalem via LXX Amos 9:12 ('seek the Lord') against MT ('possess Edom')."},
    {"id": "xr-tob12-rev8", "a": ["tob", 12, 15], "b": ["rev", 8, 2], "tier": "crimson", "title": "Seven Holy Angels Before God", "note": "Apocalypse 8:2 draws directly on the Seven Archangels angelology unique to Catholic Tobit 12:15."},
    {"id": "xr-wis2-matt27", "a": ["wis", 2, 18], "b": ["matt", 27, 43], "tier": "crimson", "title": "Chief Priests' CrucifixionTaunt from Wisdom 2", "note": "The scribes at Calvary mock Jesus verbatim in the wicked plots of Deuterocanonical Wisdom 2:18."},
    {"id": "xr-wis7-heb1", "a": ["wis", 7, 26], "b": ["heb", 1, 3], "tier": "crimson", "title": "Apaugasma (Radiance of Eternal Glory)", "note": "Hebrews 1:3 borrows its defining Nicaean Christological noun 'apaugasma' directly from Wisdom 7:26."},
    {"id": "xr-wis3-1pet3", "a": ["wis", 3, 1], "b": ["1pet", 3, 19], "tier": "sapphire", "title": "Souls of the Righteous in God's Hand", "note": "Deuterocanonical anthropology of intermediate conscious disembodied souls preserved across Wisdom & 1 Peter."},
    {"id": "xr-sir3-luke11", "a": ["sir", 3, 33], "b": ["luke", 11, 41], "tier": "crimson", "title": "Almsgiving Atones & Cleanses", "note": "Jesus commands 'give alms and behold all things are clean unto you', echoing Sirach 3:33 (LXX v.30)."},
    {"id": "xr-bar3-john1", "a": ["bar", 3, 38], "b": ["john", 1, 14], "tier": "crimson", "title": "Seen on Earth & Dwelt Among Men", "note": "Patristic Christological link between Baruch 3:36–38 ('seen upon earth') and John 1:14 ('dwelt among us')."},
    {"id": "xr-2macc7-heb11", "a": ["2macc", 7, 9], "b": ["heb", 11, 35], "tier": "crimson", "title": "Martyrdom on the Rack for a Better Resurrection", "note": "Hebrews 11:35b summarizes the Deuterocanonical Maccabean martyrs refusing release on hope of resurrection."},
    {"id": "xr-2macc12-matt12", "a": ["2macc", 12, 45], "b": ["matt", 12, 32], "tier": "crimson", "title": "Prayer for the Dead & Forgiveness in Age to Come", "note": "Judas Maccabeus's sin-offering for the fallen (2 Macc 12:45; split across v.45–46 in Vulgate/DRA) pairs with Christ teaching post-mortem remission."},
    {"id": "xr-john6-1cor11", "a": ["john", 6, 53], "b": ["1cor", 11, 24], "tier": "crimson", "title": "Eucharistic Flesh & Covenant Institution", "note": "Bread of Life discourse ('sarx' & 'haima') fulfilled in Paul's liturgical paradosis of the Last Supper."},
    {"id": "xr-rom3-jas2", "a": ["rom", 3, 28], "b": ["jas", 2, 24], "tier": "crimson", "title": "Faith vs Faith & Works Justification Synthesis", "note": "James 2:24 supplies the ONLY explicit biblical 'not by faith alone' (ouk ek pisteos monon) refuting Sola Fide."},
    {"id": "xr-2thess2-1thess2", "a": ["2thess", 2, 15], "b": ["1thess", 2, 13], "tier": "crimson", "title": "Sacred Tradition (Word of Mouth & Epistle)", "note": "Apostolic kerygma received by spoken word and written letter prior to any closed NT canon."},
]


def load_lexicon_and_links():
    """Load BibleHub-grade OpenScriptures Strongs G+H, TAGNT+LXX Greek morph, TAHOT Hebrew morph, and DRA word->Strongs links."""
    print(f"Loading precompiled lexicon bundle from {LEXICON_BUNDLE_PATH}...")
    with open(LEXICON_BUNDLE_PATH, 'r', encoding='utf-8') as f:
        bundle = json.load(f)

    strongs_gloss = bundle['strongs_gloss']
    greek_morph = bundle['greek_morph']
    hebrew_morph = bundle['hebrew_morph']

    # Defensive verification of known fixed entries
    assert greek_morph.get('εκζητησωσιν', '').endswith('G1567'), "Acts 15:17 G1567 fix missing in greek_morph!"
    assert len(strongs_gloss) >= 14000, f"strongs_gloss count low: {len(strongs_gloss)}"
    assert len(greek_morph) >= 45000, f"greek_morph count low: {len(greek_morph)}"
    assert len(hebrew_morph) >= 35000, f"hebrew_morph count low: {len(hebrew_morph)}"

    print(f"Loading DRA Strongs alignment links from {DRA_LINKS_PATH}...")
    with open(DRA_LINKS_PATH, 'r', encoding='utf-8') as f:
        raw_links = json.load(f)

    compact_links = {}
    for k, wd in raw_links.items():
        if isinstance(wd, dict) and wd:
            compact_links[k] = '|'.join(f"{w}:{st}" for w, st in wd.items())

    print(f"Lexicons ready -> Strongs: {len(strongs_gloss)} | Greek: {len(greek_morph)} | Hebrew: {len(hebrew_morph)} | DRA verse links: {len(compact_links)}")
    return strongs_gloss, greek_morph, hebrew_morph, compact_links


def map_wlc_psalm(wlc_book, vulg_chap_num):
    """Align Masoretic WLC Psalms numbering onto Catholic Vulgate/LXX/DRA Psalm numbering."""
    chaps = wlc_book['chapters']
    if vulg_chap_num <= 8:
        return [v['text'] for v in chaps[vulg_chap_num - 1]['verses']], None
    elif vulg_chap_num == 9:
        v9 = [v['text'] for v in chaps[8]['verses']]
        v10 = [v['text'] for v in chaps[9]['verses']]
        return v9 + v10, "MT numbering: combines Hebrew Ps 9 & Ps 10 into Vulgate/LXX Ps 9"
    elif 10 <= vulg_chap_num <= 112:
        return [v['text'] for v in chaps[vulg_chap_num]['verses']], f"MT numbering: Hebrew WLC Ps {vulg_chap_num + 1}"
    elif vulg_chap_num == 113:
        v114 = [v['text'] for v in chaps[113]['verses']]
        v115 = [v['text'] for v in chaps[114]['verses']]
        return v114 + v115, "MT numbering: combines Hebrew Ps 114 & Ps 115 into Vulgate/LXX Ps 113"
    elif vulg_chap_num == 114:
        return [v['text'] for v in chaps[115]['verses'][:9]], "MT numbering: Hebrew WLC Ps 116:1–9"
    elif vulg_chap_num == 115:
        return [v['text'] for v in chaps[115]['verses'][9:]], "MT numbering: Hebrew WLC Ps 116:10–19"
    elif 116 <= vulg_chap_num <= 145:
        return [v['text'] for v in chaps[vulg_chap_num]['verses']], f"MT numbering: Hebrew WLC Ps {vulg_chap_num + 1}"
    elif vulg_chap_num == 146:
        return [v['text'] for v in chaps[146]['verses'][:11]], "MT numbering: Hebrew WLC Ps 147:1–11"
    elif vulg_chap_num == 147:
        return [v['text'] for v in chaps[146]['verses'][11:]], "MT numbering: Hebrew WLC Ps 147:12–20"
    else:
        return [v['text'] for v in chaps[vulg_chap_num - 1]['verses']], None

def load_esther_additions():
    """Extract Rahlfs Greek Esther sub-verse Additions A-F from LXX_final_main.csv (book 190)."""
    adds = {}
    if not os.path.exists(LXX_CSV_PATH):
        return adds

    def _clean(s):
        s = re.sub(r'<(?:S|m)>[^<]+</(?:S|m)>', '', s)
        s = re.sub(r'<br\s*/?>', ' ', s)
        s = re.sub(r'<[^>]+>', '', s)
        return re.sub(r'\s+', ' ', s).strip()

    with open(LXX_CSV_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.startswith('190\t'):
                continue
            parts = line.rstrip('\r\n').split('\t')
            if len(parts) < 4:
                continue
            key = (parts[1], parts[2])
            if key not in {('1', '1'), ('3', '13'), ('4', '17'), ('5', '1'), ('5', '2'), ('8', '12'), ('10', '3')}:
                continue
            segs = {}
            cur_tag = 'main'
            for chunk in re.split(r'(<i>\[[^\]]+\]</i>)', parts[3]):
                mt = re.match(r'<i>\[([^\]]+)\]</i>', chunk)
                if mt:
                    cur_tag = mt.group(1)
                else:
                    txt = _clean(chunk)
                    if txt:
                        segs[cur_tag] = txt
            adds[key] = segs
    return adds


def load_bible_datasets():
    print("Loading Approved Challoner Douay-Rheims (DRA) baseline (73 books)...")
    with open(DRA_PATH, 'r', encoding='utf-8') as f:
        dra = json.load(f)

    extra_paths = [
        ('rsv2ce', RSV2CE_PATH, 'Ignatius RSV-2CE (45 born-digital books)'),
        ('nova_vulg', NV_PATH, 'Vatican Nova Vulgata (73 books)'),
        ('webc', WEBC_PATH, 'World English Bible Catholic Edition (73 books)'),
        ('brenton', BRENTON_PATH, 'Brenton English Septuagint (46 books)'),
        ('kjva', KJVA_PATH, 'King James Version w/ Apocrypha (73 books)'),
        ('asv', ASV_PATH, 'American Standard Version 1901 (66 books)'),
        ('byz', BYZ_PATH, 'Byzantine Majority NT (27 books)'),
        ('tr', TR_PATH, 'Textus Receptus NT (27 books)'),
        ('net21', NET21_PATH, 'NET Bible 2.1 (66 books)'),
        ('niv_sb', NIV11_PATH, 'NIV Study Bible (66 books)'),
        ('bsb', BSB_PATH, 'Berean Standard Bible (66 books)'),
    ]
    extra_corpora = {}
    for key, p, label in extra_paths:
        print(f"Loading {label}...")
        with open(p, 'r', encoding='utf-8') as f:
            extra_corpora[key] = json.load(f)

    print("Loading Clementine Latin Vulgate dataset...")
    with open(VULG_PATH, 'r', encoding='utf-8') as f:
        vulg = json.load(f)

    print("Loading Statistical Restoration Greek New Testament dataset...")
    with open(GNT_PATH, 'r', encoding='utf-8') as f:
        gnt = json.load(f)

    print("Loading Westminster Leningrad Codex Hebrew Old Testament...")
    with open(WLC_PATH, 'r', encoding='utf-8') as f:
        wlc = json.load(f)

    print("Loading Rahlfs 1935 Greek Septuagint...")
    with open(LXX_PATH, 'r', encoding='utf-8') as f:
        lxx = json.load(f)

    esth_adds = load_esther_additions()

    vulg_map = {b['name']: b for b in vulg['books']}
    gnt_map = {b['name']: b for b in gnt['books']}
    wlc_map = {b['name']: b for b in wlc['books']}

    canonical_books = []
    total_en_verses = 0
    total_la_verses = 0
    total_gr_verses = 0
    total_he_verses = 0

    for div in CANON_SCHEMA:
        for b_info in div['books']:
            src = b_info['source_name']
            bid = b_info['id']
            is_nt = (div['testament'] == 'NT')
            dra_chaps = dra.get(bid)
            vulg_book = vulg_map.get(src)
            gnt_book = gnt_map.get(src) if is_nt else None
            wlc_book = wlc_map.get(src) if not is_nt else None
            lxx_num = b_info.get('lxx_num')

            assert dra_chaps, f"Missing book {bid} in DRA!"

            chapters_en = []
            chapters_la = []
            chapters_gr = []
            chapters_he = []
            chap_notes = {}

            for c_idx, v_en in enumerate(dra_chaps):
                chap_num = c_idx + 1
                chapters_en.append(v_en)
                total_en_verses += len(v_en)

                # Latin Clementine Vulgate
                if vulg_book and c_idx < len(vulg_book['chapters']):
                    v_la = [v['text'] for v in vulg_book['chapters'][c_idx]['verses']]
                else:
                    v_la = []
                chapters_la.append(v_la)
                total_la_verses += len(v_la)

                # Greek (Critical NT for NT books, Rahlfs LXX for OT + Deuterocanon books)
                if is_nt:
                    if gnt_book and c_idx < len(gnt_book['chapters']):
                        raw_vs = gnt_book['chapters'][c_idx]['verses']
                        v_byz_ch = (extra_corpora.get('byz', {}).get(bid) or [])
                        v_byz_vs = v_byz_ch[c_idx] if c_idx < len(v_byz_ch) else []
                        v_tr_ch = (extra_corpora.get('tr', {}).get(bid) or [])
                        v_tr_vs = v_tr_ch[c_idx] if c_idx < len(v_tr_ch) else []
                        max_real_len = max(len(v_en), len(v_la), len(v_byz_vs), len(v_tr_vs))
                        while raw_vs and not raw_vs[-1]['text'].strip() and int(raw_vs[-1]['verse']) > max_real_len:
                            raw_vs = raw_vs[:-1]
                        versif_note = None
                        if (
                            raw_vs and not raw_vs[-1]['text'].strip()
                            and len(v_en) < len(raw_vs) and len(v_la) < len(raw_vs)
                            and (
                                (bid == 'acts' and chap_num == 19 and int(raw_vs[-1]['verse']) == 41)
                                or (bid == '2cor' and chap_num == 13 and int(raw_vs[-1]['verse']) == 14)
                            )
                        ):
                            split_v = raw_vs[-1]['verse']
                            raw_vs = raw_vs[:-1]
                            if bid == 'acts' and chap_num == 19:
                                versif_note = f"Versification split: GNT, Vulgate & DRA include 'he dismissed the assembly' inside v.40 (40 verses); Byz RP & TR number it as v.{split_v}."
                            else:
                                versif_note = f"Versification split: GNT, Vulgate & DRA combine v.12–13 so the Trinitarian benediction sits at v.13 (13 verses); Byz RP & TR number it as v.{split_v}."

                        v_gr = []
                        omitted_gnt_only = []
                        omitted_gnt_byz = []
                        for v_obj in raw_vs:
                            txt = v_obj['text'].strip()
                            if txt:
                                v_gr.append(txt)
                            else:
                                vnum = int(v_obj['verse'])
                                byz_txt = v_byz_vs[vnum - 1].strip() if 1 <= vnum <= len(v_byz_vs) else ""
                                byz_has = bool(byz_txt and not byz_txt.startswith("[— Omitted"))
                                if byz_has:
                                    v_gr.append("[— Omitted in Critical GNT MSS (ℵ/B); preserved in Clementine Vulgate / Byzantine / TR / DRA]")
                                    omitted_gnt_only.append(str(vnum))
                                else:
                                    v_gr.append("[— Omitted in Critical GNT & Byzantine RP; preserved in Clementine Vulgate / TR / DRA]")
                                    omitted_gnt_byz.append(str(vnum))
                        notes_parts = []
                        if omitted_gnt_only:
                            notes_parts.append(f"Critical GNT omits verse(s) {', '.join(omitted_gnt_only)} preserved in Clementine Vulgate, Byzantine RP, TR & DRA.")
                        if omitted_gnt_byz:
                            notes_parts.append(f"Critical GNT & Byzantine RP omit verse(s) {', '.join(omitted_gnt_byz)} (Western/Latin stream preserved in Clementine Vulgate, TR & DRA).")
                        if versif_note:
                            notes_parts.append(versif_note)
                        if notes_parts:
                            chap_notes[str(chap_num)] = " ".join(notes_parts)
                    else:
                        v_gr = []
                else:
                    target_lxx_num = lxx_num
                    target_chap_key = str(chap_num)

                    if bid == 'bar' and chap_num == 6:
                        target_lxx_num = 315
                        target_chap_key = '1'
                        chap_notes[str(chap_num)] = "Baruch Ch. 6 is preserved separately in Rahlfs LXX as Epistula Jeremiae (EpJer 1)."
                    elif bid == 'dan':
                        if chap_num == 3:
                            chap_notes[str(chap_num)] = "Includes Deuterocanonical Prayer of Azariah & Song of the Three Youths (Dan 3:24–90) absent in MT."
                        elif chap_num == 13:
                            target_lxx_num = 325
                            target_chap_key = '1'
                            chap_notes[str(chap_num)] = "Deuterocanonical Susanna (Daniel Ch. 13 in Catholic Vulgate from Theodotion; Rahlfs SusOG extract here preserves the shorter 36-verse Old Greek form)."
                        elif chap_num == 14:
                            target_lxx_num = 345
                            target_chap_key = '1'
                            chap_notes[str(chap_num)] = "Deuterocanonical Bel and the Dragon (Daniel Ch. 14 in Catholic Vulgate; BelOG in Rahlfs LXX)."
                    elif bid == 'prov' and 25 <= chap_num <= 29:
                        lxx_prov_map = {25: '32', 26: '33', 27: '34', 28: '35', 29: '36'}
                        target_chap_key = lxx_prov_map[chap_num]
                        chap_notes[str(chap_num)] = f"Rahlfs LXX places Hezekiah's collection at Proverbs ch. {target_chap_key} (aligned to MT/Catholic Ch. {chap_num})."
                    elif bid == '1kgs' and chap_num in (20, 21):
                        target_chap_key = '21' if chap_num == 20 else '20'
                        chap_notes[str(chap_num)] = f"LXX 3 Kingdoms transposes Ch. 20 & 21 relative to MT/Vulgate (showing LXX Ch. {target_chap_key} for parallel match)."
                    elif bid == 'mal' and chap_num in (3, 4):
                        chap_notes[str(chap_num)] = "MT & LXX combine Catholic Malachi Ch. 3–4 into Ch. 3:1–24 (v.19–24 = Ch. 4:1–6); aligned here."
                    elif bid == 'joel' and chap_num in (2, 3):
                        chap_notes[str(chap_num)] = "MT & LXX divide Joel Ch. 2–3 into 4 chapters (MT 3:1–5 = Catholic Joel 2:28–32; MT 4 = Catholic 3); aligned here."
                    elif bid == 'jer' and 25 <= chap_num <= 51:
                        chap_notes[str(chap_num)] = "Authentic LXX Jeremiah preserves a ~1/8 shorter Vorlage (corroborated by 4QJer^b) with Oracles Against the Nations placed in LXX Ch. 25:14–32:24 (e.g., MT Jer 31 = LXX Jer 38)."
                    elif bid == 'exod' and 35 <= chap_num <= 40:
                        chap_notes[str(chap_num)] = "LXX Tabernacle fulfillment account (Exod 35–40) differs markedly in order and length from the Proto-Masoretic Text."
                    elif bid == 'sir' and chap_num == 3:
                        chap_notes[str(chap_num)] = "Vulgate/DRA includes liturgical expansions across Ch. 3; Rahlfs LXX v.30 ('almsgiving atones for sins') appears at Greek slot v.28 and corresponds to Vulgate/DRA v.33."
                    elif bid == '2macc' and chap_num == 12:
                        chap_notes[str(chap_num)] = "Clementine Vulgate & DRA split LXX 2 Macc 12:45 across v.45–46 ('holy and wholesome thought to pray for the dead')."

                    lxx_book_data = lxx.get(str(target_lxx_num), {})
                    if bid == 'mal' and chap_num in (3, 4):
                        ch3_data = lxx_book_data.get('3', {})
                        sorted_vs = sorted(ch3_data.keys(), key=lambda x: int(x))
                        all_v = [ch3_data[vs] for vs in sorted_vs]
                        v_gr = all_v[:18] if chap_num == 3 else all_v[18:]
                    elif bid == 'joel' and chap_num == 2:
                        c2 = lxx_book_data.get('2', {})
                        c3 = lxx_book_data.get('3', {})
                        v_gr = [c2[k] for k in sorted(c2.keys(), key=int)] + [c3[k] for k in sorted(c3.keys(), key=int)]
                    elif bid == 'joel' and chap_num == 3:
                        c4 = lxx_book_data.get('4', {})
                        v_gr = [c4[k] for k in sorted(c4.keys(), key=int)]
                    elif bid == 'esth' and chap_num >= 10 and esth_adds:
                        if chap_num == 10:
                            c10 = lxx_book_data.get('10', {})
                            s10_3 = esth_adds.get(('10', '3'), {})
                            v_gr = [c10.get('1', ''), c10.get('2', ''), s10_3.get('main', '')] + [
                                f"[LXX Add. F 10:3{t}] {s10_3[t]}" for t in ['a','b','c','d','e','f','g','h','i','k'] if t in s10_3
                            ]
                            chap_notes['10'] = "Esther 10:4–13 preserves Rahlfs LXX Addition F (10:3a–k, Mordecai's interpretation of his dream). Nova Vulgata embeds Additions A–F inline inside Ch. 1–10 as [1a]–[10a]."
                        elif chap_num == 11:
                            s10_3 = esth_adds.get(('10', '3'), {})
                            s1_1 = esth_adds.get(('1', '1'), {})
                            v_gr = ([f"[LXX Add. F 10:3l] {s10_3['l']}"] if 'l' in s10_3 else []) + [
                                f"[LXX Add. A 1:1{t}] {s1_1[t]}" for t in ['a','b','c','d','e','f','g','h','i','k','l'] if t in s1_1
                            ]
                            chap_notes['11'] = "Deuterocanonical Addition F colophon (11:1 = LXX 10:3l) + Addition A Dream of Mordecai (11:2–12 = LXX 1:1a–l), placed here by St. Jerome in Clementine Vulgate/DRA (Nova Vulgata prints [10a]/[1a] inline in Ch.1–10)."
                        elif chap_num == 12:
                            s1_1 = esth_adds.get(('1', '1'), {})
                            v_gr = [f"[LXX Add. A 1:1{t}] {s1_1[t]}" for t in ['m','n','o','p','q','r'] if t in s1_1]
                            chap_notes['12'] = "Deuterocanonical Addition A Conspiracy of the Eunuchs (12:1–6 = Rahlfs LXX 1:1m–r)."
                        elif chap_num == 13:
                            s3_13 = esth_adds.get(('3', '13'), {})
                            s4_17 = esth_adds.get(('4', '17'), {})
                            v_gr = [f"[LXX Add. B 3:13{t}] {s3_13[t]}" for t in ['a','b','c','d','e','f','g'] if t in s3_13] + [
                                f"[LXX Add. C 4:17{t}] {s4_17[t]}" for t in ['a','b','c','d','e','f','g','h','i'] if t in s4_17
                            ]
                            chap_notes['13'] = "Deuterocanonical Addition B Haman's Edict (13:1–7 = LXX 3:13a–g) + Addition C Prayer of Mordecai (13:8–18 = LXX 4:17a–i)."
                        elif chap_num == 14:
                            s4_17 = esth_adds.get(('4', '17'), {})
                            v_gr = [f"[LXX Add. C 4:17{t}] {s4_17[t]}" for t in ['k','l','m','n','o','p','q','r','s','t','u','w','x','y','z'] if t in s4_17]
                            chap_notes['14'] = "Deuterocanonical Addition C Prayer of Queen Esther (Esth 14:1–19 = Rahlfs LXX 4:17k–z)."
                        elif chap_num == 15:
                            s5_1 = esth_adds.get(('5', '1'), {})
                            s5_2 = esth_adds.get(('5', '2'), {})
                            v_gr = [f"[LXX Add. D 5:1{'' if t == 'main' else t}] {s5_1[t]}" for t in ['main','a','b','c','d','e','f'] if t in s5_1] + [
                                f"[LXX Add. D 5:2{'' if t == 'main' else t}] {s5_2[t]}" for t in ['main','a','b'] if t in s5_2
                            ]
                            chap_notes['15'] = "Deuterocanonical Addition D Esther Before the King (Esth 15 = Rahlfs LXX 5:1–2 Greek expansion)."
                        elif chap_num == 16:
                            s8_12 = esth_adds.get(('8', '12'), {})
                            v_gr = [f"[LXX Add. E 8:12{t}] {s8_12[t]}" for t in ['a','b','c','d','e','f','g','h','i','k','l','m','n','o','p','q','r','s','t','u','x'] if t in s8_12]
                            chap_notes['16'] = "Deuterocanonical Addition E Counter-Edict of Artaxerxes (Esth 16:1–24 = Rahlfs LXX 8:12a–x)."
                    elif bid == 'esth' and chap_num in (1, 3, 4, 8) and esth_adds:
                        lxx_chap_data = lxx_book_data.get(target_chap_key, {})
                        sorted_vs = sorted(lxx_chap_data.keys(), key=lambda x: int(x))
                        v_gr = []
                        for vs in sorted_vs:
                            if chap_num == 1 and vs == '1' and 's' in esth_adds.get(('1', '1'), {}):
                                v_gr.append(esth_adds[('1', '1')]['s'])
                            elif chap_num == 3 and vs == '13' and 'main' in esth_adds.get(('3', '13'), {}):
                                v_gr.append(esth_adds[('3', '13')]['main'])
                            elif chap_num == 4 and vs == '17' and 'main' in esth_adds.get(('4', '17'), {}):
                                v_gr.append(esth_adds[('4', '17')]['main'])
                            elif chap_num == 8 and vs == '12' and 'main' in esth_adds.get(('8', '12'), {}):
                                v_gr.append(esth_adds[('8', '12')]['main'])
                            else:
                                v_gr.append(lxx_chap_data[vs])
                    else:
                        lxx_chap_data = lxx_book_data.get(target_chap_key, {})
                        if lxx_chap_data:
                            sorted_vs = sorted(lxx_chap_data.keys(), key=lambda x: int(x))
                            first_num = int(sorted_vs[0])
                            if first_num > 1:
                                v_gr = [f"[LXX v.{vs}] {lxx_chap_data[vs]}" for vs in sorted_vs]
                            else:
                                v_gr = [lxx_chap_data[vs] for vs in sorted_vs]
                        else:
                            v_gr = []

                chapters_gr.append(v_gr)
                total_gr_verses += len(v_gr)

                # Hebrew MT (WLC for shared OT books, with full Psalm / Joel / Malachi alignment)
                if not is_nt and wlc_book:
                    if bid == 'ps':
                        v_he, ps_note = map_wlc_psalm(wlc_book, chap_num)
                        if ps_note:
                            if str(chap_num) in chap_notes:
                                chap_notes[str(chap_num)] = f"{chap_notes[str(chap_num)]} | {ps_note}"
                            else:
                                chap_notes[str(chap_num)] = ps_note
                        if chap_num == 39:
                            chap_notes[str(chap_num)] = "Codices Vaticanus (B), Sinaiticus (א) & Alexandrinus (A) read σῶμα ('body', quoted at Heb 10:5); Rahlfs main text adopts Hexaplaric ὠτία ('ears') matching MT Ps 40:6. | " + (ps_note or "")
                    elif bid == 'mal' and chap_num in (3, 4):
                        all_he = [v['text'] for v in wlc_book['chapters'][2]['verses']]
                        v_he = all_he[:18] if chap_num == 3 else all_he[18:]
                    elif bid == 'joel' and chap_num == 2:
                        v_he = [v['text'] for v in wlc_book['chapters'][1]['verses']] + [v['text'] for v in wlc_book['chapters'][2]['verses']]
                    elif bid == 'joel' and chap_num == 3:
                        v_he = [v['text'] for v in wlc_book['chapters'][3]['verses']]
                    elif c_idx < len(wlc_book['chapters']):
                        v_he = [v['text'] for v in wlc_book['chapters'][c_idx]['verses']]
                    else:
                        v_he = []
                else:
                    v_he = []
                chapters_he.append(v_he)
                total_he_verses += len(v_he)

            tr_streams = {}
            for key, _, _ in extra_paths:
                ds_chaps = extra_corpora[key].get(bid)
                if ds_chaps:
                    tr_streams[key] = ds_chaps

            canonical_books.append({
                "id": bid,
                "name": b_info['name'],
                "abbr": b_info['abbr'],
                "division": div['division'],
                "testament": div['testament'],
                "lang": b_info['lang'],
                "deuterocanon": b_info['deuterocanon'],
                "chapter_count": len(chapters_en),
                "chap_notes": chap_notes,
                "verses_en": chapters_en,
                "verses_la": chapters_la,
                "verses_gr": chapters_gr,
                "verses_he": chapters_he,
                "tr": tr_streams
            })

    print(f"Loaded {len(canonical_books)} canonical books!")
    print(f"Verse totals -> DRA EN: {total_en_verses} | Clem LA: {total_la_verses} | GR (LXX+NA28): {total_gr_verses} | HE (WLC): {total_he_verses}")
    return canonical_books

def verify_cross_refs(books):
    bmap = {b['id']: b for b in books}
    for xr in CROSS_REFS:
        for side in ('a', 'b'):
            bid, ch, v = xr[side]
            assert bid in bmap, f"Cross-ref {xr['id']} unknown book {bid}"
            b = bmap[bid]
            assert 1 <= ch <= b['chapter_count'], f"Cross-ref {xr['id']} invalid ch {bid} {ch}"
            assert 1 <= v <= len(b['verses_en'][ch - 1]), f"Cross-ref {xr['id']} invalid verse {bid} {ch}:{v}"
    print(f"Verified {len(CROSS_REFS)} bidirectional canonical cross-references against 73-book dataset.")

def build_suite():
    books = load_bible_datasets()
    verify_cross_refs(books)
    strongs_gloss, greek_morph, hebrew_morph, dra_links = load_lexicon_and_links()

    payload = {
        "canon_schema": CANON_SCHEMA,
        "translation_registry": TRANSLATION_REGISTRY,
        "books": books,
        "preloaded_cruxes": PRELOADED_CRUXES,
        "greek_morph": greek_morph,
        "hebrew_morph": hebrew_morph,
        "strongs_gloss": strongs_gloss,
        "latin_lex": LATIN_LEX,
        "dra_links": dra_links,
        "cross_refs": CROSS_REFS,
    }

    print(f"Writing compact database to {JSON_OUT}...")
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, separators=(',', ':'))
    print(f"Written {JSON_OUT} ({os.path.getsize(JSON_OUT):,} bytes)")

    json_blob = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).replace('</script>', '<\\/script>')

    three_js_inline = ""
    if os.path.exists(THREE_JS_PATH):
        with open(THREE_JS_PATH, 'r', encoding='utf-8') as f:
            three_js_inline = f.read().replace('</script>', '<\\/script>')
        print(f"Embedding local Three.js ({len(three_js_inline)} chars) for 100% offline 3D operation...")

    lucide_js_inline = ""
    if os.path.exists(LUCIDE_JS_PATH):
        with open(LUCIDE_JS_PATH, 'r', encoding='utf-8') as f:
            lucide_js_inline = f.read().replace('//# sourceMappingURL=lucide.min.js.map', '').replace('</script>', '<\\/script>')
        print(f"Embedding local Lucide icons ({len(lucide_js_inline)} chars) for 100% offline UI rendering...")

    tailwind_css_inline = ""
    if os.path.exists(TAILWIND_CSS_PATH):
        with open(TAILWIND_CSS_PATH, 'r', encoding='utf-8') as f:
            tailwind_css_inline = f.read().replace('</style>', '')
        print(f"Embedding offline compiled Tailwind stylesheet ({len(tailwind_css_inline)} chars)...")

    print("Generating comprehensive standalone HTML workstation...")
    with open(os.path.join(SCRIPT_DIR, 'logos_suite_template.html'), 'r', encoding='utf-8') as f:
        html_content = f.read()

    final_html = html_content.replace('__PLENARY_PAYLOAD__', json_blob)
    if three_js_inline:
        final_html = final_html.replace('<!-- __THREE_JS_TAG__ -->', f'<script>\n{three_js_inline}\n</script>')
    else:
        final_html = final_html.replace('<!-- __THREE_JS_TAG__ -->', '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>')

    if lucide_js_inline:
        final_html = final_html.replace('<!-- __LUCIDE_JS_TAG__ -->', f'<script>\n{lucide_js_inline}\n</script>')
    else:
        final_html = final_html.replace('<!-- __LUCIDE_JS_TAG__ -->', '<script src="https://unpkg.com/lucide@latest"></script>')

    if tailwind_css_inline:
        final_html = final_html.replace('<!-- __OFFLINE_CSS_TAG__ -->', f'<style id="offline-tailwind">\n{tailwind_css_inline}\n</style>')
    else:
        final_html = final_html.replace('<!-- __OFFLINE_CSS_TAG__ -->', '')

    with open(HTML_OUT, 'w', encoding='utf-8') as f:
        f.write(final_html)

    print(f"Successfully generated standalone suite: {HTML_OUT} ({os.path.getsize(HTML_OUT)} bytes)")

if __name__ == '__main__':
    build_suite()
