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

---

# Confirmation on new instances (laptop run, 19 Nov 2026)

Run by the project owner with `laptop/run_confirm.sh --tier quick` on an Intel Core i5-10300H (4 cores), WSL2/Ubuntu, gcc 15.2;
22 jobs, 0 failures, 3 h 44 min. The pre-flight check reproduced the reference results exactly (so the bundled kappa=4 reference
was used). Instances are **new** (not in the screening set): 6 at n=400 (two per aperture) and 5 at n~200; 10 paired runs each;
kappa in {12, 16}; each run stopped at the kappa=4 run's evaluation count (mean ratio 1.0004). Raw data:
`RM-Report/data/ksweep_confirm_laptop/`; full output `RM-Report/data/data_ksweep_confirm_laptop.txt`.

| kappa | n = 400 (6 inst., 60 runs) | runs better | n ~ 200 (5 inst., 50 runs) | runs better |
|---|---|---|---|---|
| 12 | -0.88 % [-1.15, -0.60] | 53/60 | -0.40 % [-0.87, +0.07] | 33/50 |
| 16 | -1.11 % [-1.42, -0.80] | 53/60 | -0.68 % [-1.14, -0.24] | 35/50 |

* **n = 400 confirmed out of sample.** All 6 new instances improve for both kappa (per instance -0.51 % to -1.56 %), in all three apertures.
  Wilcoxon over the six instance means: p = 0.031 (the smallest possible with 6 instances). After Holm correction across the 22 cells, 3 of 6
  n=400 instances are significant for kappa=16 and 2-3 for kappa=12 (corrected p = 0.043-0.066).
* Pooled with the screening instances (9 instances at n=400, 84 paired runs): **kappa=12 -0.95 % [-1.18, -0.72]** (75/84 runs better),
  **kappa=16 -1.03 % [-1.29, -0.78]** (74/84). Head to head, 16 vs 12 at n=400: 16 is better by 0.24 % [-0.02, +0.48], i.e. borderline; the
  optimum lies on a plateau between 12 and 16 (at the screening, 12 looked better; here 16 does).
* **Total change vs the published ES-TRMP** (these 10-run means against the published 20-run means; approximate): n=400 -3.10 % (kappa=12) and
  -3.33 % (kappa=16), against -2.18 % for block kappa=4 on the same six instances. n~200: -2.26 % / -2.54 % against -1.98 % for kappa=4.
* **n ~ 200: smaller and less certain.** kappa=16 -0.68 % (interval excludes 0; 35/50 runs better), kappa=12 -0.40 % (interval includes 0);
  per instance the sign varies (kappa=12 is +0.30 % worse on one). Consistent with the screening (about -0.3 to -0.4 %).

**Conclusion.** A larger block destruction size, kappa in 12-16, gives about **1 % more improvement at n = 400** on top of kappa=4
(confirmed on 6 unseen instances), taking the total gain over the published ES-TRMP from about 2.3 % to about 3.1-3.3 %; at n ~ 200 the extra gain
is about 0.4-0.7 % and not firmly established.

**Limits.** 10 runs per instance; no decision threshold was pre-registered for this confirmation (the out-of-sample design is the safeguard); comparison with the published
ES-TRMP uses 10-run means; kappa=16 is the edge of the grid, so kappa=20-24 is untested and the true optimum may be higher; shuffle unchanged; the paper's 4,000-iteration protocol
is not used for kappa != 4 (the comparison is at equal evaluations, which is 1,000-1,400 iterations for kappa=12-16).

**Next steps.** (1) kappa in {20, 24, 32} at n=400 to find the end of the plateau; (2) run the best kappa on all 15 n=400 instances with 20 runs
(about 20 CPU-hours); (3) test a size-dependent rule (kappa ~ 3-4 % of n).

---

# Where does the gain end? kappa = 20, 24, 32 (laptop run, 19-20 Nov 2026)

