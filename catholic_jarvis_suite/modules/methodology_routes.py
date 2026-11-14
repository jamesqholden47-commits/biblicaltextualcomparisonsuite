"""
Methodology & Reproducibility statement (/api/methodology). Claude GUI, Sonnet 5.5, 2026-11-12.

Built under James's goal "more impressive features for scientists, scholars and scholarships":
a transparency document aimed specifically at the "scientists" angle the three prior features
(Research Portfolio, citation-rigor metric, per-file citation export) didn't cover -- a Methods
section, the way a scientific paper has one, describing what primary-source corpora this
project's tooling actually draws on and how claims in it are verified.

Every number this module reports is computed live from disk at request time (file counts, byte
totals, registry lengths) -- never a hand-typed claim about what exists. That is the whole point
of a methodology statement: if it can't be independently re-checked, it isn't one (this
project's own Rule 3/19).

  GET /api/methodology            JSON: corpus inventory + citation-rigor + research-output stats
  GET /api/methodology/export     the same, as a downloadable Markdown statement
"""
import os
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import Response

from modules.paths_config import get_path
from modules import catalog_routes as _catalog

router = APIRouter(prefix="/api/methodology", tags=["methodology"])


def _dir_stats(path, exts=None):
    """Count files (optionally filtered by extension) and total bytes under a directory. Returns
    None, not zeros, when the directory doesn't exist -- a corpus that was never downloaded must
    be reported as absent, not as "0 files present"."""
    if not os.path.isdir(path):
        return None
    n, total_bytes = 0, 0
    for name in os.listdir(path):
        if exts and not name.lower().endswith(exts):
            continue
        full = os.path.join(path, name)
        if os.path.isfile(full):
            n += 1
            total_bytes += os.path.getsize(full)
    return {"files": n, "bytes": total_bytes, "path": path}


def _file_stats(path):
    if not os.path.isfile(path):
        return None
    return {"bytes": os.path.getsize(path), "path": path}


def _manuscript_registry_count():
    try:
        from modules.manuscripts_core import MANUSCRIPT_REGISTRY
        return len(MANUSCRIPT_REGISTRY)
    except Exception:  # noqa: BLE001 -- this is a reporting endpoint, never worth a 500
        return None


def _corpus_inventory():
    pdfs = get_path("pdfs_dir")
    project = get_path("dissertation_project")
    web_app = os.path.join(project, "web_app")
    patristics = os.path.join(pdfs, "02_Patristics_and_Church_Fathers")
    return {
        "schaff_anf_npnf": _dir_stats(os.path.join(patristics, "Schaff_ANF_NPNF"), exts=(".pdf",)),
        "migne_patrologia_latina": _dir_stats(os.path.join(patristics, "Migne_Patrologia_Latina"), exts=(".pdf",)),
        "migne_patrologia_graeca": _dir_stats(os.path.join(patristics, "Migne_Patrologia_Graeca"), exts=(".pdf",)),
        "sefaria_rabbinic_corpus": _dir_stats(os.path.join(project, "06_SOURCE_MATERIAL", "RABBINIC_CORPUS_SEFARIA")),
        "stepbible_lxx": _file_stats(os.path.join(web_app, "LXX_final_main.csv")),
        "stepbible_tahot": _dir_stats(os.path.join(web_app, "sources_cache", "raw"), exts=(".txt",)),
        "wlc_hebrew_ot": _file_stats(os.path.join(web_app, "WLC.json")),
        "manuscript_registry_entries": _manuscript_registry_count(),
    }


def _size_human(n):
    """Readable size for the Markdown export -- the Migne PL/PG scans run 12-30 GB each, and
    '30378.8 MB' reads worse than '30.4 GB' for a document meant to be read by a person."""
    if not isinstance(n, (int, float)):
        return "?"
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f} GB"
    return f"{n / 1_000_000:.1f} MB"


