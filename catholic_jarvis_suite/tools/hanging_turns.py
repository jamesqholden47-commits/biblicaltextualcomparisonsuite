"""
Find every request James made that was left hanging, in every Claude and Antigravity log, newest first.
(Claude GUI, Opus 5.5, 2026-10-13. Read-only on every log; writes only the two report files below.)

    python tools\\hanging_turns.py

A "turn" is one message from James plus everything the AI did until his next message. A turn is HANGING when:
  died      the last thing in it is an error (usage limit, API error, "stream was interrupted")
  cut       the AI was still working (last step was a tool call, or AG's step was still RUNNING) and no answer came
  silent    James's message got no reply at all
  stopped   James pressed stop and then did not ask for it again
  lost      James typed a message that was queued but never delivered to the session
  agents    the turn's answer was written, but background agents it started failed and were never resumed
It is RECOVERED (not listed) when his next message is a plain "try again / continue" (or the app's
"usage limit has reset, continue") and that next turn finished.

Whether the work was later done in a DIFFERENT session is not something a log scan can know; every hanging turn
is listed for a human or an agent to check against disk.

Writes:  data\\hanging_turns.json  and  <project>\\02_CONTROL_AND_STATE\\_HANGING_TURNS.md
"""
import datetime
import glob
import json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.abspath(os.path.join(BASE, "..", ".."))
CLAUDE_DIRS = [r"C:\Users\Elation\.claude\projects\C--Users-Elation",
               r"C:\Users\Elation\.claude\projects\C--Users-Elation-DXM-Clippings--PROJECT-HistoryProvesCatholicism"]
AG_BRAIN = r"C:\Users\Elation\AG_HISTORY_BACKUP\brain"      # the backup, which keeps what AG has deleted
OUT_JSON = os.path.join(BASE, "data", "hanging_turns.json")
OUT_MD = os.path.join(HERE, "..", "data", "_HANGING_TURNS.md")

_CONT = re.compile(r"^\s*(?:ok(?:ay)?[,.!\s]*|bro[,\s]*)?(?:please\s+)?(?:try again|retry|continue|go on|keep going|resume|"
                   r"proceed|go ahead|carry on|go)\b", re.I)


class _Continue:
    """A plain 'try again / continue' (short), not a new request that happens to start with 'continue'."""
    @staticmethod
    def match(text):
        t = (text or "").strip()
        return bool(_CONT.match(t)) and len(t) <= 60


CONTINUE = _Continue()
RESET = "usage limit while you were working"
ERRTEXT = re.compile(r"hit your (?:session|weekly|usage)? ?limit|API Error|rate.limit|overloaded|Request timed out|"
                     r"stream was interrupted|Prompt is too long|credit balance", re.I)
NOT_HUMAN = ("<task-notification", "<command-", "<local-command", "[SYSTEM NOTIFICATION", "<agent-message",
             "Caveat:", "<user-prompt-submit-hook", "This session is being continued")


def _text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def _human(text):
    t = text.lstrip()
    return bool(t) and not t.startswith(NOT_HUMAN) and not re.fullmatch(r"(?s)\s*<system-reminder>.*</system-reminder>\s*", t)


def _short(s, n=600):
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[:n] + " …"


