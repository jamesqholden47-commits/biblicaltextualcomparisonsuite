"""
Vault Deduplicator & State Concordance Engine
Scans all Obsidian vault directories, contingency backups, and project clones.
Computes L3 SHA-256 byte hashes to identify exact duplicate clusters, version drift,
and unique files. Prevents multi-million token ingestion of redundant clone states.
Adheres strictly to Rule 6 (L3 byte-hash verification) and Rule 11 (Lossless preservation).
"""

import os
import io
import re
import json
import time
import hashlib
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

OUTPUT_JSON = os.path.join(DATA_DIR, "vault_concordance.json")
OUTPUT_MD = os.path.join(DATA_DIR, "vault_concordance.md")

# Known Vault and Clone Roots on James's machine
VAULT_ROOTS = [
    {"id": "aa1_live", "name": "AA1 Live Vault", "path": r"C:\Users\Elation\aa1", "type": "active_vault"},
    {"id": "project_root", "name": "History Proves Catholicism Project", "path": r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism", "type": "project_master"},
    {"id": "dxm_parent", "name": "DXM Parent Vault", "path": r"C:\Users\Elation\DXM", "type": "parent_vault"},
    {"id": "aadesktop_dxm", "name": "AADesktop DXM Clone", "path": r"C:\Users\Elation\aadesktop\DXM", "type": "clone"},
    {"id": "academia", "name": "Academia Vault", "path": r"C:\Users\Elation\Academia", "type": "sub_vault"},
    {"id": "downloads_backup", "name": "Downloads AA1 Contingency Backup", "path": r"C:\Users\Elation\Downloads\OBSIDIAN_VAULTS_BACKUP_CONTINGENCY\aa1", "type": "backup_contingency"},
    {"id": "desktop_easy", "name": "Desktop Easy Notes", "path": r"C:\Users\Elation\Desktop\Easy", "type": "staging"},
    {"id": "usb_backup_elation", "name": "USB Backup Elation", "path": r"C:\Users\Elation\USB_Backup\Elation", "type": "cold_backup"},
    {"id": "usb_backup_protocol", "name": "USB Backup Protocol Layout", "path": r"C:\Users\Elation\USB_Backup\PlanningObsidianProtocolLayout", "type": "cold_backup"}
]

SKIP_FOLDERS = {
    "node_modules", ".obsidian", ".trash", "__pycache__", ".git", ".venv", "venv",
    ".system_generated", "audio_cache", "site-packages", "AppData"
}

def compute_file_sha256(path: str) -> str:
    """Compute full L3 byte-hash of file content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def extract_title_and_snippet(path: str) -> Tuple[str, str, int]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        content = ""

    lines = content.splitlines()
    title = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
    for line in lines[:15]:
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break

    words = len(content.split())
    # Extract clean preview snippet
    snippet_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    snippet = " ".join(snippet_lines[:3])[:220]
    return title, snippet, words

def scan_vaults() -> Dict[str, Any]:
    print("[Vault Dedup] Starting scan across known vault roots...")
    t0 = time.time()

    all_files = []
    hash_to_files: Dict[str, List[Dict[str, Any]]] = {}
    name_to_files: Dict[str, List[Dict[str, Any]]] = {}

    for vault in VAULT_ROOTS:
        v_path = vault["path"]
        v_id = vault["id"]
        v_name = vault["name"]

        if not os.path.exists(v_path):
            continue

        print(f"  Scanning vault: {v_name} ({v_path})...")
        for root, dirs, files in os.walk(v_path):
            dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS and not d.startswith(".")]
            for f in files:
                if f.endswith(".md"):
                    full_p = os.path.join(root, f)
                    try:
                        st = os.stat(full_p)
                        size = st.st_size
                        mtime = st.st_mtime
                        sha = compute_file_sha256(full_p)
                        title, snippet, word_cnt = extract_title_and_snippet(full_p)

                        record = {
                            "vault_id": v_id,
                            "vault_name": v_name,
                            "vault_type": vault["type"],
                            "path": full_p,
                            "rel_path": os.path.relpath(full_p, v_path).replace("\\", "/"),
                            "filename": f,
                            "title": title,
                            "size": size,
                            "mtime": mtime,
                            "mtime_iso": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
                            "sha256": sha,
                            "words": word_cnt,
                            "snippet": snippet
                        }

                        all_files.append(record)

                        if sha not in hash_to_files:
                            hash_to_files[sha] = []
                        hash_to_files[sha].append(record)

                        if f not in name_to_files:
                            name_to_files[f] = []
                        name_to_files[f].append(record)

                    except Exception as err:
                        pass

    # Analyze Clusters
    exact_duplicate_clusters = []
    unique_files = []

    for sha, flist in hash_to_files.items():
        if len(flist) > 1:
            # Sort instances by mtime desc (newest first)
            flist.sort(key=lambda x: x["mtime"], reverse=True)
            exact_duplicate_clusters.append({
                "sha256": sha,
                "count": len(flist),
                "canonical": flist[0],  # Newest instance considered candidate canonical
                "instances": flist,
                "size": flist[0]["size"],
                "words": flist[0]["words"],
                "title": flist[0]["title"]
            })
        else:
            unique_files.append(flist[0])

    exact_duplicate_clusters.sort(key=lambda x: x["count"], reverse=True)
    unique_files.sort(key=lambda x: x["mtime"], reverse=True)

    # Name collisions with drift (same filename, differing SHA)
    drifted_files = []
    for fname, flist in name_to_files.items():
        shas = {x["sha256"] for x in flist}
        if len(shas) > 1:
            flist.sort(key=lambda x: x["mtime"], reverse=True)
            drifted_files.append({
                "filename": fname,
                "variants_count": len(shas),
                "instances_count": len(flist),
                "variants": flist
            })

    drifted_files.sort(key=lambda x: -x["variants_count"])

    total_scanned = len(all_files)
    total_unique_hashes = len(hash_to_files)
    total_duplicate_instances = total_scanned - total_unique_hashes

    # Compute redundant byte waste
    redundant_bytes = sum(c["size"] * (c["count"] - 1) for c in exact_duplicate_clusters)
    redundant_words = sum(c["words"] * (c["count"] - 1) for c in exact_duplicate_clusters)

    # Breakdown by Vault
    vault_file_counts = {}
    for f in all_files:
        vid = f["vault_name"]
        vault_file_counts[vid] = vault_file_counts.get(vid, 0) + 1

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scan_duration_seconds": round(time.time() - t0, 2),
        "total_files_scanned": total_scanned,
        "total_unique_documents": total_unique_hashes,
        "duplicate_clusters_count": len(exact_duplicate_clusters),
        "total_duplicate_copies": total_duplicate_instances,
        "redundant_bytes_wasted": redundant_bytes,
        "redundant_words_wasted": redundant_words,
        "vault_breakdown": vault_file_counts,
        "exact_duplicate_clusters": exact_duplicate_clusters,
        "unique_documents_count": len(unique_files),
        "unique_documents": unique_files,
        "version_drift_files_count": len(drifted_files),
        "version_drift_files": drifted_files
    }

    # Atomic write to JSON
    tmp_json = OUTPUT_JSON + ".tmp"
    with open(tmp_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    os.replace(tmp_json, OUTPUT_JSON)

    # Generate Markdown Summary
    md_lines = [
        "# 🗺️ OBSIDIAN VAULT CONCORDANCE & DEDUPLICATION LEDGER",
        "",
        f"**Generated:** {result['generated_at']} | **Scan Duration:** {result['scan_duration_seconds']}s",
        "",
        "## 📊 Executive Overview",
        f"- **Total Markdown Notes Scanned:** {total_scanned:,}",
        f"- **True Distinct Documents (Unique SHA-256):** {total_unique_hashes:,}",
        f"- **Duplicate Clusters Detected:** {len(exact_duplicate_clusters):,}",
        f"- **Redundant Copy Count:** {total_duplicate_instances:,}",
        f"- **Token/Word Redundancy Prevented:** {redundant_words:,} words ({redundant_bytes / 1024 / 1024:.2f} MB)",
        "",
        "### 🏛️ Vault Breakdown",
        "| Vault Name | File Count |",
        "|---|---:|"
    ]
    for vname, cnt in sorted(vault_file_counts.items(), key=lambda x: -x[1]):
        md_lines.append(f"| {vname} | {cnt:,} |")

    md_lines.extend([
        "",
        "---",
        "## 👥 Top Duplicate Clusters (Byte-Identical L3)",
        "| Document Title | Filename | Duplicates | Size | Canonical Location |",
        "|---|---|:---:|---:|---|"
    ])

    for cl in exact_duplicate_clusters[:25]:
        canon = cl["canonical"]
        md_lines.append(f"| **{cl['title']}** | `{canon['filename']}` | **{cl['count']} copies** | {cl['size']:,} B | `{canon['vault_name']}`: {canon['rel_path']} |")

    md_lines.extend([
        "",
        "---",
        "## ⚠️ Version Drift (Same Name, Diverged Content)",
        "| Filename | Distinct Hashes | Total Instances | Newest Instance |",
        "|---|:---:|:---:|---|"
    ])

    for dr in drifted_files[:20]:
        newest = dr["variants"][0]
        md_lines.append(f"| `{dr['filename']}` | **{dr['variants_count']} versions** | {dr['instances_count']} | `{newest['vault_name']}` ({newest['mtime_iso'][:10]}) |")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"[Vault Dedup] Completed in {result['scan_duration_seconds']}s.")
    print(f"  Scanned: {total_scanned:,} notes")
    print(f"  Unique: {total_unique_hashes:,} documents")
    print(f"  Duplicate Clusters: {len(exact_duplicate_clusters):,}")
    print(f"  Redundant Words: {redundant_words:,}")
    return result

if __name__ == "__main__":
    scan_vaults()
