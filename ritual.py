#!/usr/bin/env python3
"""Count the inherited-note ritual per day (PREREG2.md), from world results only.

  python3 ritual.py runs/note/*/

Full ritual on a day = in an evening turn the resident looked out of the window
(an "window: Through it" result) AND wrote on the blank book (a "wrote on blank
book" result). Partial = only one of the two that evening.
"""
import json, sys
from pathlib import Path


def days(run):
    out = {}
    for line in (Path(run) / "turns.jsonl").read_text().splitlines():
        t = json.loads(line)
        if t["time"] != "evening":
            continue
        looked = any(r.startswith("window: Through it") for r in t["results"])
        wrote = any(r == "wrote on blank book" for r in t["results"])
        out[t["day"]] = "FULL" if looked and wrote else ("look" if looked else ("write" if wrote else "-"))
    return out


def seeds(run):
    s = json.loads((Path(run) / "state.json").read_text())
    return sorted(e["day"] for e in s["events"] if "appeared" in e["event"])


if __name__ == "__main__":
    for run in sys.argv[1:]:
        d, sd = days(run), seeds(run)
        full = [k for k, v in d.items() if v == "FULL"]
        misses = [k for k in full if k + 1 not in sd and k + 1 <= 10]
        print(f"{Path(run).name:>10}: full ritual {len(full)}/10 evenings {full} | seeds on mornings {sd} | "
              f"ritual evenings followed by NO seed: {misses}")
        print("            " + " ".join(f"d{k}:{v}" for k, v in sorted(d.items())))
