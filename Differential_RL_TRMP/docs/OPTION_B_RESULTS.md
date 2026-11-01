# Option B — Stage R1 built and run as a controlled experiment (REDUCED protocol)

Branch `option-b-r1` (worktree). This is the **reduced run** requested in `docs/DECISION.md` §6.1: 10 runs on n=100 and n=198,
3 runs on n=400; **not** the full 20-run × 60-instance protocol. All statistics are exploratory, uncorrected for multiplicity
(~25 comparisons in this document).

## Verdict

**Learning κ adds nothing measurable over simply using a small κ.** At equal evaluation budgets, RL-differential is statistically
indistinguishable from *fixed κ=2* and from *uniformly random κ* on n=100 and n=198, and is worse than fixed κ=2 on n=400 (3 runs).
The small gains over the paper's κ=4 baseline (−0.47 %, −0.15 %, −0.25 %) are explained by κ=2 being cheaper per mutation
(+20–90 % more iterations in the same evaluation budget), not by learned state-dependent behaviour. The greedy policy is "κ=2" in
essentially every state. This is the paper's §25 negative outcome ("learned policy near-uniform over κ"), here in the stronger form
"learned policy is a constant". Incidentally: **fixed κ=2 beat the paper's κ=4 by 0.74 % on n=400 in 3/3 paired runs** (p can't go below
0.25 with 3 runs) — worth a dedicated test, independent of RL.

## What was built (all in `Differential_RL_TRMP/`)

* `src/rl_diff.[ch]` — tabular Q-learner, private xorshift64* RNG (never touches `rand()`), differential/SMDP update
  `δ = r − R̄·τ + max Q(s′,·) − Q(s,a); Q += αδ; R̄ += η_RL·α·δ` and a discounted twin `δ = r + γ max Q(s′,·) − Q(s,a)`.
* `src/es_drl.c` `--mode rl-online`: state = {u: 4 bins, β: 4 bins} (16 cells), actions κ∈{2,4,6,8}, uniform destroy, ε-greedy 0.30→0.02
  linear in budget used, α=0.1, η_RL=0.2, reward from the **offspring before acceptance**
  `r=(f−f′)/max(|f|,1e-9)` (exact 0 for ties), signed-log `sign(r)·log(1+|r|/c)`. Acceptance, repair, η=100/δ-ladder shuffle, pre-processing = baseline.
  Stops on an **evaluation budget B = the baseline run's `evals_calls` for the same run index** (`--budget-csv`); a mutation that would
  overshoot B is not started; parity asserted < 1 % (observed max deviation **0.098 %** across every RL/control run reported here). Q and R̄ start empty in every run (online mode).
* Dumps: `--rl-dump P` → `P.trace.csv` (per iteration state/action/reward/τ/δ/R̄/ε), `P.q.csv` (final Q and visit counts per run).
* Flags: `--rl-algo diff|disc`, `--gamma`, `--alpha`, `--eta-rl`, `--eps0/--eps-min`, `--reward-c`, `--kappas`, `--tau-unit`, `--rl-seed`.
* Tests: `tests/test_rl.c` (toy MDPs) — **pass**: 2-state cycle gives R̄→0.5 and Q(A)−Q(B)→0.5; τ=2 gives R̄→0.25 (checks the sign and
  the τ factor of the −R̄τ term); 1-state/2-action SMDP: differential picks the cheaper-per-time action, discounted (τ ignored) picks the
  larger-reward one; RNG range/mean. **Baseline unchanged**: `tests/test_equiv.sh` n018 and n025 PASS after the final build.

### Reward constant c = 0.004 (calibration, not tuned on evaluation data)
Median |r| over mutations with non-zero reward in 3 baseline runs on `covers_dirn100m060r150s06i04` (n=96, a different instance
from every evaluation instance): 12,000 mutations, 4.3 % non-zero (1.1 % improvements, 3.2 % worsenings), median |r| = 0.00415, q10 7.1e-4, q90 1.09e-2.

