"""Test 1 + 2 analysis (see docs/TEST12_RULES.md). Run from Differential_RL_TRMP/ with the project venv.
usage: analyze_t12.py [out/t12]
Equal-evaluation method as scripts/analyze_a.py: best-so-far at 25/50/100 % of B* (smallest eval total among compared arms, per run).
Negative % = better than control.
"""
import sys, os, re, collections
import numpy as np
from scipy.stats import wilcoxon

D = sys.argv[1] if len(sys.argv) > 1 else "out/t12"

def load(fn):
    ev = collections.defaultdict(list)
    for line in open(fn):
        t = line.split()
        if t[0] == "M":
            ev[int(t[1])].append((0, float(t[4]), float(t[5]), int(t[6]), int(t[7])))
        elif t[0] == "S":
            ev[int(t[1])].append((1, float(t[4]), float(t[5]), int(t[6]), 1))
    out = {}
    for r, e in ev.items():
        if sum(1 for x in e if x[0] == 0) == 4000:
            a = np.array(e, dtype=float)
            cum = np.cumsum(a[:, 3]); best = np.minimum.accumulate(np.minimum(a[:, 1], np.where(a[:, 4] == 1, a[:, 2], 1e30)))
            out[r] = (cum, best)
    return out

def arm(inst, pol, k):
    fn = f"{D}/covers_{inst}.{pol}.k{k}.log"
    if not os.path.exists(f"{D}/covers_{inst}.{pol}.k{k}.done"): return None
    return load(fn)

def best_at(c, B):
    cum, best = c; i = np.searchsorted(cum, B, side="right") - 1
    return best[max(i, 0)]

def pw(v, base):
    if len(v) < 5 or not np.any(v != base): return float("nan")
    try: return wilcoxon(v, base).pvalue
    except Exception: return float("nan")

def compare(arms, ctrl):
    """arms: dict label->{run:curve}. returns {frac: {label: (values array)}} over common runs, plus runs"""
    runs = sorted(set.intersection(*[set(d) for d in arms.values()]))
    res = {}
    for frac in (0.25, 0.5, 1.0):
        vals = {l: [] for l in arms}
        for r in runs:
            B = min(d[r][0][-1] for d in arms.values()) * frac
            for l, d in arms.items(): vals[l].append(best_at(d[r], B))
        res[frac] = {l: np.array(v) for l, v in vals.items()}
    return runs, res

def fmt_table(title, arms, ctrl):
    runs, res = compare(arms, ctrl)
    print(f"\n{title}   paired runs={len(runs)}")
    for frac in (0.25, 0.5, 1.0):
        base = res[frac][ctrl]; cells = []
        for l, v in res[frac].items():
            if l == ctrl: cells.append(f"{l}: {v.mean():9.2f}"); continue
            pct = 100 * (v.mean() - base.mean()) / base.mean()
            cells.append(f"{l}: {v.mean():9.2f} ({pct:+.2f}% W{int((v<base-1e-9).sum())}/L{int((v>base+1e-9).sum())} p={pw(v,base):.3f})")
        print(f"  B*x{frac:<4} " + " | ".join(cells))
    return runs, res

