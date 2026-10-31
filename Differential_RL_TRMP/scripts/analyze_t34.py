"""Analysis for Tests 3+4 (see docs/TEST34_RULES.md). Reads out/t34/<instance>/<policy>.csv (es_drl --mut-log).
usage: analyze_t34.py <instance> [maxruns]      (run with the venv python; cwd irrelevant)
Columns: run,itr,op,noimprv,evals,f_par,f_off,dcalls,acc,strict,cls,disp,kt,rem_cost,span ; op=-1 marks a shuffle row.
cls: 0 identical permutation, 1 equal-cost plateau, 2 worse, 3 better.
"""
import os, sys
import numpy as np, pandas as pd
from scipy.stats import wilcoxon

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "t34")
inst = sys.argv[1]
maxruns = int(sys.argv[2]) if len(sys.argv) > 2 else 99
d = os.path.join(root, inst)
ARMS = ["uniform", "block", "uniform-sorted", "block-rord", "wrap", "mix:0.25", "mix:0.5", "mix:0.75"]
n = int(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "instances", inst + ".dat")).readline().split()[2])

def load(arm):
    f = os.path.join(d, arm + ".csv")
    if not os.path.exists(f) or not os.path.exists(os.path.join(d, arm + ".done")): return None
    df = pd.read_csv(f)
    df = df[df.run < maxruns]
    ok = [r for r, g in df.groupby("run") if (g.op >= 0).sum() == 4000]
    return {r: g.reset_index(drop=True) for r, g in df.groupby("run") if r in ok}

data = {a: load(a) for a in ARMS}
data = {a: v for a, v in data.items() if v}
print(f"instance {inst} (n={n}); arms loaded: {list(data)}")
runs = sorted(set.intersection(*[set(v) for v in data.values()]))
print(f"paired runs: {len(runs)}")

def curve(g):
    cum = np.cumsum(g.dcalls.values)
    cand = np.where(g.acc.values == 1, g.f_off.values, 1e30)
    best = np.minimum.accumulate(np.minimum(g.f_par.values, cand))
    return cum, best
def best_at(g, B):
    cum, best = curve(g); i = np.searchsorted(cum, B, side="right") - 1
    return best[max(i, 0)]
tot = {a: {r: curve(data[a][r])[0][-1] for r in runs} for a in data}

def vals(arm, frac, ref_arms):
    B = {r: min(tot[x][r] for x in ref_arms) * frac for r in runs}
    return np.array([best_at(data[arm][r], B[r]) for r in runs])
def cmp(a, b, frac=1.0, ref_arms=None):
    """a vs b at equal evaluations; returns (pct a relative to b, W, L, p)"""
    ref = ref_arms or [a, b]
    va, vb = vals(a, frac, ref), vals(b, frac, ref)
    pct = 100 * (va.mean() - vb.mean()) / vb.mean()
    W = int((va < vb - 1e-9).sum()); L = int((va > vb + 1e-9).sum())
    try: p = wilcoxon(va, vb).pvalue if np.any(va != vb) else 1.0
    except Exception: p = float("nan")
    return pct, W, L, p, va.mean(), vb.mean()

print("\n== equal-evaluation best-so-far vs uniform (B* = min total over ALL arms), negative % = better ==")
allarms = list(data)
for frac in (0.25, 0.5, 1.0):
    cells = []
    for a in allarms:
        if a == "uniform": cells.append(f"uniform {vals('uniform',frac,allarms).mean():9.2f}"); continue
        pct, W, L, p, ma, mb = cmp(a, "uniform", frac, allarms)
        cells.append(f"{a} {ma:9.2f} ({pct:+.2f}% W{W}/L{L} p={p:.3f})")
    print(f"B*x{frac:<4} " + " | ".join(cells))
if len(runs) >= 10:
    print("\n(first 5 runs only, as in the original Test-3 request)")
    sub = runs[:5]
    saved = runs; runs = sub
    for frac in (1.0,):
        cells = []
        for a in allarms:
            if a == "uniform": continue
            pct, W, L, p, ma, mb = cmp(a, "uniform", frac, allarms); cells.append(f"{a} ({pct:+.2f}% W{W}/L{L} p={p:.3f})")
        print(f"B*x{frac:<4} " + " | ".join(cells))
    runs = saved

print("\n== TEST 3 rule thresholds (100% budget; pairs compared at their own B*) ==")
def line(a, b, note):
    if a in data and b in data:
        pct, W, L, p, ma, mb = cmp(a, b, 1.0)
        print(f"  {a:15s} vs {b:15s}: {pct:+.2f}%  W{W}/L{L} p={p:.3f}   [{note}]")
line("uniform-sorted", "uniform", "reinsertion order, same removed set")
line("block", "block-rord", "reinsertion order inside contiguity")
line("block-rord", "uniform-sorted", "contiguity, order differs (rand vs sorted) -- see note in results")
line("block-rord", "uniform", "contiguity + random order vs uniform")
line("block", "uniform-sorted", "contiguity at equal (sorted) order")
line("wrap", "block", "block's start distribution / edge effect")
line("block", "uniform", "headline")

