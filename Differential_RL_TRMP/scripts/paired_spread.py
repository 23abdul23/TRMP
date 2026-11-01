"""Run-to-run spread of the paired (kappa - kappa4) best-so-far difference at the full common budget B*.
usage: paired_spread.py <p1_dir> <p1b_dir>"""
import sys, collections
import numpy as np
p1, p1b = sys.argv[1:3]
S = [("n=100", p1, "covers_dirn100m060r150s06i03"), ("n=198", p1b, "covers_dirn200m120r150s06i00"), ("n=400", p1, "covers_dirn400m240r150s06i00")]
def load(d, inst, k):
    ev = collections.defaultdict(list)
    for l in open(f"{d}/{inst}.k{k}.log"):
        t = l.split()
        if t[0] == "M": ev[int(t[1])].append((0, float(t[4]), float(t[5]), int(t[6]), int(t[7])))
        elif t[0] == "S": ev[int(t[1])].append((1, float(t[4]), float(t[5]), int(t[6]), 1))
    return {r: np.array(e) for r, e in ev.items() if sum(1 for x in e if x[0] == 0) == 4000}
def best_at(e, B):
    cum = np.cumsum(e[:, 3]); best = np.minimum.accumulate(np.minimum(e[:, 1], np.where(e[:, 4] == 1, e[:, 2], 1e30)))
    return best[max(np.searchsorted(cum, B, side="right") - 1, 0)]
for lab, d, inst in S:
    D = {k: load(d, inst, k) for k in (2, 4, 6, 8)}
    runs = sorted(set.intersection(*[set(D[k]) for k in D]))
    row = {k: [] for k in D}
    for r in runs:
        B = min(np.cumsum(D[k][r][:, 3])[-1] for k in D)
        for k in D: row[k].append(best_at(D[k][r], B))
    base = np.array(row[4])
    print(f"{lab} runs={len(runs)}  between-run SD of kappa=4 best at B*: {100*base.std(ddof=1)/base.mean():.2f}% of mean")
    for k in (2, 6, 8):
        dif = 100 * (np.array(row[k]) - base) / base
        print(f"   kappa={k}: paired diff vs kappa=4  mean {dif.mean():+.2f}%  SD {dif.std(ddof=1):.2f}%  range [{dif.min():+.2f}, {dif.max():+.2f}]%  SE {dif.std(ddof=1)/np.sqrt(len(dif)):.2f}%")
