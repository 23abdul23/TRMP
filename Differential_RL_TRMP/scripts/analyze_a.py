"""Option-A analysis: paired equal-evaluation comparison of arms from M/S iteration logs.
usage: analyze_a.py <label=path[,path...]> ...   first arm is the control. Run from Differential_RL_TRMP/.
Log format (diag_es.c / es_drl --iter-log): M run itr kappa f_parent f_off evals accepted strict ; S run itr d f_before f_shuffle evals
"""
import sys, collections
import numpy as np
from scipy.stats import wilcoxon

def load(paths):
    ev = collections.defaultdict(list)
    for fn in paths:
        for line in open(fn):
            t = line.split()
            if t[0] == "M":
                ev[int(t[1])].append((0, int(t[2]), int(t[3]), float(t[4]), float(t[5]), int(t[6]), int(t[7]), int(t[8])))
            elif t[0] == "S":
                ev[int(t[1])].append((1, int(t[2]), int(t[3]), float(t[4]), float(t[5]), int(t[6]), 1, 0))
    return {r: np.array(e, dtype=float) for r, e in ev.items() if sum(1 for x in e if x[0] == 0) == 4000}

def curve(e):
    cum = np.cumsum(e[:, 5])
    best = np.minimum.accumulate(np.minimum(e[:, 3], np.where(e[:, 6] == 1, e[:, 4], 1e30)))
    return cum, best

def best_at(e, B):
    cum, best = curve(e); i = np.searchsorted(cum, B, side="right") - 1
    return best[max(i, 0)]

arms = []
for a in sys.argv[1:]:
    lab, ps = a.split("=", 1); arms.append((lab, load(ps.split(","))))
ctrl = arms[0][0]
runs = sorted(set.intersection(*[set(d) for _, d in arms]))
print(f"arms: {[l for l,_ in arms]}   paired runs: {len(runs)} {runs}")

print("\nmid-run (itr 1000-3000) mutation statistics, pooled over runs")
print(f"{'arm':14s} tie%   better%  worse%  strict-accept%  evals/mut   mean-total-evals")
for lab, d in arms:
    a = np.vstack([d[r][d[r][:, 0] == 0] for r in runs]); it = a[:, 1]; a = a[(it >= 1000) & (it < 3000)]
    fp, fo = a[:, 3], a[:, 4]; tie = np.abs(fo - fp) < 1e-7
    tot = np.mean([curve(d[r])[0][-1] for r in runs])
    print(f"{lab:14s} {100*tie.mean():5.1f}  {100*((fo<fp)&~tie).mean():7.2f}  {100*((fo>fp)&~tie).mean():6.2f}  {100*a[:,7].mean():13.2f}  {a[:,5].mean():9.0f}  {tot:15.0f}")

print("\nequal-evaluation best-so-far (mean over runs); % vs control, negative = better; W/L = runs better/worse than control")
for frac in (0.25, 0.5, 1.0):
    Bs = {r: min(curve(d[r])[0][-1] for _, d in arms) * frac for r in runs}
    base = np.array([best_at(arms[0][1][r], Bs[r]) for r in runs])
    cells = []
    for lab, d in arms:
        v = np.array([best_at(d[r], Bs[r]) for r in runs]); pct = 100 * (v.mean() - base.mean()) / base.mean()
        w = int((v < base - 1e-9).sum()); l = int((v > base + 1e-9).sum()); p = ""
        if lab != ctrl and len(runs) >= 5 and np.any(v != base):
            try: p = f" p={wilcoxon(v, base).pvalue:.3f}"
            except Exception: pass
        cells.append(f"{lab}: {v.mean():9.2f} ({pct:+.2f}% W{w}/L{l}{p})" if lab != ctrl else f"{lab}: {v.mean():9.2f}")
    print(f"B*x{frac:<4}  " + " | ".join(cells))

print("\nfinal best of own full run (each arm uses its own budget; NOT equal-evaluation):")
for lab, d in arms:
    v = np.array([curve(d[r])[1][-1] for r in runs]); print(f"  {lab:14s} mean {v.mean():9.2f}  sd {v.std():7.2f}")
