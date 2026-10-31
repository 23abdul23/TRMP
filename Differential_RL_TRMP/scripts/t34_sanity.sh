#!/bin/bash
# quick sanity of the Test-3/4 policies on n=100 (2 runs); run from Differential_RL_TRMP/
cd "$(dirname "$0")/.." || exit 1
I=instances/covers_dirn100m060r150s06i03.dat
mkdir -p out/t34/sanity
for pol in uniform block uniform-sorted block-rord wrap mix:0 mix:1; do
  rm -f out/t34/sanity/$pol.*
  ./out/es_drl --instance $I --runs 2 --policy $pol --mut-log out/t34/sanity/$pol.csv --out out/t34/sanity/$pol.row --runs-csv out/t34/sanity/$pol.runs > /dev/null
  echo "$pol $(cut -f3,4 out/t34/sanity/$pol.row | tr '\t' ' ') rows=$(wc -l < out/t34/sanity/$pol.csv)"
done
echo "nolog block:   $(./out/es_drl --instance $I --runs 2 --policy block | cut -f3,4 | tr '\t' ' ')"
echo "nolog uniform: $(./out/es_drl --instance $I --runs 2 | cut -f3,4 | tr '\t' ' ')"
for pol in uniform uniform-sorted block; do echo "$pol first mutation: $(sed -n 2p out/t34/sanity/$pol.csv)"; done
