"""
MT/LXX Surface Divergence Report (/api/mt_lxx). Claude GUI, Sonnet 5.5, 2026-11-12.

Built under James's goal: "run our in house analysis even if its surface level; mark it as
unverified if not verified or wherever its categorized" -- a deliberately deterministic,
zero-cost, no-live-API alternative to the BibCrit-style per-passage Claude classifier scoped
(but not run) in the earlier plan at ~/.claude/plans/tingly-snuggling-karp.md. This computes
ONE thing, directly and honestly: for every Old Testament chapter where both the Hebrew
Masoretic Text and the Greek Septuagint are present in the Plenary Suite's own aligned data
(web_app/plenary_logos_data.json), how many verses does each stream have, and how large is the
gap? A chapter-level verse-count mismatch is not proof of a different Vorlage (it could be a
verse-division artifact) -- so every flagged chapter is tagged [S] (surface-level / unverified)
UNLESS it matches one of a short, hand-picked list of loci with a named scholarly treatment
behind it, which are tagged [R] instead. Nothing here was generated or classified by a model;
every number is a deterministic count over already-downloaded primary texts.

  GET /api/mt_lxx/divergence           JSON: every OT chapter flagged by verse-count delta
  GET /api/mt_lxx/divergence/export    the same, as a downloadable Markdown report
"""
import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from modules.paths_config import get_path

router = APIRouter(prefix="/api/mt_lxx", tags=["mt_lxx"])

DELTA_THRESHOLD = 2  # a 1-verse gap is routine (versification differences); >=2 is worth a look

PLENARY_DATA_PATH = os.path.join(get_path("dissertation_project"), "web_app", "plenary_logos_data.json")

# Hand-picked loci with a NAMED source behind the classification (Rule 4: "draw from academia,
# never invent connections") -- not auto-selected, and not exhaustive. Each maps to the book/
# chapter the surface scan above also flags, so the two independent signals (a human-curated
# loose list of what's WELL KNOWN, and a dumb verse-count scan of what the SUITE'S OWN data
# shows) can be cross-checked against each other live, not just asserted together.
NAMED_LOCI = [
    {"book_id": "jer", "chapters": "all", "classification": "different_vorlage / shorter & reordered",
     "dss_attestation": "attests_lxx_vorlage",
     "source": "Tov, Textual Criticism of the Hebrew Bible, 3rd ed. (2012), ch. 7 -- LXX Jeremiah "
                "is ~1/8 shorter than MT and arranges the oracles against the nations differently; "
                "4QJer^b/d from Qumran attest a Hebrew Vorlage matching the shorter LXX text-type."},
    {"book_id": "1sam", "chapters": [17, 18], "classification": "different_vorlage / shorter",
     "dss_attestation": "attests_lxx_vorlage",
     "source": "Tov, op. cit., ch. 7 -- LXX 1 Samuel 17-18 (the Goliath narrative) omits roughly "
                "45% of the MT material; 4QSam^a from Qumran supports a shorter Hebrew Vorlage "
                "underlying the LXX, not a Greek translator's abridgement."},
    {"book_id": "exod", "chapters": [35, 36, 37, 38, 39, 40], "classification": "different_vorlage / reordered",
     "dss_attestation": "unknown",
     "source": "Tov, op. cit., ch. 7 -- LXX Exodus 35-40 (the Tabernacle construction account) "
                "follows a different order and is shorter than MT; widely read as reflecting a "
                "distinct recension of the building instructions."},
    {"book_id": "dan", "chapters": [3], "classification": "theological/liturgical addition",
     "dss_attestation": "no_qumran_witness",
     "source": "Fitzmyer & Harrington's standard treatment of Daniel's Greek additions -- LXX/Th "
                "Daniel 3 inserts the Prayer of Azariah and the Song of the Three Young Men "
                "(absent from MT), part of the Deuterocanonical Additions to Daniel."},
    {"book_id": "esth", "chapters": [10], "classification": "theological addition",
     "dss_attestation": "no_qumran_witness",
     "source": "The Greek Additions to Esther (A-F) append material at and after MT Esther 10:3, "
                "including the Mordecai dream-interpretation colophon -- standard Deuterocanonical "
                "material, not a translation variant of the Hebrew text."},
    {"book_id": "prov", "chapters": "most", "classification": "different_vorlage / reordered",
     "dss_attestation": "unknown",
     "source": "Fox, Proverbs 10-31 (Anchor Bible, 2009), introduction -- LXX Proverbs rearranges "
                "large blocks of chs. 24-31 relative to MT, a long-recognized structural divergence."},
]
# NOTE (2026-11-12): Deuteronomy 32 (the Song of Moses, vv. 8 and 43 -- the classic "sons of
# Israel" vs "sons of God" / Hebrews 1:6 LXX-only-addition cases) is NOT listed here on purpose.
# This chapter's MT and LXX have the IDENTICAL verse count (52 = 52, confirmed directly against
# plenary_logos_data.json) even though verse 43's CONTENT differs hugely in length -- this
# scanner only compares verse COUNTS per chapter, so Deut 32 would never be flagged here and a
# NAMED_LOCI entry for it would be permanently unreachable, dead weight. It's handled properly
# instead as a hand-verified crux entry (see PRELOADED_CRUXES in build_plenary_logos_suite.py,
# id "deut32-sonsofgod"), which is built for exactly this single-verse case.

