#!/usr/bin/env bash
# =====================================================================================================
# Confirmation run for the block-destroy kappa sweep (does a larger destruction size kappa beat kappa=4?)
#
#   bash laptop/run_confirm.sh --tier smoke      # 3-5 minute test that everything works  (do this first)
#   bash laptop/run_confirm.sh --tier quick      # default: 11 NEW instances, 10 runs, kappa 12 and 16
#   bash laptop/run_confirm.sh --tier full       # all 26 instances with n>=198, 20 runs (very long)
#
# What it does: compiles the C driver, checks that your machine reproduces the reference results, estimates the
# run time, runs every (instance, kappa) job in parallel, and writes EVERYTHING to  logs/confirm_<time>_<host>/
# and a single archive  logs/confirm_<time>_<host>.tar.gz   <-- upload this file.
# Each run gets exactly the same number of candidate evaluations as the kappa=4 run of the same index (fair
# comparison). The script is resumable: stop with Ctrl+C and re-run with  --rundir <same folder>.
# =====================================================================================================
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/.." && pwd)"; cd "$ROOT" || exit 1

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; cat <<'EOT'

Options:
  --tier smoke|quick|full   which set of instances (default quick)
  --kappas "12 16"          destruction sizes to test (default "12 16")
  --runs N                  runs per instance, 1..20 (default: smoke 2, quick 10, full 20)
  --jobs N                  parallel jobs (default: number of cores minus one)
  --rundir DIR              reuse/resume an existing log folder
  --yes                     do not ask for confirmation after the time estimate
  --dry-run                 compile, run the pre-flight check, print the plan and time estimate, then stop
EOT
}

TIER=quick; KAPPAS="12 16"; RUNS=""; JOBS=""; RUNDIR=""; YES=0; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --tier) TIER=$2; shift 2;;  --kappas) KAPPAS=$2; shift 2;;  --runs) RUNS=$2; shift 2;;
    --jobs) JOBS=$2; shift 2;;  --rundir) RUNDIR=$2; shift 2;;  --yes|-y) YES=1; shift;;  --dry-run) DRY=1; shift;;
    -h|--help) usage; exit 0;;  *) echo "unknown option: $1"; usage; exit 2;;
  esac
done

# ---------------------------------------------------------------- instance sets
ALL26="covers_dirn400m240r150s03i00 covers_dirn400m240r150s03i01 covers_dirn400m240r150s03i02 covers_dirn400m240r150s03i03 covers_dirn400m240r150s03i04 covers_dirn400m240r150s04i00 covers_dirn400m240r150s04i01 covers_dirn400m240r150s04i02 covers_dirn400m240r150s04i03 covers_dirn400m240r150s04i04 covers_dirn400m240r150s06i00 covers_dirn400m240r150s06i01 covers_dirn400m240r150s06i02 covers_dirn400m240r150s06i03 covers_dirn400m240r150s06i04 covers_dirn200m120r150s03i03 covers_dirn200m120r150s04i01 covers_dirn200m120r150s04i02 covers_dirn200m120r150s04i03 covers_dirn200m120r150s04i04 covers_dirn200m120r150s06i01 covers_dirn200m120r150s06i02 covers_dirn200m120r150s06i03 covers_dirn200m120r150s06i04 covers_dirn200m120r150s03i02 covers_dirn200m120r150s06i00"
# quick = instances NOT used in the earlier screening (out-of-sample), two per aperture at n=400, five at n~200
QUICK="covers_dirn400m240r150s03i01 covers_dirn400m240r150s03i02 covers_dirn400m240r150s04i01 covers_dirn400m240r150s04i02 covers_dirn400m240r150s06i00 covers_dirn400m240r150s06i02 covers_dirn200m120r150s03i02 covers_dirn200m120r150s04i02 covers_dirn200m120r150s04i03 covers_dirn200m120r150s06i02 covers_dirn200m120r150s06i03"
SMOKE="covers_dirn200m120r150s06i00 covers_dirn100m060r150s03i01"
case "$TIER" in
  smoke) INSTANCES=$SMOKE; DEF_RUNS=2;;
  quick) INSTANCES=$QUICK; DEF_RUNS=10;;
  full)  INSTANCES=$ALL26; DEF_RUNS=20;;
  *) echo "unknown tier: $TIER"; exit 2;;
esac
[ -z "$RUNS" ] && RUNS=$DEF_RUNS
case "$RUNS" in ''|*[!0-9]*) echo "--runs must be an integer"; exit 2;; esac
[ "$RUNS" -ge 1 ] && [ "$RUNS" -le 20 ] || { echo "--runs must be between 1 and 20"; exit 2; }

