"""
Visual Audit and Comparison Matrix Core Engine.
Enforces Rule 11 (Absolute Lossless Consolidation: zero dropped sentences)
and Rule 13 (Subject vs Infrastructure Scoping).
"""

import os
import re
import difflib
from typing import List, Dict, Any, Tuple, Optional

# Minimum normalized length for a substantive sentence (matching loss_check.py heuristics)
MIN_SENTENCE_LEN = 30
NEAR_MATCH_THRESHOLD = 0.85

# Rule 13: Infrastructure keywords and path markers
INFRASTRUCTURE_MARKERS = [
    "_SESSION_TRANSCRIPTS",
    "07_ARCHIVE_OLD_PROCESS",
    "settings.json",
    "build_system_log",
    "cli_bridge",
    "drift_check",
    "write_ag_handoff",
    "write_boot_header",
    "loss_check",
    "classify_dossiers",
    "ocr_strategy",
    "disk_checksum",
    "transcript.jsonl",
    "OSTEP",
    "Operating Systems: Three Easy Pieces",
    "ext4 ratio",
    "manage_task",
    "run_command",
    "task-",
    "__pycache__",
    ".pytest_cache",
    ".git",
    "node_modules",
]

# Common abbreviations to prevent false sentence splits
ABBREVIATIONS = (
    r"(?:[A-Z]\.)+"  # e.g. U.S., B.C., A.D.
    r"|(?:[Aa]l|[Cc]h|[Cc]hs|[Vv]s?|[Ff]n|[Nn]o|[Pp]p|[Pp]g|[Pp]l|[Ee]dg|[Ee]x|[Vv]ol|[Ff]ig|[Ss]ec)\."
    r"|(?:[Ee]\.[Gg]\.|[Ii]\.[Ee]\.|[Ee]tc\.|[Cc]a?\.)"
    r"|(?:St|Fr|Dr|Prof|Rev|Bp|Msgr|Gen|Col)\."
    r"|(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\."
)


def norm_sentence(text: str) -> str:
    """Normalize text for sentence comparison: strip markup, footnotes, code, punctuation."""
    s = re.sub(r"\[\^[^\]]*\]", " ", text)       # Footnote anchors [^1]
    s = re.sub(r"`[^`]*`", " ", s)               # Code spans `code`
    s = re.sub(r"<[^>]+>", " ", s)               # HTML tags
    s = re.sub(r"https?://\S+", " ", s)          # URLs
    s = re.sub(r"[^\w\s]", " ", s.lower())        # Punctuation to space, lowercase
    return re.sub(r"\s+", " ", s).strip()


KNOWN_ABBREVIATIONS = [
    "St.", "Dr.", "Fr.", "Prof.", "Rev.", "Bp.", "Msgr.", "Gen.", "Col.",
    "e.g.", "i.e.", "etc.", "vs.", "v.", "cf.", "ca.", "c.", "ch.", "chs.",
    "fn.", "p.", "pp.", "vol.", "no.", "al.", "A.D.", "B.C.",
]


def tokenize_sentences(text: str) -> List[Tuple[str, str]]:
    """
    Split document text into substantive sentences while protecting citations and abbreviations.
    Returns list of tuples: (normalized_sentence, raw_sentence).
    """
    if not text:
        return []

    lines = text.split("\n")
    results = []

    for line in lines:
        raw_line = line.strip()
        # Skip pure structural markdown lines (headers, table rules, dividers, blockquotes markers)
        if not raw_line or raw_line.startswith(("#", "|", "---", "===", "***")):
            continue

        # Mask known abbreviations to protect from false splits
        masked = raw_line
        for abbr in KNOWN_ABBREVIATIONS:
            masked = re.sub(r"\b" + re.escape(abbr), abbr.replace(".", "§DOT§"), masked, flags=re.IGNORECASE)

        # Protect chapter:verse dot citations e.g. 1 Clem 44.1
        masked = re.sub(r"(\d+)\.(\d+)", r"\1§DOT§\2", masked)

        # Split on sentence boundaries
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'“‘\(\[])", masked)
        for part in parts:
            p = part.replace("§DOT§", ".").strip()
            if not p:
                continue
            n = norm_sentence(p)
            if len(n) >= MIN_SENTENCE_LEN:
                results.append((n, p))
            elif len(n) >= 15 and any(term in p for term in ("AD", "BC", "AH", "PG", "PL", "MT", "LXX", "DSS")):
                # Preserve short critical citation fragments
                results.append((n, p))

    return results


