# Phase 1 decision rules (written BEFORE looking at diagnostic results)

Probe: baseline ES-TRMP with fixed destruction size kappa in {2,4,6,8}, uniform destroy,
shuffle/eta/delta unchanged; same seeds (srand(run+1)) so runs are paired across kappa.
Logged per mutation: parent cost, offspring cost, candidate evaluations used, accepted/strict.

Metrics
* M1 tie fraction  : share of offspring with |f_off - f_parent| < 1e-7 (offspring identical in cost to parent).
* M2 near fraction : share of offspring within 0.1 % of the parent cost.
* M3 equal-budget best-so-far: per (instance, run), compare kappa values at the SAME cumulative
  candidate-evaluation count B* (= smallest total over kappa of that run) and at 25/50/100 % of B*.
* M4 phase dependence: gain per 1000 evaluations (strict incumbent improvements) per kappa in 4 budget quarters.

Go / no-go (applied to instances with n >= 100; n <= 50 is expected to tie)
* NO-GO (degenerate landscape): M1 > 0.95 AND M2 > 0.99 in the middle half of the run for every kappa.
* GO to R1 requires at least one of
    (a) some kappa differs from kappa=4 in mean equal-budget best by >= 0.3 % on >= 1 instance with n >= 198, consistent in sign across runs; or
    (b) the ranking of kappa by gain/1000 evals changes between budget quarters (so a state-dependent policy has something to learn).
* If neither (a) nor (b) holds: R1 (kappa-only) is a likely negative result; recommend only a cheap R2 probe
  (selection policies) before stopping.
Limits to state honestly: few runs per cell (n=400: 3, n=198: 5, n=100: 10) so statistics are exploratory;
this probe says nothing about selection policies (cost-greedy / history-aware), which need Phase 5 code.
