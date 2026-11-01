#!/bin/bash
# Full-protocol run of `--policy block` (kappa=4, 4000 iterations, 20 runs, shuffle unchanged) on all 60 instances.
# Order: ascending n so quick instances finish first. Skips instances already done (resumable).
# usage: scripts/full_block.sh [parallel]      (from project root)
P=${1:-4}
cd "$(dirname "$0")/.." || exit 1
make -s out/es_drl || exit 1
mkdir -p out/full_block
sort -k2 -n out/sizes.txt | awk '{print $1}' |
 xargs -P "$P" -I{} sh -c 'b={}; [ -s out/full_block/$b.row ] || { rm -f out/full_block/$b.csv; ./out/es_drl --instance instances/$b.dat --policy block --runs 20 --out out/full_block/$b.row.tmp --runs-csv out/full_block/$b.csv >/dev/null 2>&1 && mv out/full_block/$b.row.tmp out/full_block/$b.row; }'