# ---------------------------------------------------------------- machine info, compiler
cores=$( (nproc || sysctl -n hw.ncpu || echo "${NUMBER_OF_PROCESSORS:-2}") 2>/dev/null | head -1 )
case "$cores" in ''|*[!0-9]*) cores=2;; esac
if [ -z "$JOBS" ]; then JOBS=$(( cores > 2 ? cores - 1 : cores )); fi
CCBIN=""; for c in "${CC:-}" gcc cc clang; do [ -n "$c" ] && command -v "$c" >/dev/null 2>&1 && { CCBIN=$c; break; }; done
[ -n "$CCBIN" ] || { echo "ERROR: no C compiler found (install gcc or clang; on Windows use WSL: wsl --install, then 'sudo apt install build-essential')."; exit 1; }
for f in src/es_drl.c src/trmp_core.c src/destroy_repair.c reference/full_block_k4 instances init_state.dat; do
  [ -e "$f" ] || { echo "ERROR: missing $f -- run this script from a full checkout of the repository."; exit 1; }
done

host=$(hostname 2>/dev/null | tr -c 'A-Za-z0-9\n' '_')
[ -z "$RUNDIR" ] && RUNDIR="logs/confirm_$(date +%Y%m%d-%H%M%S)_${host:-host}"
mkdir -p "$RUNDIR/results" "$RUNDIR/ref_k4" bin || exit 1
RUNDIR=${RUNDIR%/}
cpu=$( (lscpu | sed -n 's/^Model name:[ \t]*//p' | head -1; sysctl -n machdep.cpu.brand_string; grep -m1 'model name' /proc/cpuinfo | sed 's/.*: //') 2>/dev/null | head -1 )
{
  echo "started:     $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "host:        ${host:-?}"
  echo "system:      $(uname -a 2>/dev/null)"
  echo "cpu:         ${cpu:-unknown}   cores=$cores   parallel_jobs=$JOBS"
  echo "compiler:    $CCBIN  $($CCBIN --version 2>&1 | head -1)"
  echo "git commit:  $(git rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "tier=$TIER  runs=$RUNS  kappas=\"$KAPPAS\""
  echo "instances:   $INSTANCES"
} > "$RUNDIR/run_info.txt"
echo "== Log folder: $RUNDIR"
trap 'echo; echo "Interrupted. Resume with:  bash laptop/run_confirm.sh --tier $TIER --kappas \"$KAPPAS\" --runs $RUNS --rundir $RUNDIR --yes"; exit 130' INT TERM

echo "== Compiling ($CCBIN -O2) ..."
BIN="bin/es_drl_laptop"
$CCBIN -O2 -o "$BIN" src/es_drl.c src/trmp_core.c src/destroy_repair.c -lm > "$RUNDIR/compile.log" 2>&1 \
  || { echo "ERROR: compilation failed, see $RUNDIR/compile.log"; tail -5 "$RUNDIR/compile.log"; exit 1; }

# ---------------------------------------------------------------- pre-flight: does this machine reproduce the reference?
# One real kappa=4 run (n=198, ~30-60 s). If its result equals the bundled reference to 6 decimals, the random-number
# generator is compatible and the bundled kappa=4 results are used as the paired reference; otherwise kappa=4 is re-run here.
CAL=covers_dirn200m120r150s06i00
echo "== Pre-flight check (one kappa=4 run on $CAL, ~1 min) ..."
rm -f "$RUNDIR/preflight.csv" "$RUNDIR/preflight.row"
"$BIN" --instance "instances/$CAL.dat" --policy block --kappa 4 --runs 1 --runs-csv "$RUNDIR/preflight.csv" \
       --out "$RUNDIR/preflight.row" > "$RUNDIR/preflight.log" 2>&1
REFB="reference/full_block_k4"
match=$(awk -F, 'NR==FNR{ if(FNR>1) ref[$3]=$4; next } FNR>1{ n++; if (sprintf("%.6f",$4)!=sprintf("%.6f",ref[$3])) bad++ } END{ print (n>0 && bad==0)?"yes":"no" }' \
        "$REFB/$CAL.csv" "$RUNDIR/preflight.csv" 2>/dev/null)
mycpu=$(awk -F, 'FNR==2{print $13}' "$RUNDIR/preflight.csv" 2>/dev/null); refcpu=$(awk -F, 'FNR==2{print $13}' "$REFB/$CAL.csv")
slow=$(awk -v a="${mycpu:-0}" -v b="$refcpu" 'BEGIN{ if (a>0 && b>0) printf "%.2f", a/b; else print "1.00" }')
[ "${FORCE_LOCAL_REF:-0}" = 1 ] && match=no   # testing aid: exercise the local-reference path
if [ "$match" = "yes" ]; then
  MODE=bundled; REF="$REFB"
  echo "   OK: results identical to the bundled reference -> using the bundled kappa=4 reference."
else
  MODE=local; REF="$RUNDIR/ref_k4"
  echo "   NOTE: results differ from the bundled reference (different random-number generator on this system)."
  echo "         kappa=4 will be re-run here as the paired reference (adds about 50% to the run time)."
