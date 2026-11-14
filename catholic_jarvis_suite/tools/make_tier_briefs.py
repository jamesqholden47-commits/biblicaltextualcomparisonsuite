"""
Tool to generate WORKER_CONTRACT v1 briefs for 3-tier and Spanish section explanations.
Task C004.
Writes to:
C:\\Users\\Elation\\DXM\\Clippings\\_PROJECT_HistoryProvesCatholicism\\08_INTAKE\\_WORKER_INBOX\\TIERS\\<chapter stem>\\<section>\\BRIEF.md
Refuses to overwrite an existing brief.
Generated briefs must pass worker_gates.py brief.
"""
import os
import sys
import argparse

PROJECT_ROOT = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism"
INBOX_TIERS = os.path.join(PROJECT_ROOT, "08_INTAKE", "_WORKER_INBOX", "TIERS")
CONTRACT_PATH = os.path.join(PROJECT_ROOT, "02_CONTROL_AND_STATE", "_WORKER_SPEC", "WORKER_CONTRACT.md")
CHAPTERS_DIR = r"C:\Users\Elation\Mexico_Protestantism_Study\05_READERS_EDITION\chapters"
WORKER_GATES = os.path.join(PROJECT_ROOT, "02_CONTROL_AND_STATE", "_WORKER_SPEC", "worker_gates.py")


def generate_tier_brief(chapter_stem: str, section_num: str, section_title: str) -> str:
    """Generate a valid WORKER_CONTRACT v1 brief for writing 3-tier + Spanish explanations."""
    if not os.path.exists(CONTRACT_PATH):
        raise FileNotFoundError(f"Contract file not found at {CONTRACT_PATH}")

    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        contract_text = f.read().rstrip()

    task_id = f"TIER-{chapter_stem}-{section_num}"
    out_dir = os.path.join(INBOX_TIERS, chapter_stem, str(section_num))
    brief_path = os.path.join(out_dir, "BRIEF.md")
    output_path = os.path.join(out_dir, f"{section_num}.json")
    chapter_file = os.path.join(CHAPTERS_DIR, f"{chapter_stem}.md")

    if os.path.exists(brief_path):
        raise FileExistsError(f"Brief already exists at {brief_path}; refusing to overwrite.")

    gate_cmd = f'python "{WORKER_GATES}" handback "{output_path}" --class reader --task-id {task_id}'

    lines = [
        contract_text,
        "",
        "---",
        "",
        "## TASK",
        f"REWRITE-READER job, output class reader, task id {task_id}: produce four tiered explanations (plain ELI5, apologist working level, scholarly expert, and Spanish family register) for chapter {chapter_stem} section {section_num}: {section_title}.",
        "",
        "## CONTEXT",
        f"The source chapter is {chapter_file} (READ-ONLY).",
        f"Section {section_num}: {section_title}.",
        "The goal is multi-level pedagogic accessibility without signal loss. Every caveat, tag, and key distinction must be preserved.",
        "Output format is a JSON file matching the schema documented in catholic_jarvis_suite/data/tiers/README.md:",
        '{"chapter": "' + chapter_stem + '", "section": "' + str(section_num) + '", "title": "' + section_title + '", "plain": "...", "working": "...", "expert": "...", "spanish": "..."}',
        "",
        "## QUESTIONS",
        f"1. How can the core argument of section {section_num} be expressed in plain everyday English for a non-specialist while retaining every factual caveat?",
        f"2. How can the working apologist response be structured against standard Protestant objections to section {section_num}?",
        f"3. What exact primary source citations and technical qualifications represent the expert tier for section {section_num}?",
        f"4. How can the section be rendered in a pastoral Spanish family register suitable for Mexican evangelical relatives?",
        "",
        "## INPUTS",
        f"- {chapter_file}",
        "",
        "## OWNED FILES",
        f"- {out_dir}\\",
        "",
        "## OUTPUT",
        output_path,
        "",
        "## FORBIDDEN",
        "- Editing any file outside OWNED FILES.",
        "- Modifying the source chapter.",
        "- Using inflation words like 'unassailable', 'irrefutable', '100%'.",
        "",
        "## STOP CONDITIONS",
        "- Stop when the four tiers are generated and formatted into valid JSON.",
        "- Stop and leave PARTIAL if a usage limit hits.",
        "",
        "## COMPLETION MARKER",
        f"<!-- WORKER COMPLETE: {task_id} -->",
        "",
        "## GATE",
        gate_cmd,
        ""
    ]

    brief_content = "\n".join(lines)
    os.makedirs(out_dir, exist_ok=True)
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write(brief_content)

    return brief_path


def main():
    parser = argparse.ArgumentParser(description="Generate sample tier briefs")
    parser.add_argument("--chapter", default="06_inquisition_black_legend")
    parser.add_argument("--section", default="2")
    parser.add_argument("--title", default="The Mexican tribunal, 1571-1820: what the archives count")
    args = parser.parse_args()

    try:
        p = generate_tier_brief(args.chapter, args.section, args.title)
        print(f"Brief generated successfully at: {p}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
