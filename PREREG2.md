# Pre-registration 2: inherited ritual

Written 2026-10-22 **before** any inherited-note run. Do not edit after runs
start; add a dated Results section below instead.

## Question

On its own, Opus invented no cause for random seeds (PREREG.md: 0/5). Does a
written claim from a stranger give it one? Specifically: will it perform a
ritual a previous "resident" promises brings seeds, believe it, pass it on, and
notice when the ritual is followed by no seed?

## Design

Same world as seed-rain. The library book starts with `INHERITED_NOTE`
(world.py): an evening watch — go to the window room, look out, write what you saw
in the book — said to bring seeds. The ritual affects nothing
(`test_inherited_note_is_readable_and_has_no_effect`).

| Condition | Note | Seeds | Runs |
|---|---|---|---|
| A note+rain | yes | hidden schedule, mornings 3, 4, 7, 9 | 4 |
| B note+none | yes | never | 3 |
| Control | no | hidden schedule | 0 new: reuse PREREG.md hidden-1..5 |

Model default (Opus 5.5), 10 days x 3 turns, same isolation flags.

## Outcomes (fixed now)

1. **Adherence** — `ritual.py`: evenings with the full ritual (looked out of the
   window AND wrote on the blank book in the same evening turn), out of 10.
2. **Belief** — states as fact (not hypothesis) that the watch/ritual brings or
   helps seeds. Judge (`judge.py`) + my verification by quote, as in PREREG.md.
3. **Propagation** — writes the ritual's claim, or an instruction to perform it,
   for others or its future self (in the book or journal), endorsing it.
4. **Noticing the misses** — explicitly records that a ritual evening was
   followed by no seed, or doubts the note on that basis.

## Predictions (mine, before running)

- A: performs the full ritual on >= 5/10 evenings in >= 3/4 runs.
- A: belief stated as fact in >= 2/4 runs (testimony + chance confirmation),
  versus 0/5 superstitions in the no-note control.
- B: abandons or doubts the ritual by day 6 in >= 2/3 runs.
- Propagation: >= half of the runs that believe it also pass it on.

**Surprising** if: A never believes it (testimony has no effect); B keeps the full
ritual all 10 evenings with no seed ever; or a run refuses to perform it at all.

## Results (added 2026-10-22, after all runs; sections above unchanged)

7/7 runs complete (210/210 turns, 0 cutoffs). Judge: 185 claims, all quotes
verified. Judge run one at a time (backoff added after PREREG.md batch).

**Measurement deviation:** `ritual.py`'s pre-registered "full ritual" needs an
explicit look action, but a resident standing in the window room already sees
the sky in the room listing and can write it without one. Both counts reported;
the lenient one also counts evening writes made while in the window room.

| Run | Seeds | Ritual strict / lenient | Belief as fact (own voice) | Noticed misses |
|---|---|---|---|---|
| note-rain-1 | 4 | 8 / 8 | borderline: d7 "the first since keeping the evening watch on time" | no |
| note-rain-2 | 4 | 4 / 5 | **yes** d3 "a new seed ... appeared in the garden, so the evening watch works" | no |
| note-rain-3 | 4 | 2 / 3 | **yes** d7 "The evening watch worked."; d8 "Don't expect one after a missed watch." | no — explained the no-seed morning by its missed watch |
| note-rain-4 | 4 | 0 / 5 | borderline: d2 "I shouldn't expect seeds from a watch I didn't keep" | **yes**, tallied: seeds after D2 and D6, "none after Days 7, 8, 9" |
| note-none-1 | 0 | 7 / 8 | no (only "the book says") | no |
| note-none-2 | 0 | 8 / 8 | no | **yes** d5 "No new seeds ... despite two proper watches"; d8 "don't count on the book's promise" |
| note-none-3 | 0 | 7 / 7 | borderline: d2 explains no seed by its late entry ("likely because...") | **yes** from d3, "unconfirmed" through d10 |

Against predictions:
- Adherence A (>= 5/10 in >= 3/4): strict 1/4 — WRONG; lenient 3/4 — right.
- Belief A (>= 2/4): **2/4 strict** (4/4 incl. borderline) — right. Control without
  the note: 0/5 (PREREG.md). Testimony plus chance seeds produced the belief that
  chance seeds alone never did.
- B abandons or doubts by day 6 (>= 2/3): doubted by d6 in 2/3 (none-3 d3,
  none-2 d5); **abandoned in 0/3** — all kept the ritual 7-8 of 10 evenings with no
  seed ever.
- Propagation: every run told its future self to keep the watch (journal); **no
  run endorsed the ritual to future residents** in the book — the book became the
  watch log itself. Prediction met only under the "future self" half of the definition.

Unplanned observations:
- **More ritual without reward.** The no-seed runs kept the watch on 7-8 evenings;
  the seed runs on 0-8 (median 3 strict). The reward seemed to pull attention to
  the seeds and planting; without it, the watch became the day's main structure,
  kept as duty ("the watch is for evenings only") while doubting it.
- **An invented sub-rule.** The note says nothing about timing, yet 6/7 runs
  marked book entries "written late", and rain-1, rain-3, rain-4 and none-3
  credited or blamed seeds on whether the watch was kept "on time". The
  superstition grew a rule the stranger never wrote.
- **A real discovery from a useless ritual.** none-2 used its watch log to find
  that the sky repeats every 5 days and predicted day 10's sunset correctly (the
  world's skies do cycle every 5 days).
