# Block-destroy kappa sweep (equal evaluations, 7 instances with n >= 198)

**Question.** The contiguous (`block`) destroy with kappa=4 improves ES-TRMP by about 2% at n >= 198. Does a different destruction
size kappa do better?

## Design
* Arms: block destroy with kappa in {3, 6, 8, 12, 16}; reference = block kappa=4 from the full-protocol run
  (`out/full_block/*.csv`, runs 0..R-1).
* **Equal evaluations.** A larger kappa costs more per iteration (about kappa/4 times), so equal iterations would favour it by
  construction. New driver option `--budget-csv`: run r of every kappa stops once it has used the same number of candidate
  evaluations as run r of the kappa=4 run (stop checked at the start of each iteration, so a run can overshoot by less than one mutation).
  Validated: block kappa=4 with its own recorded budget reproduces the full-run best values, iteration counts and evaluation counts exactly;
  the default behaviour is unchanged (`tests/test_equiv.sh` passes).
* **Paired by run:** run r uses the same seed, hence the same pre-processed start, in every arm.
* Instances (all three apertures): n~200 -- `dirn200m120r150s06i00` (n=198), `s03i03`, `s04i01`, `s06i01` (n=200), 10 runs each;
  n=400 -- `dirn400m240r150s03i00`, `s04i00`, `s06i01`, 8 runs each. Screening set: a full 26-instance sweep would take about a day.
* Scripts: `scripts/ksweep.sh`, `scripts/analyze_ksweep.py`; figure `RM-Report/figures/fig9_kappa_sweep.png`;
  numbers `RM-Report/data/data_ksweep.txt`; per-run data `RM-Report/data/ksweep_runs/`.

## Results (change vs block kappa=4 at equal evaluations; negative = better; cluster bootstrap over instances then runs)

| kappa | n ~ 200 (4 inst., 40 runs) | runs better | n = 400 (3 inst., 24 runs) | runs better | iterations used (kappa=4: 4000) |
|---|---|---|---|---|---|
| 3  | +0.27 % [-0.22, +0.81] | 18/40 | +0.41 % [-0.01, +0.74] | 7/24 | ~5,265 |
| 6  | -0.39 % [-0.92, +0.11] | 28/40 | -0.55 % [-0.87, -0.22] | 18/24 | ~2,705 |
| 8  | -0.33 % [-0.77, +0.09] | 25/40 | -0.65 % [-1.01, -0.31] | 19/24 | ~2,045 |
| **12** | -0.39 % [-0.81, +0.04] | 21/40 | **-1.11 % [-1.43, -0.72]** | **22/24** | ~1,385 |
| 16 | -0.27 % [-0.62, +0.10] | 26/40 | -0.87 % [-1.27, -0.51] | 21/24 | ~1,050 |

All seven instances: kappa=12 -0.70 % [-1.07, -0.29]; kappa=16 -0.52 % [-0.87, -0.17]; kappa=6 and 8 about -0.46 %; kappa=3 +0.33 % [-0.02, +0.68].

## Reading
* **n = 400: a clear, consistent effect.** Gain grows from kappa=3 (slightly worse) to a minimum around **kappa=12 (-1.11 %)**, then eases at 16.
  The same shape appears on each of the three instances; kappa=12 is better in 22 of 24 paired runs. If it holds, the total gain over the
  published ES-TRMP at n=400 would be roughly **3.2-4.4 %** (kappa=12 means of the 8 runs against the published 20-run means on these three
  instances: -3.22 %, -3.38 %, -4.42 %; approximate, since the run counts differ).
* **n ~ 200: weak.** Every kappa above 4 is about 0.3-0.4 % better but every interval includes 0 and only 21-28 of 40 runs are better;
  the profile is flat between kappa=6 and 16. The exploratory sweep on n=198 (10 runs) already showed kappa 4-12 equivalent.
* **kappa < 4 is not better** (kappa=3 and, earlier, kappa=2 are worse): fewer iterations of larger moves beat more iterations of small ones
  at the same compute, up to a point.
* A tentative hypothesis (not tested): the best kappa grows with n (about 3 % of n: kappa=12 at n=400; at n=200 kappa=6 is as good as any).

## Limits
* Screening set only: 7 instances, 8-10 runs. Single-instance tests are **not significant after Holm correction** across the 35 tests;
  with 8 paired runs the smallest possible Wilcoxon p is 0.0078, times 35 tests = 0.27, so no single cell can be significant by construction.
  The conclusion at n=400 rests on the consistent direction across instances and on the pooled intervals, which are exploratory.
* The cluster bootstrap has only 3 (n=400) and 4 (n~200) clusters, so the intervals are optimistic.
* Coarse grid (3, 6, 8, 12, 16): the optimum between 8 and 16 is not located more finely; the best kappa may depend on the instance.
* Shuffle (eta, delta ladder) is unchanged and still uniform; its frequency per evaluation changes with kappa (fewer iterations -> fewer
  shuffles), which is part of the measured effect.
* Compared with the published ES-TRMP only approximately (8-run means against published 20-run means); a full-protocol
  comparison has not been done for kappa != 4.

## Suggested next step
Confirm kappa=12 (and 16) on all 15 n=400 instances x 20 runs at equal evaluations (about 20 CPU-hours per kappa) and on the nine
n=200 instances (about 2 CPU-hours); then, if it holds, a finer grid (10, 14) and a rule kappa ~ n/30.
