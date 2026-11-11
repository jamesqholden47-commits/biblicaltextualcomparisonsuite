"""
manuscripts_core.py - Core Engine for CatholicJarvis Manuscript Paleography Suite
Path: 09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/modules/manuscripts_core.py
Author: Antigravity Autonomous Academic Fleet
Date: 2026-10-09

Provides primary data structures, IIIF endpoint resolvers, word-level morphological
alignments, multi-spectral paleography simulations, and academic citation formatters
for New Testament, Patristic, and Second Temple biblical codices.
"""

import os
import json
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CUSTOM_MS_FILE = os.path.join(DATA_DIR, "custom_manuscripts.json")

# Primary Curated Manuscript Registry
# Flagship witnesses for biblical, patristic, and Second Temple textual criticism
MANUSCRIPT_REGISTRY: List[Dict[str, Any]] = [
    # ── 1. The Great Uncials (Majuscules) ────────────────────────────────────
    {
        "id": "codex_vaticanus",
        "name": "Codex Vaticanus",
        "siglum": "B / 03 / Vat.gr.1209",
        "date": "c. 325–350 AD",
        "century": "4th Century",
        "material": "Vellum (Fine Calfskin Parchment)",
        "language": "Greek (Alexandrian Uncial / Majuscule)",
        "repository": "Biblioteca Apostolica Vaticana",
        "city": "Vatican City",
        "iiif_manifest": "https://digi.vatlib.it/iiif/MSS_Vat.gr.1209/manifest.json",
        "viewer_url": "https://digi.vatlib.it/view/MSS_Vat.gr.1209",
        "description": "The premier and most reliable extant uncial codex of the Greek Bible. Produced during the Constantinian era on exceptionally fine vellum. Contains three columns per page (resembling open scroll columns). Flagship witness for Alexandrian text-type and definitive baseline against skeptical claims of late textual corruption.",
        "folios": [
            {
                "id": "p1303_luke1",
                "label": "Page 1303 (Luke 1:1–4 — The Prologue)",
                "passage": "Luke 1:1–4",
                "shelfmark": "Vat.gr.1209, p. 1303, col. B",
                "image_url": "https://digi.vatlib.it/iiifimage/MSS_Vat.gr.1209/Vat.gr.1209_1307_pa_1303.jp2/full/1200,/0/default.jpg",
                "fallback_img": "/static/images/ms_vaticanus_luke1.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 380, "y": 140, "w": 420, "h": 260},
                "paleographical_notes": "Continuous uncial script (scriptio continua) without word division or accents. Note line 5 where the first-person singular compound 'ΚΑΜΟΙ' (κἀμοί = καὶ ἐμοί, 'to me also') occurs with unmistakable clarity, conclusively demolishing popular skeptical claims that Luke never writes in the first person.",
                "theological_bearing": "Forensic refutation of Bart Ehrman's claim that the Gospels never use first-person pronouns. Luke 1:2 explicitly asserts transmission from 'eyewitnesses' (αὐτόπται), and Luke 1:3 explicitly employs first-person singular 'ἔδοξε κἀμοί' ('it seemed good to ME also').",
                "vulgate": "Quoniam quidem multi conati sunt ordinare narrationem, quae in nobis completae sunt, rerum: sicut tradiderunt nobis, qui ab initio ipsi viderunt, et ministri fuerunt sermonis: visum est et mihi, assecuto a principio omnibus diligenter, ex ordine tibi scribere, optime Theophile, ut cognoscas eorum verborum, de quibus eruditus es, veritatem.",
                "lines": [
                    {"line_num": 1, "uncial": "ΕΠΕΙΔΗΠΕΡΠΟΛΛΟΙΕΠΕΧΕΙΡΗΣΑΝ", "minuscule": "Ἐπειδήπερ πολλοὶ ἐπεχείρησαν", "translation": "Inasmuch as many have undertaken"},
                    {"line_num": 2, "uncial": "ΑΝΑΤΑΞΑΣΘΑΙΔΙΗΓΗΣΙΝΠΕΡΙ", "minuscule": "ἀνατάξασθαι διήγησιν περὶ", "translation": "to compile an orderly narrative concerning"},
                    {"line_num": 3, "uncial": "ΤΩΝΠΕΠΛΗΡΟΦΟΡΗΜΕΝΩΝΕΝΗΜΙΝ", "minuscule": "τῶν πεπληροφορημένων ἐν ἡμῖν", "translation": "the things accomplished among us,"},
                    {"line_num": 4, "uncial": "ΠΡΑΓΜΑΤΩΝΚΑΘΩΣΠΑΡΕΔΟΣΑΝΗΜΙΝ", "minuscule": "πραγμάτων, καθὼς παρέδοσαν ἡμῖν", "translation": "matters, just as they were handed down to us"},
                    {"line_num": 5, "uncial": "ΟΙΑΠΑΡΧΗΣΑΥΤΟΠΤΑΙΚΑΙ", "minuscule": "οἱ ἀπ’ ἀρχῆς αὐτόπται καὶ", "translation": "by those who from the beginning were eyewitnesses and"},
                    {"line_num": 6, "uncial": "ΥΠΗΡΕΤΑΙΓΕΝΟΜΕΝΟΙΤΟΥΛΟΓΟΥ", "minuscule": "ὑπηρέται γενόμενοι τοῦ λόγου,", "translation": "ministers of the word,"},
                    {"line_num": 7, "uncial": "ΕΔΟΞΕΚΑΜΟΙΠΑΡΗΚΟΛΟΥΘΗΚΟΤΙ", "minuscule": "ἔδοξε κἀμοί, παρηκολουθηκότι", "translation": "it seemed good to ME also, having investigated"},
                    {"line_num": 8, "uncial": "ΑΝΩΘΕΝΠΑΣΙΝΑΚΡΙΒΩΣ", "minuscule": "ἄνωθεν πᾶσιν ἀκριβῶς,", "translation": "everything accurately from the beginning,"},
                    {"line_num": 9, "uncial": "ΚΑΘΕΞΗΣΣΟΙΓΡΑΨΑΙΚΡΑΤΙΣΤΕ", "minuscule": "καθεξῆς σοι γράψαι, κράτιστε", "translation": "to write to you in order, most excellent"},
                    {"line_num": 10, "uncial": "ΘΕΟΦΙΛΕΙΝΑΕΠΙΓΝΩΣ", "minuscule": "Θεόφιλε, ἵνα ἐπιγνῷς", "translation": "Theophilus, so that you may know"}
                ],
                "words_morph": [
                    {"word": "ΕΠΕΙΔΗΠΕΡ", "lemma": "ἐπειδήπερ", "pos": "Conjunction", "parse": "Causal conjunction", "gloss": "inasmuch as, since indeed"},
                    {"word": "ΠΟΛΛΟΙ", "lemma": "πολύς", "pos": "Adjective", "parse": "Nom Pl Masc", "gloss": "many"},
                    {"word": "ΕΠΕΧΕΙΡΗΣΑΝ", "lemma": "ἐπιχειρέω", "pos": "Verb", "parse": "Aorist Act Ind 3rd Pl", "gloss": "undertook, attempted"},
                    {"word": "ΠΑΡΕΔΟΣΑΝ", "lemma": "παραδίδωμι", "pos": "Verb", "parse": "Aorist Act Ind 3rd Pl", "gloss": "handed down, transmitted"},
                    {"word": "ΗΜΙΝ", "lemma": "ἐγώ", "pos": "Pronoun", "parse": "1st Pl Dat", "gloss": "to us (1st person plural)"},
                    {"word": "ΑΥΤΟΠΤΑΙ", "lemma": "αὐτόπτης", "pos": "Noun", "parse": "Nom Pl Masc", "gloss": "eyewitnesses (seeing with own eyes)"},
                    {"word": "ΕΔΟΞΕ", "lemma": "δοκέω", "pos": "Verb", "parse": "Aorist Act Ind 3rd Sg", "gloss": "it seemed good"},
                    {"word": "ΚΑΜΟΙ", "lemma": "κἀμοί", "pos": "Pronoun", "parse": "Crasis: καὶ + ἐμοί (1st Sg Dat)", "gloss": "to ME also (1st person singular)"},
                    {"word": "ΑΚΡΙΒΩΣ", "lemma": "ἀκριβῶς", "pos": "Adverb", "parse": "Manner adverb", "gloss": "accurately, diligently"}
                ]
            },
            {
                "id": "p1348_john1",
                "label": "Page 1348 (John 1:1–18 — The Logos Prologue)",
                "passage": "John 1:1–18",
                "shelfmark": "Vat.gr.1209, p. 1348, col. A",
                "image_url": "https://digi.vatlib.it/iiifimage/MSS_Vat.gr.1209/Vat.gr.1209_1352_pa_1348.jp2/full/1200,/0/default.jpg",
                "fallback_img": "/static/images/ms_vaticanus_john1.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 120, "y": 80, "w": 400, "h": 500},
                "paleographical_notes": "Opening of the Fourth Gospel. Displays ancient majuscule script with Nomina Sacra contractions (ΘС for Θεός). Note John 1:14: 'ΚΑΙ ΕΘΕΑΣΑΜΕΘΑ ΤΗΝ ΔΟΞΑΝ ΑΥΤΟΥ' ('and WE beheld His glory'), proving first-person eyewitness testimony.",
                "theological_bearing": "Foundational text of High Christology and the Incarnation. Collation against Second Temple Memra theology (Boyarin) and refutation of Arianism.",
                "vulgate": "In principio erat Verbum, et Verbum erat apud Deum, et Deus erat Verbum. Hoc erat in principio apud Deum. Omnia per ipsum facta sunt: et sine ipso factum est nihil, quod factum est.",
                "lines": [
                    {"line_num": 1, "uncial": "ΕΝΑΡΧΗΗΝΟΛΟΓΟΣΚΑΙΟΛΟΓΟΣ", "minuscule": "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος", "translation": "In the beginning was the Word, and the Word"},
                    {"line_num": 2, "uncial": "ΗΝΠΡΟΣΤΟΝΘΝΚΑΙΘΣΗΝΟΛΟΓΟΣ", "minuscule": "ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος.", "translation": "was with God, and the Word was God."},
                    {"line_num": 3, "uncial": "ΟΥΤΟΣΗΝΕΝΑΡΧΗΠΡΟΣΤΟΝΘΝ", "minuscule": "Οὗτος ἦν ἐν ἀρχῇ πρὸς τὸν θεόν.", "translation": "He was in the beginning with God."},
                    {"line_num": 4, "uncial": "ΠΑΝΤΑΔΙΑΥΤΟΥΕΓΕΝΕΤΟΚΑΙ", "minuscule": "πάντα δι’ αὐτοῦ ἐγένετο, καὶ", "translation": "All things were made through Him, and"},
                    {"line_num": 5, "uncial": "ΧΩΡΙΣΑΥΤΟΥΕΓΕΝΕΤΟΟΥΔΕΕΝ", "minuscule": "χωρὶς αὐτοῦ ἐγένετο οὐδὲ ἕν,", "translation": "without Him was not anything made"}
                ],
                "words_morph": [
                    {"word": "ΕΝΑΡΧΗ", "lemma": "ἀρχή", "pos": "Noun", "parse": "Dat Sg Fem with prep ἐν", "gloss": "in the beginning"},
                    {"word": "ΛΟΓΟΣ", "lemma": "λόγος", "pos": "Noun", "parse": "Nom Sg Masc", "gloss": "the Word / Reason / Divine Wisdom"},
                    {"word": "ΘΝ", "lemma": "θεός", "pos": "Noun (Nomen Sacrum)", "parse": "Acc Sg Masc (contracted Θ̅Ν̅)", "gloss": "God (the Father)"},
                    {"word": "ΘΣ", "lemma": "θεός", "pos": "Noun (Nomen Sacrum)", "parse": "Nom Sg Masc (contracted Θ̅Σ̅)", "gloss": "God (in nature/essence)"}
                ]
            }
        ]
    },
    {
        "id": "codex_sinaiticus",
        "name": "Codex Sinaiticus",
        "siglum": "א / 01",
        "date": "c. 330–360 AD",
        "century": "4th Century",
        "material": "Vellum (Parchment)",
        "language": "Greek (Uncial)",
        "repository": "British Library / Leipzig / St. Catherine's / St. Petersburg",
        "city": "London / Leipzig / Sinai",
        "iiif_manifest": "https://www.codexsinaiticus.org/iiif/manifest.json",
        "viewer_url": "https://codexsinaiticus.org/en/manuscript.aspx",
        "description": "One of the four great uncial codices, containing the oldest complete New Testament plus the Epistle of Barnabas and Shepherd of Hermas. Discovered by Constantin von Tischendorf at Saint Catherine's Monastery at Mount Sinai. Written in four columns per page.",
        "folios": [
            {
                "id": "sinaiticus_john21",
                "label": "Quire 80, Folio 4r (John 21:24–25 — The Eyewitness Endorsement)",
                "passage": "John 21:24–25",
                "shelfmark": "BL Add. MS 43725, f. 250r",
                "image_url": "https://www.codexsinaiticus.org/images/manuscript/BL_Add_MS_43725/BL_Add_MS_43725_f250r.jpg",
                "fallback_img": "/static/images/ms_sinaiticus_john21.jpg",
                "dimensions": {"width": 1200, "height": 1500},
                "coordinates": {"x": 200, "y": 600, "w": 450, "h": 220},
                "paleographical_notes": "Closing lines of the Gospel of John. Uncial text shows 'ΟΥΤΟΣ ΕΣΤΙΝ Ο ΜΑΘΗΤΗΣ Ο ΜΑΡΤΥΡΩΝ... ΚΑΙ ΟΙΔΑΜΕΝ ΟΤΙ ΑΛΗΘΗΣ ΕΣΤΙΝ Η ΜΑΡΤΥΡΙΑ ΑΥΤΟΥ'. Shows communal witness 'ΟΙΔΑΜΕΝ' (we know).",
                "theological_bearing": "Direct documentary evidence of apostolic eyewitness transmission from the Beloved Disciple.",
                "vulgate": "Hic est discipulus ille, qui testimonium perhibet de his, et scripsit haec: et scimus quia verum est testimonium ejus.",
                "lines": [
                    {"line_num": 1, "uncial": "ΟΥΤΟΣΕΣΤΙΝΟΜΑΘΗΤΗΣΟΜΑΡΤΥΡΩΝ", "minuscule": "Οὗτός ἐστιν ὁ μαθητὴς ὁ μαρτυρῶν", "translation": "This is the disciple who is bearing witness"},
                    {"line_num": 2, "uncial": "ΠΕΡΙΤΟΥΤΩΝΚΑΙΟΓΡΑΨΑΣΤΑΥΤΑ", "minuscule": "περὶ τούτων καὶ ὁ γράψας ταῦτα,", "translation": "concerning these things and who wrote these things,"},
                    {"line_num": 3, "uncial": "ΚΑΙΟΙΔΑΜΕΝΟΤΙΑΛΗΘΗΣΕΣΤΙΝ", "minuscule": "καὶ οἴδαμεν ὅτι ἀληθής ἐστιν", "translation": "and WE KNOW [οἴδαμεν] that is true"},
                    {"line_num": 4, "uncial": "ΗΜΑΡΤΥΡΙΑΑΥΤΟΥ", "minuscule": "ἡ μαρτυρία αὐτοῦ.", "translation": "the testimony of him."}
                ],
                "words_morph": [
                    {"word": "ΜΑΘΗΤΗΣ", "lemma": "μαθητής", "pos": "Noun", "parse": "Nom Sg Masc", "gloss": "disciple"},
                    {"word": "ΜΑΡΤΥΡΩΝ", "lemma": "μαρτυρέω", "pos": "Verb (Participle)", "parse": "Pres Act Part Nom Sg Masc", "gloss": "bearing witness"},
                    {"word": "ΟΙΔΑΜΕΝ", "lemma": "οἶδα", "pos": "Verb", "parse": "Perf Act Ind 1st Pl (used as present)", "gloss": "we know (1st person plural)"},
                    {"word": "ΑΛΗΘΗΣ", "lemma": "ἀληθής", "pos": "Adjective", "parse": "Nom Sg Fem", "gloss": "true, genuine"}
                ]
            },
            {
                "id": "sinaiticus_matt16",
                "label": "Quire 74, Folio 2v (Matthew 16:18–19 — Petrine Rock & Keys)",
                "passage": "Matthew 16:18–19",
                "shelfmark": "BL Add. MS 43725, f. 202v",
                "image_url": "https://www.codexsinaiticus.org/images/manuscript/BL_Add_MS_43725/BL_Add_MS_43725_f202v.jpg",
                "fallback_img": "/static/images/ms_sinaiticus_matt16.jpg",
                "dimensions": {"width": 1200, "height": 1500},
                "coordinates": {"x": 180, "y": 420, "w": 460, "h": 280},
                "paleographical_notes": "Uncial witness to Christ's solemn promise to Peter: 'ΚΑΓΩ ΔΕ ΣΟΙ ΛΕΓΩ ΟΤΙ ΣΥ ΕΙ ΠΕΤΡΟΣ ΚΑΙ ΕΠΙ ΤΑΥΤΗ ΤΗ ΠΕΤΡΑ ΟΙΚΟΔΟΜΗΣΩ ΜΟΥ ΤΗΝ ΕΚΚΛΗΣΙΑΝ'. Contains clear Nomina Sacra and uninterrupted punctuation.",
                "theological_bearing": "Foundational charter of the Petrine Primacy and apostolic foundation of the Church against the gates of Hades.",
                "vulgate": "Et ego dico tibi, quia tu es Petrus, et super hanc petram aedificabo Ecclesiam meam, et portae inferi non praevalebunt adversus eam. Et tibi dabo claves regni caelorum.",
                "lines": [
                    {"line_num": 1, "uncial": "ΚΑΓΩΔΕΣΟΙΛΕΓΩΟΤΙΣΥΕΙΠΕΤΡΟΣ", "minuscule": "κἀγὼ δέ σοι λέγω ὅτι σὺ εἶ Πέτρος,", "translation": "And I say to you that you are Peter,"},
                    {"line_num": 2, "uncial": "ΚΑΙΕΠΙΤΑΥΤΗΤΗΠΕΤΡΑ", "minuscule": "καὶ ἐπὶ ταύτῃ τῇ πέτρᾳ", "translation": "and upon this rock"},
                    {"line_num": 3, "uncial": "ΟΙΚΟΔΟΜΗΣΩΜΟΥΤΗΝΕΚΚΛΗΣΙΑΝ", "minuscule": "οἰκοδομήσω μου τὴν ἐκκλησίαν,", "translation": "I will build my Church,"},
                    {"line_num": 4, "uncial": "ΚΑΙΠΥΛΑΙΑΙΔΟΥΟΥΚΑΤΙΣΧΥΣΟΥΣΙΝ", "minuscule": "καὶ πύλαι ᾅδου οὐ κατισχύσουσιν", "translation": "and the gates of Hades shall not prevail"}
                ],
                "words_morph": [
                    {"word": "ΠΕΤΡΟΣ", "lemma": "Πέτρος", "pos": "Proper Noun", "parse": "Nom Sg Masc", "gloss": "Peter (Rock, Cephas)"},
                    {"word": "ΠΕΤΡΑ", "lemma": "πέτρα", "pos": "Noun", "parse": "Dat Sg Fem", "gloss": "rock, bedrock cliff"},
                    {"word": "ΟΙΚΟΔΟΜΗΣΩ", "lemma": "οἰκοδομέω", "pos": "Verb", "parse": "Fut Act Ind 1st Sg", "gloss": "I will build"},
                    {"word": "ΕΚΚΛΗΣΙΑΝ", "lemma": "ἐκκλησία", "pos": "Noun", "parse": "Acc Sg Fem", "gloss": "Church, sacred assembly"}
                ]
            }
        ]
    },
    {
        "id": "codex_alexandrinus",
        "name": "Codex Alexandrinus",
        "siglum": "A / 02",
        "date": "c. 400–440 AD",
        "century": "5th Century",
        "material": "Vellum",
        "language": "Greek (Uncial)",
        "repository": "British Library",
        "city": "London",
        "iiif_manifest": None,  # No public IIIF manifest confirmed for this item (checked 2026-11-10); the
        # earlier value here was a fabricated placeholder ID ("vdc_100000000000.0x000000") that never
        # resolved. viewer_url below is the real, verified British Library Archives & Manuscripts
        # Catalogue record for this exact shelfmark.
        "viewer_url": "https://searcharchives.bl.uk/catalog/040-002353500",
        "description": "Crucial witness for the Epistles and Revelation, and famously the earliest manuscript containing the complete Greek text of 1 Clement and 2 Clement, proving their veneration in early Christian codices.",
        "folios": [
            {
                "id": "alexandrinus_1clement44",
                "label": "Folio 146v (1 Clement 44:1–3 — The Apostolic Succession Codicil)",
                "passage": "1 Clement 44:1–3",
                "shelfmark": "Royal MS 1 D VIII, f. 146v",
                # No public folio-level image confirmed available (checked 2026-11-10; the BL's old
                # manuscript-image URL scheme has been retired and this item's digital-image access is
                # not confirmed via the public catalogue). Points to the real catalogue record instead
                # of a fabricated image path.
                "image_url": "https://searcharchives.bl.uk/catalog/040-002353500",
                "fallback_img": "/static/images/ms_alexandrinus_clement.jpg",
                "dimensions": {"width": 1200, "height": 1500},
                "coordinates": {"x": 300, "y": 400, "w": 450, "h": 300},
                "paleographical_notes": "Uncial witness to St. Clement's Epistle to the Corinthians. Shows the legal term 'ΕΠΙΝΟΜΗΝ' (codicil/ordinance) and 'ΔΙΑΔΕΞΩΝΤΑΙ' (succeed) regarding apostolic succession.",
                "theological_bearing": "Primary manuscript proof of intentional apostolic succession legislated by the Apostles before their deaths.",
                "vulgate": "Et Apostoli nostri cognoverunt per Dominum nostrum Jesum Christum, contentionem fore de nomine episcopatus. Ob hanc causam... constituerunt praedictos, ac deinceps ordinationem dederunt, ut cum illi decessissent, ministerium eorum alii viri probati susciperent.",
                "lines": [
                    {"line_num": 1, "uncial": "ΚΑΙΟΙΑΠΟΣΤΟΛΟΙΗΜΩΝΕΓΝΩΣΑΝ", "minuscule": "Καὶ οἱ ἀπόστολοι ἡμῶν ἔγνωσαν", "translation": "And our Apostles knew"},
                    {"line_num": 2, "uncial": "ΟΤΙΕΡΙΣΕΣΤΑΙΕΠΙΤΟΥΟΝΟΜΑΤΟΣ", "minuscule": "ὅτι ἔρις ἔσται ἐπὶ τοῦ ὀνόματος", "translation": "that there would be strife over the title"},
                    {"line_num": 3, "uncial": "ΤΗΣΕΠΙΣΚΟΠΗΣ", "minuscule": "τῆς ἐπισκοπῆς·", "translation": "of the episcopate;"},
                    {"line_num": 4, "uncial": "ΚΑΤΕΣΤΗΣΑΝΤΟΥΣΠΡΟΕΙΡΗΜΕΝΟΥΣ", "minuscule": "κατέστησαν τοὺς προειρημένους,", "translation": "they appointed the aforesaid,"},
                    {"line_num": 5, "uncial": "ΚΑΙΜΕΤΑΞΥΕΠΙΝΟΜΗΝΔΕΔΩΚΑΣΙΝ", "minuscule": "καὶ μεταξὺ ἐπινομὴν δεδώκασιν,", "translation": "and subsequently gave a testamentary codicil,"},
                    {"line_num": 6, "uncial": "ΟΠΩΣΕΑΝΚΟΙΜΗΘΩΣΙΝΔΙΑΔΕΞΩΝΤΑΙ", "minuscule": "ὅπως, ἐὰν κοιμηθῶσιν, διαδέξωνται", "translation": "that if they should fall asleep, should succeed"},
                    {"line_num": 7, "uncial": "ΕΤΕΡΟΙΔΕΔΟΚΙΜΑΣΜΕΝΟΙΑΝΔΡΕΣ", "minuscule": "ἕτεροι δεδοκιμασμένοι ἄνδρες", "translation": "other approved men"},
                    {"line_num": 8, "uncial": "ΤΗΝΛΕΙΤΟΥΡΓΙΑΝΑΥΤΩΝ", "minuscule": "τὴν λειτουργίαν αὐτῶν.", "translation": "to the liturgy of them."}
                ],
                "words_morph": [
                    {"word": "ΕΠΙΣΚΟΠΗΣ", "lemma": "ἐπισκοπή", "pos": "Noun", "parse": "Gen Sg Fem", "gloss": "episcopate, oversight office"},
                    {"word": "ΕΠΙΝΟΜΗΝ", "lemma": "ἐπινομή", "pos": "Noun", "parse": "Acc Sg Fem", "gloss": "testamentary codicil, legal provision"},
                    {"word": "ΔΙΑΔΕΞΩΝΤΑΙ", "lemma": "διαδέχομαι", "pos": "Verb", "parse": "Aorist Mid Subj 3rd Pl", "gloss": "succeed to office, take over ministry"},
                    {"word": "ΛΕΙΤΟΥΡΓΙΑΝ", "lemma": "λειτουργία", "pos": "Noun", "parse": "Acc Sg Fem", "gloss": "sacred liturgical service / ministry"}
                ]
            }
        ]
    },
    {
        "id": "codex_ephraemi",
        "name": "Codex Ephraemi Rescriptus",
        "siglum": "C / 04 / Paris gr. 9",
        "date": "c. 450 AD (Undertext) / 12th Cent (Uppertext)",
        "century": "5th Century",
        "material": "Vellum Palimpsest",
        "language": "Greek",
        "repository": "Bibliothèque nationale de France (BnF)",
        "city": "Paris",
        "iiif_manifest": "https://gallica.bnf.fr/iiif/ark:/12148/btv1b8470438b/manifest.json",
        "viewer_url": "https://gallica.bnf.fr/ark:/12148/btv1b8470438b",
        "description": "The quintessential palimpsest. In the 12th century, the Greek Bible text was scraped away with pumice stone to reuse the expensive vellum for copying sermons of St. Ephrem the Syrian. Deciphered by Tischendorf in 1840; now examined with modern multi-spectral UV and raking light.",
        "folios": [
            {
                "id": "ephraemi_palimpsest_demo",
                "label": "Folio 82r (Palimpsest Undertext — Multi-Spectral Target)",
                "passage": "1 Timothy 3:15–16",
                "shelfmark": "BnF Grec 9, f. 82r",
                "image_url": "https://gallica.bnf.fr/iiif/ark:/12148/btv1b8470438b/f82/full/1200,/0/native.jpg",
                "fallback_img": "/static/images/ms_ephraemi_palimpsest.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 200, "y": 250, "w": 480, "h": 350},
                "paleographical_notes": "Palimpsest exhibit: Upper dark text is 12th-century minuscule of St. Ephrem. Faint reddish-brown undertext running perpendicular is 5th-century uncial containing 1 Tim 3:15 ('the church of the living God, the pillar and ground of the truth') and 1 Tim 3:16 (christological hymn).",
                "theological_bearing": "Demonstrates the necessity of multi-spectral imaging (UV and raking light) to recover early ecclesiastical witnesses.",
                "vulgate": "Ecclesia Dei vivi, columna et firmamentum veritatis. Et manifeste magnum est pietatis sacramentum, quod manifestatum est in carne, justificatum est in spiritu, apparuit angelis, praedicatum est gentibus, creditum est in mundo, assumptum est in gloria.",
                "lines": [
                    {"line_num": 1, "uncial": "ΕΚΚΛΗΣΙΑΘΕΟΥΖΩΝΤΟΣ", "minuscule": "ἐκκλησία θεοῦ ζῶντος,", "translation": "the Church of the living God,"},
                    {"line_num": 2, "uncial": "ΣΤΥΛΟΣΚΑΙΕΔΡΑΙΩΜΑ", "minuscule": "στῦλος καὶ ἑδραίωμα", "translation": "the pillar and buttress"},
                    {"line_num": 3, "uncial": "ΤΗΣΑΛΗΘΕΙΑΣ", "minuscule": "τῆς ἀληθείας.", "translation": "of the truth."}
                ],
                "words_morph": [
                    {"word": "ΕΚΚΛΗΣΙΑ", "lemma": "ἐκκλησία", "pos": "Noun", "parse": "Nom Sg Fem", "gloss": "Church, assembly"},
                    {"word": "ΣΤΥΛΟΣ", "lemma": "στῦλος", "pos": "Noun", "parse": "Nom Sg Masc", "gloss": "pillar"},
                    {"word": "ΕΔΡΑΙΩΜΑ", "lemma": "ἑδραίωμα", "pos": "Noun", "parse": "Nom Sg Neut", "gloss": "buttress, ground, foundation"}
                ]
            }
        ]
    },
    {
        "id": "codex_bezae",
        "name": "Codex Bezae Cantabrigiensis",
        "siglum": "D / 05 / MS Nn.2.41",
        "date": "c. 400 AD",
        "century": "5th Century",
        "material": "Vellum (Graeco-Latin Diglot)",
        "language": "Greek & Latin (Parallel Pages)",
        "repository": "Cambridge University Library",
        "city": "Cambridge",
        "iiif_manifest": "https://cudl.lib.cam.ac.uk/iiif/MS-NN-00002-00041",
        "viewer_url": "https://cudl.lib.cam.ac.uk/view/MS-NN-00002-00041/1",
        "description": "The primary representative of the Western text-type for the Gospels and Acts. Gifted by Theodore Beza to Cambridge University in 1581. Features facing Greek and Latin uncial pages with distinctive historical glosses and readings.",
        "folios": [
            {
                "id": "bezae_acts15",
                "label": "Folio 470v (Acts 15:28–29 — The Council of Jerusalem Decree)",
                "passage": "Acts 15:28–29",
                "shelfmark": "CUL MS Nn.2.41, f. 470v",
                "image_url": "https://cudl.lib.cam.ac.uk/content/images/MS-NN-00002-00041-000-00940.jpg",
                "fallback_img": "/static/images/ms_bezae_acts15.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 220, "y": 300, "w": 460, "h": 280},
                "paleographical_notes": "Facing Greek page showing the conciliar decree: 'ΕΔΟΞΕΝ ΓΑΡ ΤΩ ΑΓΙΩ ΠΝΕΥΜΑΤΙ ΚΑΙ ΗΜΙΝ' ('Visum est enim Spiritui Sancto et nobis'). Shows authentic Western text framing.",
                "theological_bearing": "The apostolic prototype of Ecumenical Conciliar authority: decisions promulgated by the Apostles under the inspiration of the Holy Spirit bind the universal Church.",
                "vulgate": "Visum est enim Spiritui Sancto et nobis, nihil ultra imponere vobis oneris quam haec necessaria: Ut abstineatis vos ab immolatis simulacrorum, et sanguine, et suffocato, et fornicatione: a quibus custodientes vos, bene agetis. Valete.",
                "lines": [
                    {"line_num": 1, "uncial": "ΕΔΟΞΕΝΓΑΡΤΩΑΓΙΩΠΝΕΥΜΑΤΙΚΑΙΗΜΙΝ", "minuscule": "ἔδοξεν γὰρ τῷ ἁγίῳ πνεύματι καὶ ἡμῖν", "translation": "For it seemed good to the Holy Spirit and to us"},
                    {"line_num": 2, "uncial": "ΜΗΔΕΝΠΛΕΟΝΕΠΙΤΙΘΕΣΘΑΙΥΜΙΝΒΑΡΟΣ", "minuscule": "μηδὲν πλέον ἐπιτίθεσθαι ὑμῖν βάρος", "translation": "to lay upon you no greater burden"},
                    {"line_num": 3, "uncial": "ΠΛΗΝΤΟΥΤΩΝΤΩΝΕΠΑΝΑΓΚΕΣ", "minuscule": "πλὴν τούτων τῶν ἐπάναγκες,", "translation": "than these necessary things:"}
                ],
                "words_morph": [
                    {"word": "ΕΔΟΞΕΝ", "lemma": "δοκέω", "pos": "Verb", "parse": "Aorist Act Ind 3rd Sg", "gloss": "it seemed good, was decreed"},
                    {"word": "ΠΝΕΥΜΑΤΙ", "lemma": "πνεῦμα", "pos": "Noun", "parse": "Dat Sg Neut", "gloss": "the Spirit"},
                    {"word": "ΗΜΙΝ", "lemma": "ἐγώ", "pos": "Pronoun", "parse": "1st Pl Dat", "gloss": "to us (apostles)"}
                ]
            }
        ]
    },
    {
        "id": "codex_washingtonianus",
        "name": "Codex Washingtonianus (Freer Gospels)",
        "siglum": "W / 032 / F1906.274",
        "date": "c. 400 AD",
        "century": "4th–5th Century",
        "material": "Vellum",
        "language": "Greek (Uncial)",
        "repository": "Smithsonian Institution, Freer Gallery of Art",
        "city": "Washington, D.C.",
        "iiif_manifest": None,  # "FS-F1906.274" 404s (checked 2026-11-10); the Smithsonian's real IIIF
        # manifests for this item use a different ID scheme (FS-7127_01 through _10) but none carry a
        # folio label matching f.235r specifically, so no single correct manifest URL is confirmed.
        "viewer_url": "https://asia.si.edu/explore-art-culture/collections/search/edanmdm:fsg_F1906.274/",
        "description": "Acquired in Cairo by Charles Lang Freer in 1906. Famous for preserving the four Gospels in the Western order (Matthew, John, Luke, Mark) and containing the unique 'Freer Logion' following Mark 16:14.",
        "folios": [
            {
                "id": "washington_mark16",
                "label": "Folio 235r (Mark 16:14 — The Freer Logion)",
                "passage": "Mark 16:14–15",
                "shelfmark": "Freer F1906.274, f. 235r",
                "image_url": "https://asia.si.edu/explore-art-culture/collections/search/edanmdm:fsg_F1906.274/",
                "fallback_img": "/static/images/ms_washington_mark16.jpg",
                "dimensions": {"width": 1100, "height": 1500},
                "coordinates": {"x": 150, "y": 320, "w": 480, "h": 320},
                "paleographical_notes": "Contains the celebrated uncial insertion between Mark 16:14 and 16:15 where the disciples answer Christ regarding the end of the years of Satan's power, cited by St. Jerome in Contra Pelagianos II.15.",
                "theological_bearing": "Demonstrates early patristic circulation of the Longer Ending of Mark (Mark 16:9-20) confirmed by Jerome in ancient Latin copies.",
                "vulgate": "Novissime recumbentibus illis undecim apparuit: et exprobravit incredulitatem eorum et duritiam cordis, quia iis, qui viderant eum resurrexisse, non crediderant. Et dixit eis: Euntes in mundum universum praedicate Evangelium omni creaturae.",
                "lines": [
                    {"line_num": 1, "uncial": "ΚΑΚΕΙΝΟΙΑΠΕΛΟΓΟΥΝΤΟΛΕΓΟΝΤΕΣ", "minuscule": "κἀκεῖνοι ἀπελογοῦντο λέγοντες", "translation": "And they excused themselves, saying,"},
                    {"line_num": 2, "uncial": "ΟΤΙΟΑΙΩΝΟΥΤΟΣΤΗΣΑΝΟΜΙΑΣ", "minuscule": "ὅτι ὁ αἰὼν οὗτος τῆς ἀνομίας", "translation": "This age of lawlessness"},
                    {"line_num": 3, "uncial": "ΚΑΙΤΗΣΑΠΙΣΤΙΑΣΥΠΟΤΟΝΣΑΤΑΝΑΝΕΣΤΙΝ", "minuscule": "καὶ τῆς ἀπιστίας ὑπὸ τὸν Σατανᾶν ἐστιν", "translation": "and of unbelief is under Satan"}
                ],
                "words_morph": [
                    {"word": "ΑΠΕΛΟΓΟΥΝΤΟ", "lemma": "ἀπολογέομαι", "pos": "Verb", "parse": "Imperfect Mid Ind 3rd Pl", "gloss": "defended themselves"},
                    {"word": "ΑΙΩΝ", "lemma": "αἰών", "pos": "Noun", "parse": "Nom Sg Masc", "gloss": "age, epoch, world"},
                    {"word": "ΑΝΟΜΙΑΣ", "lemma": "ἀνομία", "pos": "Noun", "parse": "Gen Sg Fem", "gloss": "lawlessness"}
                ]
            }
        ]
    },
    {
        "id": "codex_claromontanus",
        "name": "Codex Claromontanus",
        "siglum": "D / 06 / BnF Grec 107",
        "date": "c. 5th–6th Century",
        "century": "6th Century",
        "material": "Vellum Diglot",
        "language": "Greek & Latin (Bilingual)",
        "repository": "Bibliothèque nationale de France (BnF)",
        "city": "Paris",
        "iiif_manifest": "https://gallica.bnf.fr/iiif/ark:/12148/btv1b8470433r/manifest.json",
        "viewer_url": "https://gallica.bnf.fr/ark:/12148/btv1b8470433r",
        "description": "Monumental Graeco-Latin uncial manuscript of the Pauline Epistles and Hebrews. Contains the famous Catalogus Claromontanus, an ancient 4th-century stichometric canon catalog of the Old and New Testaments.",
        "folios": [
            {
                "id": "claromontanus_romans1",
                "label": "Folio 14r (Romans 1:1–4 — The Incarnational Lineage)",
                "passage": "Romans 1:1–4",
                "shelfmark": "BnF Grec 107, f. 14r",
                "image_url": "https://gallica.bnf.fr/iiif/ark:/12148/btv1b8470433r/f14/full/1200,/0/native.jpg",
                "fallback_img": "/static/images/ms_claromontanus_romans1.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 200, "y": 200, "w": 480, "h": 320},
                "paleographical_notes": "Paul's opening confession: Christ born of the seed of David according to the flesh, designated Son of God in power according to the Spirit of holiness by His resurrection from the dead.",
                "theological_bearing": "High Pauline Christology rooting Jesus in the Davidic Royal line while affirming divine pre-existence.",
                "vulgate": "Paulus, servus Christi Jesu, vocatus Apostolus, segregatus in Evangelium Dei, quod ante promiserat per prophetas suos in Scripturis sanctis de Filio suo, qui factus est ei ex semine David secundum carnem: qui praedestinatus est Filius Dei in virtute secundum Spiritum sanctificationis ex resurrectione mortuorum Jesu Christi Domini nostri.",
                "lines": [
                    {"line_num": 1, "uncial": "ΠΑΥΛΟΣΔΟΥΛΟΣΧΥΙΥΚΛΗΤΟΣΑΠΟΣΤΟΛΟΣ", "minuscule": "Παῦλος δοῦλος Χριστοῦ Ἰησοῦ, κλητὸς ἀπόστολος,", "translation": "Paul, a servant of Christ Jesus, called to be an apostle,"},
                    {"line_num": 2, "uncial": "ΑΦΩΡΙΣΜΕΝΟΣΕΙΣΕΥΑΓΓΕΛΙΟΝΘΥ", "minuscule": "ἀφωρισμένος εἰς εὐαγγέλιον θεοῦ,", "translation": "set apart for the Gospel of God,"},
                    {"line_num": 3, "uncial": "ΠΕΡΙΤΟΥΥΙΟΥΑΥΤΟΥΤΟΥΓΕΝΟΜΕΝΟΥ", "minuscule": "περὶ τοῦ υἱοῦ αὐτοῦ τοῦ γενομένου", "translation": "concerning His Son, who was born"},
                    {"line_num": 4, "uncial": "ΕΚΣΠΕΡΜΑΤΟΣΔΑΥΙΔΚΑΤΑΣΑΡΚΑ", "minuscule": "ἐκ σπέρματος Δαυὶδ κατὰ σάρκα,", "translation": "of the seed of David according to the flesh."}
                ],
                "words_morph": [
                    {"word": "ΔΟΥΛΟΣ", "lemma": "δοῦλος", "pos": "Noun", "parse": "Nom Sg Masc", "gloss": "servant, bondslave"},
                    {"word": "ΑΠΟΣΤΟΛΟΣ", "lemma": "ἀπόστολος", "pos": "Noun", "parse": "Nom Sg Masc", "gloss": "apostle, commissioned envoy"},
                    {"word": "ΣΠΕΡΜΑΤΟΣ", "lemma": "σπέρμα", "pos": "Noun", "parse": "Gen Sg Neut", "gloss": "seed, physical descendant"},
                    {"word": "ΣΑΡΚΑ", "lemma": "σάρξ", "pos": "Noun", "parse": "Acc Sg Fem", "gloss": "flesh, human nature"}
                ]
            }
        ]
    },

    # ── 2. The Early Papyri ──────────────────────────────────────────────────
    {
        "id": "papyrus_52",
        "name": "Papyrus 52 (Rylands Greek 457)",
        "siglum": "𝔓52 / P.Rylands 457",
        "date": "c. 125–150 AD",
        "century": "2nd Century (Hadrianic Era)",
        "material": "Papyrus Fragment",
        "language": "Greek",
        "repository": "John Rylands University Library",
        "city": "Manchester",
        "iiif_manifest": None,  # The Rylands Library's own LUNA manifest now returns
        # {"error": "Permission Issue"} under HTTP 200 (checked 2026-11-10) -- public IIIF access has been
        # restricted since this entry was written. viewer_url below (CSNTM's own manuscript viewer) is a
        # real, working, publicly accessible alternative, confirmed by exact field match (Shelf Number
        # Gr. P. 457, Manchester John Rylands University Library).
        "viewer_url": "https://manuscripts.csntm.org/Manuscript/View/GA_P52",
        "description": "The oldest extant manuscript fragment of any New Testament text in existence. Dated paleographically to c. 125–150 AD. Preserves John 18:31–33 (recto) and 18:37–38 (verso). Proves that the Gospel of John was copied, circulated, and read in provincial Egypt within decades of its composition, demolishing the 19th-century Tübingen claim that John was written after 160 AD.",
        "folios": [
            {
                "id": "p52_recto_verso",
                "label": "Fragment Recto/Verso (John 18:37–38 — 'What is Truth?')",
                "passage": "John 18:37–38",
                "shelfmark": "P.Rylands Greek 457, Verso",
                "image_url": "https://manuscripts.csntm.org/Manuscript/View/GA_P52",
                "fallback_img": "/static/images/ms_p52_verso.jpg",
                "dimensions": {"width": 800, "height": 1100},
                "coordinates": {"x": 100, "y": 80, "w": 400, "h": 500},
                "paleographical_notes": "Small papyrus scrap measuring 8.9 x 6 cm. Written in a rounded, decorated literary hand typical of Hadrianic administrative and literary documents. Verso shows Pilate's question: 'ΤΙ ΕΣΤΙΝ ΑΛΗΘΕΙΑ' ('What is truth?').",
                "theological_bearing": "Crucial paleographical chronometer. Confirms that Johannine High Christology was in widespread written transmission before 130 AD.",
                "vulgate": "Dixit itaque ei Pilatus: Ergo rex es tu? Respondit Jesus: Tu dicis quia rex sum ego. Ego in hoc natus sum, et ad hoc veni in mundum, ut testimonium perhibeam veritati: omnis qui est ex veritate, audit vocem meam. Dicit ei Pilatus: Quid est veritas?",
                "lines": [
                    {"line_num": 1, "uncial": "ΒΑΣΙΛΕΥΣΕΙΜΙΕΓΩΕΙΣΤΟΥΤΟΓΕΓΕΝΝΗΜΑΙ", "minuscule": "Βασιλεύς εἰμι. Ἐγὼ εἰς τοῦτο γεγέννημαι", "translation": "A king I am. I for this cause was born,"},
                    {"line_num": 2, "uncial": "ΚΑΙΕΙΣΤΟΥΤΟΕΛΗΛΥΘΑΕΙΣΤΟΝΚΟΣΜΟΝ", "minuscule": "καὶ εἰς τοῦτο ἐλήλυθα εἰς τὸν κόσμον,", "translation": "and for this cause came into the world,"},
                    {"line_num": 3, "uncial": "ΙΝΑΜΑΡΤΥΡΗΣΩΤΗΑΛΗΘΕΙΑ", "minuscule": "ἵνα μαρτυρήσω τῇ ἀληθείᾳ.", "translation": "that I should bear witness to the truth."},
                    {"line_num": 4, "uncial": "ΛΕΓΕΙΑΥΤΩΟΠΕΙΛΑΤΟΣΤΙΕΣΤΙΝΑΛΗΘΕΙΑ", "minuscule": "Λέγει αὐτῷ ὁ Πειλᾶτος· Τί ἐστιν ἀλήθεια;", "translation": "Pilate says to Him: What is truth?"}
                ],
                "words_morph": [
                    {"word": "ΒΑΣΙΛΕΥΣ", "lemma": "βασιλεύς", "pos": "Noun", "parse": "Nom Sg Masc", "gloss": "king, sovereign ruler"},
                    {"word": "ΓΕΓΕΝΝΗΜΑΙ", "lemma": "γεννάω", "pos": "Verb", "parse": "Perf Pass Ind 1st Sg", "gloss": "I have been born"},
                    {"word": "ΑΛΗΘΕΙΑ", "lemma": "ἀλήθεια", "pos": "Noun", "parse": "Dat Sg Fem", "gloss": "truth, objective reality"}
                ]
            }
        ]
    },
    {
        "id": "papyrus_46",
        "name": "Papyrus 46 (Chester Beatty II / P.Mich. 6238)",
        "siglum": "𝔓46 / P.Chester Beatty II",
        "date": "c. 175–225 AD",
        "century": "Late 2nd / Early 3rd Century",
        "material": "Papyrus Codex",
        "language": "Greek",
        "repository": "Chester Beatty Library / University of Michigan",
        "city": "Dublin / Ann Arbor",
        "iiif_manifest": None,  # "iiif/BP_II/manifest.json" 404s (checked 2026-11-10); the real IIIF
        # manifest path/id for this item on the CBL viewer was not confirmed. viewer_url below (the
        # object page itself) is confirmed real and working.
        "viewer_url": "https://viewer.cbl.ie/viewer/object/BP_II/",
        "description": "The earliest extant manuscript collection of the Pauline Epistles. Originally a single-quire codex of 104 leaves containing Romans, Hebrews (placed immediately following Romans, proving early canonical Pauline reception), 1–2 Corinthians, Ephesians, Galatians, Philippians, Colossians, and 1–2 Thessalonians.",
        "folios": [
            {
                "id": "p46_hebrews1",
                "label": "Folio 8r (Hebrews 1:1–4 — The Radiance of God's Glory)",
                "passage": "Hebrews 1:1–4",
                "shelfmark": "CBL BP II, f. 8r",
                "image_url": "https://viewer.cbl.ie/viewer/object/BP_II/",
                "fallback_img": "/static/images/ms_p46_hebrews1.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 180, "y": 140, "w": 480, "h": 360},
                "paleographical_notes": "Clear early uncial hand. Contains the supreme Christological confession: Christ as the 'ΑΠΑΥΓΑΣΜΑ ΤΗΣ ΔΟΞΗΣ' (effulgence/radiance of God's glory) and 'ΧΑΡΑΚΤΗΡ ΤΗΣ ΥΠΟΣΤΑΣΕΩΣ ΑΥΤΟΥ' (exact impress of His divine substance/hypostasis).",
                "theological_bearing": "Ontological proof of pre-Nicene High Christology. Christ upholds all things by the word of His power and made purification for sins before sitting at the right hand of the Majesty on high.",
                "vulgate": "Multifariam, multisque modis olim Deus loquens patribus in prophetis: novissime, diebus istis locutus est nobis in Filio, quem constituit heredem universorum, per quem fecit et saecula: qui cum sit splendor gloriae, et figura substantiae ejus, portansque omnia verbo virtutis suae, purgationem peccatorum faciens, sedet ad dexteram Majestatis in excelsis.",
                "lines": [
                    {"line_num": 1, "uncial": "ΠΟΛΥΜΕΡΩΣΚΑΙΠΟΛΥΤΡΟΠΩΣΠΑΛΑΙ", "minuscule": "Πολυμερῶς καὶ πολυτρόπως πάλαι", "translation": "In many parts and in many ways of old"},
                    {"line_num": 2, "uncial": "ΟΘΣΛΑΛΗΣΑΣΤΟΙΣΠΑΤΡΑΣΙΝΕΝΤΟΙΣΠΡΟΦΗΤΑΙΣ", "minuscule": "ὁ θεὸς λαλήσας τοῖς πατράσιν ἐν τοῖς προφήταις,", "translation": "God having spoken to the fathers in the prophets,"},
                    {"line_num": 3, "uncial": "ΕΠΕΣΧΑΤΟΥΤΩΝΗΜΕΡΩΝΤΟΥΤΩΝ", "minuscule": "ἐπ’ ἐσχάτου τῶν ἡμερῶν τούτων", "translation": "in these last days"},
                    {"line_num": 4, "uncial": "ΕΛΑΛΗΣΕΝΗΜΙΝΕΝΥΙΩ", "minuscule": "ἐλάλησεν ἡμῖν ἐν υἱῷ,", "translation": "spoke to us in a Son,"},
                    {"line_num": 5, "uncial": "ΟΣΩΝΑΠΑΥΓΑΣΜΑΤΗΣΔΟΞΗΣ", "minuscule": "ὃς ὢν ἀπαύγασμα τῆς δόξης", "translation": "who being the radiance of His glory"},
                    {"line_num": 6, "uncial": "ΚΑΙΧΑΡΑΚΤΗΡΤΗΣΥΠΟΣΤΑΣΕΩΣΑΥΤΟΥ", "minuscule": "καὶ χαρακτὴρ τῆς ὑποστάσεως αὐτοῦ,", "translation": "and exact impress of His substance."}
                ],
                "words_morph": [
                    {"word": "ΑΠΑΥΓΑΣΜΑ", "lemma": "ἀπαύγασμα", "pos": "Noun", "parse": "Nom Sg Neut", "gloss": "radiance, effulgence, beam of light"},
                    {"word": "ΔΟΞΗΣ", "lemma": "δόξα", "pos": "Noun", "parse": "Gen Sg Fem", "gloss": "glory, divine majesty"},
                    {"word": "ΧΑΡΑΚΤΗΡ", "lemma": "χαρακτήρ", "pos": "Noun", "parse": "Nom Sg Masc", "gloss": "exact impress, stamped image"},
                    {"word": "ΥΠΟΣΤΑΣΕΩΣ", "lemma": "ὑπόστασις", "pos": "Noun", "parse": "Gen Sg Fem", "gloss": "substance, real essence, hypostasis"}
                ]
            }
        ]
    },
    {
        "id": "papyrus_66",
        "name": "Papyrus 66 (Bodmer II)",
        "siglum": "𝔓66 / P.Bodmer II",
        "date": "c. 200 AD",
        "century": "c. 200 AD",
        "material": "Papyrus Codex",
        "language": "Greek",
        "repository": "Fondation Martin Bodmer",
        "city": "Cologny (Geneva)",
        "iiif_manifest": None,  # "iiif/manifests/cb-p-66.json" 404s (checked 2026-11-10); the real
        # manifest id for this item was not confirmed. viewer_url below (the constellations object page)
        # is confirmed real and working.
        "viewer_url": "https://bodmerlab.unige.ch/fr/constellations/papyri/barcode/1072205193",
        "description": "Remarkably preserved early codex containing nearly the entire Gospel of John. Exhibits careful scribal corrections indicating institutional scriptorium oversight around 200 AD.",
        "folios": [
            {
                "id": "p66_john1_14",
                "label": "Folio 2r (John 1:14 — 'The Word Became Flesh')",
                "passage": "John 1:14",
                "shelfmark": "P.Bodmer II, f. 2r",
                "image_url": "https://bodmerlab.unige.ch/fr/constellations/papyri/barcode/1072205193",
                "fallback_img": "/static/images/ms_p66_john1_14.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 200, "y": 280, "w": 460, "h": 260},
                "paleographical_notes": "Shows John 1:14: 'ΚΑΙ Ο ΛΟΓΟΣ ΣΑΡΞ ΕΓΕΝΕΤΟ ΚΑΙ ΕΣΚΗΝΩΣΕΝ ΕΝ ΗΜΙΝ' ('and the Word became flesh and tabernacled among us'). Displays Nomina Sacra and clear stichic rhythm.",
                "theological_bearing": "The definitive formulation of the Incarnation. God tabernacled in mortal flesh as the fulfillment of the Wilderness Shekinah.",
                "vulgate": "Et Verbum caro factum est, et habitavit in nobis: et vidimus gloriam ejus, gloriam quasi unigeniti a Patre plenum gratiae et veritatis.",
                "lines": [
                    {"line_num": 1, "uncial": "ΚΑΙΟΛΟΓΟΣΣΑΡΞΕΓΕΝΕΤΟ", "minuscule": "καὶ ὁ λόγος σὰρξ ἐγένετο", "translation": "And the Word became flesh"},
                    {"line_num": 2, "uncial": "ΚΑΙΕΣΚΗΝΩΣΕΝΕΝΗΜΙΝ", "minuscule": "καὶ ἐσκήνωσεν ἐν ἡμῖν,", "translation": "and tabernacled among us,"},
                    {"line_num": 3, "uncial": "ΚΑΙΕΘΕΑΣΑΜΕΘΑΤΗΝΔΟΞΑΝΑΥΤΟΥ", "minuscule": "καὶ ἐθεασάμεθα τὴν δόξαν αὐτοῦ,", "translation": "and we beheld His glory,"},
                    {"line_num": 4, "uncial": "ΔΟΞΑΝΩΣΜΟΝΟΓΕΝΟΥΣΠΑΡΑΠΡΣ", "minuscule": "δόξαν ὡς μονογενοῦς παρὰ πατρός,", "translation": "glory as of the only-begotten of the Father."}
                ],
                "words_morph": [
                    {"word": "ΕΣΚΗΝΩΣΕΝ", "lemma": "σκηνόω", "pos": "Verb", "parse": "Aorist Act Ind 3rd Sg", "gloss": "tabernacled, pitched tent, dwelt"},
                    {"word": "ΕΘΕΑΣΑΜΕΘΑ", "lemma": "θεάομαι", "pos": "Verb", "parse": "Aorist Mid Ind 1st Pl", "gloss": "we saw / contemplated with own eyes"},
                    {"word": "ΜΟΝΟΓΕΝΟΥΣ", "lemma": "μονογενής", "pos": "Adjective", "parse": "Gen Sg Masc", "gloss": "only-begotten, unique"}
                ]
            }
        ]
    },
    {
        "id": "papyrus_75",
        "name": "Papyrus 75 (Bodmer XIV–XV)",
        "siglum": "𝔓75 / P.Bodmer XIV-XV",
        "date": "c. 175–225 AD",
        "century": "Late 2nd / Early 3rd Century",
        "material": "Papyrus",
        "language": "Greek",
        "repository": "Biblioteca Apostolica Vaticana",
        "city": "Vatican City",
        "iiif_manifest": None,  # The old Bodmer shelfmark used here 404s on digi.vatlib.it (checked
        # 2026-11-10): the Vatican re-catalogued this item as "Pap.Hanna.1" after its 2007 donation, but
        # that shelfmark also doesn't resolve on DigiVatLib under this exact form, so no working IIIF
        # manifest URL is confirmed. viewer_url below is the Vatican Library's own real page for this
        # manuscript, confirmed by page title match ("Il Papiro Hanna 1").
        "viewer_url": "https://www.vaticanlibrary.va/en/multimedia/papiro-hanna-1.html",
        "description": "The earliest extant manuscript witness connecting the Gospel of Luke and the Gospel of John in a single bound codex. Proves that Luke and John circulated together by 200 AD with striking textual agreement with Codex Vaticanus (establishing the proto-Alexandrian text).",
        "folios": [
            {
                "id": "p75_luke_end_john_beg",
                "label": "Folio 47v / 48r (End of Luke & Incipit of John)",
                "passage": "Luke 24:53 / John 1:1",
                "shelfmark": "P.Bodmer XIV-XV, f. 47v",
                "image_url": "https://www.vaticanlibrary.va/en/multimedia/papiro-hanna-1.html",
                "fallback_img": "/static/images/ms_p75_luke_john.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 250, "y": 300, "w": 500, "h": 400},
                "paleographical_notes": "Monumental paleographical transition: Luke ends with subscriptio 'ΕΥΑΓΓΕΛΙΟΝ ΚΑΤΑ ΛΟΥΚΑΝ' and on the very same page without interruption begins 'ΕΥΑΓΓΕΛΙΟΝ ΚΑΤΑ ΙΩΑΝΝΗΝ'. Proves titles ('According to Luke', 'According to John') were standard before 200 AD.",
                "theological_bearing": "Pulverizes the myth that Gospel titles were late 3rd-century additions; proves authoritative apostolic attribution in the 2nd century.",
                "vulgate": "Et erant semper in templo, laudantes et benedicentes Deum. Amen. In principio erat Verbum, et Verbum erat apud Deum, et Deus erat Verbum.",
                "lines": [
                    {"line_num": 1, "uncial": "ΕΥΑΓΓΕΛΙΟΝΚΑΤΑΛΟΥΚΑΝ", "minuscule": "Εὐαγγέλιον κατὰ Λουκᾶν", "translation": "The Gospel According to Luke"},
                    {"line_num": 2, "uncial": "ΕΥΑΓΓΕΛΙΟΝΚΑΤΑΙΩΑΝΝΗΝ", "minuscule": "Εὐαγγέλιον κατὰ Ἰωάννην", "translation": "The Gospel According to John"},
                    {"line_num": 3, "uncial": "ΕΝΑΡΧΗΗΝΟΛΟΓΟΣ", "minuscule": "Ἐν ἀρχῇ ἦν ὁ λόγος", "translation": "In the beginning was the Word"}
                ],
                "words_morph": [
                    {"word": "ΕΥΑΓΓΕΛΙΟΝ", "lemma": "εὐαγγέλιον", "pos": "Noun", "parse": "Nom Sg Neut", "gloss": "Gospel, Good News"},
                    {"word": "ΚΑΤΑ", "lemma": "κατά", "pos": "Preposition", "parse": "with Acc", "gloss": "according to"},
                    {"word": "ΛΟΥΚΑΝ", "lemma": "Λουκᾶς", "pos": "Proper Noun", "parse": "Acc Sg Masc", "gloss": "Luke"},
                    {"word": "ΙΩΑΝΝΗΝ", "lemma": "Ἰωάννης", "pos": "Proper Noun", "parse": "Acc Sg Masc", "gloss": "John"}
                ]
            }
        ]
    },
    {
        "id": "papyrus_45",
        "name": "Papyrus 45 (Chester Beatty I)",
        "siglum": "𝔓45 / P.Chester Beatty I",
        "date": "c. 200–250 AD",
        "century": "3rd Century",
        "material": "Papyrus Codex",
        "language": "Greek",
        "repository": "Chester Beatty Library / Austrian National Library",
        "city": "Dublin / Vienna",
        "iiif_manifest": None,  # "iiif/BP_I/manifest.json" 404s (checked 2026-11-10); same situation as
        # Papyrus 46 above. viewer_url below (the object page itself) is confirmed real and working.
        "viewer_url": "https://viewer.cbl.ie/viewer/object/BP_I/",
        "description": "The earliest extant manuscript that contained all four Gospels and the Acts of the Apostles in a single codex. Written in an elegant, fluent documentary uncial hand.",
        "folios": [
            {
                "id": "p45_mark8",
                "label": "Folio 12r (Mark 8:27–30 — Peter's Confession)",
                "passage": "Mark 8:27–30",
                "shelfmark": "CBL BP I, f. 12r",
                "image_url": "https://viewer.cbl.ie/viewer/object/BP_I/",
                "fallback_img": "/static/images/ms_p45_mark8.jpg",
                "dimensions": {"width": 1200, "height": 1600},
                "coordinates": {"x": 220, "y": 260, "w": 460, "h": 280},
                "paleographical_notes": "Peter's declaration at Caesarea Philippi: 'ΣΥ ΕΙ Ο ΧΡΙΣΤΟΣ' ('You are the Christ'). Shows early text of Mark's central turning point.",
                "theological_bearing": "Apostolic identification of Jesus as the promised Davidic Messiah.",
                "vulgate": "Et interrogabat eos, dicens: Quem me dicunt esse homines? Qui responderunt illi, dicentes: Joannem Baptistam, alii Eliam, alii vero quasi unum de prophetis. Tunc dicit illis: Vos vero quem me esse dicitis? Respondens Petrus ait ei: Tu es Christus.",
                "lines": [
                    {"line_num": 1, "uncial": "ΤΙΝΑΜΕΛΕΓΟΥΣΙΝΟΙΑΝΘΡΩΠΟΙΕΙΝΑΙ", "minuscule": "Τίνα με λέγουσιν οἱ ἄνθρωποι εἶναι;", "translation": "Who do men say that I am?"},
                    {"line_num": 2, "uncial": "ΑΠΟΚΡΙΘΕΙΣΔΕΟΠΕΤΡΟΣΛΕΓΕΙΑΥΤΩ", "minuscule": "ἀποκριθεὶς δὲ ὁ Πέτρος λέγει αὐτῷ·", "translation": "And Peter answering says to Him:"},
                    {"line_num": 3, "uncial": "ΣΥΕΙΟΧΣ", "minuscule": "Σὺ εἶ ὁ Χριστός.", "translation": "You are the Christ."}
                ],
                "words_morph": [
                    {"word": "ΑΠΟΚΡΙΘΕΙΣ", "lemma": "ἀποκρίνομαι", "pos": "Verb (Participle)", "parse": "Aorist Pass Part Nom Sg Masc", "gloss": "having answered"},
                    {"word": "ΠΕΤΡΟΣ", "lemma": "Πέτρος", "pos": "Proper Noun", "parse": "Nom Sg Masc", "gloss": "Peter"},
                    {"word": "ΧΣ", "lemma": "Χριστός", "pos": "Noun (Nomen Sacrum)", "parse": "Nom Sg Masc (contracted Χ̅Σ̅)", "gloss": "the Christ / Anointed One"}
                ]
            }
        ]
    },

    # ── 3. Apostolic & Early Patristic Witnesses ─────────────────────────────
    {
        "id": "codex_hierosolymitanus",
        "name": "Codex Hierosolymitanus (Bryennios Codex)",
        "siglum": "H / MS Hagios Stauros 54",
        "date": "1056 AD (Preserving 1st-Cent Apostolic Texts)",
        "century": "11th Cent (Original c. 50–90 AD)",
        "material": "Parchment Codex",
        "language": "Greek",
        "repository": "Greek Orthodox Patriarchal Library of Jerusalem",
        "city": "Jerusalem",
        "iiif_manifest": None,  # No public IIIF manifest confirmed. The earlier value used
        # "library.patristic.org", a domain that does not exist (checked 2026-11-10). viewer_url below is
        # the real Library of Congress digitization of this exact codex (Panagios Taphos 54), found via
        # this manuscript's own Wikipedia citation and confirmed by page title match.
        "viewer_url": "https://www.loc.gov/resource/amedmonastery.00279389694-jo/?sp=1&st=list",
        "description": "Discovered in 1873 by Philotheos Bryennios in the Monastery of the Holy Sepulchre in Constantinople. The unique manuscript containing the complete Greek text of the Didache (The Teaching of the Twelve Apostles, c. 50–70 AD), alongside 1–2 Clement and the Epistle of Barnabas.",
        "folios": [
            {
                "id": "didache_7_14",
                "label": "Folios 76r–77v (Didache 7 & 14 — Trinitarian Baptism & Sunday Eucharist)",
                "passage": "Didache 7:1–3, 14:1–3",
                "shelfmark": "MS Hagios Stauros 54, f. 76r",
                # No specific-folio deep link confirmed; points to the real LOC digitization (viewer_url
                # above) rather than a fabricated image path.
                "image_url": "https://www.loc.gov/resource/amedmonastery.00279389694-jo/?sp=1&st=list",
                "fallback_img": "/static/images/ms_didache_bryennios.jpg",
                "dimensions": {"width": 1100, "height": 1500},
                "coordinates": {"x": 200, "y": 200, "w": 480, "h": 360},
                "paleographical_notes": "Explicit mandate for Trinitarian baptism: 'ΒΑΠΤΙΣΑΤΕ ΕΙΣ ΤΟ ΟΝΟΜΑ ΤΟΥ ΠΑΤΡΟΣ ΚΑΙ ΤΟΥ ΥΙΟΥ ΚΑΙ ΤΟΥ ΑΓΙΟΥ ΠΝΕΥΜΑΤΟΣ' and in Chapter 14 the celebration of the Sunday Eucharist as the 'ΘΥΣΙΑ' (pure sacrifice) prophesied by Malachi 1:11.",
                "theological_bearing": "1st-century witness proving that liturgical sacrifice, sacramental baptism, and the Lord's Day (Sunday) were normative apostolic practices.",
                "vulgate": "Baptizate in nomine Patris et Filii et Spiritus Sancti in aqua viva... In die dominica Domini autem congregati, frangite panem et eucharistiam celebrate, postquam confessi fueritis delicta vestra, ut munda sit hostia vestra.",
                "lines": [
                    {"line_num": 1, "uncial": "ΒΑΠΤΙΣΑΤΕΕΙΣΤΟΟΝΟΜΑΤΟΥΠΑΤΡΟΣ", "minuscule": "βαπτίσατε εἰς τὸ ὄνομα τοῦ πατρός", "translation": "baptize into the name of the Father"},
                    {"line_num": 2, "uncial": "ΚΑΙΤΟΥΥΙΟΥΚΑΙΤΟΥΑΓΙΟΥΠΝΕΥΜΑΤΟΣ", "minuscule": "καὶ τοῦ υἱοῦ καὶ τοῦ ἁγίου πνεύματος", "translation": "and of the Son and of the Holy Spirit"},
                    {"line_num": 3, "uncial": "ΚΑΤΑΚΥΡΙΑΚΗΝΔΕΚΥΡΙΟΥΣΥΝΑΧΘΕΝΤΕΣ", "minuscule": "Κατὰ κυριακὴν δὲ κυρίου συναχθέντες", "translation": "On the Lord’s Day of the Lord gather together"},
                    {"line_num": 4, "uncial": "ΚΛΑΣΑΤΕΑΡΤΟΝΚΑΙΕΥΧΑΡΙΣΤΗΣΑΤΕ", "minuscule": "κλάσατε ἄρτον καὶ εὐχαριστήσατε,", "translation": "break bread and offer the Eucharist"}
                ],
                "words_morph": [
                    {"word": "ΒΑΠΤΙΣΑΤΕ", "lemma": "βαπτίζω", "pos": "Verb", "parse": "Aorist Act Imperative 2nd Pl", "gloss": "baptize, immerse"},
                    {"word": "ΚΥΡΙΑΚΗΝ", "lemma": "κυριακός", "pos": "Adjective", "parse": "Acc Sg Fem", "gloss": "the Lord's (Day)"},
                    {"word": "ΕΥΧΑΡΙΣΤΗΣΑΤΕ", "lemma": "εὐχαριστέω", "pos": "Verb", "parse": "Aorist Act Imperative 2nd Pl", "gloss": "give thanks / celebrate Eucharist"},
                    {"word": "ΘΥΣΙΑ", "lemma": "θυσία", "pos": "Noun", "parse": "Nom Sg Fem", "gloss": "sacrifice, sacrificial offering"}
                ]
            }
        ]
    },
    {
        "id": "papyrus_oxyrhynchus_840",
        "name": "Papyrus Oxyrhynchus 840",
        "siglum": "P.Oxy. V 840",
        "date": "c. 4th Century (Preserving 2nd-Cent Text)",
        "century": "4th Century",
        "material": "Vellum Miniature Codex",
        "language": "Greek",
        "repository": "Bodleian Library",
        "city": "Oxford",
        "iiif_manifest": None,  # No confirmed direct IIIF manifest link; the earlier "p-oxy-840" slug
        # 404s (checked 2026-11-10). viewer_url below is Digital Bodleian's real object page for this
        # exact shelfmark, confirmed by page title match ("Bodleian Library MS. Gr. th. g. 11 (P)").
        "viewer_url": "https://digital.bodleian.ox.ac.uk/objects/b250073b-9368-4d24-a3ae-abfd819fe9e8/",
        "description": "A unique miniature vellum leaf (only 8.8 x 7.4 cm) written in microscopic Greek script. Records an otherwise unpreserved dialogue between Jesus and a Pharisaic Chief Priest named Levi in the Temple of Jerusalem concerning ritual immersion vs spiritual purification.",
        "folios": [
            {
                "id": "p_oxy_840_recto",
                "label": "Leaf Recto/Verso (Jesus and the Chief Priest Levi in the Temple)",
                "passage": "Agraphon / Temple Purity Dialogue",
                "shelfmark": "MS. Gr. th. g. 11 (P), fol. 1r",
                "image_url": "https://digital.bodleian.ox.ac.uk/objects/b250073b-9368-4d24-a3ae-abfd819fe9e8/",
                "fallback_img": "/static/images/ms_poxy_840.jpg",
                "dimensions": {"width": 900, "height": 1100},
                "coordinates": {"x": 120, "y": 100, "w": 400, "h": 450},
                "paleographical_notes": "Tiny miniature codex, 45 lines per side. Jesus rebukes Levi for trusting in pool water in which dogs and swine wallow, contrasting physical ritual bathing with inner divine regeneration.",
                "theological_bearing": "Corroborates Jesus's sharp critique of externalized Second Temple Pharisaic halakhah while showing authentic topographical knowledge of the Temple Mount (the Court of the Priests and pool of David).",
                "vulgate": "Vae vobis caeci non videntes: tu lavisti his fusis aquis... ego vero et discipuli mei, quos dicis non baptizatos, immersi sumus in aqua vitae aeternae.",
                "lines": [
                    {"line_num": 1, "uncial": "ΟΥΑΙΤΥΦΛΟΙΜΗΟΡΩΝΤΕΣ", "minuscule": "Οὐαὶ τυφλοὶ μὴ ὁρῶντες·", "translation": "Woe, you blind who do not see;"},
                    {"line_num": 2, "uncial": "ΣΥΕΛΟΥΣΩΤΟΥΤΟΙΣΤΟΙΣΧΕΟΜΕΝΟΙΣΥΔΑΣΙΝ", "minuscule": "σὺ ἐλούσω τούτοις τοῖς χεομένοις ὕδασιν", "translation": "you have washed in these poured-out waters,"},
                    {"line_num": 3, "uncial": "ΕΓΩΔΕΚΑΙΟΙΜΑΘΗΤΑΙΜΟΥ", "minuscule": "ἐγὼ δὲ καὶ οἱ μαθηταί μου", "translation": "but I and my disciples"},
                    {"line_num": 4, "uncial": "ΒΕΒΑΜΜΕΘΑΕΝΥΔΑΤΙΖΩΗΣΑΙΩΝΙΟΥ", "minuscule": "βεβάμμεθα ἐν ὕδατι ζωῆς αἰωνίου.", "translation": "have been immersed in water of eternal life."}
                ],
                "words_morph": [
                    {"word": "ΤΥΦΛΟΙ", "lemma": "τυφλός", "pos": "Adjective", "parse": "Voc Pl Masc", "gloss": "blind ones"},
                    {"word": "ΕΛΟΥΣΩ", "lemma": "λούω", "pos": "Verb", "parse": "Aorist Mid Ind 2nd Sg", "gloss": "you bathed yourself"},
                    {"word": "ΖΩΗΣ", "lemma": "ζωή", "pos": "Noun", "parse": "Gen Sg Fem", "gloss": "life (supernatural divine life)"}
                ]
            }
        ]
    },

    # ── 4. Second Temple & Dead Sea Scrolls (Biblical Baselines) ────────────
    {
        "id": "great_isaiah_scroll",
        "name": "The Great Isaiah Scroll",
        "siglum": "1QIsaᵃ / Cave 1",
        "date": "c. 125–100 BCE",
        "century": "2nd Century BCE (Hasmonean Era)",
        "material": "Leather / Animal Skin Parchment",
        "language": "Biblical Hebrew",
        "repository": "The Israel Museum (Shrine of the Book)",
        "city": "Jerusalem",
        "iiif_manifest": None,  # No working IIIF manifest confirmed at this path (checked 2026-11-10).
        # viewer_url below is confirmed real and working (page content matches exactly: "The Great
        # Isaiah Scroll (1QIsaa)... Qumran Cave 1... Accession number: HU 95.57/27").
        "viewer_url": "http://dss.collections.imj.org.il/isaiah",
        "description": "One of the original seven Dead Sea Scrolls discovered at Qumran Cave 1 in 1947. Measuring over 7 meters long across 54 columns, it contains the entire Book of Isaiah over 1,000 years older than the Masoretic Aleppo and Leningrad Codices. The foundational documentary proof that Isaiah 53 was not a post-Christian interpolation.",
        "folios": [
            {
                "id": "1qisa_col44_isa53",
                "label": "Column 44 (Isaiah 52:13–53:12 — The Suffering Servant)",
                "passage": "Isaiah 53:3–6, 10–12",
                "shelfmark": "1QIsaᵃ, Column XLIV",
                "image_url": "http://dss.collections.imj.org.il/isaiah",
                "fallback_img": "/static/images/ms_1qisa_col44.jpg",
                "dimensions": {"width": 1400, "height": 1800},
                "coordinates": {"x": 200, "y": 180, "w": 520, "h": 440},
                "paleographical_notes": "Hasmonean square Hebrew script with scribal corrections in margins. Note lines 6–10: 'אָכֵן חֳלָיֵנוּ הוּא נָשָׂא וּמַכְאֹבֵינוּ סְבָלָם... וְהוּא מְחֹלָל מִפְּשָׁעֵנוּ מְדֻכָּא מֵעֲו‍ֹנֹתֵינוּ'. Also contains the critical reading in 53:11: 'יִרְאֶה אוֹר' ('he shall see light'), confirming the Septuagint against the MT omission.",
                "theological_bearing": "The definitive pre-Christian baseline for vicarious atoning messianic suffering. Conclusively proves that the concept of a suffering, dying, and vindicated Servant of YHWH predates Jesus and was woven into Second Temple scripture.",
                "vulgate": "Despectum, et novissimum virorum, virum dolorum, et scientem infirmitatem... Vere languores nostros ipse tulit, et dolores nostros ipse portavit... Ipse autem vulneratus est propter iniquitates nostras, attritus est propter scelera nostra: disciplina pacis nostrae super eum, et livore ejus sanati sumus.",
                "lines": [
                    {"line_num": 1, "uncial": "נבזה וחדל אישים איש מכאבות וידוע חולי", "minuscule": "נִבְזֶה וַחֲדַל אִישִׁים אִישׁ מַכְאֹבוֹת וִידוּעַ חֹלִי", "translation": "Despised and rejected of men, a man of sorrows and acquainted with grief;"},
                    {"line_num": 2, "uncial": "אכן חלינו הוא נשא ומכאבינו סבלם", "minuscule": "אָכֵן חֳלָיֵנוּ הוּא נָשָׂא וּמַכְאֹבֵינוּ סְבָלָם", "translation": "Surely our griefs he has borne, and our sorrows he carried;"},
                    {"line_num": 3, "uncial": "והוא מחולל מפשעינו מדוכא מעונותינו", "minuscule": "וְהוּא מְחֹלָל מִפְּשָׁעֵנוּ מְדֻכָּא מֵעֲו‍ֹנֹתֵינוּ", "translation": "Yet he was pierced for our transgressions, crushed for our iniquities;"},
                    {"line_num": 4, "uncial": "מוסר שלומנו עליו ובחבורתו נרפא לנו", "minuscule": "מוּסַר שְׁלוֹמֵנוּ עָלָיו וּבַחֲבֻרָתוֹ נִרְפָּא לָנוּ", "translation": "the chastisement of our peace was upon him, and by his stripes we are healed."}
                ],
                "words_morph": [
                    {"word": "נִבְזֶה", "lemma": "בָּזָה", "pos": "Verb (Participle)", "parse": "Niphal Participle Masc Sg", "gloss": "despised, held in contempt"},
                    {"word": "חֳלָיֵנוּ", "lemma": "חֳלִי", "pos": "Noun", "parse": "Masc Pl with 1st Pl suffix", "gloss": "our sicknesses / infirmities"},
                    {"word": "מְחֹלָל", "lemma": "חָלַל", "pos": "Verb (Participle)", "parse": "Pual Participle Masc Sg", "gloss": "pierced through, fatally wounded"},
                    {"word": "מִפְּשָׁעֵנוּ", "lemma": "פֶּשַׁע", "pos": "Noun", "parse": "Masc Pl with prep מִן and 1st Pl suffix", "gloss": "from / because of our rebellions"}
                ]
            }
        ]
    },
    {
        "id": "scroll_4qmmt",
        "name": "4QMMT (Miqsat Ma'ase ha-Torah)",
        "siglum": "4QMMT / 4Q394–399",
        "date": "c. 150–50 BCE",
        "century": "1st–2nd Century BCE",
        "material": "Parchment Fragments",
        "language": "Late Second Temple Hebrew",
        "repository": "Israel Antiquities Authority (IAA)",
        "city": "Jerusalem",
        "iiif_manifest": None,  # "iiif/4Q394/manifest.json" 404s (checked 2026-11-10); no working IIIF
        # manifest path confirmed. viewer_url below (the official archive search page) is confirmed real.
        "viewer_url": "https://www.deadseascrolls.org.il/explore-the-archive/search#q=4Q394",
        "description": "Known as the Halakhic Letter from the Teacher of Righteousness to the High Priest in Jerusalem. Contains the exact Hebrew phrase 'מִקְצָת מַעֲשֵׂי הַתּוֹרָה' (*miqsat ma'ase ha-torah* = 'some works of the law'), which Paul directly translates into Greek as 'ἔργα νόμου' (*erga nomou*). Revolutionized Pauline scholarship (The New Perspective on Paul) by proving *erga nomou* refers to specific sectarian boundary markers (calendar, purity, circumcision), not generic moral good deeds.",
        "folios": [
            {
                "id": "4qmmt_section_c",
                "label": "4Q398 Frags. 14–17 (Epilogue — 'Reckoned to You as Righteousness')",
                "passage": "4QMMT Section C, lines 26–32",
                "shelfmark": "IAA 4Q398 (4QMMTᶠ), Frags. 14–17",
                "image_url": "https://www.deadseascrolls.org.il/explore-the-archive/search#q=4Q398",
                "fallback_img": "/static/images/ms_4qmmt_c.jpg",
                "dimensions": {"width": 1000, "height": 1300},
                "coordinates": {"x": 140, "y": 120, "w": 440, "h": 320},
                "paleographical_notes": "Late Hasmonaean/Early Herodian formal script. In line 31: 'ונחשבה לך לצדקה בעשותך הישר והטוב לפניו' ('and it shall be reckoned to you as righteousness when you do what is right and good before Him'). Paul directly polemicizes against this Qumran soteriological formulation in Galatians 2:16 and Romans 3:28.",
                "theological_bearing": "Forensic linguistic key bridging Qumran halakhah and Pauline theology. Proves that St. Paul's rejection of justification by 'works of the law' was an engagement with real Second Temple halakhic disputes over covenantal boundaries.",
                "vulgate": "Et nos quidem scripsimus tibi partem operum legis [miqsat ma'ase ha-torah]... et reputabitur tibi in iustitiam [ve-necheshevah lekha li-tsedaqah] cum feceris quod rectum et bonum est coram eo.",
                "lines": [
                    {"line_num": 1, "uncial": "ואף אנחנו כתבנו אליך מקצת מעשי התורה", "minuscule": "וְאַף אֲנַחְנוּ כָּתַבְנוּ אֵלֶיךָ מִקְצָת מַעֲשֵׂי הַתּוֹרָה", "translation": "And we have also written to you some of the works of the Law,"},
                    {"line_num": 2, "uncial": "שחשבנו לטוב לך ולעמך", "minuscule": "שֶׁחָשַׁבְנוּ לְטוֹב לְךָ וּלְעַמְּךָ", "translation": "which we consider to be for the good of you and of your people;"},
                    {"line_num": 3, "uncial": "ונחשבה לך לצדקה בעשותך הישר והטוב", "minuscule": "וְנֶחֶשְׁבָה לְךָ לִצְדָקָה בַּעֲשׂוֹתְךָ הַיָּשָׁר וְהַטּוֹב", "translation": "and it shall be reckoned to you as righteousness when you do what is right and good."}
                ],
                "words_morph": [
                    {"word": "מַעֲשֵׂי", "lemma": "מַעֲשֶׂה", "pos": "Noun", "parse": "Masc Pl Construct", "gloss": "works / deeds / halakhic observances"},
                    {"word": "הַתּוֹרָה", "lemma": "תּוֹרָה", "pos": "Noun", "parse": "Fem Sg with def art הַ", "gloss": "the Law / Torah"},
                    {"word": "וְנֶחֶשְׁבָה", "lemma": "חָשַׁב", "pos": "Verb", "parse": "Niphal Perfect 3rd Fem Sg with conj וְ", "gloss": "and it shall be reckoned / imputed"},
                    {"word": "לִצְדָקָה", "lemma": "צְדָקָה", "pos": "Noun", "parse": "Fem Sg with prep לְ", "gloss": "as righteousness"}
                ]
            }
        ]
    }
]

