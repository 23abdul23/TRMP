"""Figures for docs/OPTION_C_WRITEUP.md. Reads fixed-kappa diagnostic logs (read-only) and writes PNGs.
usage: make_figures_optionC.py <p1_dir> <p1b_dir> <noop_dir> <outdir>
Sources: n=100 (10 runs) and n=400 (3 runs) from p1; n=198 (10 runs) from p1b; no-op measurement from noop_dir.
"""
import sys, glob, re, collections
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

p1, p1b, noop, out = sys.argv[1:5]
KS = [2, 4, 6, 8]
SIZES = [("n=100", p1, "covers_dirn100m060r150s06i03", "10 runs"),
         ("n=198", p1b, "covers_dirn200m120r150s06i00", "10 runs"),
         ("n=400", p1, "covers_dirn400m240r150s06i00", "3 runs")]
COL = {2: "#1b7837", 4: "#2166ac", 6: "#d6604d", 8: "#762a83"}


def load(d, inst, k):
    ev = collections.defaultdict(list)
    for line in open(f"{d}/{inst}.k{k}.log"):
        t = line.split()
        if t[0] == "M":
            ev[int(t[1])].append((0, int(t[2]), int(t[3]), float(t[4]), float(t[5]), int(t[6]), int(t[7]), int(t[8])))
        elif t[0] == "S":
            ev[int(t[1])].append((1, int(t[2]), int(t[3]), float(t[4]), float(t[5]), int(t[6]), 1, 0))
    return {r: np.array(e, float) for r, e in ev.items() if sum(1 for x in e if x[0] == 0) == 4000}


def curve(e):
    cum = np.cumsum(e[:, 5])
    best = np.minimum.accumulate(np.minimum(e[:, 3], np.where(e[:, 6] == 1, e[:, 4], 1e30)))
    return cum, best


data = {(s[0], k): load(s[1], s[2], k) for s in SIZES for k in KS}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# ---- Fig 1: offspring outcome fractions vs kappa (mid-run) ----
fig, ax = plt.subplots(3, 3, figsize=(9, 7), sharex=True)
for j, s in enumerate(SIZES):
    tie, bet, wor = [], [], []
    for k in KS:
        a = np.vstack([e[e[:, 0] == 0] for e in data[(s[0], k)].values()])
        a = a[(a[:, 1] >= 1000) & (a[:, 1] < 3000)]
        fp, fo = a[:, 3], a[:, 4]
        t = np.abs(fo - fp) < 1e-7
        tie.append(100 * t.mean()); bet.append(100 * ((fo < fp) & ~t).mean()); wor.append(100 * ((fo > fp) & ~t).mean())
    ax[0, j].plot(KS, tie, "o-", color="#444"); ax[0, j].set_ylim(75, 100); ax[0, j].set_title(f"{s[0]} ({s[3]})")
    ax[1, j].plot(KS, wor, "o-", color="#d6604d"); ax[1, j].set_ylim(bottom=0)
    ax[2, j].plot(KS, bet, "o-", color="#1b7837"); ax[2, j].set_ylim(0, 4); ax[2, j].set_xticks(KS)
    ax[2, j].set_xlabel("destruction size $\\kappa$")
ax[0, 0].set_ylabel("offspring cost = parent (%)"); ax[1, 0].set_ylabel("offspring worse (%)"); ax[2, 0].set_ylabel("offspring better (%)")
fig.suptitle("Mid-run (iterations 1000-3000) offspring vs parent, uniform destroy", y=0.99)
fig.tight_layout(); fig.savefig(f"{out}/fig1_outcomes_vs_kappa.png", dpi=150); plt.close(fig)

# ---- Fig 2: evaluations per mutation vs kappa ----
fig, ax = plt.subplots(figsize=(4.8, 3.6))
for s, mk in zip(SIZES, "osD"):
    y = []
    for k in KS:
        a = np.vstack([e[e[:, 0] == 0] for e in data[(s[0], k)].values()])
        y.append(a[:, 5].mean())
    ax.plot(KS, y, mk + "-", label=s[0])
ax.set_yscale("log"); ax.set_xticks(KS); ax.set_xlabel("destruction size $\\kappa$"); ax.set_ylabel("candidate evaluations per mutation")
ax.legend(frameon=False); fig.tight_layout(); fig.savefig(f"{out}/fig2_evals_per_mutation.png", dpi=150); plt.close(fig)

