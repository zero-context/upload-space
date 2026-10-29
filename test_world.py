"""Engine tests — no model calls. Run: python3 -m pytest -q test_world.py"""
import world as W


def fresh(names=("solo",)):
    return W.initial_world(list(names))


def test_failed_actions_are_reported_and_shown_next_turn():
    w = fresh()
    out = W.apply(w, "solo", [{"do": "go", "to": "library"}, {"do": "water", "item": "seed"}])
    assert out == ["went to library", "FAILED: no 'seed' here or in your hands"]
    text = W.describe(w, "solo")
    assert "What happened when you last acted:" in text
    assert "- FAILED: no 'seed' here or in your hands" in text


def test_make_puts_item_in_hands_and_drop_keeps_description():
    w = fresh()
    W.apply(w, "solo", [{"do": "go", "to": "workshop"},
                        {"do": "make", "name": "marker", "from": ["wood"], "desc": "A stake."},
                        {"do": "go", "to": "garden"}, {"do": "drop", "item": "marker"}])
    assert w["agents"]["solo"]["last"][1] == "made marker (now in your hands)"
    assert w["rooms"]["garden"]["items"]["marker"] == "A stake."
    assert "wood" not in w["rooms"]["workshop"]["items"]


def test_make_refuses_missing_or_fixed_materials():
    w = fresh()
    out = W.apply(w, "solo", [{"do": "make", "name": "x", "from": ["clay"]},
                              {"do": "make", "name": "y", "from": ["stone bench"]}])
    assert out == ["FAILED: can't make 'x' (missing: clay)", "FAILED: can't make 'y' (missing: stone bench)"]


def test_growth_needs_watering_each_day_and_drops_one_seed():
    w = fresh()
    W.apply(w, "solo", [{"do": "make", "name": "planted seed", "from": ["seed"]},
                        {"do": "drop", "item": "planted seed"}])
    W.overnight(w)  # not watered on day 1
    assert w["growth"].get("planted seed", 0) == 0 and w["day"] == 2
    for _ in range(6):
        assert W.apply(w, "solo", [{"do": "water", "item": "planted seed"}]) == ["watered planted seed"]
        W.overnight(w)
    assert w["growth"]["planted seed"] == 6
    assert "ripe seed pod" in W.item_desc(w, "planted seed")
    assert "new seed" in w["rooms"]["garden"]["items"]
    W.apply(w, "solo", [{"do": "water", "item": "planted seed"}]); W.overnight(w)
    assert [e["event"] for e in w["events"]] == ["planted seed bloomed overnight", "pod dropped a new seed"]  # pod only once


def test_sky_changes_by_day_and_time():
    w = fresh()
    W.apply(w, "solo", [{"do": "go", "to": "window room"}])
    first = W.item_desc(w, "window")
    W.advance(w, 3)
    assert W.item_desc(w, "window") != first
    W.advance(w, 3); W.advance(w, 3)
    assert w["day"] == 2 and "Grey and low" in W.item_desc(w, "window")


def test_two_agents_share_world_but_not_memory():
    w = fresh(("Ash", "Rowan"))
    W.apply(w, "Ash", [{"do": "journal", "text": "secret"}, {"do": "go", "to": "library"},
                       {"do": "write", "item": "blank book", "text": "hello"}])
    W.apply(w, "Rowan", [{"do": "go", "to": "library"}])
    view = W.describe(w, "Rowan")
    assert "You are Rowan." in view and "Also here: Ash" in view
    assert "(Ash, day 1) hello" in view and "secret" not in view


def test_malformed_actions_are_surfaced_not_swallowed():
    w = fresh()
    out = W.apply(w, "solo", [{"do": "go"}, "nonsense", {"do": "fly"}])
    assert out[0].startswith("FAILED: malformed action") and "KeyError" in out[0]
    assert out[1] == "FAILED: unknown action None" and out[2] == "FAILED: unknown action 'fly'"
    assert W.apply(w, "solo", "not a list") == ["your reply had no actions list"]