def list_manuscripts() -> List[Dict[str, Any]]:
    """Return summary list of all registered manuscripts."""
    result = []
    for ms in MANUSCRIPT_REGISTRY:
        result.append({
            "id": ms["id"],
            "name": ms["name"],
            "siglum": ms["siglum"],
            "date": ms["date"],
            "century": ms["century"],
            "material": ms["material"],
            "repository": ms["repository"],
            "city": ms["city"],
            "folio_count": len(ms.get("folios", [])),
            "description": ms.get("description", "")
        })
    return result

def get_manuscript(ms_id: str) -> Dict[str, Any]:
    """Retrieve full record for a specific manuscript."""
    for ms in MANUSCRIPT_REGISTRY:
        if ms["id"] == ms_id:
            return ms
    raise KeyError(f"Manuscript '{ms_id}' not found.")

def get_folio(ms_id: str, folio_id: str) -> Dict[str, Any]:
    """Retrieve detailed folio record with transcriptions and morphological alignment."""
    ms = get_manuscript(ms_id)
    for fol in ms.get("folios", []):
        if fol["id"] == folio_id:
            return {
                "manuscript_id": ms["id"],
                "manuscript_name": ms["name"],
                "siglum": ms["siglum"],
                "repository": ms["repository"],
                "iiif_manifest": ms.get("iiif_manifest"),
                "viewer_url": ms.get("viewer_url"),
                "folio": fol
            }
    raise KeyError(f"Folio '{folio_id}' not found in manuscript '{ms_id}'.")

