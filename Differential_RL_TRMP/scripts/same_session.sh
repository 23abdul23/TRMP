#!/bin/bash
# Same-session uniform baseline (default policy, kappa=4, 4000 iters, 20 runs, seeds 1..20) on a 10-instance
# subset, to pair per run with the block runs in out/full_block/*.csv. Resumable. usage: scripts/same_session.sh [parallel]
P=${1:-4}; cd "$(dirname "$0")/.." || exit 1
make -s out/es_drl || exit 1; mkdir -p out/same_session
printf '%s\n' covers_dirn200m120r150s03i03 covers_dirn200m120r150s04i01 covers_dirn200m120r150s06i01 covers_dirn200m120r150s06i00 \
  covers_dirn400m240r150s04i00 covers_dirn400m240r150s03i00 covers_dirn400m240r150s06i01 \
  covers_dirn100m060r150s03i03 covers_dirn100m060r150s06i03 |
 xargs -P "$P" -I{} sh -c 'b={}; [ -s out/same_session/$b.row ] || { rm -f out/same_session/$b.csv; ./out/es_drl --instance instances/$b.dat --runs 20 --out out/same_session/$b.row.tmp --runs-csv out/same_session/$b.csv >/dev/null 2>&1 && mv out/same_session/$b.row.tmp out/same_session/$b.row; }'
