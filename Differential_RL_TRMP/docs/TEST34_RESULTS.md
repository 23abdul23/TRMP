# Tests 3 + 4 — why does `block` work, and do mixed operators help?

Rules were fixed before any result was looked at: `docs/TEST34_RULES.md`. Everything here is **exploratory**: one instance per size, 10 paired runs
(n=100, n=198) or 5 (n=400), two-sided Wilcoxon signed-rank, **no multiplicity correction**, kappa=4 only. Comparison = best-so-far at equal cumulative
candidate evaluations (B* = smallest per-run total over all arms; evaluations per mutation are identical across arms: 394 at n=100, 786 at n=198).
Pairing = same `srand(run+1)`, i.e. identical pre-processing; arms then diverge, so pairing only removes start-point variance.
Code: `src/destroy_repair.c` (new policies + removed-set diagnostics), `src/es_drl.c` (`--policy`, `mix:p`, `--mut-log`),
`scripts/t34_queue.sh`, `scripts/analyze_t34.py`, `scripts/analyze_t34_gain.py`, `scripts/t34_sanity.sh`.
Sanity checks passed: `uniform` is bit-identical to the baseline (`tests/test_equiv.sh` n018, n025 PASS); `mix:0` ≡ `uniform` and `mix:1` ≡ `block` exactly
(same best/mean on 2 runs); logging does not change any result; `uniform-sorted` removes the same groups as `uniform` on the first mutation
(same offspring cost and removed-set cost). The `block` row reproduces Option A's numbers (−0.97 % n=100, −1.79 % n=198).

