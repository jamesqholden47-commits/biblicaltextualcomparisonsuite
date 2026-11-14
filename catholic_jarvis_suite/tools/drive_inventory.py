"""
Inventory of every document, book, note and code file in C:\\Users\\Elation (Claude GUI, Opus 5.5, 2026-10-14).

    python tools\\drive_inventory.py            # walk + fingerprint (incremental: unchanged files reuse their hash)

READ-ONLY on everything it walks. It opens a file only to fingerprint it (sha1 of the whole file, or for files over
64 MB of size + first and last 4 MB) and, for .md/.txt, to read the first heading as a title. It moves nothing.

Left out on purpose:
  * program, game, toolchain and settings folders (AppData, .cargo, DayZ, ffmpeg ...): their .txt/.py are not James's;
  * USB_Backup (personal) and the one note in the Desktop review folder that looked like a password: never opened,
    never listed by name;
  * .json and other config/data formats except .csv / .tsv / .xlsx.

Writes data\\drive_inventory.json  (one row per file: path, top folder, ext, bytes, mtime, fingerprint, title).
"""
import datetime
import hashlib
import json
import os
import re
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

HOME = r"C:\Users\Elation"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "drive_inventory.json")

DOC = {".md", ".txt", ".docx", ".doc", ".rtf", ".odt", ".html", ".htm", ".mhtml"}
BOOK = {".pdf", ".epub", ".mobi", ".azw3", ".azw", ".djvu", ".cbz"}
CODE = {".py", ".pyw", ".js", ".ts", ".ps1", ".bat", ".cmd", ".sh", ".ipynb", ".css", ".vbs", ".ahk"}
DATA = {".csv", ".tsv", ".xlsx", ".xls"}
EXTS = DOC | BOOK | CODE | DATA

# whole top-level folders that hold no work of James's (programs, games, settings, caches) or are private
SKIP_TOP = {
    "appdata", "application data", "local settings", "cookies", "nethood", "printhood", "recent", "sendto",
    "start menu", "templates", "my documents", "favorites", "contacts", "searches", "saved games", "links",
    "usb_backup",                                                     # personal: never listed
    "database",                                                       # held account backup codes: never listed
    ".cargo", ".rustup", ".vscode", ".vscode-shared", ".vs", ".cache", ".local", ".config", ".chocolatey",
    ".codex", ".copilot", ".grok", ".idlerc", ".sbx-denybin", ".thumbnails", ".u2net", ".antigravity",
    ".claude", ".claude-server-commander", ".gemini", ".ocr_index", "__pycache__",
    "dayz", "davinci_resolve_20.0_windows", "w64devkit", "yt-dlp", "ytdlp-interface", "icaros_v3.3.3",
    "vbcable_driver_pack43", "ub500_v3_win10_win11", "ps2_bios", "discordchatexporter.cli.win-x64",
    "mpv", "mpv-x86_64-v3-20250226-git-5ae0e0f", "mpv-dev-x86_64-v3-20250624-git-18defc8 (1)",
    "ffmpeg-x86_64-v3-git-f67ca10f2", "fallout 4 script extender (f4se)-42147-0-7-2-1715628153",
    "iloveyou.exe", "configs_and_appdata",
}
SKIP_ANY = {"node_modules", ".git", "__pycache__", ".venv", "venv", "site-packages", ".pytest_cache", ".obsidian",
            ".trash", "dist-packages", ".mypy_cache", ".next", "bower_components", "audio_cache", ".system_generated"}
# program data inside a folder that otherwise holds James's files (Zotero's translators are its own code, not his)
SKIP_PATHS = {os.path.normcase(os.path.join(HOME, p)) for p in ("Zotero\\translators", "Zotero\\styles", "Zotero\\locate",
                                                                 "Zotero\\pdfjs", "Calibre Library\\.calnotes")}
PRIVATE_FILES = {os.path.normcase(os.path.join(HOME, "Desktop", "VAULT_REVIEW_2026-10-08", "Untitled 193.md"))}

# never listed, never opened: anything that looks like credentials (James's own rule: no passwords, keys or codes)
PRIVATE_NAME = re.compile(r"backup[-_ ]?codes?|password|passwd|recovery[-_ ]?key|recoverykey|2fa|seed[-_ ]?phrase|"
                          r"wallet|private[-_ ]?key|secret|credential|\.kdbx$|\.key$", re.I)

BIG = 64 * 1024 * 1024
CHUNK = 4 * 1024 * 1024


