"""Option-B analysis: RL-diff / RL-disc vs baseline Random-DR (paired by run index, equal evaluation budget).
usage: analyze_b.py [dir=out/red] [tags=100,198,400]"""
import sys, os
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

d = sys.argv[1] if len(sys.argv) > 1 else "out/red"
tags = (sys.argv[2] if len(sys.argv) > 2 else "100,198,400").split(",")
KAP = [2, 4, 6, 8]
UB = ["u<.1", ".1-.4", ".4-1", "u>=1"]

def load(fn):
    return pd.read_csv(fn) if os.path.exists(fn) and os.path.getsize(fn) > 0 else None

for tag in tags:
    base = load(f"{d}/base{tag}.csv")
    if base is None: continue
    print(f"\n################ n-tag {tag}: {os.path.basename(base.instance[0])} (n={base.n[0]}) ################")
    rows = {"baseline (Random-DR k=4)": base}
    for algo, nm in (("fixk2", "fixed kappa=2 (equal evals)"), ("rand", "random kappa (equal evals)"),
                     ("diff", "RL differential"), ("disc", "RL discounted g=0.9")):
        x = load(f"{d}/{algo}{tag}.csv")
        if x is not None and len(x) == len(base): rows[nm] = x
    b = base.sort_values("run").best.values
    print(f"{'method':28s} runs  mean best   SD      vs base%   W/T/L   Wilcoxon p   evals parity(max dev)  overhead s/run  wall s/run")
    for nm, x in rows.items():
        x = x.sort_values("run"); v = x.best.values
        if nm.startswith("baseline"):
            print(f"{nm:28s} {len(v):3d}  {v.mean():10.3f} {v.std():7.3f}      --       --        --        --                    --          {x.wall_s.mean():7.1f}")
            continue
        pct = 100 * (v.mean() - b.mean()) / b.mean()
        w = int((v < b - 1e-6).sum()); t = int((np.abs(v - b) <= 1e-6).sum()); l = int((v > b + 1e-6).sum())
        try: p = wilcoxon(v, b).pvalue if np.any(np.abs(v - b) > 1e-6) else 1.0
        except Exception: p = float("nan")
        dev = (np.abs(x.evals_calls.values - x.budget.values) / x.budget.values).max() * 100
        print(f"{nm:28s} {len(v):3d}  {v.mean():10.3f} {v.std():7.3f}  {pct:+8.3f}%   {w}/{t}/{l}   {p:9.3f}   {dev:8.3f}%              {x.rl_overhead_s.mean():8.3f}      {x.wall_s.mean():7.1f}")
    # does LEARNING add anything beyond the controls? paired Wilcoxon of RL vs each control
    for a, an in (("RL differential", "diff"), ("RL discounted g=0.9", "disc")):
        for c in ("fixed kappa=2 (equal evals)", "random kappa (equal evals)"):
            if a in rows and c in rows:
                va = rows[a].sort_values("run").best.values; vc = rows[c].sort_values("run").best.values
                w = int((va < vc - 1e-6).sum()); t = int((np.abs(va - vc) <= 1e-6).sum()); l = int((va > vc + 1e-6).sum())
                try: p = wilcoxon(va, vc).pvalue if np.any(np.abs(va - vc) > 1e-6) else 1.0
                except Exception: p = float("nan")
                print(f"   {a} vs {c}: {100*(va.mean()-vc.mean())/vc.mean():+.3f}%  W/T/L {w}/{t}/{l}  p={p:.3f}")
    # acceptance / shuffles
    for nm, x in rows.items():
        print(f"   {nm:28s} mean strict-accepts {x.acc_strict.mean():7.1f}  tie-accepts {x.acc_tie.mean():8.1f}  shuffles {x.shuffles.mean():5.1f}  iters {x.iters.mean():7.0f}")

    for algo, nm in (("diff", "differential"), ("disc", "discounted")):
        tr = load(f"{d}/{algo}{tag}.trace.csv"); q = load(f"{d}/{algo}{tag}.q.csv")
        if tr is None: continue
        print(f"\n--- {nm}: iteration structure & Rbar sanity ---")
        # action usage by budget phase
        tr["phase"] = np.minimum((tr.evals / tr.groupby("run").evals.transform("max") * 4).astype(int), 3)
        use = tr.groupby(["phase", "kappa"]).size().unstack(fill_value=0)
        print("action share by budget quarter (rows Q1..Q4, cols kappa):"); print((use.div(use.sum(1), axis=0) * 100).round(1).to_string())
        if algo == "diff":
            g = tr.groupby("run")
            print("Rbar per run: final / min / max / #sign changes (of the sign of Rbar after the first 200 iterations)")
            for r, x in g:
                rb = x.rbar.values[200:]; sc = int((np.diff(np.sign(rb)) != 0).sum())
                print(f"   run {r}: {x.rbar.values[-1]: .3e} / {x.rbar.min(): .2e} / {x.rbar.max(): .2e} / {sc}")
            qs = tr.groupby("phase").rbar.mean(); print("mean Rbar by quarter:", [f"{v:.2e}" for v in qs.values])
            print("mean reward/eval actually observed (rcomp sum / evals) overall: %.3e" % (tr.rcomp.sum() / tr.tau.sum()))
        if q is not None:
            print(f"learned greedy action by state (u-bin x budget-quarter), pooled over runs; entries = greedy kappa [visit share of greedy] (mean over runs of per-run greedy):")
            qm = q.groupby(["state", "action"]).agg(Q=("Q", "mean"), v=("visits", "sum")).reset_index()
            lines = []
            for ub in range(4):
                cells = []
                for bb in range(4):
                    s = ub * 4 + bb; qq = qm[qm.state == s]
                    if qq.v.sum() < 50: cells.append("   n/a   "); continue
                    # per-run greedy votes (only runs that visited the state >=20 times)
                    votes = []
                    for r, x in q[q.state == s].groupby("run"):
                        if x.visits.sum() >= 20: votes.append(KAP[int(x.loc[x.Q.idxmax(), "action"])])
                    maj = max(set(votes), key=votes.count) if votes else -1
                    cells.append(f"k={maj} ({votes.count(maj)}/{len(votes)})")
                lines.append(f"  {UB[ub]:6s} | " + " | ".join(f"{c:>12s}" for c in cells))
            print("              Q1           Q2           Q3           Q4   (budget quarter)"); print("\n".join(lines))
            # spread of Q across actions (is there any learned preference?)
            sp = q.groupby(["run", "state"]).apply(lambda x: x.Q.max() - x.Q.min() if x.visits.sum() >= 20 else np.nan).dropna()
            print(f"median within-state Q spread max-min = {sp.median():.4f} (reward scale: compressed reward ~ O(1) when nonzero)")