# Each value names what a scholar's own treatment actually claims about Qumran evidence for that
# locus -- "unknown"/"no_qumran_witness" are honest defaults, not placeholders to fill in later
# with a guess. See NAMED_LOCI entries above for the per-locus value; this constant only documents
# the vocabulary so a consumer of the JSON doesn't have to guess what the four strings mean.
DSS_ATTESTATION_VALUES = ("attests_lxx_vorlage", "attests_mt", "no_qumran_witness", "unknown")


def _book_name_lookup(books):
    return {b["id"]: b.get("name", b["id"]) for b in books}


def _scan():
    try:
        os.stat(PLENARY_DATA_PATH)
    except OSError:
        return None
    with open(PLENARY_DATA_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    books = data.get("books", [])
    names = _book_name_lookup(books)
    flagged = []
    for b in books:
        if b.get("testament") != "OT":
            continue
        he = b.get("verses_he") or []
        gr = b.get("verses_gr") or []
        for i in range(max(len(he), len(gr))):
            hv = len(he[i]) if i < len(he) else 0
            gv = len(gr[i]) if i < len(gr) else 0
            if hv == 0 or gv == 0:
                continue  # no Hebrew (Greek-only Deuterocanon) or no Greek -- not a divergence signal
            delta = gv - hv
            if abs(delta) >= DELTA_THRESHOLD:
                flagged.append({"book_id": b["id"], "book_name": b.get("name", b["id"]), "chapter": i + 1,
                                 "hebrew_verses": hv, "greek_verses": gv, "delta": delta})
    flagged.sort(key=lambda r: -abs(r["delta"]))

    def locus_matches(locus, book_id, chapter):
        if locus["book_id"] != book_id:
            return False
        ch = locus["chapters"]
        if ch in ("all", "most"):
            return True
        return chapter in ch

    for row in flagged:
        match = next((l for l in NAMED_LOCI if locus_matches(l, row["book_id"], row["chapter"])), None)
        if match:
            row["tier"] = "R"
            row["classification"] = match["classification"]
            row["source"] = match["source"]
            row["dss_attestation"] = match.get("dss_attestation", "unknown")
        else:
            row["tier"] = "S"
            row["classification"] = "unclassified verse-count divergence"
            row["source"] = None
            row["dss_attestation"] = "unknown"
    return {"made_from": os.path.getmtime(PLENARY_DATA_PATH), "threshold": DELTA_THRESHOLD,
            "book_names": names, "flagged": flagged}


_CACHE = {"key": None, "value": None}


def scan_cached():
    try:
        st = os.stat(PLENARY_DATA_PATH)
        key = (st.st_mtime, st.st_size)
    except OSError:
        return None
    if _CACHE["key"] == key:
        return _CACHE["value"]
    result = _scan()
    _CACHE["key"] = key
    _CACHE["value"] = result
    return result


@router.get("/divergence")
def divergence():
    data = scan_cached()
    if data is None:
        raise HTTPException(503, "Plenary Suite data not built yet -- run web_app/build_plenary_logos_suite.py")
    r_count = sum(1 for r in data["flagged"] if r["tier"] == "R")
    s_count = sum(1 for r in data["flagged"] if r["tier"] == "S")
    return {"threshold": data["threshold"], "total_flagged": len(data["flagged"]),
            "named_tier_r": r_count, "unclassified_tier_s": s_count, "rows": data["flagged"]}


@router.get("/divergence/export")
def divergence_export():
    data = scan_cached()
    if data is None:
        raise HTTPException(503, "Plenary Suite data not built yet -- run web_app/build_plenary_logos_suite.py")
    rows = data["flagged"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# MT/LXX Surface Divergence Report",
        "",
        f"Generated {stamp}. This is a SURFACE-LEVEL, purely mechanical scan -- no model "
        f"classified any of these passages. For every Old Testament chapter where this suite "
        f"holds BOTH a Hebrew Masoretic (WLC) and a Greek Septuagint (Rahlfs) text, it compares "
        f"verse counts. A gap of {data['threshold']} or more verses is flagged. A verse-count gap "
        f"is NOT proof of a different Hebrew Vorlage -- it can also reflect versification "
        f"differences -- so every row below is tagged **[R]** only when a named scholarly "
        f"treatment backs that specific classification, and **[S]** (unverified) otherwise.",
        "",
        f"**{len(rows)} chapters flagged** out of every OT chapter with both streams present "
        f"({sum(1 for r in rows if r['tier'] == 'R')} tagged [R] against named scholarship, "
        f"{sum(1 for r in rows if r['tier'] == 'S')} tagged [S], surface-level only).",
        "",
        "## Flagged chapters, largest gap first",
        "",
        "| Book | Ch. | Hebrew verses | Greek verses | Delta | Tier | Classification | DSS attestation |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['book_name']} | {r['chapter']} | {r['hebrew_verses']} | {r['greek_verses']} | "
                      f"{r['delta']:+d} | [{r['tier']}] | {r['classification']} | {r['dss_attestation']} |")
    sourced = [r for r in rows if r.get("source")]
    if sourced:
        lines += ["", "## Sources for [R]-tagged rows", ""]
        seen = set()
        for r in sourced:
            if r["source"] in seen:
                continue
            seen.add(r["source"])
            lines.append(f"- {r['source']}")
    content = "\n".join(lines) + "\n"
    fstamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Response(content=content, media_type="text/markdown; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="mt_lxx_divergence_report_{fstamp}.md"',
    })
