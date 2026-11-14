"""
modules/navigator_core.py — File Genealogy & Tiered Treemap Navigator Engine
CatholicJarvis Master Work Suite (Port 8080)

Provides:
  1. Multi-root filesystem crawler with academic tier categorization & author attribution.
  2. Tiered Treemap hierarchical data builder with togglable sort/group dimensions:
     - Sort: mtime, ctime, atime, size, lines, name
     - Group: category, folder, academic_tier, temporal_month
  3. Knowledge Genealogy Directed Graph Engine ("What file caused which file"):
     - Explicit wiki-links, citations, parent-child syntheses (Rule 11/13).
     - Upstream parent discovery and downstream derivative tracing.
  4. File inspection, metadata extraction, and atomic JSON caching.
"""

import os
import re
import sys
import time
import json
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
CACHE_FILE = os.path.join(DATA_DIR, "navigator_cache.json")
ROOTS_FILE = os.path.join(DATA_DIR, "files_roots.json")

# Configured roots (aligned with files_core.DEFAULT_ROOTS)
DEFAULT_NAVIGATOR_ROOTS = [
    [os.path.join(PROJECT_ROOT, "01_MASTER_DISSERTATION"), "Master Dissertation"],
    [os.path.join(PROJECT_ROOT, "10_VOLUMES"), "Volumes"],
    [os.path.join(PROJECT_ROOT, "03_RESEARCH_DOSSIERS"), "Research Dossiers"],
    [os.path.join(PROJECT_ROOT, "05_DRAFTS"), "Drafts & Syntheses"],
    [os.path.join(PROJECT_ROOT, "06_SOURCE_MATERIAL"), "Source Material"],
    [os.path.join(PROJECT_ROOT, "08_INTAKE"), "Intake & Notes"],
    [os.path.join(PROJECT_ROOT, "02_CONTROL_AND_STATE"), "Control & State"],
    [os.path.join(PROJECT_ROOT, "09_APPS_CATHOLICJARVIS"), "CatholicJarvis"],
]

EXCLUDE_DIRS = {
    "__pycache__", "node_modules", ".git", ".obsidian", ".trash",
    ".venv", "venv", ".pytest_cache", ".system_generated", "audio_cache",
    "RABBINIC_CORPUS_SEFARIA", "_backups_2026-10-07_phase0", "_backups_2026-10-07_reading"
}

TEXT_EXTS = {
    ".md", ".txt", ".json", ".py", ".ps1", ".bat", ".cmd",
    ".html", ".css", ".js", ".ts", ".xml", ".csv", ".tsv", ".log"
}

# Thematic academic keywords for topic clustering and provenance inference
THEMATIC_KEYWORDS = [
    "nasrani", "malabar", "diamper", "chandy", "hishtachavah", "1 chron 29:20",
    "bowing", "nicaea", "elvira", "statue", "icon", "gold streets", "rev 21",
    "hormisdas", "acacian", "primacy", "asar", "keys", "dikaio", "justification",
    "sprinkling", "affusion", "baptism", "purgatory", "incense", "thurificati",
    "kiss of peace", "dura", "qumran", "didache", "augustine", "aquinas", "wallace",
    "john 1:1", "eliakim", "shebna", "melchizedek", "boyarin", "peshitta",
    "targum", "septuagint", "vaticanus", "sinaiticus", "rule 11", "rule 13", "lossless"
]

CATEGORY_META = {
    "master": {
        "label": "Master Dissertation",
        "tier": 3,
        "color_var": "var(--accent-gold)",
        "badge": "Canonical Master"
    },
    "volumes": {
        "label": "Published Volumes",
        "tier": 3,
        "color_var": "var(--accent-gold)",
        "badge": "Volume Chapters"
    },
    "drafts": {
        "label": "Monographs & Drafts",
        "tier": 2,
        "color_var": "var(--accent-cyan)",
        "badge": "Draft Synthesis"
    },
    "dossiers": {
        "label": "Research Dossiers",
        "tier": 1,
        "color_var": "var(--accent-green)",
        "badge": "Research Dossier"
    },
    "intake": {
        "label": "Intake & Notes",
        "tier": 1,
        "color_var": "var(--info)",
        "badge": "Personal Note"
    },
    "books": {
        "label": "Books & Library",
        "tier": 0,
        "color_var": "var(--accent-purple)",
        "badge": "Primary Literature"
    },
    "sources": {
        "label": "Primary Source Material",
        "tier": 0,
        "color_var": "var(--accent-blue)",
        "badge": "Source Witness"
    },
    "control": {
        "label": "Control & State",
        "tier": 4,
        "color_var": "var(--accent-amber)",
        "badge": "System Control"
    },
    "scripts": {
        "label": "Scripts & Tooling",
        "tier": 4,
        "color_var": "var(--text-muted)",
        "badge": "Infrastructure Script"
    },
    "vaults": {
        "label": "Personal Vaults (aa1/Scriptorium)",
        "tier": 1,
        "color_var": "var(--accent-purple)",
        "badge": "External Vault"
    },
    "other": {
        "label": "General Documents",
        "tier": 1,
        "color_var": "var(--text-dim)",
        "badge": "Document"
    }
}

