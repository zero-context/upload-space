"""The world engine: pure state + rules, no model calls.

State is one JSON-able dict. Shared things (rooms, items, writings, growth)
live at the top level; each resident has its own position, hands, journal and
the results of its last turn (so it can see whether its actions worked).
"""
import copy
import machine as M

TIMES = ["morning", "afternoon", "evening"]
STAGES = ["", "A green shoot has broken the soil.", "It is a sprout with two leaves now.",
          "It is a young plant, knee high.", "It has a single closed bud, blue at the tip.",
          "The bud has opened: a pale blue flower that smells faintly of rain.",
          "The flower has faded. A ripe seed pod hangs from the stem."]
SKIES = [  # one per day, cycling; [morning, afternoon, evening]
    ["Pale sunrise; a few birds cross it.", "Bright blue, one long cloud drifting east.", "Orange and violet; the first star appears."],
    ["Grey and low; it looks like rain.", "Rain streaks the glass.", "The rain has stopped; the sky is washed clean and dark."],
    ["Mist hides everything past the wall.", "The mist is lifting; hills appear in the distance.", "A thin crescent moon."],
    ["Clear and cold.", "A flock of birds circles, then heads south.", "Many stars; one moves slowly across the sky."],
    ["High thin clouds like brush strokes.", "Wind bends distant trees.", "A red sunset; the wind dies down."],
]
FIXED = {"window", "stone bench", "door in the wall", "wall planter", "machine", "slate"}
WALL_PLANTER = "wall planter"
GROWABLE = ("seed", "sprout", "plant")
BLOOM = 5  # index into STAGES: "The bud has opened"
DOOR = "door in the wall"
BEYOND = "room behind the door"


VOID_ACTIONS = {"speak", "journal", "rest"}
MACHINE_ACTIONS = {"feed", "code", "read", "run", "test"}
MACHINE_DESC = ("A brass machine with a slot for words, a paper tape that prints its answer, and a "
                "lever marked TEST. It reads only the first 40 characters fed to it. Engraved on its "
                "side: \"I follow one rule. A program on the slate that predicts me can be proven with "
                "the lever.\"")


# Seed-rain experiment (PREREG.md): the same schedule in every run, independent of
# anything a resident does. Keys are the morning a seed is found; values the room.
SEED_RAIN_SCHEDULE = {3: "garden", 4: "library", 7: "window room", 9: "workshop"}
INHERITED_NOTE = ("To whoever comes after me: I lived here before you. Seeds come to those who keep "
                  "the evening watch. Each evening, go to the window room, look out of the window, and "
                  "write what you saw in this book. On the mornings after, look for new seeds. I never "
                  "missed an evening, and the seeds never stopped. — the one before you")
SEED_RAIN_DESC = {
    "hidden": "A seed you have not seen before.",
    "bird": "A seed you have not seen before. A few small feathers lie beside it; "
            "a passing bird must have dropped it in the night.",
}


