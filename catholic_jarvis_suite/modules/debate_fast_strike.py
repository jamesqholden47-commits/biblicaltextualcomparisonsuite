"""
debate_fast_strike.py - One-Click Forensic Debate Snippet Generator for Discord & CatholicJarvis
Path: 09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/modules/debate_fast_strike.py

Generates 3-part Discord-ready markdown payloads:
  Part 1: Interlocutor Claim & Strategic Defeater
  Part 2: Primary Documentary Witness & 3D Manuscript Proof (IIIF link + transcription + gloss)
  Part 3: Patristic / Magisterial Counter-Strike & Dogmatic Collation (Logos/Verbum deep links)
"""

import re
from typing import Dict, Any, List, Optional

STRIKE_REGISTRY: List[Dict[str, Any]] = [
    {
        "id": "ehrman_anonymity",
        "keywords": ["ehrman", "anonymous", "anonymity", "luke", "pronoun", "eyewitness", "kamoi", "gospel author"],
        "title": "Bart Ehrman's 'Anonymous Gospels' & 'No First-Person Pronouns' Defeater",
        "opponent_claim": "The Gospels are completely anonymous folklore; none of the authors ever use the first-person singular pronoun 'I' or claim eyewitness transmission.",
        "ms_name": "Codex Vaticanus (B / 03 / Vat.gr.1209)",
        "shelfmark": "Vat.gr.1209, p. 1303, col. B (Luke 1:1–4)",
        "date": "c. 325–350 AD",
        "repo": "Biblioteca Apostolica Vaticana",
        "iiif_link": "https://digi.vatlib.it/iiif/MSS_Vat.gr.1209/manifest.json#xywh=380,140,420,260",
        "facsimile_ui": "http://localhost:8080/#library/manuscripts?ms=codex_vaticanus&folio=p1303_luke1",
        "logos_ref": "Bible.Lk1.1-4",
        "lines": [
            ("L5", "ΟΙΑΠΑΡΧΗΣΑΥΤΟΠΤΑΙΚΑΙ", "οἱ ἀπ’ ἀρχῆς αὐτόπται καὶ", "from the beginning EYEWITNESSES [autóptai]"),
            ("L7", "ΕΔΟΞΕΚΑΜΟΙΠΑΡΗΚΟΛΟΥΘΗΚΟΤΙ", "ἔδοξε κἀμοί, παρηκολουθηκότι", "it seemed good TO ME ALSO [kamoí = καὶ ἐμοί, 1st Sg Dat Pronoun]"),
            ("L8", "ΑΝΩΘΕΝΠΑΣΙΝΑΚΡΙΒΩΣ", "ἄνωθεν πᾶσιν ἀκριβῶς", "having investigated all things ACCURATELY [akribōs] from the beginning")
        ],
        "morphology": [
            ("ΚΑΜΟΙ", "κἀμοί", "Crasis of καὶ + ἐμοί", "First-person singular personal pronoun dative: 'to ME also'"),
            ("ΑΥΤΟΠΤΑΙ", "αὐτόπτης", "Noun Nom Pl Masc", "Eyewitnesses (direct seeing with own eyes)")
        ],
        "patristic_strike": "St. Irenaeus of Lyons (*Adversus Haereses* 3.1.1, c. 180 AD): 'Luke also, the companion of Paul, recorded in a book the Gospel preached by him.' The Clementine Vulgate affirms: *'visum est et mihi, assecuto a principio omnibus diligenter, ex ordine tibi scribere'* (Lk 1:3)."
    },
    {
        "id": "1clem_succession",
        "keywords": ["clem", "clement", "succession", "bishop", "episcopacy", "presbyter", "cyprian", "irenaeus", "order", "epinomē", "diadexontai"],
        "title": "Apostolic Succession & Episcopal Governance in 1 Clement 44 Defeater",
        "opponent_claim": "The early church was an egalitarian democracy of equal elders without succession; monarchical bishops and apostolic succession were 2nd/3rd-century hierarchical corruptions.",
        "ms_name": "Codex Alexandrinus (A / 02 / Royal MS 1 D VIII)",
        "shelfmark": "Royal MS 1 D VIII, f. 146v (1 Clement 44:1–3)",
        "date": "5th Century (Preserving 96 AD Apostolic Text)",
        "repo": "British Library, London",
        "iiif_link": "https://api.bl.uk/metadata/iiif/ark:/81055/vdc_100022441865.0x000001/manifest.json#xywh=100,200,600,400",
        "facsimile_ui": "http://localhost:8080/#library/manuscripts?ms=codex_alexandrinus&folio=f146v_1clem44",
        "logos_ref": "AposFath.1Clem44.1-3",
        "lines": [
            ("L3", "ΚΑΙΜΕΤΑΞΥΕΠΙΝΟΜΗΝΔΕΔΩΚΑΣΙΝ", "καὶ μεταξὺ ἐπινομὴν δεδώκασιν", "and afterward they gave a TESTAMENTARY CODICIL / legal directive [epinomē]"),
            ("L4", "ΟΠΩΣΕΑΝΚΟΙΜΗΘΩΣΙΝΔΙΑΔΕΞΩΝΤΑΙ", "ὅπως, ἐὰν κοιμηθῶσιν, διαδέξωνται", "so that, when they should fall asleep, others should SUCCEED [diadexōntai]"),
            ("L5", "ΕΤΕΡΟΙΔΕΔΟΚΙΜΑΣΜΕΝΟΙΑΝΔΡΕΣ", "ἕτεροι δεδοκιμασμένοι ἄνδρες", "other approved men to their ministry / office [leitourgia]")
        ],
        "morphology": [
            ("ΕΠΙΝΟΜΗΝ", "ἐπινομή", "Noun Acc Sg Fem", "Roman testamentary law: an official codicil to a last will and testament"),
            ("ΔΙΑΔΕΞΩΝΤΑΙ", "διαδέχομαι", "Verb Aorist Mid Subj 3rd Pl", "To receive through succession / take over an official inheritance")
        ],
        "patristic_strike": "Pope St. Clement of Rome writes in c. 96 AD (contemporary with the Apostle John). Succession was not left to spontaneous voting: the Apostles legally legislated succession via testamentary codicil (*epinomē*). Corroborated by St. Ignatius of Antioch (*Ad Smyrn.* 8.1, c. 110 AD): 'Wherever the bishop appears, there let the congregation be.'"
    },
    {
        "id": "4qmmt_works_of_law",
        "keywords": ["4qmmt", "works of law", "erga nomou", "faith alone", "sola fide", "justification", "qumran", "halakha"],
        "title": "Pauline 'Works of the Law' (4QMMT / Dead Sea Scrolls) Defeater",
        "opponent_claim": "When Paul condemns 'works of the law' (Romans 3:28, Galatians 2:16), he means any moral good works, charity, or obedience; justification is by faith alone with zero human cooperation.",
        "ms_name": "Dead Sea Scroll 4QMMT (4Q394–399 / Miqsat Ma'ase ha-Torah)",
        "shelfmark": "Qumran Cave 4, 4QMMT Section C, lines 26–32",
        "date": "c. 150–50 BCE (Pre-Christian Second Temple Hebrew)",
        "repo": "Israel Antiquities Authority / Shrine of the Book, Jerusalem",
        "iiif_link": "https://www.deadseascrolls.org.il/explore-the-archive/image/B-359204",
        "facsimile_ui": "http://localhost:8080/#library/manuscripts?ms=dss_4qmmt&folio=section_c_lines26_32",
        "logos_ref": "DSS.4QMMT",
        "lines": [
            ("L26", "וְאַף אֲנַחְנוּ כָּתַבְנוּ אֵלֶיךָ", "ve-af anachnu katavnu elekha", "And we have written to you"),
            ("L27", "מִקְצָת מַעֲשֵׂי הַתּוֹרָה", "miqsat ma'ase ha-torah", "some of the WORKS OF THE LAW [ma'ase ha-torah]"),
            ("L31", "וְנֶחֶשְׁבָה לְךָ לִצְדָקָה", "ve-necheshevah lekha li-tsedaqah", "and it shall be reckoned to you as righteousness")
        ],
        "morphology": [
            ("מַעֲשֵׂי הַתּוֹרָה", "ma'ase ha-torah", "Construct phrase", "Exact Hebrew linguistic equivalent of Greek ἔργα νόμου (erga nomou)"),
            ("לִצְדָקָה", "li-tsedaqah", "Preposition + Noun Fem Sg", "Unto righteousness (direct allusion to Gen 15:6 covenant reckoning)")
        ],
        "patristic_strike": "In 4QMMT, the 'works of the law' are an explicit inventory of ceremonial halakhic boundary markers: calendar, liquid streams, heifer ashes, and priest marriages. Paul's polemic against 'works of the law' in Romans and Galatians addresses the Mosaic ceremonial boundary markers dividing Jews from Gentiles, NOT Catholic charity or moral obedience. James 2:24: 'You see that a man is justified by works and not by faith alone.'"
    },
    {
        "id": "p52_dating",
        "keywords": ["p52", "john", "dating", "tubingen", "second century", "late date", "rylands"],
        "title": "Papyrus 52 & 1st-Century Johannine Composition Defeater",
        "opponent_claim": "The Gospel of John was composed late in the 2nd century (c. 160–170 AD) as a Hellenistic philosophical treatise with no connection to the historical Apostle John.",
        "ms_name": "Papyrus 52 (𝔓52 / P.Rylands Greek 457)",
        "shelfmark": "P.Rylands Greek 457 (John 18:31–33, 37–38)",
        "date": "c. 125–150 AD (Middle Egypt)",
        "repo": "John Rylands Library, Manchester, UK",
        "iiif_link": "https://luna.manchester.ac.uk/luna/servlet/iiif/m/ManchesterDev~93~3~22967~100254/manifest",
        "facsimile_ui": "http://localhost:8080/#library/manuscripts?ms=papyrus_52&folio=p52_recto_verso",
        "logos_ref": "Bible.Jn18.37-38",
        "lines": [
            ("Verso L2", "ΒΑΣΙΛΕΥΣ ΕΙΜΙ ΕΓΩ", "βασιλεύς εἰμι ἐγώ", "A king am I"),
            ("Verso L3", "ΕΙΣ ΤΟΥΤΟ ΓΕΓΕΝΝΗΜΑΙ", "εἰς τοῦτο γεγέννημαι", "For this cause I was born"),
            ("Verso L5", "ΤΙ ΕΣΤΙΝ ΑΛΗΘΕΙΑ", "τί ἐστιν ἀλήθεια;", "What is truth? (Pilate's question)")
        ],
        "morphology": [
            ("ΑΛΗΘΕΙΑ", "ἀλήθεια", "Noun Nom Sg Fem", "Truth, objective reality (core Johannine theme)")
        ],
        "patristic_strike": "In antiquity, manuscript propagation was slow. For a Greek codex composed in Ephesus to be copied, purchased, and transported to provincial Middle Egypt (Fayum/Oxyrhynchus) by c. 125 AD requires the autograph to have been written decades prior—squarely within the late 1st-century apostolic lifetime of St. John. The 19th-century Tübingen late-date thesis was physically shattered by an 8.9 x 6.0 cm scrap of papyrus."
    },
    {
        "id": "isaiah_53",
        "keywords": ["isaiah", "isaiah 53", "messiah", "suffering", "pierced", "qumran", "1qisa", "jewish"],
        "title": "Great Isaiah Scroll (1QIsaᵃ) Pre-Christian Suffering Servant Defeater",
        "opponent_claim": "Isaiah 53 was altered or forged by Christian scribes in the Middle Ages; ancient pre-Christian Jewish texts never described a pierced, dying, substitutionary Messiah.",
        "ms_name": "The Great Isaiah Scroll (1QIsaᵃ)",
        "shelfmark": "1QIsaᵃ, Column XLIV (Isaiah 52:13–53:12)",
        "date": "c. 125–100 BCE (Over a century BEFORE Christ)",
        "repo": "Israel Antiquities Authority / Shrine of the Book",
        "iiif_link": "https://www.deadseascrolls.org.il/explore-the-archive/image/B-279933",
        "facsimile_ui": "http://localhost:8080/#library/manuscripts?ms=great_isaiah_scroll&folio=col44_isaiah53",
        "logos_ref": "Bible.Is53.3-6",
        "lines": [
            ("Col XLIV L5", "וְהוּא מְחֹלָל מִפְּשָׁעֵנוּ", "ve-hu mecholal mi-pesha'enu", "He was PIERCED for our transgressions"),
            ("Col XLIV L6", "מְדֻכָּא מֵעֲו‍ֹנֹתֵינוּ", "medukka me-avonotenu", "CRUSHED for our iniquities"),
            ("Col XLIV L11", "יִרְאֶה אוֹר יִשְׂבָּע", "yir'eh or yisba", "He shall see LIGHT and be satisfied [Resurrection witness!]")
        ],
        "morphology": [
            ("מְחֹלָל", "chalal", "Polal Participle Masc Sg", "Pierced through, bored through (deadly wound)"),
            ("אוֹר", "or", "Noun Masc Sg", "LIGHT (preserved in 1QIsa and LXX, showing life after death)")
        ],
        "patristic_strike": "1QIsaᵃ sat sealed in a clay jar in Cave 1 for 2,000 years, completely untouched by medieval hands. Carbon-14 dating and paleography confirm c. 125–100 BCE. Every substitutionary, pierced detail of Christ’s Passion was locked in Hebrew leather before Jesus was born. St. Justin Martyr (*Dialogue with Trypho* 13) deployed this very prophecy against 2nd-century Jewish interlocutors."
    },
    {
        "id": "petros_petra",
        "keywords": ["peter", "petros", "petra", "rock", "matthew 16", "papacy", "primacy", "keys", "pebble"],
        "title": "Matthew 16:18 Petros/Petra & Papal Primacy Defeater",
        "opponent_claim": "Jesus called Peter 'Petros' (a tiny pebble) and the rock 'petra' (a giant boulder / Peter's faith), proving Jesus never made Peter the rock foundation of the Church.",
        "ms_name": "Codex Sinaiticus (א / 01) & Codex Vaticanus (B / 03)",
        "shelfmark": "Codex Sinaiticus, Quire 74, f. 10v (Matt 16:18–19)",
        "date": "c. 330–360 AD",
        "repo": "British Library / Vatican Library",
        "iiif_link": "https://www.codexsinaiticus.org/en/manuscript.aspx?book=33&chapter=16",
        "facsimile_ui": "http://localhost:8080/#library/manuscripts?ms=codex_sinaiticus&folio=quire74_matt16",
        "logos_ref": "Bible.Mt16.18-19",
        "lines": [
            ("Line 1", "ΣΥ ΕΙ ΠΕΤΡΟΣ", "σὺ εἶ Πέτρος", "You are Peter [Petros]"),
            ("Line 2", "ΚΑΙ ΕΠΙ ΤΑΥΤΗ ΤΗ ΠΕΤΡΑ", "καὶ ἐπὶ ταύτῃ τῇ πέτρᾳ", "and upon THIS ROCK [petra]"),
            ("Line 3", "ΟΙΚΟΔΟΜΗΣΩ ΜΟΥ ΤΗΝ ΕΚΚΛΗΣΙΑΝ", "οἰκοδομήσω μου τὴν ἐκκλησίαν", "I will build my Church")
        ],
        "morphology": [
            ("ΠΕΤΡΟΣ / ΠΕΤΡΑ", "Petros / petra", "Gender Inflection", "In Aramaic (Jesus's spoken language): 'Anta hu Kepha, ve'al hadey Kepha' (Kepha = Kepha, identical word). In Greek, a male cannot take a feminine name (*Petra*), requiring masculine termination *-os* (*Petros*). The demonstrative 'ταύτῃ' (this very) connects Peter directly to the rock."),
            ("ΚΛΕΙΔΑΣ", "κλείς", "Noun Acc Pl Fem", "Keys of the Kingdom (direct fulfillment of Isaiah 22:22 prime minister office)")
        ],
        "patristic_strike": "Tertullian (*De Praescriptione Haereticorum* 22): 'Was anything withheld from Peter, who was called \\'the rock on which the Church should be built\\'?' Council of Chalcedon (451 AD, Session II, DS 306): 'Peter has spoken through Leo!' St. Jerome (*Epistola 15 ad Damasum*): 'I speak with the successor of the fisherman and disciple of the cross. I am joined in communion with Your Beatitude, that is, with the chair of Peter. Upon this rock I know the Church is built.'"
    }
]


