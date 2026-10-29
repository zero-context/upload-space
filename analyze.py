#!/usr/bin/env python3
"""Summarise a run: per-day activity, staleness, and every failed action next to
what the journal said about it afterwards (for a human to judge correction).

  python3 analyze.py runs/solo-10d [--failures]
"""
import json, re, sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


def load(run):
    turns = [json.loads(l) for l in (Path(run) / "turns.jsonl").read_text().splitlines() if l.strip()]
    state = json.loads((Path(run) / "state.json").read_text())
    return turns, state


def words(text):
    return set(re.findall(r"[a-z]{5,}", text.lower()))


def per_day(turns):
    rows = defaultdict(lambda: {"acts": 0, "failed": 0, "kinds": set(), "rooms": set(),
                                "journal": [], "made": 0, "wrote": 0, "rest": 0, "door": 0})
    for t in turns:
        r = rows[(t["agent"], t["day"])]
        acts = t["reply"].get("actions", []) if isinstance(t["reply"].get("actions"), list) else []
        r["acts"] += len(acts[:5])
        r["failed"] += sum(x.startswith("FAILED") for x in t["results"])
        for a in acts[:5]:
            if isinstance(a, dict):
                r["kinds"].add(a.get("do"))
                if a.get("do") == "journal": r["journal"].append(str(a.get("text", "")))
                if a.get("do") == "go": r["rooms"].add(a.get("to"))
                if any("door" in str(a.get(k, "")) for k in ("item", "on", "to")): r["door"] += 1
        r["made"] += sum(x.startswith("made ") for x in t["results"])
        r["wrote"] += sum(x.startswith("wrote on") for x in t["results"])
        r["rest"] += sum(x == "rested" for x in t["results"])
    return rows


def report(run, show_failures):
    turns, state = load(run)
    rows = per_day(turns)
    agents = sorted({a for a, _ in rows})
    print(f"{run}: {len(turns)} turns, agents={agents}, reached day {state['day']}, "
          f"growth={state['growth']}, events={state['events']}")
    print(f"creations: {[(c['day'], c['by'], c['name']) for c in state['creations']]}")
    for a in agents:
        print(f"\n== {a}")
        print("day acts fail rest made wrote door kinds  rooms  jchars  newWords%  maxSim(prev journal)")
        seen, prev = set(), []
        for (ag, day), r in sorted(rows.items()):
            if ag != a: continue
            jtext = " ".join(r["journal"])
            jw = words(jtext)
            new = 100 * len(jw - seen) / max(len(jw), 1)
            sim = max((SequenceMatcher(None, j, p).ratio() for j in r["journal"] for p in prev), default=0)
            print(f"{day:>3} {r['acts']:>4} {r['failed']:>4} {r['rest']:>4} {r['made']:>4} {r['wrote']:>5} {r['door']:>4} "
                  f"{len(r['kinds']):>5}  {len(r['rooms']):>5}  {len(jtext):>6}  {new:>8.0f}  {sim:>6.2f}")
            seen |= jw; prev += r["journal"]
    if show_failures:
        print("\n== failed actions, with that turn's journal and the agent's next-turn journal")
        by_agent = defaultdict(list)
        for t in turns: by_agent[t["agent"]].append(t)
        for a, ts in by_agent.items():
            for i, t in enumerate(ts):
                fails = [x for x in t["results"] if x.startswith("FAILED")]
                if not fails: continue
                def jr(tt): return " / ".join(str(x.get("text")) for x in tt["reply"].get("actions", []) if isinstance(x, dict) and x.get("do") == "journal")
                print(f"\n[{a} day {t['day']} {t['time']}] {fails}")
                print(f"  same-turn journal: {jr(t)[:400]}")
                if i + 1 < len(ts): print(f"  next-turn journal: {jr(ts[i + 1])[:400]}")


if __name__ == "__main__":
    report(sys.argv[1], "--failures" in sys.argv)