`laptop/run_confirm.sh --tier plateau`: the same six n=400 instances and seeds as the kappa=12/16 confirmation, kappa in {20, 24, 32}, 10 paired runs,
equal evaluations (mean ratio 1.0006). Same i5-10300H / WSL2 laptop; 18 jobs, 0 failures, 5 h 01 min; pre-flight reproduced the reference exactly.
Raw data `RM-Report/data/ksweep_plateau_laptop/`, merged analysis `RM-Report/data/data_ksweep_plateau_merged.txt`, figure `RM-Report/figures/fig10_kappa_profile.png`.

## kappa profile at n = 400 (6 instances common to all kappas, 60 paired runs each; vs block kappa=4)

| kappa | change vs kappa=4 (95 % CI) | runs better | iterations at equal evaluations | vs kappa=16 |
|---|---|---|---|---|
| 12 | -0.88 % [-1.16, -0.59] | 53/60 | ~1,370 | +0.24 % [-0.01, +0.49] |
| **16** | **-1.11 % [-1.42, -0.80]** | 53/60 | ~1,040 | -- |
| **20** | **-1.07 % [-1.37, -0.77]** | 53/60 | ~835 | +0.05 % [-0.35, +0.42] |
| 24 | -0.78 % [-1.13, -0.39] | 46/60 | ~700 | +0.34 % [-0.00, +0.69] |
| 32 | -0.27 % [-0.75, +0.21] | 35/60 | ~530 | **+0.85 % [+0.47, +1.29]** (better in only 10/60 runs) |

* **Plateau at kappa = 12-20, peak at 16-20.** kappa=16 and kappa=20 are indistinguishable (0.05 %). Beyond 20 the gain declines: kappa=24 is slightly worse than 16
  (borderline), and **kappa=32 is clearly worse than 16** (+0.85 %, interval excludes 0) and no longer significantly better than kappa=4 (interval includes 0).
  The profile is an inverted U: too-small destruction does too little per move, too-large destruction does too few moves per evaluation (only ~530 iterations at kappa=32) and its
  contiguous block becomes as disruptive as the shuffle (delta = 40 at n >= 200).
* **Consistent across the three apertures** (kappa=20: -0.91 %, -1.25 %, -1.04 % for 2pi/3, pi/2, pi/3) and on every instance kappa=20 is better than kappa=4 in 8-10 of 10 runs (except
  -0.70 % / 8 of 10 on one instance, all negative).
* **Total change vs the published ES-TRMP at n=400** (10-run means vs published 20-run means; approximate): kappa=16 -3.33 %, kappa=20 -3.29 %, kappa=24 -3.01 %,
  kappa=32 -2.50 %, against -2.18 % for block kappa=4 on the same six instances.
* A reasonable setting at n=400 is **kappa = 16-20 (about 4-5 % of n)**.

## Limits
* 10 runs and 6 instances; per-instance tests cannot be significant after Holm correction (smallest p = 0.002 x 40 cells = 0.08), the conclusion rests on the pooled intervals and the consistent direction.
* The shape at **n ~ 200 is not established**: only kappa=12 (-0.40 %) and 16 (-0.68 %) have been measured on 5 instances; a 2-run smoke test on n=198 hinted that kappa=24/32 are worse there
  (+1.0 %, +1.5 %) but is far too small to rely on. Whether the optimum scales with n (about 4-5 % of n) or is roughly constant (about 16) is open.
* Comparison with the published ES-TRMP is approximate (run counts differ); the shuffle is unchanged; the paper's 4,000-iteration protocol is not used for kappa != 4.

## Next steps
1. kappa in {20, 24, 32} (and 8, 10) at n ~ 200 (cheap: about 40 minutes) to see whether the optimum scales with n.
2. Final confirmation of kappa=16 (and 20) on all 15 n=400 instances (and the 11 instances with n of 198-200) with 20 runs: about 22 CPU-hours per kappa.

---

# Does the best kappa scale with n? n ~ 200, kappa = 8, 10, 20, 24, 32 (run in the project container, 20 Nov 2026)

