"""
bhq_bhs_importer.py -- Skeleton Pipeline & Schema for Biblia Hebraica Quinta (BHQ) & BHS Apparatus.
Part of Plenary Logos Suite & Catholic Jarvis Suite.

Architecture for ingesting and normalizing:
1. Biblia Hebraica Quinta (BHQ, Deutsche Bibelgesellschaft, Stuttgart)
2. Biblia Hebraica Stuttgartensia (BHS, 1977/1997)
3. Masorah Parva (Mp) and Masorah Magna (Mm) as documented by Gérard E. Weil
4. Dead Sea Scrolls, Samaritan Pentateuch, and Ancient Versions textual collations

Zero external dependencies (pure Python standard library).
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


@dataclass
class MasorahNote:
    note_type: str                # "parva" (Mp) or "magna" (Mm)
    weil_number: Optional[int]    # Number in Weil's Massorah Gedolah
    circellus_position: int      # Word position marked with small circle (circellus)
    aramaic_abbreviation: str     # e.g. "ל" (Lamed = unique / hapax legomenon), "ב̇" (twice)
    expanded_latin: str           # e.g. "let kahet" (non amplius / unique occurrence)
    notes_english: str            # "Occurs only once in this precise vocalization"


@dataclass
class BHQReading:
    reading_id: str               # "1", "2", "3"
    hebrew_text: str              # Hebrew consonants + vowels (or retroverted)
    transliteration: str
    translation_en: str
    sigla_witnesses: List[str]    # ["M (Leningradensis)", "4QDeut-j", "Sm (Samaritan)", "G (LXX)", "S (Peshitta)", "T (Targum)", "V (Vulgate)"]
    editorial_judgment: str       # "preferred", "secondary", "graphic error", "theological revision", "harmonization"


@dataclass
class BHQApparatusEntry:
    locus: str                    # "Deut 32:8"
    book: str                     # "Deuteronomy"
    chapter: int                  # 32
    verse: int                    # 8
    lemma: str                    # Hebrew lemma under discussion
    masorah_notes: List[MasorahNote] = field(default_factory=list)
    readings: List[BHQReading] = field(default_factory=list)
    bhq_editorial_eval: str = ""  # General BHQ editor evaluation (e.g. by Jan de Waard / Carmel McCarthy)
    dss_sigla: List[str] = field(default_factory=list)


class BHQImporter:
    """Production-grade ingestion skeleton for BHQ and BHS Hebrew diplomatic apparatus."""

    def __init__(self, raw_input_dir: Optional[str] = None):
        self.raw_input_dir = raw_input_dir or os.path.join(os.path.dirname(__file__), "raw_feeds")
        self.entries: List[BHQApparatusEntry] = []

    def parse_bhq_json(self, json_content: str) -> List[BHQApparatusEntry]:
        """Parses structured JSON representations of BHQ apparatus fascicles."""
        data = json.loads(json_content)
        parsed = []
        for item in data.get("apparatus_entries", []):
            masorah = [MasorahNote(**m) for m in item.get("masorah_notes", [])]
            readings = [BHQReading(**r) for r in item.get("readings", [])]
            entry = BHQApparatusEntry(
                locus=item["locus"],
                book=item["book"],
                chapter=item["chapter"],
                verse=item["verse"],
                lemma=item["lemma"],
                masorah_notes=masorah,
                readings=readings,
                bhq_editorial_eval=item.get("bhq_editorial_eval", ""),
                dss_sigla=item.get("dss_sigla", [])
            )
            parsed.append(entry)
        self.entries.extend(parsed)
        return parsed

    def export_normalized_catalog(self, output_path: str):
        payload = {
            "apparatus_name": "Biblia Hebraica Quinta (BHQ) Diplomatic Apparatus",
            "schema_version": "1.0.0-PROD",
            "total_entries": len(self.entries),
            "entries": [asdict(e) for e in self.entries]
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[BHQ Importer] Successfully exported {len(self.entries)} entries to {output_path}")

    @staticmethod
    def get_sample_bhq_payload() -> Dict[str, Any]:
        """Sample BHQ apparatus entry for Deut 32:8."""
        return {
            "apparatus_entries": [
                {
                    "locus": "Deut 32:8",
                    "book": "Deuteronomy",
                    "chapter": 32,
                    "verse": 8,
                    "lemma": "בְּנֵי יִשְׂרָאֵל",
                    "bhq_editorial_eval": "The BHQ committee recognizes 'בני אלוהים / בני אל' as the original Old Hebrew reading, altered in proto-Masoretic tradition (M) for theological reasons to avoid suggesting that Yahweh had equal divine companions presiding over the nations.",
                    "dss_sigla": ["4QDeut-j (4Q37)", "4QDeut-q (4Q44)"],
                    "masorah_notes": [
                        {
                            "note_type": "parva",
                            "weil_number": 1420,
                            "circellus_position": 7,
                            "aramaic_abbreviation": "ל̇",
                            "expanded_latin": "let kahet",
                            "notes_english": "Unique occurrence of this specific phrase in this cantillation"
                        }
                    ],
                    "readings": [
                        {
                            "reading_id": "1",
                            "hebrew_text": "בְּנֵי יִשְׂרָאֵל",
                            "transliteration": "bənēy Yisrā'ēl",
                            "translation_en": "the sons of Israel",
                            "sigla_witnesses": ["M (Codex Leningradensis)", "Sm (Samaritan Pentateuch)", "T (Targumim)", "S (Peshitta)", "V (Vulgate)"],
                            "editorial_judgment": "theological revision"
                        },
                        {
                            "reading_id": "2",
                            "hebrew_text": "בְּנֵי אֱלֹהִים",
                            "transliteration": "bənēy 'ĕlōhīm",
                            "translation_en": "the sons of God",
                            "sigla_witnesses": ["4QDeut-j", "G (LXX: ἀγγέλων θεοῦ / υἱῶν θεοῦ)", "Vetus Latina (filiorum dei)"],
                            "editorial_judgment": "preferred"
                        },
                        {
                            "reading_id": "3",
                            "hebrew_text": "בְּנֵי אֵל",
                            "transliteration": "bənēy 'ēl",
                            "translation_en": "the sons of El",
                            "sigla_witnesses": ["4QDeut-q"],
                            "editorial_judgment": "archaic poetry variant"
                        }
                    ]
                }
            ]
        }


if __name__ == "__main__":
    importer = BHQImporter()
    sample = importer.get_sample_bhq_payload()
    parsed = importer.parse_bhq_json(json.dumps(sample))
    print(f"Parsed {len(parsed)} BHQ demonstration entries. Locus: {parsed[0].locus}")
    print(f"Lemma: {parsed[0].lemma}, Total Readings: {len(parsed[0].readings)}")
