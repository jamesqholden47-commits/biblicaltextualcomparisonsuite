"""
A PROPOSED physical tidy-up of the scattered files, for James to approve (Claude GUI, Opus 5.5, 2026-10-14).

    python tools\\organize_plan.py              # write the proposal only (moves nothing)
    python tools\\organize_plan.py --apply ID    # carry out proposal ID (the ID printed by the plan step); James's call
    python tools\\organize_plan.py --undo FILE   # put every file in an applied manifest back where it was

What it proposes to move: only what belongs to nothing yet, from the Organizer's buckets
   Loose notes      -> C:\\Users\\Elation\\LIBRARY\\Notes\\<where it was found>\\...
   Saved web pages  -> C:\\Users\\Elation\\LIBRARY\\Web pages\\        (the page and its _files folder together)
   Code elsewhere   -> C:\\Users\\Elation\\LIBRARY\\Code\\<where it was found>\\...
   Books scattered outside PDFS, Calibre Library and Zotero -> C:\\Users\\Elation\\LIBRARY\\Books\\<subject>\\
What it never touches: the vault and archives, the dissertation project, the other projects, PDFS, Calibre Library,
Zotero, anything USB_Backup, and any file whose name is written inside a project document or script (moving it
would break that reference; those are listed as "staying, because <document> points to it").
A duplicate whose identical copy already lives in a kept place is listed as "already kept at <path>", not moved.

--apply moves with os.replace (same drive: a rename, nothing is copied or deleted), never overwrites, and writes a
manifest (old path -> new path) first so --undo can reverse every move. Nothing runs unless James says so.
"""
import datetime
import hashlib
import json
import os
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from modules import organizer_core as core  # noqa: E402

HOME = core.HOME
DEST = os.path.join(HOME, "LIBRARY")
PLAN = os.path.join(BASE, "data", "organize_plan.json")
PLAN_MD = os.path.join(BASE, "data", "_ORGANIZE_PLAN_PROPOSAL.md")
MANIFESTS = os.path.join(BASE, "data", "organize_manifests")
BOOK_HOMES = ("pdfs\\", "calibre library\\", "zotero\\")
REF_ROOTS = [os.path.join(HOME, "DXM"), os.path.join(HOME, "Mexico_Protestantism_Study"),
             os.path.join(HOME, "Scholar_Decade_Plan"), os.path.join(HOME, "aa1")]
FILENAME = re.compile(r"[^\\/\n\r\"'`<>|*?:]{2,200}\.(?:pdf|epub|mobi|md|txt|html?|py|docx|csv)", re.I)


NOT_A_REFERENCE = re.compile(r"(?i)transcript|syslog|conversation|_log|log_|handoff|catalog|proposal|hanging|"
                             r"unfinished|checkpoint|session|_runlog|inventory|genealogy|manifest")


def referenced_names():
    """Every file name written inside a project document or script -> one document that mentions it.
    A log, transcript, handoff or one of the organiser's own lists is not a reference: it mentions a file in passing,
    nothing breaks if the file moves. Generated data (.json) and the suite's data folder are skipped for the same reason."""
    refs = {}
    for root in REF_ROOTS:
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in core_skip() and d not in ("_SESSION_TRANSCRIPTS", "data", "AG_HISTORY_BACKUP")
                     and not NOT_A_REFERENCE.search(d)]
            for f in fn:
                if not f.lower().endswith((".md", ".py", ".txt", ".js", ".ps1", ".bat", ".html")) or NOT_A_REFERENCE.search(f):
                    continue
                p = os.path.join(dp, f)
                try:
                    if os.path.getsize(p) > 8_000_000:
                        continue
                    with open(p, encoding="utf-8", errors="ignore") as fh:
                        text = fh.read()
                except OSError:
                    continue
                for m in FILENAME.findall(text):
                    name = os.path.basename(m.strip()).lower()
                    if len(name) > 4:
                        refs.setdefault(name, p)
    return refs


