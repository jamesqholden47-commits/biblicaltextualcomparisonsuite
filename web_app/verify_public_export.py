"""Verify that the public export repository contains no private or build-artifact leaks.

Scans C:\\Users\\Elation\\catholic-jarvis-suite-export (or --export-dir) and exits 1 if any
forbidden artifact (.sqlite, plenary_logos_data.json, plenary_logos_suite.html,
sources_cache/, or private full-text translations such as NKJV) is tracked by git
or present on disk outside .gitignore.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

DEFAULT_EXPORT_DIR = Path(r"C:\Users\Elation\catholic-jarvis-suite-export")

FORBIDDEN_SUFFIXES = (".sqlite", ".sqlite-wal", ".sqlite-shm", ".db")
FORBIDDEN_BASENAMES = {
    "plenary_logos_data.json",
    "plenary_logos_suite.html",
}
FORBIDDEN_DIR_PARTS = {"sources_cache"}
TEXT_SCAN_EXTS = {".json", ".jsonl", ".csv", ".tsv", ".txt", ".html", ".js", ".py", ".md"}


def _git_lines(repo_dir: Path, args: list[str]) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return [line for line in proc.stdout.split("\0") if line]


def _is_git_ignored(repo_dir: Path, rel_posix: str) -> bool:
    proc = subprocess.run(
        ["git", "-C", str(repo_dir), "check-ignore", "-q", rel_posix],
        capture_output=True,
    )
    return proc.returncode == 0


def _check_path_pattern(rel_posix: str) -> str | None:
    lower = rel_posix.lower()
    parts = lower.split("/")
    basename = parts[-1]

    if lower.endswith(FORBIDDEN_SUFFIXES):
        return f"forbidden database file ({Path(basename).suffix})"
    if basename in FORBIDDEN_BASENAMES:
        return f"forbidden build artifact ({basename})"
    if any(p in FORBIDDEN_DIR_PARTS for p in parts[:-1]) or basename in FORBIDDEN_DIR_PARTS:
        return "forbidden sources_cache/ path"
    if "nkjv" in basename:
        return "forbidden private translation filename (nkjv)"
    return None


def _check_nkjv_full_text(file_path: Path) -> str | None:
    if file_path.suffix.lower() not in TEXT_SCAN_EXTS:
        return None
    try:
        if file_path.stat().st_size > 150_000_000:
            return "oversized data file (>150 MB)"
        text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return None

    count = text.count("nkjv")
    ext = file_path.suffix.lower()
    threshold = 100 if ext in {".json", ".jsonl", ".csv", ".tsv", ".txt"} else 200
    if count >= threshold:
        return f"suspected private NKJV full-text payload ({count} occurrences of 'nkjv')"
    if (
        ext in {".json", ".jsonl", ".csv", ".tsv", ".txt"}
        and "new king james version" in text
        and file_path.stat().st_size > 1_000_000
    ):
        return f"suspected private NKJV full-text payload ({file_path.stat().st_size} bytes)"
    return None


def verify_export(export_dir: Path) -> int:
    if not export_dir.exists() or not (export_dir / ".git").exists():
        print(f"[FAIL] Export git repository not found at: {export_dir}")
        return 1

    violations: list[str] = []

    tracked = _git_lines(export_dir, ["ls-files", "-z"])
    untracked_unignored = _git_lines(
        export_dir, ["ls-files", "--others", "--exclude-standard", "-z"]
    )

    for label, rel_list in (("tracked", tracked), ("untracked-unignored", untracked_unignored)):
        for rel in rel_list:
            rel_posix = rel.replace("\\", "/")
            reason = _check_path_pattern(rel_posix)
            if reason:
                violations.append(f"[{label}] {rel_posix}: {reason}")
                continue
            full_path = export_dir / rel_posix
            if full_path.is_file():
                nkjv_reason = _check_nkjv_full_text(full_path)
                if nkjv_reason:
                    violations.append(f"[{label}] {rel_posix}: {nkjv_reason}")

    # Belt-and-suspenders filesystem walk: any forbidden file/dir on disk must be gitignored.
    for root, dirs, files in os.walk(export_dir):
        if ".git" in dirs:
            dirs.remove(".git")
        root_path = Path(root)
        for dname in list(dirs):
            d_rel = (root_path / dname).relative_to(export_dir).as_posix()
            if dname.lower() in FORBIDDEN_DIR_PARTS:
                if not _is_git_ignored(export_dir, d_rel + "/"):
                    violations.append(f"[disk-unignored] {d_rel}/: not covered by .gitignore")
                dirs.remove(dname)
        for fname in files:
            f_path = root_path / fname
            f_rel = f_path.relative_to(export_dir).as_posix()
            reason = _check_path_pattern(f_rel)
            if reason and not _is_git_ignored(export_dir, f_rel):
                msg = f"[disk-unignored] {f_rel}: {reason} and not covered by .gitignore"
                if msg not in violations:
                    violations.append(msg)

    print(
        f"Scanned {export_dir}: {len(tracked)} tracked files, "
        f"{len(untracked_unignored)} untracked-unignored files."
    )
    if violations:
        print(f"[FAIL] {len(violations)} export leak violation(s) detected:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("[PASS] Public export is clean: no forbidden files tracked or present outside .gitignore.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify public export repo has no private leaks.")
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=DEFAULT_EXPORT_DIR,
        help=f"Path to export git repo (default: {DEFAULT_EXPORT_DIR})",
    )
    args = parser.parse_args()
    return verify_export(args.export_dir)


if __name__ == "__main__":
    sys.exit(main())
