# Differential RL for TRMP — Implementation Plan

**Source design:** `Differential_RL_TRMP_1_1.pdf` (§ references below are to that document).
**Goal:** Replace the blind destroy step of ES-TRMP with a tabular differential (average-reward, SMDP) Q-learning controller, keeping everything else bit-for-bit identical, and measure the effect under an *equal evaluation budget*.
**Code under change:** `Differential_RL_TRMP/es_pre_sfFIN.c` (694 lines, C). `Original_TRMP/` is an untouched copy (verified identical) and stays the reference baseline.

---

## 0. What the existing code actually does (read before changing anything)

Mapping of the paper's components to `es_pre_sfFIN.c`:

| Paper | Code | Notes |
|---|---|---|
| Encoding, `f(ρ)` | `findcost`, `findcost_d(ind, sub)` | Angles in **radians**, absent sensor = sentinel `9` (test `wt<7`), not 400°. `findcost_d` costs a prefix of length `grp-sub`. |
| Pre-processing (NEH + opposite) | `init_pop1`, `fun_neh` | χ = 20 (`SPOP`), `pop_size=grp` if `grp<4`. Leave untouched. |
| Destroy-and-repair | `pert_d(a)` | Reads global `d` (= κ). Destroy: uniform draw of `dd` groups (lines 519–527). Repair: greedy best-position reinsertion (lines 545–576). **Only lines 519–527 are the RL leverage point.** |
| Acceptance | main loop, lines 147–163 | Accepts `record-mut_cost >= ACC` **or equal** (`xdf==1`). Paper says strict; code also takes neutral moves. Keep as is (baseline fidelity), document it. |
| Shuffle | lines 179–219 | `noimprv>=100` → `d` = ladder → `pert_d` → `d=4`. Shuffle result is accepted unconditionally. |
| Run protocol | `tit=20`, `maxit=4000`, 1 instance per process | Output row appended to the results file. |

**Findings that affect the plan (verify in Phase 0, do not assume):**

1. **The `seed` CLI argument is dead.** `srand(seed1)` (line 111) is overwritten by `srand(trn+1)` (line 118) inside the run loop. All 20 runs always use seeds 1..20. Paired comparisons are therefore *naturally* paired by run index; the RL variant needs its own seed stream that does not disturb the baseline's `rand()` draws (see §3.2).
2. **Budget is not 4000 × constant.** The cost of one mutation is `Σ (n−κ+i)` position evaluations and shuffles use δ ≫ κ, so total evaluations per run vary with the number of shuffles. Budget `B` must be **measured per (instance, run)** from Random-DR, not computed.
3. **κ is clamped** to `grp/2` (lines 501–510) and `sub[zl]` caps it at 100. κ=8 on tiny instances silently becomes smaller; the action table must record the *effective* κ.
4. **Shuffle ladder differs slightly from the paper** (`d=(int)(grp/7)` floor vs ⌈n/7⌉, line 190). The baseline is "the code", so we keep the code and note the discrepancy.
5. `vit[]` is read uninitialised in the SD loop (line 270; the value is unused in output). Harmless; leave alone in baseline, don't copy into new code.
6. Large stack arrays (`temp[701][701]` ints ≈ 2 MB in `pert_d`/`fun_neh`). Fine on Linux defaults; don't add more of them.
7. Environment: `gcc 13`, 4 cores, `numpy/scipy` **not installed** (needed for Wilcoxon/Friedman → install in a venv in Phase 9).

---

## 1. Design decisions (resolved here so implementation doesn't stall)