def check_rule_13_infrastructure(path_or_content: str) -> Tuple[bool, str]:
    """
    Enforce Rule 13: Check if a path or text content represents infrastructure rather than dissertation content.
    Returns (is_infrastructure: bool, reason: str).
    """
    normalized = path_or_content.replace("\\", "/")
    
    for marker in INFRASTRUCTURE_MARKERS:
        if marker.lower() in normalized.lower():
            return True, f"Rule 13 Violation: Matched infrastructure marker '{marker}'."
            
    # Check for infrastructure prose patterns
    infra_patterns = [
        (r"\bOSTEP\b", "Cites OSTEP (Operating Systems: Three Easy Pieces)"),
        (r"\bdisk-checksum\b", "Cites disk-checksum infrastructure"),
        (r"\bext4-style Superblock\b", "Cites ext4 superblock design directly in content"),
        (r"\bmanage_task\b", "Cites agentic task runner infrastructure"),
        (r"\btranscript\.jsonl\b", "Cites transcript log file"),
    ]
    for pat, desc in infra_patterns:
        if re.search(pat, path_or_content, re.IGNORECASE):
            return True, f"Rule 13 Violation: {desc}."

    return False, "Valid Subject Matter (Dissertation candidate)"


def check_sentence_survival(
    norm_s: str, 
    target_joined: str, 
    target_norms: List[str]
) -> Tuple[bool, str]:
    """
    Check if a normalized sentence survives in the target corpus.
    Survives on:
    1. Exact normalized match in target sentence list.
    2. Exact substring match in full target body.
    3. Token Jaccard overlap >= NEAR_MATCH_THRESHOLD (85%).
    """
    # 1. Exact match
    if norm_s in target_norms:
        return True, "exact"

    # 2. Substring containment
    if norm_s in target_joined:
        return True, "substring"

    # 3. Token overlap near-match
    tok_s = set(norm_s.split())
    if len(tok_s) >= 6:
        for t_norm in target_norms:
            tok_t = set(t_norm.split())
            if not tok_t:
                continue
            overlap = len(tok_s & tok_t) / len(tok_s)
            if overlap >= NEAR_MATCH_THRESHOLD:
                return True, f"near_match ({overlap:.2f})"

    return False, "lost"


def compute_audit_matrix(source_text: str, target_text: str) -> Dict[str, Any]:
    """
    Compute full Visual Audit and Comparison Matrix between source and target texts.
    Returns detailed diff opcodes, Rule 11 verification, and visual markup blocks.
    """
    source_sentences = tokenize_sentences(source_text)
    target_sentences = tokenize_sentences(target_text)

    source_norms = [n for n, _ in source_sentences]
    target_norms = [n for n, _ in target_sentences]
    target_joined = norm_sentence(target_text)

    # Track survival of every source sentence (Rule 11)
    preserved = []
    omitted = []

    for idx, (n_s, raw_s) in enumerate(source_sentences):
        survives, match_type = check_sentence_survival(n_s, target_joined, target_norms)
        record = {
            "index": idx,
            "raw": raw_s,
            "norm": n_s,
            "match_type": match_type,
        }
        if survives:
            preserved.append(record)
        else:
            omitted.append(record)

    # Compute difflib opcodes over raw sentences
    raw_source = [r for _, r in source_sentences]
    raw_target = [r for _, r in target_sentences]
    matcher = difflib.SequenceMatcher(None, raw_source, raw_target)
    
    diff_blocks = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i1, i2):
                diff_blocks.append({
                    "status": "equal",
                    "source_text": raw_source[k],
                    "target_text": raw_target[j1 + (k - i1)] if (j1 + (k - i1)) < j2 else "",
                    "badge": "⚖️ PRESERVED",
                })
        elif tag == "delete":
            for k in range(i1, i2):
                # Verify if this deleted line actually survived elsewhere
                norm_k = norm_sentence(raw_source[k])
                survives, mtype = check_sentence_survival(norm_k, target_joined, target_norms)
                diff_blocks.append({
                    "status": "omitted" if not survives else "relocated",
                    "source_text": raw_source[k],
                    "target_text": "",
                    "badge": "❌ OMITTED (RULE 11 DEFECT)" if not survives else f"🔄 RELOCATED ({mtype})",
                })
        elif tag == "insert":
            for k in range(j1, j2):
                diff_blocks.append({
                    "status": "added",
                    "source_text": "",
                    "target_text": raw_target[k],
                    "badge": "➕ ADDED",
                })
        elif tag == "replace":
            # Compare chunks
            s_chunk = raw_source[i1:i2]
            t_chunk = raw_target[j1:j2]
            max_len = max(len(s_chunk), len(t_chunk))
            for k in range(max_len):
                s_item = s_chunk[k] if k < len(s_chunk) else ""
                t_item = t_chunk[k] if k < len(t_chunk) else ""
                
                s_survives = False
                if s_item:
                    norm_k = norm_sentence(s_item)
                    s_survives, _ = check_sentence_survival(norm_k, target_joined, target_norms)

                diff_blocks.append({
                    "status": "replaced",
                    "source_text": s_item,
                    "target_text": t_item,
                    "badge": "✏️ REWRITTEN" if s_survives else "⚠️ REWRITTEN (CHECK LOSS)",
                })

    total_source = len(source_sentences)
    total_preserved = len(preserved)
    total_omitted = len(omitted)
    total_added = len(target_sentences) - total_preserved if len(target_sentences) > total_preserved else 0
    preservation_rate = (total_preserved / total_source) if total_source > 0 else 1.0

    rule_11_passed = (total_omitted == 0)

    # Rule 13 Checks on both source and target
    is_source_infra, source_infra_reason = check_rule_13_infrastructure(source_text)
    is_target_infra, target_infra_reason = check_rule_13_infrastructure(target_text)

    return {
        "summary": {
            "rule_11_passed": rule_11_passed,
            "rule_13_source_passed": not is_source_infra,
            "rule_13_target_passed": not is_target_infra,
            "total_source_sentences": total_source,
            "total_target_sentences": len(target_sentences),
            "preserved_count": total_preserved,
            "omitted_count": total_omitted,
            "added_count": total_added,
            "preservation_rate": round(preservation_rate * 100, 2),
            "verdict": "LOSSLESS (Rule 11 Verified)" if rule_11_passed else f"RULE 11 DEFECT: {total_omitted} Sentence(s) Lost",
        },
        "rule_13_audit": {
            "source_infra": is_source_infra,
            "source_reason": source_infra_reason,
            "target_infra": is_target_infra,
            "target_reason": target_infra_reason,
        },
        "omitted_sentences": omitted,
        "diff_blocks": diff_blocks,
    }


