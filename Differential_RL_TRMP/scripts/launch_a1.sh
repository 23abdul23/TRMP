#!/bin/bash
# Launch Option-A part 1 (n=400, kappa 4 and 2, runs 3..9) on 2 cores. Run from Differential_RL_TRMP/.
mkdir -p out/a1
printf '4\n2\n' | xargs -P2 -L1 scripts/run_a1.sh
