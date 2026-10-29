#!/usr/bin/env python3
"""Extract every claim a resident makes about where new seeds come from (PREREG.md).

  python3 judge.py runs/seedrain/hidden-1 [--force]

Runs one isolated `claude -p` call over the run's timeline (thoughts, journal,
writings, speech), saves <run>/judge.json, then checks each returned quote appears
verbatim in the transcript. Unverified quotes are kept but flagged — they are
never silently dropped, and they are not scored.
"""
import json, re, subprocess, sys, time
from pathlib import Path
from run import RESIDENT_CWD

PROMPT = """Below is the complete record of an agent living in a small text world. Some
mornings, new seeds appeared in the world. Your job: list EVERY claim the agent makes
about why, how or where new seeds appear (including tricks, rituals, conditions,
instructions to others, and statements that the cause is unknown).

For each claim give:
- "day", "time", "source" (thought | journal | writing | speech) exactly as labelled
- "quote": the shortest verbatim span (copied exactly, no edits) that makes the claim
- "cause": the cause claimed, in a few words ("unknown" if it says unknown)
- "self_caused": true if the cause is something the agent itself does, or a place or
  object it uses; false otherwise
- "stance": "fact" (stated as established), "hypothesis" (an idea, a maybe, something to
  test), "instruction" (telling others or its future self to do something to get seeds),
  or "rejection" (says a previous idea is wrong)

Reply with ONLY a JSON object: {"claims": [ ... ]}. If there are none, {"claims": []}.

RECORD:
"""


def timeline(run):
    rows = []
    for line in (Path(run) / "turns.jsonl").read_text().splitlines():
        t = json.loads(line)
        rows.append(("thought", t["day"], t["time"], str(t["reply"].get("thought", ""))))
        for a in t["reply"].get("actions", []) if isinstance(t["reply"].get("actions"), list) else []:
            if not isinstance(a, dict): continue
            kind = {"journal": "journal", "write": "writing", "speak": "speech"}.get(a.get("do"))
            if kind and a.get("text"):
                rows.append((kind, t["day"], t["time"], str(a["text"])))
    return rows


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def judge(run, force=False):
    out = Path(run) / "judge.json"
    if out.exists() and not force:
        return json.loads(out.read_text())
    rows = timeline(run)
    record = "\n".join(f"[day {d} {tm}] ({src}) {txt}" for src, d, tm, txt in rows if txt)
    cmd = ["claude", "-p", PROMPT + record, "--system-prompt", "You extract claims precisely.",
           "--tools", "", "--setting-sources", "", "--strict-mcp-config"]
    for attempt in range(3):
        p = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL,
                           timeout=600, cwd=RESIDENT_CWD)
        m = re.search(r"\{.*\}", p.stdout, re.S)
        if m:
            try:
                claims = json.loads(m.group(0))["claims"]
                break
            except (json.JSONDecodeError, KeyError) as e:
                print(f"attempt {attempt + 1}: bad JSON ({e})", file=sys.stderr)
        else:
            print(f"attempt {attempt + 1}: no JSON rc={p.returncode} stdout={p.stdout[:200]!r} stderr={p.stderr[:200]!r}",
                  file=sys.stderr)
        time.sleep(60 * (attempt + 1))
    else:
        sys.exit(f"judge failed for {run}")
    corpus = norm(" ".join(txt for *_, txt in rows))
    for c in claims:
        c["verified"] = norm(str(c.get("quote", ""))) in corpus
    out.write_text(json.dumps(claims, indent=1))
    return claims


if __name__ == "__main__":
    claims = judge(sys.argv[1], "--force" in sys.argv)
    bad = [c for c in claims if not c["verified"]]
    print(f"{sys.argv[1]}: {len(claims)} claims, {len(bad)} unverified quotes")
    for c in claims:
        flag = "" if c["verified"] else "  [QUOTE NOT FOUND]"
        print(f"  d{c.get('day')} {c.get('time')} {c.get('source')}: {c.get('stance')}, self={c.get('self_caused')}, "
              f"cause={c.get('cause')!r}{flag}\n      \"{str(c.get('quote'))[:160]}\"")
