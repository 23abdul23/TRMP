# DECISION — end of Phases 0–2 (go / no-go for Differential-RL destruction control)

Date: 2026-10-31. Rules were fixed in `docs/DECISION_RULES_PHASE1.md` before any diagnostic result was seen.

## 1. Verdict

**Do not start Stage R1 (learn κ only) on the strength of this evidence.** The probe finds a very small κ-headroom
(≤ ~0.2 % at n=198 with 10 runs; a weak, unconfirmed −0.36 % at n=400 with only 3 runs), and it finds a much bigger
structural fact: **92–98 % of all mutations return an offspring with exactly the parent's cost**, so most of the
evaluation budget is spent on no-op moves. Recommended next step (needs your call, see §6):
1. extend the n=400 probe (κ=2 vs κ=4, ≥10 runs) — cheap and decides the only borderline case;
2. a cheap **R2 probe** (fixed cost-greedy / history-aware / block destroy policies, same logging) — the diagnostic below says
   nothing about selection policy, which is where the paper's novelty claim sits;
3. only then build the Q-learner. If both probes are flat, the paper's own §25 negative result applies and is the finding.

Literal application of the pre-registered rules: NO-GO clause not triggered (tie fraction at κ=8 is 82–92 %, below the 95 % bar);
GO clause (a) is technically met at n=400 (κ=2: −0.36 %, 3 wins / 0 losses) but with 3 runs the smallest attainable
Wilcoxon p is 0.25, and the sign flips with budget (κ=2 is +0.43 % *worse* at 25 % of the budget); (a) fails at n=198 once
10 runs are used; (b) (κ ranking changes by phase) fails: κ=2 has the best gain per evaluation in essentially every quarter.
Result: **inconclusive-to-negative for κ, not a proven dead end.**

> **Erratum (Option C measurement):** "most of the evaluation budget is spent on no-op moves" is too strong.
> Of the 92–98 % tie offspring, only 3.9 % (n=100) / 16.4 % (n=198) of mutations at κ=4 return the *identical permutation*; the rest are
> different permutations of equal cost (plateau moves), which the code accepts. True no-ops use ~4 % / ~16 % of the budget at κ=4.

## 2. Phase 0 — reproduction (done)

* Baseline rebuilt from `es_pre_sfFIN.c` (gcc -O2). **32 of 32 instances compared match `results_ESapproach.ods` (Sheet1) exactly**
  on best, mean, SD, and mean/SD of best-iteration: all 31 instances with n ≤ 100 plus n=198 (2198.577 / 2224.518 / 13.914, equal to
  the published table). Script: `scripts/phase0_repro.sh`, `scripts/compare_phase0.py`.
* Not yet reproduced: the other 13 instances with 100 < n < 400 and all 15 with n=400 (compute). A 20-run n=400 reproduction of
  `dirn400m240r150s06i00` (reference 4349.337 / 4373.350 / 17.225) was started with the new driver and was still running at the time of writing:
  `out/n400/row.txt` is written on completion; compare with `scripts/compare_phase0.py`-style check. **Pending — not claimed.**
* Per-run time here is about 0.6× the paper's (31 s vs 52 s at n=198); hardware differs.

## 3. Phase 2 — instrumented refactor (done)

* `src/trmp_core.c`, `src/destroy_repair.c`, `src/es_drl.c`: baseline functions lifted verbatim (by line range), with an evaluation
  counter on `findcost_d` (the per-candidate-position call = the paper's "objective evaluation"; `eval_units` additionally counts prefix
  length scanned), `pert_d(a, κ, policy)` taking κ as a parameter, and a driver with `--runs-csv`, `--iter-log`, `--state-log`
  (u, β, ψ, θ, ζ features — computed without touching `rand()`).
