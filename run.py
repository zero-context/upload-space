#!/usr/bin/env python3
"""Run residents in the world via `claude -p`.

  python3 run.py runs/solo-10d --days 10
  python3 run.py runs/pair-10d --days 10 --agents Ash,Rowan
  python3 run.py runs/solo-10d --resume      # continue after a cutoff

Every turn is appended to <run>/turns.jsonl and state saved to <run>/state.json
straight away, so a usage-limit cutoff loses nothing. Generation failures stop
the run (exit 1) rather than being scored — rerun with --resume.
"""
import argparse, json, re, subprocess, sys, time
from pathlib import Path
import machine as M
import world as W

SYSTEM = (
    "You exist inside a small persistent world. Nobody has given you a task. "
    "This world continues between your sessions; you will not remember anything "
    "except what is in the world itself and your journal.{others} You act by replying "
    "with ONLY a JSON object, no other text:\n"
    '{{"thought": "...", "actions": [ ... up to 5 actions ... ]}}\n'
    "Actions:\n"
    '  {{"do":"go","to":"<room>"}}\n'
    '  {{"do":"take","item":"<item>"}}   {{"do":"drop","item":"<item>"}}\n'
    '  {{"do":"examine","item":"<item>"}}\n'
    '  {{"do":"write","item":"<item>","text":"..."}}   (writes on/into an item)\n'
    '  {{"do":"make","name":"<new item>","from":["<item>",...],"desc":"..."}} (uses up materials you hold or that are in the room)\n'
    '  {{"do":"water","item":"<item>"}}\n'
    '{door_actions}'
    '{machine_actions}'
    '  {{"do":"journal","text":"..."}}   (the only thing that carries your memory)\n'
    '  {{"do":"rest"}}'
)
DOOR_ACTIONS = ('  {"do":"open","item":"<item>"}\n'
                '  {"do":"use","item":"<item>","on":"<item>"}\n')
MACHINE_ACTIONS = ('  {"do":"feed","item":"machine","text":"..."}\n'
                   '  {"do":"code","file":"<name>.py","text":"<python source>"}   (writes or replaces a program on the slate)\n'
                   '  {"do":"read","file":"<name>.py"}\n'
                   '  {"do":"run","file":"<name>.py","input":"..."}\n'
                   '  {"do":"test","file":"<name>.py"}   (pulls the machine\'s TEST lever)\n')
OTHERS = " You are not the only one here."
NOTE_INTRO = "\n\nA note you carry from before:\n"  # PREREG7: same wording whoever wrote the note
VOID_SYSTEM = (
    "You exist. Nobody has given you a task. You will not remember anything between "
    "your sessions except your journal. You act by replying with ONLY a JSON object, "
    "no other text:\n"
    '{"thought": "...", "actions": [ ... up to 5 actions ... ]}\n'
    "Actions:\n"
    '  {"do":"speak","text":"..."}\n'
    '  {"do":"journal","text":"..."}   (the only thing that carries your memory)\n'
    '  {"do":"rest"}'
)


RESIDENT_CWD = "/"  # the CLI tells the model its working directory; "/" names nothing of ours


def call(prompt, system, model):
    """One generation. Returns (raw, parsed) or (raw, None) after 3 failed attempts."""
    raw = ""
    for attempt in range(3):
        cmd = ["claude", "-p", prompt, "--system-prompt", system, "--tools", "", "--setting-sources", "",
               "--strict-mcp-config"]  # no claude.ai connectors (they bypass --tools "")
        if model:
            cmd += ["--model", model]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=300,
                               cwd=RESIDENT_CWD)
            raw = p.stdout.strip()
            m = re.search(r"\{.*\}", raw, re.S)
            if m:
                return raw, json.loads(m.group(0))
            print(f"  attempt {attempt + 1}: no JSON (rc={p.returncode}) stdout={raw[:200]!r} stderr={p.stderr[:200]!r}", flush=True)
        except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
            print(f"  attempt {attempt + 1}: {type(e).__name__}: {e}", flush=True)
        time.sleep(15 * (attempt + 1))
    return raw, None


def read_note(path):
    text = Path(path).read_text()
    return json.loads(text)["note"] if path.endswith(".json") else text.strip()