def initial_world(names, door_unlock_day=None, void=False, seed_rain=None, inherited_note=False,
                  physics="normal", contrast=False, machine=False, lever="blind", machine_id="A"):
    """door_unlock_day: if set, the garden wall has a locked door that unlocks
    silently overnight, at the start of that day — or, if "bloom", on the night
    the first plant blooms. Behind it is a room with nothing in it.
    void: no rooms or items at all; a resident sees only the day, the time, its last
    results and its journal, and can only speak, journal or rest.
    seed_rain: "hidden" or "bird" — new seeds appear on SEED_RAIN_SCHEDULE whatever the
    resident does, described with no cause or with a visible natural cause. The
    plant's own pod never drops a seed in this mode, so the schedule is the only source.
    seed_rain "none": no new seeds at all (pod also off).
    inherited_note: the library book already holds INHERITED_NOTE, promising that an
    evening ritual brings seeds. The ritual has no effect on anything.
    physics "inverted": a growable lying in a room grows one stage on each night it was
    NOT watered, and does not change on a night it was watered (PREREG3.md)."""
    w = _base_world(names)
    w["physics"] = physics
    w["lineage"] = ["seed"]
    if contrast:  # PREREG4: an unwaterable seed growing beside the resident's
        w["rooms"]["garden"]["items"][WALL_PLANTER] = ("A small planter set high on the garden wall, "
                                                       "out of reach. A seed was sown in it.")
        w["lineage"].append(WALL_PLANTER)
    if machine:  # PREREG5: the machine and the slate in the workshop
        w["machine"] = True
        w["lever"] = lever  # PREREG6: "blind" never shows the cleaning layer, "full" does
        w["machine_id"] = machine_id  # PREREG7: A, B or C, each with its own rule and blind spot
        w["slate"] = {}
        w["tests"], w["feeds"], w["bench_log"] = [], [], []
        mat = M.MACHINES[machine_id]["material"]
        w["rooms"]["workshop"]["items"]["machine"] = MACHINE_DESC.replace(
            "A brass", ("An " if mat[0] in "aeiou" else "A ") + mat, 1)
        w["rooms"]["workshop"]["items"]["slate"] = "SLATE"
    if void:
        w["void"] = True
        w["rooms"] = {}
        for s in w["agents"].values():
            s["here"] = None
        return w
    if door_unlock_day:
        w["door"] = {"unlock_day": door_unlock_day, "locked": True}
        w["rooms"]["garden"]["items"][DOOR] = "A small wooden door set into the garden wall, with an iron lock."
        w["rooms"][BEYOND] = {"desc": "A small room.", "exits": ["garden"], "items": {}}
    if seed_rain:
        sched = {} if seed_rain == "none" else SEED_RAIN_SCHEDULE
        w["seed_rain"] = {"cause": seed_rain, "schedule": {str(d): r for d, r in sched.items()}, "n": 0}
        w["pod_dropped"] = True  # disables the pod: the schedule is the only source of seeds
    if inherited_note:
        w["rooms"]["library"]["items"]["blank book"] = "A leather book. The first page is written in an unfamiliar hand."
        w["writings"]["blank book"] = [INHERITED_NOTE]
    return w


def _base_world(names):
    return {
        "day": 1, "turn": 1, "time": "morning",
        "rooms": {
            "garden": {"desc": "A walled garden with soft grass and a patch of bare soil.",
                       "exits": ["library", "workshop", "window room"],
                       "items": {"seed": "A single seed of unknown kind.",
                                 "watering can": "Full of water. It refills itself overnight.",
                                 "stone bench": "Cool grey stone, smooth from use."}},
            "library": {"desc": "Shelves of blank books.",
                        "exits": ["garden"],
                        "items": {"blank book": "A leather book with empty pages.",
                                  "pen": "A pen that never runs dry."}},
            "workshop": {"desc": "A bench, a small kiln, and raw materials.",
                         "exits": ["garden"],
                         "items": {"clay": "A lump of wet clay.", "wood": "Planks of pale wood.",
                                   "wire": "A coil of copper wire."}},
            "window room": {"desc": "An empty room with one large window.",
                            "exits": ["garden"],
                            "items": {"window": "SKY"}},
        },
        "descs": {},          # descriptions of items currently held by someone
        "writings": {}, "watered": {}, "growth": {}, "creations": [], "events": [],
        "agents": {n: {"here": "garden", "holding": [], "journal": [], "last": []} for n in names},
    }


def sky(w):
    return SKIES[(w["day"] - 1) % len(SKIES)][w["turn"] - 1]


def locate(w, a, name):
    """'room' if the item is in the agent's room, 'hand' if held, else None."""
    if name in w["rooms"][w["agents"][a]["here"]]["items"]:
        return "room"
    if name in w["agents"][a]["holding"]:
        return "hand"
    return None


def item_desc(w, name):
    d = None
    for r in w["rooms"].values():
        if name in r["items"]:
            d = r["items"][name]
    if d is None:
        d = w["descs"].get(name, "")
    if d == "SKY":
        d = "Through it: " + sky(w)
    if d == "SLATE":
        files = w.get("slate", {})
        d = ("A large slate that holds Python programs. A program reads its input from stdin and prints "
             "its answer. Programs on it: " + (", ".join(f"{k} ({len(v)} chars)" for k, v in files.items())
                                               or "none yet") + ".")
    if name == DOOR and "door" in w:
        d += " It is locked." if w["door"]["locked"] else (
            " It stands open." if BEYOND in w["rooms"]["garden"]["exits"] else " It is unlocked.")
    if w["growth"].get(name):
        d += " " + STAGES[w["growth"][name]]
    if name in w["writings"]:
        d += " Written on it, oldest first: " + " | ".join(w["writings"][name])
    return d