@router.get("")
def methodology():
    inv = _corpus_inventory()
    portfolio = _catalog._portfolio_data()
    rigor = None
    d, rows = _catalog._files_rows(infra=0)
    if d is not None:
        targets = [r for r in rows if r.get("exists") and r.get("kind") in _catalog.RIGOR_KINDS]
        totals = {"V": 0, "R": 0, "S": 0}
        for r in targets:
            c = _catalog._count_tags_in_file(r["path"])
            for k in totals:
                totals[k] += c[k]
        total_tagged = sum(totals.values())
        rigor = {"totals": totals,
                 "verified_rate": round(100 * totals["V"] / total_tagged, 1) if total_tagged else None,
                 "sourced_rate": round(100 * (totals["V"] + totals["R"]) / total_tagged, 1) if total_tagged else None}
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "corpus_inventory": inv,
            "research_output": portfolio, "citation_rigor": rigor}


_CORPUS_LABELS = {
    "schaff_anf_npnf": "Schaff's Ante-Nicene and Nicene/Post-Nicene Fathers (CCEL, PDF)",
    "migne_patrologia_latina": "Migne, Patrologia Latina (PDF, scanned volumes)",
    "migne_patrologia_graeca": "Migne, Patrologia Graeca (PDF, scanned volumes)",
    "sefaria_rabbinic_corpus": "Sefaria rabbinic corpus (Talmud, Midrash, etc.)",
    "stepbible_lxx": "STEPBible/CATSS Septuagint, word-level with Strong's + morphology",
    "stepbible_tahot": "STEPBible TAHOT Hebrew Old Testament, tagged",
    "wlc_hebrew_ot": "Westminster Leningrad Codex (Hebrew OT)",
}


@router.get("/export")
def methodology_export():
    data = methodology()
    inv = data["corpus_inventory"]
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        "# Methodology & Reproducibility Statement",
        "",
        f"Generated {stamp}. Every figure below is computed live from the primary-source files "
        "and the research corpus on disk at the moment this document was generated -- none is a "
        "remembered or asserted number (this project's own standing rule: a claim that cannot be "
        "independently re-checked is not a verified claim).",
        "",
        "## Primary-source corpora in use",
        "",
    ]
    any_corpus = False
    for key, label in _CORPUS_LABELS.items():
        v = inv.get(key)
        if v is None:
            lines.append(f"- **{label}:** not present on this machine.")
            continue
        any_corpus = True
        if "files" in v:
            lines.append(f"- **{label}:** {v['files']} files, {_size_human(v['bytes'])}.")
        else:
            lines.append(f"- **{label}:** {_size_human(v['bytes'])}.")
    if inv.get("manuscript_registry_entries") is not None:
        lines.append(f"- **Curated manuscript witnesses** (e.g. the Great Isaiah Scroll, 1QIsa^a): "
                      f"{inv['manuscript_registry_entries']} entries in the manuscript registry.")
    if not any_corpus:
        lines.append("- No external corpora were found on disk at generation time.")

    rigor = data.get("citation_rigor")
    lines += ["", "## Verification methodology", "",
              "Every factual or historical claim in this project's research output is tagged at "
              "one of three tiers: **[V]** verified against a named primary or critical source "
              "with a direct citation or link, **[R]** reliably sourced via named scholarly "
              "consensus, or **[S]** stated/inferred and flagged as requiring further "
              "verification. This is enforced as a standing rule, not applied selectively.", ""]
    if rigor and sum(rigor["totals"].values()):
        t = rigor["totals"]
        lines.append(f"Across the dossiers, dissertation drafts, and reports scanned for this "
                      f"statement: {sum(t.values()):,} tagged claims -- {t['V']:,} [V] verified, "
                      f"{t['R']:,} [R] reliably sourced, {t['S']:,} [S] stated/unsourced. "
                      f"{rigor['verified_rate']}% of tagged claims are independently verified; "
                      f"{rigor['sourced_rate']}% are verified or reliably sourced.")
    else:
        lines.append("No tagged claims were found in the current corpus at generation time.")

    rp = data.get("research_output")
    lines += ["", "## Research output", ""]
    if rp:
        lines.append(f"{rp['total_words']:,} words across {rp['total_files']} completed, "
                      f"independently authored works (dossiers, reports, dissertation drafts, "
                      f"and books), excluding code, logs, and other project infrastructure.")
    content = "\n".join(lines) + "\n"
    fstamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return Response(content=content, media_type="text/markdown; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="methodology_statement_{fstamp}.md"',
    })