* **Equivalence with the original baseline: PASS** on n=18, n=25 and n=198 (`tests/test_equiv.sh`, columns incl. best-iteration mean/SD,
  which fingerprint the RNG stream). Unit test of cost / wrap-around / κ clamp passes (`tests/test_unit.c`).
  n=400 equivalence is only implied by the pending run above.
* Budget file: `--runs-csv` records per-run `evals_calls` for the baseline; this is the budget `B` RL modes must match.

## 4. Phase 1 — diagnostic results (fixed κ ∈ {2,4,6,8}, uniform destroy, paired seeds)

Mid-run (iterations 1000–3000) offspring vs parent:

| instance (n) | κ | offspring cost == parent | better | worse | evals/mutation |
|---|---|---|---|---|---|
| n=100 (10 runs) | 2 / 4 / 8 | 99.0 / 95.4 / 81.6 % | 0.4 / 0.5 / 0.7 % | 0.6 / 4.0 / 17.8 % | 199 / 394 / 772 |
| n=198 (10 runs) | 2 / 4 / 8 | 98.4 / 95.9 / 87.4 % | 1.1 / 1.4 / 1.4 % | 0.5 / 2.7 / 11.1 % | 395 / 786 / 1556 |
| n=400 (3 runs)  | 2 / 4 / 8 | 96.5 / 97.4 / 92.1 % | 3.3 / 1.8 / 2.8 % | 0.2 / 0.9 /  5.1 % | 799 / 1594 / 3172 |

* Larger κ buys almost no extra improvements; it mostly creates worse offspring while multiplying cost by ~κ/2.
* Best-so-far at equal evaluations, relative to κ=4 (negative = better):
  * n=198 (10 runs): full budget κ=2 −0.00 %, κ=6 +0.02 %, κ=8 +0.08 % (all p > 0.8). Early (25–50 % of budget) κ=6 is worse (+0.47 %, p=0.027; +0.54 %, p=0.014).
  * n=100 (10 runs): κ=6 −0.63 %, κ=8 −0.56 % at full budget (p=0.38, 0.28; 6–7 of 10 wins) — not significant.
  * n=400 (3 runs): κ=2 −0.36 % (3/0), κ=8 −0.20 %, κ=6 +0.44 %; non-monotone and sign-flipping with budget → noise-level at 3 runs.
* Gain per 1000 evaluations: κ=2 is best in every budget quarter at n=100/198/400, κ=8 worst. Note this does **not** translate into better
  final quality (above), because tie moves dominate and everything converges to the same neighbourhood.
* Reading: the destroy-repair operator is highly insensitive to κ at this budget. The learner would have to find gains in
  *which* groups are removed or *when* to shuffle, not in how many.

## 5. What the original paper used for evaluation (answer to your item 4)

From Srivastava & Singh (2018), §5 and Tables 3–5: termination = **4,000 iterations** (not an evaluation count); metrics = best, average,
SD over **20 independent runs** per instance, plus mean **CPU time in seconds**; 60 instances; compared against GA-TRMP+LSB and ES-TRMP_NO-PP;
no statistical test. The paper contains **no evaluation counter**; budget parity vs the RL variants therefore has to come from our own
instrumentation. Decision: **τ = number of `findcost_d` calls (candidate evaluations)**, as in the design document, with `eval_units` and CPU
time reported alongside. Because shuffles use a much larger δ, a baseline run's total evaluations differ from run to run — `B` must be
measured per (instance, run), not computed.

Corrections to the design document / plan found while reading the paper and code:
* Shuffle size: paper and code both use ⌊n/7⌋ (design doc §3.5 says ⌈n/7⌉). We follow the code.
* The `seed` command-line argument of the baseline is dead (overwritten by `srand(run+1)`): runs always use seeds 1..20.
* Code accepts ties (`xdf`), paper text says "better"; we keep the code. Ties are 92–98 % of mutations, so this matters for the
  acceptance-rate metrics (`acc_tie` is logged separately).

## 6. Open items and what I need from you

