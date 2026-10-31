#!/bin/bash
# Option-A R2 policy probe scheduler: runs es_drl jobs from out/a2/jobs.txt, never more than MAXP busy
# simulation processes (diag_bin or es_drl) *belonging to this worktree* (matched by cwd). Run from Differential_RL_TRMP/.
# job line: <instance> <policy> <runs>
MAXP=${MAXP:-2}
here=$(pwd -P)
busy() {
  local n=0 p
  for p in $(pgrep -x diag_bin; pgrep -x es_drl); do
    [ "$(readlink /proc/$p/cwd 2>/dev/null)" == "$here" ] && n=$((n+1))
  done
  echo $n
}
while read -r inst pol runs; do
  [ -z "$inst" ] && continue
  while [ "$(busy)" -ge "$MAXP" ]; do sleep 10; done
  nice -n 5 ./out/es_drl --instance instances/$inst.dat --policy $pol --kappa 4 --runs $runs \
      --iter-log out/a2/$inst.$pol.log --out out/a2/$inst.$pol.res --runs-csv out/a2/$inst.$pol.csv > /dev/null 2>&1 &
  sleep 5
done < out/a2/jobs.txt
wait
