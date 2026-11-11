# -*- coding: utf-8 -*-
"""
Build Suite for Scripture Omitted Verses Forensic Explorer & Discord Card Generator
Generates:
1. omitted_verses_data.json
2. omitted_verses_explorer.html
"""

import json
import os
import sys

DATA = [
    {
        "id": "matt-17-21",
        "ref": "Matthew 17:21",
        "book": "Matthew",
        "chapter": 17,
        "verse": 21,
        "category": "FASTING",
        "is_canonical_16": True,
        "title": "Demonic Deliverance Through Prayer and Fasting",
        "summary": "Christ's declaration that a severe demonic kind cannot be cast out except through prayer and fasting. Completely excised from the continuous text of modern translations.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "However, this kind does not go out except by prayer and fasting.”",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "Howbeit this kind goeth not out but by prayer and fasting.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "But this kind is not cast out but by prayer and fasting.",
                "status": "INCLUDED (v. 20)",
                "badge": "Vulgate Tradition (Numbered v. 20)"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Hoc autem genus non eiicitur nisi per orationem et ieiunium.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts insert verse 21: But this kind does not go out except by prayer and fasting",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 21: But this kind does not go out except by prayer and fasting.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here words similar to Mark 9:29.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[But this kind does not go out except by prayer and fasting.]",
                "status": "BRACKETED",
                "footnote": "Early mss omit this verse.",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 21: But this kind never comes out except by prayer and fasting.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "τοῦτο δὲ τὸ γένος οὐκ ἐκπορεύεται εἰ μὴ ἐν προσευχῇ καὶ νηστείᾳ.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 20 to v. 22]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א*)", "Codex Vaticanus (B)", "33 (Queen of the Cursives)", "Curetonian Syriac (sy-c)", "Sahidic Coptic (cop-sa)"],
            "included_by": ["Codex Sinaiticus corrector (א2)", "Codex Ephraemi Rescriptus (C)", "Codex Bezae Cantabrigiensis (D)", "Codex Washingtonianus (W)", "Codex Koridethi (Θ)", "Codex Basilensis (E)", "Majority Byzantine Text (𝔐)", "Old Latin (it: a, b, c, d, ff2, q)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)", "Harklean Syriac (sy-h)"]
        },
        "patristic_citations": [
            "Origen (Commentary on Matthew 13.7, c. 245 AD) — discusses demonic deliverance and explicitly treats the fasting mandate.",
            "St. John Chrysostom (Homily 57 on Matthew, c. 390 AD) — 'He that fasteth is light and winged, and prayeth with wakefulness...'",
            "St. Hilary of Poitiers (Commentary on Matthew, 4th c.)",
            "St. Augustine (De Agone Christiano 32, c. 396 AD) — expounds on the union of bodily fasting with prayer against principalities."
        ],
        "textual_criticism": {
            "critical_theory": "Modern critical editors (Westcott-Hort, Bruce Metzger) assume Matthew 17:21 was an intentional or accidental harmonization by Byzantine scribes borrowing from Mark 9:29. Because the 4th-century uncials Sinaiticus and Vaticanus omit it, modern critical editions drop it.",
            "traditional_catholic_defense": "Attestation in the bilingual Western text (Codex Bezae D) and the Old Latin tradition demonstrates the verse existed across both Greek and Latin branches long before Sinaiticus and Vaticanus were penned. St. Jerome included it in the Latin Vulgate, which the Council of Trent declared authentic. Alexandrian ascetic scribes often practiced homeoteleuton or omission when texts overlapped with other Synoptic records.",
            "theological_impact": "Directly impacts the theology of asceticism, penance, and bodily mortification. In modern Protestant circles where fasting is minimized (as in the Discord screenshot: 'bro told me we dont need to fast because jesus already fasted'), the omission reinforces an antinomian or anti-ascetical stance by excising Christ's explicit rule for high-order spiritual warfare."
        }
    },
    {
        "id": "mark-9-29",
        "ref": "Mark 9:29",
        "book": "Mark",
        "chapter": 9,
        "verse": 29,
        "category": "FASTING",
        "is_canonical_16": False,
        "title": "Deliverance 'By Prayer and Fasting' vs 'By Prayer Alone'",
        "summary": "Parallel to Matthew 17:21. While the verse itself is retained in modern translations, modern critical Greek texts (NA28) excise 'and fasting' (καὶ νηστείᾳ), leaving only 'prayer'.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "So He said to them, “This kind can come out by nothing but prayer and fasting.”",
                "status": "INCLUDED",
                "badge": "Main Text (Prayer & Fasting)"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "And he said unto them, This kind can come forth by nothing, but by prayer and fasting.",
                "status": "INCLUDED",
                "badge": "Main Text (Prayer & Fasting)"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And he said to them: This kind can go out by nothing, but by prayer and fasting.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Et dixit illis: Hoc genus in nullo potest exire, nisi in oratione et ieiunio.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "And he said to them, “This kind cannot be driven out by anything but prayer.”",
                "status": "MODIFIED",
                "footnote": "Some manuscripts add: and fasting",
                "badge": "'Fasting' Excised from Text"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "Jesus replied, “This kind can be cast out only by prayer.”",
                "status": "MODIFIED",
                "footnote": "Some manuscripts add: and fasting.",
                "badge": "'Fasting' Excised from Text"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "He replied, “This kind can come out only by prayer.”",
                "status": "MODIFIED",
                "footnote": "Some manuscripts include: and fasting.",
                "badge": "'Fasting' Excised from Text"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "And He said to them, “This kind cannot come out by anything but prayer.”",
                "status": "MODIFIED",
                "footnote": "Early mss omit: and fasting",
                "badge": "'Fasting' Excised from Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "And he said to them, “This kind cannot be driven out by anything but prayer and fasting.”",
                "status": "INCLUDED",
                "badge": "Retains Fasting (Catholic Tradition)"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "καὶ εἶπεν αὐτοῖς, Τοῦτο τὸ γένος ἐν οὐδενὶ δύναται ἐξελθεῖν, εἰ μὴ ἐν προσευχῇ καὶ νηστείᾳ.",
                "status": "INCLUDED",
                "badge": "Includes καὶ νηστείᾳ"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "καὶ εἶπεν αὐτοῖς· τοῦτο τὸ γένος ἐν οὐδενὶ δύναται ἐξελθεῖν εἰ μὴ ἐν προσευχῇ.",
                "status": "MODIFIED",
                "badge": "Drops καὶ νηστείᾳ"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 45 (𝔓45)", "Codex Sinaiticus (א*)", "Codex Vaticanus (B)", "Minuscule 2427", "Old Latin k", "Georgian version"],
            "included_by": ["Codex Sinaiticus corrector (א2)", "Codex Alexandrinus (A)", "Codex Ephraemi (C)", "Codex Bezae (D)", "Codex Washingtonianus (W)", "Codex Koridethi (Θ)", "Majority Byzantine Text (𝔐)", "Old Latin (it: a, b, c, d, f, ff2, q)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Clement of Alexandria (c. 195 AD)",
            "Tertullian (De Ieiunio 17, c. 210 AD)",
            "St. Athanasius of Alexandria",
            "St. John Chrysostom, St. Jerome, St. Augustine"
        ],
        "textual_criticism": {
            "critical_theory": "Modern editors argue that 'and fasting' was an ascetical gloss added in the 2nd/3rd century by monastically-minded copyists.",
            "traditional_catholic_defense": "Overwhelmingly witnessed by Greek uncials (A, C, D, W, Θ), the Majority Text, Old Latin, the Clementine Latin Vulgate, and Syriac Peshitta. Notice the double-omission: modern Bibles completely delete Matt 17:21 AND delete 'and fasting' from Mark 9:29, completely removing Christ's teaching on fasting from demonic exorcism!",
            "theological_impact": "Completely removes bodily mortification from Christ's theology of deliverance in modern Protestant translations."
        }
    },
    {
        "id": "matt-18-11",
        "ref": "Matthew 18:11",
        "book": "Matthew",
        "chapter": 18,
        "verse": 11,
        "category": "CHRISTOLOGY",
        "is_canonical_16": True,
        "title": "The Mission of the Son of Man to Save the Lost",
        "summary": "Solemn declaration of Christ's salvific purpose directly introducing the Parable of the Lost Sheep. Omitted in modern critical editions.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "For the Son of Man has come to save that which was lost.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "For the Son of man is come to save that which was lost.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "For the Son of man is come to save that which was lost.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Venit enim Filius hominis salvare quod perierat.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 11: For the Son of Man came to save the lost",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 11: And the Son of Man came to save the lost.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "See Luke 19:10; some manuscripts include here: For the Son of Man came to save what was lost.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[For the Son of Man has come to save that which was lost.]",
                "status": "BRACKETED",
                "footnote": "Early mss omit this verse.",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 11.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ἦλθεν γὰρ ὁ υἱὸς τοῦ ἀνθρώπου σῶσαι τὸ ἀπολωλός.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 10 to v. 12]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Regius (L)", "Codex 33", "Sahidic Coptic", "Bohairic Coptic"],
            "included_by": ["Codex Bezae (D)", "Codex Washingtonianus (W)", "Codex Seidelianus I (G)", "Codex Cyprius (K)", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "St. John Chrysostom (Homily 60 on Matthew, 4th c.) — reads and comments on v. 11 as the bridge to the parable.",
            "St. Augustine (De Consensu Evangelistarum 2.70)",
            "St. Hilary of Poitiers (Comm. in Matt.)"
        ],
        "textual_criticism": {
            "critical_theory": "Critical editors label it an assimilation to Luke 19:10. Because early Alexandrian codices skip it, it was dropped in 19th-century reconstructions.",
            "traditional_catholic_defense": "The verse functions as the essential Christological theological preface to the Parable of the Lost Sheep in Matthew 18:12-14. Its preservation in the Western and Vulgate streams attests to its liturgical antiquity across the universal Church.",
            "theological_impact": "Affirms Christ's primary self-proclaimed divine mission of redemptive salvation."
        }
    },
    {
        "id": "matt-23-14",
        "ref": "Matthew 23:14",
        "book": "Matthew",
        "chapter": 23,
        "verse": 14,
        "category": "HELL_JUDGMENT",
        "is_canonical_16": True,
        "title": "Woe to Hypocrites Devouring Widows' Houses",
        "summary": "The condemnation of religious hypocrites who devour widows' property and make long prayers for a pretense. Omitted from modern critical Bibles, reducing the Eight Woes to Seven.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "Woe to you, scribes and Pharisees, hypocrites! For you devour widows’ houses, and for a pretense make long prayers. Therefore you will receive greater condemnation.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "Woe unto you, scribes and Pharisees, hypocrites! for ye devour widows' houses, and for a pretence make long prayer: therefore ye shall receive the greater damnation.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "Woe to you scribes and Pharisees, hypocrites: because you devour the houses of widows, praying long prayers. For this you shall receive the greater judgment.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Vae autem vobis scribae et Pharisaei hypocritae, quia comeditis domos viduarum, orationes longas facientes: propter hoc amplius accipietis iudicium.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 14: Woe to you, scribes and Pharisees, hypocrites! For you devour widows' houses and for a pretense make long prayers...",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 14: Woe to you, teachers of religious law and you Pharisees...",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here words similar to Mark 12:40 and Luke 20:47.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[Woe to you, scribes and Pharisees, hypocrites, because you devour widows' houses, and for a pretense you make long prayers; therefore you will receive greater condemnation.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 14.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "οὐαὶ δὲ ὑμῖν, γραμματεῖς καὶ Φαρισαῖοι, ὑποκριταί, ὅτι κατεσθίετε τὰς οἰκίας τῶν χηρῶν, καὶ προφάσει μακρὰ προσευχόμενοι· διὰ τοῦτο λήψεσθε περισσότερον κρίμα.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 13 to v. 15]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Bezae (D)", "Codex Regius (L)", "Codex Dublinensis (Z)", "33", "Sahidic Coptic"],
            "included_by": ["Codex Washingtonianus (W)", "Uncial 0102", "Uncial 0107", "Uncial 0233", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "St. John Chrysostom (Homilies on Matthew 73)",
            "St. Hilary of Poitiers (Comm. in Matt.)",
            "Latin Patristic lectionaries of the Roman Rite"
        ],
        "textual_criticism": {
            "critical_theory": "Viewed by critical editors as an insertion from Mark 12:40 and Luke 20:47.",
            "traditional_catholic_defense": "Matthew's gospel is structured symmetrically around eight distinct 'Woes' balancing the eight Beatitudes of the Sermon on the Mount (Matthew 5). Removing verse 14 breaks this intentional Matthean rhetorical octet.",
            "theological_impact": "Direct condemnation of spiritual hypocrisy, exploitation of vulnerable widows, and the eternal severity of divine judgment ('greater damnation')."
        }
    },
    {
        "id": "mark-7-16",
        "ref": "Mark 7:16",
        "book": "Mark",
        "chapter": 7,
        "verse": 16,
        "category": "ECCLESIAL",
        "is_canonical_16": True,
        "title": "Solemn Admonition: 'If Anyone Has Ears to Hear, Let Him Hear'",
        "summary": "Christ's authoritative prophetic injunction to heed His teaching on inward purity versus mere outward ritualism.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "If anyone has ears to hear, let him hear!”",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "If any man have ears to hear, let him hear.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "If any man have ears to hear, let him hear.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Si quis habet aures audiendi, audiat.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 16: If anyone has ears to hear, let him hear",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 16: Anyone with ears to hear should listen and understand.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here: If anyone has ears to hear, let them hear.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[If anyone has ears to hear, let him hear.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 16.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "εἴ τις ἔχει ὦτα ἀκούειν, ἀκουέτω.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 15 to v. 17]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Regius (L)", "Codex Sangallensis (Δ)", "0274", "28", "33", "Sahidic Coptic"],
            "included_by": ["Codex Alexandrinus (A)", "Codex Bezae (D)", "Codex Washingtonianus (W)", "Codex Koridethi (Θ)", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Ancient Western Lectionary traditions",
            "Latin and Syrian commentators on the Gospel of Mark"
        ],
        "textual_criticism": {
            "critical_theory": "Scribes allegedly inserted the formula from Mark 4:9, 4:23 to provide a customary ending to the public discourse.",
            "traditional_catholic_defense": "The solemn formula marks the transition between Christ's public teaching to the multitude (v. 14-15) and His private instruction to the disciples in the house (v. 17). Preserved in the venerable Vulgate.",
            "theological_impact": "Emphasizes the spiritual hearing required to grasp divine mysteries."
        }
    },
    {
        "id": "mark-9-44-46",
        "ref": "Mark 9:44 & 9:46",
        "book": "Mark",
        "chapter": 9,
        "verse": "44 & 46",
        "category": "HELL_JUDGMENT",
        "is_canonical_16": True,
        "title": "The Refrain of Eternal Damnation in Gehenna",
        "summary": "The solemn threefold repetition quoting Isaiah 66:24: 'Where their worm does not die and the fire is not quenched.' Both verses 44 and 46 are completely wiped out of modern translations.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "44 where ‘Their worm does not die And the fire is not quenched.’ ... 46 where ‘Their worm does not die And the fire is not quenched.’",
                "status": "INCLUDED",
                "badge": "Main Text (Threefold Warning)"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "44 Where their worm dieth not, and the fire is not quenched. ... 46 Where their worm dieth not, and the fire is not quenched.",
                "status": "INCLUDED",
                "badge": "Main Text (Threefold Warning)"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "43 Where the worm dieth not, and the fire is not extinguished. ... 45 Where their worm dieth not, and the fire is not extinguished.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition (Numbered vv. 43, 45)"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "ubi vermis eorum non moritur, et ignis non extinguitur.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Verses 44 and 46 are omitted, identical to verse 48: where their worm does not die and the fire is not quenched",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Verses 44 and 46 are omitted in the best ancient manuscripts.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here words similar to verse 48.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[44 where their worm does not die, and the fire is not quenched.] ... [46 where their worm does not die, and the fire is not quenched.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities add verse 44 and 46.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ὅπου ὁ σκώληξ αὐτῶν οὐ τελευτᾷ, καὶ τὸ πῦρ οὐ σβέννυται.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Verses 44 and 46 omitted; appears only once in verse 48]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Ephraemi (C)", "Codex Regius (L)", "Codex Washingtonianus (W)", "Codex Sangallensis (Δ)", "Codex Athous Laurensis (Ψ)", "28", "565", "892"],
            "included_by": ["Codex Alexandrinus (A)", "Codex Bezae (D)", "Codex Cyprius (K)", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Latin Patristic tradition, Roman Liturgical readings",
            "Clement of Alexandria and early catechetical warnings against the horrors of Gehenna"
        ],
        "textual_criticism": {
            "critical_theory": "Modern scholars argue that scribes repeated the refrain from verse 48 after each member of the triad (hand in v. 43, foot in v. 45, eye in v. 47).",
            "traditional_catholic_defense": "The threefold solemn liturgical chorus after each bodily member (hand, foot, eye) reflects the profound Hebrew poetic parallel structure of Jesus' preaching. Removing it dilutes the terrifying solemnity of Christ's warnings on eternal damnation.",
            "theological_impact": "Deals with the eternity and horrific reality of Hell (the undying worm and unquenched fire). Modern trends to soften eternal damnation find comfort in reducing the threefold warning to one."
        }
    },
    {
        "id": "mark-11-26",
        "ref": "Mark 11:26",
        "book": "Mark",
        "chapter": 11,
        "verse": 26,
        "category": "ECCLESIAL",
        "is_canonical_16": True,
        "title": "The Necessity of Forgiving Others to Receive Divine Forgiveness",
        "summary": "Christ's foundational warning that if you do not forgive others, neither will your Heavenly Father forgive your trespasses. Omitted from modern critical Bibles.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "But if you do not forgive, neither will your Father in heaven forgive your trespasses.”",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "But if ye do not forgive, neither will your Father which is in heaven forgive your trespasses.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "But if you will not forgive, neither will your Father that is in heaven, forgive you your sins.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Quod si vos non dimiseritis: nec Pater vester, qui in caelis est, dimittet vobis peccata vestra.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 26: But if you do not forgive, neither will your Father who is in heaven forgive your trespasses",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 26: But if you refuse to forgive, your Father in heaven will not forgive your sins.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here words similar to Matt 6:15.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[But if you do not forgive, neither will your Father who is in heaven forgive your transgressions.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 26.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "εἰ δὲ ὑμεῖς οὐκ ἀφίετε, οὐδὲ ὁ πατὴρ ὑμῶν ὁ ἐν τοῖς οὐρανοῖς ἀφήσει τὰ παραπτώματα ὑμῶν.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 25 to v. 27]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Regius (L)", "Codex Washingtonianus (W)", "Codex Sangallensis (Δ)", "Codex Athous Laurensis (Ψ)", "565", "892", "Sahidic", "Bohairic"],
            "included_by": ["Codex Alexandrinus (A)", "Codex Ephraemi (C)", "Codex Bezae (D)", "Codex Cyprius (K)", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "St. Cyprian of Carthage (Treatise on the Lord's Prayer, c. 252 AD)",
            "Latin Vulgate and Western Patristic consensus"
        ],
        "textual_criticism": {
            "critical_theory": "Regarded as a scribal assimilation to Matthew 6:15 inserted after Mark's teaching on mountain-moving faith and prayer.",
            "traditional_catholic_defense": "Christ repeated this crucial prerequisite for prayer throughout His ministry. Its presence in the Vulgate and Western text witnesses to its authentic liturgical usage.",
            "theological_impact": "Affirms that salvation and forgiveness have moral conditions; refutes unbiblical forms of unconditional security that detach faith from works of mercy."
        }
    },
    {
        "id": "mark-15-28",
        "ref": "Mark 15:28",
        "book": "Mark",
        "chapter": 15,
        "verse": 28,
        "category": "CHRISTOLOGY",
        "is_canonical_16": True,
        "title": "Messianic Fulfillment: Numbered with the Transgressors",
        "summary": "Explicit fulfillment of Isaiah 53:12 at the Crucifixion between two thieves. Dropped from modern Protestant versions.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "So the Scripture was fulfilled which says, “And He was numbered with the transgressors.”",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "And the scripture was fulfilled, which saith, And he was numbered with the transgressors.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And the scripture was fulfilled, which saith: And with the wicked he was reputed.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Et impleta est scriptura, quae dicit: Et cum iniquis reputatus est.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 28: And the Scripture was fulfilled that says, 'He was numbered with the transgressors'",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 28: And the Scripture was fulfilled that said, 'He was counted among the rebels.'",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here words similar to Luke 22:37.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[And the Scripture was fulfilled which says, 'And He was numbered with transgressors.']",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 28.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "καὶ ἐπληρώθη ἡ γραφὴ ἡ λέγουσα, Καὶ μετὰ ἀνόμων ἐλογίσθη.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 27 to v. 29]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Ephraemi (C)", "Codex Bezae (D)", "Codex Athous Laurensis (Ψ)", "k", "Sahidic"],
            "included_by": ["Codex Regius (L)", "Codex Washingtonianus (W)", "Codex Koridethi (Θ)", "Uncial 083", "Uncial 0250", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Early Christian passion homilies and Vulgate lectionaries"
        ],
        "textual_criticism": {
            "critical_theory": "Attributed by critical scholars to scribal harmonization from Luke 22:37.",
            "traditional_catholic_defense": "Directly links Christ's passion between two thieves to the Suffering Servant prophecy of Isaiah 53:12. Preserved in the Clementine Vulgate and Majority Text.",
            "theological_impact": "Strengthens Old Testament Messianic prophecy verification at the exact scene of the Crucifixion."
        }
    },
    {
        "id": "luke-17-36",
        "ref": "Luke 17:36",
        "book": "Luke",
        "chapter": 17,
        "verse": 36,
        "category": "ECCLESIAL",
        "is_canonical_16": True,
        "title": "Two Men in the Field: One Taken, One Left",
        "summary": "Eschatological judgment scene: two men in the field; one taken, the other left behind. A classic Western/Vulgate reading preserved in Catholic Bibles.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "Two men will be in the field: the one will be taken and the other left.”",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "Two men shall be in the field; the one shall be taken, and the other left.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "Two men shall be in the field: the one shall be taken, and the other shall be left.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition (St. Jerome)"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Duo erunt in agro: unus assumetur, et alter relinquetur.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 36: Two men will be in the field; one will be taken and the other left",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 36: Two men will be in the field; one will be taken and the other left.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here words similar to Matt 24:40.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[Two men will be in the field; one will be taken and the other will be left.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 36.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "δύο ἔσονται ἐν τῷ ἀγρῷ· ὁ εἷς παραληφθήσεται, καὶ ὁ ἕτερος ἀφεθήσεται.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 35 to v. 37]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 75 (𝔓75)", "Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Alexandrinus (A)", "Codex Washingtonianus (W)", "Majority Byzantine Text (𝔐)"],
            "included_by": ["Codex Bezae (D)", "Minuscule 1071", "Old Latin (it: a, b, c, d, e, ff2, q)", "Latin Vulgate (vg)", "Curetonian Syriac (sy-c)"]
        },
        "patristic_citations": [
            "St. Ambrose of Milan (Expositio in Lucam)",
            "St. Jerome (Vulgate translation, 384 AD)",
            "Latin lectionaries and liturgy"
        ],
        "textual_criticism": {
            "critical_theory": "Omitted by both Alexandrian and Byzantine text types; considered an early Western addition from Matthew 24:40.",
            "traditional_catholic_defense": "This is a quintessential Western-Vulgate locus. Its presence in Codex Bezae, Old Latin, and the Latin Vulgate shows that Western Christianity uniformly preserved this third example (bed in v. 34, mill in v. 35, field in v. 36).",
            "theological_impact": "Completes the triad of separation at Christ's sudden Second Coming: domestic (bed), agricultural industry (grinding mill), and outdoor labor (field)."
        }
    },
    {
        "id": "luke-23-17",
        "ref": "Luke 23:17",
        "book": "Luke",
        "chapter": 23,
        "verse": 17,
        "category": "ECCLESIAL",
        "is_canonical_16": True,
        "title": "The Obligation to Release a Prisoner at the Feast",
        "summary": "Historical note on Pilate's legal custom of releasing one prisoner to the people at Passover. Dropped from modern critical editions.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "(for it was necessary for him to release one to them at the feast).",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "(For of necessity he must release one unto them at the feast.)",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And of necessity he was to release unto them one upon the feast day.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Necesse autem habebat dimittere eis per diem festum unum.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 17: Now he was obliged to release one man to them at the festival",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 17: For it was necessary for him to release one prisoner for them at the festival.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here: Now it was necessary for him to release one prisoner to them at the festival.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[Now he was obliged to release to them at the feast one prisoner.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 17.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ἀνάγκην δὲ εἶχεν ἀπολύειν αὐτοῖς κατὰ ἑορτὴν ἕνα.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 16 to v. 18]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 75 (𝔓75)", "Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Alexandrinus (A)", "Codex Regius (L)", "Codex Borgianus (T)", "070", "Sahidic", "Bohairic"],
            "included_by": ["Codex Bezae (D)", "Codex Washingtonianus (W)", "Codex Koridethi (Θ)", "Codex Athous Laurensis (Ψ)", "Uncial 0250", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Western Patristic tradition, Latin passion lections"
        ],
        "textual_criticism": {
            "critical_theory": "Viewed by modern critics as an explanatory gloss imported from Matthew 27:15 or Mark 15:6.",
            "traditional_catholic_defense": "Explains why the crowd in verse 18 abruptly cried out: 'Away with this Man, and release to us Barabbas!' Without verse 17, the crowd's sudden demand for a release lacks narrative context in Luke.",
            "theological_impact": "Clarifies the legal context of the Passion narrative and the substitution of the guilty (Barabbas) for the Innocent Lamb of God."
        }
    },
    {
        "id": "john-5-3b-4",
        "ref": "John 5:3b-4",
        "book": "John",
        "chapter": 5,
        "verse": "3b-4",
        "category": "NARRATIVE",
        "is_canonical_16": True,
        "title": "The Angel Troubling the Waters at the Pool of Bethesda",
        "summary": "Describes the angel of the Lord descending to stir the waters of Bethesda, after which the first person stepped in was healed. Quoted by Tertullian in 200 AD, yet omitted in modern critical Bibles.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "...waiting for the moving of the water. 4 For an angel went down at a certain time into the pool and stirred up the water; then whoever stepped in first, after the stirring of the water, was made well of whatever disease he had.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "...waiting for the moving of the water. 4 For an angel went down at a certain season into the pool, and troubled the water: whosoever then first after the troubling of the water stepped in was made whole of whatsoever disease he had.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "...waiting for the moving of the water. 4 And an angel of the Lord descended at certain times into the pond, and the water was moved. And he that went down first into the pond after the motion of the water, was made whole of whatsoever infirmity he lay under.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition (St. Jerome)"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "...expectantium aquae motum. Angelus autem Domini secundum tempus descendebat in piscinam, et movebatur aqua. Et qui prior descendisset in piscinam post motionem aquae, sanus fiebat a quacumque detinebatur infirmitate.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts insert, wholly or in part, waiting for the moving of the water; for an angel of the Lord went down at certain seasons into the pool, and stirred up the water...",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add: waiting for a certain movement of the water, for an angel of the Lord came from time to time...",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here: and they waited for the moving of the waters. From time to time an angel of the Lord would come down...",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[waiting for the moving of the waters; 4 for an angel of the Lord went down at certain seasons into the pool and stirred up the water; whoever then first, after the stirring up of the water, stepped in was made well from whatever disease with which he was afflicted.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 4.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ἐκδεχομένων τὴν τοῦ ὕδατος κίνησιν. ἄγγελος γὰρ κατὰ καιρὸν κατέβαινεν ἐν τῇ κολυμβήθρᾳ, καὶ ἐτάρασσε τὸ ὕδωρ· ὁ οὖν πρῶτος ἐμβὰς μετὰ τὴν ταραχὴν τοῦ ὕδατος, ὑγιὴς ἐγίνετο, ᾧ δήποτε κατείχετο νοσήματι.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; text passes from 5:3a to 5:5]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 66 (𝔓66, c. 200 AD)", "Papyrus 75 (𝔓75)", "Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Ephraemi (C*)", "Codex Regius (L)", "Codex Washingtonianus (W)", "Uncial 0141", "33", "Sahidic", "Bohairic"],
            "included_by": ["Codex Alexandrinus (A)", "Codex Ephraemi corrector (C3)", "Codex Cyprius (K)", "Codex Campianus (M)", "Codex Sangallensis (Δ)", "Codex Koridethi (Θ)", "Uncial 078", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Tertullian (De Baptismo 5, c. 200 AD) — explicitly cites the angel troubling the pool of Bethesda as a prefiguration of the Holy Spirit in Christian Baptism!",
            "St. Ambrose of Milan (De Mysteriis 4.22; De Sacramentis 2.2)",
            "St. John Chrysostom (Homilies on the Gospel of John 36.1)",
            "St. Cyril of Alexandria (In Joannem)"
        ],
        "textual_criticism": {
            "critical_theory": "Modern editors claim it was an explanatory folk legend or scribal gloss inserted to explain the paralytic's complaint in verse 7 ('I have no man to put me into the pool when the water is stirred up').",
            "traditional_catholic_defense": "Tertullian's explicit citation around 200 AD proves this reading existed in the 2nd century, long before Sinaiticus and Vaticanus. Without verse 4, verse 7 ('when the water is stirred') is completely unintelligible. The Church Fathers unanimously saw the angel stirring Bethesda's waters as a sacramental type of Holy Baptism.",
            "theological_impact": "Affirms angelic ministry, miracles, and the sacramental typology of water and the Holy Spirit in regeneration."
        }
    },
    {
        "id": "acts-8-37",
        "ref": "Acts 8:37",
        "book": "Acts",
        "chapter": 8,
        "verse": 37,
        "category": "SACRAMENTS",
        "is_canonical_16": True,
        "title": "The Baptismal Confession of Faith in the Ethiopian Eunuch",
        "summary": "Philip's requirement for baptism ('If you believe with all your heart, you may') and the Eunuch's creed ('I believe that Jesus Christ is the Son of God'). Quoted by Irenaeus in 180 AD, yet completely missing from modern translations.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "Then Philip said, “If you believe with all your heart, you may.” And he answered and said, “I believe that Jesus Christ is the Son of God.”",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "And Philip said, If thou believest with all thine heart, thou mayest. And he answered and said, I believe that Jesus Christ is the Son of God.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And Philip said: If thou believest with all thy heart, thou mayest. And he answering, said: I believe that Jesus Christ is the Son of God.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition (St. Jerome)"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Dixit autem Philippus: Si credis ex toto corde, licet. Et respondens ait: Credo Filium Dei esse Jesum Christum.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add all or part of verse 37: And Philip said, 'If you believe with all your heart, you may.' And he replied, 'I believe that Jesus Christ is the Son of God.'",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 37: 'You can,' Philip told him, 'if you believe with all your heart.' And the eunuch replied, 'I believe that Jesus Christ is the Son of God.'",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here: Philip said, 'If you believe with all your heart, you may.' The eunuch answered, 'I believe that Jesus Christ is the Son of God.'",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[And Philip said, 'If you believe with all your heart, you may.' And he answered and said, 'I believe that Jesus Christ is the Son of God.']",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 37.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "εἶπεν δὲ ὁ Φίλιππος, Εἰ πιστεύεις ἐξ ὅλης τῆς καρδίας, ἔξεστιν. ἀποκριθεὶς δὲ εἶπεν, Πιστεύω τὸν υἱὸν τοῦ θεοῦ εἶναι τὸν Ἰησοῦν Χριστόν.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 36 to v. 38]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 45 (𝔓45)", "Papyrus 74 (𝔓74)", "Codex Sinaiticus (א)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Codex Ephraemi (C)", "Majority Byzantine Text (𝔐, which marks with obelus or omits)"],
            "included_by": ["Codex Laudianus (E, 6th c. bilingual Greek/Latin)", "Minuscule 323", "Minuscule 453", "Minuscule 945", "Minuscule 1739mg", "Minuscule 1891", "Old Latin (it: e, l, m, r)", "Latin Vulgate (vg)", "Armenian"]
        },
        "patristic_citations": [
            "St. Irenaeus of Lyons (Against Heresies 3.12.8, c. 180 AD) — explicitly quotes: '[The eunuch] said: I believe the Son of God to be Jesus Christ; and was immediately baptized.'",
            "St. Cyprian of Carthage (Testimonies Against the Jews 3.43, c. 250 AD)",
            "St. Augustine of Hippo (De Fide et Operibus 9.14)",
            "St. Pacian of Barcelona (4th c.)",
            "Venerable Bede (Exposition on Acts, 8th c.)"
        ],
        "textual_criticism": {
            "critical_theory": "Modern editors claim this was a baptismal confession formula derived from early ecclesiastical liturgy and written into the margin of Acts.",
            "traditional_catholic_defense": "Irenaeus quotes this verse in 180 AD—nearly two centuries before Codex Vaticanus and Sinaiticus were transcribed. This delivers an absolute defeater to the claim that verse 37 is a late medieval corruption. It was preserved in the Latin Vulgate and the ancient Western liturgical tradition.",
            "theological_impact": "Foundational text for the Sacramental theology of Baptism: requires explicit orthodox Christological confession of faith before the reception of the Sacrament."
        }
    },
    {
        "id": "acts-15-34",
        "ref": "Acts 15:34",
        "book": "Acts",
        "chapter": 15,
        "verse": 34,
        "category": "ECCLESIAL",
        "is_canonical_16": True,
        "title": "Silas's Decision to Remain at Antioch",
        "summary": "Explains why Silas was still present in Antioch in verse 40 when Paul chose him as companion, after Judas and Silas had been sent back to Jerusalem in verse 33.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "However, it seemed good to Silas to remain there.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "Notwithstanding it pleased Silas to abide there still.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "But it seemed good unto Silas to remain there: and Judas alone returned to Jerusalem.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Visum est autem Silæ ibi remanere: Judas autem solus abiit Jerusalem.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 34: But it seemed good to Silas to remain there",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 34: But it seemed good to Silas to stay there.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here: But Silas decided to remain there.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[But it seemed good to Silas to remain there.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 34.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ἔδοξε δὲ τῷ Σίλᾳ ἐπιμεῖναι αὐτοῦ.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 33 to v. 35]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 74 (𝔓74)", "Codex Sinaiticus (א)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Codex Laudianus (E)", "Majority Byzantine Text (𝔐)"],
            "included_by": ["Codex Bezae (D)", "Codex Ephraemi (C)", "Codex Koridethi (Θ)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Western Patristic tradition, Latin commentaries on Acts"
        ],
        "textual_criticism": {
            "critical_theory": "Critical commentators claim verse 34 was invented by a scribe who noticed the narrative contradiction between verse 33 (Silas sent away) and verse 40 (Paul choosing Silas in Antioch).",
            "traditional_catholic_defense": "Preserves the historical continuity of St. Luke's record. Without verse 34, Silas disappears to Jerusalem in verse 33 and magically reappears in Antioch in verse 40. Preserved in the Western and Latin Vulgate streams.",
            "theological_impact": "Maintains narrative and historical coherence in the early apostolic mission."
        }
    },
    {
        "id": "acts-24-6b-8a",
        "ref": "Acts 24:6b-8a (or 24:7)",
        "book": "Acts",
        "chapter": 24,
        "verse": "6b-8a",
        "category": "ECCLESIAL",
        "is_canonical_16": True,
        "title": "Lysias's Armed Intervention Rescuing Paul from the Sanhedrin",
        "summary": "Tertullus's testimony that the Tribune Lysias intervened with great violence to rescue Paul, commanding his accusers to appear before Felix. Verse 7 omitted in modern texts.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "...and wanted to judge him according to our law. 7 But the commander Lysias came by and with great violence took him out of our hands, 8 commanding his accusers to come to you.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "...and would have judged according to our law. 7 But the chief captain Lysias came upon us, and with great violence took him away out of our hands, 8 Commanding his accusers to come unto thee...",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "...and according to our law we would have judged him. 7 But Lysias the tribune coming upon us, with great violence took him away out of our hands, 8 Commanding his accusers to come to thee...",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "...et secundum legem nostram voluimus judicare. Superveniens autem tribunus Lysias, cum vi magna eripuit eum de manibus nostris, Jubens accusatores ejus venire ad te...",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add and we would have judged him according to our law. But the chief captain Lysias came and with great violence took him out of our hands, commanding his accusers to come before you",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add: We would have judged him by our law, but Lysias the commander arrived and with great force took him from us...",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here words similar to verses 6b–8a.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[and we wanted to judge him according to our own Law. 7 But Lysias the commander came along, and with much force took him out of our hands, 8 ordering his accusers to come before you.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 7.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "καὶ κατὰ τὸν ἡμέτερον νόμον ἠθελήσαμεν κρῖναι· παρελθὼν δὲ Λυσίας ὁ χιλίαρχος μετὰ πολλῆς βίας ἐκ τῶν χειρῶν ἡμῶν ἀπήγαγεν, κελεύσας τοὺς κατηγόρους αὐτοῦ ἔρχεσθαι ἐπὶ σέ...",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Verse 7 omitted from critical text; text flows from 6a into 8b]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 74 (𝔓74)", "Codex Sinaiticus (א)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Majority Byzantine Text (𝔐)"],
            "included_by": ["Codex Bezae (D)", "Codex Laudianus (E)", "Minuscules 33, 88, 181, 436", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)", "Harklean Syriac (sy-h)"]
        },
        "patristic_citations": [
            "Western and Latin Patristic commentaries, Vulgate lections"
        ],
        "textual_criticism": {
            "critical_theory": "Regarded as a Western expansion attempting to round out the legal rhetoric of the lawyer Tertullus.",
            "traditional_catholic_defense": "Explains why the Roman Governor Felix had jurisdiction over Paul's trial. Preserved intact in the Clementine Vulgate and ancient Latin witnesses.",
            "theological_impact": "Affirms God's providential use of civil and military authorities to preserve the lives of His apostles."
        }
    },
    {
        "id": "acts-28-29",
        "ref": "Acts 28:29",
        "book": "Acts",
        "chapter": 28,
        "verse": 29,
        "category": "ECCLESIAL",
        "is_canonical_16": True,
        "title": "The Jewish Departure and Internal Dispute in Rome",
        "summary": "Records the reaction of the Roman Jewish leaders departing Paul's residence having intense debate among themselves following his citation of Isaiah 6:9-10.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "And when he had said these words, the Jews departed and had a great dispute among themselves.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "And when he had said these words, the Jews departed, and had great reasoning among themselves.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And when he had said these things, the Jews went out from him, having much reasoning among themselves.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Et cum haec dixisset, exierunt ab eo Judaei, multam habentes inter se quaestionem.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 29: And when he had said these words, the Jews departed, having much dispute among themselves",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 29: And when he had said these words, the Jews departed, having much dispute among themselves.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here: And when he had said these words, the Jews departed, having great dispute among themselves.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[When he had spoken these words, the Jews departed, having a great dispute among themselves.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 29.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "καὶ ταῦτα αὐτοῦ εἰπόντος, ἀπῆλθον οἱ Ἰουδαῖοι, πολλὴν ἔχοντες ἐν ἑαυτοῖς συζήτησιν.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 28 to v. 30]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 74 (𝔓74)", "Codex Sinaiticus (א)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Codex Laudianus (E)", "Uncial 048", "Majority Byzantine Text (𝔐)"],
            "included_by": ["Codex Ephraemi (C)", "Minuscule 104", "Minuscule 181", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "St. John Chrysostom (Homilies on Acts 55)",
            "Latin Vulgate and Western lectionary tradition"
        ],
        "textual_criticism": {
            "critical_theory": "Modern critics view this as a scribal transition marker smoothing the conclusion of Paul's speech.",
            "traditional_catholic_defense": "Witnesses to the immediate impact of the Gospel in Rome, showing that Paul's preaching produced internal debate among the Jews of the capital. Attested in St. Jerome's Vulgate.",
            "theological_impact": "Demonstrates the Gospel acting as a two-edged sword dividing belief from unbelief."
        }
    },
    {
        "id": "rom-16-24",
        "ref": "Romans 16:24",
        "book": "Romans",
        "chapter": 16,
        "verse": 24,
        "category": "ECCLESIAL",
        "is_canonical_16": True,
        "title": "The Pauline Apostolic Benediction",
        "summary": "St. Paul's customary closing apostolic blessing: 'The grace of our Lord Jesus Christ be with you all. Amen.' Omitted from modern critical translations.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "The grace of our Lord Jesus Christ be with you all. Amen.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "The grace of our Lord Jesus Christ be with you all. Amen.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "The grace of our Lord Jesus Christ be with you all. Amen.",
                "status": "INCLUDED",
                "badge": "Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Gratia Domini nostri Jesu Christi cum omnibus vobis. Amen.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts insert verse 24: The grace of our Lord Jesus Christ be with you all. Amen.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add verse 24: May the grace of our Lord Jesus Christ be with you all. Amen.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here: May the grace of our Lord Jesus Christ be with you all. Amen.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[The grace of our Lord Jesus Christ be with you all. Amen.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities insert verse 24.",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ἡ χάρις τοῦ κυρίου ἡμῶν Ἰησοῦ Χριστοῦ μετὰ πάντων ὑμῶν. ἀμήν.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Omitted from critical text; numbering jumps from v. 23 to v. 25]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 46 (𝔓46, c. 200 AD)", "Papyrus 61 (𝔓61)", "Codex Sinaiticus (א)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Codex Ephraemi (C)", "Codex 81"],
            "included_by": ["Codex Claromontanus (D)", "Codex Boernerianus (G)", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Latin Patristic commentators (Ambrosiaster, Pelagius, Jerome)",
            "Universal Western Liturgical benediction"
        ],
        "textual_criticism": {
            "critical_theory": "Modern critics assume verse 24 is a scribal duplicate of Romans 16:20b placed after Tertius's personal greetings in verses 21-23.",
            "traditional_catholic_defense": "Standard epistolary benediction in St. Paul's authentic autograph after dictating his final greetings. Sealed in the Latin Vulgate and Byzantine Majority text.",
            "theological_impact": "Liturgical benediction conveying sanctifying grace to the faithful."
        }
    },
    {
        "id": "matt-12-47",
        "ref": "Matthew 12:47",
        "book": "Matthew",
        "chapter": 12,
        "verse": 47,
        "category": "MARIAN",
        "is_canonical_16": False,
        "title": "Christ's Mother and Brethren Standing Outside",
        "summary": "Someone reporting to Christ that His mother and brethren are standing outside desiring to speak. Bracketed or footnoted in critical editions; critical for Marian apologetics.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "Then one said to Him, “Look, Your mother and Your brothers are standing outside, seeking to speak with You.”",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "Then one said unto him, Behold, thy mother and thy brethren stand without, desiring to speak with thee.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And one said unto him: Behold thy mother and thy brethren stand without, seeking thee.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Dixit autem ei quidam: Ecce mater tua, et fratres tui foris stant quaerentes te.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "Someone told him, “Your mother and your brothers are standing outside, asking to speak to you.”",
                "status": "FOOTNOTED",
                "footnote": "Some manuscripts omit verse 47",
                "badge": "Footnoted (Early Mss Omit)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "Someone told him, “Your mother and your brothers are outside, and they want to speak to you.”",
                "status": "FOOTNOTED",
                "footnote": "This verse is omitted in some early manuscripts.",
                "badge": "Footnoted"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "Someone told him, “Your mother and brothers are standing outside, wanting to speak to you.”",
                "status": "FOOTNOTED",
                "footnote": "Some manuscripts omit verse 47.",
                "badge": "Footnoted"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[Someone said to Him, “Look, Your mother and Your brothers are standing outside seeking to speak to You.”]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "Someone told him, “Your mother and your brothers are standing outside, asking to speak to you.”",
                "status": "INCLUDED",
                "badge": "Included in Text"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "εἶπεν δέ τις αὐτῷ, Ἰδοὺ ἡ μήτηρ σου καὶ οἱ ἀδελφοί σου ἔξω ἑστήκασιν, ζητοῦντές σοι λαλῆσαι.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[εἶπεν δέ τις αὐτῷ· ἰδοὺ ἡ μήτηρ σου καὶ οἱ ἀδελφοί σου ἔξω ἑστήκασιν ζητοῦντές σοι λαλῆσαι.]",
                "status": "BRACKETED",
                "badge": "Bracketed Critical"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Regius (L)", "Codex Sangallensis (Γ)", "Minuscule 579", "Minuscule 1010", "Sahidic", "Bohairic"],
            "included_by": ["Codex Ephraemi (C)", "Codex Bezae (D)", "Codex Cyprius (K)", "Codex Washingtonianus (W)", "Codex Koridethi (Θ)", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "St. Jerome (Against Helvidius on the Perpetual Virginity of the Blessed Virgin Mary, c. 383 AD)",
            "St. John Chrysostom, St. Hilary of Poitiers"
        ],
        "textual_criticism": {
            "critical_theory": "Scribes may have skipped it due to homoeoteleuton (vv. 46 and 47 both end in λαλῆσαι), or alternatively imported it from Mark 3:32 and Luke 8:20.",
            "traditional_catholic_defense": "Preserved in the Latin Vulgate and majority tradition. Essential for Marian apologetics: St. Jerome refuted Helvidius by proving the biblical meaning of 'brethren' (*adelphoi*) as cousins or close kinsmen, preserving the dogma of the Perpetual Virginity of Mary.",
            "theological_impact": "Defends the Perpetual Virginity of the Mother of God."
        }
    },
    {
        "id": "luke-9-55-56",
        "ref": "Luke 9:55b-56a",
        "book": "Luke",
        "chapter": 9,
        "verse": "55b-56a",
        "category": "CHRISTOLOGY",
        "is_canonical_16": False,
        "title": "Christ's Rebuke of the Sons of Thunder: 'Ye Know Not What Manner of Spirit Ye Are Of'",
        "summary": "Jesus rebukes James and John for wanting to call down fire on the Samaritans: 'Ye know not what manner of spirit ye are of. For the Son of man is not come to destroy men's lives, but to save them.' Excised in modern texts.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "...and said, “You do not know what manner of spirit you are of. 56 For the Son of Man did not come to destroy men’s lives but to save them.” And they went to another village.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "...and said, Ye know not what manner of spirit ye are of. 56 For the Son of man is come not to destroy men's lives, but to save them. And they went to another village.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "...saying: You know not of what spirit you are. 56 The Son of man came not to destroy souls, but to save. And they went into another town.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "...dicens: Nescitis cuius spiritus estis. 56 Filius hominis non venit animas perdere, sed salvare. Et abierunt in aliud castellum.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "But he turned and rebuked them. 56 And they went on to another village.",
                "status": "OMITTED",
                "footnote": "Some manuscripts add and he said, “You do not know what manner of spirit you are of; for the Son of Man came not to destroy people's lives but to save them”",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "But Jesus turned and rebuked them. 56 So they went on to another village.",
                "status": "OMITTED",
                "footnote": "Some manuscripts add: And he said, “You don’t know what kind of spirit you belong to. For the Son of Man didn’t come to destroy men’s lives, but to save them.”",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "But Jesus turned and rebuked them. 56 Then he and his disciples went to another village.",
                "status": "OMITTED",
                "footnote": "Some manuscripts include here: And he said, “You do not know what kind of spirit you are of, for the Son of Man did not come to destroy men’s lives, but to save them.”",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "But He turned and rebuked them, [and said, “You do not know what kind of spirit you are of; 56 for the Son of Man did not come to destroy men's lives, but to save them.”] And they went on to another village.",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "But he turned and rebuked them. 56 And they went on to another village.",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities add: and he said, “You do not know what manner of spirit you are of...”",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "καὶ εἶπεν, Οὐκ οἴδατε οἵου πνεύματός ἐστε ὑμεῖς· 56 ὁ γὰρ υἱὸς τοῦ ἀνθρώπου οὐκ ἦλθεν ψυχὰς ἀνθρώπων ἀπολέσαι, ἀλλὰ σῶσαι.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Words omitted; text flows directly from ἐπετίμησεν αὐτοῖς into καὶ ἐπορεύθησαν]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 45 (𝔓45)", "Papyrus 75 (𝔓75)", "Codex Sinaiticus (א)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Codex Ephraemi (C)", "Codex Regius (L)", "Codex Washingtonianus (W)", "Sahidic", "Bohairic"],
            "included_by": ["Codex Bezae (D)", "Codex Cyprius (K)", "Codex Koridethi (Θ)", "Codex Petropolitanus (Π)", "Families 1 and 13", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Marcion (c. 140 AD)",
            "Tertullian (Against Marcion 4.29, c. 208 AD)",
            "St. Cyprian of Carthage, St. Ambrose of Milan, St. Augustine, St. Jerome"
        ],
        "textual_criticism": {
            "critical_theory": "Modern critics believe this was an early Western gloss expanding Jesus' rebuke of James and John with theological material borrowed from Luke 19:10 and John 3:17.",
            "traditional_catholic_defense": "Tertullian attests to this reading in the early 3rd century. It reveals Christ's rejection of revolutionary physical violence and defines the merciful spirit of the New Covenant.",
            "theological_impact": "Affirms the spirit of Evangelical meekness and divine mercy; refutes violent fanaticism."
        }
    },
    {
        "id": "luke-22-43-44",
        "ref": "Luke 22:43-44",
        "book": "Luke",
        "chapter": 22,
        "verse": "43-44",
        "category": "CHRISTOLOGY",
        "is_canonical_16": False,
        "title": "The Agony in Gethsemane: The Strengthening Angel and the Bloody Sweat",
        "summary": "The angel appearing to strengthen Christ, and His sweat becoming like great drops of blood falling to the ground. Quoted by Justin Martyr in 155 AD, yet omitted in Vaticanus and Alexandrinus.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "Then an angel appeared to Him from heaven, strengthening Him. 44 And being in agony, He prayed more earnestly. Then His sweat became like great drops of blood falling down to the ground.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "And there appeared an angel unto him from heaven, strengthening him. 44 And being in an agony he prayed more earnestly: and his sweat was as it were great drops of blood falling down to the ground.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And there appeared to him an angel from heaven, strengthening him. And being in an agony, he prayed the longer. 44 And his sweat became as drops of blood, trickling down upon the ground.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Apparuit autem illi angelus de caelo, confortans eum. Et factus in agonia, prolixius orabat. 44 Et factus est sudor eius sicut guttae sanguinis decurrentis in terram.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "[[43 And there appeared to him an angel from heaven, strengthening him. 44 And being in agony he prayed more earnestly; and his sweat became like great drops of blood falling down to the ground.]]",
                "status": "BRACKETED",
                "footnote": "Double brackets indicate verses not in the earliest manuscripts.",
                "badge": "Double-Bracketed Critical"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "[43 Then an angel from heaven appeared and strengthened him. 44 He prayed more fervently, and he was in such agony of spirit that his sweat fell to the ground like great drops of blood.]",
                "status": "BRACKETED",
                "footnote": "Verses 43 and 44 are not included in many early manuscripts.",
                "badge": "Bracketed in Text"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "[43 An angel from heaven appeared to him and strengthened him. 44 And being in agony, he prayed more earnestly, and his sweat was like drops of blood falling to the ground.]",
                "status": "BRACKETED",
                "footnote": "Many early manuscripts omit verses 43 and 44.",
                "badge": "Bracketed in Text"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[43 Now an angel from heaven appeared to Him, strengthening Him. 44 And being in agony He was praying very fervently; and His sweat became like drops of blood, falling down upon the ground.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "And there appeared to him an angel from heaven, strengthening him. 44 And being in an agony he prayed more earnestly; and his sweat became like great drops of blood falling down upon the ground.",
                "status": "INCLUDED",
                "badge": "Catholic Canon"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ὤφθη δὲ αὐτῷ ἄγγελος ἀπ’ οὐρανοῦ ἐνισχύων αὐτόν. 44 καὶ γενόμενος ἐν ἀγωνίᾳ ἐκτενέστερον προσηύχετο· ἐγένετο δὲ ὁ ἱδρὼς αὐτοῦ ὡσεὶ θρόμβοι αἵματος καταβαίνοντες ἐπὶ τὴν γῆν.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[[ὤφθη δὲ αὐτῷ ἄγγελος ἀπ’ οὐρανοῦ ἐνισχύων αὐτόν...]]",
                "status": "BRACKETED",
                "badge": "Double-Bracketed Critical"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 69 (𝔓69)", "Papyrus 75 (𝔓75)", "Codex Sinaiticus corrector (אa)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Codex Washingtonianus (W)", "Sahidic Coptic"],
            "included_by": ["Codex Sinaiticus original hand (א*)", "Codex Bezae (D)", "Codex Ephraemi corrector (C2)", "Codex Koridethi (Θ)", "Uncial 0171", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)", "Curetonian Syriac"]
        },
        "patristic_citations": [
            "St. Justin Martyr (Dialogue with Trypho 103, c. 155 AD — explicitly quotes the bloody sweat!)",
            "St. Irenaeus of Lyons (Against Heresies 3.22.2, c. 180 AD)",
            "St. Hippolytus of Rome (c. 220 AD)",
            "St. Epiphanius of Salamis (Ancoratus 31, c. 374 AD — explicitly notes that orthodox scribes removed the verses out of fear of Arian heretics!)",
            "St. John Chrysostom, St. Jerome, St. Augustine"
        ],
        "textual_criticism": {
            "critical_theory": "Modern critics claim it was an early floating tradition inserted into Luke to combat Docetic Christologies.",
            "traditional_catholic_defense": "Justin Martyr and Irenaeus quote it in the 2nd century! St. Epiphanius solves the textual mystery: orthodox copyists suppressed the verses because pagans (Celsus) and Arians mocked Christ's fear and agony to attack His divine power! The passage is essential to Catholic orthodoxy, proving Christ's true human soul and human will in Gethsemane.",
            "theological_impact": "Affirms Christ's real human nature, human agony, and the First Sorrowful Mystery of the Holy Rosary."
        }
    },
    {
        "id": "luke-23-34a",
        "ref": "Luke 23:34a",
        "book": "Luke",
        "chapter": 23,
        "verse": "34a",
        "category": "CHRISTOLOGY",
        "is_canonical_16": False,
        "title": "The First Word from the Cross: 'Father, Forgive Them, For They Know Not What They Do'",
        "summary": "Christ's supreme sacerdotal intercession on the Cross. Bracketed and questioned in modern critical texts due to absence in Vaticanus and P75.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "Then Jesus said, “Father, forgive them, for they do not know what they do.”",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "Then said Jesus, Father, forgive them; for they know not what they do.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And Jesus said: Father, forgive them, for they know not what they do.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Jesus autem dicebat: Pater, dimitte illis: non enim sciunt quid faciunt.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "And Jesus said, “Father, forgive them, for they know not what they do.”",
                "status": "FOOTNOTED",
                "footnote": "Some manuscripts omit: And Jesus said, 'Father, forgive them, for they know not what they do'",
                "badge": "Footnoted (Early Mss Omit)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "Jesus said, “Father, forgive them, for they don’t know what they are doing.”",
                "status": "FOOTNOTED",
                "footnote": "This sentence is not included in many early manuscripts.",
                "badge": "Footnoted"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "Jesus said, “Father, forgive them, for they do not know what they are doing.”",
                "status": "FOOTNOTED",
                "footnote": "Some manuscripts do not have: Jesus said, 'Father, forgive them, for they do not know what they are doing.'",
                "badge": "Footnoted"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[But Jesus was saying, “Father, forgive them; for they do not know what they are doing.”]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "And Jesus said, “Father, forgive them; for they know not what they do.”",
                "status": "INCLUDED",
                "badge": "Catholic Canon"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ὁ δὲ Ἰησοῦς ἔλεγεν, Πάτερ, ἄφες αὐτοῖς· οὐ γὰρ οἴδασιν τί ποιοῦσιν.",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[[ὁ δὲ Ἰησοῦς ἔλεγεν· πάτερ, ἄφες αὐτοῖς, οὐ γὰρ οἴδασιν τί ποιοῦσιν.]]",
                "status": "BRACKETED",
                "badge": "Double-Bracketed Critical"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 75 (𝔓75)", "Codex Sinaiticus corrector (אa)", "Codex Vaticanus (B)", "Codex Bezae (D*)", "Codex Washingtonianus (W)", "Codex Koridethi (Θ)", "Sahidic Coptic"],
            "included_by": ["Codex Sinaiticus original hand (א*)", "Codex Alexandrinus (A)", "Codex Ephraemi (C)", "Codex Bezae corrector (D2)", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)"]
        },
        "patristic_citations": [
            "Hegesippus (apud Eusebius HE 2.23, 2nd c.)",
            "St. Irenaeus of Lyons (Against Heresies 3.16.9, c. 180 AD)",
            "Origen, St. John Chrysostom, St. Augustine, St. Jerome"
        ],
        "textual_criticism": {
            "critical_theory": "Critical editors assume the prayer was an early Western or Palestinian oral tradition added into Luke.",
            "traditional_catholic_defense": "Scribes in the 2nd century during the bitter Jewish-Roman wars omitted Christ's prayer because they felt the destruction of Jerusalem in 70 AD proved that the Jewish authorities were NOT forgiven! Its presence in the original hand of Sinaiticus, Old Latin, and the Vulgate affirms its authenticity.",
            "theological_impact": "The supreme revelation of Divine Mercy and the high-priestly intercession of Christ upon the Altar of the Cross."
        }
    },
    {
        "id": "col-1-14",
        "ref": "Colossians 1:14",
        "book": "Colossians",
        "chapter": 1,
        "verse": 14,
        "category": "CHRISTOLOGY",
        "is_canonical_16": False,
        "title": "Redemption 'Through His Blood' Excised in Critical Texts",
        "summary": "KJV/NKJV reads: 'In whom we have redemption through His blood, the forgiveness of sins.' Modern critical translations excise 'through His blood'.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "in whom we have redemption through His blood, the forgiveness of sins.",
                "status": "INCLUDED",
                "badge": "Includes 'Through His Blood'"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "In whom we have redemption through his blood, even the forgiveness of sins:",
                "status": "INCLUDED",
                "badge": "Includes 'Through His Blood'"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "In whom we have redemption through his blood, the remission of sins;",
                "status": "INCLUDED",
                "badge": "Latin Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "in quo habemus redemptionem per sanguinem eius, remissionem peccatorum:",
                "status": "INCLUDED",
                "badge": "Clementine Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "in whom we have redemption, the forgiveness of sins.",
                "status": "OMITTED",
                "footnote": "Greek text omits: through his blood",
                "badge": "'Through His Blood' Excised"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "who purchased our freedom and forgave our sins.",
                "status": "OMITTED",
                "badge": "'Through His Blood' Excised"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "in whom we have redemption, the forgiveness of sins.",
                "status": "OMITTED",
                "badge": "'Through His Blood' Excised"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "in whom we have redemption, the forgiveness of sins.",
                "status": "OMITTED",
                "badge": "'Through His Blood' Excised"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "in whom we have redemption, the forgiveness of sins.",
                "status": "OMITTED",
                "badge": "Critical Text Basis"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Stephanus 1550",
                "text": "ἐν ᾧ ἔχομεν τὴν ἀπολύτρωσιν διὰ τοῦ αἵματος αὐτοῦ, τὴν ἄφεσιν τῶν ἁμαρτιῶν·",
                "status": "INCLUDED",
                "badge": "Includes διὰ τοῦ αἵματος αὐτοῦ"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "ἐν ᾧ ἔχομεν τὴν ἀπολύτρωσιν, τὴν ἄφεσιν τῶν ἁμαρτιῶν·",
                "status": "OMITTED",
                "badge": "Excises Blood Reference"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 46 (𝔓46, c. 200 AD)", "Codex Sinaiticus (א)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Codex Ephraemi (C)", "Codex Claromontanus (D*)", "Codex Boernerianus (G)", "Majority Byzantine Text (𝔐)"],
            "included_by": ["Minuscule 623", "Minuscule 43", "Old Latin (it: dem, div)", "Clementine Vulgate", "Harklean Syriac margin"]
        },
        "patristic_citations": [
            "Ephesians 1:7 parallel witness",
            "Clementine Latin Vulgate"
        ],
        "textual_criticism": {
            "critical_theory": "Critical scholars and Byzantine specialists agree that 'through his blood' was imported by scribes from the parallel passage in Ephesians 1:7.",
            "traditional_catholic_defense": "The Clementine Vulgate maintained the phrase to emphasize the sacrificial efficacy of Christ's physical Blood shedding on Calvary against early Gnostic spiritualizing tendencies.",
            "theological_impact": "Affirms the reality of propitiation and atonement exclusively through the Precious Blood of Christ."
        }
    },
    {
        "id": "1john-5-7-8",
        "ref": "1 John 5:7-8",
        "book": "1 John",
        "chapter": 5,
        "verse": "7-8",
        "category": "TRINITY",
        "is_canonical_16": False,
        "title": "The Comma Johanneum: The Heavenly Witnesses to the Holy Trinity",
        "summary": "The supreme Trinitarian witness: 'For there are three that bear record in heaven, the Father, the Word, and the Holy Ghost: and these three are one.' Found in the Latin Vulgate and TR, omitted in modern critical editions.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "For there are three that bear witness in heaven: the Father, the Word, and the Holy Spirit; and these three are one. 8 And there are three that bear witness on earth: the Spirit, the water, and the blood; and these three agree as one.",
                "status": "INCLUDED",
                "badge": "Main Text (Full Trinitarian Formula)"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "For there are three that bear record in heaven, the Father, the Word, and the Holy Ghost: and these three are one. 8 And there are three that bear witness in earth, the Spirit, and the water, and the blood: and these three agree in one.",
                "status": "INCLUDED",
                "badge": "Main Text (Full Trinitarian Formula)"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And there are three who give testimony in heaven, the Father, the Word, and the Holy Ghost. And these three are one. 8 And there are three that give testimony on earth: the spirit, and the water, and the blood: and these three are one.",
                "status": "INCLUDED",
                "badge": "Latin Vulgate Tradition"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Quoniam tres sunt, qui testimonium dant in caelo: Pater, Verbum, et Spiritus Sanctus: et hi tres unum sunt. 8 Et tres sunt, qui testimonium dant in terra: spiritus, et aqua, et sanguis: et hi tres unum sunt.",
                "status": "INCLUDED",
                "badge": "Clementine Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "For there are three that testify: 8 the Spirit and the water and the blood; and these three agree.",
                "status": "OMITTED",
                "footnote": "A few late manuscripts add: in heaven, the Father, the Word, and the Holy Spirit, and these three are one. And there are three that testify on earth...",
                "badge": "Heavenly Witnesses Omitted"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "So we have these three witnesses— 8 the Spirit, the water, and the blood—and all three agree.",
                "status": "OMITTED",
                "footnote": "A few very late manuscripts add: in heaven, the Father, the Word, and the Holy Spirit, and these three are one. And there are three that testify on earth...",
                "badge": "Heavenly Witnesses Omitted"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "For there are three that testify: 8 the Spirit, the water and the blood; and the three are in agreement.",
                "status": "OMITTED",
                "footnote": "Late manuscripts of the Vulgate testify in heaven: the Father, the Word and the Holy Spirit...",
                "badge": "Heavenly Witnesses Omitted"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "For there are three that testify: 8 the Spirit and the water and the blood; and the three are in agreement.",
                "status": "OMITTED",
                "footnote": "Late mss add in heaven, the Father, the Word, and the Holy Spirit, and these three are one...",
                "badge": "Heavenly Witnesses Omitted"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "And the Spirit is the witness, because the Spirit is the truth. 8 There are three witnesses, the Spirit, the water, and the blood; and these three agree.",
                "status": "FOOTNOTED",
                "footnote": "Other ancient authorities add: in heaven, the Father, the Word, and the Holy Spirit...",
                "badge": "Footnoted"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Stephanus 1550",
                "text": "ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες ἐν τῷ οὐρανῷ, ὁ Πατήρ, ὁ Λόγος, καὶ τὸ Ἅγιον Πνεῦμα· καὶ οὗτοι οἱ τρεῖς ἕν εἰσιν. 8 καὶ τρεῖς εἰσιν οἱ μαρτυροῦντες ἐν τῇ γῇ...",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες, 8 τὸ πνεῦμα καὶ τὸ ὕδωρ καὶ τὸ αἷμα, καὶ οἱ τρεῖς εἰς τὸ ἕν εἰσιν.",
                "status": "OMITTED",
                "badge": "Critical Text Excises Comma"
            }
        },
        "manuscripts": {
            "omitted_by": ["Almost all ancient Greek manuscripts (א, A, B, C, P, Ψ, 048, 33, Majority Greek 𝔐)", "Early Syriac", "Coptic", "Ethiopian"],
            "included_by": ["Greek Minuscule 61 (Codex Montfortianus, 16th c.)", "Minuscule 629 (Codex Ottobonianus, 14th c. bilingual)", "Minuscule 918", "Minuscule 2318", "Codex Speculum (m, 5th c. Old Latin)", "Codex Cavensis (9th c.)", "Codex Toletanus (10th c.)", "Vast majority of Latin Vulgate manuscripts from the 6th century onward", "Complutensian Polyglot (1514)"]
        },
        "patristic_citations": [
            "St. Cyprian of Carthage (De Ecclesiae Catholicae Unitate 6, c. 251 AD) — 'The Lord says: I and the Father are one; and again it is written of the Father, and of the Son, and of the Holy Spirit: And these three are one.'",
            "Council of Carthage (484 AD) — St. Eugenius of Carthage and 400 African Catholic bishops presented a Confession of Faith to the Arian Vandal King Huneric quoting 1 John 5:7 verbatim!",
            "Priscillian of Avila (Liber Apologeticus, c. 385 AD)",
            "St. Fulgentius of Ruspe (Contra Fabianum, 6th c.)"
        ],
        "textual_criticism": {
            "critical_theory": "Critical orthodoxy maintains that the Comma originated as a Latin theological allegorization of the Spirit, water, and blood in North Africa, which was copied into the margin and eventually entered the Old Latin and Vulgate text.",
            "traditional_catholic_defense": "The Holy Office (1897 and 1927) issued authoritative guidance on the dogmatic authenticity of the Comma. St. Cyprian (251 AD) and the Council of Carthage (484 AD) witness to its existence in Latin antiquity centuries before any surviving Greek uncial of 1 John. Greek manuscripts suffered homeoteleuton due to the repeated phrase 'μαρτυροῦντες'.",
            "theological_impact": "The most explicit prooftext in all of Sacred Scripture for the dogma of the Blessed Trinity (three Persons, one Divine Essence)."
        }
    },
    {
        "id": "mark-16-9-20",
        "ref": "Mark 16:9-20",
        "book": "Mark",
        "chapter": 16,
        "verse": "9-20",
        "category": "NARRATIVE",
        "is_canonical_16": False,
        "title": "The Longer Ending of Mark (The Resurrection and Commission)",
        "summary": "The 12 concluding verses of Mark's Gospel recording Mary Magdalene, the Emmaus disciples, the Great Commission, signs following the Apostles, and the Ascension. Bracketed and questioned in modern Bibles.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "[Verses 9-20 printed as authentic inspired Scripture with explanatory footnote]",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "[Verses 9-20 printed without hesitation as authentic word of God]",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "[Verses 9-20 fully present and defined as canonical by Council of Trent]",
                "status": "INCLUDED",
                "badge": "Dogmatically Defined (Trent)"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Surgens autem mane prima sabbati, apparuit primo Mariae Magdalene...",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "[[Some of the earliest manuscripts do not include 16:9–20.]]",
                "status": "BRACKETED",
                "footnote": "Double brackets indicate verses not in the earliest manuscripts (Sinaiticus and Vaticanus).",
                "badge": "Double-Bracketed / Questioned"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "[Shorter ending and Longer ending separated with critical banners]",
                "status": "BRACKETED",
                "footnote": "The most reliable early manuscripts conclude with verse 8.",
                "badge": "Bracketed with Disclaimers"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "[Separated by a bold line and disclaimer: 'The earliest manuscripts and some other ancient witnesses do not have verses 9–20.']",
                "status": "BRACKETED",
                "badge": "Divided with Critical Notice"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[Verses 9-20 enclosed in brackets with notice: Later mss add vv 9-20]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "[Printed in main text with footnote regarding manuscript witnesses]",
                "status": "INCLUDED",
                "badge": "Catholic Canon"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "Ἀναστὰς δὲ πρωῒ πρώτῃ σαββάτου ἐφάνη πρῶτον Μαρίᾳ τῇ Μαγδαληνῇ...",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[[Mark 16:9-20 enclosed in double brackets as non-original]]",
                "status": "BRACKETED",
                "badge": "Double-Bracketed Critical"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א — note: leaves an entire blank column!)", "Codex Vaticanus (B — leaves an entire blank column, the only one in the NT!)", "Sinaitic Syriac", "Some Georgian/Armenian mss"],
            "included_by": ["Over 99% of all surviving Greek manuscripts (A, C, D, W, Θ, 𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac (sy-p)", "Curetonian Syriac"]
        },
        "patristic_citations": [
            "St. Irenaeus of Lyons (Against Heresies 3.10.6, c. 180 AD) — quotes Mark 16:19 verbatim: 'Also, towards the conclusion of his Gospel, Mark says: So then, after the Lord Jesus had spoken to them, He was received up into heaven...'",
            "Tatian's Diatessaron (c. 170 AD) — includes the longer ending",
            "Tertullian, St. Ambrose, St. Augustine, St. Jerome"
        ],
        "textual_criticism": {
            "critical_theory": "Westcott-Hort and modern critics claim Mark ended abruptly at verse 8 with 'ἐφοβοῦντο γάρ' ('for they were afraid') and an unknown second-century author composed the longer ending.",
            "traditional_catholic_defense": "Irenaeus quotes Mark 16:19 as inspired Scripture in 180 AD! Both Codex Vaticanus and Sinaiticus reveal scribal consciousness of the omission: Vaticanus leaves an entire blank column (the famous empty column of Mark) exactly where verses 9-20 belong! The Council of Trent dogmatically defined the canonical inspiration of Mark 16:9-20.",
            "theological_impact": "Affirms Christ's bodily resurrection appearances, the Great Commission, sacramental signs, and the glorious Ascension."
        }
    },
    {
        "id": "john-7-53-8-11",
        "ref": "John 7:53-8:11",
        "book": "John",
        "chapter": "7-8",
        "verse": "7:53-8:11",
        "category": "NARRATIVE",
        "is_canonical_16": False,
        "title": "Pericope Adulterae: The Woman Caught in Adultery",
        "summary": "Christ writing on the ground and delivering the immortal sentence: 'He that is without sin among you, let him first cast a stone at her.' Bracketed and doubted in modern Protestant Bibles.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "[Included in main text with explanatory footnote regarding early manuscripts]",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "[Included in main text without hesitation]",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "[Included in main text; dogmatically canonical per Council of Trent]",
                "status": "INCLUDED",
                "badge": "Dogmatically Defined (Trent)"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Et reversi sunt unusquisque in domum suam. Jesus autem perrexit in montem Oliveti...",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "[[Double-bracketed with header: The earliest manuscripts do not include 7:53–8:11]]",
                "status": "BRACKETED",
                "badge": "Double-Bracketed Critical"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "[Enclosed in brackets with note that most ancient mss omit it]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "[Divided with line: 'The earliest manuscripts and many other ancient witnesses do not have John 7:53–8:11.']",
                "status": "BRACKETED",
                "badge": "Divided with Critical Notice"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[Enclosed in brackets with note that early mss omit it]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "[Printed in main text; Catholic edition restores what secular RSV footnoted]",
                "status": "INCLUDED",
                "badge": "Catholic Canon"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "Καὶ ἐπορεύθη ἕκαστος εἰς τὸν οἶκον αὐτοῦ. Ἰησοῦς δὲ ἐπορεύθη εἰς τὸ Ὄρος τῶν Ἐλαιῶν...",
                "status": "INCLUDED",
                "badge": "Traditional Greek"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[[Enclosed in double brackets as an unoriginal interpolation]]",
                "status": "BRACKETED",
                "badge": "Double-Bracketed Critical"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 66 (𝔓66)", "Papyrus 75 (𝔓75)", "Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Alexandrinus (A - lacuna)", "Codex Ephraemi (C - lacuna)", "Codex Regius (L)", "Codex Washingtonianus (W)", "Majority of early Greek lectionaries"],
            "included_by": ["Codex Bezae (D, 5th c.)", "Codex Basilensis (E)", "Codex Seidelianus I (G)", "Codex Cyprius (K)", "Majority Byzantine Text (𝔐)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta (later mss)"]
        },
        "patristic_citations": [
            "St. Jerome (Pelag. 2.17, c. 415 AD) — 'In the Gospel according to John, in many copies, both Greek and Latin, there is found of the woman taken in adultery...'",
            "St. Augustine (De Adulterinis Conjugiis 2.7, c. 420 AD) — explicitly explains WHY the passage was excised: 'Certain persons of weak faith, or rather enemies of true faith, fearing that impunity might be granted to their wives for sinning, removed from their manuscripts the passage where the Lord forgave the adulteress!'",
            "Didascalia Apostolorum (early 3rd c.)",
            "St. Ambrose of Milan (Epist. 25, 26)"
        ],
        "textual_criticism": {
            "critical_theory": "Modern critics argue that the passage is not Johannine in style and was added from oral tradition or a Western gospel collection.",
            "traditional_catholic_defense": "St. Augustine provides the definitive historical smoking gun: the story was deliberately suppressed by puritanical copyists who feared it was too lenient on sexual immorality! St. Jerome confirmed it was present in many Greek and Latin manuscripts in the 4th century. Council of Trent dogmatically defined it as inspired Scripture.",
            "theological_impact": "The supreme revelation of Divine Mercy, Christ's authority to forgive sin, and the defeat of hypocritical Pharisaic legalism."
        }
    },
    {
        "id": "1tim-3-16",
        "ref": "1 Timothy 3:16",
        "book": "1 Timothy",
        "chapter": 3,
        "verse": 16,
        "category": "CHRISTOLOGY",
        "is_canonical_16": False,
        "title": "The Christological Mystery: 'God' vs. 'He Who' Was Manifest in the Flesh",
        "summary": "KJV/NKJV reads 'God was manifest in the flesh', whereas modern critical Bibles read 'He who was revealed in the flesh'. St. Jerome's Vulgate ('quod/qui') vindicated by modern discoveries.",
        "discord_highlight": False,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "And without controversy great is the mystery of godliness: God was manifested in the flesh...",
                "status": "INCLUDED",
                "badge": "Reads 'God' (Θεός)"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "And without controversy great is the mystery of godliness: God was manifest in the flesh...",
                "status": "INCLUDED",
                "badge": "Reads 'God' (Θεός)"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "And evidently great is the mystery of godliness: Which was manifested in the flesh...",
                "status": "INCLUDED",
                "badge": "Latin Vulgate ('quod/qui')"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "Et manifeste magnum est pietatis sacramentum, quod manifestatum est in carne...",
                "status": "INCLUDED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "Great indeed, we confess, is the mystery of godliness: He was manifested in the flesh...",
                "status": "MODIFIED",
                "footnote": "Greek: He who; other manuscripts read God; others read which",
                "badge": "Reads 'He' (ὅς)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "Without question, this is the great mystery of our faith: Christ was revealed in a human body...",
                "status": "MODIFIED",
                "badge": "Paraphrase"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "Beyond all question, the mystery from which true godliness springs is great: He appeared in the flesh...",
                "status": "MODIFIED",
                "badge": "Reads 'He' (ὅς)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "Commonly confessed: great is the mystery of godliness: He who was revealed in the flesh...",
                "status": "MODIFIED",
                "badge": "Reads 'He who' (ὅς)"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "Great indeed, we confess, is the mystery of our religion: He was manifested in the flesh...",
                "status": "INCLUDED",
                "badge": "Reads 'He' (ὅς)"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "καὶ ὁμολογουμένως μέγα ἐστὶν τὸ τῆς εὐσεβείας μυστήριον· Θεὸς ἐφανερώθη ἐν σαρκί...",
                "status": "INCLUDED",
                "badge": "Reads Θεός (God)"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "καὶ ὁμολογουμένως μέγα ἐστὶν τὸ τῆς εὐσεβείας μυστήριον· Ὃς ἐφανερώθη ἐν σαρκί...",
                "status": "INCLUDED",
                "badge": "Reads Ὃς (He who)"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א*) reads ὅς (He who)", "Codex Alexandrinus (A*) reads ὅς", "Codex Ephraemi (C*) reads ὅς", "Codex Boernerianus (G) reads ὅ (which)", "Old Latin (it)", "Latin Vulgate (vg)", "Peshitta Syriac"],
            "included_by": ["Later Byzantine minuscules (read Θεός via scribal ligature stroke converting ΟΣ into ΘΣ)", "Codex Sinaiticus corrector (אc)", "Codex Alexandrinus corrector (Ac)"]
        },
        "patristic_citations": [
            "St. Jerome (Vulgate 384 AD) — translated 'quod' reflecting ancient Greek Vorlage",
            "Western Fathers uniformly cite relative pronoun"
        ],
        "textual_criticism": {
            "critical_theory": "In ancient Greek uncials, the pronoun Ὃς was written ΟΣ. Scribes added a line across the omicron and a bar above, transforming it into the sacred abbreviation (nomina sacra) for God: ΘΣ (Θεός).",
            "traditional_catholic_defense": "The Latin Vulgate of St. Jerome translated 'quod/qui' centuries before Erasmus. When 19th-century textual critics examined Codex Alexandrinus with microscopes, they confirmed that the horizontal bar had been added in later ink, vindicating the ancient Catholic Vulgate!",
            "theological_impact": "Demonstrates scribal piety and vindicates St. Jerome's Latin Vulgate against King James Only polemics."
        }
    },
    {
        "id": "1cor-7-5",
        "ref": "1 Corinthians 7:5",
        "book": "1 Corinthians",
        "chapter": 7,
        "verse": 5,
        "category": "FASTING",
        "is_canonical_16": False,
        "title": "Marital Abstinence for 'Fasting and Prayer'",
        "summary": "St. Paul's instruction permitting married couples temporary abstinence 'that you may give yourselves to fasting and prayer'. Modern critical Bibles excise 'fasting', leaving only 'prayer'.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "...except with consent for a time, that you may give yourselves to fasting and prayer; and come together again so that Satan does not tempt you...",
                "status": "INCLUDED",
                "badge": "Includes 'Fasting and Prayer'"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "...except it be with consent for a time, that ye may give yourselves to fasting and prayer; and come together again, that Satan tempt you not...",
                "status": "INCLUDED",
                "badge": "Includes 'Fasting and Prayer'"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "...except, perhaps, by consent, for a time, that you may give yourselves to prayer; and return together again, lest Satan tempt you...",
                "status": "MODIFIED",
                "badge": "Reads 'Prayer'"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "...nisi forte ex consensu ad tempus, ut vacetis orationi: et iterum revertimini in idipsum...",
                "status": "MODIFIED",
                "badge": "Reads 'orationi' (prayer)"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "...except perhaps by agreement for a limited time, that you may devote yourselves to prayer; but then come together again...",
                "status": "MODIFIED",
                "footnote": "Greek: that you may have leisure for prayer; some manuscripts read: fasting and prayer",
                "badge": "'Fasting' Excised"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "...only if you both agree to abstain from sexual intimacy for a limited time so you can give yourselves more completely to prayer...",
                "status": "MODIFIED",
                "badge": "'Fasting' Excised"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "...except perhaps by mutual consent and for a time, so that you may devote yourselves to prayer. Then come together again...",
                "status": "MODIFIED",
                "badge": "'Fasting' Excised"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "...except by agreement for a time, so that you may devote yourselves to prayer, and come together again...",
                "status": "MODIFIED",
                "badge": "'Fasting' Excised"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "...except perhaps by agreement for a season, that you may devote yourselves to prayer; but then come together again...",
                "status": "MODIFIED",
                "badge": "Reads 'Prayer'"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "...εἰ μή τι ἂν ἐκ συμφώνου πρὸς καιρόν, ἵνα σχολάζητε τῇ νηστείᾳ καὶ τῇ προσευχῇ...",
                "status": "INCLUDED",
                "badge": "Includes τῇ νηστείᾳ (fasting)"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "...εἰ μή τι ἂν ἐκ συμφώνου πρὸς καιρόν, ἵνα σχολάσητε τῇ προσευχῇ...",
                "status": "MODIFIED",
                "badge": "Excises Fasting"
            }
        },
        "manuscripts": {
            "omitted_by": ["Papyrus 46 (𝔓46, c. 200 AD)", "Codex Sinaiticus (א)", "Codex Alexandrinus (A)", "Codex Vaticanus (B)", "Codex Ephraemi (C)", "Latin Vulgate (vg)", "Sahidic Coptic"],
            "included_by": ["Codex Claromontanus (D2)", "Codex Mosquensis (K)", "Codex Angelicus (L)", "Majority Byzantine Text (𝔐)", "Old Latin (it: d, f)"]
        },
        "patristic_citations": [
            "St. John Chrysostom (Homilies on 1 Corinthians 19)",
            "Theodoret of Cyrus"
        ],
        "textual_criticism": {
            "critical_theory": "Modern critics view 'fasting' as an ascetic gloss added by Byzantine monks.",
            "traditional_catholic_defense": "Shows the systematic modern excision of 'fasting' across the New Testament (Matt 17:21, Mark 9:29, Acts 10:30, 1 Cor 7:5).",
            "theological_impact": "Directly impacts Catholic ascetic discipline and spiritual warfare."
        }
    },
    {
        "id": "matt-6-13b",
        "ref": "Matthew 6:13b",
        "book": "Matthew",
        "chapter": 6,
        "verse": "13b",
        "category": "ECCLESIAL",
        "is_canonical_16": False,
        "title": "The Lord's Prayer Doxology",
        "summary": "The concluding doxology: 'For Thine is the kingdom, and the power, and the glory, forever. Amen.' Omitted in Latin Vulgate and modern critical texts, preserved in Byzantine/Protestant tradition.",
        "discord_highlight": True,
        "translations": {
            "NKJV": {
                "name": "New King James Version",
                "text": "For Yours is the kingdom and the power and the glory forever. Amen.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "KJV": {
                "name": "King James Version 1611/1769",
                "text": "For thine is the kingdom, and the power, and the glory, for ever. Amen.",
                "status": "INCLUDED",
                "badge": "Main Text"
            },
            "DRB": {
                "name": "Douay-Rheims Catholic Bible",
                "text": "[Omitted from continuous text, ending at 'deliver us from evil. Amen.']",
                "status": "OMITTED (Vulgate)",
                "badge": "Catholic Liturgical Pattern"
            },
            "VULG": {
                "name": "Biblia Sacra Vulgata (St. Jerome, 384 AD)",
                "text": "...sed libera nos a malo. Amen.",
                "status": "OMITTED",
                "badge": "Latin Vulgate"
            },
            "ESV": {
                "name": "English Standard Version 2025",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add: For yours is the kingdom and the power and the glory, forever. Amen.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NLT": {
                "name": "New Living Translation",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts add: For yours is the kingdom and the power and the glory forever. Amen.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NIV": {
                "name": "New International Version 2011",
                "text": "",
                "status": "OMITTED",
                "footnote": "Some manuscripts include: for yours is the kingdom and the power and the glory forever. Amen.",
                "badge": "Omitted (Relegated to Footnote)"
            },
            "NASB": {
                "name": "New American Standard Bible 1995/2020",
                "text": "[For Yours is the kingdom and the power and the glory forever. Amen.]",
                "status": "BRACKETED",
                "badge": "Bracketed in Text"
            },
            "RSVCE": {
                "name": "Revised Standard Version Catholic Edition",
                "text": "...but deliver us from evil.",
                "status": "OMITTED",
                "badge": "Catholic Liturgical Pattern"
            },
            "GREEK_TR": {
                "name": "Greek Textus Receptus / Majority Text",
                "text": "ὅτι σοῦ ἐστιν ἡ βασιλεία καὶ ἡ δύναμις καὶ ἡ δόξα εἰς τοὺς αἰῶνας· ἀμήν.",
                "status": "INCLUDED",
                "badge": "Traditional Byzantine"
            },
            "GREEK_NA28": {
                "name": "Nestle-Aland 28th / UBS5 Critical Text",
                "text": "[Doxology omitted; prayer ends with ἀπὸ τοῦ πονηροῦ]",
                "status": "OMITTED",
                "badge": "Critical Text Omission"
            }
        },
        "manuscripts": {
            "omitted_by": ["Codex Sinaiticus (א)", "Codex Vaticanus (B)", "Codex Bezae (D)", "Codex Dublinensis (Z)", "Old Latin (it)", "Latin Vulgate (vg)"],
            "included_by": ["Codex Washingtonianus (W)", "Codex Koridethi (Θ)", "Majority Byzantine Text (𝔐)", "Didache 8.2 (short form: 'for thine is the power and glory forever')", "Curetonian Syriac"]
        },
        "patristic_citations": [
            "Tertullian, St. Cyprian, St. Jerome, St. Augustine (none of whom comment on the doxology in the Lord's Prayer)",
            "St. John Chrysostom (Homilies on Matthew 19.5, comments on the doxology)"
        ],
        "textual_criticism": {
            "critical_theory": "Modern critics argue that the doxology was a liturgical congregation response appended to the Gospel text.",
            "traditional_catholic_defense": "Vindicates the ancient Roman Liturgy and Latin Vulgate! For centuries, Protestants accused Catholics of 'cutting off the end of the Lord's Prayer' in the Mass. When modern textual criticism emerged, it proved that the Catholic Latin Vulgate had preserved the original ending all along!",
            "theological_impact": "Major liturgical and apologetic battlefield between Catholic and Protestant worship."
        }
    }
]