PROGRAM_MARKERS = {"package.json", "pyproject.toml", "setup.py", "cargo.toml", "manifest.json", "install.rdf", ".git",
                   "prefs.js", "requirements.txt", "go.mod", "pom.xml", "makefile", "cmakelists.txt"}
_program_cache = {}


def inside_program(path):
    """True if any folder between the file and its top-level home folder looks like a program, add-on or code
    repository (has an .exe/.dll, or a package/build/manifest file). Moving one file out of such a folder can
    break the program, so the file stays."""
    rel = core._rel(path)
    parts = rel.split("\\")[:-1]
    # the top folder itself (Downloads, Desktop, Documents) is not a program just because an installer lies in it
    for i in range(len(parts), 1, -1):
        d = os.path.join(HOME, *parts[:i])
        if d not in _program_cache:
            try:
                names = {n.lower() for n in os.listdir(d)}
            except OSError:
                names = set()
            _program_cache[d] = bool(names & PROGRAM_MARKERS) or any(n.endswith((".exe", ".dll")) for n in names)
        if _program_cache[d]:
            return d
    return ""


def core_skip():
    return {"node_modules", ".git", "__pycache__", ".obsidian", ".trash", "audio_cache", "RABBINIC_CORPUS_SEFARIA"}


def plan():
    d = core.load()
    if not d:
        print("No inventory yet: run tools\\drive_inventory.py first.")
        return 1
    rows = d["rows"]
    kept_fp = {}
    for r in rows:
        if r["bucket"] not in ("Loose notes", "Saved web pages", "Code elsewhere") and r.get("fp"):
            kept_fp.setdefault(r["fp"], r["path"])
    refs = referenced_names()
    moves, stays, dupes = [], [], []
    for r in rows:
        low = r["rel"].lower()
        target = None
        if r["bucket"] == "Loose notes":
            target = os.path.join(DEST, "Notes", r["rel"])
        elif r["bucket"] == "Code elsewhere":
            target = os.path.join(DEST, "Code", r["rel"])
        elif r["bucket"] == "Saved web pages":
            if "\\" in r["rel"] and "_files\\" in low:
                continue                          # moves with its page (below)
            target = os.path.join(DEST, "Web pages", os.path.basename(r["rel"]))
        elif r["bucket"] == "Books" and not low.startswith(BOOK_HOMES):
            target = os.path.join(DEST, "Books", r["shelf"], os.path.basename(r["rel"]))
        if not target:
            continue
        name = os.path.basename(r["path"]).lower()
        prog = inside_program(r["path"])
        if prog:
            stays.append({"path": r["path"], "why": "inside a program or code folder: " + prog})
            continue
        if name in refs:
            stays.append({"path": r["path"], "why": refs[name]})
            continue
        if r.get("fp") in kept_fp and kept_fp[r["fp"]] != r["path"]:
            dupes.append({"path": r["path"], "kept": kept_fp[r["fp"]]})
            continue
        m = {"from": r["path"], "to": target, "bucket": r["bucket"], "bytes": r["bytes"]}
        if r["bucket"] == "Saved web pages":
            companion = os.path.splitext(r["path"])[0] + "_files"
            if os.path.isdir(companion):
                m["with_folder"] = companion
        moves.append(m)
    pid = hashlib.sha1(json.dumps(moves, sort_keys=True).encode()).hexdigest()[:10]
    out = {"id": pid, "made": datetime.datetime.now().isoformat(timespec="seconds"), "dest": DEST,
           "moves": moves, "staying_referenced": stays, "duplicates_already_kept": dupes}
    with open(PLAN + ".tmp", "w", encoding="utf-8") as w:
        json.dump(out, w, ensure_ascii=False, indent=1)
    os.replace(PLAN + ".tmp", PLAN)
    write_md(out)
    by = {}
    for m in moves:
        k = m["to"][len(DEST) + 1:].split("\\")[0]
        by[k] = by.get(k, 0) + 1
    print(f"proposal {pid}: {len(moves)} files would move into {DEST} {by}; {len(stays)} stay (a document points to them); "
          f"{len(dupes)} are duplicates of a kept file")
    print("wrote", PLAN)
    print("wrote", PLAN_MD)
    return 0


