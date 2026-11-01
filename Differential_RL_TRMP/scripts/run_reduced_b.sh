#!/bin/bash
# Reduced protocol for Option B (run from anywhere; script cds to the project root).
#  base100|base198|base400 : baseline Random-DR control, also the per-run-index budget file
#  rl <tag> <instance> <runs> <algo> : rl-online with --rl-algo diff|disc on the same instance/runs
cd "$(dirname "$0")/.." || exit 1
make -s out/es_drl || exit 1
mkdir -p out/red
D=out/red
I100=instances/covers_dirn100m060r150s06i03.dat
I198=instances/covers_dirn200m120r150s06i00.dat
I400=instances/covers_dirn400m240r150s06i00.dat
case $1 in
 base100) nice -n 5 ./out/es_drl --instance $I100 --runs 10 --runs-csv $D/base100.csv > /dev/null ;;
 base198) nice -n 5 ./out/es_drl --instance $I198 --runs 10 --runs-csv $D/base198.csv > /dev/null ;;
 base400) nice -n 5 ./out/es_drl --instance $I400 --runs 3  --runs-csv $D/base400.csv > /dev/null ;;
 rl)
   tag=$2; inst=$3; n=$4; algo=$5
   nice -n 5 ./out/es_drl --instance "$inst" --runs "$n" --mode rl-online --rl-algo "$algo" --budget-csv $D/base$tag.csv \
        --runs-csv $D/$algo$tag.csv --rl-dump $D/$algo$tag --out $D/$algo$tag.row > /dev/null ;;
 ctl) # ctl <tag> <instance> <runs> <fixk2|rand>   equal-evaluation controls run through the same rl-online loop
   tag=$2; inst=$3; n=$4; name=$5
   case $name in
     fixk2) extra="--kappas 2 --eps0 0 --eps-min 0" ;;   # only one action: fixed kappa=2
     rand)  extra="--eps0 1 --eps-min 1" ;;              # uniform-random kappa in {2,4,6,8}, no exploitation
   esac
   nice -n 5 ./out/es_drl --instance "$inst" --runs "$n" --mode rl-online --budget-csv $D/base$tag.csv $extra \
        --runs-csv $D/$name$tag.csv --out $D/$name$tag.row > /dev/null ;;
esac