def fingerprint(p, size):
    h = hashlib.sha1()
    with open(p, "rb") as fh:
        if size <= BIG:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
            return "sha1:" + h.hexdigest()
        h.update(str(size).encode())
        h.update(fh.read(CHUNK))
        fh.seek(-CHUNK, os.SEEK_END)
        h.update(fh.read(CHUNK))
        return "head-tail:" + h.hexdigest()


def title_of(p, ext):
    if ext not in (".md", ".txt"):
        return ""
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            head = fh.read(3000)
    except OSError:
        return ""
    head = re.sub(r"(?s)^---\n.*?\n---\n", "", head)                     # front matter
    for line in head.splitlines():
        t = line.strip().lstrip("#").strip().strip("*").strip()
        if len(t) >= 3:
            return t[:160]
    return ""


# strong signs only: a .git folder or a manifest.json also sit in James's own vault and project (2026-10-14)
PROGRAM_MARKERS = {"package.json", "manifest.json", "install.rdf", "prefs.js", "cargo.toml", "go.mod", "pom.xml", "cmakelists.txt"}
# his own work is never a "program", whatever it contains
OWN_ROOTS = tuple(os.path.normcase(os.path.join(HOME, p)) for p in (
    "aa1", "DXM", "Mexico_Protestantism_Study", "Scholar_Decade_Plan", "CS2_Dust2_Codex", "Desktop\\Scholar_Decade_Plan",
    "CLONE_FOR_SORTING_2026-10-08__COPIES_NOT_ORIGINALS", "Downloads\\OBSIDIAN_VAULTS_BACKUP_CONTINGENCY", "Easter",
    "Q_Corpus_Analysis", "CatenaStudio", "CanonCouncil", "pope-leo-hub", "warriors-admin-hub", "warriors-housekeeping-app",
    "warriors-public-site", "warriors-test-agency-site"))


def walk():
    for top in os.scandir(HOME):
        name = top.name
        if name.lower() in SKIP_TOP or name.lower().startswith(("ntuser", "$")):
            continue
        if top.is_file(follow_symlinks=False):
            yield top.path, "(home folder)", ""
            continue
        if not top.is_dir(follow_symlinks=False):
            continue
        stack = [(top.path, "")]                       # (folder, the program folder it sits inside, if any)
        while stack:
            d, prog = stack.pop()
            try:
                it = list(os.scandir(d))
            except OSError:
                continue
            # a folder below the top level that holds an .exe/.dll or a package/build/manifest file is a program,
            # add-on or code repository: its .txt and .js files are not James's notes or code
            if not prog and d != top.path and not os.path.normcase(d).startswith(OWN_ROOTS):
                names = {e.name.lower() for e in it}
                if names & PROGRAM_MARKERS or any(n.endswith((".exe", ".dll")) for n in names):
                    prog = d
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False):
                        if e.name.lower() not in SKIP_ANY and os.path.normcase(e.path) not in SKIP_PATHS:
                            stack.append((e.path, prog))
                    elif e.is_file(follow_symlinks=False):
                        yield e.path, name, prog
                except OSError:
                    continue


def main():
    t0 = time.time()
    old = {}
    try:
        with open(OUT, encoding="utf-8") as fh:
            old = {r["path"]: r for r in json.load(fh)["rows"]}
    except (OSError, ValueError, KeyError):
        pass
    rows, hashed, reused, failed = [], 0, 0, 0
    for p, top, prog in walk():
        ext = os.path.splitext(p)[1].lower()
        if ext not in EXTS or os.path.normcase(p) in PRIVATE_FILES or PRIVATE_NAME.search(os.path.basename(p)):
            continue
        try:
            st = os.stat(p)
        except OSError:
            failed += 1
            continue
        prev = old.get(p)
        if prev and prev["bytes"] == st.st_size and prev["mtime"] == int(st.st_mtime):
            prev["program"] = prog
            rows.append(prev)
            reused += 1
            continue
        try:
            fp = fingerprint(p, st.st_size)
        except OSError:
            fp, failed = "", failed + 1
        hashed += 1
        rows.append({"path": p, "top": top, "ext": ext, "bytes": st.st_size, "mtime": int(st.st_mtime),
                     "fp": fp, "title": title_of(p, ext), "program": prog})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT + ".tmp", "w", encoding="utf-8") as w:
        json.dump({"made": datetime.datetime.now().isoformat(timespec="seconds"), "home": HOME, "rows": rows}, w,
                  ensure_ascii=False)
    os.replace(OUT + ".tmp", OUT)
    print(f"{len(rows)} files ({hashed} fingerprinted, {reused} unchanged, {failed} unreadable) in {time.time() - t0:.0f} s")
    print("wrote", OUT)
    print("DRIVE-INVENTORY-END")


if __name__ == "__main__":
    main()
