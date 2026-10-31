# Test 3 + 4 — pre-registered decision rules (written BEFORE any result of these tests was looked at)

Setup common to both tests: baseline ES-TRMP driver (`src/es_drl.c`), kappa=4, eta=100/delta-ladder shuffle (always uniform destroy),
4000 iterations, `srand(run+1)` so arms share pre-processing and the first RNG state; comparison = best-so-far at EQUAL cumulative candidate
evaluations (25/50/100 % of B*, B* = smallest per-run total among the compared arms), paired Wilcoxon signed-rank (two-sided), W/L = runs better/worse.
All p-values exploratory, no multiplicity correction. Instances: n=100 `dirn100m060r150s06i03`, n=198 `dirn200m120r150s06i00` (10 paired runs each —
the directive asked for 5 for Test 3; 10 is a superset and the first 5 are reported too), n=400 `dirn400m240r150s04i00` (5 runs, if CPU allows).

## Test 3 — which property of `block` creates the gain?
Arms: `uniform`, `block` (as implemented: start uniform in [0,n-k], no wrap, reinsertion in ascending position order),
`uniform-sorted` (same removed set and RNG use as uniform, reinsertion in ascending position order),
`block-rord` (contiguous segment as block, reinsertion in RANDOM order), `wrap` (contiguous segment, uniform start with wraparound, cyclic order).
Mechanism claims allowed only under these rules (at 100 % budget, n=198 as primary, n=100 as replication; gap means mean best differs):
* **Contiguity matters** if block-rord is better than uniform-sorted by >= 0.5 % at n=198 with W >= 8/10, AND the same sign at n=100.
* **Reinsertion order matters** if uniform-sorted is better than uniform by >= 0.5 % at n=198 with W >= 8/10 (same sign at n=100), or block is better than block-rord by that margin.
* **Neither** if |uniform-sorted - uniform| and |block-rord - block| are both < 0.3 % at n=198; then the gain is attributed to the removed set / start distribution.
* **Edge effect of block's start distribution** (positions near the ends are under-sampled) matters if wrap differs from block by >= 0.5 % at n=198, W/L >= 8/2.
* Anything between these thresholds is reported as "not resolved".
Descriptive measures (not decision rules): offspring class fractions (identical permutation / equal-cost plateau / worse / better), mean position displacement and
Kendall-tau distance of offspring vs parent, mean cost of the removed set vs uniform draw, mid-run (iterations 1000-3000).

## Test 4 — mixed operators (`--policy mix:p`: per mutation block with prob p else uniform, private xorshift RNG)
Arms: uniform, block, mix:0.25, mix:0.5, mix:0.75.
* A mix **beats block** if at 100 % budget its mean best is lower than block's by >= 0.3 % on BOTH n=100 and n=198, with paired two-sided p < 0.1 on at least n=198.
  (Consequence if true: a learner over operators has something to choose.)
* **Block dominates** if no mix beats block under that rule AND block's mean is <= every mix's mean at n=198 (pure block is the best fixed arm).
* Otherwise: "no resolved difference" (the mixes and block are statistically exchangeable at this sample size).
* n=400 (5 runs) is reported as confirmation only; it cannot overturn the n=100/198 classification (smallest attainable p with 5 pairs is 0.0625).

Per-state evidence (the signal a learner needs), computed from the pure `uniform` and pure `block` logs (and the mixes' per-operator rows):
strict-improvement rate PER 1000 EVALUATIONS by operator within cells of (stagnation u = noimprv/100 in quartile bins [0,.25),[.25,.5),[.5,.75),[.75,1.0] x budget quarter),
using cells with >= 30 strict improvements in each compared arm. A **state-dependent preference exists** only if, among valid cells, the sign of
(block - uniform) rate differs between at least two cells AND each of those cells has a bootstrap (over runs) 90 % interval excluding 0. Otherwise: block (or uniform) uniformly preferred / unresolved.
