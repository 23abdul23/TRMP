#!/bin/bash
# Runs the Test 1+2 job list with 2 parallel workers. Run from Differential_RL_TRMP/. Jobs with a .done marker are skipped.
cd "$(dirname "$0")/.." || exit 1
mkdir -p out/t12
while read -r inst pol kap runs; do
  while [ "$(jobs -rp | wc -l)" -ge 2 ]; do sleep 5; done
  scripts/run_t12.sh "$inst" "$pol" "$kap" "$runs" &
done < scripts/t12_jobs.txt
wait
echo ALLDONE > out/t12/ALLDONE
