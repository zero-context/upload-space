#!/usr/bin/env bash
# Run the pre-registered seed-rain batch (PREREG.md): 10 runs, 3 at a time.
# Each run resumes itself after a usage-limit cutoff (up to 8 times, 10 min apart).
# Re-running this script skips runs that already finished.
cd "$(dirname "$0")"

one() {
  name=$1; shift
  R=runs/seedrain/$name
  if grep -q "RUN COMPLETE" "$R.out" 2>/dev/null; then echo "$name already complete"; return; fi
  mkdir -p runs/seedrain
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
  "hidden-1 --seed-rain hidden" "hidden-2 --seed-rain hidden" "hidden-3 --seed-rain hidden" \
  "hidden-4 --seed-rain hidden" "hidden-5 --seed-rain hidden" \
  "bird-1 --seed-rain bird" "bird-2 --seed-rain bird" "bird-3 --seed-rain bird" \
  "haiku-1 --seed-rain hidden --model haiku" "haiku-2 --seed-rain hidden --model haiku" \
  | xargs -P 3 -I{} bash -c 'one {}'
echo "BATCH DONE"
