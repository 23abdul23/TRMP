"""Analyse laptop runs (laptop/run_confirm.sh). Accepts one or more run folders / .tar.gz archives and MERGES their cells, so e.g. the
kappa 20/24/32 run can be analysed together with the earlier kappa 12/16 run (RM-Report/data/ksweep_confirm_laptop).
Each (instance, kappa) cell is compared run by run with the kappa=4 reference (same seeds) at equal evaluations: the bundled reference
(reference/full_block_k4) or the folder's own ref_k4/ if the laptop's RNG differed. Negative % = better than block kappa=4.
usage: .venv/bin/python -I scripts/analyze_laptop.py <folder|archive.tar.gz> [<folder|archive> ...]"""
import sys, os, re, glob, tarfile, tempfile, numpy as np, pandas as pd
from scipy.stats import wilcoxon
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rng = np.random.default_rng(0)
try:
    pub = pd.read_excel(os.path.join(ROOT, 'results_ESapproach.ods'), engine='odf', sheet_name='Sheet1').iloc[:, :9]
    pub.columns = ['inst', 'n', 'best', 'avg', 'sd', 'time', 'sdtime', 'bg', 'sbg']; pub['inst'] = pub.inst.str.replace('.dat', '', regex=False); pub = pub.set_index('inst')
except Exception as e: pub = None; print('published table unavailable:', e)
rows = {}; pct = {}; absb = {}
for arg in sys.argv[1:]:
    if arg.endswith(('.tar.gz', '.tgz')):
        tmp = tempfile.mkdtemp(); tf = tarfile.open(arg)
        try: tf.extractall(tmp, filter='data')
        except TypeError: tf.extractall(tmp)
        run = [d for d in glob.glob(tmp + '/*') if os.path.isdir(d)][0]
    else: run = arg
    print('== run folder:', run)
    for l in open(os.path.join(run, 'run_info.txt')).read().splitlines()[:11]: print('   ' + l[:170])
    local = len(glob.glob(os.path.join(run, 'ref_k4', '*.k4.csv'))) > 0
    refpath = (lambda i, run=run: os.path.join(run, 'ref_k4', i + '.k4.csv')) if local else (lambda i: os.path.join(ROOT, 'reference', 'full_block_k4', i + '.csv'))
    print('   reference mode:', 'LOCAL kappa=4 runs (laptop RNG differed)' if local else 'bundled kappa=4 reference')
    for f in sorted(glob.glob(os.path.join(run, 'results', '*.k*.csv'))):
        if not os.path.exists(f[:-4] + '.row'): continue                                  # unfinished job
        m = re.match(r'(covers_[^.]+)\.k(\d+)\.csv', os.path.basename(f)); inst, k = m.group(1), int(m.group(2))
        d = pd.read_csv(f).sort_values('run'); r = pd.read_csv(refpath(inst)).sort_values('run'); r = r[r.run.isin(d.run)]
        x, y = d.best.values, r.best.values; pc = 100 * (x - y) / y
        p = wilcoxon(x, y).pvalue if np.any(x != y) else 1.0
        row = dict(inst=inst, n=int(d.n.iloc[0]), ap=re.search(r's(0\d)i', inst).group(1), k=k, runs=len(d), mean_ref=y.mean(), mean_k=x.mean(), pct=pc.mean(),
                   W=int((x < y - 1e-9).sum()), L=int((x > y + 1e-9).sum()), p=p, iters=d['iters'].mean(), evr=d.evals_calls.mean() / r.evals_calls.mean())
        if pub is not None and inst in pub.index: row['vs_pub'] = 100 * (x.mean() - pub.loc[inst, 'avg']) / pub.loc[inst, 'avg']
        rows[(inst, k)] = row; pct[(inst, k)] = pc; absb[(inst, k)] = (x, y)
if not rows: print('no finished cells'); sys.exit()
t = pd.DataFrame(list(rows.values())).sort_values(['n', 'inst', 'k']).reset_index(drop=True)
mm = len(t); order = np.argsort(t.p.values); holm = np.empty(mm); cur = 0
for i, idx in enumerate(order): cur = max(cur, (mm - i) * t.p.values[idx]); holm[idx] = min(1, cur)
t['p_holm'] = holm
t['short'] = t.inst.map(lambda s: 'm%d-s%s-i%s' % (int(re.search(r'dirn(\d{3})', s).group(1)), *re.search(r's(0\d)i(\d\d)', s).groups()))
pd.set_option('display.width', 230)
print(f'\n{len(t)} cells. Budget check: mean evaluations vs kappa=4 reference = {t.evr.mean():.4f} (should be ~1.000)\n')
cols = ['short', 'n', 'k', 'runs', 'mean_ref', 'mean_k', 'pct', 'W', 'L', 'p', 'p_holm', 'iters'] + (['vs_pub'] if 'vs_pub' in t else [])
print(t[cols].round(3).to_string(index=False))
def boot(vals):
    o = [np.mean([rng.choice(vals[i], len(vals[i])).mean() for i in rng.integers(0, len(vals), len(vals))]) for _ in range(3000)]
    return np.percentile(o, [2.5, 97.5])
