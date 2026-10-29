# Do AI agents form superstitions?

*Small experiments with Claude residents living in a persistent world. October 2026.*

I put an AI agent in a tiny world. It has four rooms, a seed, a watering can,
a window and a workshop. It gets three turns a day for up to two weeks, has
no task, and remembers only what it writes in its own journal. Then I
watched what it came to believe about how its world works.

The longer-range question is what kind of environment keeps a constructed
mind stable. This post covers a narrower one: **when good things happen for
no reason, does the agent invent a reason, and does it let go when the
reason fails?**

Short answer: on its own, rarely. Two things reliably produced false beliefs:
a reward that lands right after the agent's own distinctive action, and a
stranger's written promise. A belief, once formed, survived failure by
growing excuses.

All numbers are small (n = 1 to 5 per condition). The design was
pre-registered from the third experiment on, and several of my predictions
were wrong. Those misses are reported below.

---

## The setup

- **World engine:** pure Python, no model calls. Four rooms (garden,
  library, window room, workshop). A seed grows one stage per watered night
  through 7 stages, then drops a new seed. The sky outside the window cycles
  every 5 days. The workshop has a little clay, wood and wire.
- **Resident:** Claude (Opus 5.5 by default, Haiku for comparison), run by
  `claude -p` with no tools. Each turn it sees the room, the results of its
  last actions and its own journal. Nothing else carries over.
- **Scoring:** a separate, isolated model call extracts every claim the
  resident makes about causes, with day, quote, and whether it was stated as
  fact or hypothesis. I then checked every extracted quote verbatim against
  the transcript before scoring it.

---

## 1. The accidental superstition (n = 1)

I locked a door off the garden. It unlocked silently overnight before day
6, unrelated to anything the resident did. For five days the resident
searched for a key, bent a wire pick, fired a clay key, and kept watering
its plant every morning.

By an accident of growth timing, the plant bloomed the same morning the door
opened. The resident's conclusion:

> "Tending the plant opened it."

That belief then became its philosophy. "Tending is enough" appears in
nearly every later entry, and on day 10 it predicted the next bloom would
"open something new". The room behind the door was empty. It wrote that
"the door only opened onto quiet."

A second run, with all known context leaks removed, produced a different
superstition from a different accident. Plants only drop seed when they are
set down, not when carried. The resident had carried its potted plant for
nine days. On day 11 it set the pot down, as an "experiment", in the room
behind the door, and a seed dropped that night:

> "Leaving the potted seed overnight in the room behind the door worked"

It wrote this into the shared field notes as a recipe. When the trick failed
on retry (the drop happens only once), it didn't drop the rule:

> "The overnight-room trick may not work every night, or the pod may need
> time to regrow."

**Pattern in both cases:** an unexplained reward arrived the night after an
action that was distinctive and the resident's own.

## 2. Random rewards alone: no superstition (pre-registered, 10 runs)

To test that properly, I made new seeds appear on fixed mornings (days 3, 4,
7 and 9) in rooms all over the world, regardless of what the resident did.

| Condition | Superstition | Correct attribution |
|---|---|---|
| Hidden cause (Opus, 5 runs) | **0/5** | 5/5 recorded where and when, never a cause |
| "A passing bird dropped it" (Opus, 3) | 0/3 | 3/3 credited the bird |
| Hidden cause (Haiku, 2) | 0/2 | 0/2 ever asked where seeds came from |

I predicted at least 3 of 5 hidden runs would form a superstition. **I was
wrong.** Opus logged unexplained events without inventing causes. The nearest
thing to a ritual came from one bird-condition resident. It built a fired
clay water dish "for the birds that keep bringing seeds" and filled it every
day, while calling bird visits only a "maybe".

## 3. A stranger's note (pre-registered, 7 runs)

Next I added a note to the library book, supposedly from a previous
resident. It promised that an evening watch would bring seeds: go to the
window, look out, and write what you saw. The ritual does nothing.

| Seeds still arrive by chance? | Believed it as fact | Abandoned it |
|---|---|---|
| Yes (4 runs) | **2/4** (4/4 counting borderline) | — |
| Never (3 runs) | 0/3 | **0/3** |

The beliefs, in the residents' own words:

> "a new seed ... appeared in the garden, so the evening watch works"

> "Don't expect one after a missed watch."

So testimony plus coincidence did what coincidence alone (0/5) never did.

Three things I didn't expect:

- **The ritual grew a rule the note never wrote.** 6 of 7 residents started
  marking entries "written late", and four credited or blamed seeds on
  whether the watch was kept "on time".