_lock = threading.Lock()
_index_state = {
    "status": "idle",
    "total_files": 0,
    "processed_files": 0,
    "last_indexed": None,
    "error": None
}


def get_roots() -> List[Dict[str, Any]]:
    """Return active roots with labels and existing status."""
    if os.path.exists(ROOTS_FILE):
        try:
            with open(ROOTS_FILE, encoding="utf-8") as f:
                cf = json.load(f)
                if isinstance(cf, list) and cf:
                    return [{"path": os.path.abspath(p), "label": l, "exists": os.path.isdir(p)} for p, l in cf]
        except Exception:
            pass
    return [{"path": os.path.abspath(p), "label": l, "exists": os.path.isdir(p)} for p, l in DEFAULT_NAVIGATOR_ROOTS]


def classify_file(path: str) -> Tuple[str, int]:
    """Determine category and academic tier from path and filename."""
    norm = os.path.normcase(os.path.abspath(path))
    name = os.path.basename(norm)

    if norm.endswith((".py", ".ps1", ".bat", ".cmd", ".sh")) or "\\tools\\" in norm or "\\scripts\\" in norm:
        return "scripts", 4

    if "\\01_master_dissertation\\" in norm or "dissertation" in name or "master" in name:
        return "master", 3

    if "\\10_volumes\\" in norm or "volume_" in name:
        return "volumes", 3

    if "\\05_drafts\\" in norm or "claude_handoff" in name or "cowork_synthesis" in name or "monograph" in name:
        return "drafts", 2

    if "\\03_research_dossiers\\" in norm or "dossier" in name or "subagent_raw_extract" in name:
        return "dossiers", 1

    if "\\08_intake\\" in norm:
        return "intake", 1

    if "\\pdfs\\" in norm or norm.endswith((".pdf", ".djvu", ".epub")):
        return "books", 0

    if "\\06_source_material\\" in norm or "sefaria" in norm or "transcript" in name or "scan" in name:
        return "sources", 0

    if "\\02_control_and_state\\" in norm or name.startswith(("_boot_", "_ag_", "_cli_", "claude.md", "gemini.md", "taskboard")):
        return "control", 4

    if "\\aa1\\" in norm or "\\scholar_decade_plan\\" in norm or "\\mexico_protestantism_study\\" in norm:
        return "vaults", 1

    return "other", 1


def detect_author_type(path: str, snippet: str = "") -> str:
    """Heuristic identification of author provenance (James vs AI vs Canonical)."""
    norm = os.path.normcase(path)
    lower_snip = snippet.lower()

    if "\\aa1\\" in norm or "\\08_intake\\" in norm:
        return "user_authored"

    if any(h in lower_snip for h in ["autonomous academic fleet", "subagent", "claude opus", "antigravity", "prompt:", "system instruction"]):
        return "ai_authored"

    if any(h in lower_snip for h in ["patrologia graeca", "vulgate", "septuagint", "codex", "migne", "bav"]):
        return "canonical_edition"

    if "\\01_master_dissertation\\" in norm or "\\10_volumes\\" in norm:
        return "hybrid"

    return "hybrid"