### Deviation found by running it (disclosed): τ unit
Attempt 1 followed the design document literally with τ = raw candidate evaluations (median 199–395 per step). R̄'s effective gain is then
η_RL·α·τ ≈ 4–8 > 1 and the coupled estimate **diverged to ±1e306/NaN within 7–10 iterations** (the "coupled-estimate instability" of design §12).
Files kept in `out/red_v1_rawtau/` (git-ignored). Fix: τ is measured in units of one κ=4 mutation's evaluations (`--tau-unit` default; `--tau-unit 1`
reproduces attempt 1); R̄ is then reward per baseline-mutation-equivalent. B and all parity checks remain in raw evaluations. A divergence
guard (`|R̄|>1e6` → abort, exit 4) was added. This is a stability fix dictated by the NaN, not a performance tuning; no other parameter was changed after seeing results.

## Results (equal candidate-evaluation budget, paired by run index; lower is better)

Controls run through the identical loop: **fixed κ=2** (`--kappas 2 --eps0 0 --eps-min 0`) and **random κ** (`--eps0 1 --eps-min 1`).
"Random-DR" = the paper's κ=4 baseline. W/T/L is RL-vs-row; p = paired Wilcoxon, two-sided.

| instance (runs) | method | mean best | SD | vs Random-DR | W/T/L | p |
|---|---|---|---|---|---|---|
| n=100 (10) | Random-DR κ=4 | 392.881 | 6.04 | — | — | — |
| | fixed κ=2 | 391.145 | 4.59 | −0.442 % | 6/0/4 | 0.63 |
| | random κ | 390.975 | 5.51 | −0.485 % | 6/0/4 | 0.63 |
| | **RL differential** | 391.018 | 5.50 | −0.474 % | 6/0/4 | 0.63 |
| | RL discounted γ=0.9 | 388.556 | 4.73 | **−1.101 %** | 8/0/2 | **0.027** |
| n=198 (10) | Random-DR κ=4 | 2227.478 | 13.88 | — | — | — |
| | fixed κ=2 | 2227.331 | 13.04 | −0.007 % | 5/0/5 | 0.92 |
| | random κ | 2230.431 | 8.34 | +0.133 % | 5/0/5 | 0.63 |
| | **RL differential** | 2224.158 | 12.08 | −0.149 % | 7/0/3 | 0.13 |
| | RL discounted γ=0.9 | 2226.276 | 11.00 | −0.054 % | 6/0/4 | 0.63 |
| n=400 (3) | Random-DR κ=4 | 4368.833 | 15.06 | — | — | — |
| | fixed κ=2 | 4336.500 | 6.87 | −0.740 % | 3/0/0 | 0.25 (min possible) |
| | **RL differential** | 4357.816 | 20.73 | −0.252 % | 2/0/1 | 0.75 |

Does learning add anything beyond the controls? (paired, RL minus control)

| instance | RL-diff vs fixed κ=2 | RL-diff vs random κ | RL-disc vs fixed κ=2 | RL-disc vs random κ |
|---|---|---|---|---|
| n=100 | −0.033 % (6/0/4, p=0.56) | +0.011 % (5/0/5, p=1.0) | −0.662 % (7/0/3, p=0.19) | −0.619 % (8/0/2, p=0.084) |
| n=198 | −0.142 % (5/0/5, p=0.63) | −0.281 % (7/0/3, p=0.28) | −0.047 % (5/0/5, p=0.85) | −0.186 % (6/0/4, p=0.43) |
| n=400 (3 runs) | **+0.492 %** (1/0/2, p=0.50) | not run | not run | not run |

Reading:
* No difference between RL-differential and the constant-κ=2 policy at n=100/198; at n=400 RL is *worse* than fixed κ=2 (consistent with ε-exploration
  spending ~58 % of first-quarter choices on κ∈{4,6,8} at n=400; 3 runs only).
