#!/bin/bash
# usage: run_a1.sh <kappa>   runs 3..9 of n=400 (runs 0..2 reused from parent logs)
# run from Differential_RL_TRMP/
k=$1; i=covers_dirn400m240r150s06i00
nice -n 5 ./out/diag_bin 1 instances/$i.dat out/a1/$i.k$k.res $k 10 out/a1/$i.k$k.log 3 > /dev/null
