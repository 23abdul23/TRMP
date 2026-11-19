#!/usr/bin/env bash
# Plain-text summary of a run (works with only bash + awk). usage: summarize.sh <rundir> <refdir> <bundled|local>
# Compares each (instance, kappa) cell with the kappa=4 reference run by run (same seeds). Negative % = better than kappa=4.
RUNDIR=$1; REF=$2; MODE=$3
refcsv() { if [ "$MODE" = local ]; then echo "$REF/$1.k4.csv"; else echo "$REF/$1.csv"; fi; }
: > "$RUNDIR/cells.tmp"
for f in "$RUNDIR"/results/*.k*.csv; do
  [ -f "$f" ] || continue
  [ -s "${f%.csv}.row" ] || continue
  b=$(basename "$f" .csv); inst=${b%.k*}; k=${b##*.k}
  r=$(refcsv "$inst"); [ -s "$r" ] || continue
  awk -F, -v inst="$inst" -v k="$k" '
    NR==FNR { if (FNR>1) ref[$3]=$4; if (FNR==2) n=$2; next }
    FNR>1   { if ($3 in ref) { c++; sk+=$4; sr+=ref[$3]; if ($4<ref[$3]-1e-9) w++; else if ($4>ref[$3]+1e-9) l++ } }
    END     { if (c>0) printf "%s %d %d %d %.3f %.3f %.3f %d %d\n", inst, n, k, c, sr/c, sk/c, 100*(sk/c-sr/c)/(sr/c), w, l }' "$r" "$f" >> "$RUNDIR/cells.tmp"
done
{
  echo "Per cell (negative % = better than the kappa=4 reference at equal evaluations; W/L = runs better/worse):"
  printf "%-32s %5s %5s %5s %11s %11s %8s %4s %4s\n" instance n kappa runs ref_mean mean_k pct W L
  sort -k2,2n -k1,1 -k3,3n "$RUNDIR/cells.tmp" | awk '{printf "%-32s %5d %5d %5d %11.3f %11.3f %+8.2f %4d %4d\n",$1,$2,$3,$4,$5,$6,$7,$8,$9}'
  echo
  echo "Pooled (mean of per-instance % change; instances = number of cells pooled):"
  printf "%-10s %5s %9s %9s %12s\n" size kappa instances mean_pct runs_better
  awk '{ g=($2<=100)?"n<=100":(($2<=200)?"n~200":"n=400"); key=g" "$3; s[key]+=$7; c[key]++; w[key]+=$8; t[key]+=$4 }
       END { for (key in s) { split(key,a," "); printf "%-10s %5d %9d %+9.2f %5d/%-5d\n", a[1], a[2], c[key], s[key]/c[key], w[key], t[key] } }' "$RUNDIR/cells.tmp" | sort -k1,1 -k2,2n
} > "$RUNDIR/summary.txt"
rm -f "$RUNDIR/cells.tmp"
cat "$RUNDIR/summary.txt"
