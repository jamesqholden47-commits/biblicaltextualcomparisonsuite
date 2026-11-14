"""
tools/make_episode_briefs.py  (Task C005, 2026-10-03)

Writes WORKER_CONTRACT v1 briefs asking a worker for a podcast script JSON file
whose every figure is either hedged or traceable in the chapter.
Writes to:
C:\\Users\\Elation\\DXM\\Clippings\\_PROJECT_HistoryProvesCatholicism\\08_INTAKE\\_WORKER_INBOX\\EPISODES\\<chapter stem>\\BRIEF.md
Refuses to overwrite an existing brief.
Generated briefs must pass worker_gates.py brief.
"""
import os
import sys
import argparse

PROJECT_ROOT = r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism"
INBOX_EPISODES = os.path.join(PROJECT_ROOT, "08_INTAKE", "_WORKER_INBOX", "EPISODES")
CONTRACT_PATH = os.path.join(PROJECT_ROOT, "02_CONTROL_AND_STATE", "_WORKER_SPEC", "WORKER_CONTRACT.md")
CHAPTERS_DIR = r"C:\Users\Elation\Mexico_Protestantism_Study\05_READERS_EDITION\chapters"
WORKER_GATES = os.path.join(PROJECT_ROOT, "02_CONTROL_AND_STATE", "_WORKER_SPEC", "worker_gates.py")


def generate_episode_brief(chapter_stem: str, chapter_title: str) -> str:
    """Generate a valid WORKER_CONTRACT v1 brief for producing an episode script JSON."""
    if not os.path.exists(CONTRACT_PATH):
        raise FileNotFoundError(f"Contract file not found at {CONTRACT_PATH}")

    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        contract_text = f.read().rstrip()

    task_id = f"EPISODE-{chapter_stem}"
    out_dir = os.path.join(INBOX_EPISODES, chapter_stem)
    brief_path = os.path.join(out_dir, "BRIEF.md")
    output_path = os.path.join(out_dir, f"{chapter_stem}.script.json")
    chapter_file = os.path.join(CHAPTERS_DIR, f"{chapter_stem}.md")

    if os.path.exists(brief_path):
        raise FileExistsError(f"Brief already exists at {brief_path}; refusing to overwrite.")

    gate_cmd = f'python "{WORKER_GATES}" handback "{output_path}" --class code --task-id {task_id}'

    lines = [
        contract_text,
        "",
        "---",
        "",
        "## TASK",
        f"CODE job, output class code, task id {task_id}: create a two-host conversational podcast script JSON for chapter {chapter_stem}: {chapter_title}, strictly vetted against the chapter's 'still needs checking' lines.",
        "",
        "## CONTEXT",
        f"Source document: {chapter_file} (READ-ONLY).",
        "The podcast script must match the schema in data/podcast_scripts/ (id, title, source_path, speakers, turns).",
        "Fidelity requirement: every figure voiced in the dialogue must appear in the chapter.",
        "Crucial gate rule: any figure mentioned in the chapter's 'Before using this in public: what still needs checking' section MUST be spoken with an audible hedge (e.g. 'unconfirmed', 'still needs checking', 'reportedly', 'if the figure holds'). Unhedged claims fail the builder gate.",
        "",
        "## QUESTIONS",
        f"1. How can the core findings and primary source revelations of {chapter_stem} be scripted into an authentic conversational dialogue between Rachel and Leo?",
        f"2. Does every number, date, and statistic in the dialogue script trace back directly to {chapter_file}?",
        f"3. Is every figure appearing in the 'Before using this in public' section spoken with an explicit hedge to pass podcast_fidelity_check?",
        "",
        "## INPUTS",
        f"- {chapter_file}",
        r"- C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism\09_APPS_CATHOLICJARVIS\_LOG_ANALYSIS_2026-10-03\podcast_fidelity_check.py",
        "",
        "## OWNED FILES",
        f"- {out_dir}\\",
        "",
        "## OUTPUT",
        output_path,
        "",
        "## FORBIDDEN",
        "- Editing any file outside OWNED FILES.",
        "- Using inflation words like 'unassailable', 'irrefutable', 'destroys'.",
        "- Voicing unhedged figures from the needs-checking lines.",
        "",
        "## STOP CONDITIONS",
        "- Stop when the full script JSON is validated and written.",
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
    parser = argparse.ArgumentParser(description="Generate sample episode briefs")
    parser.add_argument("--chapter", default="06_inquisition_black_legend")
    parser.add_argument("--title", default="The Inquisition and the Black Legend")
    args = parser.parse_args()

    try:
        p = generate_episode_brief(args.chapter, args.title)
        print(f"Brief generated successfully at: {p}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