groups = {
    "n~100": ["dirn100m060r150s03i03", "dirn100m060r150s04i02", "dirn100m060r150s06i04"],
    "n~200": ["dirn200m120r150s03i03", "dirn200m120r150s04i01", "dirn200m120r150s06i01"],
    "n=400": ["dirn400m240r150s03i00", "dirn400m240r150s04i00", "dirn400m240r150s06i01"],
}
print("=== TEST 1: block(k=4) vs uniform(k=4), equal evaluations ===")
verdicts = {}
for g, insts in groups.items():
    per = []; pooled = []
    for inst in insts:
        u, b = arm(inst, "uniform", 4), arm(inst, "block", 4)
        if u is None or b is None: print(f"\n{g} {inst}: not finished"); continue
        runs, res = fmt_table(f"{g}  {inst}", {"uniform": u, "block": b}, "uniform")
        v, base = res[1.0]["block"], res[1.0]["uniform"]
        pct = 100 * (v - base) / base
        per.append(dict(inst=inst, mean_pct=100 * (v.mean() - base.mean()) / base.mean(), better=v.mean() < base.mean(),
                        p=pw(v, base), sig_worse=(pw(v, base) < 0.05 and v.mean() > base.mean()), n=len(runs)))
        pooled += list(pct)
    if not per: continue
    mean_gain = np.mean([x["mean_pct"] for x in per]); nb = sum(x["better"] for x in per)
    ps = wilcoxon(pooled).pvalue if len(pooled) >= 5 and np.any(np.array(pooled) != 0) else float("nan")
    rule = (len(per) == 3) and nb >= 2 and not any(x["sig_worse"] for x in per) and mean_gain <= -0.5
    verdicts[g] = rule
    print(f"\n  >> {g}: instances finished={len(per)}/3, block better on {nb}; mean per-instance diff {mean_gain:+.2f}%; "
          f"pooled per-run Wilcoxon p={ps:.4f} (n={len(pooled)}, exploratory); any significantly worse: {any(x['sig_worse'] for x in per)}; "
          f"RULE 'generalises' = {rule}")
print("\nTest-1 rule outcome per size:", verdicts)

print("\n\n=== TEST 2: kappa sweep ===")
for inst in ["dirn200m120r150s06i00", "dirn400m240r150s04i00"]:
    arms = {}
    for pol, ks in (("uniform", (4, 2)), ("block", (2, 4, 6, 8, 12))):
        for k in ks:
            a = arm(inst, pol, k)
            if a is not None: arms[f"{pol[:4]}{k}"] = a
    if "unif4" not in arms or len(arms) < 2: print(f"\n{inst}: not enough finished arms"); continue
    fmt_table(f"{inst} (all arms, B* = smallest total among ALL arms)", arms, "unif4")
    # pairwise vs the better uniform
    runs, res = compare(arms, "unif4")
    r1 = res[1.0]
    best_unif = min([l for l in r1 if l.startswith("unif")], key=lambda l: r1[l].mean())
    best_block = min([l for l in r1 if l.startswith("bloc")], key=lambda l: r1[l].mean(), default=None)
    if best_block:
        d = 100 * (r1[best_block].mean() - r1[best_unif].mean()) / r1[best_unif].mean()
        wl = f"W{int((r1[best_block]<r1[best_unif]-1e-9).sum())}/L{int((r1[best_block]>r1[best_unif]+1e-9).sum())}"
        d4 = 100 * (r1[best_block].mean() - r1.get("bloc4", r1[best_block]).mean()) / r1.get("bloc4", r1[best_block]).mean()
        print(f"  >> best block = {best_block}, best uniform = {best_unif}: {d:+.2f}% {wl} p={pw(r1[best_block], r1[best_unif]):.3f}; "
              f"best block vs block4 = {d4:+.2f}%")
    if "bloc4" in r1:
        v, u = r1["bloc4"], r1[best_unif]
        print(f"  bloc4 vs best uniform ({best_unif}) @100%: {100*(v.mean()-u.mean())/u.mean():+.2f}% W{int((v<u-1e-9).sum())}/L{int((v>u+1e-9).sum())} p={pw(v,u):.3f}")
        for l in r1:
            if l.startswith("bloc") and l != "bloc4":
                v, b4 = r1[l], r1["bloc4"]
                print(f"  {l} vs bloc4 @100%: {100*(v.mean()-b4.mean())/b4.mean():+.2f}% W{int((v<b4-1e-9).sum())}/L{int((v>b4+1e-9).sum())} p={pw(v,b4):.3f}")
    print("  total evals per run (mean) by arm:", {l: int(np.mean([d[r][0][-1] for r in runs])) for l, d in arms.items()})
