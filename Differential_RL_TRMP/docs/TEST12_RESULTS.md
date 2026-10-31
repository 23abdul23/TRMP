# Test 1 + 2 results — does `block` destroy generalise, and what is its best kappa?

Pre-registration: `docs/TEST12_RULES.md` (committed before any run). Full numeric output: `docs/data/test12_analysis.txt`
(reproduce: `scripts/sched_t12.sh` with `scripts/t12_jobs.txt`, then `scripts/analyze_t12.py`).
Method: baseline ES-TRMP, 4000 iterations, eta=100/delta-ladder shuffle **uniform** (only the mutation's destroy selection changes),
srand(run+1) pairing, comparison = best-so-far at equal cumulative candidate evaluations (`findcost_d` calls), 25/50/100 % of the smaller
eval total (Test 1) or of the smallest total among all arms (Test 2). Negative % = better than the control. Wilcoxon signed-rank on paired runs, uncorrected.
With 5 runs the smallest attainable two-sided p is 0.0625, so no n=400 cell can reach p<0.05 by construction.

## Test 1 — block(k=4) vs uniform(k=4), 100 % budget

| size | instance (aperture) | runs | uniform mean | block mean | diff | W/L | p |
|---|---|---|---|---|---|---|---|
| n~100 | s03i03 (n=94) | 10 | 305.33 | 303.94 | −0.46 % | 6/4 | 0.23 |
| n~100 | s04i02 (n=99) | 10 | 371.56 | 371.92 | +0.10 % | 4/6 | 0.77 |
| n~100 | s06i04 (n=96) | 10 | 326.02 | 326.79 | +0.24 % | 4/6 | 0.70 |
| n~200 | s03i03 (n=200) | 10 | 749.85 | 742.02 | −1.04 % | 9/1 | 0.004 |
| n~200 | s04i01 (n=200) | 10 | 1397.51 | 1363.83 | −2.41 % | 10/0 | 0.002 |
| n~200 | s06i01 (n=200) | 10 | 1341.01 | 1308.76 | −2.40 % | 9/1 | 0.004 |
| n=400 | s03i00 | 5 | 2577.62 | 2515.00 | −2.43 % | 5/0 | 0.0625 |
| n=400 | s04i00 | 5 | 3275.62 | 3184.07 | −2.79 % | 5/0 | 0.0625 |
| n=400 | s06i01 | 5 | 3777.56 | 3670.98 | −2.82 % | 5/0 | 0.0625 |

Pre-registered rule ("generalises" = better on >=2 of 3 instances, none significantly worse, mean per-instance gain <= −0.5 %):

| size | block better on | mean per-instance diff | pooled per-run Wilcoxon (exploratory) | rule |
|---|---|---|---|---|
| n~100 | 1 of 3 | −0.04 % | p=0.84 (30 pairs) | **not met** |
| n~200 | 3 of 3 | −1.95 % | p<0.0001 (30 pairs) | **met** |
| n=400 | 3 of 3 | −2.68 % | p=0.0001 (15 pairs) | **met** (every pair favours block, 15/15 W) |

Reading: **size-dependent, not general.** At n~100 block is a wash (the early 25 %-budget advantage on s04i02, −0.63 %, p=0.049, disappears by
the end: +0.10 %). At n~200 and n=400 block wins on every instance and aperture tested with a consistent 1–3 % gain at 100 % budget; at
n=400 every one of the 15 paired runs favours block. The gain also appears already at 25 % of the budget, i.e. it is faster convergence and a
better end point, not a late effect.

## Test 2 — kappa sweep (block k in {2,4,6,8,12}, uniform k in {2,4}), 100 % of B* (smallest eval total among all arms)

n=198 (`dirn200m120r150s06i00`, 10 runs), % vs uniform k=4:

| uniform k=2 | block k=2 | block k=4 | block k=6 | block k=8 | block k=12 |
|---|---|---|---|---|---|
| −0.00 % (5/5) | −0.52 % (8/2, p=0.049) | −1.87 % (10/0, p=0.002) | −1.83 % (10/0) | −1.82 % (9/1) | −1.86 % (10/0) |

n=400 (`dirn400m240r150s04i00`, 5 runs), % vs uniform k=4:

| uniform k=2 | block k=2 | block k=4 | block k=6 | block k=8 | block k=12 |
|---|---|---|---|---|---|
| −0.24 % (3/2) | −1.74 % (5/0) | −2.83 % (5/0) | −3.17 % (5/0) | −3.14 % (5/0) | −3.58 % (5/0) |

Block k vs block k=4 at 100 % budget: n=198 — k=2 +1.38 % (1/9, p=0.004), k=6 +0.04 %, k=8 +0.05 %, k=12 +0.01 % (no difference);
n=400 — k=2 +1.12 % (0/5), k=6 −0.35 % (3/2), k=8 −0.32 % (3/2), k=12 −0.77 % (4/1, p=0.44).

* **Does the gain survive the best uniform kappa?** Yes. Best uniform arm is k=2 at both sizes (k=2 and k=4 are equal at n=198; k=2 is nominally 0.24 % better at n=400).
  block k=4 vs best uniform: −1.87 % (10/0, p=0.002) at n=198 and −2.60 % at n=400 (5/0; p floor 0.0625). The gain is not a kappa artefact.
* **Best block kappa:** at n=198, any k in {4,6,8,12} is equivalent (within 0.05 %); k=2 is clearly worse. At n=400 there is a nominal trend towards
  larger k (k=12 −0.77 % vs k=4, 4 wins/1 loss) which meets the pre-registered ">=0.3 % with W>L" bar for k=6, 8 and 12, but is not
  statistically distinguishable with 5 runs (p>=0.31). So: *"best block k differs from 4" is not shown at n=198 and is suggestive but unproven at n=400.*
  A safe default is k=4–8; k=2 should be avoided.
* Caveat on the comparison: at equal budget B* equals the *smallest* arm total (uniform/block k=2), so block k=12 is judged after ~17 % of its own 4000 iterations
  (k=8 ~26 %, k=6 ~34 %). Higher k is being compared early in its run; its own full-run quality was not part of the equal-evaluation test. At a longer common budget the
  ranking of large k could differ.

## Honest limits

* n=400 cells have 5 runs (extending to 10 was not done, time); p-values there sit at the 0.0625 floor and are exploratory; the evidence is the 15/15 sign consistency and effect size (~2.7 %), not significance.
* One instance per (size, aperture) cell; three instances per size. The kappa sweep uses one instance per size (n=198 s06i00, n=400 s04i00).
* n~100 instances (n=94–99) show no effect; n<=50 not tested (the paper reports SD=0 there, no headroom expected).
* Only the mutation uses block; shuffle remains uniform. Block was only run for the four-kappa grid above, not combined with other policies; no mechanism analysis (why contiguity helps) was done here.
* Uncorrected p-values; the pooled Wilcoxon treats runs on the same instance as independent, which they are not (exploratory only).
* Baseline reproduction of the uniform arm on these particular new instances against the published tables was not checked (the driver is bit-identical to the baseline on n=18/25/198 and logs-compatible with `analyze_p1`); CPU time is not reported (shared machine).

## Verdict

`block` destroy is a **real improvement for n>=~200 (≈1–2.4 % at n~200, ≈2.4–2.8 % at n=400, all apertures tested), not at n~100**. It survives the best uniform kappa. Its kappa is
not critical for k>=4 (k=2 is clearly worse); larger k may help further at n=400 but needs more runs.