def render_html_diff_matrix(audit_result: Dict[str, Any], title: str = "Visual Audit Matrix") -> str:
    """Generate high-clarity HTML view with red/green diff badges."""
    summary = audit_result["summary"]
    diff_blocks = audit_result["diff_blocks"]

    passed_badge = (
        '<span style="background-color: #2da44e; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">PASS (LOSSLESS)</span>'
        if summary["rule_11_passed"]
        else '<span style="background-color: #cf222e; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">FAIL (SENTENCE LOSS DETECTED)</span>'
    )

    rows = []
    for b in diff_blocks:
        st = b["status"]
        if st == "equal":
            bg = "#ffffff"
            text_color = "#24292e"
        elif st in ("omitted", "delete"):
            bg = "#ffeef0"
            text_color = "#cf222e"
        elif st == "added":
            bg = "#e6ffed"
            text_color = "#1a7f37"
        elif st == "relocated":
            bg = "#fff8c5"
            text_color = "#9a6700"
        else:
            bg = "#f6f8fa"
            text_color = "#57606a"

        src_escaped = b["source_text"].replace("<", "&lt;").replace(">", "&gt;")
        tgt_escaped = b["target_text"].replace("<", "&lt;").replace(">", "&gt;")

        rows.append(f"""
        <tr style="background-color: {bg}; border-bottom: 1px solid #d0d7de;">
            <td style="padding: 8px; font-size: 11px; font-weight: bold; width: 140px; color: {text_color};">{b['badge']}</td>
            <td style="padding: 8px; font-family: monospace; font-size: 12px; width: 45%;">{src_escaped}</td>
            <td style="padding: 8px; font-family: monospace; font-size: 12px; width: 45%;">{tgt_escaped}</td>
        </tr>
        """)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{title}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; background: #f6f8fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 24px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }}
            .stats-bar {{ display: flex; gap: 20px; background: #f6f8fa; padding: 12px 16px; border-radius: 6px; margin: 16px 0; }}
            .stat-box {{ display: flex; flex-direction: column; }}
            .stat-label {{ font-size: 11px; text-transform: uppercase; color: #57606a; }}
            .stat-value {{ font-size: 18px; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
            th {{ text-align: left; padding: 8px; background: #f6f8fa; border-bottom: 2px solid #d0d7de; font-size: 12px; text-transform: uppercase; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>{title} &nbsp; {passed_badge}</h2>
            <div class="stats-bar">
                <div class="stat-box"><span class="stat-label">Source Sentences</span><span class="stat-value">{summary['total_source_sentences']}</span></div>
                <div class="stat-box"><span class="stat-label">Preserved</span><span class="stat-value" style="color: #1a7f37;">{summary['preserved_count']}</span></div>
                <div class="stat-box"><span class="stat-label">Omitted (Lost)</span><span class="stat-value" style="color: #cf222e;">{summary['omitted_count']}</span></div>
                <div class="stat-box"><span class="stat-label">Added</span><span class="stat-value" style="color: #0969da;">{summary['added_count']}</span></div>
                <div class="stat-box"><span class="stat-label">Preservation Rate</span><span class="stat-value">{summary['preservation_rate']}%</span></div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Source Text (Candidate / Note)</th>
                        <th>Target Text (Dossier / Master)</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html


# The 8 Laser Deduplication Campaigns
CAMPAIGN_REGISTRY = [
    {
        "id": "CAMP-01",
        "name": "Trunk I: Textual Transmission & Ulrich Clusters",
        "anchor_file": "03_RESEARCH_DOSSIERS/dossier_ulrich_variant_register.md",
        "cluster_count": 110,
        "token_estimate": "3.8M",
        "description": "4QSam-a, 4QJer-b, MT vs LXX alignments, homoioteleuton registers",
    },
    {
        "id": "CAMP-02",
        "name": "Trunk II: Second Temple Ben Sira & Genizah MSS",
        "anchor_file": "03_RESEARCH_DOSSIERS/dossier_ben_sira_wisdom.md",
        "cluster_count": 65,
        "token_estimate": "2.2M",
        "description": "Genizah MSS A-F, Masada fragments, Sirach 24 sapiential halakhah",
    },
    {
        "id": "CAMP-03",
        "name": "Trunk III: Halakhic Jurisprudence & 4QMMT Fragments",
        "anchor_file": "03_RESEARCH_DOSSIERS/dossier_halakhic_precedent.md",
        "cluster_count": 85,
        "token_estimate": "2.9M",
        "description": "4QMMT liquid streams, Damascus Document Sabbath bounds, Gospel legal disputes",
    },
    {
        "id": "CAMP-04",
        "name": "Trunk IV: Sacred Prototype & Archetypal Christology",
        "anchor_file": "03_RESEARCH_DOSSIERS/THE_SACRED_PROTOTYPE_DISSERTATION.md",
        "cluster_count": 145,
        "token_estimate": "5.4M",
        "description": "Primordial priest-king, cosmic sanctuary, Melchizedek, high Christology",
    },
    {
        "id": "CAMP-05",
        "name": "Trunk V: Cosmic Geography & Gates of Hades",
        "anchor_file": "03_RESEARCH_DOSSIERS/dossier_gates_of_hades.md",
        "cluster_count": 55,
        "token_estimate": "1.8M",
        "description": "Caesarea Philippi, Banias Pan grotto, Matt 16:18, Mount Hermon Watchers",
    },
    {
        "id": "CAMP-06",
        "name": "Trunk VI: Intercession & Talmudic Disputations",
        "anchor_file": "03_RESEARCH_DOSSIERS/dossier_intercession_talmud.md",
        "cluster_count": 70,
        "token_estimate": "2.5M",
        "description": "Bavli Sanhedrin 38b, Berakhot 10a, angelic advocacy, Merkabah mysticism",
    },
    {
        "id": "CAMP-07",
        "name": "Trunk VII: Applied Ecclesiology Mexico Monograph (35 Chs)",
        "anchor_file": "03_RESEARCH_DOSSIERS/monograph_mexico_study_complete_35chs.md",
        "cluster_count": 160,
        "token_estimate": "6.2M",
        "description": "35-chapter monograph version drift, qualitative field notes, Cristero history",
    },
    {
        "id": "CAMP-08",
        "name": "Trunk VIII: Meta-Corpus Infrastructure & Graph Stubs",
        "anchor_file": "02_CONTROL_AND_STATE/vault_deduplication_master_ledger.md",
        "cluster_count": 40,
        "token_estimate": "3.2M",
        "description": "Vault redirection stubs, MOC consolidation, wikilink validation",
    },
]


def list_campaigns() -> List[Dict[str, Any]]:
    """Return the list of 8 laser deduplication campaigns."""
    return CAMPAIGN_REGISTRY