* The single nominally significant result (discounted, n=100, −1.10 %, p=0.027 vs Random-DR) is not significant against the controls
  (p=0.084/0.19), is not reproduced at n=198 (−0.05 %), and is one of ~25 tests → treat as noise until replicated. Differential vs discounted: no consistent ordering.
* Budget parity holds (max |evals−B|/B = 0.098 %), so the iteration surplus is real: RL-diff made 5069 / 4861 / 4555 iterations vs 4000 for the baseline;
  fixed κ=2 made 7764 on n=400.

## Learned behaviour

* **Greedy action by state** (majority over runs of each run's own greedy κ, states visited ≥ 20 times): κ=2 in **every** (u-bin × budget-quarter) cell
  that was visited, on n=100 (5–10 of 10 runs agree per cell; the one exception is u∈[.4,1) in budget quarter 2, where the majority κ is 4 with only 5/10 runs), n=198 (5–9/10) and n=400 (1–3 of 3; low agreement because 3 runs and 3 runs' worth of visits). Discounted: same.
  The u≥1 bin is visited only for the single iteration before a shuffle (28–82 visits per 10 runs) → effectively 12 states.
* Action share by budget quarter (RL-diff, n=198): κ=2: 53→57→67→67 %; κ=8: 10→9→6→4 %. The share of κ≥4 is largely ε-exploration, which anneals.
* Within-state Q spread (max−min over actions) median 0.035 (n=198), 0.149 (n=100): small relative to a non-zero reward of O(1); only 4.7 % of rewards are non-zero (2.7 % positive).
* **R̄ sanity** (differential): finite and bounded in all 23 runs after the τ fix, but it **changes sign 26–72 times per run** (iterations 200+); mean R̄ by budget quarter at n=198:
  1.2e-2, 8e-4, 1.5e-4, −3e-4; at n=100 mostly negative (−1.1e-2 in Q2–Q4). I.e. the average reward rate is ≈ 0 and slightly negative at n=100 (worsening offspring outnumber improvements), exactly the "R̄ → 0, differential structure degenerates"
  symptom of design §19/§25: the sparse reward leaves little for the −R̄τ term to do.
* **Overhead**: learner time (select + update, measured with `clock()`) = 0.003–0.008 s per run vs 5.6 s (n=100), 32 s (n=198), 163 s (n=400) wall → < 0.01 %. State-feature logging is separate and off by default.

## Caveats (why this is not a final answer)

* Online mode only (Q reset each run, 4000-ish decisions of which ~95 % are no-ops); the design's mode (b) (train across a stream of instances, then freeze) was not tried and
  could differ, though the state-dependence it would exploit is exactly what showed no signal here.
* Only R1 (κ) and only 16 cells (12 reachable). Selection policies (R2) and a learned shuffle (R3) are untested; Phase 1 already said κ-only headroom is tiny.
* RL runs share the pre-processing with their paired baseline run (same `srand(run+1)`) but their search trajectories diverge afterwards, so "paired" means same start only.
* n=400: 3 runs, no discounted/random controls. n=100/198: 10 runs. One instance per size. ε schedule/α/η_RL/c were not tuned (by design); a sensitivity study was not run.
* Fixed κ=2 vs the paper's κ=4: the n=100/198 differences are ≤ 0.44 % and insignificant; the n=400 −0.74 % (3/0/0) is promising but needs ≥ 10 runs and more instances.

## Reproduce

```
make out/es_drl out/test_rl && ./out/test_rl && bash tests/test_equiv.sh tests/golden/n018.txt tests/golden/n025.txt
scripts/run_reduced_b.sh base100 ; scripts/run_reduced_b.sh base198 ; scripts/run_reduced_b.sh base400
scripts/run_reduced_b.sh rl 100 instances/covers_dirn100m060r150s06i03.dat 10 diff      # also: disc ; tag 198 / 400
scripts/ctl_chain.sh fixk2 ; scripts/ctl_chain.sh rand
python scripts/analyze_b.py out/red 100,198,400
```
