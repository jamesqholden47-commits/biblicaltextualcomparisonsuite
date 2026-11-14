#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
critical_editions_registry.py — Architectural Schema & Import Pipeline
for the Top-Ranked Scholarly Critical Editions in Biblical Textual Criticism.

Covers the supreme international standards recommended for comprehensive
text-critical and exegesis research (competing with Logos Bible Software Diamond/Platinum):

HEBREW BIBLE / QUMRAN:
  1. Emanuel Tov, Textual Criticism of the Hebrew Bible (4th ed., Fortress 2022) [Rank 2]
  2. Eugene Ulrich (ed.), The Biblical Qumran Scrolls: Transcriptions and Textual Variants (3 vols., Brill 2010) [Rank 12]
  3. García Martínez & Tigchelaar (eds.), The Dead Sea Scrolls Study Edition (2 vols., Brill/Eerdmans) [Rank 18]
  4. Biblia Hebraica Quinta (BHQ): Megilloth & Twelve Prophets (DBG 2010) [Rank 57]
  5. Hendel & Joosten, How Old Is the Hebrew Bible? (Yale 2018) [Rank 56]
  6. Cross & Talmon (eds.), Qumran and the History of the Biblical Text (Harvard 1975) [Rank 100]

SEPTUAGINT (LXX):
  7. Rahlfs & Hanhart (eds.), Septuaginta: Editio altera (DBG 2006) [Rank 52]
  8. Göttingen Septuaginta Major Critical Edition (Ziegler Sirach XII,2; Ziegler Wisdom XII,1; Wevers Deut III,2) [Ranks 21, 53, 54]
  9. Takamitsu Muraoka, A Greek-English Lexicon of the Septuagint (Peeters 2009) [Rank 55]
  10. Karen Jobes & Moisés Silva, Invitation to the Septuagint (2nd ed., Baker 2015) [Rank 29]
  11. Timothy Michael Law, When God Spoke Greek (Oxford 2013) [Rank 30]

NEW TESTAMENT (GNT):
  12. NA28 — Novum Testamentum Graece (Nestle-Aland, Deutsche Bibelgesellschaft 2012) [Rank 6]
  13. Bruce M. Metzger & Bart D. Ehrman, The Text of the New Testament (4th ed., Oxford 2005) [Rank 5]
  14. Bruce M. Metzger, A Textual Commentary on the Greek New Testament (2nd ed., UBS 1994) [Rank 46]
  15. Tommy Wasserman & Peter J. Gurry, A New Approach to Textual Criticism: CBGM Intro (SBL 2017) [Rank 11]
  16. David C. Parker, An Introduction to the New Testament Manuscripts and Their Texts (Cambridge 2008) [Rank 45]
  17. Philip W. Comfort, The Text of the Earliest New Testament Greek Manuscripts (2 vols., Kregel 2019) [Rank 47]
  18. ECM — Editio Critica Maior (Vol. IV Catholic Letters; Vol. III Acts; DBG) [Ranks 48, 51]
  19. Bruce M. Metzger, The Early Versions of the New Testament (Oxford 1977) [Rank 58]
  20. George A. Kiraz, Comparative Edition of the Syriac Gospels (4 vols., Brill 1996) [Rank 59]
  21. Reuben J. Swanson, New Testament Greek Manuscripts: Variant Readings (Romans etc.) [Rank 60]

VULGATE & LATIN:
  22. Robert Weber & Roger Gryson (eds.), Biblia Sacra Vulgata (Stuttgart Vulgate, 5th ed., DBG 2007) [Rank 19]
  23. H.A.G. Houghton, The Latin New Testament: A Guide to its History, Texts, and Manuscripts (Oxford 2016) [Rank 23]
  24. Vetus Latina Database (Vetus Latina Institut Beuron / Brepols)
  25. Bonifatius Fischer, Novae Concordantiae Bibliorum Sacrorum Iuxta Vulgatam Versionem (Frommann-Holzboog 1977)
