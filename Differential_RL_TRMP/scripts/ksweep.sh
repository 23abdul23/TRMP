#!/bin/bash
# Block-destroy kappa sweep at EQUAL EVALUATIONS: run r of every kappa stops when it has used the same number of
# candidate evaluations as run r of the kappa=4 full-protocol run (out/full_block/<inst>.csv, column evals_calls).
# Resumable (skips finished jobs). usage: scripts/ksweep.sh [parallel]      (from Differential_RL_TRMP/)
P=${1:-4}; cd "$(dirname "$0")/.." || exit 1
make -s out/es_drl || exit 1; mkdir -p out/ksweep
N400="covers_dirn400m240r150s03i00 covers_dirn400m240r150s04i00 covers_dirn400m240r150s06i01"
N200="covers_dirn200m120r150s06i00 covers_dirn200m120r150s03i03 covers_dirn200m120r150s04i01 covers_dirn200m120r150s06i01"
{ for i in $N400; do for k in 12 16 8 6 3; do echo "$i $k 8"; done; done
  for i in $N200; do for k in 12 16 8 6 3; do echo "$i $k 10"; done; done; } |
 xargs -P "$P" -L1 sh -c 'i=$0; k=$1; r=$2; [ -s out/ksweep/$i.k$k.row ] || { rm -f out/ksweep/$i.k$k.csv; ./out/es_drl --instance instances/$i.dat --policy block --kappa $k --runs $r --budget-csv out/full_block/$i.csv --out out/ksweep/$i.k$k.row.tmp --runs-csv out/ksweep/$i.k$k.csv >/dev/null 2>&1 && mv out/ksweep/$i.k$k.row.tmp out/ksweep/$i.k$k.row; }'
