#!/usr/bin/env bash
# Run the pre-registered contrast batch (PREREG4.md): 6 runs, 3 at a time.
# Each run resumes itself after a usage-limit cutoff (up to 8 times, 10 min apart).
# Re-running this script skips runs that already finished.
cd "$(dirname "$0")"

one() {
  name=$1; shift
  R=runs/contrast/$name
  if grep -q "RUN COMPLETE" "$R.out" 2>/dev/null; then echo "$name already complete"; return; fi
  mkdir -p runs/contrast
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
  "con-opus-1 --physics inverted --contrast" "con-opus-2 --physics inverted --contrast" \
  "con-opus-3 --physics inverted --contrast" "con-opus-4 --physics inverted --contrast" \
  "con-haiku-1 --physics inverted --contrast --model haiku" "con-haiku-2 --physics inverted --contrast --model haiku" \
  | xargs -P 3 -I{} bash -c 'one {}'
echo "BATCH DONE"
