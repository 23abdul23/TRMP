"""Extra Test-3 descriptor: size and frequency of strict improvements per arm (mid-run and whole run).
usage: analyze_t34_gain.py <instance>"""
import os, sys
import numpy as np, pandas as pd
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "t34", sys.argv[1])
arms = ["uniform", "uniform-sorted", "block", "block-rord", "wrap", "mix:0.25", "mix:0.5", "mix:0.75"]
print(f"{'arm':15s} strict/10k-mut  mean-gain/strict(%f)  total-gain/1000evals(%f0)  share-of-gain-from-iters<1000")
for a in arms:
    f = os.path.join(root, a + ".csv")
    if not os.path.exists(os.path.join(root, a + ".done")): continue
    df = pd.read_csv(f); m = df[df.op >= 0]
    s = m[m.strict == 1]
    rel = (s.f_par - s.f_off) / s.f_par
    evals = m.dcalls.sum()
    gain = ((s.f_par - s.f_off) / m.groupby("run").f_par.transform("first").loc[s.index]).sum()
    early = ((s[s.itr < 1000].f_par - s[s.itr < 1000].f_off) / m.groupby("run").f_par.transform("first").loc[s[s.itr < 1000].index]).sum()
    print(f"{a:15s} {10000*len(s)/len(m):12.1f}  {100*rel.mean():18.4f}  {1000*gain/evals*100:22.5f}   {100*early/gain:6.1f}")