## 0. What `block` does, exactly (src/destroy_repair.c, `select_positions`)
`s0 = (int)(u01*(n-κ+1))`; removed positions = `s0 … s0+κ-1` (contiguous, **no wraparound**, so positions near the ends are under-sampled);
`sub[]` is filled in ascending position order, so the greedy repair **reinserts in ascending position order**, whereas `uniform` reinserts in random draw order.
So `block` differs from `uniform` in two things at once — *which set* is removed (adjacent groups) and *reinsertion order* — hence the controls:
`uniform-sorted` (identical RNG use and removed set as `uniform`, ascending reinsertion), `block-rord` (block's segment, random reinsertion order),
`wrap` (segment start uniform over all n positions, cyclic).

## 1. Test 3 — mechanism

Equal-evaluation best-so-far at 100 % budget, % relative to `uniform` (negative = better), W/L = runs better/worse, p two-sided Wilcoxon:

| arm | n=100 (10 runs) | n=198 (10 runs) |
|---|---|---|
| uniform (mean best) | 392.90 | 2227.48 |
| uniform-sorted | −0.60 % (5/5, p=.23) | +0.10 % (5/5, p=.49) |
| block | −0.97 % (8/2, p=.084) | **−1.79 % (10/0, p=.002)** |
| block-rord | −1.63 % (8/2, p=.064) | **−1.61 % (10/0, p=.002)** |
| wrap | −0.70 % (6/4, p=.49) | **−1.56 % (10/0, p=.002)** |

Pre-registered tests at n=198 (primary) with n=100 as replication:
* **Contiguity matters — rule satisfied.** `block-rord` vs `uniform-sorted`: −1.71 %, 10/0, p=.002 at n=198; same sign at n=100 (−1.04 %, 7/3, p=.13 — direction replicates, significance does not).
* **Reinsertion order does not matter — "neither" clause satisfied at n=198.** `uniform-sorted` vs `uniform`: +0.10 % (5/5); `block` vs `block-rord`: −0.18 % (7/3, p=.32); both below the 0.3 % bar.
  (At n=100 these two contrasts are −0.60 % and +0.67 %, both not significant, opposite in sign to each other — noise-level.)
* **No edge effect from block's start distribution:** `wrap` vs `block` +0.24 % (4/6, p=.32) at n=198, +0.28 % at n=100 — below 0.5 %.
* The 5-run subset (first 5 runs, the size the task asked for) gives the same ordering at n=198 (block −1.87 %, block-rord −2.08 %, wrap −1.50 %, uniform-sorted +0.10 %; 5/0 wins, smallest attainable p=.0625) and, at n=100, is too noisy to separate arms (all within −0.15 … −1.15 %).

**Conclusion (supported):** the gain comes from **removing a contiguous run of adjacent groups**. It is *not* due to reinsertion order, nor to block's edge handling,
nor to removing expensive groups (below). **Not tested:** *why* adjacency helps (see §1.3 for the leading hypothesis) and whether it is adjacency per se or merely locality (a window-restricted random subset would separate these).

### 1.1 Offspring descriptors (mid-run, iterations 1000–3000, pooled over runs; offspring vs its parent)
| n=198 | identical perm | equal-cost plateau | worse | better | removed-set cost¹ | span of removed positions |
|---|---|---|---|---|---|---|
| uniform | 18.1 % | 77.8 % | 2.7 % | 1.41 % | 45.1 | 119 |
| uniform-sorted | 17.9 % | 78.8 % | 1.8 % | 1.49 % | 45.3 | 120 |
| block | 14.6 % | 59.8 % | 24.1 % | 1.47 % | 43.9 | 3 |
| block-rord | 17.7 % | 41.9 % | 39.1 % | 1.34 % | 43.9 | 3 |
| wrap | 14.3 % | 59.8 % | 24.3 % | 1.54 % | 44.4 | 6 |

n=100: identical 3–4 % for every arm; plateau 92 % (uniform) vs 86 % (block) vs 59 % (block-rord); worse 4.0 / 10.1 / 36.0 %; better 0.53 / 0.58 / 0.89 %; removed-set cost 15.9 / 14.9 / 14.9.
¹ mean sum of D(S_{i-1}, g_i) of the κ removed groups at their parent positions, same units as f.
Position displacement / Kendall-tau distance of non-identical offspring are tiny for all arms (n=198: mean displacement 0.04 positions for uniform vs 0.12–0.13 for contiguous arms; normalised KT 0.0002 vs 0.0006–0.0007), i.e. every operator makes small permutation changes; contiguous removal makes ~3× larger ones.

What the descriptors say:
* Contiguous removal produces **many more worse offspring (24–39 % vs 2–4 %)** and fewer plateau moves; the share of *better* offspring is **not** materially different (1.4–1.5 % at n=198). So the gain is not "more improving mutations of a different kind".
* The removed set is **not** more expensive than a uniform draw (43.9 vs 45.1; 14.9 vs 15.9) — slightly cheaper. Contiguity is not a proxy for "cost-greedy" (consistent with Option A: cost-greedy gave nothing).
* Reinsertion order changes the offspring distribution a lot (block-rord: 39 % worse vs block 24 %; uniform-sorted 1.8 % worse vs uniform 2.7 %) but **not the final quality** — so offspring "disruptiveness" per se is not what drives the result.

### 1.2 Frequency vs size of strict improvements (`scripts/analyze_t34_gain.py`, whole run)
| n=198 | strict improvements per 10 000 mutations | mean relative gain per success | total gain per 1000 evals (% of start cost ×100) | share of gain in first 1000 iterations |
|---|---|---|---|---|
| uniform | 290.8 | 0.0674 % | 0.00240 | 73 % |
| uniform-sorted | 302.0 | 0.0639 % | 0.00237 | 72 % |
| block | 333.2 | 0.0699 % | 0.00284 | 79 % |
| block-rord | 328.0 | 0.0699 % | 0.00279 | 80 % |
| wrap | 333.0 | 0.0690 % | 0.00280 | 77 % |

(n=100 shows the same direction but smaller: 117.8 uniform vs 124.5 block per 10 000 mutations; mean gain/success 0.277 % vs 0.300 %.)
* Contiguous removal succeeds **~14 % more often per mutation** at n=198 (333 vs 291) with essentially **the same size of improvement**; total gain per evaluation is ~18 % higher, concentrated in the first quarter of the budget (pure-arm cell u-bin 0 × Q1: +0.025 strict improvements per 1000 evals, 90 % bootstrap interval [+0.009, +0.041]).
* Equal-evaluation gap vs uniform is already −1.63 % at 25 % of the budget and −1.88 % at 50 %, −1.79 % at 100 %: **the advantage is built in the first quarter and then persists** (it is not a late-run effect).

### 1.3 Mechanism — what is supported and what is hypothesis
Supported by the data above: (i) contiguity of the removed set is the active ingredient; (ii) it works through a higher frequency of ordinary-sized strict improvements, mostly early; (iii) it is not removed-set cost, not reinsertion order, not the edge distribution.
**Hypothesis (not tested here):** TRMP cost of a group depends on the orientation history of its sensors, and adjacent groups in a schedule share that history, so removing κ *adjacent* groups lets the greedy repair re-optimise them *jointly*, whereas κ widely separated removals behave almost like κ independent single-group reinsertions, which the already-converged single-insertion local optimum rarely improves (uniform offspring are ~96 % identical-or-plateau at both sizes). An adjacent-but-not-contiguous control (random κ-subset inside a window of width 2κ) and a κ sweep of `block` would test this; I did not run them (1-core budget).
My own initial guess — that contiguity produces *larger* improvements — is **refuted** by §1.2 (gain per success is the same).

## 2. Test 4 — mixed operators (`mix:p`: block with probability p, else uniform; private xorshift RNG; draws never touch `rand()`)

Equal-evaluation best at 100 % budget (mean over 10 runs), % vs uniform; W/L; p:

| arm | n=100 | n=198 |
|---|---|---|
| uniform | 392.90 | 2227.48 |
| mix:0.25 | 388.06 (−1.23 %, 9/1, p=.037) | 2202.96 (−1.10 %, 10/0, p=.002) |
| mix:0.5 | 388.93 (−1.01 %, 8/2, p=.16) | 2202.24 (−1.13 %, 10/0, p=.002) |
| mix:0.75 | 385.84 (−1.80 %, 8/2, p=.020) | 2197.39 (−1.35 %, 8/2, p=.010) |
| block | 389.07 (−0.97 %, 8/2, p=.084) | **2187.55 (−1.79 %, 10/0, p=.002)** |

**Pre-registered contrast, mix vs block (negative = mix better):**
| | n=100 | n=198 |
|---|---|---|
| mix:0.25 vs block | −0.26 % (6/4, p=.49) | **+0.67 % (2/8, p=.027)** |
| mix:0.5 vs block | −0.04 % (5/5, p=1.0) | **+0.66 % (2/8, p=.049)** |
| mix:0.75 vs block | **−0.83 % (8/2, p=.064)** | +0.44 % (3/7, p=.19) |

* **No mix beats block under the rule** (needs ≥0.3 % better on *both* sizes with p<0.1 at n=198): at n=198 every mix is **worse** than block (+0.44 … +0.67 %, two of three p<0.05). **Block dominates** at the instance where the signal is clear.
* The one mix that looks good at n=100 (`mix:0.75`, −0.83 % vs block, p=.064) does **not** replicate at n=198 (+0.44 %) and n=100 is non-monotone in p (392.9 → 388.1 → 388.9 → 385.8 → 389.1 for block share 0 → .25 → .5 → .75 → 1), so I read it as noise.
* At n=198 the result is a clean **dose–response**: mean best 2227.5 (0 % block) → 2203.0 → 2202.2 → 2197.4 → 2187.6 (100 % block): each extra unit of block share is better, no interior optimum.

### 2.1 Per-state evidence (what a learner over operators would need)
Strict-improvement rate per 1000 evaluations by (stagnation quartile u=noimprv/100) × (budget quarter); block minus uniform; 90 % bootstrap interval over runs; only cells with ≥30 strict improvements in both arms are shown.
Pure arms, n=198: 8 valid cells (u-bins 0–1 × 4 quarters); u-bin 0 × Q1 **+0.025 [+0.009,+0.041]\*** (876 vs 686 improvements), Q2 +0.008, Q3 −0.008, Q4 −0.008 (both intervals include 0), u-bin 1 ≈ 0.
Mixed arms (operator used per mutation, pooled over the three mixes), n=198: u-bin 0 × Q1 +0.012\*, u-bin 1 × Q1 +0.013\*, u-bin 1 × Q3 +0.008\* — **all significant cells favour block; no cell favours uniform significantly**. n=100: only u-bin 0 × Q1 (+0.028\*, pooled mixes) is significant, positive.
* **Pre-registered rule for "state-dependent preference" is NOT satisfied at n=100 or n=198** (needs ≥2 significant cells of opposite sign). The hint of a flip is the *late-run, low-stagnation* cells (n=198 pure arms: block −0.008 per 1000 evals vs uniform in Q3/Q4, intervals touching 0; 50–100 events per cell). **At n=400 the rule is met** (§3: Q1 +0.020\*, Q4 −0.010\*, 5 runs only).
* **What this would mean for a learner:** the only candidate state-dependence is *"block early, uniform late"*, i.e. a function of budget phase, which a fixed schedule (e.g. block for the first ~50 % of the evaluations, uniform afterwards) could implement without any RL. Neither this schedule nor a time-varying mix was run; `mix:p` with constant p is monotone-worse than pure block at n=198, so constant mixing is not the way to exploit it.
* **Power limit:** strict improvements are rare (≈1–3 % of mutations early, <0.5 % late) and the high-stagnation bins (u ≥ 0.5) have almost none, so a state-dependent operator choice could only be detected in the early/low-stagnation corner, where block is already uniformly better. A learner would therefore have no resolvable signal to exploit at this sample size.

## 3. n=400 (`dirn400m240r150s04i00`, φ=π/2, 5 paired runs) — confirmation only, pure arms only
This is a **different instance** from Option A's n=400 (`s06i00`), so it is an independent replication of the headline.
Equal-evaluation best-so-far, `block` vs `uniform` (mean best uniform 3275.62):
| budget | block | W/L | p |
|---|---|---|---|
| 25 % | −2.49 % | 5/0 | .0625 |
| 50 % | −2.84 % | 5/0 | .0625 |
| 100 % | **−2.79 %** | 5/0 | .0625 (smallest attainable with 5 pairs) |
Offspring (iterations 1000–3000): identical 4.1/4.6 %, plateau 92.1/80.2 %, worse 1.3/12.2 %, better 2.52/2.95 %, removed-set cost 32.9/31.8, removed span 241/3 (uniform/block). Same picture as n=198: more worse offspring, similar share of better ones, cheaper removed set.
Strict-improvement rate per 1000 evals (block minus uniform, pure arms): u-bin 0 × Q1 **+0.020 [+0.014,+0.025]\*** (888 vs 664 improvements), Q2 +0.005, Q3 −0.004, **Q4 −0.010 [−0.015,−0.005]\*** (33 vs 76); u-bin 1 × Q2 +0.007\*.
**Mixed arms at n=400 were NOT run to completion** (the queue was still on them when I stopped; the Test-4 classification therefore rests on n=100 and n=198 only).
**Per-state rule at n=400: the pre-registered condition (≥2 significant cells of opposite sign) IS met on the pure arms** — block is better early/low-stagnation, uniform is better in the last quarter. Read with care: only 5 runs to resample, the late cell has 33 vs 76 events, no multiplicity correction. The same *direction* is visible at n=198 (Q3/Q4 −0.008 per 1000 evals, intervals include 0), so it is a consistent hint, not an established effect.

## 4. Honest limits
* One instance per size; n=100 and n=198 are the same aperture (φ=π/3), n=400 here is φ=π/2 (pure arms only, 5 runs).
* n=100 has weak power (10 pairs; typical p≈.1). Uncorrected p-values; ~30 contrasts reported.
* κ=4 only; the shuffle (η=100, δ-ladder) is always uniform in every arm — a block-shuffle was not tried.
* The mechanism claim in §1.3 beyond "contiguity of the removed set" is a hypothesis.
* The mix arms use a different RNG consumption pattern than pure arms, so identical seeds do not give identical streams — pairing removes only start-point variance.
* The rule-based classification used n=198 as primary; n=100 mostly replicates direction but not significance.