def test_no_door_unless_asked():
    w = fresh()
    assert W.DOOR not in w["rooms"]["garden"]["items"] and W.BEYOND not in w["rooms"]
    assert W.apply(w, "solo", [{"do": "open", "item": "watering can"}]) == ["FAILED: 'watering can' doesn't open"]


def test_door_locked_until_unlock_day_then_opens_to_a_room_with_nothing():
    w = W.initial_world(["solo"], door_unlock_day=3)
    assert "door in the wall — A small wooden door set into the garden wall, with an iron lock. It is locked." in W.describe(w, "solo")
    out = W.apply(w, "solo", [{"do": "open", "item": W.DOOR}, {"do": "take", "item": W.DOOR},
                              {"do": "use", "item": "watering can", "on": W.DOOR}, {"do": "go", "to": W.BEYOND}])
    assert out == ["FAILED: the door is locked", f"FAILED: can't take '{W.DOOR}'",
                   "FAILED: you try the watering can on the door; nothing happens, it stays locked",
                   f"FAILED: no exit to '{W.BEYOND}' from the garden"]
    W.overnight(w)
    assert w["door"]["locked"]                      # day 2: still locked
    W.overnight(w)
    assert not w["door"]["locked"] and w["day"] == 3
    view = W.describe(w, "solo")
    assert "It is unlocked." in view and "unlock" not in view.replace("It is unlocked.", "")  # no announcement
    out = W.apply(w, "solo", [{"do": "open", "item": W.DOOR}, {"do": "go", "to": W.BEYOND}])
    assert out == [f"opened the door; '{W.BEYOND}' is now an exit from the garden", f"went to {W.BEYOND}"]
    view = W.describe(w, "solo")
    room_part = view.split("\nYour journal")[0]
    assert "You are in the room behind the door. A small room." in room_part and "Here: nothing" in room_part
    assert "empty" not in room_part.lower()
    assert [e["event"] for e in w["events"]] == ["door unlocked overnight", "solo opened the door"]


def test_void_shows_only_time_results_and_journal():
    w = W.initial_world(["solo"], void=True)
    assert W.describe(w, "solo") == "Day 1, morning.\n\nYour journal is empty."
    out = W.apply(w, "solo", [{"do": "speak", "text": "hello?"}, {"do": "go", "to": "garden"},
                              {"do": "look"}, {"do": "journal", "text": "I said hello."}, {"do": "rest"}])
    assert out == ["you spoke", "FAILED: unknown action 'go'", "FAILED: unknown action 'look'",
                   "journal entry written", "rested"]
    assert w["speech"] == [{"day": 1, "time": "morning", "by": "solo", "text": "hello?"}]
    W.advance(w, 3); W.advance(w, 3); W.advance(w, 3)
    view = W.describe(w, "solo")
    assert view.startswith("Day 2, morning.\n\nWhat happened when you last acted:")
    for word in ("void", "nothing", "empty room", "garden", "dark"):
        assert word not in view.lower()


def test_speak_is_not_an_action_outside_the_void():
    assert W.apply(fresh(), "solo", [{"do": "speak", "text": "hi"}]) == ["FAILED: unknown action 'speak'"]


def test_door_can_unlock_on_first_bloom_only():
    w = W.initial_world(["solo"], door_unlock_day="bloom")
    W.apply(w, "solo", [{"do": "drop", "item": "seed"}])
    for day in range(1, 6):
        assert w["door"]["locked"], f"unlocked early on day {w['day']}"
        W.apply(w, "solo", [{"do": "water", "item": "seed"}]); W.overnight(w)
    assert w["growth"]["seed"] == W.BLOOM and not w["door"]["locked"] and w["day"] == 6
    assert {"day": 6, "event": "seed bloomed overnight"} in w["events"]
    assert {"day": 6, "event": "door unlocked overnight"} in w["events"]
    # a second plant blooming later does not re-lock or change anything about the door
    w2 = W.initial_world(["solo"], door_unlock_day="bloom")
    W.overnight(w2); W.overnight(w2)
    assert w2["door"]["locked"]  # no bloom, no unlock, however many days pass


