#!/bin/bash
# One core, low priority. Run from Differential_RL_TRMP/ (needs out/diag_noop built from src/diag_noop.c).
mkdir -p out/noop
for i in covers_dirn100m060r150s06i03 covers_dirn200m120r150s06i00; do
  for k in 2 4 8; do
    nice -n 5 ./out/diag_noop 1 instances/$i.dat out/noop/$i.k$k.res $k 3 out/noop/$i.k$k.log > /dev/null
  done
done
echo finished > out/noop/DONE