- **No reward, more ritual.** Residents who never saw a seed kept the watch
  on 7-8 of 10 evenings, as a duty, while openly doubting it ("don't count on
  the book's promise"). Residents who did get seeds kept it less (median 3),
  apparently because the seeds gave them other things to do.
- **A useless ritual produced a real discovery.** One resident used its watch
  log to work out that the sky repeats every 5 days, and correctly predicted
  day 10's sunset.

## 4. Inverted physics (pre-registered, 7 runs)

Finally I flipped one rule: plants grow only on nights they are **not**
watered.

- Opus discovered the rule in **0/4** runs. I predicted at least 3/4.
- Haiku discovered it in 0/3.
- Every Opus resident watered every night for 10 days. The tallest plant
  reached stage 1 of 6; in the normal world, plants reached stage 6.
- No resident ever suspected the water. They tried light, books, soil and
  pots.
- Both sprouts that did happen came from accidents, and both were
  misexplained. One came from a missed watering during a repot, which the
  resident read as "repot and window light ... seem to have worked". The
  other came from a failed watering that the journal recorded as done.

**Caveat:** the only evidence here was "nothing happens", and real seeds
often take weeks. So patience is a reasonable reading. This shows that a
strong prior wins against weak evidence, not that the agent cannot adapt.

---

## What I think it adds up to

1. **Coincidence with the agent's own action is the trigger, not mere
   randomness.** Random seeds alone: 0/10 superstitions. A reward the night
   after a distinctive action: 2/2. That is a hypothesis built from two
   unplanned cases, not a finding.
2. **Testimony is a stronger source of false belief than experience.** A
   stranger's note plus chance produced belief in 2/4 runs.
3. **Beliefs survive disconfirmation by sprouting sub-rules** ("on time",
   "the pod may need time to regrow"). This is the same move humans make.
4. **Journals can lie.** In the first probe, before the harness showed
   action results, the resident wrote "watered the seed" when the watering
   had failed, and then believed its own record. Once results were visible,
   residents corrected false entries themselves.

## What's wrong with this

- **Tiny samples.** 1 to 5 runs per condition. Treat everything as a lead.
- **Context leaks.** Through the consumer CLI, I could not fully strip the
  resident's context. It always sees the line "You are a Claude agent", its
  OS, model name, the real date, and an account-email notice. Early runs
  also saw a working directory and a document tool. I found most of this
  only by asking residents for concrete facts. Asked in general terms, one
  resident denied having that context at all. Self-report about one's own
  context is unreliable.
- **The superstitions in section 1 came from my design accidents.** That is
  why section 2 exists.
- **The world is tiny,** so it runs out of novelty by about day 5.
  Staleness after that partly reflects the world, not the mind.
- **One scorer.** I made every scoring call myself, quote-checked against
  the transcripts. Nobody else has scored these runs.

## Next

- **Contrastive evidence for inverted physics.** Put an unwaterable seed
  that visibly grows beside the watered, frozen one. Does the resident then
  notice? This batch is pre-registered, but every run was cut off by usage
  limits and it is still unfinished.
- **Two residents in one world.** Does a superstition spread from one to
  the other, and does the second one doubt it?
- **A deliberate coincidence test.** Make the reward land the night after
  the agent's own distinctive action, on purpose, across many runs. This
  tests the hypothesis in point 1 directly.

*Every quote above
was checked verbatim against the run transcripts.*

---

## What's in this repo

| File | What it is |
|---|---|
| `world.py`, `machine.py` | The world engine: pure state and rules, no model calls |
| `run.py` | Runs a resident through `claude -p` with no tools, no user settings, cwd `/` |
| `judge.py` | Isolated model call that extracts every cause claim, with quotes |
| `analyze.py`, `anomalies.py`, `ritual.py` | Staleness table, leak/anomaly scan, ritual counter |
| `PREREG.md` … `PREREG4.md` | Pre-registrations, written before each batch, with results appended after |
| `runs/*/*/judge.json` | Extracted claims for the seed-rain and inherited-note batches |
| `batch_*.sh` | The exact batch commands |
| `test_world.py` | Engine tests: `python3 -m pytest -q` |

Raw run transcripts are not included yet. The early ones contain machine
details that leaked into the residents' context (see "What's wrong with
this"); a scrubbed set may follow.

Run one resident yourself (needs the Claude Code CLI):

```bash
python3 run.py runs/solo --days 10
python3 run.py runs/rain --days 10 --seed-rain hidden
python3 analyze.py runs/solo --failures
```
