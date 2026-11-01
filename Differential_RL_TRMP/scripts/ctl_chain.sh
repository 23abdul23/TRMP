#!/bin/bash
# usage: ctl_chain.sh <fixk2|rand>   -- runs the equal-evaluation control on n=100 then n=198 (10 runs each)
cd "$(dirname "$0")/.." || exit 1
scripts/run_reduced_b.sh ctl 100 instances/covers_dirn100m060r150s06i03.dat 10 "$1"
scripts/run_reduced_b.sh ctl 198 instances/covers_dirn200m120r150s06i00.dat 10 "$1"