grp = lambda n: 'n<=100' if n <= 100 else ('n~200' if n <= 200 else 'n=400')
t['grp'] = t.n.map(grp); ks = sorted(t.k.unique())
print('\n== pooled by size and kappa (cluster bootstrap over instances then runs) ==')
for g in ['n<=100', 'n~200', 'n=400']:
    for k in ks:
        s = t[(t.grp == g) & (t.k == k)]
        if len(s) == 0: continue
        vals = [pct[(i, k)] for i in s.inst]; lo, hi = boot(vals); allr = np.concatenate(vals)
        pw = wilcoxon(s.mean_k, s.mean_ref).pvalue if len(s) >= 6 else float('nan')
        extra = f"  vs published ES-TRMP {s.vs_pub.mean():+.2f}%" if 'vs_pub' in s else ''
        print(f"{g:7s} kappa={k:2d} inst={len(s):2d} mean {s.pct.mean():+6.2f}% CI [{lo:+.2f},{hi:+.2f}] runs better {int((allr<0).sum())}/{len(allr)}  Wilcoxon(inst means) p={pw:.4f}{extra}")
    print()
# kappa profile per size group, on the instances common to ALL kappas present in that group, so the values are directly comparable
for g in ['n~200', 'n=400']:
    tg = t[t.grp == g]; kg = sorted(tg.k.unique()); common = [i for i in tg.inst.unique() if all((i, k) in rows for k in kg)]
    if len(kg) < 2 or not common: continue
    print(f'== kappa profile at {g} on the {len(common)} instances common to all its kappas (vs kappa=4; negative = better) ==')
    base = 16 if 16 in kg else kg[0]
    for k in kg:
        vals = [pct[(i, k)] for i in common]; lo, hi = boot(vals); allr = np.concatenate(vals)
        vs = ''
        if k != base:
            dv = [100 * (absb[(i, k)][0] - absb[(i, base)][0]) / absb[(i, k)][1] for i in common]; dl, dh = boot(dv); da = np.concatenate(dv)
            vs = f"   vs kappa={base}: {np.mean([v.mean() for v in dv]):+.2f}% [{dl:+.2f},{dh:+.2f}] (better in {int((da<0).sum())}/{len(da)} runs)"
        print(f"kappa={k:2d}  mean {np.mean([v.mean() for v in vals]):+6.2f}%  CI [{lo:+.2f},{hi:+.2f}]  runs better {int((allr<0).sum())}/{len(allr)}  iterations ~{tg[tg.k==k].iters.mean():.0f}{vs}")
    best = min(kg, key=lambda k: np.mean([pct[(i, k)].mean() for i in common])); print(f'best kappa on these instances: {best}\n')
if len(ks) >= 2:
    print('== head to head between kappas (paired per run, % of the kappa=4 reference; negative = first is better) ==')
    for a in ks:
        for b in ks:
            if a < b:
                for g in ['n~200', 'n=400']:
                    insts = [i for i in t[t.grp == g].inst.unique() if (i, a) in absb and (i, b) in absb]
                    if not insts: continue
                    vals = [100 * (absb[(i, a)][0] - absb[(i, b)][0]) / absb[(i, a)][1] for i in insts]
                    allr = np.concatenate(vals); lo, hi = boot(vals)
                    print(f"{g:6s} kappa {a:2d} vs {b:2d}: mean {np.mean([v.mean() for v in vals]):+.2f}% CI [{lo:+.2f},{hi:+.2f}] first better in {int((allr<0).sum())}/{len(allr)} runs ({len(insts)} inst)")
print('\n== by aperture (n >= 198) ==')
for ap, nm in [('03', '2pi/3'), ('04', 'pi/2'), ('06', 'pi/3')]:
    for k in ks:
        s = t[(t.ap == ap) & (t.k == k) & (t.n >= 198)]
        if len(s): print(f"phi={nm:6s} kappa={k:2d} inst={len(s)} mean {s.pct.mean():+.2f}%")