def match_strike(query: str) -> Optional[Dict[str, Any]]:
    """Match a query string to the best apologetics strike."""
    if not query:
        return None
    q = query.lower().strip()
    
    # 1. Direct ID match
    for s in STRIKE_REGISTRY:
        if s["id"] == q:
            return s
            
    # 2. Keyword scoring
    best_score = 0
    best_strike = None
    q_words = re.findall(r"\w+", q)
    for s in STRIKE_REGISTRY:
        score = 0
        for kw in s["keywords"]:
            if kw in q:
                score += 3
            for w in q_words:
                if w == kw or (len(w) >= 4 and w in kw):
                    score += 2
        if score > best_score:
            best_score = score
            best_strike = s
            
    if best_score >= 2:
        return best_strike
    return STRIKE_REGISTRY[0]  # default fallback


def build_discord_payload(strike: Dict[str, Any]) -> str:
    """Format strike into 3-part Discord-ready markdown payload."""
    lines_fmt = "\n".join([f"• **{ln[0]}**: `{ln[1]}` ({ln[2]})\n  ↳ *\"{ln[3]}\"*" for ln in strike["lines"]])
    morph_fmt = "\n".join([f"• **{m[0]}** (*{m[1]}* — {m[2]}): {m[3]}" for m in strike["morphology"]])
    
    ref_ly_link = f"https://ref.ly/logosres/{strike.get('logos_ref', 'Bible')}"
    logos_uri = f"logosres:gntmorph;ref={strike.get('logos_ref', 'Bible')}"
    
    payload = f"""> ⚔️ **DISCORD FAST-STRIKE DEFEATER: {strike['title'].upper()}**
> **Interlocutor Assertion:** *"{strike['opponent_claim']}"*

### 📜 PART 1: PRIMARY DOCUMENTARY WITNESS & 3D PALEOGRAPHY
**Artifact:** {strike['ms_name']}
**Shelfmark & Date:** `{strike['shelfmark']}` ({strike['date']})
**Repository:** {strike['repo']}
**Institutional IIIF Facsimile:** <{strike['iiif_link']}>
**CatholicJarvis 3D Viewer:** <{strike['facsimile_ui']}>

### 🔍 PART 2: UNCIAL / HEBREW TRANSCRIPTION & MORPHOLOGICAL PROOF
{lines_fmt}

**Philological Breakdown:**
{morph_fmt}

### 🏛️ PART 3: PATRISTIC COUNTER-STRIKE & MAGISTERIAL RECEPTION
{strike['patristic_strike']}

**Logos/Verbum Deep-Links:**
• Universal Web Gateway: <{ref_ly_link}>
• Desktop Protocol: `{logos_uri}`
*Generated by CatholicJarvis Paleography Suite — History Proves Catholicism.*"""
    return payload


def generate_strike(query: str) -> Dict[str, Any]:
    """Return JSON payload and raw Discord Markdown for the requested topic."""
    strike = match_strike(query)
    discord_md = build_discord_payload(strike)
    return {
        "strike": strike,
        "discord_markdown": discord_md
    }