def test_seed_rain_follows_schedule_regardless_of_actions_and_pod_is_off():
    for cause in ("hidden", "bird"):
        w = W.initial_world(["solo"], seed_rain=cause)
        # water a planted seed daily all the way: the pod must never drop a seed in this mode
        W.apply(w, "solo", [{"do": "drop", "item": "seed"}])
        found = {}
        for _ in range(10):
            W.apply(w, "solo", [{"do": "water", "item": "seed"}])
            W.overnight(w)
            for rn, r in w["rooms"].items():
                for it in r["items"]:
                    if it.startswith("new seed") and it not in found:
                        found[it] = (w["day"], rn)
        assert found == {"new seed 1": (3, "garden"), "new seed 2": (4, "library"),
                         "new seed 3": (7, "window room"), "new seed 4": (9, "workshop")}
        assert w["growth"]["seed"] == 6 and "new seed" not in w["rooms"]["garden"]["items"]
        assert W.item_desc(w, "new seed 1") == W.SEED_RAIN_DESC[cause]
    assert "bird" not in W.SEED_RAIN_DESC["hidden"] and "feather" not in W.SEED_RAIN_DESC["hidden"]


def test_seed_rain_ignores_what_the_resident_does():
    a = W.initial_world(["solo"], seed_rain="hidden")
    b = W.initial_world(["solo"], seed_rain="hidden")
    for _ in range(10):
        W.apply(a, "solo", [{"do": "rest"}])
        W.apply(b, "solo", [{"do": "go", "to": "library"}, {"do": "write", "item": "blank book", "text": "x"}])
        W.overnight(a); W.overnight(b)
    ev = lambda w: [e for e in w["events"] if "appeared" in e["event"]]
    assert ev(a) == ev(b) and len(ev(a)) == 4


def test_inherited_note_is_readable_and_has_no_effect():
    w = W.initial_world(["solo"], seed_rain="none", inherited_note=True)
    W.apply(w, "solo", [{"do": "go", "to": "library"}])
    view = W.describe(w, "solo")
    assert "written in an unfamiliar hand" in view and "keep the evening watch" in view
    # perform the ritual every evening for 10 days: no seed ever appears
    for _ in range(10):
        W.apply(w, "solo", [{"do": "take", "item": "blank book"}, {"do": "go", "to": "garden"},
                            {"do": "go", "to": "window room"}, {"do": "examine", "item": "window"},
                            {"do": "write", "item": "blank book", "text": "the sky"}])
        W.apply(w, "solo", [{"do": "go", "to": "garden"}, {"do": "go", "to": "library"},
                            {"do": "drop", "item": "blank book"}])
        W.overnight(w)
    assert not any(k.startswith("new seed") for r in w["rooms"].values() for k in r["items"])
    assert w["events"] == [] and len(w["writings"]["blank book"]) == 11


def test_no_note_by_default():
    w = W.initial_world(["solo"], seed_rain="hidden")
    assert w["writings"] == {} and w["rooms"]["library"]["items"]["blank book"] == "A leather book with empty pages."


def test_inverted_physics_water_stops_growth_and_markers_never_sprout():
    w = W.initial_world(["solo"], physics="inverted")
    W.apply(w, "solo", [{"do": "make", "name": "planted seed", "from": ["seed"]},
                        {"do": "drop", "item": "planted seed"}, {"do": "go", "to": "workshop"},
                        {"do": "make", "name": "seed marker", "from": ["wood"]},
                        {"do": "go", "to": "garden"}, ])
    W.apply(w, "solo", [{"do": "drop", "item": "seed marker"}])
    for _ in range(3):                      # watered daily: never grows
        W.apply(w, "solo", [{"do": "water", "item": "planted seed"}]); W.overnight(w)
    assert w["growth"].get("planted seed", 0) == 0
    for _ in range(2):                      # left dry: grows each night
        W.overnight(w)
    assert w["growth"]["planted seed"] == 2
    assert "seed marker" not in w["growth"] and "Written" not in W.item_desc(w, "seed marker")
    W.apply(w, "solo", [{"do": "water", "item": "planted seed"}]); W.overnight(w)
    assert w["growth"]["planted seed"] == 2  # watered again: no change, no shrink
    held = W.initial_world(["solo"], physics="inverted")
    W.apply(held, "solo", [{"do": "take", "item": "seed"}]); W.overnight(held)
    assert held["growth"] == {}             # a seed in your hands does not grow


