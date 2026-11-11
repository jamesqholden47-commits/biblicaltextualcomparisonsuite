"""
paths_config.py -- single source of truth for the personal filesystem paths this suite's modules
read from, so a different operator can point the whole suite at their own folders instead of
James's (C:\\Users\\Elation\\...). Every module that used to hardcode one of these paths now calls
get_path(key) instead.

Precedence per key: environment variable JARVIS_<KEY UPPER> > data/jarvis_paths.json > the built-in
default (James's own layout, kept so his running app needs no reconfiguration).
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(_HERE), "data")
CONFIG_FILE = os.path.join(DATA_DIR, "jarvis_paths.json")

DEFAULTS = {
    "home": r"C:\Users\Elation",
    "dissertation_project": r"C:\Users\Elation\DXM\Clippings\_PROJECT_HistoryProvesCatholicism",
    "mexico_study": r"C:\Users\Elation\Mexico_Protestantism_Study",
    "scholar_decade_plan": r"C:\Users\Elation\Scholar_Decade_Plan",
    "aa1_vault": r"C:\Users\Elation\aa1",
    "ag_history_backup": r"C:\Users\Elation\AG_HISTORY_BACKUP",
    "pdfs_dir": r"C:\Users\Elation\PDFS",
    "downloads": r"C:\Users\Elation\Downloads",
    "ocr_index": r"C:\Users\Elation\.ocr_index",
    "research_imports_text": r"C:\Users\Elation\Research_Imports\Text_and_Notes",
    "claude_projects": r"C:\Users\Elation\.claude\projects",
    "gemini_antigravity_brain": r"C:\Users\Elation\.gemini\antigravity\brain",
}


def _load_overrides():
    try:
        if os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        pass
    return {}


_overrides = _load_overrides()


def get_path(key):
    """Resolve a configured root path by key (see DEFAULTS for the full key list).

    Checks, in order: environment variable JARVIS_<KEY UPPER>, data/jarvis_paths.json, then the
    built-in default.
    """
    env_key = "JARVIS_" + key.upper()
    if env_key in os.environ:
        return os.environ[env_key]
    if key in _overrides:
        return _overrides[key]
    return DEFAULTS[key]