# ---- Fig 3: equal-evaluation best-so-far relative to kappa=4 ----
fig, ax = plt.subplots(1, 3, figsize=(11, 3.4), sharey=False)
grid = np.linspace(0.05, 1.0, 60)
for j, s in enumerate(SIZES):
    runs = sorted(set.intersection(*[set(data[(s[0], k)]) for k in KS]))
    rel = {k: [] for k in KS}
    for r in runs:
        Bs = min(curve(data[(s[0], k)][r])[0][-1] for k in KS)
        base = None
        vals = {}
        for k in KS:
            cum, best = curve(data[(s[0], k)][r])
            idx = np.clip(np.searchsorted(cum, grid * Bs, side="right") - 1, 0, None)
            vals[k] = best[idx]
        for k in KS:
            rel[k].append(100 * (vals[k] - vals[4]) / vals[4])   # paired difference to kappa=4, same run & budget
    for k in KS:
        m = np.mean(rel[k], 0); lo = np.min(rel[k], 0); hi = np.max(rel[k], 0)
        ax[j].plot(grid, m, color=COL[k], label=f"$\\kappa$={k}")
        ax[j].fill_between(grid, lo, hi, color=COL[k], alpha=0.12)
    ax[j].axhline(0, color="k", lw=0.5); ax[j].set_title(f"{s[0]} ({len(runs)} paired runs)")
    ax[j].set_xlabel("fraction of common evaluation budget B*")
ax[0].set_ylabel("best-so-far minus $\\kappa$=4 (%), mean and min-max")
ax[0].legend(frameon=False, fontsize=8); fig.tight_layout(); fig.savefig(f"{out}/fig3_equal_budget_best.png", dpi=150); plt.close(fig)

# ---- Fig 4: gain per 1000 evals by budget quarter ----
fig, ax = plt.subplots(1, 3, figsize=(11, 3.4))
for j, s in enumerate(SIZES):
    for i, k in enumerate(KS):
        g = np.zeros(4); n = np.zeros(4)
        for e in data[(s[0], k)].values():
            m = e[:, 0] == 0; cum = np.cumsum(e[:, 5]); tot = cum[-1]
            gain = np.where(m & (e[:, 7] == 1), e[:, 3] - e[:, 4], 0.0) / e[0, 3] * 100
            q = np.minimum((cum / tot * 4).astype(int), 3)
            for b in range(4): g[b] += gain[q == b].sum(); n[b] += e[q == b, 5].sum()
        ax[j].bar(np.arange(4) + (i - 1.5) * 0.2, 1000 * g / np.maximum(n, 1), 0.2, color=COL[k], label=f"$\\kappa$={k}")
    ax[j].set_yscale("log"); ax[j].set_xticks(range(4)); ax[j].set_xticklabels(["Q1", "Q2", "Q3", "Q4"]); ax[j].set_title(s[0])
ax[0].set_ylabel("strict gain per 1000 evals (% of start cost)"); ax[0].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(f"{out}/fig4_gain_per_1000_evals.png", dpi=150); plt.close(fig)

# ---- Fig 5: no-op decomposition (only if the measurement exists) ----
rows = []
for inst, lab in [("covers_dirn100m060r150s06i03", "n=100"), ("covers_dirn200m120r150s06i00", "n=198")]:
    for k in (2, 4, 8):
        fn = f"{noop}/{inst}.k{k}.log"
        try:
            L = [l.split() for l in open(fn) if l.startswith("M") and len(l.split()) == 10]
        except OSError:
            continue
        a = np.array([[float(x) for x in t[1:]] for t in L])       # trn itr ke fp fo dcalls acc strict same
        a = a[(a[:, 1] >= 1000) & (a[:, 1] < 3000)]
        tie = np.abs(a[:, 4] - a[:, 3]) < 1e-7
        same = a[:, 8] == 1
        rows.append((lab, k, tie.mean() * 100, (tie & same).mean() * 100, (tie & ~same).mean() * 100, (a[same, 5].sum() / a[:, 5].sum()) * 100))
if rows:
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    x = np.arange(len(rows))
    ax.bar(x, [r[3] for r in rows], color="#444", label="identical permutation (true no-op)")
    ax.bar(x, [r[4] for r in rows], bottom=[r[3] for r in rows], color="#bbb", label="different permutation, equal cost (plateau)")
    ax.set_xticks(x); ax.set_xticklabels([f"{r[0]}\n$\\kappa$={r[1]}" for r in rows]); ax.set_ylabel("% of mutations (iterations 1000-3000)")
    ax.set_ylim(0, 105); ax.legend(frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=1); fig.tight_layout()
    fig.savefig(f"{out}/fig5_noop_decomposition.png", dpi=150); plt.close(fig)
    print("noop rows (label, k, tie%, identical%, plateau%, eval-share-identical%):")
    for r in rows: print(r[0], r[1], *[f"{v:.1f}" for v in r[2:]])
print("figures written")
