"""Make (or refresh) the working clone the Volumes sorting and writing read from (James, 2026-10-08:
"dont mess with the original notes ... clone and make it clear as such in the title").

Copies every source file in the Volumes plan into
    C:\\Users\\Elation\\CLONE_FOR_SORTING_2026-10-08__COPIES_NOT_ORIGINALS\\
keeping each file's path below C:\\Users\\Elation (aa1\\..., Research_Imports\\..., DXM\\... and so on), so every copy
says where it came from. Originals are only read, never written. MANIFEST.tsv: original path, clone path, bytes,
sha256; every copy is re-hashed after copying and must match. Re-running copies only new or changed files.
Exit code 1 if any copy fails or does not match."""
import hashlib
import json
import os
import shutil
import sys
import time

HOME = r"C:\Users\Elation"
CLONE = os.path.join(HOME, "CLONE_FOR_SORTING_2026-10-08__COPIES_NOT_ORIGINALS")
SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(SUITE, "data", "books_plan.json")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def clone_path(original):
    return os.path.join(CLONE, os.path.relpath(original, HOME))


def main():
    with open(PLAN, encoding="utf-8") as fh:
        plan = json.load(fh)
    os.makedirs(CLONE, exist_ok=True)
    old = {}
    man = os.path.join(CLONE, "MANIFEST.tsv")
    if os.path.exists(man):
        with open(man, encoding="utf-8") as fh:
            for ln in fh:
                a = ln.rstrip("\n").split("\t")
                if len(a) == 4:
                    old[a[0]] = a
    rows, copied, same, failed, missing = [], 0, 0, [], 0
    for s in plan["sources"].values():
        src = s["path"]
        if not os.path.isfile(src):
            missing += 1
            continue
        dst = clone_path(src)
        h = sha(src)
        prev = old.get(src)
        if prev and prev[3] == h and os.path.isfile(dst):
            rows.append(prev)
            same += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        if sha(dst) != h:
            failed.append(src)
            continue
        rows.append([src, dst, str(os.path.getsize(src)), h])
        copied += 1
    with open(man + ".tmp", "w", encoding="utf-8") as w:
        for r in rows:
            w.write("\t".join(r) + "\n")
    os.replace(man + ".tmp", man)
    print(f"{time.strftime('%Y-%m-%d %H:%M')}  copied {copied}, unchanged {same}, failed {len(failed)}, "
          f"original missing {missing}, total in clone {len(rows)}")
    for f in failed[:10]:
        print("  FAILED", f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
