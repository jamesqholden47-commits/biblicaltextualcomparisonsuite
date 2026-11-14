"""
biblical_chiasm_engine.py -- BibCrit-Style Concentric Literary & Chiastic Structure Engine.
Part of Plenary Logos Suite & Catholic Jarvis Suite.

Analyzes, classifies, and visualizes inverted parallelisms (chiasms, palistrophes,
ring compositions) across Hebrew and Greek biblical pericopes. Each structure features
mirrored correspondences (A - B - C ... X ... C' - B' - A'), centering on the thematic
and theological apex of the passage.

Cites foundational structural scholarship:
- Gordon J. Wenham, "The Coherence of the Flood Narrative" (Vetus Testamentum 28, 1978)
- J.P. Fokkelman, Narrative Art in Genesis (Van Gorcum 1975)
- R. Alan Culpepper, "The Pivot of John's Prologue" (NTS 27, 1980)
- Nils W. Lund, Chiasmus in the New Testament (UNC Press 1942)

100% offline, zero runtime calls.
"""

import json
import os
from typing import Dict, List, Any

_HERE = os.path.dirname(os.path.abspath(__file__))
SOURCES_CACHE = os.path.join(_HERE, "sources_cache")
OUTPUT_JSON = os.path.join(SOURCES_CACHE, "biblical_chiasms_catalog.json")