def write_md(p):
    groups = {}
    for m in p["moves"]:
        rel = m["to"][len(DEST) + 1:]
        parts = rel.split("\\")
        key = "\\".join(parts[:2]) if len(parts) > 2 else parts[0]
        groups.setdefault(key, []).append(m)
    L = ["# Proposed tidy-up of the scattered files — NOT DONE, waiting for James", "",
         f"*Proposal `{p['id']}`, made {p['made'].replace('T', ' ')} by `tools\\organize_plan.py`. Nothing has moved.*", "",
         f"**{len(p['moves'])} files would move** into `{p['dest']}`, into Notes, Web pages, Code and Books folders that keep "
         f"the name of where each file was found. **{len(p['staying_referenced'])} stay put** because a project document "
         f"or script names them, or they sit inside a program or code folder that moving would break. "
         f"**{len(p['duplicates_already_kept'])} are exact duplicates** of a file that is already "
         f"kept somewhere organised, so they are left where they are for you to decide.", "",
         "Never touched: the vault and archives, the dissertation project, the other projects, PDFS, Calibre Library, "
         "Zotero, USB_Backup, and anything that looks like passwords, keys or backup codes (those are not even listed).", "",
         "If you approve, it runs as a rename on the same drive (nothing copied, nothing deleted), never overwrites, and "
         "writes a list of every move first so one command puts everything back.", "",
         "## Where things would go", ""]
    for k in sorted(groups, key=lambda k: -len(groups[k])):
        g = groups[k]
        L.append(f"- **LIBRARY\\{k}**: {len(g)} files, e.g. " + "; ".join(f"`{os.path.basename(m['from'])}`" for m in g[:3]))
    L += ["", "## Staying put: a document points to them, or they sit inside a program folder (first 60)", ""]
    for s in p["staying_referenced"][:60]:
        why = s["why"] if s["why"].startswith("inside") else f"named in `{s['why']}`"
        L.append(f"- `{s['path']}` ← {why}")
    with open(PLAN_MD + ".tmp", "w", encoding="utf-8") as w:
        w.write("\n".join(L) + "\n")
    os.replace(PLAN_MD + ".tmp", PLAN_MD)


def apply(pid):
    with open(PLAN, encoding="utf-8") as fh:
        p = json.load(fh)
    if p["id"] != pid:
        print(f"proposal on disk is {p['id']}, not {pid}: re-read the proposal before applying")
        return 1
    os.makedirs(MANIFESTS, exist_ok=True)
    man = os.path.join(MANIFESTS, f"applied_{pid}_{datetime.datetime.now():%Y%m%d-%H%M%S}.tsv")
    done = skipped = 0
    with open(man, "w", encoding="utf-8") as log:
        for m in p["moves"]:
            pairs = [(m["from"], m["to"])]
            if m.get("with_folder"):
                pairs.append((m["with_folder"], os.path.join(os.path.dirname(m["to"]), os.path.basename(m["with_folder"]))))
            for src, dst in pairs:
                if not os.path.exists(src) or os.path.exists(dst):
                    skipped += 1
                    log.write(f"SKIP\t{src}\t{dst}\n")
                    continue
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                log.write(f"MOVE\t{src}\t{dst}\n")
                log.flush()
                os.replace(src, dst)
                done += 1
    print(f"moved {done}, skipped {skipped}; manifest {man}")
    return 0


def undo(man):
    back = 0
    with open(man, encoding="utf-8") as fh:
        lines = [ln.rstrip("\n").split("\t") for ln in fh if ln.startswith("MOVE\t")]
    for _, src, dst in reversed(lines):
        if os.path.exists(dst) and not os.path.exists(src):
            os.makedirs(os.path.dirname(src), exist_ok=True)
            os.replace(dst, src)
            back += 1
    print(f"put back {back} of {len(lines)}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--apply"] and len(a) == 2:
        sys.exit(apply(a[1]))
    if a[:1] == ["--undo"] and len(a) == 2:
        sys.exit(undo(a[1]))
    sys.exit(plan())
