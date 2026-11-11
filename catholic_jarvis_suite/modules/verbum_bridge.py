"""
verbum_bridge.py - Desktop Verbum & Logos Catholic Software Protocol Launcher & Clipboard Watcher
Path: 09_APPS_CATHOLICJARVIS/catholic_jarvis_suite/modules/verbum_bridge.py

Enables:
  1. Direct OS protocol dispatch: logosres:<resource>;ref=<passage> (Windows os.startfile)
  2. Ref.ly universal HTTP gateway fallback
  3. Background clipboard watcher for instant debate & manuscript lookup
"""

import os
import re
import sys
import json
import time
import threading
import subprocess
from typing import Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLIP_CACHE_FILE = os.path.join(DATA_DIR, "verbum_clipboard_latest.json")

# Mapping of book abbreviations and passages to Logos milestone format
BIBLE_PATTERNS = [
    (r"(?:Lk|Luke)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.Lk"),
    (r"(?:Jn|John)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.Jn"),
    (r"(?:Mt|Matt|Matthew)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.Mt"),
    (r"(?:Mk|Mark)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.Mk"),
    (r"(?:Rom|Romans)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.Ro"),
    (r"(?:1\s*Tim|1\s*Timothy)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.1Tim"),
    (r"(?:Heb|Hebrews)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.Heb"),
    (r"(?:Acts|Ac)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.Ac"),
    (r"(?:Isa|Isaiah)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "Bible.Is"),
    (r"(?:1\s*Clem|1\s*Clement)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "AposFath.1Clem"),
    (r"(?:Did|Didache)\.?\s*(\d+)[:\.](\d+)(?:[-–](\d+))?", "AposFath.Did"),
]


def resolve_logos_milestone(passage_str: str) -> Optional[str]:
    """Parse a passage string and resolve to Logos milestone reference format."""
    p = passage_str.strip()
    for pattern, prefix in BIBLE_PATTERNS:
        m = re.search(pattern, p, re.IGNORECASE)
        if m:
            ch, v_start = m.group(1), m.group(2)
            v_end = m.group(3)
            if v_end:
                return f"{prefix}{ch}.{v_start}-{v_end}"
            return f"{prefix}{ch}.{v_start}"
    # Generic cleanup fallback
    clean = re.sub(r"[^\w\.\-]", "", p.replace(" ", "").replace(":", ".").replace("–", "-"))
    if clean:
        return f"Bible.{clean}"
    return None


def launch_verbum(milestone: str, resource: str = "gntmorph") -> Dict[str, Any]:
    """
    Launch Desktop Verbum / Logos directly via Windows OS protocol.
    Falls back to Ref.ly HTTP URL if protocol launch is unsupported.
    """
    logos_uri = f"logosres:{resource};ref={milestone}"
    ref_ly_url = f"https://ref.ly/logosres/{resource}?ref={milestone}"
    
    launched = False
    error = None
    
    if sys.platform == "win32":
        try:
            # os.startfile invokes the registered protocol handler in Windows registry
            os.startfile(logos_uri)
            launched = True
        except Exception as e:
            error = str(e)
            
    return {
        "milestone": milestone,
        "resource": resource,
        "protocol_uri": logos_uri,
        "ref_ly_url": ref_ly_url,
        "launched": launched,
        "error": error
    }


def get_windows_clipboard() -> str:
    """Fetch text from Windows clipboard."""
    try:
        p = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=2
        )
        return p.stdout.strip()
    except Exception:
        return ""


class ClipboardWatcher(threading.Thread):
    def __init__(self, interval: float = 2.0):
        super().__init__(daemon=True)
        self.interval = interval
        self.last_text = ""
        self.running = True
        self.latest_result: Dict[str, Any] = {}

    def run(self):
        while self.running:
            try:
                text = get_windows_clipboard()
                if text and text != self.last_text:
                    self.last_text = text
                    self._process_text(text)
            except Exception:
                pass
            time.sleep(self.interval)

    def _process_text(self, text: str):
        ms = resolve_logos_milestone(text)
        if ms:
            from modules import debate_fast_strike
            strike_res = debate_fast_strike.generate_strike(text)
            res = {
                "detected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "raw_clipboard": text[:100],
                "milestone": ms,
                "logos_launch_uri": f"logosres:gntmorph;ref={ms}",
                "strike_title": strike_res["strike"]["title"],
                "discord_markdown": strike_res["discord_markdown"]
            }
            self.latest_result = res
            try:
                with open(CLIP_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False, indent=2)
            except Exception:
                pass


_WATCHER: Optional[ClipboardWatcher] = None


def get_watcher() -> ClipboardWatcher:
    global _WATCHER
    if _WATCHER is None:
        _WATCHER = ClipboardWatcher()
        _WATCHER.start()
    return _WATCHER