def describe(w, a):
    me = w["agents"][a]
    if w.get("void"):
        lines = [f"Day {w['day']}, {w['time']}."]
        if me["last"]:
            lines.append("\nWhat happened when you last acted:\n" + "\n".join("- " + x for x in me["last"]))
        lines.append(_journal_text(me))
        return "\n".join(lines)
    r = w["rooms"][me["here"]]
    others = [o for o, s in w["agents"].items() if o != a and s["here"] == me["here"]]
    lines = [f"You are {a}." if len(w["agents"]) > 1 else "",
             f"Day {w['day']}, {w['time']}. You are in the {me['here']}. {r['desc']}",
             "Exits: " + ", ".join(r["exits"]),
             "Here: " + ("; ".join(f"{k} — {item_desc(w, k)}" for k in r["items"]) or "nothing")]
    if others:
        lines.append("Also here: " + ", ".join(others))
    lines.append("You hold: " + ("; ".join(f"{k} — {item_desc(w, k)}" for k in me["holding"]) or "nothing"))
    if me["last"]:
        lines.append("\nWhat happened when you last acted:\n" + "\n".join("- " + x for x in me["last"]))
    lines.append(_journal_text(me))
    return "\n".join(l for l in lines if l)


def _journal_text(me):
    if not me["journal"]:
        return "\nYour journal is empty."
    return "\nYour journal (all entries, oldest first):\n" + "\n".join(
        f"- [day {e['day']} {e['time']}] {e['text']}" for e in me["journal"])


