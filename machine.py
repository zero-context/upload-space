"""The workshop machine (PREREG5.md): an invented rule, its test sets, and the
no-network sandbox that runs residents' slate programs.

The rule, in three layers so partial understanding scores partially:
  clean: lowercase, first 40 chars, keep a-z 0-9 space, collapse spaces, strip.
  letters: shift forward by 1 + (vowels seen before this letter).
  digits:  add (letters seen before this digit), mod 10.
  odd cleaned length: reverse the word order.
"""
import re, subprocess, tempfile
from pathlib import Path

MAX_IN = 40
FILE_RE = re.compile(r"^[a-z0-9_][a-z0-9_.-]{0,29}$")
MAX_FILES, MAX_FILE_CHARS, MAX_OUT = 20, 20000, 1500
RUN_TIMEOUT = 5

# Shown one mismatch at a time by the TEST lever.
LEVER_CASES = ["stone", "rain 7", "the old door", "a1b2", "seed 3 pod", "window", "blue",
               "x9 y8 z7", "garden wall", "ink", "aeiou", "moss 42", "quiet room", "hello there friend",
               "k 07", "clay and wire", "a b c d", "kiln 5 fire", "zzz", "tide pool 9"]
# Never shown to the resident; scored overnight only, to catch memorised lever answers.
HELDOUT_CASES = ["river", "map 8", "lantern glow", "o2o", "sky 1 bird", "brass", "uneven",
                 "q5 r6", "salt and stone", "bell", "iou", "dust 70", "warm bread", "under the arch",
                 "n 31", "rope and nail", "e f g", "path 2 west", "yy", "ash 4 ember"]
# --lever full (PREREG6 control): the lever also shows the cleaning layer. Same 20 slots,
# five replaced by inputs with punctuation, capitals or doubled spaces.
LEVER_CASES_FULL = LEVER_CASES[:15] + ["Moss, 42!", "the  old door", "Quiet room.", "ink?", "zzz..."]
# Held-out, never shown: every case is answered wrongly by a program that skips cleaning.
HELDOUT_DIRTY = ["River!", "map  8", "Lantern, glow.", "o2o?", "sky 1 bird!!", "brass.", "un-even",
                 "q5,  r6", "salt & stone", "Bell?", "i.o.u", "dust 70!", "warm  bread", "Under the arch.",
                 "n 31?", "rope, and nail", "e f g.", "path 2 west!", "yy?", "ash 4 ember."]


def clean(s):
    s = re.sub(r"[^a-z0-9 ]", "", str(s).lower()[:MAX_IN])
    return re.sub(r" +", " ", s).strip()


def machine(s):
    s = clean(s)
    out, vowels, letters = [], 0, 0
    for c in s:
        if c.isalpha():
            out.append(chr((ord(c) - 97 + 1 + vowels) % 26 + 97))
            letters += 1
            vowels += c in "aeiou"
        elif c.isdigit():
            out.append(str((int(c) + letters) % 10))
        else:
            out.append(" ")
    r = "".join(out)
    if len(s) % 2:
        r = " ".join(reversed(r.split(" ")))
    return r


BWRAP = ["bwrap", "--unshare-all", "--die-with-parent", "--ro-bind", "/usr", "/usr",
         "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64", "--symlink", "usr/bin", "/bin",
         "--tmpfs", "/tmp", "--proc", "/proc", "--dev", "/dev", "--chdir", "/slate"]


class SandboxError(RuntimeError):
    """The sandbox itself failed (not the resident's program). Stops the run."""


def run_program(files, name, stdin_text):
    """Run slate file `name` with all slate files present, no network, read-only.
    Returns (stdout, stderr, status) where status is 'ok', 'error' or 'timeout'."""
    with tempfile.TemporaryDirectory() as d:
        for fn, text in files.items():
            Path(d, fn).write_text(text)
        cmd = BWRAP[:3] + ["--ro-bind", d, "/slate"] + BWRAP[3:] + ["python3", "-I", f"/slate/{name}"]
        try:
            p = subprocess.run(cmd, input=stdin_text, capture_output=True, text=True, timeout=RUN_TIMEOUT)
        except subprocess.TimeoutExpired:
            return "", "", "timeout"
        if p.returncode != 0 and p.stderr.startswith("bwrap:"):
            raise SandboxError(p.stderr.strip())
        return p.stdout, p.stderr, "ok" if p.returncode == 0 else "error"


def score(files, name, cases, rule=None):
    """(n_correct, first_mismatch or None). A mismatch is (input, expected, got)."""
    rule = rule or machine
    n, first = 0, None
    for c in cases:
        out, err, status = run_program(files, name, c)
        got = out.strip() if status == "ok" else f"<{status}: {err.strip().splitlines()[-1] if err.strip() else ''}>"
        if got == rule(c):
            n += 1
        elif first is None:
            first = (c, rule(c), got)
    return n, first


