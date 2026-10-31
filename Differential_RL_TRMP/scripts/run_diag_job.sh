#!/bin/bash
# usage: run_diag_job.sh <instance> <kappa> <nruns>   (run from project root)
i=$1; k=$2; n=$3
./out/diag_bin 1 instances/$i.dat out/p1/$i.k$k.res $k $n out/p1/$i.k$k.log > /dev/null