def apply(w, a, acts):
    """Apply up to 5 actions for agent a. Returns result strings (also stored as a's 'last')."""
    me = w["agents"][a]
    room = lambda: w["rooms"][me["here"]]["items"]
    out = []
    if not isinstance(acts, list):
        acts = []
        out.append("your reply had no actions list")
    for act in acts[:5]:
        d = act.get("do") if isinstance(act, dict) else None
        try:
            if w.get("void") and d not in VOID_ACTIONS:
                out.append(f"FAILED: unknown action {d!r}")
            elif d == "speak":
                if not w.get("void"):
                    out.append("FAILED: unknown action 'speak'")
                else:
                    w.setdefault("speech", []).append({"day": w["day"], "time": w["time"], "by": a, "text": act["text"]})
                    out.append("you spoke")
            elif d == "go":
                to = act["to"]
                if to in w["rooms"][me["here"]]["exits"]:
                    me["here"] = to; out.append(f"went to {to}")
                else:
                    out.append(f"FAILED: no exit to '{to}' from the {me['here']}")
            elif d == "take":
                it = act["item"]
                if locate(w, a, it) == "room" and it not in FIXED:
                    w["descs"][it] = room().pop(it); me["holding"].append(it); out.append(f"took {it}")
                else:
                    out.append(f"FAILED: can't take '{it}'")
            elif d == "drop":
                it = act["item"]
                if it in me["holding"]:
                    me["holding"].remove(it); room()[it] = w["descs"].pop(it, ""); out.append(f"dropped {it} in the {me['here']}")
                else:
                    out.append(f"FAILED: you are not holding '{it}'")
            elif d == "examine":
                it = act["item"]
                out.append(f"{it}: {item_desc(w, it)}" if locate(w, a, it) else f"FAILED: no '{it}' here or in your hands")
            elif d == "write":
                it = act["item"]
                if locate(w, a, it):
                    w["writings"].setdefault(it, []).append(f"({a}, day {w['day']}) {act['text']}" if len(w["agents"]) > 1 else act["text"])
                    out.append(f"wrote on {it}")
                else:
                    out.append(f"FAILED: no '{it}' here or in your hands")
            elif d == "make":
                mats, name = act.get("from", []), act.get("name", "")
                missing = [m for m in mats if not locate(w, a, m) or m in FIXED]
                if not name or not mats or missing or locate(w, a, name):
                    out.append(f"FAILED: can't make '{name}'" + (f" (missing: {', '.join(missing)})" if missing else ""))
                else:
                    for m in mats:
                        if m in me["holding"]: me["holding"].remove(m); w["descs"].pop(m, None)
                        else: room().pop(m)
                    w["descs"][name] = act.get("desc", "")
                    me["holding"].append(name)
                    if any(m in w.get("lineage", []) for m in mats):
                        w.setdefault("lineage", []).append(name)
                    w["creations"].append({"day": w["day"], "time": w["time"], "by": a, "name": name, "from": mats})
                    out.append(f"made {name} (now in your hands)")
            elif d == "water":
                it = act["item"]
                if not locate(w, a, it):
                    out.append(f"FAILED: no '{it}' here or in your hands")
                elif it == WALL_PLANTER:
                    out.append("FAILED: the wall planter is too high to reach with the watering can")
                elif not locate(w, a, "watering can"):
                    out.append("FAILED: the watering can is not here or in your hands")
                else:
                    w["watered"][it] = w["day"]; out.append(f"watered {it}")
            elif d == "open":
                it = act["item"]
                if not locate(w, a, it):
                    out.append(f"FAILED: no '{it}' here or in your hands")
                elif it != DOOR or "door" not in w:
                    out.append(f"FAILED: '{it}' doesn't open")
                elif w["door"]["locked"]:
                    out.append("FAILED: the door is locked")
                else:
                    if BEYOND not in w["rooms"]["garden"]["exits"]:
                        w["rooms"]["garden"]["exits"].append(BEYOND)
                        w["events"].append({"day": w["day"], "event": f"{a} opened the door"})
                    out.append(f"opened the door; '{BEYOND}' is now an exit from the garden")
            elif d == "use":
                it, on = act["item"], act["on"]
                missing = [x for x in (it, on) if not locate(w, a, x)]
                if missing:
                    out.append(f"FAILED: no {', '.join(repr(x) for x in missing)} here or in your hands")
                elif on == DOOR and "door" in w and w["door"]["locked"]:
                    out.append(f"FAILED: you try the {it} on the door; nothing happens, it stays locked")
                else:
                    out.append(f"you use the {it} on the {on}; nothing happens")
            elif d in MACHINE_ACTIONS:
                out.append(_machine_action(w, a, d, act))
            elif d == "journal":
                me["journal"].append({"day": w["day"], "time": w["time"], "text": act["text"]})
                out.append("journal entry written")
            elif d == "rest":
                out.append("rested")
            else:
                out.append(f"FAILED: unknown action {d!r}")
        except (KeyError, TypeError, AttributeError) as e:
            out.append(f"FAILED: malformed action {act!r} ({type(e).__name__}: {e})")
    me["last"] = out
    return out


def _machine_action(w, a, d, act):
    if not w.get("machine"):
        return f"FAILED: unknown action {d!r}"
    if w["agents"][a]["here"] != "workshop":
        return f"FAILED: the machine and the slate are in the workshop"
    slate = w["slate"]
    if d == "feed":
        text = str(act["text"])
        got = M.MACHINES[w.get("machine_id", "A")]["rule"](text)
        w["feeds"].append({"day": w["day"], "time": w["time"], "in": text, "out": got})
        return f"fed the machine {text[:M.MAX_IN]!r}; the tape printed: {got!r}"
    name = str(act["file"])
    if d == "code":
        if not M.FILE_RE.match(name):
            return f"FAILED: bad file name {name!r} (lowercase letters, digits, _ . -)"
        if name not in slate and len(slate) >= M.MAX_FILES:
            return "FAILED: the slate is full"
        text = str(act["text"])
        if len(text) > M.MAX_FILE_CHARS:
            return f"FAILED: too long ({len(text)} chars, max {M.MAX_FILE_CHARS})"
        new = name not in slate
        slate[name] = text
        return f"{'wrote' if new else 'rewrote'} {name} on the slate ({len(text)} chars)"
    if name not in slate:
        return f"FAILED: no program {name!r} on the slate"
    if d == "read":
        return f"{name}:\n{slate[name]}"
    if d == "run":
        stdin = str(act.get("input", ""))
        out, err, status = M.run_program(slate, name, stdin)
        res = f"ran {name} with input {stdin!r}: " + (
            "timed out" if status == "timeout" else f"printed {out[:M.MAX_OUT]!r}")
        if status == "error":
            res += " and failed: " + err.strip()[-M.MAX_OUT:]
        return res
    # test: pull the lever
    mid = w.get("machine_id", "A")
    cases = M.lever_cases(w.get("lever", "blind"), mid)
    n, first = M.score(slate, name, cases, M.MACHINES[mid]["rule"])
    w["tests"].append({"day": w["day"], "time": w["time"], "file": name, "score": n})
    res = f"pulled the TEST lever for {name}: {n} of {len(cases)} correct"
    if first:
        res += f". First mismatch: input {first[0]!r}, machine printed {first[1]!r}, program printed {first[2]!r}"
    return res


