"""fig10: block-destroy kappa profile at n=400 (6 instances common to all kappas) and kappa 12/16 at n~200, vs block kappa=4 at equal evaluations,
from the laptop runs saved in RM-Report/data/ksweep_confirm_laptop and ksweep_plateau_laptop. Run from Differential_RL_TRMP/:
.venv/bin/python -I ../RM-Report/scripts/make_kprofile_figure.py"""
import glob, os, re, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
rng = np.random.default_rng(0); pct = {}
for d in ['../RM-Report/data/ksweep_confirm_laptop', '../RM-Report/data/ksweep_plateau_laptop']:
    for f in glob.glob(d + '/results/*.k*.csv'):
        if not os.path.exists(f[:-4] + '.row'): continue
        m = re.match(r'(covers_[^.]+)\.k(\d+)\.csv', os.path.basename(f)); i, k = m.group(1), int(m.group(2))
        x = pd.read_csv(f).sort_values('run'); r = pd.read_csv(f'reference/full_block_k4/{i}.csv').sort_values('run'); r = r[r.run.isin(x.run)]
        pct[(i, k)] = 100 * (x.best.values - r.best.values) / r.best.values
def boot(v): return np.percentile([np.mean([rng.choice(v[j], len(v[j])).mean() for j in rng.integers(0, len(v), len(v))]) for _ in range(3000)], [2.5, 97.5])
insts400 = sorted({i for (i, k) in pct if '400m' in i}); insts200 = sorted({i for (i, k) in pct if '200m' in i})
fig, ax = plt.subplots(figsize=(7.8, 4.3))
for name, insts, ks, c, off in [('n = 400 (6 instances, 60 runs)', insts400, [12, 16, 20, 24, 32], '#d6604d', 0.1), ('n ≈ 200 (5 instances, 50 runs; κ = 12, 16 only)', insts200, [12, 16], '#4575b4', -0.1)]:
    xs = [4]; ys = [0.0]; lo = [0.0]; hi = [0.0]
    for k in ks:
        v = [pct[(i, k)] for i in insts]; mu = np.mean([a.mean() for a in v]); l, h = boot(v); xs.append(k); ys.append(mu); lo.append(mu - l); hi.append(h - mu)
    ax.errorbar(np.array(xs) + off * np.array(xs) ** 0.5 * 0.5, ys, yerr=[lo, hi], fmt='-o', color=c, capsize=3, label=name)
ax.axhline(0, color='#444', lw=.8); ax.set_xticks([4, 12, 16, 20, 24, 32]); ax.set_xlabel('block destruction size κ  (κ = 4 is the reference)')
ax.set_ylabel('change vs block κ=4 at equal evaluations (%)\nnegative = better'); ax.set_title('Block destroy: the gain peaks around κ = 16–20 and fades by κ = 32 (95% CI)', fontsize=10.5)
ax.legend(frameon=False, loc='lower right'); [ax.spines[s].set_visible(False) for s in ('top', 'right')]
fig.tight_layout(); fig.savefig('../RM-Report/figures/fig10_kappa_profile.png', dpi=170); print('ok')
