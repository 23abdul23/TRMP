#!/bin/bash
# Equivalence of the refactored driver (baseline mode) with the ORIGINAL es_pre_sfFIN.c.
# golden/*.txt = rows produced by the untouched baseline binary (20 runs). Compared columns:
# instance, n, best, mean, SD, avg best-iteration, SD best-iteration (time columns excluded).
# usage: tests/test_equiv.sh [golden files...]   (run from project root; default = all golden files)
cd "$(dirname "$0")/.." || exit 1
make -s out/es_drl || exit 1
files=("$@"); [ ${#files[@]} -eq 0 ] && files=(tests/golden/*.txt)
fail=0
for g in "${files[@]}"; do
  inst=$(cut -f1 "$g" | head -1)
  new=$(./out/es_drl --instance "$inst" 2>/dev/null | tail -1)
  a=$(cut -f1-5,8,9 "$g" | head -1); b=$(echo "$new" | cut -f1-5,8,9)
  if [ "$a" == "$b" ]; then echo "PASS $inst"; else echo "FAIL $inst"; echo "  golden: $a"; echo "  driver: $b"; fail=1; fi
done
exit $fail