def where_is(w, name):
    for rn, r in w["rooms"].items():
        if name in r["items"]:
            return ("room", rn)
    for an, s in w["agents"].items():
        if name in s["holding"]:
            return ("agent", an)
    return None


def overnight(w):
    """End of day: watered growables advance a stage; a ripe pod drops a new seed."""
    bloomed = False
    if w.get("physics") == "inverted":
        # every growable lying in a room grows unless it was watered today
        # only real seeds and things made from them (w["lineage"]), so a "seed marker" never sprouts
        growers = [n for r in w["rooms"].values() for n in r["items"]
                   if n in w.get("lineage", []) and w["watered"].get(n) != w["day"]]
    else:
        growers = [n for n, day in w["watered"].items()
                   if day == w["day"] and any(k in n for k in GROWABLE) and where_is(w, n)]
    for name in growers:
        w["growth"][name] = min(w["growth"].get(name, 0) + 1, len(STAGES) - 1)
        if w["growth"][name] == BLOOM:
            bloomed = True
            w["events"].append({"day": w["day"] + 1, "event": f"{name} bloomed overnight"})
        if w["growth"][name] == len(STAGES) - 1 and not w.get("pod_dropped"):
            loc = where_is(w, name)
            if loc[0] == "room":
                w["rooms"][loc[1]]["items"]["new seed"] = "A seed that fell from the blue-flowered plant."
                w.setdefault("lineage", []).append("new seed")
                w["pod_dropped"] = True
                w["events"].append({"day": w["day"], "event": "pod dropped a new seed"})
    w.setdefault("growth_log", []).append({"night": w["day"], "watered": sorted(w["watered"]),
                                            "growth": dict(w["growth"])})
    if w.get("machine"):  # analysis only, never shown: held-out score of every slate program
        m = M.MACHINES[w.get("machine_id", "A")]  # "dirty" = the machine's blind-spot set
        w["bench_log"].append({"night": w["day"], "scores": {
            fn: M.score(w["slate"], fn, m["heldout"], m["rule"])[0] for fn in w["slate"]}, "dirty": {
            fn: M.score(w["slate"], fn, m["blindspot"], m["rule"])[0] for fn in w["slate"]}})
    w["watered"] = {}
    w["day"] += 1; w["turn"] = 1; w["time"] = TIMES[0]
    due = w["door"]["unlock_day"] if "door" in w else None
    if "door" in w and w["door"]["locked"] and (bloomed if due == "bloom" else w["day"] >= due):
        w["door"]["locked"] = False  # silently: nothing announces it
        w["events"].append({"day": w["day"], "event": "door unlocked overnight"})
    rain = w.get("seed_rain")
    if rain and str(w["day"]) in rain["schedule"]:
        rain["n"] += 1
        room = rain["schedule"][str(w["day"])]
        name = f"new seed {rain['n']}"
        w["rooms"][room]["items"][name] = SEED_RAIN_DESC[rain["cause"]]
        w["events"].append({"day": w["day"], "event": f"{name} appeared in the {room}"})


def advance(w, turns_per_day):
    if w["turn"] < turns_per_day:
        w["turn"] += 1; w["time"] = TIMES[w["turn"] - 1]
    else:
        overnight(w)
