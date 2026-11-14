"""Build File Genealogy & Causality Graph for CatholicJarvis (stdlib-only, Python 3.12).

Scans dissertation roots, research vaults, and book collections to construct a causal
Directed Acyclic Graph (DAG) of file provenance, textual lineage, and citation flows.

Output: 09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/data/file_genealogy_graph.json
"""

import collections
import concurrent.futures
import datetime
import hashlib
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

# Reconfigure stdout for UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Root Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

OUTPUT_GRAPH_FILE = os.path.join(DATA_DIR, "file_genealogy_graph.json")
CACHE_FILE = os.path.join(DATA_DIR, "_genealogy_cache.json")

CRAWL_ROOTS = [
    (PROJECT_ROOT, "Project"),
    (r"C:\Users\Elation\PDFS", "Books (PDFS)"),
    (r"C:\Users\Elation\Easter\Antigravity\Test", "Easter Scratchpad"),
    (os.path.join(PROJECT_ROOT, "06_SOURCE_MATERIAL", "RABBINIC_CORPUS_SEFARIA"), "Sefaria"),
    (os.path.join(PROJECT_ROOT, "10_VOLUMES"), "Volumes"),
]

SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", ".obsidian", ".trash",
    ".venv", "venv", ".pytest_cache", "audio_cache", "_TIMECAPSULE_2026-07-22",
    "Rockstar Games", "SOLIDWORKS Downloads", "STAR WARS Battlefront II"
}
VALID_EXTS = {".md", ".txt", ".json", ".py", ".pdf", ".docx", ".epub"}

NODE_PALETTE = {
    "BOOK": {"color": "#D97706", "icon": "📖", "tier": 0},
    "NOTE": {"color": "#059669", "icon": "📝", "tier": 0},
    "REPORT": {"color": "#0284C7", "icon": "📋", "tier": 1},
    "SCRIPT": {"color": "#10B981", "icon": "⚙️", "tier": 1},
    "DOSSIER": {"color": "#7C3AED", "icon": "📜", "tier": 2},
    "CONTROL_STATE": {"color": "#B45309", "icon": "🏛️", "tier": 2},
    "TRANSCRIPT": {"color": "#475569", "icon": "💬", "tier": 2},
    "MONOGRAPH": {"color": "#DC2626", "icon": "📚", "tier": 3},
    "DISSERTATION_MASTER": {"color": "#F59E0B", "icon": "👑", "tier": 4},
}

# Derived Artifact Exclusion Guard (loss_check.py 2026-08-01 invariant)
CIRCULARITY_EXCLUSIONS = {
    "01_MASTER_DISSERTATION/_CONSOLIDATED_DISSERTATION_2026-08-01.md": [
        "03_RESEARCH_DOSSIERS/_SANDBOX_MIDRASH_HALAKHA_2026-07-27/_N5_MIDRASH_HALAKHA_BINDINGNESS_DISSERTATION.md"
    ]
}