`laptop/run_confirm.sh --tier n200 --jobs 4` on the project container (4 cores, gcc 13.3): 25 jobs, 0 failures, 31 minutes; pre-flight reproduced the reference exactly.
The same five n ~ 200 instances and seeds as the kappa=12/16 run (so all seven kappa values pair run by run), 10 runs, equal evaluations (mean ratio 1.0005).
Raw data `RM-Report/data/ksweep_n200_container/`, merged analysis `RM-Report/data/data_ksweep_n200_profile.txt`, figure `RM-Report/figures/fig10_kappa_profile.png`.

## kappa profile at n ~ 200 (5 instances, 50 paired runs each; vs block kappa=4)

| kappa | change vs kappa=4 (95 % CI) | runs better | iterations | vs kappa=16 |
|---|---|---|---|---|
| 8  | -0.31 % [-0.64, +0.02] | 32/50 | ~2,050 | +0.36 % [-0.08, +0.82] |
| 10 | -0.41 % [-0.92, +0.09] | 31/50 | ~1,655 | +0.26 % [-0.31, +0.89] |
| 12 | -0.40 % [-0.87, +0.06] | 33/50 | ~1,390 | +0.28 % [-0.25, +0.79] |
| **16** | **-0.68 % [-1.15, -0.23]** | 35/50 | ~1,055 | -- |
| 20 | -0.42 % [-0.96, +0.13] | 30/50 | ~855 | +0.26 % [-0.32, +0.84] |
| 24 | +0.03 % [-0.57, +0.79] | 26/50 | ~720 | **+0.71 % [+0.20, +1.25]** |
| 32 | +0.62 % [-0.00, +1.24] | 16/50 | ~555 | **+1.30 % [+0.72, +1.84]** (better in only 9/50 runs) |

## Reading
* **Same shape as n = 400, smaller and shifted:** a shallow minimum at **kappa = 16** (-0.68 %, the only interval that excludes zero among 8-20), a flat plateau from kappa = 8 to 20 whose members are not
  distinguishable from each other, and loss of the benefit beyond: **kappa = 24 is no better than kappa = 4** and clearly worse than 16; kappa = 32 is worse than kappa = 4.
  At n = 400 the useful range extends further (kappa = 24 still -0.78 %, kappa = 32 -0.27 %).
* **kappa ~ 16 is the best setting at both sizes** (n = 400: -1.11 %; n ~ 200: -0.68 %). A proportional rule (4-5 % of n, i.e. 8-10 at n = 200) is *not* supported: kappa = 8 and 10 are nominally worse
  than 16 at n ~ 200 (+0.36 % and +0.26 %, not significant). A constant kappa of about 16 fits both sizes better, though the n ~ 200 differences among 8-20 are within noise.
* Instance dependent: on one n = 200 instance (`s06i02`) kappa >= 20 is worse than kappa = 4 (up to +1.36 %), on another (`s04i03`) kappa = 20 is the best (-1.02 %).
* **Total change vs the published ES-TRMP** (10-run means vs published 20-run means; approximate): kappa = 16: n ~ 200 **-2.54 %** (kappa=4: -1.98 % on these five instances), n = 400 **-3.33 %** (kappa=4: -2.18 %).
* Practical recommendation: **block destroy with kappa = 16 for instances with n >= 200** (n = 400: kappa = 16-20 equivalent).

## Limits
10 runs and 5 instances at n ~ 200; no per-instance cell is significant after Holm correction (smallest p = 0.002 x 47 cells); the plateau 8-20 at n ~ 200 cannot be resolved further with this sample; kappa for n < 198 not tested
(the block gain itself is small below n ~ 100); shuffle unchanged; equal-evaluation comparison, not the paper's 4,000-iteration protocol.

## Next step
Final confirmation of kappa = 16 against kappa = 4 and the published ES-TRMP on all instances with n >= 198 (26 instances, 20 runs; about 22 CPU-hours), ideally under a pre-stated decision rule.