CHIASM_RECORDS: List[Dict[str, Any]] = [
    {
        "id": "CHIASM_GEN_FLOOD",
        "title": "The Great Flood Palistrophe (Wenham's 31-Point Ring Composition)",
        "locus": "Genesis 6:10 - 9:19",
        "pericope": "Noah and the Deluge",
        "center_verse": "Genesis 8:1a",
        "center_text": "וַיִּזְכֹּר אֱלֹהִים אֶת־נֹחַ (\"And God remembered Noah\")",
        "center_theology": "The exact grammatical and thematic apex of the entire Flood narrative: God's covenantal memory of Noah turns the catastrophe of un-creation into the recreation of the cosmos.",
        "scholar": "Gordon J. Wenham (Vetus Testamentum 28, 1978, pp. 336-348)",
        "levels": [
            {"label": "A", "ref": "Gen 6:10", "summary": "Noah and his three sons: Shem, Ham, Japheth"},
            {"label": "B", "ref": "Gen 6:11-12", "summary": "All flesh corrupted on earth; violence fills the world"},
            {"label": "C", "ref": "Gen 6:13-22", "summary": "Divine resolution to destroy; command to build the ark and preserve covenant"},
            {"label": "D", "ref": "Gen 7:1-9", "summary": "Command to enter ark with 7 pairs of clean beasts and 1 pair of unclean"},
            {"label": "E", "ref": "Gen 7:10-16", "summary": "7 days wait; floodwaters break forth; Yahweh shuts the door"},
            {"label": "F", "ref": "Gen 7:17-24", "summary": "Rising waters prevail 40 days and 150 days; all mountains covered, all breath dies"},
            {"label": "CENTER (X)", "ref": "Gen 8:1a", "summary": "AND GOD REMEMBERED NOAH and all the beasts and cattle with him in the ark", "is_apex": True},
            {"label": "F'", "ref": "Gen 8:1b-5", "summary": "God causes wind to pass; fountains shut; waters recede after 150 days; mountain peaks appear"},
            {"label": "E'", "ref": "Gen 8:6-14", "summary": "After 40 days Noah opens window; sends raven and dove; 7 days intervals; earth dries"},
            {"label": "D'", "ref": "Gen 8:15-19", "summary": "Command to go forth from the ark with every living thing to multiply on earth"},
            {"label": "C'", "ref": "Gen 8:20-22", "summary": "Noah builds altar; soothing aroma; God promises never again to strike all life"},
            {"label": "B'", "ref": "Gen 9:1-17", "summary": "God blesses Noah; sanctity of blood and life; Everlasting Covenant with earth (Rainbow)"},
            {"label": "A'", "ref": "Gen 9:18-19", "summary": "Noah's sons who went forth: Shem, Ham, Japheth; from these the whole earth was populated"}
        ]
    },
    {
        "id": "CHIASM_GEN_BABEL",
        "title": "The Tower of Babel Inverted Parallelism",
        "locus": "Genesis 11:1-9",
        "pericope": "The Dispersion of Nations",
        "center_verse": "Genesis 11:5",
        "center_text": "וַיֵּרֶד יְהוָה לִרְאֹת אֶת־הָעִיר וְאֶת־הַמִּגְדָּל (\"And the LORD came down to see the city and the tower\")",
        "center_theology": "Devastating divine irony: man's supreme monumental architecture aimed at reaching the heavens is so minuscule that the transcendent Creator must 'come down' just to see it.",
        "scholar": "J.P. Fokkelman (Narrative Art in Genesis, 1975)",
        "levels": [
            {"label": "A", "ref": "Gen 11:1", "summary": "The whole earth had one language (שָׂפָה אֶחָת) and the same words"},
            {"label": "B", "ref": "Gen 11:2", "summary": "They migrated from the east and settled in a plain in the land of Shinar"},
            {"label": "C", "ref": "Gen 11:3", "summary": "Human technology: 'Come, let us make bricks and burn them thoroughly'"},
            {"label": "D", "ref": "Gen 11:4", "summary": "'Come, let us build a city and a tower with its top in the heavens, and let us make a name for ourselves, lest we be scattered'"},
            {"label": "CENTER (X)", "ref": "Gen 11:5", "summary": "AND THE LORD CAME DOWN to see the city and the tower which the children of man had built", "is_apex": True},
            {"label": "D'", "ref": "Gen 11:6", "summary": "The Lord assesses human hubris: 'Behold, they are one people... nothing they propose will be impossible'"},
            {"label": "C'", "ref": "Gen 11:7", "summary": "Divine counter-decree: 'Come, let us go down and there confuse their language'"},
            {"label": "B'", "ref": "Gen 11:8", "summary": "The Lord scattered them abroad over the face of all the earth; they ceased building the city"},
            {"label": "A'", "ref": "Gen 11:9", "summary": "Name called Babel (confusion), for there the Lord confused the language of the whole earth"}
        ]
    },
    {
        "id": "CHIASM_JOHN_PROLOGUE",
        "title": "The Johannine Prologue Ring Composition",
        "locus": "John 1:1-18",
        "pericope": "Incarnation of the Divine Logos",
        "center_verse": "John 1:12-13",
        "center_text": "τέκνα θεοῦ γενέσθαι, τοῖς πιστεύουσιν εἰς τὸ ὄνομα αὐτοῦ (\"to become children of God, to those who believe in His name\")",
        "center_theology": "The structural and theological core of the Fourth Gospel: the entire descent of the Logos (katabasis) and ascent (anabasis) exists to effect divine filiation (theosis / adoption as sons of God) for believers.",
        "scholar": "R. Alan Culpepper (NTS 27, 1980) & Raymond E. Brown (Anchor Bible)",
        "levels": [
            {"label": "A", "ref": "John 1:1-2", "summary": "The Word in the beginning with God (πρὸς τὸν θεόν); the Word was God; eternal pre-existence"},
            {"label": "B", "ref": "John 1:3-5", "summary": "Cosmic creation through the Word; Life was the Light of men; Light shines in darkness"},
            {"label": "C", "ref": "John 1:6-8", "summary": "The historical witness: John the Baptist sent from God to bear witness to the Light"},
            {"label": "D", "ref": "John 1:9-11", "summary": "The True Light coming into the world; in the world He made, yet His own people did not receive Him"},
            {"label": "CENTER (X)", "ref": "John 1:12-13", "summary": "BUT TO ALL WHO RECEIVED HIM, HE GAVE POWER TO BECOME CHILDREN OF GOD, born not of blood nor will of the flesh, but of God", "is_apex": True},
            {"label": "D'", "ref": "John 1:14", "summary": "The Word became flesh and tabernacled among us, and we beheld His glory, glory as of the Only-Begotten"},
            {"label": "C'", "ref": "John 1:15", "summary": "John's public testimony: 'He who comes after me ranks before me, for He was before me'"},
            {"label": "B'", "ref": "John 1:16-17", "summary": "From His fullness we have all received grace upon grace; Law through Moses, grace and truth through Christ"},
            {"label": "A'", "ref": "John 1:18", "summary": "No one has seen God at any time; the Only-Begotten God (μονογενὴς θεός) in the bosom of the Father has revealed Him"}
        ]
    },
    {
        "id": "CHIASM_PSALM_23",
        "title": "Psalm 23 (The Shepherd and Host Chiasm)",
        "locus": "Psalm 23:1-6",
        "pericope": "Confidence in Divine Guidance",
        "center_verse": "Psalm 23:4",
        "center_text": "כִּי־אַתָּה עִמָּדִי שִׁבְטְךָ וּמִשְׁעַנְתֶּךָ הֵמָּה יְנַחֲמֻנִי (\"For You are with me; Your rod and Your staff, they comfort me\")",
        "center_theology": "Shift from talking ABOUT God in the 3rd person ('He makes me lie down') to talking TO God in the intimate 2nd person ('You are with me') precisely when entering the valley of deep shadow.",
        "scholar": "David Noel Freedman & J. Kenneth Kuntz",
        "levels": [
            {"label": "A", "ref": "Ps 23:1", "summary": "Yahweh is my shepherd; I shall not want (total sufficiency)"},
            {"label": "B", "ref": "Ps 23:2-3a", "summary": "Green pastures, still waters, restores soul (refreshment and peace)"},
            {"label": "C", "ref": "Ps 23:3b", "summary": "He leads me in paths of righteousness for His name's sake"},
            {"label": "CENTER (X)", "ref": "Ps 23:4", "summary": "EVEN THOUGH I WALK THROUGH THE VALLEY OF THE SHADOW OF DEATH, I WILL FEAR NO EVIL, FOR YOU ARE WITH ME; YOUR ROD AND STAFF COMFORT ME", "is_apex": True},
            {"label": "C'", "ref": "Ps 23:5a", "summary": "You prepare a table before me in the presence of my enemies"},
            {"label": "B'", "ref": "Ps 23:5b", "summary": "You anoint my head with oil; my cup overflows (banquet abundance)"},
            {"label": "A'", "ref": "Ps 23:6", "summary": "Surely goodness and mercy shall follow me, and I shall dwell in the house of Yahweh forever (eternal communion)"}
        ]
    },
    {
        "id": "CHIASM_BEATITUDES",
        "title": "The Eight Beatitudes Concentric Structure",
        "locus": "Matthew 5:3-10",
        "pericope": "Sermon on the Mount - Kingdom Constitution",
        "center_verse": "Matthew 5:6-7",
        "center_text": "Hunger and Thirst for Righteousness / The Merciful",
        "center_theology": "Righteousness (dikaiosyne) and Mercy (eleos) stand at the center: the inner desire for God's holiness mirrored immediately by external compassion toward humanity.",
        "scholar": "Nils W. Lund (Chiasmus in the NT) & Ulrich Luz",
        "levels": [
            {"label": "A", "ref": "Matt 5:3", "summary": "Blessed are the poor in spirit: FOR THEIRS IS THE KINGDOM OF HEAVEN (present possession)"},
            {"label": "B", "ref": "Matt 5:4", "summary": "Blessed are those who mourn, for they shall be comforted"},
            {"label": "C", "ref": "Matt 5:5", "summary": "Blessed are the meek, for they shall inherit the earth"},
            {"label": "D (CENTER 1)", "ref": "Matt 5:6", "summary": "BLESSED ARE THOSE WHO HUNGER AND THIRST FOR RIGHTEOUSNESS, FOR THEY SHALL BE SATISFIED", "is_apex": True},
            {"label": "D' (CENTER 2)", "ref": "Matt 5:7", "summary": "BLESSED ARE THE MERCIFUL, FOR THEY SHALL RECEIVE MERCY", "is_apex": True},
            {"label": "C'", "ref": "Matt 5:8", "summary": "Blessed are the pure in heart, for they shall see God"},
            {"label": "B'", "ref": "Matt 5:9", "summary": "Blessed are the peacemakers, for they shall be called sons of God"},
            {"label": "A'", "ref": "Matt 5:10", "summary": "Blessed are those persecuted for righteousness' sake: FOR THEIRS IS THE KINGDOM OF HEAVEN (inclusio bookend)"}
        ]
    }
]


def build_biblical_chiasms_catalog() -> Dict[str, Any]:
    os.makedirs(SOURCES_CACHE, exist_ok=True)
    catalog = {
        "title": "BibCrit Biblical Chiasm & Ring Composition Visualizer Engine",
        "version": "1.0.0",
        "engine": "Plenary Logos Suite / Catholic Jarvis",
        "total_chiasms": len(CHIASM_RECORDS),
        "scholarship": [
            "Gordon J. Wenham, 'The Coherence of the Flood Narrative' (VT 28, 1978)",
            "J.P. Fokkelman, Narrative Art in Genesis (1975)",
            "R. Alan Culpepper, 'The Pivot of John's Prologue' (NTS 27, 1980)",
            "Nils W. Lund, Chiasmus in the New Testament (1942)"
        ],
        "entries": CHIASM_RECORDS
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"[Biblical Chiasm Engine] Wrote {len(CHIASM_RECORDS)} chiasms to {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON):,} bytes)")
    return catalog


if __name__ == "__main__":
    build_biblical_chiasms_catalog()