fi
{ echo "preflight_matches_reference=$match  reference_mode=$MODE  speed_factor_vs_reference=$slow  (calibration run cpu_s=${mycpu:-?}, reference cpu_s=$refcpu)"; } >> "$RUNDIR/run_info.txt"

# ---------------------------------------------------------------- job lists and time estimate
: > "$RUNDIR/jobs_ref.txt"; : > "$RUNDIR/jobs_main.txt"
est=0
for i in $INSTANCES; do
  one=$(awk -F, -v R="$RUNS" 'NR>1 && $3<R {s+=$13} END{print s+0}' "$REFB/$i.csv")
  [ "$MODE" = local ] && { echo "$i 4 $RUNS - $RUNDIR/ref_k4" >> "$RUNDIR/jobs_ref.txt"; est=$(awk -v e="$est" -v o="$one" 'BEGIN{print e+o}'); }
  for k in $KAPPAS; do
    if [ "$MODE" = local ]; then bud="$RUNDIR/ref_k4/$i.k4.csv"; else bud="$REFB/$i.csv"; fi
    echo "$i $k $RUNS $bud $RUNDIR/results" >> "$RUNDIR/jobs_main.txt"
    est=$(awk -v e="$est" -v o="$one" 'BEGIN{print e+o}')
  done
done
# longest jobs first (n=400 before n~200) for better parallel utilisation
for f in jobs_ref jobs_main; do sort -r "$RUNDIR/$f.txt" -o "$RUNDIR/$f.txt"; done
njobs=$(( $(wc -l < "$RUNDIR/jobs_main.txt") + $(wc -l < "$RUNDIR/jobs_ref.txt") ))
lo_min=$(awk -v e="$est" -v s="$slow" -v j="$JOBS" 'BEGIN{printf "%d", e*s/60/j}')   # unloaded speed; parallel jobs run slower (memory/thermal)
hi_min=$(awk -v m="$lo_min" 'BEGIN{printf "%d", m*1.6}')
fmt() { awk -v m="$1" 'BEGIN{ if (m<90) printf "%d min", m; else printf "%.1f h", m/60 }'; }
echo "== Plan: tier=$TIER, $(echo $INSTANCES | wc -w | tr -d ' ') instances x kappa [$KAPPAS] x $RUNS runs = $njobs jobs, $JOBS in parallel"
echo "   Estimated wall-clock time on this machine: $(fmt $lo_min) to $(fmt $hi_min)  (rough guide; depends on cooling and other load)."
echo "   Keep the laptop plugged in and prevent sleep. Progress: tail -f $RUNDIR/progress.log"
echo "plan: $njobs jobs, estimated wall $(fmt $lo_min) to $(fmt $hi_min)" >> "$RUNDIR/run_info.txt"
[ "$DRY" -eq 1 ] && { echo "(dry run: stopping here; nothing was run. Log folder $RUNDIR can be deleted.)"; exit 0; }
if [ "$YES" -ne 1 ] && [ -t 0 ]; then
  printf "   Continue? [y/N] "; read -r ans; case "$ans" in y|Y|yes|YES) ;; *) echo "Aborted."; exit 0;; esac
fi

# ---------------------------------------------------------------- run
run_jobs() {  # $1 = job list file
  [ -s "$1" ] || return 0
  xargs -P "$JOBS" -L 1 bash laptop/job.sh "$RUNDIR" "$BIN" < "$1"
}
t0=$(date +%s)
if [ "$MODE" = local ]; then echo "== Phase 1/2: kappa=4 reference runs ..."; run_jobs "$RUNDIR/jobs_ref.txt"; echo "== Phase 2/2: kappa sweep ..."; else echo "== Running ..."; fi
run_jobs "$RUNDIR/jobs_main.txt"
echo "== Finished in $(( ( $(date +%s) - t0 ) / 60 )) minutes."

# ---------------------------------------------------------------- summary + archive
bash laptop/summarize.sh "$RUNDIR" "$REF" "$MODE"
failed=$(grep -c "exit=[1-9]" "$RUNDIR/progress.log" 2>/dev/null); ndone=$(ls "$RUNDIR"/results/*.row 2>/dev/null | wc -l | tr -d ' ')
echo "finished:    $(date '+%Y-%m-%d %H:%M:%S %z')   cells_done=$ndone   failed_jobs=${failed:-0}" >> "$RUNDIR/run_info.txt"
tar czf "$RUNDIR.tar.gz" -C "$(dirname "$RUNDIR")" "$(basename "$RUNDIR")" 2>/dev/null \
  && echo && echo "=====> UPLOAD THIS FILE:  $ROOT/$RUNDIR.tar.gz   ($(du -h "$RUNDIR.tar.gz" | cut -f1))" \
  || echo "Could not create the archive; upload the folder $RUNDIR instead."
[ "${failed:-0}" -gt 0 ] && echo "WARNING: $failed job(s) failed; see $RUNDIR/progress.log and results/*.log. Re-run with --rundir $RUNDIR to retry them."
exit 0