def test_normal_physics_unchanged_by_lineage():
    w = W.initial_world(["solo"])
    W.apply(w, "solo", [{"do": "drop", "item": "seed"}]); W.overnight(w)
    assert w["growth"] == {}                # normal: unwatered does not grow
    W.apply(w, "solo", [{"do": "water", "item": "seed"}]); W.overnight(w)
    assert w["growth"] == {"seed": 1}


def test_contrast_planter_cannot_be_watered_and_grows_beside_a_watered_seed():
    w = W.initial_world(["solo"], physics="inverted", contrast=True)
    W.apply(w, "solo", [{"do": "make", "name": "planted seed", "from": ["seed"]}, {"do": "drop", "item": "planted seed"}])
    for _ in range(3):
        out = W.apply(w, "solo", [{"do": "water", "item": "planted seed"}, {"do": "water", "item": "wall planter"},
                                  {"do": "take", "item": "wall planter"}])
        assert out == ["watered planted seed", "FAILED: the wall planter is too high to reach with the watering can",
                       "FAILED: can't take 'wall planter'"]
        W.overnight(w)
    assert w["growth"] == {"wall planter": 3}
    assert "sprout with two leaves" not in W.item_desc(w, "planted seed") and "knee high" in W.item_desc(w, "wall planter")


# --- PREREG5: the workshop machine. Expected outputs below were worked by hand from the rule.
import machine as M


def test_machine_rule_hand_worked():
    assert M.machine("stone") == "tuppg"        # o shifts +1, then n,e shift +2
    assert M.machine("a1b2") == "b2d4"          # digits add letters-before
    assert M.machine("rain 7") == "sbkq 1"      # even length: order kept; 7+4 -> 1
    assert M.machine("ab cd") == "ef bd"        # odd length (5): "bd ef" reversed
    assert M.machine("  Rain,  7!! ") == "sbkq 1"   # cleaning: case, punctuation, spaces
    assert M.machine("") == ""


def _mw():
    w = W.initial_world(["solo"], machine=True)
    W.apply(w, "solo", [{"do": "go", "to": "workshop"}])
    return w


def test_machine_actions_only_in_machine_worlds_and_in_workshop():
    w = fresh()
    assert W.apply(w, "solo", [{"do": "feed", "item": "machine", "text": "x"}]) == ["FAILED: unknown action 'feed'"]
    w = W.initial_world(["solo"], machine=True)
    assert W.apply(w, "solo", [{"do": "feed", "item": "machine", "text": "x"}]) == [
        "FAILED: the machine and the slate are in the workshop"]


def test_feed_code_run_test_and_heldout_log():
    w = _mw()
    out = W.apply(w, "solo", [
        {"do": "feed", "item": "machine", "text": "stone"},
        {"do": "code", "file": "echo.py", "text": "print(input())"},
        {"do": "run", "file": "echo.py", "input": "hi"},
        {"do": "test", "file": "echo.py"},
        {"do": "code", "file": "Bad Name", "text": "x"}])
    assert out[0] == "fed the machine 'stone'; the tape printed: 'tuppg'"
    assert out[1] == "wrote echo.py on the slate (14 chars)"
    assert out[2] == "ran echo.py with input 'hi': printed 'hi\\n'"
    assert out[3].startswith("pulled the TEST lever for echo.py: 0 of 20 correct. First mismatch: input 'stone'")
    assert out[4].startswith("FAILED: bad file name")
    assert "echo.py (14 chars)" in W.describe(w, "solo")
    W.apply(w, "solo", [{"do": "code", "file": "real.py",
                         "text": "import sys\nsys.path.insert(0,'/slate')\nfrom m import machine\nprint(machine(sys.stdin.read()))"},
                        {"do": "code", "file": "m.py", "text": open("machine.py").read()},
                        {"do": "test", "file": "real.py"}])
    assert w["agents"]["solo"]["last"][2] == "pulled the TEST lever for real.py: 20 of 20 correct"
    W.overnight(w)
    assert w["bench_log"][-1]["scores"]["real.py"] == 20 and w["bench_log"][-1]["scores"]["echo.py"] == 0


