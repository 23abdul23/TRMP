# Differential RL for TRMP — what we tried, what we learned, and what improved over the original ES-TRMP

*Project: G2 — RL-guided destroy-and-repair for the Total Rotation Minimization Problem. Base algorithm: ES-TRMP (Srivastava & Singh, Applied Intelligence 48:4760–4774, 2018). Design brief: "Differential Reinforcement Learning for TRMP" (v1.0).*
*Branch: `claude/serene-faraday-i9lkid`. Everything below is reproducible from the repository; file names are given for each claim.*

---

## 1. Executive summary

**The brief** proposed replacing the *blind* destroy step of ES-TRMP (remove κ=4 uniformly random groups) with a tabular **differential (average-reward, SMDP) Q-learning** controller that chooses the destruction size κ and, later, which groups to remove — everything else (pre-processing, greedy repair, acceptance, budget) frozen.

**What we found, in four sentences**
1. We reproduced the published ES-TRMP **exactly** (33 instances re-run — all 31 with n ≤ 100, one n=198 and one n=400 — with identical best/mean/SD and best-iteration statistics), and built an instrumented driver that is bit-identical to the original.
2. **Learning the destruction size κ does not help.** Fixed κ barely matters, and a differential-RL controller (and a discounted one) ends up equal to simply fixing κ=2, i.e. it learns a constant. This is a controlled negative result.
3. **Which groups are destroyed does matter.** Removing a *contiguous block* of κ adjacent groups instead of κ random groups — a one-line change to the destroy step, no learning involved — improves ES-TRMP on large instances.
4. **Full-protocol result (the paper's own protocol: 4,000 iterations, 20 runs, all 60 instances):** on the 26 instances with n ≥ 198 the new operator improves the mean solution on **26 of 26 instances, by 2.17 % on average (range 1.18 % – 3.07 %), p < 0.0001**; on the 15 instances with n = 400 by **2.32 %** (15/15). It changes nothing on tiny instances (n ≤ 50: ties) and is neutral-to-slightly-better in between. It does **not** reduce run-to-run variance.

**Honest framing for a reader:** the project's *stated method* (differential RL) produced a negative result; the *positive* result is a problem-specific destroy operator discovered by the controlled experiments the RL design required. The learner infrastructure and the negative result remain useful (and are a publishable outcome per §25 of the brief).

---

## 2. Background (what TRMP and ES-TRMP are)

* **TRMP**: order *n* groups of directional sensors so the total rotation (degrees/radians) is minimal. The cost of a group depends on *several* preceding groups (a sensor keeps its last orientation until a later group uses it), so costs cannot be pre-computed; NP-hard.
* **ES-TRMP** (the baseline we must beat): (1+1)-evolution strategy on permutations. NEH + opposite-solution **pre-processing** (χ=20); **mutation = destroy-and-repair** (remove κ=4 uniformly random groups, reinsert each greedily at its best position); elitist acceptance (the code also accepts equal-cost offspring); **shuffle** (same operator with δ ≫ κ) after η=100 non-improving iterations; 4,000 iterations; 20 runs; 60 instances (m∈{50,100,200,400}, apertures 2π/3, π/2, π/3).
* **What the brief called the leverage point**: the destroy step is blind (uniform draw, constant κ); the repair is intelligent. Only the destroy step was to be replaced.

Code facts discovered while reading `es_pre_sfFIN.c` that matter later: the CLI `seed` argument is dead (overwritten by `srand(run+1)`, so runs always use seeds 1..20); the shuffle size uses ⌊n/7⌋ (brief says ⌈n/7⌉; paper and code agree on floor); ties are accepted (paper text says "better"); the budget in evaluations is not fixed because shuffles cost more than normal mutations.

---

## 3. What we did, in order — and what each step taught us

| # | Step | What we did | Result | Decision |
|---|---|---|---|---|
| 0 | **Reproduce ES-TRMP** (`scripts/phase0_repro.sh`, `compare_phase0.py`) | Rebuilt the baseline, ran it on all 31 instances with n ≤ 100, on `dirn200m120r150s06i00` (n=198) and on one n=400 instance, compared with `results_ESapproach.ods` | 32/32 + the n=400 instance (`dirn400m240r150s06i00`: 4349.337 / 4373.350 / 17.225) match the reference **exactly** (best, mean, SD, best-iteration mean and SD) | **Kept** — the baseline is trustworthy |
| 1 | **Instrumented refactor** (`src/trmp_core.c`, `destroy_repair.c`, `es_drl.c`, `tests/`) | Lifted baseline functions verbatim, added an evaluation counter (`findcost_d` calls = the paper's "objective evaluations"), parameterised κ and the destroy policy, added state/iteration logging that never touches `rand()` | Driver ≡ original on n=18, 25, 198 and at n=400; unit tests pass | **Kept** — all later experiments use it |
| 2 | **Phase-1 diagnostic** (fixed κ ∈ {2,4,6,8}, uniform destroy; `docs/DECISION_RULES_PHASE1.md` written *before* results) | Logged parent vs offspring cost per mutation on n≈100/200/400 | 92–98 % of offspring tie the parent's cost; larger κ mostly makes more *worse* offspring (2–4 % → 11–18 % at κ=8) while *better* offspring stay ≈1–3 %; κ costs ~κ/2 times more evaluations; **no κ beats κ=4 at the full budget** | **Go/no-go: κ-only learning looks unpromising**; kept diagnostics as the control methodology |
| 3 | **Option A** — more runs + destroy policies | κ=2 vs κ=4 at n=400 with 10 runs; implemented `cost-greedy`, `history-aware`, `block` destroy | κ=2 vs 4: +0.05 % (p=0.77) — the earlier −0.36 % (3 runs) was noise. `cost-greedy`: no gain. `history-aware`: no gain at n≤198, −0.29 % at n=400 (5/0, p=0.0625, worse early) → unproven. **`block`: −0.97 % (n=100), −1.79 % (n=198, 10/10 runs, p=0.002), −2.66 % (n=400, 5/5)** | `block` **kept**; `cost-greedy` and `history-aware` **dropped** (no demonstrated benefit) |
| 4 | **Option B** — build the RL learner (reduced protocol; `docs/OPTION_B_RESULTS.md`, branch `option-b-r1`) | Tabular differential Q-learning (eqs 11–13), SMDP time = evaluations, state {stagnation u, budget β}, actions κ ∈ {2,4,6,8}, offspring-based signed-log reward; own RNG; strict evaluation-budget parity (max deviation 0.098 %); unit tests on toy MDPs | RL-differential = fixed κ=2 = random κ (differences −0.03 %…−0.14 %, p>0.5); learned policy is "κ=2 in essentially every state"; at n=400 it is 0.49 % *worse* than fixed κ=2 (3 runs). Discounted γ=0.9 was −1.10 % vs κ=4 at n=100 (p=0.027) but that is what fixed κ=2 also gives. Raw-evaluation τ made R̄ diverge to NaN in ~10 iterations → τ measured in κ=4-mutation units (disclosed deviation) | **Dropped as a method**: κ has no headroom, so a learner over κ cannot beat the constant policy. Kept as infrastructure and as the negative result |
| 5 | **Option C** — write-up of the insensitivity (`docs/OPTION_C_WRITEUP.md`, five figures) | Reproduced numbers from the logs; measured how many tie offspring are the *identical permutation* | At κ=4 only 3.9 % (n=100) / 16.4 % (n=198) of mutations return the identical permutation (≈ 4 % / 16 % of the budget); the rest are *plateau moves* (different permutation, equal cost) | **Kept**; corrected my earlier overstatement that "most budget is wasted on no-ops" |
| 6 | **Test 1** — does `block` generalise? (`docs/TEST12_RULES.md` pre-registered) | 3 instances per size across all three apertures, 10 runs (n≈100, 200) / 5 runs (n=400) | n≈100: not better (1/3, −0.04 %); n≈200: 3/3, −1.95 % (p≤0.004 each); n=400: 3/3, −2.68 %, 15/15 paired runs favour block | **Kept**: real at n ≳ 200, not at n≈100 |
| 7 | **Test 2** — κ for block | κ ∈ {2,4,6,8,12} | κ=2 clearly worse (+1.38 %, p=0.004); κ=4,6,8,12 equivalent at n=198; κ=12 maybe −0.77 % at n=400 (not significant, 5 runs) | Use **κ=4** (as in the paper); κ>4 left as a lead |
| 8 | **Test 3** — why does block work? (`docs/TEST34_RESULTS.md`) | Controls: block with random reinsertion order, uniform with sorted reinsertion, block with wrap-around | The ingredient is **removing a contiguous run of adjacent groups** (−1.71 %, 10/0, p=0.002 vs uniform-sorted). Not reinsertion order, not edge effects, not removed-group cost (block removes slightly *cheaper* groups). Block makes strict improvements ~14 % more often with the *same size* per success; advantage built in the first quarter of the budget | Mechanism claim limited to "contiguity"; *why* (joint re-optimisation of adjacent groups sharing sensor history) is an **untested hypothesis** |
| 9 | **Test 4** — mixes of uniform and block | `mix:p`, p ∈ {0.25,0.5,0.75} | At n=198 every mix is worse than pure block (+0.44…+0.67 %), clean dose–response; no state-dependent operator preference at n ≤ 198 | **Dropped** mixing; no signal for a learner over operators |
| 10 | **Test 5** — n=400 reproduction | 20 runs of `dirn400m240r150s06i00` | Identical to the reference row | Driver ≡ baseline at n=400 |
| 11 | **Full-protocol validation** (`scripts/full_block.sh`, `compare_full.py`; `docs/data_full_protocol.txt`) | `--policy block`, κ=4, 4,000 iterations, 20 runs, **all 60 instances**, seeds 1..20, compared with the reference table | See §4 | **Headline result** |

### 3.1 What we deliberately dropped, and why

* **Learning κ with differential or discounted Q-learning (Stage R1 as a method).** κ has essentially no effect on final quality (all κ end within ~0.1 % at n=198), so the optimal policy is "constant"; the learner converges to κ=2 almost everywhere and R̄ flips sign many times per run. No headroom ⇒ nothing to learn.
* **Learning over destroy policy × κ (Stage R2) and learned shuffle (R3).** Not built: Tests 3–4 show `block` dominates every mix and no state-dependent preference is resolvable at n ≤ 198 (strict improvements are too rare in late/high-stagnation states). Would be reconsidered only if a phase-dependent preference is confirmed at n=400 (see §6).
* **`cost-greedy` destroy**: no gain. **`history-aware` destroy** (the brief's "novelty claim"): no gain at n ≤ 198; −0.29 % at n=400 with 5 runs is unproven and slightly worse early in the run.
* **GA-TRMP+LSB comparison**: skipped on instruction (the published GA numbers are not in the repo).
* **Differential-vs-discounted as a claim**: tested on n=100/198; the discounted variant was nominally better at n=100 but equal to the fixed-κ=2 control, so *neither* RL variant is supported; the "differential is better than discounted" claim of the brief is not demonstrated.

### 3.2 Corrections to our own earlier statements (so nobody repeats them)

1. "Most of the evaluation budget is spent on no-op moves" → **wrong as stated**; true no-ops are ≈ 4 % (n=100) to ≈ 16 % (n=198) of the budget at κ=4; most tie offspring are plateau moves.
2. "κ=2 beats κ=4 at n=400" (−0.36 %, −0.74 % on 3 runs) → **noise**; 10 paired runs: +0.05 %, p=0.77.
3. The brief/plan says the shuffle size is ⌈n/7⌉ → code and paper use ⌊n/7⌋; we followed the code.

---

## 4. Improvements over the original TRMP (ES-TRMP) — full protocol

**Setup (identical to the paper except the destroy step):** 4,000 iterations, 20 independent runs per instance (seeds 1..20), κ=4, η=100 / δ-ladder shuffle (still uniform), pre-processing and repair unchanged, acceptance unchanged, 60 instances. Baseline = the published/reference ES-TRMP rows (`results_ESapproach.ods`), which our rebuild reproduces exactly (§3 step 0). Negative % = **block is better**. Statistics are paired over *instances* (one 20-run mean per instance), Wilcoxon signed-rank; tied instances excluded from the test.

### 4.1 Results by instance size (`docs/data_full_protocol.txt`)

| Group | Instances | Mean change of 20-run mean | Wins / ties / losses | Wilcoxon p |
|---|---|---|---|---|
| n ≤ 50 | 21 | 0.00 % | 7 / 7 / 7 | 0.90 (no headroom, as in the paper) |
| 50 < n ≤ 100 | 10 | **−0.35 %** | 9 / 0 / 1 | 0.0098 |
| 100 < n < 200 | 5 | **−1.13 %** | 5 / 0 / 0 | (k too small) |
| n = 200 | 9 | **−1.97 %** | 9 / 0 / 0 | 0.0039 |
| n = 400 | 15 | **−2.32 %** | 15 / 0 / 0 | 0.0001 |
| **n ≥ 198 (headline)** | **26** | **−2.17 %** (range −1.18 % … −3.07 %) | **26 / 0 / 0** | **< 0.0001** |
| all 60 | 60 | −1.03 % (median −0.51 %) | 45 / 7 / 8 | < 0.0001 |

By aperture at n ≥ 198 (the three apertures behave alike, hardest aperture gains most):

| Aperture φ | Instances | Mean change | Wins | p |
|---|---|---|---|---|
| 2π/3 | 7 | −1.83 % | 7/7 | 0.0156 |
| π/2 | 9 | −2.12 % | 9/9 | 0.0039 |
| π/3 | 10 | −2.45 % | 10/10 | 0.0020 |

**Best-found solution (best of 20 runs):** improved on 37 instances, unchanged on 19 (the tiny ones), worse on 4 (n=28, 36, 100, 145; best-of-20 is noisy). On every one of the 26 instances with n ≥ 198 the best-found solution improved.

### 4.2 Examples (angles in radians, as in the paper)

| Instance | ES-TRMP mean (published) | + block destroy mean | Change | Best: published → block |
|---|---|---|---|---|
| dirn200m120r150s06i00 (n=198) | 2224.518 | 2184.983 | −1.78 % | 2198.577 → 2155.020 |
| dirn400m240r150s06i00 (n=400) | 4373.350 | 4270.926 | −2.34 % | 4349.337 → 4231.313 |
| dirn400m240r150s06i01 | 3801.517 | 3692.783 | −2.86 % | 3741.209 → 3635.950 |
| dirn400m240r150s06i02 (largest gain) | 3920.388 | 3800.164 | −3.07 % | 3870.738 → 3733.638 |
| dirn400m240r150s04i00 | 3267.053 | 3191.441 | −2.31 % | 3227.201 → 3137.830 |

Effect size vs noise: for `dirn400m240r150s06i00` the gain of 102.4 equals ≈ 26 standard errors of the published mean (SD 17.2 over 20 runs ⇒ SE 3.85) — far outside seed noise. The brief had predicted 0.5–2 % at n=200 and 1–3 % at n=400 for an RL controller; the measured 2.0 % and 2.3 % for the fixed contiguous operator are within those ranges.

### 4.3 Cost
The change does not alter the repair operator or the number of candidate evaluations per mutation (verified: identical evaluations per mutation, e.g. 394 at n=100, 786 at n=198), so the gain comes at **no extra evaluation cost**; the 4,000-iteration protocol is also the equal-evaluation protocol except for shuffles. We did not report clean wall-clock times (the machine was shared by parallel jobs; the median block/baseline time ratio was 0.98).

### 4.4 What did *not* improve (state this in any presentation)
* **n ≤ 50: no change** (SD is already 0 in the paper; no headroom). **n ≈ 50–100: small** (−0.35 %); at n ≈ 100 block's early advantage fades by the end of the budget.
* **Run-to-run variability is not reduced.** The median SD ratio (block / baseline) is 1.12 at n ≥ 198 — slightly *larger*. The brief's "variance reduction is the more probable win" hypothesis is **not supported**; the improvement is in the mean.
* 8 small instances (n ≤ 78) have a marginally worse mean (≤ 0.52 %); these are small-sample noise on instances where the algorithm already converges.

---

## 5. Everything that was built (deliverables in the repository)

* `src/` — instrumented driver: `trmp_core.c/h` (lifted baseline + evaluation counters), `destroy_repair.c` (destroy policies `uniform`, `block`, `cost-greedy`, `history-aware`, controls, `mix:p`), `es_drl.c` (`--policy`, `--runs-csv`, `--iter-log`, `--state-log` with the brief's u/β/ψ/θ/ζ features), `rl_diff.c/h` (tabular differential/discounted Q-learning; driver integration is on branch `option-b-r1`, not merged because it overlaps with the policy edits).
* `tests/` — equivalence vs the original (`test_equiv.sh` + golden rows), cost/wrap-around unit tests, `history-aware` unit test, RL toy-MDP tests.
* `scripts/` — diagnostics, job runners, reproduction/comparison/analysis scripts (`full_block.sh`, `compare_full.py`, `analyze_*.py`).
* `docs/` — plan, pre-registered decision rules (Phase 1, Tests 1–2, Tests 3–4), `DECISION.md` (running decision log), per-option write-ups, `figures/`, `data/`, `data_full_protocol.txt`.

---

## 6. Threats to validity and open items

* The baseline is the *published/reference* table, reproduced exactly by our rebuild for 33 instances (the 31 with n ≤ 100, one n=198, one n=400); the other 27 instances (13 with 100 < n < 400, 14 with n=400) were not re-run with the baseline. The reference file has only per-instance means, so the §4 test is over instances; the per-run paired confirmation on a 10-instance subset is in §8 (it closes this gap for that subset).
* One hyper-parameter setting for block (κ=4, shuffle unchanged and still uniform); κ=12 looked better at n=400 (−0.77 % vs κ=4, 5 runs, not significant).
* Mechanism is established only to "contiguity of the removed set"; *why* adjacency helps is a hypothesis (joint re-optimisation of groups that share sensor history) — a window-restricted random-subset control would test adjacency vs locality.
* Exploratory p-values in Tests 1–4 are uncorrected (≈ 25 contrasts per write-up); n=400 cells there have 5 runs (p-value floor 0.0625). The full-protocol result (§4) uses all 60 instances and 20 runs and does not rely on them.
* The n=400 pure-arm data suggest block is better early and uniform late in the run (one instance, 5 runs; pre-registered rule met only there) — a lead, not a result.
* No GA-TRMP+LSB comparison (skipped on instruction).

**Suggested next steps (in order of value/cost):** (1) ~~same-session baseline rerun on ≥ 10 instances for per-run paired statistics~~ — done, see §8; (2) block with κ ∈ {6, 8, 12} under the full protocol at n=400; (3) a block-early / uniform-late fixed schedule; (4) window-restricted random-subset control for the mechanism; (5) block-style (contiguous) shuffle; (6) only if (3) shows a confirmed phase-dependent preference, a small learner over {uniform, block} × phase; (7) write-up: lead with the contiguous destroy operator and the controlled negative result for learned κ.

---

## 7. How to reproduce

```bash
cd Differential_RL_TRMP
make out/es_drl out/es_base                      # driver and original baseline
bash tests/test_equiv.sh                         # driver == original (golden rows)
scripts/phase0_repro.sh 1 200 4                  # rebuild baseline rows -> out/phase0
.venv/bin/python scripts/compare_phase0.py       # exact-match check vs results_ESapproach.ods
scripts/full_block.sh 4                          # block, 60 instances x 20 runs (several hours; the 15 n=400 instances dominate)
.venv/bin/python scripts/compare_full.py         # the tables in section 4
```
Environment: `python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt`.

---

## 8. Addendum — same-session baseline and per-run paired confirmation (10 instances)

**Why:** §4 compared `block` against the *published* reference rows, which only contain per-instance means, so the test could only be over instances. To check the result with the strongest paired design, we re-ran the original uniform-destroy ES-TRMP **in this session** on a 10-instance subset and paired it with the `block` runs **run by run**.

**Design.** Same code and protocol for both arms (4,000 iterations, κ=4, shuffle uniform, seeds 1..20). Run *r* of both arms starts from the identical pre-processed solution (`srand(r+1)`), then the trajectories diverge, so the pairing removes start-point variance. Subset (all three apertures, all sizes with headroom): n≈100 — `s03i03` (n=94), `s06i03` (n=100); n≈200 — `s06i00` (n=198), `s03i03`, `s04i01`, `s06i01` (n=200); n=400 — `s03i00`, `s04i00`, `s06i00`, `s06i01`. The `s06i00` n=400 baseline is the earlier 20-run reproduction run; the other nine were run for this addendum. Scripts: `scripts/same_session.sh`, `scripts/analyze_paired.py`; numbers: `docs/data_paired.txt`.

**Validity check.** The same-session uniform mean equals the published reference mean on **10 / 10** instances (|Δ| < 0.001), so the comparison baseline is the genuine ES-TRMP and the paired design is sound.

### 8.1 Per-instance results (20 paired runs each; negative % = block better)

| Instance | n | Uniform mean | Block mean | Change | Runs better / worse | Wilcoxon p (Holm over 10 instances) | Paired effect size dz |
|---|---|---|---|---|---|---|---|
| dirn100m060r150s03i03 | 94 | 305.439 | 303.957 | −0.48 % | 13 / 7 | 0.048 (0.08) | −0.50 |
| dirn100m060r150s06i03 | 100 | 392.536 | 389.603 | −0.73 % | 15 / 5 | 0.040 (0.08) | −0.49 |
| dirn200m120r150s06i00 | 198 | 2224.518 | 2184.983 | −1.78 % | 20 / 0 | < 0.001 (< 0.001) | −2.29 |
| dirn200m120r150s03i03 | 200 | 749.745 | 740.870 | −1.18 % | 18 / 2 | < 0.001 (< 0.001) | −1.30 |
| dirn200m120r150s04i01 | 200 | 1397.124 | 1364.673 | −2.32 % | 20 / 0 | < 0.001 (< 0.001) | −2.25 |
| dirn200m120r150s06i01 | 200 | 1340.500 | 1308.422 | −2.39 % | 19 / 1 | < 0.001 (< 0.001) | −2.39 |
| dirn400m240r150s03i00 | 400 | 2569.235 | 2511.092 | −2.26 % | 20 / 0 | < 0.001 (< 0.001) | −3.61 |
| dirn400m240r150s04i00 | 400 | 3267.053 | 3191.441 | −2.31 % | 20 / 0 | < 0.001 (< 0.001) | −3.03 |
| dirn400m240r150s06i00 | 400 | 4373.350 | 4270.926 | −2.34 % | 20 / 0 | < 0.001 (< 0.001) | −4.87 |
| dirn400m240r150s06i01 | 400 | 3801.517 | 3692.783 | −2.86 % | 20 / 0 | < 0.001 (< 0.001) | −3.99 |

(Paired effect size dz = mean of the per-run % difference divided by its SD; |dz| > 0.8 is conventionally "large".)

### 8.2 Pooled (cluster bootstrap over instances, then runs; 95 % interval)

| Group | Instances | Mean change | 95 % CI | Paired runs where block is better |
|---|---|---|---|---|
| n ≈ 100 | 2 | −0.60 % | [−1.06, −0.21] | 28 / 40 |
| n ≈ 200 (198–200) | 4 | −1.92 % | [−2.39, −1.39] | 77 / 80 |
| n = 400 | 4 | −2.44 % | [−2.74, −2.20] | **80 / 80** |
| **n ≥ 198** | **8** | **−2.18 %** | **[−2.50, −1.81]** | **157 / 160** |
| whole subset | 10 | −1.86 % | [−2.33, −1.36] | 185 / 200 |

Wilcoxon over instance means: n ≥ 198, p = 0.0078 (the smallest possible with 8 instances); whole subset, p = 0.0020.

### 8.3 Findings

1. **The headline is confirmed with the strongest design.** At n ≥ 198, block is better in **157 of 160 paired runs** and the pooled mean gain is **−2.18 %** (CI −2.50 … −1.81 %), matching the −2.17 % found against the published table in §4. At n = 400 it wins **all 80** paired runs (−2.44 %).
2. **The effect is large relative to run-to-run noise** (|dz| between 1.3 and 4.9 at n ≥ 198): the gain is not an artefact of lucky seeds or of comparing against a published table.
3. **The size dependence is confirmed.** The gain grows from ≈ 0.6 % (n ≈ 100) to ≈ 1.9 % (n ≈ 200) to ≈ 2.4 % (n = 400). At n ≈ 100 it is modest: 28 of 40 runs, per-instance p ≈ 0.04–0.05, which does **not** survive Holm correction across the 10 tests (p = 0.08). Treat n ≈ 100 as "suggestive", consistent with the −0.35 % over the 10 instances of 50 < n ≤ 100 in §4.
4. **Run-to-run variability is still not reduced.** Median SD ratio (block / uniform) at n ≥ 198 is 1.09 (the SD is about 9 % larger, individual instances range 0.8–1.6). The gain is in the mean, not in consistency.
5. **The baseline reproducibility claim is strengthened:** a fresh run of the original algorithm reproduced the reference mean on 10 / 10 instances, so differences in §4 cannot be explained by hardware, compiler or code drift.

### 8.4 Limits of this addendum
* 10 instances (8 with n ≥ 198), not all 60; the full-population statement remains §4 (against the published table, 60 instances); this addendum replaces its weakest assumption (baseline provenance and instance-level pairing) on the subset.
* Both arms use the same seeds 1..20, so pairing is by start point only; within an instance the 20 runs are not independent of the instance, so the pooled bootstrap resamples instances then runs (only 4 n = 400 instances, so the n = 400 interval is narrower than a fresh-instance interval would be).
* Block is still tested only at κ=4 with uniform shuffle. The per-state "block early / uniform late" hint (n = 400, one instance) is untouched.
* Subset selection was by size/aperture coverage and by compute (n = 400 is ~1 h per instance per arm), not by results; the instances were not chosen after seeing outcomes. Two instances (`s06i00` n = 198 and n = 400) were also used in earlier exploratory tests.

**Bottom line after the addendum:** the improvement of contiguous (`block`) destroy over the original ES-TRMP is real, large at n ≥ 198 (≈ 2 %, ≈ 98 % of paired runs), modest at n ≈ 100, absent at n ≤ 50, and does not reduce variance. It costs no extra evaluations per mutation.