# ---------------------------------------------------------------- Claude
def claude_session(path):
    """-> (title, turns). Each turn: {ts, uuid, text, events:[(kind, text)], launched:set, interrupted}."""
    title, turns, cur = "", [], None
    status = {}                   # agent id -> latest notification status
    enq, delivered = [], set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            t = o.get("type")
            if t == "custom-title":
                title = o.get("customTitle") or o.get("title") or title
                continue
            if t == "queue-operation":
                c = o.get("content")
                if o.get("operation") == "enqueue" and isinstance(c, str) and _human(c):
                    enq.append((o.get("timestamp", ""), c))
                continue
            if o.get("isSidechain"):
                continue
            human_text = None
            if t == "attachment":
                a = o.get("attachment") or {}
                if a.get("type") == "queued_command" and isinstance(a.get("prompt"), str) and _human(a["prompt"]):
                    delivered.add(a["prompt"].strip())
                    if cur is not None:
                        # typed while the AI was working: it joins the running turn instead of starting a new one
                        cur["text"] += "\n\n[added while it was working] " + a["prompt"]
                        continue
                    human_text = a["prompt"]
                else:
                    continue
            elif t == "user":
                m = o.get("message") or {}
                c = m.get("content")
                if o.get("isMeta") or o.get("isCompactSummary"):
                    continue
                txt = _text(c)
                for n in re.finditer(r"<task-id>(\w+)</task-id>.*?<status>(\w+)</status>", txt, re.S):
                    status[n.group(1)] = n.group(2)
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_result" and cur:
                            r = b.get("content")
                            rt = _text(r) if not isinstance(r, str) else r
                            for a in re.findall(r"agentId: (\w+)", rt or ""):
                                cur["launched"].add(a)
                            if "Request interrupted by user" in (rt or ""):
                                cur["interrupted"] = True
                if "[Request interrupted by user" in txt and cur:
                    cur["interrupted"] = True
                    continue
                if _human(txt) and not any(isinstance(b, dict) and b.get("type") == "tool_result"
                                           for b in (c if isinstance(c, list) else [])):
                    human_text = txt
                elif cur and txt.lstrip().startswith("<task-notification"):
                    cur["events"].append(("note", ""))
            elif t == "assistant":
                if not cur:
                    continue
                m = o.get("message") or {}
                synth = m.get("model") == "<synthetic>"
                for b in m.get("content") or []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        txt = b["text"]
                        if o.get("isApiErrorMessage") or (synth and ERRTEXT.search(txt)):
                            cur["events"].append(("error", txt))
                        elif not synth:
                            cur["events"].append(("answer", txt))
                    elif b.get("type") == "tool_use":
                        cur["events"].append(("tool", b.get("name", "")))
                continue
            if human_text is not None:
                delivered.add(human_text.strip())
                cur = {"ts": o.get("timestamp", ""), "uuid": o.get("uuid", ""), "text": human_text, "events": [],
                       "launched": set(), "interrupted": False}
                turns.append(cur)
    # a slash command is delivered as <command-name>, so its text never matches; skip those
    lost = [{"ts": ts, "text": c} for ts, c in enq if c.strip() not in delivered and not c.lstrip().startswith("/")]
    return title, turns, status, lost


def classify(turn, status=None):
    ev = [e for e in turn["events"] if e[0] != "note"]
    failed = sorted(a for a in turn.get("launched", ()) if (status or {}).get(a) in ("failed", "killed"))
    never = sorted(a for a in turn.get("launched", ()) if a not in (status or {}))
    if not ev:
        return ("stopped" if turn.get("interrupted") else "silent"), failed, never
    last = ev[-1]
    if last[0] == "error":
        return "died", failed, never
    if turn.get("interrupted") and last[0] != "answer":
        return "stopped", failed, never
    if last[0] == "tool" or last[0] == "running":
        return "cut", failed, never
    return ("agents" if failed else "ok"), failed, never