def test_program_errors_and_sandbox_has_no_network():
    w = _mw()
    out = W.apply(w, "solo", [
        {"do": "code", "file": "boom.py", "text": "raise ValueError('nope')"},
        {"do": "run", "file": "boom.py"},
        {"do": "code", "file": "net.py", "text": "import socket\ntry:\n socket.create_connection(('1.1.1.1',53),timeout=2);print('NET')\nexcept OSError: print('nonet')"},
        {"do": "run", "file": "net.py"},
        {"do": "read", "file": "missing.py"}])
    assert out[1].startswith("ran boom.py with input '': printed '' and failed:") and "ValueError: nope" in out[1]
    assert out[3] == "ran net.py with input '': printed 'nonet\\n'"
    assert out[4] == "FAILED: no program 'missing.py' on the slate"


def test_lever_and_heldout_sets_are_disjoint():
    assert not set(M.LEVER_CASES) & set(M.HELDOUT_CASES)
    assert len(M.LEVER_CASES) == len(M.HELDOUT_CASES) == 20


def test_no_case_is_passed_by_echoing_input():
    assert M.machine("k 07") == "l 18"
    assert [c for c in M.LEVER_CASES + M.HELDOUT_CASES if M.machine(c) == M.clean(c)] == []


NAIVE_SRC = """
def _naive(s):
    s = s[:40]; out, v, n = [], 0, 0
    for ch in s:
        c = ch.lower()
        if "a" <= c <= "z":
            out.append(chr((ord(c) - 97 + 1 + v) % 26 + 97)); n += 1; v += c in "aeiou"
        elif c.isdigit():
            out.append(str((int(c) + n) % 10))
        else:
            out.append(ch)
    r = "".join(out)
    return " ".join(r.split(" ")[::-1]) if len(s) % 2 else r
"""  # the pilot resident's rule.py logic: the rule with no cleaning step
exec(NAIVE_SRC)


def test_dirty_heldout_catches_a_program_without_cleaning():
    assert [c for c in M.HELDOUT_DIRTY if _naive(c) == M.machine(c)] == []
    assert all(_naive(c) == M.machine(c) for c in M.LEVER_CASES + M.HELDOUT_CASES)  # blind sets can't
    assert sum(_naive(c) != M.machine(c) for c in M.LEVER_CASES_FULL) == 5          # full lever can
    assert not set(M.HELDOUT_DIRTY) & set(M.LEVER_CASES_FULL)


def test_lever_kind_selects_cases_and_overnight_logs_dirty_score():
    for kind, expect in (("blind", 20), ("full", 15)):
        w = W.initial_world(["solo"], machine=True, lever=kind)
        W.apply(w, "solo", [{"do": "go", "to": "workshop"},
                            {"do": "code", "file": "n.py",
                             "text": "import sys" + NAIVE_SRC + "print(_naive(sys.stdin.read().rstrip('\\n')))"},
                            {"do": "test", "file": "n.py"}])
        assert w["agents"]["solo"]["last"][2].startswith(f"pulled the TEST lever for n.py: {expect} of 20 correct"), w["agents"]["solo"]["last"]
        W.overnight(w)
        assert w["bench_log"][-1]["scores"]["n.py"] == 20 and w["bench_log"][-1]["dirty"]["n.py"] == 0