"""

import json
import os
from typing import Dict, List, Any, Optional

CRITICAL_EDITIONS_CATALOG = [
    # --- HEBREW BIBLE / QUMRAN ---
    {
        "id": "tov_tchb",
        "rank": 2,
        "category": "Hebrew Bible / Qumran",
        "title": "Textual Criticism of the Hebrew Bible",
        "author_editor": "Emanuel Tov",
        "edition": "4th Revised & Expanded Edition",
        "publisher": "Fortress Press",
        "year": 2022,
        "standard_status": "The supreme international standard for Hebrew Bible textual criticism",
        "format_type": "Monograph / Handbook / Variant Typology",
        "import_status": "Curated Schema + Excerpted Variant Matrix",
        "license_note": "Commercial Academic Copyright (Fortress Press); apparatus excerpts digitized under fair use",
        "key_features": [
            "Classification of Qumran biblical scrolls into 5 groups (Proto-Masoretic, Pre-Samaritan, Septuagintal Vorlage, Non-Aligned, Morphologically unique)",
            "Systematic typology of scribal errors, orthographic shifts, and editorial reworkings",
            "Detailed collation tables for Samaritan Pentateuch vs MT vs LXX"
        ]
    },
    {
        "id": "ulrich_qumran",
        "rank": 12,
        "category": "Hebrew Bible / Qumran",
        "title": "The Biblical Qumran Scrolls: Transcriptions and Textual Variants",
        "author_editor": "Eugene Ulrich (ed.)",
        "edition": "3 Volumes",
        "publisher": "Brill",
        "year": 2010,
        "standard_status": "Complete diplomatic transcriptions of every biblical Dead Sea Scroll fragment",
        "format_type": "Diplomatic Editions & Variant Apparatus",
        "import_status": "Curated Schema + Crux DSS Transcriptions",
        "license_note": "Commercial Academic Copyright (Brill); canonical cruxes pre-loaded into suite",
        "key_features": [
            "Diplomatic Hebrew transcriptions of Caves 1-11 biblical scrolls",
            "Variant apparatus against MT (Codex Leningradensis B19A) and Samaritan Pentateuch",
            "4QpaleoExodᵐ, 4QSamᵃ (with 1 Sam 10/11 Nahash paragraph), 4QDeutʲ (Deut 32:8 'sons of God')",
            "1QIsaᵃ Great Isaiah Scroll complete transcription"
        ]
    },
    {
        "id": "garcia_martinez_dss",
        "rank": 18,
        "category": "Hebrew Bible / Qumran",
        "title": "The Dead Sea Scrolls Study Edition",
        "author_editor": "Florentino García Martínez & Eibert J.C. Tigchelaar (eds.)",
        "edition": "2 Volumes",
        "publisher": "Brill / Eerdmans",
        "year": 1998,
        "standard_status": "Top-5 essential corpus for non-biblical sectarian Qumran texts",
        "format_type": "Bilingual Facing Hebrew/Aramaic and English Text",
        "import_status": "Curated Schema + Major Sectarian Texts",
        "license_note": "Commercial Academic Copyright (Brill / Eerdmans)",
        "key_features": [
            "1QS (Rule of the Community / Serek ha-Yahad)",
            "1QM (War Scroll)",
            "1QHᵃ (Hodayot / Thanksgiving Hymns)",
            "CD (Damascus Document)",
            "4QMMT (Miqsat Ma'ase ha-Torah / Some Works of the Law — vital Pauline forensic background)"
        ]
    },
    {
        "id": "bhq",
        "rank": 57,
        "category": "Hebrew Bible / Qumran",
        "title": "Biblia Hebraica Quinta (BHQ)",
        "author_editor": "International Committee (A. Schenker et al., eds.)",
        "edition": "Fascicles 1-20 (Megilloth, Twelve Prophets, etc.)",
        "publisher": "Deutsche Bibelgesellschaft (DBG)",
        "year": 2010,
        "standard_status": "Newest diplomatic critical edition succeeding BHS (Biblia Hebraica Stuttgartensia)",
        "format_type": "Diplomatic Hebrew Text + Full Text-Critical & Masoretic Apparatus",
        "import_status": "Curated Schema + Masorah Magna/Parva Module",
        "license_note": "Copyright Deutsche Bibelgesellschaft (DBG); requires proprietary digital license for verbatim text",
        "key_features": [
            "Color diplomatic representation of Codex Leningradensis B19A",
            "Complete critical apparatus with explicit retroversion justifications",
            "Detailed commentary volume accompanying each biblical book"
        ]
    },
    {
        "id": "hendel_joosten_age",
        "rank": 56,
        "category": "Hebrew Bible / Qumran",
        "title": "How Old Is the Hebrew Bible? A Linguistic, Textual, and Historical Study",
        "author_editor": "Ronald Hendel & Jan Joosten",
        "edition": "1st Edition",
        "publisher": "Yale University Press",
        "year": 2018,
        "standard_status": "Standard linguistic and diachronic profile of Biblical Hebrew strata",
        "format_type": "Monograph / Diachronic Linguistic Analysis",
        "import_status": "Linguistic Strata Metadata Indexed to WLC Lexicon",
        "license_note": "Yale University Press copyright",
        "key_features": [
            "Archaic Biblical Hebrew (ABH: Exod 15, Judg 5, Deut 32)",
            "Classical Biblical Hebrew (CBH: Pre-exilic prose)",
            "Late Biblical Hebrew (LBH: Chronicles, Ezra, Nehemiah, Daniel, Esther)",
            "Qumran & Rabbinic Hebrew transitions"
        ]
    },
    {
        "id": "cross_talmon_qumran",
        "rank": 100,
        "category": "Hebrew Bible / Qumran",
        "title": "Qumran and the History of the Biblical Text",
        "author_editor": "Frank Moore Cross & Shemaryahu Talmon (eds.)",
        "edition": "Harvard Seminar Volume",
        "publisher": "Harvard University Press",
        "year": 1975,
        "standard_status": "Foundational symposium defining Local Text Theory and Multiple Text Types",
        "format_type": "Historical Critical Essays",
        "import_status": "Local Text Matrix (Egyptian, Palestinian, Babylonian)",
        "license_note": "Harvard University Press copyright",
        "key_features": [
            "Frank Moore Cross: Local Text Theory (Egyptian/LXX, Palestinian/DSS/Samaritan, Babylonian/MT)",
            "Shemaryahu Talmon: Synonymous readings and stylistic variation in textual transmission"
        ]
    },

    # --- SEPTUAGINT (LXX) ---
    {
        "id": "rahlfs_hanhart_lxx",
        "rank": 52,
        "category": "Septuagint",
        "title": "Septuaginta: Editio altera",
        "author_editor": "Alfred Rahlfs & Robert Hanhart (eds.)",
        "edition": "Revised Edition",
        "publisher": "Deutsche Bibelgesellschaft (DBG)",
        "year": 2006,
        "standard_status": "The universal standard manual edition of the complete Greek Septuagint",
        "format_type": "Full Critical Eclectic Greek OT + Deuterocanon",
        "import_status": "ACTIVE IN SUITE (`LXX_clean.json`, 7,179,330 B, 35,161 verses)",
        "license_note": "Rahlfs 1935 base text public domain; Hanhart 2006 apparatus copyrighted DBG",
        "key_features": [
            "Complete 73-book Catholic canon OT plus 1-2 Esdras, 3-4 Maccabees, Prayer of Manasseh, Psalm 151",
            "Alternative parallel versions for Judges (A vs B), Tobit (Sinaiticus long vs Vaticanus short), Daniel (Theodotion vs Old Greek), Susanna, Bel and the Dragon",
            "Esther Additions A, B, C, D, E, F integrated"
        ]
    },
    {
        "id": "goettingen_septuaginta",
        "rank": 21,
        "category": "Septuagint",
        "title": "Vetus Testamentum Graecum: Göttingen Septuaginta Major Critical Edition",
        "author_editor": "Joseph Ziegler (Sirach XII,2; Wisdom XII,1), John William Wevers (Deut III,2), et al.",
        "edition": "Definitive Multi-Volume Editio Maior",
        "publisher": "Vandenhoeck & Ruprecht",
        "year": 1962,
        "standard_status": "The definitive major critical edition of the Septuagint worldwide",
        "format_type": "Editio Maior with Two Extensive Negative Apparatuses",
        "import_status": "Curated Schema + Major Crux Apparatus (Sirach, Wisdom, Deut 32)",
        "license_note": "Vandenhoeck & Ruprecht copyright; major variants excerpted",
        "key_features": [
            "Apparatus I: Manuscript witnesses, papyri, daughter versions, hexaplaric signs",
            "Apparatus II: Patristic citations, secondary revisions (Aquila, Symmachus, Theodotion)",
            "Ziegler's reconstruction of the two Greek recensions of Sirach (Greek I vs Greek II expansion)",
            "Wevers' exhaustively documented Vorlage analysis for the Pentateuch"
        ]
    },
    {
        "id": "muraoka_lxx_lexicon",
        "rank": 55,
        "category": "Septuagint",
        "title": "A Greek-English Lexicon of the Septuagint",
        "author_editor": "Takamitsu Muraoka",
        "edition": "Revised Edition",
        "publisher": "Peeters Publishers",
        "year": 2009,
        "standard_status": "The gold standard lexicon dedicated exclusively to Septuagint Greek semantics",
        "format_type": "Specialized Academic Lexicon",
        "import_status": "Curated Morphological Gloss Matrix (Mapped to Strong's Greek)",
        "license_note": "Peeters Publishers copyright",
        "key_features": [
            "Distinguishes translation Greek (calques on Hebrew idioms) from original Greek compositions (Wisdom, 2 Maccabees)",
            "Full semantic analysis of sacrificial, legal, and theological vocabulary (hilasterion, diatheke, dikaiosyne)",
            "Syntactic valency patterns for prepositions and verbs"
        ]
    },
    {
        "id": "jobes_silva_lxx",
        "rank": 29,
        "category": "Septuagint",
        "title": "Invitation to the Septuagint",
        "author_editor": "Karen H. Jobes & Moisés Silva",
        "edition": "2nd Edition",
        "publisher": "Baker Academic",
        "year": 2015,
        "standard_status": "Standard academic university handbook on Septuagint studies",
        "format_type": "Handbook & Methodological Guide",
        "import_status": "Integrated Exegetical Guidelines & Transmission Timelines",
        "license_note": "Baker Academic copyright",
        "key_features": [
            "Methodology for distinguishing translator technique from a deviant Hebrew Vorlage",
            "Transmission history from the Letter of Aristeas through Origen's Hexapla to Christian codices",
            "Analysis of New Testament quotations of the Old Testament (LXX vs MT agreements)"
        ]
    },
    {
        "id": "law_god_spoke_greek",
        "rank": 30,
        "category": "Septuagint",
        "title": "When God Spoke Greek: The Septuagint and the Formation of the Christian Bible",
        "author_editor": "Timothy Michael Law",
        "edition": "1st Edition",
        "publisher": "Oxford University Press",
        "year": 2013,
        "standard_status": "Premier historical monograph on the Septuagint as the early Church's primary Bible",
        "format_type": "Historical Monograph",
        "import_status": "Patristic Canon & Apostles' Bible Theological Syntheses",
        "license_note": "Oxford University Press copyright",
        "key_features": [
            "Demonstrates that the Apostles and Apostolic Fathers treated the Greek LXX as inspired Scripture",
            "Traces the shift in Western Christendom with Jerome's Hebraica Veritas and Augustine's defense of the LXX",
            "Theological impact on virgin birth (Isa 7:14 parthenos) and Son of God christology"
        ]
    },

    # --- NEW TESTAMENT ---
    {
        "id": "na28_gnt",
        "rank": 6,
        "category": "New Testament",
        "title": "Novum Testamentum Graece (NA28)",
        "author_editor": "E. & E. Nestle, B. & K. Aland, J. Karavidopoulos, C.M. Martini, B.M. Metzger (eds.)",
        "edition": "28th Revised Edition (incorporating ECM Catholic Letters)",
        "publisher": "Deutsche Bibelgesellschaft (DBG)",
        "year": 2012,
        "standard_status": "The universal standard critical text of the Greek New Testament worldwide",
        "format_type": "Critical Greek Text + Comprehensive Negative Apparatus",
        "import_status": "Statistical Restoration GNT (`StatResGNT.json`) + NA28 Crux Matrix pre-loaded",
        "license_note": "Critical apparatus and text copyrighted Deutsche Bibelgesellschaft (DBG)",
        "key_features": [
            "Papyri witnesses (P45, P46, P66, P72, P75) and Great Uncials (01 Sinaiticus, 02 Alexandrinus, 03 Vaticanus, 04 Ephraemi, 05 Bezae)",
            "Incorporation of Coherence-Based Genealogical Method (CBGM) in the Catholic Letters",
            "Marginal Eusebian canons and cross-reference system"
        ]
    },
    {
        "id": "metzger_ehrman_text",
        "rank": 5,
        "category": "New Testament",
        "title": "The Text of the New Testament: Its Transmission, Corruption, and Restoration",
        "author_editor": "Bruce M. Metzger & Bart D. Ehrman",
        "edition": "4th Edition",
        "publisher": "Oxford University Press",
        "year": 2005,
        "standard_status": "The supreme international introductory textbook for New Testament textual criticism",
        "format_type": "Monograph & Methodological Handbook",
        "import_status": "Palaeographical & Textual Families Reference Guide",
        "license_note": "Oxford University Press copyright",
        "key_features": [
            "History of printed text from Complutensian Polyglot and Erasmus to Westcott-Hort and NA28",
            "Systematic categorization of unintentional errors (dittography, haplography, homoioteleuton, itacism) and intentional modifications (doctrinal harmonizations)",
            "Descriptions of all major Greek uncials, minuscules, and lectionaries"
        ]
    },
    {
        "id": "metzger_textual_commentary",
        "rank": 46,
        "category": "New Testament",
        "title": "A Textual Commentary on the Greek New Testament",
        "author_editor": "Bruce M. Metzger (for the UBS Editorial Committee)",
        "edition": "2nd Edition",
        "publisher": "German Bible Society / United Bible Societies",
        "year": 1994,
        "standard_status": "The official companion explaining the editorial decisions behind NA28 / UBS4",
        "format_type": "Verse-by-Verse Text-Critical Commentary",
        "import_status": "COMPLETE CRUX COMMENTARY MATRIX PRE-LOADED IN SUITE",
        "license_note": "UBS copyright; major variant justifications excerpted",
        "key_features": [
            "Committee certainty ratings: {A} virtually certain, {B} some doubt, {C} considerable doubt, {D} very high doubt",
            "Detailed majority and minority dissenting opinions (Metzger, Aland, Black, Martini, Wikgren)",
            "Explicit rationale for famous variants: Mark 16:9-20, John 7:53-8:11, Luke 22:43-44, 1 John 5:7-8, John 1:18, Rom 5:1, 1 Tim 3:16"
        ]
    },
    {
        "id": "wasserman_gurry_cbgm",
        "rank": 11,
        "category": "New Testament",
        "title": "A New Approach to Textual Criticism: An Introduction to the CBGM",
        "author_editor": "Tommy Wasserman & Peter J. Gurry",
        "edition": "1st Edition",
        "publisher": "SBL Press",
        "year": 2017,
        "standard_status": "The definitive primer on the Coherence-Based Genealogical Method behind ECM & NA28",
        "format_type": "Methodological Monograph",
        "import_status": "CBGM Algorithm & Stemma Generation Module",
        "license_note": "SBL Press copyright",
        "key_features": [
            "Pre-genealogical coherence: percentage of agreement between manuscript pairs",
            "Genealogical queries: determining which reading gave rise to the other (local stemmata)",
            "Global stemmata and optimal substructure reconstruction",
            "Resolving contaminations, mixtures, and transcriptional coincidences"
        ]
    },
    {
        "id": "comfort_earliest_mss",
        "rank": 47,
        "category": "New Testament",
        "title": "The Text of the Earliest New Testament Greek Manuscripts",
        "author_editor": "Philip W. Comfort & David P. Barrett",
        "edition": "2 Volumes (Expanded)",
        "publisher": "Kregel Publications",
        "year": 2019,
        "standard_status": "Full diplomatic transcriptions and photographic analysis of all 1st–3rd century Greek NT papyri",
        "format_type": "Diplomatic Editions & Photographs",
        "import_status": "Papyri Witness Catalog (P1 through P140) with dates & provenance",
        "license_note": "Kregel Publications copyright",
        "key_features": [
            "P52 (c. AD 125 John 18)",
            "P46 (c. AD 175-225 Pauline Epistles & Hebrews)",
            "P66 & P75 (c. AD 200 John & Luke)",
            "P72 (c. 3rd-4th cent. 1-2 Peter & Jude)"
        ]
    },
    {
        "id": "ecm_gnt",
        "rank": 48,
        "category": "New Testament",
        "title": "Editio Critica Maior (ECM)",
        "author_editor": "Institut für Neutestamentliche Textforschung (INTF, Münster)",
        "edition": "Vol. III (Acts), Vol. IV (Catholic Letters), Vol. II (Gospel of Mark)",
        "publisher": "Deutsche Bibelgesellschaft (DBG)",
        "year": 2017,
        "standard_status": "The 21st-century editio maior providing the definitive documentation for all future NT texts",
        "format_type": "Comprehensive Editio Maior + Full CBGM Apparatus",
        "import_status": "INTF Open Database Connector & Transcriptions Integration",
        "license_note": "Commercial Academic Copyright (DBG); open research data accessible via Münster NTVMR",
        "key_features": [
            "Complete collation of all extant Greek manuscripts up to the 10th century and selected minuscules",
            "Direct application of the Coherence-Based Genealogical Method (CBGM)",
            "Full electronic transcription of thousands of witnesses"
        ]
    },

    {
        "id": "parker_nt_manuscripts",
        "rank": 45,
        "category": "New Testament",
        "title": "An Introduction to the New Testament Manuscripts and Their Texts",
        "author_editor": "David C. Parker",
        "edition": "1st Edition",
        "publisher": "Cambridge University Press",
        "year": 2008,
        "standard_status": "Masterwork on physical paleography, living text dynamics, and digital NT editions",
        "format_type": "Monograph & Text-Critical Method Guide",
        "import_status": "Manuscript Typology & Living Text Schema",
        "license_note": "Cambridge University Press copyright",
        "key_features": [
            "Detailed analysis of the 'living text' phenomenon and codicology across major uncials",
            "In-depth investigation of Codex Bezae Cantabrigiensis (D 05) and Western text peculiarities",
            "Foundational modern bridge between physical paleography and electronic transcription editions"
        ]
    },
    {
        "id": "metzger_early_versions",
        "rank": 58,
        "category": "New Testament",
        "title": "The Early Versions of the New Testament: Their Origin, Transmission, and Limitations",
        "author_editor": "Bruce M. Metzger",
        "edition": "1st Edition",
        "publisher": "Oxford University Press",
        "year": 1977,
        "standard_status": "The supreme international reference guide to non-Greek ancient biblical versions",
        "format_type": "Comparative Versionology Handbook",
        "import_status": "Versional Translation Limitation & Grammar Matrix",
        "license_note": "Oxford University Press copyright",
        "key_features": [
            "Comprehensive breakdown of the Syriac, Coptic, Armenian, Georgian, Ethiopic, Gothic, and Old Church Slavonic traditions",
            "Rigorous linguistic limitations of each language when retroverting into Greek (e.g., absence of definite article in Latin, tense shifts in Syriac)",
            "Essential handbook for evaluating versional citations in critical apparatuses"
        ]
    },
    {
        "id": "kiraz_syriac_gospels",
        "rank": 59,
        "category": "New Testament",
        "title": "Comparative Edition of the Syriac Gospels: Aligning the Sinaiticus, Curetonianus, Peshîṭtâ & Ḥarklean",
        "author_editor": "George A. Kiraz",
        "edition": "4 Volumes",
        "publisher": "Brill",
        "year": 1996,
        "standard_status": "Definitive 4-way synoptic collation of the entire Syriac Gospel tradition",
        "format_type": "4-Column Comparative Textual Edition",
        "import_status": "Syriac Synoptic Alignment Schema (Syr-Sin, Syr-Cur, Syr-Pesh, Syr-Hark)",
        "license_note": "Brill Academic Publishers copyright",
        "key_features": [
            "Parallel synoptic presentation of Old Syriac (Sinaiticus & Curetonianus), Peshitta, and Harklean",
            "Full grammatical vocalization and alignment to Greek NA28 Gospel text",
            "Crucial primary witness for Western and Semitic textual influences in the early Eastern Church"
        ]
    },
    {
        "id": "swanson_nt_mss",
        "rank": 60,
        "category": "New Testament",
        "title": "New Testament Greek Manuscripts: Variant Readings Arranged in Horizontal Lines against Codex Vaticanus",
        "author_editor": "Reuben J. Swanson",
        "edition": "Multi-volume Series (Matthew, Mark, Luke, John, Romans, 1-2 Corinthians, Galatians)",
        "publisher": "Sheffield Academic Press / William Carey Int.",
        "year": 2001,
        "standard_status": "Complete horizontal line-by-line collations of major Greek uncials and minuscules",
        "format_type": "Horizontal Comparative Layout",
        "import_status": "Horizontal Line Collator Engine (Vaticanus B Base)",
        "license_note": "Sheffield Academic Press / William Carey copyright",
        "key_features": [
            "Line-by-line visual alignment of P46, א, A, B, C, D, F, G, Ψ against Vaticanus",
            "Instant visual identification of singular readings, lacunae, and scribal assimilations",
            "Eliminates cryptic apparatus abbreviations by printing the full continuous Greek text of each manuscript"
        ]
    },
    {
        "id": "stuttgart_vulgate",
        "rank": 19,
        "category": "Vulgate / Latin",
        "title": "Biblia Sacra Vulgata (Stuttgart Vulgate)",
        "author_editor": "Robert Weber & Roger Gryson (eds.)",
        "edition": "5th Edition",
        "publisher": "Deutsche Bibelgesellschaft (DBG)",
        "year": 2007,
        "standard_status": "The supreme critical manual edition of St. Jerome's Latin Vulgate",
        "format_type": "Critical Latin Text + Extensive Variant Apparatus",
        "import_status": "Curated Schema + Jerome Translation Profiles (Pairing with Sixto-Clementine & Nova Vulgata)",
        "license_note": "Deutsche Bibelgesellschaft (DBG) copyright",
        "key_features": [
            "Reconstruction of St. Jerome's original 4th/5th century Latin translations directly from Codex Amiatinus, Codex Fuldensis, and Codex Cavensis",
            "Parallel Gallican and Hebraicum Psalters",
            "Full Latin text-critical apparatus documenting Old Latin (Vetus Latina) variations"
        ]
    },
    {
        "id": "houghton_latin_nt",
        "rank": 23,
        "category": "Vulgate / Latin",
        "title": "The Latin New Testament: A Guide to its History, Texts, and Manuscripts",
        "author_editor": "H.A.G. Houghton",
        "edition": "1st Edition",
        "publisher": "Oxford University Press",
        "year": 2016,
        "standard_status": "Definitive modern guide to the Vetus Latina, Jerome's revision, and the Latin manuscript tradition",
        "format_type": "Monograph & Manuscript Catalog",
        "import_status": "Vetus Latina Manuscript Sigla Catalog (VL 1 to VL 89)",
        "license_note": "Oxford University Press (Open Access under CC-BY)",
        "key_features": [
            "Catalog of all 100+ Old Latin witnesses (Codex Vercellensis, Codex Veronensis, Codex Bobbiensis, Codex Palatinus)",
            "Jerome's editorial method: Greek Vorlage identification (Western vs Alexandrian-type Greek manuscripts)",
            "History of the Vulgate in the British Isles (Amiatinus, Lindisfarne) and Carolingian revisions (Alcuin, Theodulf)"
        ]
    },
    {
        "id": "vetus_latina_beuron",
        "rank": 65,
        "category": "Vulgate / Latin",
        "title": "Vetus Latina: Die Reste der altlateinischen Bibel (Beuron Edition)",
        "author_editor": "Vetus Latina Institut (Erbach / Beuron Abbey)",
        "edition": "Comprehensive Multi-fascicle Edition",
        "publisher": "Verlag Herder (Freiburg)",
        "year": 1949,
        "standard_status": "Monumental comprehensive critical edition of all pre-Vulgate Old Latin biblical texts and patristic citations",
        "format_type": "Comprehensive Editio Maior for Old Latin",
        "import_status": "Old Latin Manuscript Typology & Patristic Lemma Mapping",
        "license_note": "Verlag Herder / Vetus Latina Institut copyright",
        "key_features": [
            "Complete collection of all Old Latin manuscript fragments (African vs European text-types: Afra vs Itala)",
            "Exhaustive collection of patristic biblical citations (Tertullian, Cyprian, Novatian, Lucifer of Cagliari, Tyconius)",
            "Indispensable for recovering the earliest 2nd/3rd century Greek NT text known in North Africa and Rome"
        ]
    },
    {
        "id": "fischer_novae_concordantiae",
        "rank": 70,
        "category": "Vulgate / Latin",
        "title": "Novae Concordantiae Bibliorum Sacrorum Iuxta Vulgatam Versionem Critice Editam",
        "author_editor": "Bonifatius Fischer",
        "edition": "5 Volumes",
        "publisher": "Frommann-Holzboog",
        "year": 1977,
        "standard_status": "The supreme critical concordance of the Latin Vulgate, keyed to the Weber-Gryson critical edition",
        "format_type": "Exhaustive Critical Latin Concordance",
        "import_status": "Latin Lemma & Morphology Parsing Engine",
        "license_note": "Frommann-Holzboog copyright",
        "key_features": [
            "Exhaustive lemmatization of every single Latin word across the complete 73-book critical Vulgate",
            "Distinguishes between Jerome's Hebrew-based and Septuagint-based Latin vocabulary",
            "Standard lexicon reference for patristic and medieval scholastic theology"
        ]
    }
]


def get_catalog() -> List[Dict[str, Any]]:
    """Return the complete catalog of scholarly critical editions."""
    return CRITICAL_EDITIONS_CATALOG


def get_edition_by_id(edition_id: str) -> Optional[Dict[str, Any]]:
    """Fetch an edition specification by its unique ID."""
    for ed in CRITICAL_EDITIONS_CATALOG:
        if ed["id"] == edition_id:
            return ed
    return None


def export_catalog_json(output_path: str) -> None:
    """Save the catalog as JSON for suite loading."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(CRITICAL_EDITIONS_CATALOG, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(CRITICAL_EDITIONS_CATALOG)} critical editions to {output_path}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources_cache")
    os.makedirs(out_dir, exist_ok=True)
    export_catalog_json(os.path.join(out_dir, "critical_editions_catalog.json"))