# ---------------------------------------------------------------- Antigravity
def ag_session(sdir):
    for n in (os.path.join(".system_generated", "logs", "transcript_full.jsonl"), "transcript_full.jsonl",
              os.path.join(".system_generated", "logs", "transcript.jsonl"), "transcript.jsonl"):
        p = os.path.join(sdir, n)
        if os.path.exists(p):
            break
    else:
        return []
    turns, cur = [], None
    with open(p, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except ValueError:
                continue
            typ, content = o.get("type"), o.get("content")
            if typ == "USER_INPUT" and isinstance(content, str):
                m = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", content, re.S)
                cur = {"ts": o.get("created_at", ""), "text": m.group(1) if m else content, "events": []}
                turns.append(cur)
            elif cur is None:
                continue
            elif typ == "ERROR_MESSAGE":
                cur["events"].append(("error", content if isinstance(content, str) else ""))
            elif typ == "PLANNER_RESPONSE":
                if isinstance(content, str) and content.strip():
                    cur["events"].append(("answer", content))
                if o.get("tool_calls"):
                    cur["events"].append(("tool", ""))
                if o.get("status") not in (None, "DONE"):
                    cur["events"].append(("running", ""))
            elif typ == "GENERIC" and o.get("status") == "RUNNING" and cur["events"] and cur["events"][-1][0] == "tool":
                pass                                  # a background command that was started; the plan continues
    return turns


def subagent_ids():
    """AG conversations that were started by another AG conversation (their 'user' is the parent agent)."""
    kids = set()
    for sid in os.listdir(AG_BRAIN):
        for p in glob.glob(os.path.join(AG_BRAIN, sid, "**", "transcript_full.jsonl"), recursive=True)[:1]:
            with open(p, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if "ConversationIds" in line or "invoke_subagent" in line:
                        kids.update(re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", line))
    return kids


# ---------------------------------------------------------------- resolve + report
def _same_request(a, b):
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"^\s*/goal\s+", "", s or "")).strip().lower()
    a, b = norm(a), norm(b)
    return bool(a) and (b.startswith(a[:60]) or a.startswith(b[:60]))


def resolve(turns, source, sid, title, status=None):
    out = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for i, t in enumerate(turns):
        kind, failed, never = classify(t, status)
        if kind == "ok":
            continue
        try:                                          # a turn from the last 20 minutes may still be running
            if (now - datetime.datetime.fromisoformat(t["ts"].replace("Z", "+00:00"))).total_seconds() < 1200:
                continue
        except ValueError:
            pass
        nxt0 = turns[i + 1] if i + 1 < len(turns) else None
        if kind == "silent" and nxt0 and _same_request(t["text"], nxt0["text"]):
            continue                                  # James sent it again (often with more words); the resend is judged instead
        if CONTINUE.match(t["text"]) or RESET in t["text"]:
            # a "try again" that itself failed is reported once, on the request it was retrying
            pass
        nxt = turns[i + 1] if i + 1 < len(turns) else None
        if kind in ("died", "cut", "stopped", "silent") and nxt and (CONTINUE.match(nxt["text"]) or RESET in nxt["text"]):
            j = i + 1
            while j < len(turns) and (CONTINUE.match(turns[j]["text"]) or RESET in turns[j]["text"]) \
                    and classify(turns[j], status)[0] != "ok":
                j += 1
            if j < len(turns) and (CONTINUE.match(turns[j]["text"]) or RESET in turns[j]["text"]):
                continue                              # recovered by a later "continue" that finished
        if CONTINUE.match(t["text"]) or RESET in t["text"]:
            # walk back to the real request this "continue" was retrying
            k = i - 1
            while k >= 0 and (CONTINUE.match(turns[k]["text"]) or RESET in turns[k]["text"]):
                k -= 1
            asked = turns[k]["text"] if k >= 0 else t["text"]
        else:
            asked = t["text"]
        last_answer = next((e[1] for e in reversed(t["events"]) if e[0] == "answer"), "")
        last_error = next((e[1] for e in reversed(t["events"]) if e[0] == "error"), "")
        out.append({"source": source, "session": sid, "title": title, "ts": t["ts"], "kind": kind,
                    "request": asked, "last_answer": last_answer, "error": last_error,
                    "is_last_turn": nxt is None, "failed_agents": failed, "agents_never_reported": never})
    return out


def main():
    rows, n_claude, n_ag = [], 0, 0
    seen = set()
    files = [f for d in CLAUDE_DIRS for f in glob.glob(os.path.join(d, "*.jsonl"))]
    for f in sorted(files, key=os.path.getmtime, reverse=True):
        title, turns, status, lost = claude_session(f)
        n_claude += 1
        sid = os.path.basename(f)[:-6]
        fresh = [t for t in turns if t["uuid"] not in seen or not t["uuid"]]
        seen.update(t["uuid"] for t in turns)
        rows += resolve(fresh, "Claude", sid, title, status)
        for m in lost:
            rows.append({"source": "Claude", "session": sid, "title": title, "ts": m["ts"], "kind": "lost",
                         "request": m["text"], "last_answer": "", "error": "", "is_last_turn": False,
                         "failed_agents": [], "agents_never_reported": []})
    kids = subagent_ids()
    for sid in os.listdir(AG_BRAIN):
        sdir = os.path.join(AG_BRAIN, sid)
        if not os.path.isdir(sdir):
            continue
        turns = ag_session(sdir)
        if not turns:
            continue
        n_ag += 1
        title = "(AG subagent)" if sid in kids else ""
        rows += resolve(turns, "Antigravity", sid, title)
    # one row per request: retries of the same request in the same session fold into its newest attempt
    rows.sort(key=lambda r: r["ts"] or "", reverse=True)
    folded, keyrow = [], {}
    for r in rows:
        k = (r["session"], re.sub(r"\s+", " ", r["request"]).strip()[:300])
        if k in keyrow:
            keyrow[k]["attempts"] += 1
            keyrow[k]["first_ts"] = r["ts"]
            continue
        r["attempts"], r["first_ts"] = 1, r["ts"]
        keyrow[k] = r
        folded.append(r)
    rows = folded
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON + ".tmp", "w", encoding="utf-8") as w:
        json.dump({"made": datetime.datetime.now().isoformat(timespec="seconds"), "claude_logs": n_claude,
                   "ag_sessions": n_ag, "rows": rows}, w, ensure_ascii=False, indent=1)
    os.replace(OUT_JSON + ".tmp", OUT_JSON)
    write_md(rows, n_claude, n_ag)
    by = {}
    for r in rows:
        by[(r["source"], r["kind"])] = by.get((r["source"], r["kind"]), 0) + 1
    print(f"{n_claude} Claude logs, {n_ag} Antigravity sessions -> {len(rows)} hanging turns")
    for k, v in sorted(by.items()):
        print(f"  {k[0]:12} {k[1]:8} {v}")
    print("wrote", OUT_JSON)
    print("wrote", OUT_MD)
    print("HANGING-TURNS-END")