def normalize_line(line: str) -> str:
    """Normalize line per Rule 14 & loss_check.py: strip footnotes, code spans, HTML."""
    s = re.sub(r"\[\^[^\]]*\]", " ", line)
    s = re.sub(r"`[^`]*`", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def extract_substantive_sentences(text: str) -> List[str]:
    """Extract substantive lines (>= 40 chars, skipping markdown syntax)."""
    sentences = []
    for raw in text.split("\n"):
        r = raw.strip()
        if not r or r.startswith(("#", "|", "---", "===", ">")):
            continue
        n = normalize_line(r)
        if len(n) >= 40:
            sentences.append(n)
    return sentences


def classify_node_type(path: str, content: str = "") -> str:
    """Classify file into one of the 9 ontological types."""
    p_lower = path.lower()
    base = os.path.basename(path).lower()

    if p_lower.startswith(r"c:\users\elation\pdfs") or p_lower.endswith(".pdf"):
        return "BOOK"
    if "01_master_dissertation" in p_lower:
        return "DISSERTATION_MASTER"
    if "10_volumes" in p_lower or "05_drafts" in p_lower or base.startswith("monograph_"):
        return "MONOGRAPH"
    if "03_research_dossiers" in p_lower or base.startswith("dossier_"):
        return "DOSSIER"
    if (p_lower.endswith((".py", ".ps1", ".bat", ".sh")) or 
        "tools" in p_lower or ("02_control_and_state" in p_lower and p_lower.endswith(".py"))):
        return "SCRIPT"
    if any(k in base for k in ("_boot_header", "_live_checkpoint", "taskboard", "_session_checkpoint", "ledger")):
        return "CONTROL_STATE"
    if any(k in p_lower for k in ("_session_transcripts", "_ag_session_log", "transcript")):
        return "TRANSCRIPT"
    if any(k in p_lower for k in ("audit", "report", "receipt", "sweep")):
        return "REPORT"
    if any(k in p_lower for k in ("easter", ".gemini", "scratch", "notes")):
        return "NOTE"
    return "NOTE"


def scan_file_metadata(filepath: str, vault_label: str) -> Optional[Dict[str, Any]]:
    """Scan a single file for metadata, content fingerprints, and links."""
    try:
        stat = os.stat(filepath)
    except OSError:
        return None

    mtime_dt = datetime.datetime.fromtimestamp(stat.st_mtime, tz=datetime.timezone.utc).isoformat()
    ctime_dt = datetime.datetime.fromtimestamp(stat.st_ctime, tz=datetime.timezone.utc).isoformat()
    size = stat.st_size
    filename = os.path.basename(filepath)

    node_type = classify_node_type(filepath)
    rel_path = os.path.relpath(filepath, PROJECT_ROOT).replace("\\", "/") if filepath.startswith(PROJECT_ROOT) else filepath

    meta: Dict[str, Any] = {
        "id": hashlib.sha1(filepath.lower().encode("utf-8")).hexdigest()[:16],
        "label": filename,
        "path": filepath,
        "rel_path": rel_path,
        "vault_root": vault_label,
        "type": node_type,
        "tier": NODE_PALETTE[node_type]["tier"],
        "color": NODE_PALETTE[node_type]["color"],
        "icon": NODE_PALETTE[node_type]["icon"],
        "size_bytes": size,
        "substantive_lines": 0,
        "mtime": mtime_dt,
        "ctime": ctime_dt,
        "explicit_links": [],
        "sentences": [],
        "headers": {},
    }

    # Only read content for markdown and text notes under 5 MB
    if filepath.endswith((".md", ".markdown", ".txt")) and size < 5 * 1024 * 1024:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError:
            content = ""

        # Extract explicit links: [label](target) and [[wiki]]
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        wiki_links = re.findall(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]", content)
        meta["explicit_links"] = [target for _, target in md_links if not target.startswith("http")] + wiki_links

        # Extract structured header fields
        for line in content.split("\n")[:30]:
            if ":" in line and not line.startswith(("#", "|", "---")):
                k, _, v = line.partition(":")
                k_clean = k.strip().lower()
                if k_clean in ("classification", "status", "target path", "epistemic standard", "author", "agent role"):
                    meta["headers"][k_clean] = v.strip()

        # Extract substantive sentences only for doctoral documents
        if node_type in ("DOSSIER", "MONOGRAPH", "DISSERTATION_MASTER"):
            sentences = extract_substantive_sentences(content)
            meta["substantive_lines"] = len(sentences)
            meta["sentences"] = sentences

    return meta


def build_genealogy_graph(quick: bool = False) -> Dict[str, Any]:
    """Execute the full crawling, link resolution, fingerprinting, and DAG assembly."""
    t0 = time.time()
    nodes: Dict[str, Dict[str, Any]] = {}
    path_to_id: Dict[str, str] = {}
    name_to_ids: Dict[str, List[str]] = collections.defaultdict(list)

    print("🔍 Step 1: Crawling filesystem roots...")
    files_to_scan = []
    for root_path, label in CRAWL_ROOTS:
        if not os.path.exists(root_path):
            continue
        for dp, dn, fn in os.walk(root_path):
            dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith(".")]
            for f in fn:
                ext = os.path.splitext(f)[1].lower()
                if ext in VALID_EXTS:
                    fp = os.path.join(dp, f)
                    files_to_scan.append((fp, label))

    print(f"   Found {len(files_to_scan):,} total files to evaluate.", flush=True)

    # Parallel metadata extraction
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = pool.map(lambda x: scan_file_metadata(x[0], x[1]), files_to_scan)
        for r in results:
            if r:
                nodes[r["id"]] = r
                norm_p = os.path.normpath(r["path"]).lower()
                path_to_id[norm_p] = r["id"]
                name_to_ids[os.path.basename(r["path"]).lower()].append(r["id"])

    print(f"   Successfully indexed {len(nodes):,} candidate nodes.")

    # Step 2: Establish Edges
    print("🔗 Step 2: Resolving causal edges (Citations, Textual Lineage, Session Manifests)...")
    edges: List[Dict[str, Any]] = []
    edge_seen: Set[Tuple[str, str, str]] = set()

    def add_edge(u: str, v: str, rel: str, conf: float, ev_type: str, detail: str = ""):
        key = (u, v, rel)
        if key not in edge_seen and u != v:
            edge_seen.add(key)
            edges.append({
                "source": u,
                "target": v,
                "relation": rel,
                "confidence": round(conf, 2),
                "evidence_type": ev_type,
                "evidence_detail": detail
            })

    # Layer 1: Explicit Links
    for nid, n in nodes.items():
        src_path = n["path"]
        src_dir = os.path.dirname(src_path)

        for target in n.get("explicit_links", []):
            target_norm = os.path.normpath(os.path.join(src_dir, target)).lower()
            tid = path_to_id.get(target_norm)

            if not tid:
                # Try filename match
                target_base = os.path.basename(target).lower()
                cands = name_to_ids.get(target_base, [])
                if len(cands) == 1:
                    tid = cands[0]

            if tid:
                # Direction: Target is the parent source, Source is referencing it
                target_node = nodes[tid]
                if n["tier"] > target_node["tier"]:
                    add_edge(tid, nid, "derived_from", 0.95, "EXPLICIT_CITATION", f"Explicit citation to {target}")
                else:
                    add_edge(nid, tid, "cites", 0.90, "EXPLICIT_CITATION", f"Reference link to {target}")

    # Layer 2: Inverted Sentence Matching (Lineage)
    print("🧬 Step 3: Fingerprinting substantive sentence lineage...")
    sentence_map: Dict[str, List[str]] = collections.defaultdict(list)
    for nid, n in nodes.items():
        if n["type"] in ("DOSSIER", "MONOGRAPH", "DISSERTATION_MASTER"):
            for s in n.get("sentences", []):
                sentence_map[s].append(nid)

    # Detect parent-child inclusions
    shared_counts: Dict[Tuple[str, str], int] = collections.defaultdict(int)
    for s, nids in sentence_map.items():
        if 1 < len(nids) <= 10:
            for i in range(len(nids)):
                for j in range(i + 1, len(nids)):
                    pair = (nids[i], nids[j])
                    shared_counts[pair] += 1

    for (id_a, id_b), count in shared_counts.items():
        node_a = nodes[id_a]
        node_b = nodes[id_b]

        # Determine direction based on mtime and tier
        mtime_a = node_a["mtime"]
        mtime_b = node_b["mtime"]

        if node_a["tier"] < node_b["tier"] or (node_a["tier"] == node_b["tier"] and mtime_a < mtime_b):
            parent, child = id_a, id_b
            parent_node, child_node = node_a, node_b
        else:
            parent, child = id_b, id_a
            parent_node, child_node = node_b, node_a

        overlap_ratio = count / max(1, parent_node["substantive_lines"])
        if overlap_ratio >= 0.15 or count >= 5:
            rel = "inserted_into" if child_node["type"] == "DISSERTATION_MASTER" else "synthesizes"
            add_edge(parent, child, rel, min(1.0, 0.70 + overlap_ratio * 0.3), "SUBSTRING_OVERLAP",
                     f"{count} shared substantive sentences ({overlap_ratio:.1%})")

    # Clean nodes payload for output (remove bulky sentence array)
    output_nodes = []
    for nid, n in nodes.items():
        node_copy = dict(n)
        node_copy.pop("sentences", None)
        node_copy.pop("explicit_links", None)
        output_nodes.append(node_copy)

    # Step 4: Topological Sort & Validation
    print("📐 Step 4: Computing topological sort and hierarchy...")
    in_degree: Dict[str, int] = {n["id"]: 0 for n in output_nodes}
    adj: Dict[str, List[str]] = collections.defaultdict(list)
    for e in edges:
        adj[e["source"]].append(e["target"])
        in_degree[e["target"]] = in_degree.get(e["target"], 0) + 1

    queue = collections.deque([nid for nid, deg in in_degree.items() if deg == 0])
    topo_order: List[str] = []
    while queue:
        u = queue.popleft()
        topo_order.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    elapsed_ms = round((time.time() - t0) * 1000, 2)
    stats = {
        "total_nodes": len(output_nodes),
        "total_edges": len(edges),
        "nodes_by_type": dict(collections.Counter(n["type"] for n in output_nodes)),
        "edges_by_relation": dict(collections.Counter(e["relation"] for e in edges)),
        "execution_ms": elapsed_ms
    }

    payload = {
        "version": "1.0.0",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "stats": stats,
        "nodes": output_nodes,
        "edges": edges,
        "topological_order": topo_order
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    temp_out = OUTPUT_GRAPH_FILE + f".tmp.{os.getpid()}"
    with open(temp_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(temp_out, OUTPUT_GRAPH_FILE)

    print(f"✅ Finished in {elapsed_ms} ms. Written to: {OUTPUT_GRAPH_FILE}")
    print(f"   Nodes: {stats['total_nodes']:,} | Edges: {stats['total_edges']:,}")
    return payload


if __name__ == "__main__":
    build_genealogy_graph()