| Decision | Choice | Source |
|---|---|---|
| Language | Keep C for the search + RL (RL loop is trivial next to O(κn²m) repair). Python only for orchestration, stats, plots. | — |
| Algorithm | Differential Q-learning, eqs. (11)–(13); RVI variant behind a flag (eq. 14, table-mean reference). | §12–13 |
| Time unit τ | **Number of `findcost_d` calls** inside the repair (= Σ(n−κ+i), paper's "objective evaluations"). Also log prefix-length work units and wall clock as secondary. | §14.2 |
| Reward | `(f(x)−f(x'))/max(|f(x)|,ε)` computed on the **offspring before acceptance**, then signed-log compressed: `sign(r)·log(1+|r|/c)`. Alternates: raw incumbent (16), rank-normalised (window 200). | §19 |
| Continuing-task fix | Q and R̄ **persist across runs**; the search state resets per run (regenerative stream over training instances). | §20 |
| State | Start `{u, β}` (16 states) → add ψ → add ζ → (θ optional). Bins per §17.3. | §17 |
| Actions | R1: κ∈{2,4,6,8}, uniform. R2: ×{uniform, cost-greedy, history-aware, block} = 16. R3: add `shuffle`, drop η/δ ladder. | §18 |
| ε schedule | 0.30→0.02 linear over budget. α=0.1 constant, η_RL=0.2. | §22 |
| Primary control | **Random-DR** = baseline code path via the same new driver with action fixed to (κ=4, uniform). | §23.1 |

---

## 2. Target file layout

```
Differential_RL_TRMP/
  es_pre_sfFIN.c            # UNCHANGED baseline (kept for Phase 0 regression)
  src/
    trmp_core.c/.h          # instance load, findcost*, eval counter, NEH preprocess (lifted from baseline, behaviour-identical)
    destroy_repair.c/.h     # pert_d split: destroy policies + unchanged greedy repair
    rl_diff.c/.h            # state extractor, Q-table, differential/RVI/discounted update, reward, logging
    es_drl.c                # driver: modes baseline | heuristic | rl-online | rl-train | rl-frozen
  scripts/
    run_batch.py            # parallel runs (4 cores), writes CSV
    analyze.py              # tables, Wilcoxon, Friedman, plots
    requirements.txt        # numpy scipy matplotlib pandas
  Makefile
  tests/
    test_equiv.sh           # driver(baseline mode) == es_pre_sfFIN.exe, per instance
    test_unit.c             # cost, destroy policies, state bins, update rule
  out/                      # gitignored: raw CSV/logs/Q-tables
  docs/plans/…
```

Lifting code rather than editing `es_pre_sfFIN.c` in place keeps a pristine oracle for the equivalence test.

---

## 3. Phased plan (follows §27, with exit criteria)

### Phase 0 — Reproduce ES-TRMP and lock the oracle
- Build `es_pre_sfFIN.c`; run on 3 small + 2 large instances; compare with the paper table (§3.7) and `results_ESapproach.ods` within noise.
- Record per-instance wall time (needed to plan compute: the n=400 runs are ~5 min each × 20 runs).
- **Exit:** reproduction within noise; baseline outputs saved as golden files for the equivalence test.

### Phase 1 — Reward diagnostic (go / no-go, §25)
- Add temporary logging to a copy of the baseline: per iteration, `f(parent)`, `f(offspring)`, accepted?, κ.
- On one n≈200 and one n=400 instance (several seeds): plot acceptance rate over time and the distribution of `(f(x)−f(x'))/f(x)`.
- **Decision rule (write down before looking):** if >95% of offspring have |Δ| below measurement noise of the *offspring spread* (i.e. offspring cost is essentially constant), stop and report the negative result; otherwise continue.
- Also test the **extra signal that varies by κ**: run fixed κ ∈ {2,4,6,8} and compare mean offspring Δ per evaluation — if indistinguishable, the learner has nothing to learn.
- **Exit:** a short `docs/diagnostic.md` with figures and the go/no-go call. **Stop and show the user here.**

### Phase 2 — Instrumentation and refactor (no behaviour change)
1. Split core into `src/`; add global **evaluation counters** (calls and prefix-length units) incremented only inside `findcost_d`/`findcost`.
2. Split `pert_d` into `destroy(policy, κ)` + `repair()`; with policy=uniform and the same RNG call order it must reproduce the baseline.
3. Driver modes: `baseline` (η/δ ladder, fixed κ=4), `heuristic` (cost-greedy κ=4).
4. Stopping condition becomes `evals < B`; in `baseline` mode, `B=∞` and stop at 4000 iterations while recording total evals → this value is the **budget file** consumed by RL modes.
5. State extractor + logging (u, β, ψ, θ, ζ per iteration) — computed from quantities the loop already has; ζ needs per-position transition costs (one extra O(nm) pass, **counted in learning overhead, not budget** — report it).
- **Exit:** `tests/test_equiv.sh` passes — driver in `baseline` mode gives identical best cost per (instance, run) to `es_pre_sfFIN.exe` on all 60 instances (or a justified subset for the n=400 ones if time-bound), and budget files exist.

### Phase 3 — Stage R1 (learn κ only)
- Actions κ∈{2,4,6,8}, state `{u,β}`, differential Q-learning with SMDP τ, offspring + signed-log reward, ε-greedy, ε annealed over budget.
- Shuffle/η/δ **unchanged** in R1/R2 (§22).
- Diagnostics always written: R̄ trace, Q-table dump, action histogram by state, evals counter.
- **Exit:** R̄ stays bounded and non-oscillating; greedy action differs across states on at least one training instance; budget parity check `|evals_RL − B|/B < 1%`.

### Phase 4 — Differential vs discounted (Ablation 3)
- Add γ∈{0.9, 0.99} discounted Q-learning with the same state/action/reward.
- **Exit:** same-budget comparison table; this is what justifies "differential" as a claim.

### Phase 5 — Stage R2 (size × selection policy, 16 actions)
- Implement selection policies in `destroy_repair.c`:
  - `uniform` (baseline draw, must match RNG order);
  - `cost-greedy`: choose κ groups with the largest `D(S_{i−1}, g_{ρi})` contributions;
  - `history-aware`: groups whose cost is driven by a *distant* predecessor (shares a sensor with an earlier group, none in between) — needs a per-sensor "last-touched position" array, built in the same cost pass; **write a unit test with a hand-built 5-group instance first**;
  - `block`: contiguous run of κ positions.
- Selection must be randomised enough (random tie-break / sampling proportional to score) to avoid the destroy step becoming deterministic and repeating the same offspring.
- **Exit:** unit tests pass; action frequency by state logged.

### Phase 6 — SMDP timing ablation (Ablation 4)
- Flag `--tau=evals|one` (τ=1 reproduces plain per-iteration MDP). Compare under identical `B`.

### Phase 7 — Train/test split and deployment modes (§20, §21)
- Split the 60 instances into train/test **stratified by (n, φ)**; fix and commit the split file before running anything on the test set.
- Mode (b): `rl-train` runs the instance stream (fresh instance + seed + pre-processing each "episode", Q and R̄ persist), saves `Q.bin`; `rl-frozen` loads it with ε=0 (or tiny) and learning disabled.
- Mode (a): `rl-online`, Q starts empty inside one run; learning overhead charged.
- Features are all scale-free in n, so a policy trained on n=200 can be tried on n=400 (generalisation test).

### Phase 8 — Stage R3 (learned shuffle)
- Add `shuffle` action (δ-sized destruction, same ladder value as the *size* but chosen by the agent) and remove the η=100 trigger; keep an ablation with it on.
- Optional: swap / insertion neighbourhoods only if R2 shows headroom.

### Phase 9 — Full evaluation and statistics (§23)
- Algorithms: GA-TRMP+LSB (**not in repo — see open question 3**), ES-NO-PP, ES-TRMP/Random-DR, Heuristic-DR, RL-DR (disc.), RL-DR (diff.).
- 20 runs × 60 instances × each algorithm; `run_batch.py` uses 4 workers. n=400 runs dominate (~5 min × 20 × 20 instances ≈ 33 CPU-h per algorithm) → plan compute before launching (see risks).
- Metrics: best, mean, SD, time, convergence vs **evaluations**, relative improvement, acceptance rate, R̄ trace, action frequency by state, learning/inference overhead separately.
- Stats: paired Wilcoxon (RL vs Random-DR) with wins/ties/losses; Friedman + Holm-corrected Wilcoxon across algorithms. Aggregate Wilcoxon over the 20 large instances is the headline, not a single instance.
- Sensitivity: α × η_RL grid (flatness is a claim that must be shown).
- Ablations 1–9 from §23.5.
- Create the venv here: `python3 -m venv .venv && pip install -r scripts/requirements.txt`.

### Phase 10 — Policy interpretation
- Greedy action and q-advantage over (u, β, …) table; R̄ vs evaluations figure; history-aware advantage in identifiable states.

---

## 4. Verification built into every phase

- **Equivalence test** (Phase 2): new driver ≡ baseline. Run in CI-style script after every refactor.
- **Budget parity assertion**: every non-baseline run prints `evals_used`; `analyze.py` fails loudly if any method differs from its Random-DR budget by >1% (§23.2).
- **Unit tests** (`tests/test_unit.c`): cost of a hand-computed 3-group/2-sensor example (including wrap-around > 180°), state bin edges, update rule on a 2-state toy MDP where R̄ and Q are known analytically (checks the sign of the `−R̄τ` term).
- **Bug signatures from §24.4**: separation from iteration 0 ⇒ leaked seed / different init; separation only in the last few % ⇒ budget leak. Add an automatic check on the convergence-curve data.
- Baseline-mode and RL-mode use **separate RNG streams** (`rand()` for the search exactly as baseline, a private xorshift for ε-greedy and tie-breaks) so RL exploration cannot change the search's random draws.

---

## 5. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Landscape insensitive to κ/selection (no learnable signal) | Phase 1 go/no-go; negative result is a planned, publishable outcome (§25). |
| Compute: n=400 ≈ 5 min/run on a 4-core box | Develop and tune on n=50–200; run n=400 only for final tables; run overnight in background; 1 CPU-h ≈ cheap to estimate after Phase 0. |
| Hidden budget leak (RL stops at 4000 iterations, not B) | Loop is on `evals`, asserted in analysis. |
| R̄/Q instability | Always log R̄; reduce η_RL, then α; RVI fallback. |
| Overfitting to training instances | Fixed stratified split, scale-free features, test only once. |
| Baseline acceptance accepts ties (differs from paper text) | Kept for fidelity; flagged in write-up. |
| Dead `seed` argument | Documented; RL driver exposes its own `--rl-seed`. |

---

## 6. Open questions for you (answers change scope)

1. **Stopping point:** after the plan, should I do **Phases 0–2 only** (reproduce + diagnostic + instrumented refactor) and stop for review at the go/no-go, or push straight on to R1? I recommend stopping at the Phase 1 decision.
2. **n=400 compute:** is a 4-core, hours-long batch acceptable here, or should evaluation on n=400 use fewer runs/instances until the method is tuned?
3. **GA-TRMP+LSB baseline:** not in the repo. Skip it (compare against ES variants only), or can you provide that code / published numbers to cite?
4. **Evaluation unit:** confirm τ = number of `findcost_d` calls (paper's definition), with prefix-length work units reported as a secondary measure.
5. **Python deps:** OK to create a venv and `pip install numpy scipy matplotlib pandas` for the analysis scripts?
