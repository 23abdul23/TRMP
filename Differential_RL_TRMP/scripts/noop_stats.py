"""No-op decomposition from out/noop logs (M lines: trn itr kappa f_parent f_off dcalls accepted strict same_perm).
usage: noop_stats.py <noop_dir>"""
import sys, glob, re
import numpy as np

d = sys.argv[1]
print("instance                       k  runs | tie%  identical%  plateau%  | % of mutations|  eval share of: identical / tie / all-mut | whole-run budget share (mut+shuffle): identical")
for inst in ["covers_dirn100m060r150s06i03", "covers_dirn200m120r150s06i00"]:
    for k in (2, 4, 8):
        M, S = [], []
        for l in open(f"{d}/{inst}.k{k}.log"):
            t = l.split()
            if t[0] == "M" and len(t) == 10: M.append([float(x) for x in t[1:]])
            elif t[0] == "S" and len(t) == 7: S.append(float(t[6]))
        a = np.array(M); runs = len(set(a[:, 0]))
        tie = np.abs(a[:, 4] - a[:, 3]) < 1e-7; same = a[:, 8] == 1
        assert not (same & ~tie).any(), "identical permutation must give identical cost"
        mid = (a[:, 1] >= 1000) & (a[:, 1] < 3000)
        m = lambda x, sel=mid: 100 * x[sel].mean()
        tot_all = a[:, 5].sum() + sum(S)
        print(f"{inst:30s} {k}  {runs}    | {m(tie):5.1f}  {m(same):9.1f}  {m(tie & ~same):8.1f} |"
              f"               | {100*a[mid&same,5].sum()/a[mid,5].sum():6.1f} / {100*a[mid&tie,5].sum()/a[mid,5].sum():6.1f} |"
              f" {100*a[same,5].sum()/tot_all:6.1f}")
        # fraction of identical-perm among ties
        print(f"{'':36s} identical share of ties (mid-run): {100*(same&mid).sum()/(tie&mid).sum():.1f}%   "
              f"strict-better {m((a[:,4]<a[:,3]-1e-7))} %  worse {m((a[:,4]>a[:,3]+1e-7))} %  (iterations 1000-3000)")