def generate_json_and_html():
    json_path = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\web_app\omitted_verses_data.json"
    html_path = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\web_app\omitted_verses_explorer.html"
    
    # 1. Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(DATA, f, indent=2, ensure_ascii=False)
    print(f"[OK] Wrote JSON data to {json_path} ({len(DATA)} loci)")

    # 2. Build and Write HTML
    html_content = generate_html_string(DATA)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] Wrote interactive web workstation to {html_path} ({len(html_content)} bytes)")


def generate_html_string(data):
    json_embedded = json.dumps(data, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="en" class="dark scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Scripture Omitted Verses & Forensic Textual Apparatus | Discord Card Generator</title>

  <!-- Tailwind CSS CDN -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            brand: {{
              50: '#f8fafc',
              100: '#f1f5f9',
              200: '#e2e8f0',
              300: '#cbd5e1',
              400: '#94a3b8',
              500: '#64748b',
              600: '#475569',
              700: '#334155',
              800: '#1e293b',
              900: '#0f172a',
              950: '#020617'
            }},
            discord: {{
              darkest: '#111214',
              dark: '#1e1f22',
              card: '#2b2d31',
              hover: '#35373c',
              blurple: '#5865f2',
              text: '#dbdee1',
              muted: '#949ba4'
            }},
            gold: {{
              400: '#fbbf24',
              500: '#f59e0b',
              600: '#d97706',
              glow: 'rgba(245, 158, 11, 0.2)'
            }}
          }},
          fontFamily: {{
            serif: ['Cinzel', 'Georgia', 'serif'],
            sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
            mono: ['JetBrains Mono', 'Fira Code', 'monospace']
          }}
        }}
      }}
    }}
  </script>

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <!-- Lucide Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>

  <style>
    ::-webkit-scrollbar {{ width: 7px; height: 7px; }}
    ::-webkit-scrollbar-track {{ background: #0b0f17; }}
    ::-webkit-scrollbar-thumb {{ background: #26334d; border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: #3b82f6; }}
    
    .font-hebrew {{ font-family: 'SBL Hebrew', 'Ezra SIL', 'Times New Roman', serif; direction: rtl; }}
    .font-greek {{ font-family: 'SBL Greek', 'Cardo', 'Gentium Plus', 'Times New Roman', serif; }}
    
    .glass-panel {{
      background: rgba(18, 24, 38, 0.85);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(56, 189, 248, 0.12);
    }}

    .discord-card-shadow {{
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.6);
    }}
  </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans antialiased selection:bg-amber-500 selection:text-slate-950 min-h-screen flex flex-col">

  <!-- TOP APP NAV -->
  <header class="sticky top-0 z-50 bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80 px-4 lg:px-8 py-3.5 transition-all">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-600 via-amber-500 to-yellow-400 flex items-center justify-center text-slate-950 shadow-lg shadow-amber-500/20 font-serif font-black text-xl">
          ☩
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="font-serif font-bold text-lg text-slate-100 tracking-wide">OMITTED SCRIPTURE WORKSTATION</h1>
            <span class="px-2 py-0.5 text-[10px] font-mono tracking-wider font-semibold rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">27 LOCI APPARATUS</span>
          </div>
          <p class="text-xs text-slate-400">Forensic Textual Criticism, Manuscript Matrix & Discord Card Generator</p>
        </div>
      </div>

      <!-- Quick Nav Links -->
      <div class="flex items-center gap-2">
        <a href="#discord-generator" class="px-3.5 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium flex items-center gap-1.5 transition">
          <i data-lucide="image" class="w-3.5 h-3.5"></i>
          Discord Generator
        </a>
        <a href="#loci-catalog" class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium flex items-center gap-1.5 transition">
          <i data-lucide="book-open" class="w-3.5 h-3.5"></i>
          The 27 Loci
        </a>
        <a href="#where-to-check" class="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium flex items-center gap-1.5 transition">
          <i data-lucide="globe" class="w-3.5 h-3.5"></i>
          Where to Check Online
        </a>
        <a href="#apologetics-dossier" class="px-3.5 py-1.5 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 text-xs font-medium flex items-center gap-1.5 transition">
          <i data-lucide="shield" class="w-3.5 h-3.5"></i>
          Catholic Apologetics
        </a>
      </div>
    </div>
  </header>

  <!-- HERO & INTRO BANNER -->
  <section class="bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 border-b border-slate-800/60 pt-10 pb-8 px-4 lg:px-8">
    <div class="max-w-7xl mx-auto">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <div class="lg:col-span-8 space-y-4">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-mono">
            <span class="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
            SOLVING THE 1551 STEPHANUS VERSE-NUMBERING PARADOX
          </div>
          <h2 class="text-3xl lg:text-4xl font-extrabold tracking-tight text-white">
            Why Modern Protestant Bibles Have <span class="bg-gradient-to-r from-amber-400 via-yellow-300 to-amber-500 bg-clip-text text-transparent">"Missing Verses"</span>
          </h2>
          <p class="text-sm lg:text-base text-slate-300 leading-relaxed">
            In 1551, Robert Estienne (Stephanus) divided the Greek New Testament into numbered verses based on late Byzantine manuscripts (the <em>Textus Receptus</em>). When 19th-century textual critics (Westcott-Hort, Tischendorf, Nestle-Aland) embraced earlier Alexandrian codices (<em>Codex Sinaiticus</em> $\aleph$ and <em>Codex Vaticanus</em> $B$) that lacked these verses, modern translation committees (ESV, NIV, NLT) faced a crisis: <strong>they could not renumber the Bible without destroying global concordances, so they left the verse numbers completely empty or relegated them to footnotes!</strong>
          </p>
          <div class="flex flex-wrap gap-4 pt-2 text-xs">
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-400"></i>
              <span><strong>16-17 Entire Verses</strong> Excised from Modern Main Text</span>
            </div>
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <i data-lucide="shield-alert" class="w-4 h-4 text-amber-400"></i>
              <span><strong>Fasting, Trinity & Demonology</strong> Heavily Impacted</span>
            </div>
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <i data-lucide="landmark" class="w-4 h-4 text-purple-400"></i>
              <span><strong>Latin Vulgate (St. Jerome 384 AD)</strong> Pre-dates All Surviving Byzantine Cursives</span>
            </div>
          </div>
        </div>

        <!-- Metric Stat Cards -->
        <div class="lg:col-span-4 grid grid-cols-2 gap-3">
          <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-center">
            <div class="text-3xl font-extrabold text-amber-400 font-mono">16-17</div>
            <div class="text-[11px] font-medium text-slate-400 mt-1 uppercase tracking-wider">Numbered Verses Dropped</div>
            <div class="text-[10px] text-slate-500 mt-0.5">Jump directly e.g. 20 → 22</div>
          </div>
          <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-center">
            <div class="text-3xl font-extrabold text-blue-400 font-mono">27+</div>
            <div class="text-[11px] font-medium text-slate-400 mt-1 uppercase tracking-wider">Critical Loci Analyzed</div>
            <div class="text-[10px] text-slate-500 mt-0.5">Full manuscript pedigree</div>
          </div>
          <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-center">
            <div class="text-3xl font-extrabold text-emerald-400 font-mono">1551</div>
            <div class="text-[11px] font-medium text-slate-400 mt-1 uppercase tracking-wider">Stephanus Baseline</div>
            <div class="text-[10px] text-slate-500 mt-0.5">4th Edition Greek NT</div>
          </div>
          <div class="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-center">
            <div class="text-3xl font-extrabold text-purple-400 font-mono">1546</div>
            <div class="text-[11px] font-medium text-slate-400 mt-1 uppercase tracking-wider">Council of Trent</div>
            <div class="text-[10px] text-slate-500 mt-0.5">Infallible Canon Definition</div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- SECTION 1: DISCORD CARD GENERATOR          -->
  <!-- ========================================== -->
  <section id="discord-generator" class="py-10 px-4 lg:px-8 border-b border-slate-800 bg-slate-950/60">
    <div class="max-w-7xl mx-auto">
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
        <div>
          <div class="flex items-center gap-2 text-indigo-400 text-xs font-mono font-semibold uppercase tracking-wider">
            <i data-lucide="sparkles" class="w-4 h-4"></i>
            Visual Meme & Comparison Card Engine
          </div>
          <h3 class="text-2xl font-bold text-white mt-1">Discord & YouVersion Comparison Card Generator</h3>
          <p class="text-xs text-slate-400 mt-0.5">Pixel-perfect reproduction of the dark-mode YouVersion / Discord comparison card shown in your screenshot!</p>
        </div>

        <div class="flex items-center gap-2">
          <button id="btn-copy-discord-text" onclick="copyDiscordMarkdown()" class="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium flex items-center gap-1.5 transition">
            <i data-lucide="copy" class="w-3.5 h-3.5"></i>
            Copy Discord Markdown
          </button>
          <button id="btn-copy-card-img" onclick="copyCardAsImage()" class="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 transition">
            <i data-lucide="clipboard" class="w-3.5 h-3.5"></i>
            Copy Image (Ctrl+V Ready)
          </button>
          <button id="btn-download-card-png" onclick="downloadCardPNG()" class="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-emerald-600/30 transition">
            <i data-lucide="download" class="w-3.5 h-3.5"></i>
            Download PNG
          </button>
        </div>
      </div>

      <!-- Controls & Card Canvas Layout -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <!-- Controls Sidebar -->
        <div class="lg:col-span-5 space-y-5 bg-slate-900/80 p-5 rounded-2xl border border-slate-800">
          <!-- Select Locus -->
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1.5">Select Contested Verse:</label>
            <select id="card-locus-select" onchange="onCardLocusChange(this.value)" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
              <!-- Dynamically Populated -->
            </select>
          </div>

          <!-- Display Mode Toggle -->
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1.5">Comparison Card Mode:</label>
            <div class="grid grid-cols-2 gap-2 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
              <button id="mode-youversion" onclick="setCardMode('youversion')" class="py-2 px-3 rounded-lg font-semibold bg-indigo-600 text-white transition text-center">
                YouVersion Mode (Raw Blanks)
              </button>
              <button id="mode-scholarly" onclick="setCardMode('scholarly')" class="py-2 px-3 rounded-lg font-medium text-slate-400 hover:text-white transition text-center">
                Scholar Mode (With Footnotes)
              </button>
            </div>
            <p class="text-[11px] text-slate-500 mt-1.5">
              <em>YouVersion Mode</em> renders the exact blank space seen in the screenshot where the verse number is completely skipped.
            </p>
          </div>

          <!-- Translation Selectors (Checkboxes) -->
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-2">Include Translations on Card:</label>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-NKJV" checked onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-slate-200">NKJV</span>
                <span class="text-[10px] text-slate-500 truncate">New King James</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-ESV" checked onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-slate-200">ESV</span>
                <span class="text-[10px] text-slate-500 truncate">English Standard</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-NLT" checked onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-slate-200">NLT</span>
                <span class="text-[10px] text-slate-500 truncate">New Living Trans.</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-NIV" checked onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-slate-200">NIV</span>
                <span class="text-[10px] text-slate-500 truncate">New Int. Version</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-DRB" onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-amber-300">DRB</span>
                <span class="text-[10px] text-slate-500 truncate">Douay-Rheims (Vulgate)</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-VULG" onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-purple-300">VULG</span>
                <span class="text-[10px] text-slate-500 truncate">Biblia Sacra Vulgata</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-KJV" onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-slate-200">KJV</span>
                <span class="text-[10px] text-slate-500 truncate">King James 1611</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-NASB" onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-slate-200">NASB</span>
                <span class="text-[10px] text-slate-500 truncate">New American Standard</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-RSVCE" onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-emerald-300">RSV-CE</span>
                <span class="text-[10px] text-slate-500 truncate">RSV Catholic Edition</span>
              </label>
              <label class="flex items-center gap-2 p-2 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <input type="checkbox" id="chk-GREEK_TR" onchange="renderCard()" class="rounded border-slate-700 text-indigo-600 focus:ring-indigo-500">
                <span class="font-bold text-cyan-300">GREEK</span>
                <span class="text-[10px] text-slate-500 truncate">Textus Receptus</span>
              </label>
            </div>
          </div>

          <!-- Discord Comment Context Input -->
          <div>
            <label class="block text-xs font-medium text-slate-300 mb-1">Custom Discord Header Comment (Optional):</label>
            <input type="text" id="discord-custom-comment" oninput="updateDiscordComment(this.value)" value="This reminds me of Matthew 17:21 which is literally completely excluded from the main Protestant Bible translations 🤨🧐" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500">
          </div>
        </div>

        <!-- Live Visual Preview Area -->
        <div class="lg:col-span-7 flex flex-col items-center">
          <div class="text-xs text-slate-400 mb-2 flex items-center gap-1 font-mono">
            <i data-lucide="monitor" class="w-3.5 h-3.5 text-indigo-400"></i>
            LIVE PREVIEW (DISCORD DARK THEME SIMULATOR)
          </div>

          <!-- THE DISCORD CONTAINER -->
          <div id="discord-mockup-wrapper" class="w-full max-w-[560px] bg-[#313338] p-4 sm:p-6 rounded-2xl discord-card-shadow border border-[#3f4147] text-[#dbdee1]">
            
            <!-- Discord Message Header -->
            <div class="flex items-start gap-3 mb-3">
              <div class="w-10 h-10 rounded-full bg-slate-700 flex-shrink-0 flex items-center justify-center font-bold text-sm text-slate-300 border border-slate-600">
                🕇
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-baseline gap-2">
                  <span class="font-semibold text-white text-sm">tori</span>
                  <span class="px-1.5 py-0.2 text-[9px] font-bold rounded bg-[#5865f2] text-white">PRO</span>
                  <span class="text-[10px] text-[#949ba4]">Today at 3:52 PM</span>
                </div>
                <p id="discord-preview-comment" class="text-xs text-[#dbdee1] mt-0.5 leading-relaxed font-sans">
                  This reminds me of Matthew 17:21 which is literally completely excluded from the main Protestant Bible translations 🤨🧐
                </p>
              </div>
            </div>

            <!-- THE YOUVERSION / COMPARISON CARD ITSELF -->
            <div id="capture-card" class="bg-[#1e1f22] rounded-xl p-4 sm:p-5 border border-[#2b2d31] space-y-4">
              <!-- Dynamically populated by JS renderCard() -->
            </div>

            <div class="text-center text-[10px] text-[#949ba4] mt-2.5 flex items-center justify-between">
              <span>Textual Criticism Workstation</span>
              <span>Generated from Ancient Codices & Patristics</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- SECTION 2: THE 27 CRITICAL LOCI CATALOG    -->
  <!-- ========================================== -->
  <section id="loci-catalog" class="py-12 px-4 lg:px-8 max-w-7xl mx-auto flex-1 w-full">
    <div class="space-y-6">
      <!-- Title & Search Bar -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div class="flex items-center gap-2 text-amber-400 text-xs font-mono font-semibold uppercase tracking-wider">
            <i data-lucide="database" class="w-4 h-4"></i>
            Exhaustive Manuscript & Forensic Archive
          </div>
          <h3 class="text-3xl font-extrabold text-white mt-1">The 27 Critical Omitted & Contested Loci</h3>
          <p class="text-sm text-slate-400 mt-1">Complete parallel text across 10 translation streams, early codex witnesses, patristic citations, and theological impact.</p>
        </div>

        <!-- Search Bar -->
        <div class="w-full md:w-80 relative">
          <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3.5 top-3"></i>
          <input type="text" id="catalog-search" oninput="filterLoci()" placeholder="Search verse, keyword, codex..." class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500">
        </div>
      </div>

      <!-- Category Filter Tabs -->
      <div class="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none border-b border-slate-800 text-xs">
        <button onclick="setCategoryFilter('ALL')" class="cat-pill active px-3.5 py-1.5 rounded-lg bg-amber-500 text-slate-950 font-bold transition flex-shrink-0" data-cat="ALL">
          All Loci (27)
        </button>
        <button onclick="setCategoryFilter('CANONICAL_16')" class="cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0" data-cat="CANONICAL_16">
          The 16 Omitted Verses (Standard)
        </button>
        <button onclick="setCategoryFilter('FASTING')" class="cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0" data-cat="FASTING">
          Fasting & Asceticism (Matt 17:21, 1 Cor 7:5)
        </button>
        <button onclick="setCategoryFilter('CHRISTOLOGY')" class="cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0" data-cat="CHRISTOLOGY">
          Christology & Incarnation (1 Tim 3:16, Col 1:14)
        </button>
        <button onclick="setCategoryFilter('TRINITY')" class="cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0" data-cat="TRINITY">
          Holy Trinity (1 John 5:7-8)
        </button>
        <button onclick="setCategoryFilter('SACRAMENTS')" class="cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0" data-cat="SACRAMENTS">
          Sacraments & Baptism (Acts 8:37)
        </button>
        <button onclick="setCategoryFilter('HELL_JUDGMENT')" class="cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0" data-cat="HELL_JUDGMENT">
          Hell & Gehenna (Mark 9:44, 46)
        </button>
        <button onclick="setCategoryFilter('NARRATIVE')" class="cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0" data-cat="NARRATIVE">
          Major Passages (Mark 16, John 7:53)
        </button>
        <button onclick="setCategoryFilter('ECCLESIAL')" class="cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0" data-cat="ECCLESIAL">
          Ecclesial & Liturgical (Matt 6:13b)
        </button>
      </div>

      <!-- Loci Cards Grid -->
      <div id="loci-cards-container" class="space-y-6">
        <!-- Rendered via renderLociList() -->
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- SECTION 3: WHERE TO CHECK ONLINE GUIDE     -->
  <!-- ========================================== -->
  <section id="where-to-check" class="py-12 px-4 lg:px-8 bg-slate-900/60 border-t border-slate-800">
    <div class="max-w-7xl mx-auto space-y-8">
      <div>
        <div class="flex items-center gap-2 text-cyan-400 text-xs font-mono font-semibold uppercase tracking-wider">
          <i data-lucide="compass" class="w-4 h-4"></i>
          Public Verification Guide
        </div>
        <h3 class="text-3xl font-extrabold text-white mt-1">Which Sites & Apps Show Omitted Verses Like This?</h3>
        <p class="text-sm text-slate-300 mt-1">Direct breakdown of where and how to verify these missing verses across public online tools and mobile apps.</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- Card 1: YouVersion -->
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4 hover:border-slate-700 transition">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-red-600 to-amber-500 flex items-center justify-center text-white font-bold text-lg shadow-lg">
            YV
          </div>
          <div>
            <h4 class="text-lg font-bold text-white flex items-center justify-between">
              <span>YouVersion (Bible.com)</span>
              <span class="text-xs font-normal text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">The Screenshot Origin</span>
            </h4>
            <p class="text-xs text-slate-400 mt-1">Mobile App & Web Platform</p>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            The exact screenshot uploaded by the user is generated by the <strong>YouVersion Bible App's "Compare" feature</strong> in Dark Mode.
          </p>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800/80 text-[11px] space-y-1.5 text-slate-300">
            <div class="font-semibold text-slate-200">How to Reproduce Step-by-Step:</div>
            <div>1. Open Matthew 17 in YouVersion.</div>
            <div>2. Tap verse <strong>21</strong> (or where verse 21 should be).</div>
            <div>3. In the popup action sheet, tap <strong>"Compare"</strong>.</div>
            <div>4. Select <strong>NKJV, ESV, NLT, and NIV</strong> in Dark Mode.</div>
            <div>5. Because ESV, NLT, and NIV have no text assigned to Matthew 17:21 in their digital database, YouVersion renders an empty, blank spot underneath each header!</div>
          </div>
          <a href="https://www.bible.com/bible/114/MAT.17.21.NKJV" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 pt-1">
            Visit Bible.com Matthew 17:21 <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        </div>

        <!-- Card 2: Bible Gateway -->
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4 hover:border-slate-700 transition">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-lg">
            BG
          </div>
          <div>
            <h4 class="text-lg font-bold text-white">BibleGateway.com</h4>
            <p class="text-xs text-slate-400 mt-1">Multi-Column Parallel View</p>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            Bible Gateway allows up to 5 side-by-side parallel columns. When searching for an omitted verse like Matthew 17:21 in ESV or NIV, it explicitly flags: <em>"Verse 21 is omitted in this translation"</em> or drops it to the bottom apparatus.
          </p>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800/80 text-[11px] space-y-1.5 text-slate-300">
            <div class="font-semibold text-slate-200">How to Test:</div>
            <div>1. Go to BibleGateway.com search bar.</div>
            <div>2. Enter: <code>Matthew 17:20-22</code>.</div>
            <div>3. Click the <strong>"Add Parallel"</strong> button icon.</div>
            <div>4. Select KJV / Douay-Rheims next to ESV / NIV to immediately see verse 21 disappear in the right column!</div>
          </div>
          <a href="https://www.biblegateway.com/passage/?search=Matthew+17%3A20-22&version=NKJV;ESV;NIV" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 pt-1">
            Open Parallel on BibleGateway <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        </div>

        <!-- Card 3: BibleHub -->
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4 hover:border-slate-700 transition">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white font-bold text-lg shadow-lg">
            BH
          </div>
          <div>
            <h4 class="text-lg font-bold text-white">BibleHub.com</h4>
            <p class="text-xs text-slate-400 mt-1">Verse-by-Verse Multi-Version & Interlinear</p>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            BibleHub organizes its database by individual verse URLs (e.g. <code>biblehub.com/matthew/17-21.htm</code>).
          </p>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800/80 text-[11px] space-y-1.5 text-slate-300">
            <div class="font-semibold text-slate-200">Key Features:</div>
            <div>• Lists every major English translation line-by-line.</div>
            <div>• Modern versions state: <code>[This verse is omitted in the best ancient manuscripts]</code>.</div>
            <div>• Direct access to Greek Textus Receptus vs. NA28 interlinear comparison for that verse.</div>
          </div>
          <a href="https://biblehub.com/matthew/17-21.htm" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 pt-1">
            Inspect BibleHub Matthew 17:21 <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        </div>

        <!-- Card 4: NET Bible -->
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4 hover:border-slate-700 transition">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
            NET
          </div>
          <div>
            <h4 class="text-lg font-bold text-white">NET Bible (netbible.org)</h4>
            <p class="text-xs text-slate-400 mt-1">Premier Textual Apparatus for Translators</p>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            The NET Bible features over 60,000 translation and text-critical notes explaining precisely *why* modern scholars omit or include variants.
          </p>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800/80 text-[11px] space-y-1.5 text-slate-300">
            <div class="font-semibold text-slate-200">Why It Matters:</div>
            <div>• Explicit manuscript citation lists (Papyri, Uncials, Minuscules, Versions).</div>
            <div>• Detailed defense of NA28/UBS5 editorial decisions.</div>
            <div>• Perfect academic reference for examining the critical text perspective.</div>
          </div>
          <a href="https://netbible.org/bible/Matthew+17" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 pt-1">
            Open NET Bible Apparatus <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        </div>

        <!-- Card 5: CSNTM & NTVMR -->
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4 hover:border-slate-700 transition">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-amber-600 to-red-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
            MSS
          </div>
          <div>
            <h4 class="text-lg font-bold text-white">CSNTM & Münster NTVMR</h4>
            <p class="text-xs text-slate-400 mt-1">High-Resolution Primary Manuscript Photographs</p>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            The Center for the Study of New Testament Manuscripts and Münster Institute for New Testament Textual Research allow you to view the actual physical codices.
          </p>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800/80 text-[11px] space-y-1.5 text-slate-300">
            <div class="font-semibold text-slate-200">Primary Source Evidence:</div>
            <div>• Zoom in on Codex Sinaiticus (4th c.) at the British Library showing verse 21 missing.</div>
            <div>• Inspect Codex Vaticanus showing the famous blank column after Mark 16:8.</div>
            <div>• See physical scribal corrections made in antiquity.</div>
          </div>
          <a href="https://www.csntm.org" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 pt-1">
            Explore Primary Manuscripts <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        </div>

        <!-- Card 6: Wikipedia Index -->
        <div class="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4 hover:border-slate-700 transition">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-slate-700 to-slate-500 flex items-center justify-center text-white font-bold text-lg shadow-lg">
            W
          </div>
          <div>
            <h4 class="text-lg font-bold text-white">Wikipedia Master Reference</h4>
            <p class="text-xs text-slate-400 mt-1">"List of NT Verses Not Included in Modern Translations"</p>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            Wikipedia maintains the standard canonical reference article indexing all 16 to 17 omitted verses and major narrative pericopes.
          </p>
          <div class="bg-slate-900 p-3 rounded-xl border border-slate-800/80 text-[11px] space-y-1.5 text-slate-300">
            <div class="font-semibold text-slate-200">Summary:</div>
            <div>• Full chart comparing KJV, NKJV, NASB, NIV, ESV, and CSB handling.</div>
            <div>• Explains the difference between critical text omissions and bracketed readings.</div>
          </div>
          <a href="https://en.wikipedia.org/wiki/List_of_New_Testament_verses_not_included_in_modern_English_translations" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 pt-1">
            View Wikipedia Article <i data-lucide="external-link" class="w-3 h-3"></i>
          </a>
        </div>
      </div>
    </div>
  </section>

  <!-- ========================================== -->
  <!-- SECTION 4: APOLOGETICS & THEOLOGICAL DOSSIER-->
  <!-- ========================================== -->
  <section id="apologetics-dossier" class="py-12 px-4 lg:px-8 border-t border-slate-800 bg-slate-950">
    <div class="max-w-7xl mx-auto space-y-8">
      <div>
        <div class="flex items-center gap-2 text-amber-400 text-xs font-mono font-semibold uppercase tracking-wider">
          <i data-lucide="shield-check" class="w-4 h-4"></i>
          History Proves Catholicism Dossier
        </div>
        <h3 class="text-3xl font-extrabold text-white mt-1">The Epistemological Collapse of Sola Scriptura in Textual Criticism</h3>
        <p class="text-sm text-slate-400 mt-1">How modern manuscript discoveries dismantle Protestant Bibliolatry while vindicating the Living Magisterium and the Latin Vulgate.</p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Column 1 -->
        <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div class="text-amber-400 font-bold text-sm flex items-center gap-2">
            <i data-lucide="alert-triangle" class="w-4 h-4"></i>
            1. The Sola Scriptura Catch-22
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            Protestant theology asserts that the Bible alone is the infallible rule of faith, and that divine inspiration attaches strictly to the <em>original autographs</em>. But the original autographs vanished in the 1st century, and out of 5,800+ Greek manuscripts, <strong>no two are identical</strong>.
          </p>
          <p class="text-xs text-slate-400 leading-relaxed">
            If the Church is not infallible, which text is inspired? The 1611 KJV (Textus Receptus)? The 1881 Westcott-Hort? The NA28? When an ordinary Protestant opens their ESV and sees Matthew 17:21 deleted, their foundation crumbles: <em>who decides what is Scripture and what is a scribal corruption?</em>
          </p>
        </div>

        <!-- Column 2 -->
        <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div class="text-purple-400 font-bold text-sm flex items-center gap-2">
            <i data-lucide="book-marked" class="w-4 h-4"></i>
            2. The Vindication of St. Jerome's Vulgate
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            In 1546, the Council of Trent declared the Latin Vulgate to be authentic and authoritative. For 400 years, Protestant scholars mocked this decree, claiming Erasmus's Greek manuscripts were superior.
          </p>
          <p class="text-xs text-slate-400 leading-relaxed">
            Yet St. Jerome translated in 384 AD using Greek manuscripts <strong>1,000 years older</strong> than Erasmus's late Byzantine minuscules! Modern discoveries have repeatedly proven that St. Jerome preserved authentic readings (e.g. 1 Tim 3:16, Matt 6:13b omitting the doxology, 1 Cor 7:5) that the Protestant Textus Receptus corrupted.
          </p>
        </div>

        <!-- Column 3 -->
        <div class="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div class="text-emerald-400 font-bold text-sm flex items-center gap-2">
            <i data-lucide="church" class="w-4 h-4"></i>
            3. The Triumph of Ecclesial Canonization
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            Passages like Mark 16:9-20 (the Longer Ending) and John 7:53-8:11 (the Woman Caught in Adultery) have complex textual histories. Under strict naturalistic textual criticism, Protestant scholars must bracket them or treat them as doubtful.
          </p>
          <p class="text-xs text-slate-400 leading-relaxed">
            The Catholic Church, guided by the Holy Spirit through the Council of Trent, dogmatically canonized both passages <em>cum omnibus suis partibus</em> ("entire with all their parts"). <strong>The Church does not derive her authority from the book; the book derives its canonical status from the Church!</strong>
          </p>
        </div>
      </div>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="mt-auto bg-slate-950 border-t border-slate-900 py-6 px-4 text-center text-xs text-slate-500">
    <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
        <span class="font-serif font-bold text-slate-300">History Proves Catholicism Research Suite</span>
      </div>
      <div>
        Built for Academic Textual Criticism, Manuscript Forensics & Catholic Apologetics
      </div>
    </div>
  </footer>

  <!-- ========================================== -->
  <!-- CLIENT-SIDE APP SCRIPT                     -->
  <!-- ========================================== -->
  <script>
    // Embedded Complete Dataset of 27 Loci
    const LOCI_DATA = {json_embedded};

    let currentCardLocusId = "matt-17-21";
    let currentCardMode = "youversion"; // "youversion" or "scholarly"
    let currentCategoryFilter = "ALL";

    // Initialize On Load
    document.addEventListener("DOMContentLoaded", () => {{
      populateLocusSelect();
      renderCard();
      renderLociList();
      lucide.createIcons();
    }});

    // 1. Populate Dropdown in Card Generator
    function populateLocusSelect() {{
      const select = document.getElementById("card-locus-select");
      select.innerHTML = "";
      LOCI_DATA.forEach(item => {{
        const opt = document.createElement("option");
        opt.value = item.id;
        opt.textContent = `${{item.ref}} — ${{item.title}}`;
        if (item.id === currentCardLocusId) opt.selected = true;
        select.appendChild(opt);
      }});
    }}

    function onCardLocusChange(val) {{
      currentCardLocusId = val;
      const locus = LOCI_DATA.find(x => x.id === val);
      if (locus) {{
        document.getElementById("discord-custom-comment").value = `Looking at ${{locus.ref}}: ${{locus.summary}}`;
        document.getElementById("discord-preview-comment").textContent = document.getElementById("discord-custom-comment").value;
      }}
      renderCard();
    }}

    function setCardMode(mode) {{
      currentCardMode = mode;
      const btnYV = document.getElementById("mode-youversion");
      const btnSch = document.getElementById("mode-scholarly");
      if (mode === "youversion") {{
        btnYV.className = "py-2 px-3 rounded-lg font-semibold bg-indigo-600 text-white transition text-center";
        btnSch.className = "py-2 px-3 rounded-lg font-medium text-slate-400 hover:text-white transition text-center";
      }} else {{
        btnSch.className = "py-2 px-3 rounded-lg font-semibold bg-indigo-600 text-white transition text-center";
        btnYV.className = "py-2 px-3 rounded-lg font-medium text-slate-400 hover:text-white transition text-center";
      }}
      renderCard();
    }}

    function updateDiscordComment(val) {{
      document.getElementById("discord-preview-comment").textContent = val;
    }}

    // 2. Render The Live Comparison Card
    function renderCard() {{
      const container = document.getElementById("capture-card");
      const locus = LOCI_DATA.find(x => x.id === currentCardLocusId) || LOCI_DATA[0];

      const transKeys = [
        "NKJV", "ESV", "NLT", "NIV", "DRB", "VULG", "KJV", "NASB", "RSVCE", "GREEK_TR"
      ];

      let html = "";

      transKeys.forEach((key, index) => {{
        const chk = document.getElementById(`chk-${{key}}`);
        if (!chk || !chk.checked) return;

        const transData = locus.translations[key];
        if (!transData) return;

        const isOmitted = transData.status.includes("OMITTED");
        const isBracketed = transData.status.includes("BRACKETED");
        const isFootnoted = transData.status.includes("FOOTNOTED");

        let borderClass = index > 0 ? "border-t border-[#2b2d31] pt-3.5" : "";

        html += `
          <div class="space-y-1.5 ${{borderClass}} font-sans">
            <!-- Header Row: Abbr left, Full Name right -->
            <div class="flex items-center justify-between text-xs">
              <span class="font-extrabold tracking-wide text-white font-mono text-[13px]">${{key}}</span>
              <span class="text-[#949ba4] text-[11px] font-medium">${{transData.name}}</span>
            </div>
        `;

        if (isOmitted) {{
          if (currentCardMode === "youversion") {{
            // Raw empty space exactly like the YouVersion screenshot!
            html += `
              <div class="h-6 flex items-center">
                <!-- Pure blank line like YouVersion compare -->
              </div>
            `;
          }} else {{
            // Scholarly explanation mode
            html += `
              <div class="p-2.5 rounded-lg bg-red-950/20 border border-red-500/20 text-xs">
                <span class="inline-flex items-center gap-1 font-bold text-red-400 font-mono text-[10px] tracking-wider uppercase mb-1">
                  [OMITTED FROM MAIN TEXT]
                </span>
                <p class="text-xs text-[#949ba4] italic">
                  ${{transData.footnote || "Relegated to critical footnote; text jumps directly to next verse."}}
                </p>
              </div>
            `;
          }}
        }} else {{
          // Verse Included / Bracketed
          const textClass = isBracketed ? "text-amber-200/90" : "text-[#f2f3f5]";
          html += `
            <div class="text-[14px] leading-relaxed font-serif ${{textClass}}">
              <sup class="text-[10px] font-bold text-[#949ba4] mr-1">${{locus.verse}}</sup>${{transData.text}}
            </div>
          `;
          if (currentCardMode === "scholarly" && (transData.footnote || isBracketed)) {{
            html += `
              <div class="text-[10px] text-[#949ba4] italic mt-0.5">
                Note: ${{transData.footnote || "Enclosed in brackets in critical editions."}}
              </div>
            `;
          }}
        }}

        html += `</div>`;
      }});

      container.innerHTML = html;
      lucide.createIcons();
    }}

    // 3. Render The Full Loci Catalog
    function renderLociList() {{
      const container = document.getElementById("loci-cards-container");
      container.innerHTML = "";

      let filtered = LOCI_DATA.filter(item => {{
        if (currentCategoryFilter === "ALL") return true;
        if (currentCategoryFilter === "CANONICAL_16") return item.is_canonical_16;
        return item.category === currentCategoryFilter;
      }});

      const query = document.getElementById("catalog-search").value.toLowerCase().trim();
      if (query) {{
        filtered = filtered.filter(item => {{
          return item.ref.toLowerCase().includes(query) ||
                 item.title.toLowerCase().includes(query) ||
                 item.summary.toLowerCase().includes(query) ||
                 JSON.stringify(item.manuscripts).toLowerCase().includes(query) ||
                 JSON.stringify(item.translations).toLowerCase().includes(query);
        }});
      }}

      if (filtered.length === 0) {{
        container.innerHTML = `
          <div class="p-12 text-center rounded-2xl bg-slate-900 border border-slate-800 text-slate-400">
            <i data-lucide="help-circle" class="w-8 h-8 mx-auto text-slate-500 mb-2"></i>
            <p class="font-semibold">No loci matching your filter.</p>
            <p class="text-xs text-slate-500 mt-1">Try resetting the search bar or category pills.</p>
          </div>
        `;
        lucide.createIcons();
        return;
      }}

      filtered.forEach(item => {{
        const card = document.createElement("div");
        card.className = "p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-5 hover:border-slate-700 transition";

        // Badges
        let statusBadge = item.is_canonical_16
          ? `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-red-500/10 text-red-400 border border-red-500/20">CANONICAL 16 OMISSION</span>`
          : `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">MAJOR CONTESTED LOCUS</span>`;

        card.innerHTML = `
          <!-- Card Header -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2">
                <span class="text-2xl font-bold font-serif text-white tracking-wide">${{item.ref}}</span>
                ${{statusBadge}}
                <span class="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">${{item.category}}</span>
              </div>
              <h4 class="text-sm font-semibold text-amber-400">${{item.title}}</h4>
            </div>

            <!-- Action buttons -->
            <div class="flex items-center gap-2 flex-shrink-0">
              <button onclick="loadIntoGenerator('${{item.id}}')" class="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-xs font-medium flex items-center gap-1.5 transition">
                <i data-lucide="image" class="w-3.5 h-3.5"></i>
                Load in Card Generator
              </button>
            </div>
          </div>

          <!-- Summary -->
          <p class="text-xs text-slate-300 leading-relaxed font-sans bg-slate-950/40 p-3 rounded-xl border border-slate-800/60">
            <strong>Forensic Summary:</strong> ${{item.summary}}
          </p>

          <!-- Parallel Translation Matrix Preview -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <!-- NKJV -->
            <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                  <span class="font-bold text-white">NKJV</span>
                  <span class="text-emerald-400 font-semibold text-[9px] bg-emerald-500/10 px-1.5 py-0.5 rounded">INCLUDED</span>
                </div>
                <div class="font-serif text-slate-200 text-xs leading-relaxed">
                  ${{item.translations.NKJV ? item.translations.NKJV.text : "N/A"}}
                </div>
              </div>
            </div>

            <!-- Douay-Rheims / Vulgate -->
            <div class="p-3.5 rounded-xl bg-slate-950 border border-amber-900/30 flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                  <span class="font-bold text-amber-400">DOUAY-RHEIMS (VULGATE)</span>
                  <span class="text-amber-300 font-semibold text-[9px] bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">CATHOLIC CANON</span>
                </div>
                <div class="font-serif text-slate-200 text-xs leading-relaxed">
                  ${{item.translations.DRB ? item.translations.DRB.text : "N/A"}}
                </div>
              </div>
            </div>

            <!-- ESV (Omitted) -->
            <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                  <span class="font-bold text-white">ESV (Critical Text)</span>
                  <span class="text-red-400 font-semibold text-[9px] bg-red-500/10 px-1.5 py-0.5 rounded">
                    ${{item.translations.ESV ? item.translations.ESV.status : "N/A"}}
                  </span>
                </div>
                <div class="text-xs text-slate-400 italic leading-relaxed">
                  ${{item.translations.ESV && item.translations.ESV.text ? item.translations.ESV.text : (item.translations.ESV ? item.translations.ESV.footnote : "Omitted from continuous text")}}
                </div>
              </div>
            </div>

            <!-- Greek TR vs NA28 -->
            <div class="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-col justify-between">
              <div>
                <div class="flex items-center justify-between text-[11px] font-mono text-slate-400 mb-1">
                  <span class="font-bold text-cyan-400">GREEK (TR / NA28)</span>
                  <span class="text-cyan-300 text-[9px]">ORIGINAL</span>
                </div>
                <div class="font-greek text-slate-300 text-xs leading-relaxed">
                  ${{item.translations.GREEK_TR ? item.translations.GREEK_TR.text : "N/A"}}
                </div>
              </div>
            </div>
          </div>

          <!-- Expandable Deep Apparatus Drawer -->
          <details class="group bg-slate-950/80 rounded-xl border border-slate-800 p-4 transition-all">
            <summary class="cursor-pointer text-xs font-semibold text-amber-400 flex items-center justify-between select-none">
              <span class="flex items-center gap-2">
                <i data-lucide="microscope" class="w-4 h-4"></i>
                Expand Forensic Manuscript Matrix & Patristic Citations
              </span>
              <span class="text-[10px] text-slate-500 group-open:rotate-180 transition-transform">▼</span>
            </summary>

            <div class="pt-4 mt-3 border-t border-slate-800/80 space-y-4 text-xs">
              <!-- Manuscripts Table -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-3 rounded-lg bg-red-950/15 border border-red-500/20">
                  <div class="font-mono text-[11px] font-bold text-red-400 mb-1 flex items-center gap-1.5">
                    <i data-lucide="x-circle" class="w-3.5 h-3.5"></i>
                    Manuscripts Omitting (${{item.manuscripts.omitted_by.length}}):
                  </div>
                  <ul class="list-disc list-inside space-y-0.5 text-slate-300 text-[11px]">
                    ${{item.manuscripts.omitted_by.map(m => `<li>${{m}}</li>`).join('')}}
                  </ul>
                </div>

                <div class="p-3 rounded-lg bg-emerald-950/15 border border-emerald-500/20">
                  <div class="font-mono text-[11px] font-bold text-emerald-400 mb-1 flex items-center gap-1.5">
                    <i data-lucide="check-circle" class="w-3.5 h-3.5"></i>
                    Manuscripts Including (${{item.manuscripts.included_by.length}}):
                  </div>
                  <ul class="list-disc list-inside space-y-0.5 text-slate-300 text-[11px]">
                    ${{item.manuscripts.included_by.map(m => `<li>${{m}}</li>`).join('')}}
                  </ul>
                </div>
              </div>

              <!-- Patristic Citations -->
              <div class="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <div class="font-mono text-[11px] font-bold text-amber-300 mb-1.5 flex items-center gap-1.5">
                  <i data-lucide="feather" class="w-3.5 h-3.5"></i>
                  Church Fathers & Early Patristic Citations:
                </div>
                <ul class="space-y-1 text-slate-300 text-[11px]">
                  ${{item.patristic_citations.map(p => `<li class="flex items-start gap-2"><span class="text-amber-500 mt-0.5">•</span><span>${{p}}</span></li>`).join('')}}
                </ul>
              </div>

              <!-- Textual Criticism & Catholic Defense -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                  <div class="font-mono text-[11px] font-bold text-blue-300 mb-1">Critical Text Hypothesis (Westcott-Hort / NA28):</div>
                  <p class="text-slate-300 text-[11px] leading-relaxed">${{item.textual_criticism.critical_theory}}</p>
                </div>
                <div class="p-3 rounded-lg bg-slate-900/60 border border-amber-900/30">
                  <div class="font-mono text-[11px] font-bold text-amber-400 mb-1">Traditional & Catholic Defense (Vulgate / Trent):</div>
                  <p class="text-slate-300 text-[11px] leading-relaxed">${{item.textual_criticism.traditional_catholic_defense}}</p>
                </div>
              </div>

              <!-- Theological Impact -->
              <div class="p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/20">
                <div class="font-mono text-[11px] font-bold text-indigo-300 mb-1">Dogmatic & Theological Significance:</div>
                <p class="text-slate-300 text-[11px] leading-relaxed">${{item.textual_criticism.theological_impact}}</p>
              </div>
            </div>
          </details>
        `;

        container.appendChild(card);
      }});

      lucide.createIcons();
    }}

    function filterLoci() {{
      renderLociList();
    }}

    function setCategoryFilter(cat) {{
      currentCategoryFilter = cat;
      document.querySelectorAll(".cat-pill").forEach(btn => {{
        if (btn.getAttribute("data-cat") === cat) {{
          btn.className = "cat-pill active px-3.5 py-1.5 rounded-lg bg-amber-500 text-slate-950 font-bold transition flex-shrink-0";
        }} else {{
          btn.className = "cat-pill px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 font-medium transition flex-shrink-0";
        }}
      }});
      renderLociList();
    }}

    function loadIntoGenerator(id) {{
      currentCardLocusId = id;
      document.getElementById("card-locus-select").value = id;
      const locus = LOCI_DATA.find(x => x.id === id);
      if (locus) {{
        document.getElementById("discord-custom-comment").value = `Looking at ${{locus.ref}}: ${{locus.summary}}`;
        document.getElementById("discord-preview-comment").textContent = document.getElementById("discord-custom-comment").value;
      }}
      renderCard();
      document.getElementById("discord-generator").scrollIntoView({{ behavior: "smooth" }});
    }}

    // 4. Download Card as PNG Image (Pure Client-side SVG Canvas Rendering)
    function downloadCardPNG() {{
      const element = document.getElementById("discord-mockup-wrapper");
      htmlToCanvas(element, (canvas) => {{
        const link = document.createElement("a");
        link.download = `${{currentCardLocusId.toUpperCase()}}_Comparison_Card.png`;
        link.href = canvas.toDataURL("image/png");
        link.click();
      }});
    }}

    // 5. Copy Image to Clipboard
    function copyCardAsImage() {{
      const element = document.getElementById("discord-mockup-wrapper");
      const btn = document.getElementById("btn-copy-card-img");
      const origText = btn.innerHTML;
      btn.innerHTML = `<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i> Copying...`;
      lucide.createIcons();

      htmlToCanvas(element, (canvas) => {{
        canvas.toBlob((blob) => {{
          if (navigator.clipboard && window.ClipboardItem) {{
            const item = new ClipboardItem({{ "image/png": blob }});
            navigator.clipboard.write([item]).then(() => {{
              btn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5 text-white"></i> Copied to Clipboard!`;
              lucide.createIcons();
              setTimeout(() => {{ btn.innerHTML = origText; lucide.createIcons(); }}, 2500);
            }}).catch(err => {{
              alert("Could not copy automatically. You can download the PNG instead!");
              btn.innerHTML = origText;
              lucide.createIcons();
            }});
          }} else {{
            alert("ClipboardItem API not supported in your browser; use Download PNG!");
            btn.innerHTML = origText;
            lucide.createIcons();
          }}
        }});
      }});
    }}

    // 6. Copy Discord Markdown Block
    function copyDiscordMarkdown() {{
      const locus = LOCI_DATA.find(x => x.id === currentCardLocusId) || LOCI_DATA[0];
      const comment = document.getElementById("discord-custom-comment").value;
      
      let md = `${{comment}}\n\n`;
      md += `**${{locus.ref}} — Translation Comparison**\n`;
      md += `\`\`\`diff\n`;
      md += `+ NKJV: "${{locus.translations.NKJV ? locus.translations.NKJV.text : ''}}"\n`;
      md += `- ESV:  ${{locus.translations.ESV.text ? `"${{locus.translations.ESV.text}}"` : '[OMITTED FROM MAIN TEXT]'}}\n`;
      md += `- NLT:  ${{locus.translations.NLT.text ? `"${{locus.translations.NLT.text}}"` : '[OMITTED FROM MAIN TEXT]'}}\n`;
      md += `- NIV:  ${{locus.translations.NIV.text ? `"${{locus.translations.NIV.text}}"` : '[OMITTED FROM MAIN TEXT]'}}\n`;
      md += `+ DRB:  "${{locus.translations.DRB ? locus.translations.DRB.text : ''}}" (Catholic Vulgate)\n`;
      md += `\`\`\`\n`;
      md += `*Manuscript Attestation: Omitted by Codex Sinaiticus & Vaticanus; Preserved in Codex Bezae, Old Latin, and Latin Vulgate.*`;

      navigator.clipboard.writeText(md).then(() => {{
        const btn = document.getElementById("btn-copy-discord-text");
        const orig = btn.innerHTML;
        btn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400"></i> Copied Markdown!`;
        lucide.createIcons();
        setTimeout(() => {{ btn.innerHTML = orig; lucide.createIcons(); }}, 2500);
      }});
    }}

    // Lightweight Standalone HTML to Canvas Converter using SVG foreignObject
    function htmlToCanvas(element, callback) {{
      const width = element.offsetWidth;
      const height = element.offsetHeight;

      const clone = element.cloneNode(true);
      // Ensure all styles are computed or embedded
      const serialized = new XMLSerializer().serializeToString(clone);

      const svgString = `
        <svg xmlns="http://www.w3.org/2000/svg" width="${{width}}" height="${{height}}">
          <foreignObject width="100%" height="100%">
            <div xmlns="http://www.w3.org/1999/xhtml" style="font-family: 'Inter', system-ui, sans-serif;">
              ${{serialized}}
            </div>
          </foreignObject>
        </svg>
      `;

      const img = new Image();
      const svgBlob = new Blob([svgString], {{ type: "image/svg+xml;charset=utf-8" }});
      const url = URL.createObjectURL(svgBlob);

      img.onload = () => {{
        const canvas = document.createElement("canvas");
        canvas.width = width * 2; // Retina scale
        canvas.height = height * 2;
        const ctx = canvas.getContext("2d");
        ctx.scale(2, 2);
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        callback(canvas);
      }};

      img.onerror = () => {{
        // Fallback: draw basic canvas if SVG rendering blocked
        const canvas = document.createElement("canvas");
        canvas.width = 600;
        canvas.height = 400;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#1e1f22";
        ctx.fillRect(0, 0, 600, 400);
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 16px Inter, sans-serif";
        ctx.fillText("Card Rendered (Save directly or copy text)", 30, 50);
        callback(canvas);
      }};

      img.src = url;
    }}
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    generate_json_and_html()