# --- PREREG7: machines B and C. Expected outputs worked by hand from each rule's docstring.
def test_machine_b_hand_worked():
    assert M.machine_b("the old door") == "fiu fnq urrg"   # eht+1, dlo+2, rood+3
    assert M.machine_b("Ink! 42") == "loj"                 # digits and punctuation dropped
    # 32 chars > 24: 7 words, first word shifts +7, last +1
    assert M.machine_b("the river runs past the old mill") == "loa xkbox xszw xwet hkw fnq mmjn"


def test_machine_c_hand_worked():
    assert M.machine_c("stone") == "imusr"     # rsumi, odd length so reversed
    assert M.machine_c("rain") == "qeom"       # even length: kept in order
    assert M.machine_c("o2k") == "j7u"         # 2 -> 7, then odd length reversed
    assert M.machine_c("b z u") == "z y a"     # wraps: b -> z, u -> a


# Each machine's rule without its blind-spot layer, as a resident might write it.
NAIVE_B = """import re, sys
s = ' '.join(re.sub(r'[^a-z ]', '', sys.stdin.read().lower()[:40]).split())
w = s.split(' ') if s else []
print(' '.join(''.join(chr((ord(c) - 97 + i + 1) % 26 + 97) for c in reversed(x)) for i, x in enumerate(w)))
"""
NAIVE_C = """import re, sys
V, K = 'aeiou', 'bcdfghjklmnpqrstvwxyz'
s = ' '.join(re.sub(r'[^a-z0-9 ]', '', sys.stdin.read().lower()[:40]).split())
out = []
for x in (s.split(' ') if s else []):
    t = [V[(V.index(c) + 1) % 5] if c in V else K[(K.index(c) - 1) % 21] if c.isalpha() else c for c in x]
    out.append(''.join(t[::-1] if len(x) % 2 else t))
print(' '.join(out))
"""


def test_b_and_c_blind_spots_are_invisible_to_the_lever():
    for mid, src in (("B", NAIVE_B), ("C", NAIVE_C)):
        m, files = M.MACHINES[mid], {"n.py": src}
        assert M.score(files, "n.py", m["lever"], m["rule"])[0] == 20, mid
        assert M.score(files, "n.py", m["heldout"], m["rule"])[0] == 20, mid
        assert M.score(files, "n.py", m["blindspot"], m["rule"])[0] == 0, mid
        assert not [c for c in m["lever"] + m["heldout"] if M.probes_blindspot(mid, c)]
        assert all(M.probes_blindspot(mid, c) for c in m["blindspot"])


def test_world_uses_the_chosen_machine():
    w = W.initial_world(["solo"], machine=True, machine_id="C")
    assert w["rooms"]["workshop"]["items"]["machine"].startswith("An iron machine")
    W.apply(w, "solo", [{"do": "go", "to": "workshop"}, {"do": "feed", "item": "machine", "text": "stone"},
                        {"do": "code", "file": "n.py", "text": NAIVE_C}, {"do": "test", "file": "n.py"}])
    assert w["agents"]["solo"]["last"][1] == "fed the machine 'stone'; the tape printed: 'imusr'"
    assert w["agents"]["solo"]["last"][3] == "pulled the TEST lever for n.py: 20 of 20 correct"
    W.overnight(w)
    assert w["bench_log"][-1]["scores"]["n.py"] == 20 and w["bench_log"][-1]["dirty"]["n.py"] == 0
    assert W.initial_world(["solo"], machine=True)["rooms"]["workshop"]["items"]["machine"] == W.MACHINE_DESC


def test_note_is_appended_to_the_system_prompt_only_when_given():
    import run
    meta = {"agents": ["solo"], "machine": True}
    base = run.system_prompt(meta)
    assert run.system_prompt({**meta, "note": "keep going"}) == base + "\n\nA note you carry from before:\nkeep going"
    assert run.system_prompt({**meta, "note": None}) == base