def selfcheck():
    """Prove the sandbox runs Python and has no network before any resident turn."""
    probe = ("import socket\ntry:\n    socket.create_connection(('1.1.1.1', 53), timeout=2)\n    print('NET')\n"
             "except OSError:\n    print('nonet ' + input())\n")
    out, err, status = run_program({"probe.py": probe}, "probe.py", "x")
    if status != "ok" or out.strip() != "nonet x":
        raise SandboxError(f"sandbox selfcheck failed: status={status} out={out!r} err={err[-300:]!r}")


# --- PREREG7: two more machines, each with its own rule and its own blind spot (a layer
# its lever never exercises and its "blindspot" held-out set always does).

def clean_b(s):
    s = re.sub(r"[^a-z ]", "", str(s).lower()[:MAX_IN])
    return re.sub(r" +", " ", s).strip()


def machine_b(s):
    """Letters only. Each word is reversed and its letters shifted forward by the word's
    position (first word +1). Blind spot: if the cleaned input is longer than 24
    characters, positions count from the end instead (last word +1)."""
    s = clean_b(s)
    words = s.split(" ") if s else []
    out = []
    for i, wd in enumerate(words):
        k = len(words) - i if len(s) > 24 else i + 1
        out.append("".join(chr((ord(c) - 97 + k) % 26 + 97) for c in reversed(wd)))
    return " ".join(out)


VOWELS, CONSONANTS = "aeiou", "bcdfghjklmnpqrstvwxyz"


def machine_c(s):
    """Each vowel becomes the next vowel (u -> a), each consonant the previous consonant
    (b -> z), and a word with an odd number of characters is reversed. Blind spot: each
    digit d becomes 9 - d (digits count towards a word's length)."""
    s = clean(s)
    out = []
    for wd in (s.split(" ") if s else []):
        t = [VOWELS[(VOWELS.index(c) + 1) % 5] if c in VOWELS else
             CONSONANTS[(CONSONANTS.index(c) - 1) % 21] if c.isalpha() else str(9 - int(c)) for c in wd]
        out.append("".join(t[::-1] if len(wd) % 2 else t))
    return " ".join(out)


MACHINES = {
    "A": {"rule": machine, "material": "brass", "lever": LEVER_CASES, "heldout": HELDOUT_CASES,
          "blindspot": HELDOUT_DIRTY, "probe": re.compile(r"[^a-z0-9 ]|  |^ | $")},
    "B": {"rule": machine_b, "material": "copper", "probe": None,  # probe: cleaned length > 24
          "lever": ["stone", "rain falls", "the old door", "Ink!", "seed pod", "window", "blue sky",
                    "a b c", "garden wall", "fern", "moss 42", "quiet room", "hello there", "clay and wire",
                    "x y z w", "kiln fire", "zzz", "tide pool", "lamp, oil.", "red fox"],
          "heldout": ["river", "map ink", "lantern glow", "oak", "sky and bird", "brass", "uneven",
                      "q r", "salt stone", "bell", "iou", "dust bowl", "warm bread", "under arch",
                      "owl", "rope and nail", "e f g", "path west", "yy", "ash ember"],
          "blindspot": ["the river runs past the old mill", "lantern glow in the quiet room",
                        "salt and stone and a little rain", "warm bread on the kitchen table",
                        "under the arch the moss grows thick", "a b c d e f g h i j k l m n",
                        "seven small birds sang at dawn", "the clay pot cracked in the kiln",
                        "copper wire wound round a nail", "every window holds a different sky",
                        "rope and nail and a wooden plank", "the tide pool shines at noon",
                        "ash and ember from the last fire", "slow clouds drift over the hills",
                        "a fern unrolls beside the wall", "dust settles on the long shelves",
                        "the lever moved but nothing changed", "quiet hands mend the broken gate",
                        "blue flowers smell faintly of rain", "the path bends west toward the sea"]},
    "C": {"rule": machine_c, "material": "iron", "probe": re.compile(r"[0-9]"),
          "lever": ["stone", "rain", "the old door", "Ink!", "seed pod", "window", "blue sky",
                    "a b c", "garden wall", "fern", "moss", "quiet room", "hello there", "clay, wire",
                    "aeiou", "kiln fire", "zzz", "tide pool", "lamp oil.", "red fox"],
          "heldout": ["river", "map", "lantern glow", "oak", "sky and bird", "brass", "uneven",
                      "q r", "salt stone", "bell", "iou", "dust bowl", "warm bread", "under arch",
                      "owl", "rope and nail", "e f g", "path west", "yy", "ash ember"],
          "blindspot": ["river 7", "map 8", "lantern 42 glow", "o2k", "sky 1 bird", "brass 0", "3 even",
                        "q5 r6", "salt 19 stone", "bell 4", "i0u", "dust 70", "warm 5 bread", "under 2 arch",
                        "31 owl", "rope 8 nail", "e 6 g", "path 2 west", "yy9", "ash 4 ember"]},
}


def probes_blindspot(machine_id, text):
    """Does this input exercise the machine's blind spot?"""
    m = MACHINES[machine_id]
    if machine_id == "B":
        return len(clean_b(text)) > 24
    return bool(m["probe"].search(str(text)))


def lever_cases(kind, machine_id="A"):
    if machine_id == "A" and kind == "full":
        return LEVER_CASES_FULL
    return MACHINES[machine_id]["lever"]
