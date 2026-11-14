"""
theological_revision_detector.py -- BibCrit-Style Theological Revision & Tendenz Engine.
Part of Plenary Logos Suite & Catholic Jarvis Suite.

Analyzes and categorizes theological and ideological alterations across biblical manuscripts:
1. Tiqqun Soferim (the 18 classical rabbinic Scribal Emendations in the Masorah Magna)
2. Anti-Anthropomorphic Euphemisms (Targumic and Septuagintal filters)
3. Anti-Polytheism / Divine Council Softening (suppression of 'sons of El' / subordinate deities)
4. Anti-Baal Euphemisms (Bosheth substitutions for Baal in the Deuteronomistic History)
5. Anti-Samaritan / Sectarian Polemical Shifts (Gerizim vs Ebal, 10th Commandment)
6. Messianic Tendenz Alterations (Rabbinic vs Early Christian variant trajectories)

Zero external runtime calls, 100% offline JSON compilation.
"""

import json
import os
from typing import Dict, List, Any

_HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES_CACHE = os.path.join(_HERE, "sources_cache")
OUTPUT_JSON = os.path.join(SOURCES_CACHE, "theological_revisions_catalog.json")

REVISION_RECORDS: List[Dict[str, Any]] = [
    {
        "id": "TIQQUN_GEN_18_22",
        "locus": "Genesis 18:22",
        "category": "Tiqqun Soferim (Scribal Emendation)",
        "subtype": "Honorific Reversal / Avoidance of Divine Subservience",
        "title": "Abraham Standing Before Yahweh vs Yahweh Standing Before Abraham",
        "masoretic_reading": {
            "hebrew": "וְאַבְרָהָם עוֹדֶנּוּ עֹמֵד לִפְנֵי יְהוָה",
            "translation": "but Abraham still stood before the LORD",
            "masorah_note": "Tiqqun Soferim #1 recorded in Masorah Magna at Num 11:15 and Bereshit Rabbah 49:7"
        },
        "original_reading": {
            "hebrew": "וַיהוָה עוֹדֶנּוּ עֹמֵד לִפְנֵי אַבְרָהָם",
            "translation": "and the LORD was still standing before Abraham",
            "attestation": "Explicitly admitted by the Masoretes themselves as the original text before their correction"
        },
        "scribal_rationale": "In ancient Near Eastern court protocol, an inferior servant stands before a superior master. The original narrative had Yahweh standing before Abraham waiting for Abraham's intercession for Sodom. Early scribes deemed it blasphemous for the Creator to stand waiting before a mortal, and reversed the subject to 'Abraham stood before the LORD'.",
        "theological_impact": "Masks the radical humility and condescension of God in the narrative of patriarchal intercession."
    },
    {
        "id": "TIQQUN_ZECH_2_12",
        "locus": "Zechariah 2:12 (ET 2:8)",
        "category": "Tiqqun Soferim (Scribal Emendation)",
        "subtype": "Anatomical Euphemism",
        "title": "The Apple of His Eye vs The Apple of My Eye",
        "masoretic_reading": {
            "hebrew": "הַנֹּגֵעַ בָּכֶם נֹגֵעַ בְּבָבַת עֵינוֹ",
            "translation": "he who touches you touches the apple of his [own] eye",
            "masorah_note": "Tiqqun Soferim recorded in Mekhilta de-Rabbi Ishmael, Shirata 6"
        },
        "original_reading": {
            "hebrew": "הַנֹּגֵעַ בָּכֶם נֹגֵעַ בְּבָבַת עֵינִי",
            "translation": "he who touches you touches the apple of MY eye [God's eye]",
            "attestation": "Masorah Magna, Sifre Numbers 84"
        },
        "scribal_rationale": "God is speaking in the first person ('for thus said the Lord of hosts...'). The original text read 'touches the apple of my eye' (עֵינִי), indicating that harming Israel harms God Himself. Scribes changed the 1st person suffix yod to 3rd person vav ('his eye') to avoid attributing vulnerability or physical harm to God's eye.",
        "theological_impact": "Weakens the intense divine empathy where persecuting Israel is an assault on God's own person."
    },
    {
        "id": "TIQQUN_JOB_7_20",
        "locus": "Job 7:20",
        "category": "Tiqqun Soferim (Scribal Emendation)",
        "subtype": "Avoidance of Divine Burden",
        "title": "A Burden to Myself vs A Burden to You",
        "masoretic_reading": {
            "hebrew": "לָמָה שַׂמְתַּנִי לְמִפְגָּע לָךְ וָאֶהְיֶה עָלַי לְמַשָּׂא",
            "translation": "Why have you made me your target? Why have I become a burden to myself?",
            "masorah_note": "Tiqqun Soferim #10 in the Masoretic lists"
        },
        "original_reading": {
            "hebrew": "וָאֶהְיֶה עָלֶיךָ לְמַשָּׂא",
            "translation": "so that I have become a burden unto YOU [God]?",
            "attestation": "LXX (εἰμὶ δὲ ἐπὶ σοὶ φορτίον), Masoretic notes"
        },
        "scribal_rationale": "In his agony, Job asks God why He treats him as an enemy and whether Job has become a burden to God ('āleykā). Scribes emended 'āleykā ('upon you') to 'ālay ('upon myself') to prevent the implication that a mortal human could burden the Almighty.",
        "theological_impact": "Dulls Job's daring challenge to divine sovereignty; the Septuagint faithfully preserves the original daring address."
    },
    {
        "id": "TIQQUN_HAB_1_12",
        "locus": "Habakkuk 1:12",
        "category": "Tiqqun Soferim (Scribal Emendation)",
        "subtype": "Avoidance of Divine Mortality",
        "title": "We Shall Not Die vs You Shall Not Die",
        "masoretic_reading": {
            "hebrew": "הֲלוֹא אַתָּה מִקֶּדֶם יְהוָה אֱלֹהַי קְדֹשִׁי לֹא נָמוּת",
            "translation": "Are you not from everlasting, O LORD my God, my Holy One? We shall not die.",
            "masorah_note": "Tiqqun Soferim recorded in Tanhuma, Beshallah 16"
        },
        "original_reading": {
            "hebrew": "לֹא תָמוּת",
            "translation": "You [O God] do not die! / You never die!",
            "attestation": "Masorah, Midrash Tanhuma, some Greek minuscules"
        },
        "scribal_rationale": "The prophet's original exclamation praised God's immortality: 'O LORD my God, my Holy One, You never die!' Scribes feared that juxtaposing the concept of 'death' with the Holy One was improper, even with a negative particle ('lo tamut'), so they changed the 2nd person singular 'ta-mut' to 1st person plural 'na-mut' ('we shall not die').",
        "theological_impact": "Alters a direct philosophical assertion of God's eternal immortality into an anthropocentric petition for Israel's survival."
    },
    {
        "id": "EUPH_BOSHETH_SUBST",
        "locus": "2 Samuel 2:8, 4:4; 1 Chron 8:33, 9:39",
        "category": "Anti-Baal Euphemism (Cacophemism)",
        "subtype": "Onomastic Censorship",
        "title": "Ish-Bosheth for Esh-Baal & Mephibosheth for Merib-Baal",
        "masoretic_reading": {
            "hebrew": "אִישׁ בֹּשֶׁת (Ish-bosheth = 'Man of Shame'), מְפִיבֹשֶׁת (Mephibosheth = 'From the mouth of shame')",
            "translation": "Ish-bosheth, Mephibosheth",
            "masorah_note": "Consistent replacement throughout 2 Samuel"
        },
        "original_reading": {
            "hebrew": "אֶשְׁבַּעַל ('Eshba'al = 'Man of Baal/Lord'), מְרִיב בַּעַל (Məriv-ba'al = 'Baal contends')",
            "translation": "Eshbaal, Meribbaal",
            "attestation": "1 Chronicles 8:33, 9:39, 9:40; LXX Lucianic recension (Ιεσβααλ, Μεμφιβααλ)"
        },
        "scribal_rationale": "In early Israel, the noun 'Baal' simply meant 'Master' or 'Lord' and was applied legitimately as an epithet of Yahweh (cf. Hos 2:16). After the Tyrian Baal crises of Jezebel and the prophetic polemics, the name Baal became odious. Scribes copying 1-2 Samuel systematically substituted 'Bosheth' (בֹּשֶׁת, 'shame') for 'Baal'. The Chronicler, copying centuries later from un-emended archives, innocently preserved the original names Eshbaal and Meribbaal.",
        "theological_impact": "Conceals the linguistic history of early Israelite onomastics and the gradual purification of the divine lexicon."
    },
    {
        "id": "SECT_GERIZIM_TENTH_CMD",
        "locus": "Exodus 20:17 / Deuteronomy 5:21",
        "category": "Sectarian Theological Expansion",
        "subtype": "Samaritan Sanctuary Mandate",
        "title": "The Samaritan Tenth Commandment (Sanctuary at Mount Gerizim)",
        "masoretic_reading": {
            "hebrew": "Decalogue ends at Exod 20:17 with prohibition against coveting neighbor's house/wife.",
            "translation": "10 commandments conclude with prohibition of coveting.",
            "masorah_note": "Proto-MT standard text"
        },
        "original_reading": {
            "hebrew": "And it shall be when the Lord your God brings you into the land... you shall set up these stones on Mount Gerizim... and build there an altar to the Lord your God",
            "translation": "Appends an entire paragraph after the 10th commandment obligating sacrifice on Mount Gerizim",
            "attestation": "Samaritan Pentateuch (SP), Samaritan Decalogue Inscriptions"
        },
        "scribal_rationale": "The Samaritans regarded the Decalogue as having exactly ten words/commandments. To establish Mount Gerizim as the only legitimate place of divine worship, they combined the first two commandments into one, and inserted a new 10th commandment compiling Deut 11:29 and 27:2-7 requiring the building of the altar on Mount Gerizim.",
        "theological_impact": "The ultimate example of sectarian tendenz rewriting the foundational constitutional text of Israelite covenant law."
    },
    {
        "id": "POLY_DEUT_32_8_DIVINE_COUNCIL",
        "locus": "Deuteronomy 32:8-9",
        "category": "Anti-Polytheism / Divine Council Attenuation",
        "subtype": "Subordinate Deities to Human Tribes",
        "title": "Sons of God Substituted by Sons of Israel",
        "masoretic_reading": {
            "hebrew": "יַצֵּב גְּבֻלֹת עַמִּים לְמִסְפַּר בְּנֵי יִשְׂרָאֵל",
            "translation": "he set the bounds of the people according to the number of the children of Israel",
            "masorah_note": "BHS / Codex Leningradensis"
        },
        "original_reading": {
            "hebrew": "למספר בני אל / בני אלוהים",
            "translation": "according to the number of the sons of God / sons of El",
            "attestation": "4QDeut-j, 4QDeut-q, LXX (ἀγγέλων θεοῦ / υἱῶν θεοῦ)"
        },
        "scribal_rationale": "The ancient poetic worldview depicted the supreme deity (Elyon) allotting the Gentile nations among the heavenly sons of God, reserving Jacob as Yahweh's own portion. Monotheistic scribes of the late Second Temple era eliminated the divine council to protect absolute monotheism, converting the 'sons of God' into the 70 'sons of Israel'.",
        "theological_impact": "Conceals the biblical theology of the cosmic divine council and Gentile angelic oversight (cf. Dan 10, Psalm 82)."
    },
    {
        "id": "TEND_MESSIANIC_PS_110_3",
        "locus": "Psalm 110:3",
        "category": "Messianic Tendenz & Vocalization Variance",
        "subtype": "Eternal Divine Begetting vs Dawn Youth",
        "title": "From the Womb of the Dawn I Begot You vs Dew of Your Youth",
        "masoretic_reading": {
            "hebrew": "מֵרֶחֶם מִשְׁחָר לְךָ טַל יַלְדֻתֶךָ",
            "transliteration": "mēreḥem mišḥār ləkā ṭal yaldūtekā",
            "translation": "from the womb of the dawn, yours is the dew of your youth",
            "masorah_note": "Vocalized with pointing in the 9th-10th century AD Masoretic academies"
        },
        "original_reading": {
            "hebrew": "מֵרֶחֶם מִשְׁחָר יְלִדְתִּיךָ",
            "transliteration": "mēreḥem mišḥār yəlīdtīkā",
            "translation": "from the womb before the morning star I have begotten you",
            "attestation": "LXX Ps 109:3 (ἐκ γαστρὸς πρὸ ἑωσφόρου ἐξεγέννησά σε), Vulgate (ex utero ante luciferum genui te), Old Latin, Peshitta"
        },
        "scribal_rationale": "In the unpointed Hebrew consonantal text, יַלְדֻתֶךָ (yaldūtekā, 'your youth') and יְלִדְתִּיךָ (yəlīdtīkā, 'I have begotten you', identical to Ps 2:7) share identical root consonants. The ancient Septuagint and Latin witnesses read the verbal form 'I have begotten you', which became a primary Patristic prooftext for the eternal generation of the Son (the Logos begotten of the Father before the cosmos). Later Masoretic vocalization vocalized the consonants as a noun ('your youth') to neutralize Christian trinitarian exegesis.",
        "theological_impact": "Directly impacts the doctrine of the eternal generation of Christ from the Father before all worlds (Nicene Creed)."
    }
]


def build_theological_revisions_catalog() -> Dict[str, Any]:
    os.makedirs(SOURCES_CACHE, exist_ok=True)
    catalog = {
        "title": "BibCrit Theological Revision & Manuscript Tendenz Database",
        "version": "1.0.0",
        "engine": "Plenary Logos Suite / Catholic Jarvis",
        "total_revisions": len(REVISION_RECORDS),
        "taxonomies": [
            "Tiqqun Soferim (Masoretic Emendations of the Scribes)",
            "Anti-Anthropomorphic Euphemisms",
            "Anti-Polytheism / Divine Council Censorship",
            "Anti-Baal Euphemisms (Bosheth Subsitutions)",
            "Sectarian Polemical Additions & Emendations",
            "Messianic Vocalization Alterations"
        ],
        "entries": REVISION_RECORDS
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"[Theological Revision Detector] Wrote {len(REVISION_RECORDS)} records to {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON):,} bytes)")
    return catalog


if __name__ == "__main__":
    build_theological_revisions_catalog()
