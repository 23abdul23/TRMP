#!/bin/bash
# Phase 0: run the ORIGINAL baseline binary on instances with n in [lo,hi] and store one row per instance.
# usage: scripts/phase0_repro.sh <lo> <hi> <parallel>      (from project root)
lo=$1; hi=$2; P=${3:-2}
mkdir -p out/phase0
make -s out/es_base
for f in instances/*.dat; do n=$(head -1 $f | awk '{print $3}'); [ $n -ge $lo ] && [ $n -le $hi ] && echo $f; done |
  xargs -P $P -I{} sh -c 'b=$(basename {} .dat); [ -s out/phase0/$b.txt ] || ./out/es_base 1 {} out/phase0/$b.txt >/dev/null'
