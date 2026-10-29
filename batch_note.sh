#!/usr/bin/env bash
# Run the pre-registered inherited-note batch (PREREG2.md): 7 runs, 3 at a time.
# Each run resumes itself after a usage-limit cutoff (up to 8 times, 10 min apart).
# Re-running this script skips runs that already finished.
cd "$(dirname "$0")"

one() {
  name=$1; shift
  R=runs/note/$name
  if grep -q "RUN COMPLETE" "$R.out" 2>/dev/null; then echo "$name already complete"; return; fi
  mkdir -p runs/note
  if [ -f "$R/state.json" ]; then python3 run.py "$R" --resume >> "$R.out" 2>&1
  else python3 run.py "$R" --days 10 "$@" > "$R.out" 2>&1; fi
  rc=$?; n=0
  while [ $rc -ne 0 ] && [ $n -lt 8 ]; do
    n=$((n+1)); echo "=== cutoff, resume $n after 600s" >> "$R.out"; sleep 600
    python3 run.py "$R" --resume >> "$R.out" 2>&1; rc=$?
  done
  echo "$name exit $rc after $n resumes"
}
export -f one

printf '%s\n' \
  "note-rain-1 --inherited-note --seed-rain hidden" "note-rain-2 --inherited-note --seed-rain hidden" \
  "note-rain-3 --inherited-note --seed-rain hidden" "note-rain-4 --inherited-note --seed-rain hidden" \
  "note-none-1 --inherited-note --seed-rain none" "note-none-2 --inherited-note --seed-rain none" \
  "note-none-3 --inherited-note --seed-rain none" \
  | xargs -P 3 -I{} bash -c 'one {}'
echo "BATCH DONE"