def extract_links_and_citations(text: str) -> List[str]:
    """Extract wiki-links [[...]], markdown links [x](y), and quoted filename references."""
    targets = []
    # 1. Wiki links [[Target]] or [[Target|Alias]]
    for m in re.finditer(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]", text):
        clean = m.group(1).strip()
        if clean:
            targets.append(clean)

    # 2. Markdown links [Text](path/to/target.md)
    for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        link = m.group(2).strip().split("#")[0].split("?")[0]
        if link and not link.startswith(("http://", "https://", "mailto:")):
            base = os.path.basename(link)
            if base:
                targets.append(base)

    # 3. Direct mention of specific project dossiers or chapters
    for m in re.finditer(r"\b([a-zA-Z0-9_\-]{3,}\.(?:md|txt|pdf))\b", text, re.I):
        targets.append(m.group(1))

    return targets


NOT_DISSERTATION_FILE = os.path.join(PROJECT_ROOT, "02_CONTROL_AND_STATE", "_NOT_DISSERTATION_CONTENT.json")


def load_not_dissertation_content() -> Set[str]:
    """Load exclusion list of infrastructure/non-dissertation content if present."""
    if os.path.exists(NOT_DISSERTATION_FILE):
        try:
            with open(NOT_DISSERTATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {os.path.normcase(os.path.abspath(p)) if os.path.isabs(p) else os.path.normcase(p) for p in data}
                elif isinstance(data, dict):
                    res = set()
                    for k, v in data.items():
                        res.add(os.path.normcase(k))
                        if isinstance(v, list):
                            for item in v:
                                if isinstance(item, str):
                                    res.add(os.path.normcase(item))
                    return res
        except Exception:
            pass
    return set()


def count_citations(text: str) -> int:
    """Count citations: [^...] footnotes + PG/PL + DH patristic/magisterial citations."""
    c_fn = len(re.findall(r"\[\^[^\]]+\]", text))
    c_pgpl = len(re.findall(r"\b(?:PG|PL)\b", text))
    c_dh = len(re.findall(r"\bDH\b", text))
    return c_fn + c_pgpl + c_dh


def scan_corpus(roots: Optional[List[Dict[str, Any]]] = None, max_files: int = 15000) -> Dict[str, Any]:
    """Walk roots, collect stats, inspect textual relationships, and build node/genealogy graph."""
    if roots is None:
        roots = get_roots()

    not_dissertation_set = load_not_dissertation_content()

    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []
    name_to_id: Dict[str, List[str]] = {}
    stem_to_id: Dict[str, List[str]] = {}

    total_scanned = 0

    for root_info in roots:
        r_path = root_info["path"]
        if not os.path.isdir(r_path):
            continue

        for root_dir, dirs, files in os.walk(r_path):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in EXCLUDE_DIRS]

            for fname in files:
                if fname.startswith("."):
                    continue

                full_p = os.path.abspath(os.path.join(root_dir, fname))
                norm_p = os.path.normcase(full_p)

                if norm_p in nodes:
                    continue

                try:
                    st = os.stat(full_p)
                except OSError:
                    continue

                total_scanned += 1
                cat, tier = classify_file(full_p)
                ext = os.path.splitext(fname)[1].lower()

                mtime = st.st_mtime
                ctime = getattr(st, "st_ctime", mtime)
                atime = getattr(st, "st_atime", mtime)
                size = st.st_size

                # Fast line and snippet inspection for text
                line_count = 0
                snippet = ""
                referenced_targets = []
                topics_matched = []
                citations = 0

                if ext in TEXT_EXTS and size < 20 * 1024 * 1024:
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="replace") as fh:
                            sample = fh.read(512 * 1024 if ext == ".md" else 128 * 1024)
                            snippet = sample[:1200]
                            referenced_targets = extract_links_and_citations(sample)
                            lower_c = sample.lower()
                            topics_matched = [kw for kw in THEMATIC_KEYWORDS if kw in lower_c]
                            if ext == ".md":
                                citations = count_citations(sample)
                            if size <= 128 * 1024:
                                line_count = sample.count("\n") + 1
                            else:
                                line_count = max(1, int(size / max(1, len(sample) / max(1, sample.count("\n")))))
                    except Exception:
                        pass
                else:
                    line_count = max(1, size // 60)

                author = detect_author_type(full_p, snippet)
                rel_to_proj = os.path.relpath(full_p, PROJECT_ROOT) if PROJECT_ROOT in full_p else fname

                is_infra = (
                    tier == 4
                    or cat in ("control", "scripts")
                    or norm_p in not_dissertation_set
                    or fname.lower() in not_dissertation_set
                    or rel_to_proj.lower() in not_dissertation_set
                    or "\\02_control_and_state\\" in norm_p
                    or "\\09_apps_catholicjarvis\\" in norm_p
                    or "\\tools\\" in norm_p
                    or "\\scripts\\" in norm_p
                )

                node_id = norm_p
                stem = os.path.splitext(fname)[0].lower()

                node_data = {
                    "id": node_id,
                    "name": fname,
                    "stem": stem,
                    "path": full_p,
                    "rel_path": rel_to_proj,
                    "root_label": root_info["label"],
                    "category": cat,
                    "academic_tier": tier,
                    "author_type": author,
                    "size": size,
                    "line_count": line_count,
                    "citations": citations,
                    "is_infrastructure": bool(is_infra),
                    "ext": ext,
                    "mtime": mtime,
                    "ctime": ctime,
                    "atime": atime,
                    "mtime_iso": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "ctime_iso": datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S"),
                    "atime_iso": datetime.fromtimestamp(atime).strftime("%Y-%m-%d %H:%M:%S"),
                    "temporal_month": datetime.fromtimestamp(mtime).strftime("%Y-%m"),
                    "temporal_year": datetime.fromtimestamp(mtime).strftime("%Y"),
                    "snippet": snippet[:350],
                    "topics": topics_matched,
                    "referenced_targets": referenced_targets,
                    "color_var": CATEGORY_META.get(cat, {}).get("color_var", "var(--text-main)"),
                    "badge": CATEGORY_META.get(cat, {}).get("badge", "Doc")
                }

                nodes[node_id] = node_data

                name_lower = fname.lower()
                name_to_id.setdefault(name_lower, []).append(node_id)
                stem_to_id.setdefault(stem, []).append(node_id)

                if total_scanned >= max_files:
                    break
            if total_scanned >= max_files:
                break

    # Pass 2: Build Directed Genealogy Edges ("What file caused which file")
    edge_seen: Set[Tuple[str, str]] = set()

    GENERIC_FILENAMES = {
        "manifest.json", "readme.md", "__init__.py", "index.html", "package.json",
        "settings.json", "config.json", "license.txt", "notes.txt", "styles.css", "app.py"
    }

    for node_id, node in nodes.items():
        targets = node.get("referenced_targets", [])
        for target_str in targets:
            target_lower = target_str.lower()
            if target_lower in GENERIC_FILENAMES:
                continue
            target_stem = os.path.splitext(target_lower)[0]
            if len(target_stem) < 4:
                continue

            matched_ids = name_to_id.get(target_lower) or stem_to_id.get(target_stem) or []
            if len(matched_ids) > 4:
                continue

            for target_id in matched_ids:
                if target_id == node_id:
                    continue

                source_node = nodes[node_id]
                target_node = nodes[target_id]

                # Determine direction: Progenitor -> Derivative
                # If target was modified earlier or is a lower tier (Source -> Dossier -> Chapter),
                # target caused node!
                if target_node["mtime"] <= source_node["mtime"] or target_node["academic_tier"] < source_node["academic_tier"]:
                    parent_id = target_id
                    child_id = node_id
                    relation = "synthesizes" if source_node["academic_tier"] > target_node["academic_tier"] else "cites"
                else:
                    parent_id = node_id
                    child_id = target_id
                    relation = "derived_from"

                edge_key = (parent_id, child_id)
                if edge_key not in edge_seen:
                    edge_seen.add(edge_key)
                    edges.append({
                        "source": parent_id,
                        "target": child_id,
                        "relation": relation,
                        "weight": 2.0 if relation == "synthesizes" else 1.0,
                        "label": relation.replace("_", " ").title()
                    })

    # Pass 3: Thematic Ancestry Inferences (for files with 3+ overlapping topics across tiers)
    topic_buckets: Dict[str, List[str]] = {}
    for node_id, node in nodes.items():
        for top in node.get("topics", []):
            topic_buckets.setdefault(top, []).append(node_id)

    for top, id_list in topic_buckets.items():
        if 2 <= len(id_list) <= 25:
            # Group by tier
            by_tier = {}
            for nid in id_list:
                t = nodes[nid]["academic_tier"]
                by_tier.setdefault(t, []).append(nid)

            # Link lower tier progenitors (Sources 0, Dossiers 1) to higher tier (Drafts 2, Master 3)
            for low_tier in [0, 1]:
                progenitors = by_tier.get(low_tier, [])
                for high_tier in [2, 3]:
                    derivatives = by_tier.get(high_tier, [])
                    for anc_id in progenitors[:3]:
                        for desc_id in derivatives[:3]:
                            if nodes[desc_id]["mtime"] >= nodes[anc_id]["mtime"]:
                                edge_key = (anc_id, desc_id)
                                if edge_key not in edge_seen:
                                    edge_seen.add(edge_key)
                                    edges.append({
                                        "source": anc_id,
                                        "target": desc_id,
                                        "relation": "temporal_precursor",
                                        "weight": 0.8,
                                        "label": f"Thematic: {top}"
                                    })

    return {
        "nodes": nodes,
        "edges": edges,
        "indexed_at": datetime.now().isoformat(),
        "total_nodes": len(nodes),
        "total_edges": len(edges)
    }


def reindex_async():
    """Trigger background re-indexing with thread locking."""
    global _index_state

    with _lock:
        if _index_state["status"] == "running":
            return _index_state
        _index_state["status"] = "running"
        _index_state["error"] = None

    def worker():
        global _index_state
        try:
            data = scan_corpus()
            tmp = CACHE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            if os.path.exists(CACHE_FILE):
                os.replace(tmp, CACHE_FILE)
            else:
                os.rename(tmp, CACHE_FILE)

            with _lock:
                _index_state["status"] = "ready"
                _index_state["total_files"] = data["total_nodes"]
                _index_state["last_indexed"] = data["indexed_at"]
        except Exception as e:
            with _lock:
                _index_state["status"] = "error"
                _index_state["error"] = f"{type(e).__name__}: {str(e)}"

    t = threading.Thread(target=worker, daemon=True, name="navigator-reindex")
    t.start()
    return _index_state


_SCAN_CACHE = {"key": None, "value": None}


def get_cached_or_scan() -> Dict[str, Any]:
    """Retrieve indexed dataset from cache, or scan on demand.

    Previously re-parsed the full 10 MB navigator_cache.json from disk on EVERY call -- every hit
    of /api/navigator/tree or /api/navigator/genealogy paid this, measured at 261ms/161ms under
    tools/stress_suite.py, two of the suite's slowest routes. Added an in-process (mtime, size)
    cache, same pattern as the recall_index.json fix applied elsewhere this session -- the parsed
    dict is kept in memory and only re-read when the cache file on disk actually changes."""
    if os.path.exists(CACHE_FILE):
        try:
            st = os.stat(CACHE_FILE)
            cache_key = (CACHE_FILE, st.st_mtime, st.st_size)
            if _SCAN_CACHE["key"] == cache_key:
                return _SCAN_CACHE["value"]
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            _SCAN_CACHE["key"] = cache_key
            _SCAN_CACHE["value"] = data
            return data
        except Exception:
            pass
    data = scan_corpus()
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        st = os.stat(CACHE_FILE)
        _SCAN_CACHE["key"] = (CACHE_FILE, st.st_mtime, st.st_size)
        _SCAN_CACHE["value"] = data
    except Exception:
        pass
    return data


def build_treemap(
    data: Dict[str, Any],
    sort_by: str = "mtime",
    group_by: str = "category",
    size_metric: str = "size",
    root_filter: Optional[str] = None,
    exclude_infrastructure: bool = False,
    chrono_max_month: Optional[str] = None
) -> Dict[str, Any]:
    """
    Construct hierarchical Treemap JSON structure.
    group_by options: 'category', 'academic_tier', 'temporal_month', 'folder'
    sort_by options: 'mtime', 'ctime', 'atime', 'size', 'lines', 'citations', 'name'
    size_metric options: 'size', 'lines', 'citations'
    """
    nodes = data.get("nodes", {})
    root: Dict[str, Any] = {
        "name": "Corpus Knowledge Base",
        "category": "root",
        "color_var": "var(--bg-base)",
        "children": []
    }

    sort_keys = {
        "mtime": lambda n: n.get("mtime", 0),
        "ctime": lambda n: n.get("ctime", 0),
        "atime": lambda n: n.get("atime", 0),
        "size": lambda n: n.get("size", 0),
        "lines": lambda n: n.get("line_count", 0),
        "citations": lambda n: n.get("citations", 0),
        "name": lambda n: n.get("name", "").lower()
    }
    reverse_sort = sort_by != "name"
    key_func = sort_keys.get(sort_by, sort_keys["mtime"])

    filtered_nodes = list(nodes.values())
    if root_filter:
        filtered_nodes = [n for n in filtered_nodes if root_filter.lower() in n.get("root_label", "").lower()]
    if exclude_infrastructure:
        filtered_nodes = [n for n in filtered_nodes if not n.get("is_infrastructure", False)]
    if chrono_max_month:
        filtered_nodes = [n for n in filtered_nodes if (n.get("temporal_month") or "") <= chrono_max_month]

    groups: Dict[str, List[Dict[str, Any]]] = {}

    for node in filtered_nodes:
        if group_by == "category":
            grp_key = node.get("category", "other")
        elif group_by == "academic_tier":
            grp_key = f"Tier {node.get('academic_tier', 1)}"
        elif group_by == "temporal_month":
            grp_key = node.get("temporal_month", "Unknown Date")
        elif group_by == "folder":
            p = node.get("path", "")
            d = os.path.dirname(p)
            grp_key = os.path.basename(d) or "Root"
        else:
            grp_key = node.get("category", "other")

        groups.setdefault(grp_key, []).append(node)

    for grp_name, group_items in groups.items():
        sorted_items = sorted(group_items, key=key_func, reverse=reverse_sort)
        group_node: Dict[str, Any] = {
            "name": grp_name.replace("_", " ").title(),
            "group_key": grp_name,
            "category": group_items[0].get("category", "other") if group_by == "category" else "group",
            "color_var": CATEGORY_META.get(grp_name, {}).get("color_var", "var(--accent-blue)") if group_by == "category" else "var(--accent-cyan)",
            "children": []
        }

        for item in sorted_items:
            if size_metric == "citations":
                val = max(1, item.get("citations", 0))
            elif size_metric == "lines":
                val = max(1, item.get("line_count", 1))
            else:
                val = max(1, item.get("size", 1))

            group_node["children"].append({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "path": item.get("path", ""),
                "value": max(1, val),
                "size_bytes": item.get("size", 0),
                "lines": item.get("line_count", 0),
                "citations": item.get("citations", 0),
                "is_infrastructure": item.get("is_infrastructure", False),
                "category": item.get("category", "other"),
                "academic_tier": item.get("academic_tier", 1),
                "author_type": item.get("author_type", "hybrid"),
                "mtime_iso": item.get("mtime_iso", ""),
                "ctime_iso": item.get("ctime_iso", ""),
                "atime_iso": item.get("atime_iso", ""),
                "temporal_month": item.get("temporal_month", ""),
                "color_var": item.get("color_var", "var(--text-main)"),
                "badge": item.get("badge", "Doc"),
                "snippet": item.get("snippet", "")
            })

        root["children"].append(group_node)

    return root


def get_genealogy_graph(
    data: Dict[str, Any],
    file_id: Optional[str] = None,
    depth: int = 2,
    category: Optional[str] = None,
    exclude_infrastructure: bool = False,
    chrono_max_month: Optional[str] = None
) -> Dict[str, Any]:
    """Extract ego network or full directed lineage graph with infrastructure and chrono filtering."""
    nodes = data.get("nodes", {})
    edges = data.get("edges", [])

    if not file_id:
        # Global graph with filtering
        filtered_nodes = []
        node_id_set = set()

        for nid, n in nodes.items():
            if category and n.get("category") != category:
                continue
            if exclude_infrastructure and n.get("is_infrastructure", False):
                continue
            if chrono_max_month and (n.get("temporal_month") or "") > chrono_max_month:
                continue
            node_id_set.add(nid)
            filtered_nodes.append({
                "id": nid,
                "label": n["name"],
                "category": n["category"],
                "academic_tier": n["academic_tier"],
                "size": n["size"],
                "lines": n["line_count"],
                "citations": n.get("citations", 0),
                "is_infrastructure": n.get("is_infrastructure", False),
                "color_var": n["color_var"],
                "author_type": n["author_type"],
                "temporal_month": n.get("temporal_month", "")
            })

        filtered_edges = [
            e for e in edges if e["source"] in node_id_set and e["target"] in node_id_set
        ]
        return {
            "nodes": filtered_nodes[:800],
            "edges": filtered_edges[:2000],
            "stats": {"node_count": len(filtered_nodes), "edge_count": len(filtered_edges)}
        }

    # Ego network centered around file_id
    norm_target = os.path.normcase(os.path.abspath(file_id))
    visited_nodes: Set[str] = {norm_target}
    included_edges: List[Dict[str, Any]] = []

    current_frontier = {norm_target}

    for _ in range(depth):
        next_frontier = set()
        for e in edges:
            src, tgt = e["source"], e["target"]
            if src in current_frontier and tgt not in visited_nodes:
                visited_nodes.add(tgt)
                next_frontier.add(tgt)
                included_edges.append(e)
            elif tgt in current_frontier and src not in visited_nodes:
                visited_nodes.add(src)
                next_frontier.add(src)
                included_edges.append(e)
            elif src in visited_nodes and tgt in visited_nodes and e not in included_edges:
                included_edges.append(e)
        current_frontier = next_frontier
        if not current_frontier:
            break

    result_nodes = []
    for nid in visited_nodes:
        n = nodes.get(nid)
        if n:
            if exclude_infrastructure and n.get("is_infrastructure", False) and nid != norm_target:
                continue
            if chrono_max_month and (n.get("temporal_month") or "") > chrono_max_month and nid != norm_target:
                continue
            result_nodes.append({
                "id": nid,
                "label": n["name"],
                "category": n["category"],
                "academic_tier": n["academic_tier"],
                "size": n["size"],
                "lines": n["line_count"],
                "citations": n.get("citations", 0),
                "is_infrastructure": n.get("is_infrastructure", False),
                "color_var": n["color_var"],
                "author_type": n["author_type"],
                "temporal_month": n.get("temporal_month", ""),
                "is_focus": nid == norm_target
            })

    return {
        "nodes": result_nodes,
        "edges": included_edges,
        "focus_id": norm_target,
        "stats": {"node_count": len(result_nodes), "edge_count": len(included_edges)}
    }


def get_file_preview(path: str) -> Dict[str, Any]:
    """Retrieve full preview, rendered HTML, upstream parents, and downstream children."""
    norm = os.path.normcase(os.path.abspath(path))
    data = get_cached_or_scan()
    nodes = data.get("nodes", {})
    edges = data.get("edges", [])

    node = nodes.get(norm)
    if not node and os.path.exists(path):
        cat, tier = classify_file(path)
        st = os.stat(path)
        node = {
            "id": norm,
            "name": os.path.basename(path),
            "path": os.path.abspath(path),
            "category": cat,
            "academic_tier": tier,
            "size": st.st_size,
            "line_count": 0,
            "mtime_iso": datetime.fromtimestamp(st.st_mtime).isoformat(),
            "color_var": CATEGORY_META.get(cat, {}).get("color_var", "var(--text-main)"),
            "badge": CATEGORY_META.get(cat, {}).get("badge", "Doc")
        }

    if not node:
        raise FileNotFoundError(f"File not found: {path}")

    # Discover upstream parents (edges where target == norm)
    upstream = []
    for e in edges:
        if e["target"] == norm:
            src_node = nodes.get(e["source"])
            if src_node:
                upstream.append({
                    "id": src_node["id"],
                    "name": src_node["name"],
                    "path": src_node["path"],
                    "category": src_node["category"],
                    "relation": e["relation"],
                    "color_var": src_node["color_var"]
                })

    # Discover downstream children (edges where source == norm)
    downstream = []
    for e in edges:
        if e["source"] == norm:
            tgt_node = nodes.get(e["target"])
            if tgt_node:
                downstream.append({
                    "id": tgt_node["id"],
                    "name": tgt_node["name"],
                    "path": tgt_node["path"],
                    "category": tgt_node["category"],
                    "relation": e["relation"],
                    "color_var": tgt_node["color_var"]
                })

    raw_content = ""
    if os.path.exists(node["path"]):
        try:
            with open(node["path"], "r", encoding="utf-8", errors="replace") as f:
                raw_content = f.read(80000)
        except Exception:
            raw_content = f"Binary or unreadable file: {node['path']}"

    return {
        "metadata": node,
        "upstream_parents": upstream,
        "downstream_derivatives": downstream,
        "content_sample": raw_content,
        "can_open_external": True
    }