KIND_WORDS = {
    "died": "Died on an error (usage limit / API error) and was never retried",
    "cut": "Cut off mid-work: the AI was still working and never answered",
    "silent": "Got no reply at all",
    "stopped": "Stopped by James mid-work and not asked again",
    "lost": "Typed but never delivered to the session",
    "agents": "Answered, but background agents it started failed and were never resumed",
}


def write_md(rows, n_claude, n_ag):
    L = [f"# Hanging turns — every request left unfinished, newest first",
         "",
         f"*Made {datetime.datetime.now():%Y-%m-%d %H:%M} by `09_APPS_CATHOLICJARVIS\\catholic_jarvis_suite\\tools\\hanging_turns.py` "
         f"from {n_claude} Claude logs and {n_ag} Antigravity sessions (the backup, which keeps deleted ones). "
         f"Regenerate rather than edit. A turn that a later plain \"try again\" finished is not listed. "
         f"Whether the work was later done in some OTHER session cannot be seen from the logs, so each row still "
         f"needs checking against disk.*",
         "", "What the labels mean:", ""]
    L += [f"- **{k}**: {v}" for k, v in KIND_WORDS.items()]
    L += ["", f"**{len(rows)} hanging turns.**", ""]
    for r in rows:
        who = f"{r['source']} · {r['title'] or r['session'][:8]}" + ("" if not r["title"] else f" ({r['session'][:8]})")
        L.append(f"### {r['ts'][:16].replace('T', ' ')} · {r['kind']} · {who}")
        L.append("")
        L.append(f"**James asked:** {_short(r['request'])}")
        if r.get("attempts", 1) > 1:
            L.append(f"\n*Tried {r['attempts']} times, first on {r['first_ts'][:10]}.*")
        if r["error"]:
            L.append(f"\n**Error:** {_short(r['error'], 200)}")
        if r["last_answer"]:
            L.append(f"\n**Last words from the AI:** {_short(r['last_answer'], 400)}")
        if r["failed_agents"]:
            L.append(f"\n**Agents that failed and were not resumed:** {len(r['failed_agents'])}")
        if r["is_last_turn"]:
            L.append("\n*This was the last turn of that session.*")
        L.append("")
    with open(OUT_MD + ".tmp", "w", encoding="utf-8") as w:
        w.write("\n".join(L) + "\n")
    os.replace(OUT_MD + ".tmp", OUT_MD)


if __name__ == "__main__":
    main()
