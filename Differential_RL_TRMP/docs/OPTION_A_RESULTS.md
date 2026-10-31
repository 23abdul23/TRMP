# Option A results — extended probes (κ at n=400, then destroy-selection policies)

Setup: baseline ES-TRMP, 4000 iterations/run, η=100 and δ-ladder shuffle unchanged, κ=4 unless stated, `srand(run+1)`
per run so arms are paired (identical pre-processing). Comparison = best-so-far at **equal cumulative candidate-evaluation
count** (`findcost_d` calls) per run, at 25/50/100 % of B* (the smallest total among the compared arms); Wilcoxon signed-rank
on the paired per-run values, W/L = runs better/worse than control. No multiplicity correction. Raw logs are in `out/`
(git-ignored); commands in `scripts/launch_a1.sh`, `scripts/sched_a2.sh`; analysis `scripts/analyze_a.py`.
Uniform control = the parent's κ=4 diag logs (the diag build is the baseline plus counters, bit-identical search).

## 1. n=400: κ=2 vs κ=4, 10 paired runs (was 3)

| budget | κ=4 mean best | κ=2 vs κ=4 | W/L | p |
|---|---|---|---|---|
| 25 % | 4431.81 | +0.18 % | 3/7 | 0.131 |
| 50 % | 4402.36 | +0.09 % | 4/6 | 0.557 |
| 100 % | 4383.30 | +0.05 % | 4/6 | 0.770 |

The −0.36 % (3 wins / 0 losses) seen with 3 runs **was noise**. κ-only control has no detectable headroom at n=100, 198 or 400.
κ=2 has a lower tie-rate cost per evaluation but the same end quality (tie 97.3 % vs 96.8 %).

## 2. Destroy-selection policies at κ=4 vs uniform

Mid-run (iterations 1000–3000) offspring statistics and equal-budget results. `strict-accept` = share of mutations that
strictly improved the incumbent.

### n=100 (`dirn100m060r150s06i03`, 10 runs)
| arm | tie % | worse % | strict-accept % | 25 % | 50 % | 100 % (vs uniform; W/L; p) |
|---|---|---|---|---|---|---|
| uniform | 95.4 | 4.0 | 0.53 | — | — | 392.90 |
| cost-greedy | 94.7 | 4.7 | 0.60 | +0.55 % (4/6, .38) | +0.30 % | +0.31 % (5/5, .70) |
| history-aware | 93.7 | 5.6 | 0.66 | +0.51 % (3/7, .38) | +0.08 % | −0.04 % (4/6, 1.0) |
| **block** | 89.3 | 10.1 | 0.58 | **−1.28 % (9/1, .037)** | −1.08 % (8/2, .13) | **−0.97 % (8/2, .084)** |

### n=198 (`dirn200m120r150s06i00`, 10 runs)
| arm | tie % | worse % | strict-accept % | 25 % | 50 % | 100 % |
|---|---|---|---|---|---|---|
| uniform | 95.9 | 2.7 | 1.41 | — | — | 2227.48 |
| cost-greedy | 94.4 | 4.0 | 1.60 | +0.41 % (2/8, .027) | −0.06 % | +0.13 % (5/5, .63) |
| history-aware | 94.0 | 4.6 | 1.43 | +0.21 % (5/5) | +0.08 % | +0.15 % (5/5, .63) |
| **block** | 74.5 | 24.1 | 1.47 | **−1.63 % (10/0, .002)** | **−1.88 % (10/0, .002)** | **−1.79 % (10/0, .002)** |

### n=400 (`dirn400m240r150s06i00`, 5 runs; control = κ=4 runs 0–4)
| arm | tie % | worse % | strict-accept % | 25 % | 50 % | 100 % |
|---|---|---|---|---|---|---|
| uniform | 97.0 | 0.9 | 2.07 | — | — | 4374.04 |
| cost-greedy | 95.8 | 1.9 | 2.35 | +0.53 % (1/4, .19) | +0.33 % | +0.22 % (2/3, .63) |
| history-aware | 95.5 | 2.0 | 2.51 | +0.17 % (1/4, .63) | +0.05 % | −0.29 % (5/0, .0625) |
| **block** | 83.8 | 13.3 | 2.91 | **−2.14 % (5/0, .0625)** | −2.40 % (5/0, .0625) | **−2.66 % (5/0, .0625)** |

(With 5 pairs the smallest attainable two-sided Wilcoxon p is 0.0625; with 10 pairs, 0.002.)

## 3. What is significant, what is noise

* **block (contiguous κ positions) is a real, consistent improvement**: −0.97 % (n=100, 8/10), −1.79 % (n=198, **10/10, p=0.002**),
  −2.66 % (n=400, 5/5). Effect grows with n, is present already at 25 % of the budget, and uses the same number of evaluations.
  At n=400 its mean best (4257.5) is below the published ES-TRMP *best* of any single run for this instance (reference 4349.337;
  our uniform control reproduces the published mean, 4373.8 vs 4373.35). Mechanism visible in the logs: block offspring differ from the
  parent far more often (tie 84 % / 75 % vs 97 % / 96 %) and strict-accept rate rises.
* **cost-greedy: no gain** (null or slightly worse; +0.5 % early at n=198, p=0.027 for *worse*, not significant elsewhere).
* **history-aware (the paper's "novelty" candidate): no demonstrable gain.** Zero effect at n=100/198; −0.29 % (5/5, p=0.0625) only at
  n=400 full budget, after being slightly worse at 25–50 %. Treat as unproven; it needs ≥10 runs at n=400 before any claim.
* All p-values are exploratory and uncorrected; 3 policies × 3 budgets × 3 instances = 27 tests.

## 4. Validity checks

* `POLICY_UNIFORM` unchanged: `tests/test_equiv.sh` passes on n=18 and n=25 (incl. best-iteration mean/SD, an RNG fingerprint).
* `tests/test_history.c`: hand-built 5-group instance, history scores [0,0,0,0.5,0.5] and costs as derived; every policy returns a valid
  permutation with the correct cost. `tests/test_policy_real.c`: on the real n=198 instance all four policies give
  |reported − recomputed cost| = 0 over 300 mutations each.
* Driver-reported per-run bests (`--runs-csv`) agree with the log-reconstructed means (block n=198: 2187.55 both).
* Budget parity: mean total evaluations per run differ by <1.5 % between arms (e.g. 3.223 M vs 3.228 M at n=198); the equal-evaluation
  comparison truncates to the common budget anyway.
* Caveats: cost-greedy / history-aware call `position_costs`/`history_costs` per mutation; this O(nm) overhead is **not** charged to the
  budget (it would only hurt them). Block was run only at κ=4 (not tuned). Uniform control logs come from the diag build, policy arms
  from `es_drl`; both use identical RNG streams and uniform equivalence was verified only on n=18/25 (n=198 equivalence passed earlier in the parent session).

## 5. Verdict

κ-only learning (Stage R1): **no headroom** — drop or demote it. The learnable lever is *which* groups are removed: a fixed
**contiguous-block destroy already gives ≈1–2.7 % over the published baseline at equal evaluations**, which is far above the
paper's expected 0.5–3 % for an RL controller. Recommended next step: treat `block` as the new fixed baseline ("Heuristic-DR" in §23.1
of the design doc), sweep κ for block (2, 4, 6, 8, 12), then test whether a state-dependent choice among {uniform, block, κ} has
anything left to learn. Any RL claim must be made against block-DR, not only against Random-DR.
