# Test 1 + 2 pre-registration (written and committed BEFORE any Test 1/2 run)

Question: is `block` destroy a real, general improvement over uniform destroy, and what is its best kappa?
Everything except the destroy selection of the *mutation* is baseline ES-TRMP (eta=100/delta-ladder shuffle remains
uniform, pre-processing identical, srand(run+1) pairing, 4000 iterations). Comparison metric: best-so-far at equal
cumulative candidate-evaluation count (`findcost_d` calls), at 25/50/100 % of the smaller eval total of the two arms in each
run (same method as scripts/analyze_a.py). Negative % = block better.

## Test 1 instances (not used by Option A)
* n~100: dirn100m060r150s03i03 (n=94), dirn100m060r150s04i02 (99), dirn100m060r150s06i04 (96)   — 10 runs
* n~200: dirn200m120r150s03i03 (200), dirn200m120r150s04i01 (200), dirn200m120r150s06i01 (200) — 10 runs
* n=400: dirn400m240r150s03i00, dirn400m240r150s04i00, dirn400m240r150s06i01                     —  5 runs (extend to 10 only if time allows)
Arms: block kappa=4 vs uniform kappa=4.

## Rule: block "generalises" at a size if ALL hold
1. block is better than uniform (mean best at 100 % budget) on >= 2 of the 3 instances of that size;
2. on no instance is block significantly worse (Wilcoxon p < 0.05 with block worse);
3. the mean of the three per-instance % differences at 100 % budget is <= -0.5 %.
"Real and general" overall = rule holds at all three sizes; "size-dependent" = holds at some sizes only; otherwise "not shown".
Pooled test per size: Wilcoxon signed-rank on all per-run paired % differences pooled across the 3 instances (exploratory:
pairs from one instance are not independent) plus the count of instances where block wins. All p-values uncorrected.

## Test 2 (kappa sweep for block)
Instances: dirn200m120r150s06i00 (n=198, 10 runs), dirn400m240r150s04i00 (n=400, 5 runs; same instance as the s04 Test-1 cell).
Arms: block kappa in {2,4,6,8,12}; uniform kappa in {2,4}. Control for gain = uniform kappa=4; "gain survives" if block's best kappa
beats the better of uniform kappa=2/4 at 100 % budget by >= 0.5 % mean. "Best kappa differs from 4" = another block kappa has
a lower mean best at 100 % budget than block kappa=4 by >= 0.3 % with W>L.

## Known limits (stated now)
Few runs at n=400 (5), one aperture per instance, uncorrected p-values, kappa sweep done on one instance per size, only the
mutation uses block (shuffle stays uniform), timing under shared CPU is not a result.