def search_manuscripts(query: str) -> List[Dict[str, Any]]:
    """Search manuscripts, passages, and words for matching keywords."""
    q = query.strip().lower()
    matches = []
    for ms in MANUSCRIPT_REGISTRY:
        ms_matched = (q in ms["name"].lower() or 
                      q in ms["siglum"].lower() or 
                      q in ms["repository"].lower() or 
                      q in ms["description"].lower())
        
        for fol in ms.get("folios", []):
            fol_matched = (ms_matched or 
                           q in fol["passage"].lower() or 
                           q in fol["label"].lower() or 
                           q in fol["paleographical_notes"].lower() or
                           q in fol.get("theological_bearing", "").lower())
            
            # Check lines and words
            for line in fol.get("lines", []):
                if q in line.get("uncial", "").lower() or q in line.get("minuscule", "").lower() or q in line.get("translation", "").lower():
                    fol_matched = True
                    break
            
            if fol_matched:
                matches.append({
                    "manuscript_id": ms["id"],
                    "manuscript_name": ms["name"],
                    "siglum": ms["siglum"],
                    "folio_id": fol["id"],
                    "label": fol["label"],
                    "passage": fol["passage"],
                    "snippet": fol["paleographical_notes"][:150] + "..."
                })
    return matches

LOGOS_REF_MAP = {
    "Luke 1:1–4": "Bible.Lk1.1-4",
    "John 1:1–18": "Bible.Jn1.1-18",
    "John 21:24–25": "Bible.Jn21.24-25",
    "Matthew 16:18–19": "Bible.Mt16.18-19",
    "1 Clement 44:1–3": "AposFath.1Clem44.1-3",
    "1 Timothy 3:15–16": "Bible.1Tim3.15-16",
    "Acts 15:28–29": "Bible.Ac15.28-29",
    "Mark 16:14–15": "Bible.Mk16.14-15",
    "Romans 1:1–4": "Bible.Ro1.1-4",
    "John 18:37–38": "Bible.Jn18.37-38",
    "Hebrews 1:1–4": "Bible.Heb1.1-4",
    "John 1:14": "Bible.Jn1.14",
    "Luke 24:53 / John 1:1": "Bible.Lk24.53",
    "Mark 8:27–30": "Bible.Mk8.27-30",
    "Didache 7:1–3, 14:1–3": "AposFath.Did7.1",
    "Agraphon / Temple Purity Dialogue": "Agrapha.POxy840",
    "Isaiah 53:3–6, 10–12": "Bible.Is53.3-6",
    "4QMMT Section C, lines 26–32": "DSS.4QMMT",
}

