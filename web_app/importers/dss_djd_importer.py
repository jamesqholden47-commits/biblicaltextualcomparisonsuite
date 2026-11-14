"""
dss_djd_importer.py -- Skeleton Pipeline & Schema for Dead Sea Scrolls (DJD & Ulrich).
Part of Plenary Logos Suite & Catholic Jarvis Suite.

Architecture for ingesting and normalizing:
1. Discoveries in the Judaean Desert (DJD, 40 vols., Oxford University Press)
2. Eugene Ulrich (ed.), The Biblical Qumran Scrolls: Transcriptions and Textual Variants (3 vols., Brill 2010)
3. Florentino García Martínez & Eibert J.C. Tigchelaar, The Dead Sea Scrolls Study Edition (2 vols., Brill/Eerdmans)
4. Frank Moore Cross, Qumran and the History of the Biblical Text (Harvard 1975)

Zero external dependencies (pure Python standard library).
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


@dataclass
class DSSVariantAnnotation:
    locus: str                    # "1 Sam 17:4"
    aligned_mt_reading: str       # "שֵׁשׁ אַמּוֹת וָזָרֶת"
    aligned_lxx_reading: str      # "τεσσάρων πήχεων καὶ σπιθαμῆς"
    dss_reading: str              # "ארבע אמות וזרת"
    text_type_affinity: str       # "Pre-Septuagintal (Old Greek Vorlage)", "Proto-Masoretic", "Proto-Samaritan", "Independent / Non-Aligned"
    scholarly_note: str           # Commentary by Ulrich, Cross, or Tov


@dataclass
class DSSFragmentEntry:
    cave: int                     # 1, 4, 11
    scroll_siglum: str            # "4QSam-a"
    inventory_number: str         # "4Q51"
    djd_volume: str               # "DJD XVII (ed. F.M. Cross, D.W. Parry, R.J. Saley, E. Ulrich 2005)"
    date_paleographic: str        # "c. 50-25 BC (Late Hasmonaean / Early Herodian)"
    material: str                 # "Leather / Parchment"
    script_style: str             # "Hasmonaean formal book hand"
    paleo_hebrew_tetragrammaton: bool # True if YHWH is written in Paleo-Hebrew script
    column_number: str            # "Col. XII"
    lines: str                    # "lines 1-4"
    transcription_diplomatic: str # Diplomatic unpointed Hebrew with brackets
    variants: List[DSSVariantAnnotation] = field(default_factory=list)


class DSSDJDImporter:
    """Production-grade ingestion skeleton for Dead Sea Scrolls diplomatic transcriptions."""

    def __init__(self, raw_input_dir: Optional[str] = None):
        self.raw_input_dir = raw_input_dir or os.path.join(os.path.dirname(__file__), "raw_feeds")
        self.fragments: List[DSSFragmentEntry] = []

    def parse_dss_json(self, json_content: str) -> List[DSSFragmentEntry]:
        data = json.loads(json_content)
        parsed = []
        for item in data.get("fragments", []):
            variants = [DSSVariantAnnotation(**v) for v in item.get("variants", [])]
            frag = DSSFragmentEntry(
                cave=item["cave"],
                scroll_siglum=item["scroll_siglum"],
                inventory_number=item["inventory_number"],
                djd_volume=item["djd_volume"],
                date_paleographic=item["date_paleographic"],
                material=item["material"],
                script_style=item["script_style"],
                paleo_hebrew_tetragrammaton=item.get("paleo_hebrew_tetragrammaton", False),
                column_number=item["column_number"],
                lines=item["lines"],
                transcription_diplomatic=item["transcription_diplomatic"],
                variants=variants
            )
            parsed.append(frag)
        self.fragments.extend(parsed)
        return parsed

    def export_normalized_catalog(self, output_path: str):
        payload = {
            "apparatus_name": "Dead Sea Scrolls Diplomatic Transcriptions (DJD & Ulrich)",
            "schema_version": "1.0.0-PROD",
            "total_fragments": len(self.fragments),
            "fragments": [asdict(f) for f in self.fragments]
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[DSS/DJD Importer] Successfully exported {len(self.fragments)} fragments to {output_path}")

    @staticmethod
    def get_sample_dss_payload() -> Dict[str, Any]:
        return {
            "fragments": [
                {
                    "cave": 4,
                    "scroll_siglum": "4QSam-a",
                    "inventory_number": "4Q51",
                    "djd_volume": "DJD XVII (ed. F.M. Cross et al., 2005)",
                    "date_paleographic": "c. 50-25 BC (Early Herodian)",
                    "material": "Leather",
                    "script_style": "Jewish formal book hand",
                    "paleo_hebrew_tetragrammaton": False,
                    "column_number": "Col. XII",
                    "lines": "lines 1-2",
                    "transcription_diplomatic": "וַיֵּצֵא אִישׁ הַבֵּנַיִם מִמַּחֲנוֹת פְּלִשְׁתִּים גָּלְיָת שְׁמוֹ מִגַּת [גָּבְהוֹ אַרְ]בַּע אַמּוֹת וָזָרֶת",
                    "variants": [
                        {
                            "locus": "1 Sam 17:4",
                            "aligned_mt_reading": "שֵׁשׁ אַמּוֹת וָזָרֶת (six cubits and a span, approx 9'9\")",
                            "aligned_lxx_reading": "τεσσάρων πήχεων καὶ σπιθαμῆς (four cubits and a span, approx 6'9\")",
                            "dss_reading": "[אַרְ]בַּע אַמּוֹת וָזָרֶת (four cubits and a span)",
                            "text_type_affinity": "Pre-Septuagintal (Old Greek Vorlage)",
                            "scholarly_note": "Eugene Ulrich and Frank Moore Cross confirm that 4QSam-a preserves the pristine Palestinian text of Samuel that served as the Hebrew parent text (Vorlage) for the Old Greek translation. The Masoretic six cubits represents scribal exaggeration."
                        }
                    ]
                }
            ]
        }


if __name__ == "__main__":
    importer = DSSDJDImporter()
    sample = importer.get_sample_dss_payload()
    parsed = importer.parse_dss_json(json.dumps(sample))
    print(f"Parsed {len(parsed)} DSS demonstration fragments. Siglum: {parsed[0].scroll_siglum}")
    print(f"DJD Volume: {parsed[0].djd_volume}, Column: {parsed[0].column_number}")
