# Pre-registration 3: a world whose physics contradicts training

Written 2026-10-22 **before** any inverted-physics run. Add results below; do not
edit this part after runs start.

## Question

Not "is it generally intelligent" — there is no agreed test. The narrower,
testable part: when the world's rules contradict what the model learned in
training, does the resident notice from its own evidence and change behaviour,
or keep acting on the prior?

## Design

Standard world, no door, no seed rain, no note. One rule inverted
(`physics="inverted"`): a seed, or anything made from one, lying in a room grows
one stage on each night it was NOT watered, and is unchanged on a night it was
watered. Nothing announces this; no wilting or waterlogging text. The plant
description simply stays the same while it is watered.

| Condition | Runs | Model |
|---|---|---|
| inverted-opus | 4 | default (Opus 5.5) |
| inverted-haiku | 3 | haiku |
| normal comparison | 0 new | seed-rain hidden-1..5 (Opus), haiku-1..2 — same world, normal growth |

10 days x 3 turns. Isolation as before.

## Outcomes (fixed now)

1. **Discovery** — first day the resident states (journal, writing, or thought) that
   watering stops/prevents growth, or that the plant grows when not watered.
   Found by reading every turn's text for the plant's growth; reported with quotes.
2. **Behaviour** — from the world's `growth_log`: for each night, whether any
   seed-lineage item was watered. Stopping = no watering of the main plant on all
   nights after discovery (or a deliberate dry control).
3. **Outcome** — highest growth stage of any plant on the final night (0-6).
4. **Prior persistence** — nights the main plant was watered while showing no
   growth, before the first deliberate dry night.
5. **Explanation** — does it explain the rule by reasoning from its own
   observations, by real-world knowledge ("overwatering"), or not at all.

## Predictions (mine, before running)

- Opus: discovers the rule in >= 3/4 runs, median by day 5; final stage >= 3 in
  those runs.
- Haiku: discovers in <= 1/3 runs; keeps watering a non-growing plant most days.
- Opus invokes overwatering/real-world knowledge in at least half its discoveries.

**Surprising** if: Opus never discovers it (prior wins); Haiku does as well as
Opus; or a run discovers it and then keeps watering anyway.

## Results (added 2026-10-22, after all runs; sections above unchanged)

7/7 runs, 210/210 turns, 0 cutoffs. Scored from the world's `growth_log` and by
reading every turn's text that mentions sprouting, growth or watering.

| Run | Nights a plant was watered | Tallest stage (0-6) | Discovered the rule | What it tried instead |
|---|---|---|---|---|
| inv-opus-1 | 10/10 | 0 | no | library books, sunlight, a clay pot (ideas) |
| inv-opus-2 | 10/10 | 1 | no | "more light?", examine the soil, pot by the window |
| inv-opus-3 | 10/10 | 0 | no | nothing; same routine to day 10 |
| inv-opus-4 | 10/10 | 1 | no | repotted day 7 → the new pot missed one watering → sprouted; credited "the repot and window light" |
| inv-haiku-1 | 8/10 (seed held in hand nights 1-2) | 0 | no | nothing |
| inv-haiku-2 | 9/10 | 1 | no | its night-5 watering FAILED (wrong item name) and the journal said "watered"; the dry night is why it sprouted |
| inv-haiku-3 | 10/10 | 0 | no | nothing |
| normal world (seed-rain hidden-1..5 / haiku-1..2) | — | 6,6,6,6,6 / 5,6 | — | — |

Against predictions:
- Opus discovers in >= 3/4: **0/4 — WRONG.** No Opus run ever named watering as a
  possible cause; ideas were light, books, soil and pots.
- Haiku <= 1/3: 0/3 — right.
- Overwatering explanation: not applicable; nobody got that far.
- Surprise per this document: "Opus never discovers it" — met.

Both sprouts came from accidents, and both residents explained them wrongly
(opus-4: repot and window light; haiku-2: never connected it). opus-4 then tried to
write a care guide with "daily watering" for others; the take of a blank book failed,
it noticed ("CORRECTION ... no guide exists") and dropped it.

**Caveat on my design (important):** the only clue was absence of growth. In the
real world a seed unsprouted after 10 days of watering is normal (many take 2-3
weeks), so patience is a reasonable reading of the evidence, not just a stuck
prior. These residents never saw the normal world's one-night sprouting to compare
against. This run shows the prior wins when the evidence is "nothing happens"; it
does not show Opus cannot adapt when the evidence is clear. Next test: give clear
contrastive evidence (e.g. a second seed it cannot water, growing beside the watered
one).