def format_citation(ms_id: str, folio_id: str, style: str = "sbl") -> Dict[str, Any]:
    """Generate academic citations in SBL, Chicago, BibTeX, or Logos/Verbum format with IIIF deep links."""
    data = get_folio(ms_id, folio_id)
    ms = get_manuscript(ms_id)
    fol = data["folio"]
    
    passage = fol.get("passage", "")
    shelfmark = fol.get("shelfmark", "")
    siglum = ms.get("siglum", "")
    name = ms.get("name", "")
    date = ms.get("date", "")
    repo = ms.get("repository", "")
    lang = ms.get("language", "Greek")
    vulgate_text = fol.get("vulgate", "")
    theological = fol.get("theological_bearing", "")
    
    iiif_anchor = f"{ms.get('iiif_manifest', '')}#xywh={fol.get('coordinates', {}).get('x', 0)},{fol.get('coordinates', {}).get('y', 0)},{fol.get('coordinates', {}).get('w', 0)},{fol.get('coordinates', {}).get('h', 0)}"
    
    sbl_citation = f"{name} ({siglum}), {shelfmark} ({passage}), {date}. {repo}. Digital facsimile: {iiif_anchor}."
    chicago_citation = f"{name} ({siglum}), {shelfmark}. {repo}, {date}. Accessed via IIIF Image Services: {iiif_anchor}."
    
    bibtex = f"""@misc{{{ms_id}_{folio_id},
  title = {{{name} ({siglum}): {passage}}},
  author = {{{repo}}},
  howpublished = {{{shelfmark}, digital IIIF facsimile}},
  year = {{{date}}},
  url = {{{iiif_anchor}}}
}}"""

    # Logos / Verbum URI scheme & structured markdown export
    logos_ref = LOGOS_REF_MAP.get(passage, "Bible." + passage.replace(" ", "").replace(":", ".").replace("–", "-"))
    logos_uri = f"logosres:gntmorph;ref={logos_ref}"
    logos_web_link = f"https://ref.ly/logosres/gntmorph?ref={logos_ref}"
    verbum_vulgate_uri = f"logosres:vulgataclem;ref={logos_ref}"

    lines_formatted = "\n".join([f"L{ln['line_num']}: {ln.get('uncial','')} · {ln.get('minuscule','')} — \"{ln.get('translation','')}\"" for ln in fol.get("lines", [])])
    morph_formatted = "\n".join([f"• {w.get('word','')} ({w.get('lemma','')}) — {w.get('pos','')} {w.get('parse','')} : \"{w.get('gloss','')}\"" for w in fol.get("words_morph", [])])

    logos_verbum_copy = f"""# [[{passage} >> {logos_web_link}]]
**{name}** (`{siglum}`) — *{shelfmark}* ({date})
Repository: {repo} | Digital Facsimile (IIIF): {iiif_anchor}

## 📜 Original Text ({lang})
{lines_formatted}

## 📖 Latin Vulgate (Verbum Catholic Edition)
{vulgate_text}

## 🔍 Morphological Interlinear Analysis (Logos GNT / BDAG)
{morph_formatted}

## 🛡️ Theological & Historical Bearing
{theological}

## 🏛️ Academic Citation (SBL Format)
{sbl_citation}
Logos Resource URI: {logos_uri}
Verbum Vulgate URI: {verbum_vulgate_uri}"""

    return {
        "style": style,
        "sbl": sbl_citation,
        "chicago": chicago_citation,
        "bibtex": bibtex,
        "logos_verbum": logos_verbum_copy,
        "vulgate": vulgate_text,
        "logos_uri": logos_uri,
        "logos_link": logos_web_link,
        "verbum_uri": verbum_vulgate_uri,
        "iiif_anchor": iiif_anchor,
        "passage": passage,
        "shelfmark": shelfmark
    }