print("\n== mid-run (iterations 1000-3000) mutation descriptors, pooled over runs ==")
print(f"{'arm':15s} ident%  plateau%  worse%  better%  disp(pos)  KT/maxKT  rem-cost  span  evals/mut")
for a in data:
    g = pd.concat([data[a][r] for r in runs]); g = g[(g.op >= 0) & (g.itr >= 1000) & (g.itr < 3000)]
    c = g.cls.value_counts(normalize=True) * 100
    ch = g[g.cls != 0]
    ktn = (ch.kt[ch.kt >= 0].mean() / (n * (n - 1) / 2)) if (ch.kt >= 0).any() else float("nan")
    print(f"{a:15s} {c.get(0,0):6.1f} {c.get(1,0):8.1f} {c.get(2,0):7.1f} {c.get(3,0):8.2f}  {ch.disp.mean():8.2f}  {ktn:8.4f}  {g.rem_cost.mean():8.3f}  {g.span.mean():6.1f}  {g.dcalls.mean():7.0f}")
print("(disp/KT are over non-identical offspring only; KT normalised by n(n-1)/2; rem-cost = mean sum of position costs of the removed groups)")

print("\n== TEST 4 rule: does a mix beat block? (100% budget, vs block; negative = mix better) ==")
for a in ["mix:0.25", "mix:0.5", "mix:0.75"]:
    if a in data and "block" in data:
        pct, W, L, p, ma, mb = cmp(a, "block", 1.0)
        print(f"  {a:9s} vs block: {pct:+.2f}%  W{W}/L{L} p={p:.3f}   (mix mean {ma:.2f}, block mean {mb:.2f})")

# ---- per-state evidence: strict-improvement rate per 1000 evals by (u bin, budget quarter)
def cells_for(arms_ops):
    """arms_ops: list of (arm, op or None). Returns per-run arrays strict[ubin,q], evals[ubin,q], gain[ubin,q] for each unit."""
    out = []
    for a, op in arms_ops:
        for r in runs:
            g = data[a][r]; g = g[g.op >= 0]
            if op is not None: g = g[g.op == op]
            full = data[a][r]; tot_e = full.dcalls.sum(); cum = (np.cumsum(data[a][r].dcalls.values) )
            # budget quarter from the mutation's own start eval over the full run total
            q = np.minimum((g.evals.values / tot_e * 4).astype(int), 3)
            ub = np.minimum((g.noimprv.values / 100.0 * 4).astype(int), 3)
            S = np.zeros((4, 4)); E = np.zeros((4, 4)); G = np.zeros((4, 4))
            st = g.strict.values == 1
            for i in range(4):
                for j in range(4):
                    m = (ub == i) & (q == j)
                    S[i, j] = st[m].sum(); E[i, j] = g.dcalls.values[m].sum(); G[i, j] = (g.f_par.values[m] - g.f_off.values[m])[st[m]].sum()
            out.append((S, E, G))
    return out

def rate(units, idx):
    S = sum(units[i][0] for i in idx); E = sum(units[i][1] for i in idx)
    with np.errstate(divide="ignore", invalid="ignore"): return 1000 * S / E, S, E

rng = np.random.default_rng(12345)
def state_table(title, a_units, b_units, la, lb):
    print(f"\n== {title}: strict-improvement rate per 1000 evals, {la} minus {lb}; rows u=noimprv/100 quartile, cols budget quarter ==")
    na, nb = len(a_units), len(b_units)
    ra, Sa, Ea = rate(a_units, range(na)); rb, Sb, Eb = rate(b_units, range(nb))
    diff = ra - rb
    # bootstrap over run indices (paired when both lists are aligned by run)
    nb_boot = 1000; boots = np.zeros((nb_boot, 4, 4))
    for k in range(nb_boot):
        ia = rng.integers(0, na, na); ib = rng.integers(0, nb, nb)
        boots[k] = rate(a_units, ia)[0] - rate(b_units, ib)[0]
    valid = (Sa >= 30) & (Sb >= 30)
    signs = set(); sig_cells = []
    print("          " + "  ".join(f"Q{j+1:<28d}" for j in range(4)))
    for i in range(4):
        row = []
        for j in range(4):
            if not valid[i, j]: row.append(f"{'(n<30 strict)':28s}"); continue
            lo, hi = np.nanpercentile(boots[:, i, j], [5, 95]); sig = (lo > 0) or (hi < 0)
            if sig: sig_cells.append((i, j, np.sign(diff[i, j])))
            row.append(f"{diff[i,j]:+7.3f} [{lo:+.3f},{hi:+.3f}]{'*' if sig else ' '} {int(Sa[i,j]):4d}/{int(Sb[i,j]):4d}")
        print(f"  u-bin {i} " + "  ".join(row))
    sg = {s for _, _, s in sig_cells}
    print(f"  cells with 90% interval excluding 0: {len(sig_cells)}; signs present: {sorted(sg)} -> "
          + ("STATE-DEPENDENT PREFERENCE (rule satisfied)" if len(sig_cells) >= 2 and len(sg) >= 2 else "no state-dependent sign flip under the pre-registered rule"))
    print(f"  overall rate: {la} {1000*Sa.sum()/Ea.sum():.4f}  {lb} {1000*Sb.sum()/Eb.sum():.4f}   (cell entries 'a/b' = strict-improvement counts)")

if "uniform" in data and "block" in data:
    ua = cells_for([("block", None)]); ub_ = cells_for([("uniform", None)])
    state_table("PURE arms", ua, ub_, "block", "uniform")
mixes = [m for m in ["mix:0.25", "mix:0.5", "mix:0.75"] if m in data]
if mixes:
    ma = cells_for([(m, 3) for m in mixes]); mb = cells_for([(m, 0) for m in mixes])
    state_table("MIXED arms, per-operator rows pooled over mix arms (operator used per mutation)", ma, mb, "block", "uniform")
