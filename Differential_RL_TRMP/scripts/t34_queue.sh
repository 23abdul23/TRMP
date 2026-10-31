#!/bin/bash
# Sequential (1 core, nice) queue for Tests 3+4. Resumable: skips jobs whose .done marker exists.
# usage: t34_queue.sh   (any cwd)
cd "$(dirname "$0")/.." || exit 1
mkdir -p out/t34
job() {  # instance runs policy
  local inst=$1 runs=$2 pol=$3 d=out/t34/$1
  mkdir -p "$d"
  [ -e "$d/$pol.done" ] && return
  rm -f "$d/$pol.csv" "$d/$pol.runs" "$d/$pol.row"
  nice -n 5 ./out/es_drl --instance instances/$inst.dat --runs $runs --policy $pol \
      --mut-log "$d/$pol.csv" --runs-csv "$d/$pol.runs" --out "$d/$pol.row" > /dev/null 2> "$d/$pol.err" && touch "$d/$pol.done"
}
for inst in covers_dirn100m060r150s06i03 covers_dirn200m120r150s06i00; do
  for pol in uniform block uniform-sorted block-rord wrap mix:0.5 mix:0.25 mix:0.75; do job $inst 10 $pol; done
done
inst=covers_dirn400m240r150s04i00
for pol in uniform block mix:0.5 mix:0.25 mix:0.75; do job $inst 5 $pol; done
echo ALL_DONE > out/t34/queue.done