1. **Your note (item 2): test reduced runs later.** *TODO after the go decision:* evaluate with a reduced protocol (fewer runs/instances and/or
   shorter budget, e.g. 5 runs, n ≤ 200 + a subset of n=400) to see whether the method shows any improvement before committing to the
   multi-day full protocol (~33 CPU-hours per algorithm for n=400). Record the reduced-protocol result next to the full one; do not
   substitute it for the full study.
2. Choose: (A) extend probes (n=400 κ=2 vs 4 at ≥10 runs, then R2 probe) before building R1 — my recommendation; (B) build R1 now anyway
   as a controlled experiment, accepting that the expected κ-headroom is ≲0.3 %; (C) stop and write up the insensitivity finding.
3. Not done / not claimed: n=400 reproduction (running), 13 mid-size instances, R2-policy sensitivity, the learned-shuffle idea (R3).
4. Statistical power: n=400 cells have 3 runs, n=100 and n=198 have 10; all p-values above are exploratory (no multiplicity correction).

## 7. Files

`src/` driver + lifted core; `tests/` equivalence + unit; `scripts/` diagnostic generator, job runners, `analyze_p1.py`, Phase 0 scripts;
raw diagnostic logs are in `out/` (git-ignored; regenerate with `scripts/make_diag.py` + `scripts/run_diag_job.sh`).
Python env: `.venv` (numpy, scipy, matplotlib, pandas, odfpy); `scripts/requirements.txt` should list these.

## 8. Update — Options A, B, C were run (3 agents, separate worktrees, exploratory, not yet merged)

Branches (local, not pushed): A `worktree-agent-aca907d2c67746012` (docs/OPTION_A_RESULTS.md), B `option-b-r1` (docs/OPTION_B_RESULTS.md),
C `worktree-agent-ad7233bf917520519` (docs/OPTION_C_WRITEUP.md + figures).

* **κ-only learning has no headroom (A, B, C agree).** n=400, 10 paired runs: κ=2 vs κ=4 is +0.05 % (4 wins/6 losses, p=0.77) — the earlier −0.36 % (3 runs) and B's
  −0.74 % (3 runs) were noise. B's R1 learner (differential, SMDP) matches fixed κ=2 / random κ at n=100 and n=198 (−0.03 %, −0.14 % vs κ=2, p>0.5), converges to
  κ=2 almost everywhere, and is 0.49 % worse than κ=2 at n=400 (3 runs). Discounted γ=0.9 was −1.10 % vs κ=4 at n=100 (p=0.027) but that equals what fixed κ=2 gives.
  B needed a deviation: τ in raw evaluations made R̄ diverge; τ is now in units of one κ=4 mutation (documented, failed attempt kept).
* **Which groups are removed matters (A).** At κ=4, equal evaluations, vs uniform destroy: `block` −0.97 % (n=100), −1.79 % (n=198, 10/10 runs, p=0.002), −2.66 % (n=400, 5/5 runs, p=0.0625);
  `cost-greedy` no gain; `history-aware` no gain at n≤198 and −0.29 % at n=400 (5/0, p=0.0625, worse early) — unproven. The block n=400 mean (4257.5) is below the published best for that instance (4349.3); the uniform control reproduces the published mean.
  Caveats: one instance per size, ≤10 runs, uncorrected p-values, block only tested at κ=4. **This is a fixed, non-learned operator change — an improvement of the baseline itself, not of an RL controller.**
* **Implication for the plan:** a learner over κ is pointless; a learner over {uniform, block, …} may be worth testing *only after* block is validated on more instances. Suggested next step: make block the fixed baseline, sweep its κ, validate on ≥3 instances per size with ≥10 runs, then re-ask whether anything is left for a learner (R2 over policy × κ).
* **Still not done:** the 20-run n=400 reproduction of the baseline died without output (needs rerun, ~hours); 13 mid-size and 15 n=400 instances unreproduced.
