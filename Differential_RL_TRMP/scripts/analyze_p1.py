"""Phase 1 analysis of fixed-kappa diagnostic logs (out/p1/*.log). Usage: analyze_p1.py [dir]"""
import sys, glob, os, re, collections
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

d = sys.argv[1] if len(sys.argv) > 1 else "out/p1"
rows = []      # per mutation
runs = {}      # (inst,k,run) -> dict(events)
for fn in sorted(glob.glob(f"{d}/*.log")):
    m = re.match(r".*/(covers_[^.]+)\.k(\d+)\.log", fn)
    inst, k = m.group(1), int(m.group(2))
    ev = collections.defaultdict(list)
    for line in open(fn):
        t = line.split()
        if t[0] == "M":
            run, itr, ke = int(t[1]), int(t[2]), int(t[3]); fp, fo, dc = float(t[4]), float(t[5]), int(t[6]); acc, st = int(t[7]), int(t[8])
            ev[run].append((0, itr, ke, fp, fo, dc, acc, st))
        elif t[0] == "S":
            run, itr = int(t[1]), int(t[2]); fp, fo, dc = float(t[4]), float(t[5]), int(t[6])
            ev[run].append((1, itr, int(t[3]), fp, fo, dc, 1, 0))
    for run, e in ev.items():
        if len(e) and sum(1 for x in e if x[0] == 0) == 4000:     # only complete runs
            runs[(inst, k, run)] = np.array(e, dtype=float)
insts = sorted({i for i, _, _ in runs}, key=lambda s: (int(re.search(r"n(\d+)m", s).group(1)), s))
ks = sorted({k for _, k, _ in runs})

def nof(inst): return int(re.search(r"n(\d+)m", inst).group(1))

print("== M1/M2: offspring vs parent (mutations only, mid half of run = iterations 1000-3000) ==")
print(f"{'instance':30s} k  eff_k  tie%   near0.1%  worse%  better%  meanRelWorse  evals/mut")
for inst in insts:
    for k in ks:
        arr = [runs[(inst, k, r)] for (i, kk, r) in runs if i == inst and kk == k]
        if not arr: continue
        a = np.vstack([x[x[:, 0] == 0] for x in arr]); it = a[:, 1]
        a = a[(it >= 1000) & (it < 3000)]
        fp, fo = a[:, 3], a[:, 4]; rel = (fo - fp) / fp
        tie = np.abs(fo - fp) < 1e-7; near = np.abs(rel) < 1e-3
        worse = rel > 0; worse = worse & ~tie
        print(f"{inst:30s} {k}  {int(np.median(a[:,2]))}  {100*tie.mean():6.1f} {100*near.mean():8.1f} {100*worse.mean():8.1f} {100*(rel<0).mean():8.1f}   {np.mean(rel[worse]) if worse.any() else 0:10.4f}  {a[:,5].mean():9.0f}")

def curve(e):
    """cumulative evals and best-so-far after each event"""
    cum = np.cumsum(e[:, 5]); best = np.minimum.accumulate(np.minimum(e[:, 3], np.where(e[:, 6] == 1, e[:, 4], 1e30)))
    return cum, best
def best_at(e, B):
    cum, best = curve(e); idx = np.searchsorted(cum, B, side="right") - 1
    return best[max(idx, 0)]

print("\n== M3: equal-evaluation best-so-far, mean over runs, % relative to kappa=4 (negative = better than kappa 4) ==")
for inst in insts:
    rr = sorted({r for (i, k, r) in runs if i == inst and all((inst, kk, r) in runs for kk in ks)})
    if not rr: continue
    for frac in (0.25, 0.5, 1.0):
        vals = {k: [] for k in ks}
        for r in rr:
            Bstar = min(curve(runs[(inst, k, r)])[0][-1] for k in ks) * frac
            for k in ks: vals[k].append(best_at(runs[(inst, k, r)], Bstar))
        base = np.array(vals[4]); out = []
        for k in ks:
            v = np.array(vals[k]); pct = 100 * (v.mean() - base.mean()) / base.mean()
            wins = int((v < base - 1e-9).sum()); loss = int((v > base + 1e-9).sum())
            p = ""
            if k != 4 and len(rr) >= 5 and np.any(v != base):
                try: p = f" p={wilcoxon(v, base).pvalue:.3f}"
                except Exception: pass
            out.append(f"k={k}: {v.mean():9.2f} ({pct:+.2f}%, W{wins}/L{loss}{p})")
        print(f"{inst:30s} runs={len(rr):2d} B*x{frac:<4}  " + " | ".join(out))

print("\n== M4: strict incumbent gain per 1000 evals (units: % of start cost), by budget quarter ==")
for inst in insts:
    if nof(inst) < 100: continue
    for k in ks:
        keys = [key for key in runs if key[0] == inst and key[1] == k]
        g = np.zeros(4); n = np.zeros(4)
        for key in keys:
            e = runs[key]; m = e[:, 0] == 0; cum = np.cumsum(e[:, 5]); tot = cum[-1]
            gain = np.where(m & (e[:, 7] == 1), e[:, 3] - e[:, 4], 0.0) / e[0, 3] * 100
            q = np.minimum((cum / tot * 4).astype(int), 3)
            for b in range(4): g[b] += gain[q == b].sum(); n[b] += e[q == b, 5].sum()
        print(f"{inst:30s} k={k}  " + "  ".join(f"Q{b+1}:{1000*g[b]/max(n[b],1):7.4f}" for b in range(4)))
    # ranking per quarter
    print()
