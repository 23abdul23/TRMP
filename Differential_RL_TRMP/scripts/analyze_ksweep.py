"""Analyse the block-kappa sweep (out/ksweep/*.csv) against block kappa=4 (out/full_block/*.csv), paired by run
(identical seeds => identical pre-processed start) and at EQUAL candidate evaluations (each run was stopped at the
kappa=4 run's evaluation count). Negative % = better than kappa=4. Usage (from Differential_RL_TRMP/): analyze_ksweep.py"""
import glob, os, re, numpy as np, pandas as pd
from scipy.stats import wilcoxon
rng = np.random.default_rng(0)
rows = []; pct_by = {}
for f in sorted(glob.glob('out/ksweep/*.k*.csv')):
    m = re.match(r'.*/(covers_[^.]+)\.k(\d+)\.csv', f); inst, k = m.group(1), int(m.group(2))
    if not os.path.exists(f'out/ksweep/{inst}.k{k}.row'): continue          # unfinished job
    d = pd.read_csv(f).sort_values('run'); b = pd.read_csv(f'out/full_block/{inst}.csv').sort_values('run').iloc[:len(d)]
    x, y = d.best.values, b.best.values; pct = 100*(x-y)/y
    p = wilcoxon(x, y).pvalue if np.any(x != y) else 1.0
    rows.append(dict(inst=inst, n=int(d.n.iloc[0]), k=k, runs=len(d), mean_k=x.mean(), mean_4=y.mean(), pct=pct.mean(),
                     W=int((x < y-1e-9).sum()), L=int((x > y+1e-9).sum()), p=p, iters=d['iters'].mean(), iters4=b['iters'].mean(),
                     evr=d.evals_calls.mean()/b.evals_calls.mean()))
    pct_by[(inst, k)] = pct
if not rows: print('no finished jobs yet'); raise SystemExit
t = pd.DataFrame(rows).sort_values(['n', 'inst', 'k']).reset_index(drop=True)
m = len(t); order = np.argsort(t.p.values); holm = np.empty(m); run = 0
for i, idx in enumerate(order): run = max(run, (m-i)*t.p.values[idx]); holm[idx] = min(1, run)
t['p_holm'] = holm
t['short'] = t.inst.map(lambda s: 'm%d-s%s-i%s' % (int(re.search(r'dirn(\d{3})', s).group(1)), *re.search(r's(0\d)i(\d\d)', s).groups()))
pd.set_option('display.width', 220)
print(f"{len(t)} finished (instance, kappa) cells; negative % = better than block kappa=4 at equal evaluations\n")
print(t[['short', 'n', 'k', 'runs', 'mean_4', 'mean_k', 'pct', 'W', 'L', 'p', 'p_holm', 'iters']].round(3).to_string(index=False))
def boot(vals):
    out = []
    for _ in range(3000):
        ii = rng.integers(0, len(vals), len(vals))
        out.append(np.mean([rng.choice(vals[i], len(vals[i])).mean() for i in ii]))
    return np.percentile(out, [2.5, 97.5])
print("\n== pooled over instances (cluster bootstrap: instances, then runs) ==")
for name, sel in [('n~200 (198-200)', t.n <= 200), ('n=400', t.n == 400), ('all n>=198', t.n > 0)]:
    for k in sorted(t.k.unique()):
        s = t[sel & (t.k == k)]
        if len(s) == 0: continue
        vals = [pct_by[(i, k)] for i in s.inst]; lo, hi = boot(vals); allr = np.concatenate(vals)
        print(f"{name:16s} kappa={k:2d}  inst={len(s)}  mean {s.pct.mean():+6.2f}%  95% CI [{lo:+.2f},{hi:+.2f}]  runs better {int((allr<0).sum())}/{len(allr)}  (iterations ~{s.iters.mean():.0f} vs {s.iters4.mean():.0f} at kappa=4)")
    print()
