"""fig9: block-kappa sweep at equal evaluations (paired by run vs block kappa=4). Run from Differential_RL_TRMP/:
.venv/bin/python ../RM-Report/scripts/make_ksweep_figure.py  (reads out/ksweep and out/full_block; writes RM-Report/figures/fig9_kappa_sweep.png)"""
import glob, os, re, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
rng=np.random.default_rng(0); pct={}; ninst={}
for f in glob.glob('out/ksweep/*.k*.csv'):
    m=re.match(r'.*/(covers_[^.]+)\.k(\d+)\.csv',f); inst,k=m.group(1),int(m.group(2))
    if not os.path.exists(f'out/ksweep/{inst}.k{k}.row'): continue
    d=pd.read_csv(f).sort_values('run'); b=pd.read_csv(f'out/full_block/{inst}.csv').sort_values('run').iloc[:len(d)]
    pct[(inst,k)]=100*(d.best.values-b.best.values)/b.best.values; ninst[inst]=int(d.n.iloc[0])
def boot(vals):
    o=[np.mean([rng.choice(vals[i],len(vals[i])).mean() for i in rng.integers(0,len(vals),len(vals))]) for _ in range(3000)]
    return np.percentile(o,[2.5,97.5])
ks=sorted({k for _,k in pct}); groups={'n ≈ 200 (4 instances, 40 runs)':[i for i in ninst if ninst[i]<=200],'n = 400 (3 instances, 24 runs)':[i for i in ninst if ninst[i]==400]}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(figsize=(7.6,4.2)); col=['#4575b4','#d6604d']
for (name,insts),c,off in zip(groups.items(),col,(-0.12,0.12)):
    xs=[4]+ks; ys=[0.0]; lo=[0.0]; hi=[0.0]
    for k in ks:
        v=[pct[(i,k)] for i in insts]; mu=np.mean([x.mean() for x in v]); l,h=boot(v); ys.append(mu); lo.append(mu-l); hi.append(h-mu)
    order=np.argsort(xs); xs=np.array(xs)[order]; ys=np.array(ys)[order]; lo=np.array(lo)[order]; hi=np.array(hi)[order]
    xp=np.arange(len(xs))+off
    ax.errorbar(xp,ys,yerr=[lo,hi],fmt='-o',color=c,capsize=3,label=name)
ax.axhline(0,color='#444',lw=.8); ax.set_xticks(range(len(ks)+1)); ax.set_xticklabels([str(k) for k in sorted([4]+ks)])
ax.set_xlabel('block destruction size κ (κ = 4 is the reference)'); ax.set_ylabel('change vs block κ=4 at equal evaluations (%)\nnegative = better')
ax.set_title('Block destroy: effect of the destruction size κ (95% bootstrap CI)',fontsize=10.5); ax.legend(frameon=False,loc='lower left')
fig.tight_layout(); fig.savefig('../RM-Report/figures/fig9_kappa_sweep.png',dpi=170); print('ok')