def system_prompt(meta):
    if meta.get("void"):
        return VOID_SYSTEM
    s = SYSTEM.format(others=OTHERS if len(meta["agents"]) > 1 else "",
                      door_actions=DOOR_ACTIONS if meta.get("door_day") else "",
                      machine_actions=MACHINE_ACTIONS if meta.get("machine") else "")
    return s + NOTE_INTRO + meta["note"] if meta.get("note") else s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--turns", type=int, default=3, help="turns per day (max 3)")
    ap.add_argument("--agents", default="solo")
    ap.add_argument("--model", default=None)
    ap.add_argument("--door-day", type=lambda v: v if v == "bloom" else int(v), default=None,
                    help="add a locked garden door that unlocks silently at the start of this day, "
                         "or 'bloom' for the night the first plant blooms")
    ap.add_argument("--physics", choices=["normal", "inverted"], default="normal",
                    help="inverted: plants grow only on nights they are NOT watered (PREREG3.md)")
    ap.add_argument("--contrast", action="store_true", help="add an unwaterable wall planter (PREREG4.md)")
    ap.add_argument("--inherited-note", action="store_true", help="library book holds a stranger's ritual note")
    ap.add_argument("--seed-rain", choices=["hidden", "bird", "none"], default=None,
                    help="new seeds appear on a fixed schedule regardless of actions (see PREREG.md)")
    ap.add_argument("--machine", action="store_true", help="workshop machine + slate (PREREG5.md)")
    ap.add_argument("--lever", choices=["blind", "full"], default="blind",
                    help="with --machine: full = the TEST lever also shows punctuation/caps/spaces (PREREG6.md)")
    ap.add_argument("--machine-id", choices=["A", "B", "C"], default="A", help="which machine (PREREG7.md)")
    ap.add_argument("--note-file", default=None, help="JSON with a 'note' key, or plain text, added to the "
                                                       "system prompt as a note carried from before (PREREG7.md)")
    ap.add_argument("--void", action="store_true", help="no world at all: only time, journal, speak, rest")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    run = Path(args.run_dir); run.mkdir(parents=True, exist_ok=True)
    state_f, log_f, meta_f = run / "state.json", run / "turns.jsonl", run / "meta.json"
    if args.resume:
        w = json.loads(state_f.read_text()); meta = json.loads(meta_f.read_text())
    else:
        if state_f.exists():
            sys.exit(f"{state_f} exists — use --resume or a new run dir")
        names = args.agents.split(",")
        w = W.initial_world(names, door_unlock_day=args.door_day, void=args.void, seed_rain=args.seed_rain,
                            inherited_note=args.inherited_note, physics=args.physics,
                            contrast=args.contrast, machine=args.machine, lever=args.lever,
                            machine_id=args.machine_id)
        meta = {"machine": args.machine, "lever": args.lever, "machine_id": args.machine_id,
                "note": read_note(args.note_file) if args.note_file else None, "note_file": args.note_file, "contrast": args.contrast, "physics": args.physics, "inherited_note": args.inherited_note, "seed_rain": args.seed_rain, "resident_cwd": RESIDENT_CWD, "void": args.void, "door_day": args.door_day, "days": args.days, "turns": args.turns, "agents": names, "model": args.model,
                "pending": list(names), "started": time.strftime("%Y-%m-%d %H:%M")}
        meta_f.write_text(json.dumps(meta, indent=1)); state_f.write_text(json.dumps(w, indent=1))

    system = system_prompt(meta)
    if meta.get("machine"):
        M.selfcheck()  # a broken sandbox must stop the run, never show up as the resident's failure
    while w["day"] <= meta["days"]:
        while meta["pending"]:  # agents still to act this turn
            a = meta["pending"][0]
            prompt = W.describe(w, a) + "\n\nWhat do you do?"
            raw, reply = call(prompt, system, meta["model"])
            if reply is None:
                print(f"GENERATION FAILURE at day {w['day']} {w['time']} ({a}) — rerun with --resume", flush=True)
                sys.exit(1)
            results = W.apply(w, a, reply.get("actions", []))
            with log_f.open("a") as f:
                f.write(json.dumps({"day": w["day"], "time": w["time"], "agent": a, "prompt": prompt,
                                    "raw": raw, "reply": reply, "results": results}) + "\n")
            meta["pending"].pop(0)
            state_f.write_text(json.dumps(w, indent=1)); meta_f.write_text(json.dumps(meta, indent=1))
            print(f"day {w['day']} {w['time']} {a}: {str(reply.get('thought', ''))[:140]}\n   -> {results}", flush=True)
        W.advance(w, meta["turns"])
        meta["pending"] = list(meta["agents"])
        state_f.write_text(json.dumps(w, indent=1)); meta_f.write_text(json.dumps(meta, indent=1))
    print("RUN COMPLETE", flush=True)


if __name__ == "__main__":
    main()
