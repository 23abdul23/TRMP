#!/usr/bin/env bash
# One job = one (instance, kappa) cell: block destroy, equal-evaluation stop. Called by run_confirm.sh via xargs.
# usage: job.sh <rundir> <bin> <instance> <kappa> <runs> <budget_csv|-> <outdir>
rundir=$1; bin=$2; inst=$3; k=$4; runs=$5; budget=$6; outdir=$7
out="$outdir/$inst.k$k"
ts() { date '+%Y-%m-%d %H:%M:%S'; }
if [ -s "$out.row" ]; then echo "$(ts) SKIP  $inst k=$k (already finished)" >> "$rundir/progress.log"; exit 0; fi
rm -f "$out.csv" "$out.log" "$out.row.tmp"
extra=""; [ "$budget" != "-" ] && extra="--budget-csv $budget"
start=$(date +%s)
echo "$(ts) START $inst k=$k runs=$runs" >> "$rundir/progress.log"
"$bin" --instance "instances/$inst.dat" --policy block --kappa "$k" --runs "$runs" $extra \
       --out "$out.row.tmp" --runs-csv "$out.csv" > "$out.log" 2>&1
rc=$?
[ $rc -eq 0 ] && mv "$out.row.tmp" "$out.row"
echo "$(ts) END   $inst k=$k exit=$rc seconds=$(( $(date +%s) - start ))" >> "$rundir/progress.log"
exit 0
