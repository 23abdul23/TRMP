#!/bin/bash
# usage: run_t12.sh <instance> <policy> <kappa> <runs>   (run from Differential_RL_TRMP/)
i=$1; p=$2; k=$3; n=$4; b=out/t12/$i.$p.k$k
[ -s $b.done ] && exit 0
nice -n 5 ./out/es_drl --instance instances/$i.dat --policy $p --kappa $k --runs $n --out $b.res --runs-csv $b.csv --iter-log $b.log > /dev/null 2>&1 && echo ok > $b.done
