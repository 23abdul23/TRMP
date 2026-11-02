"""Per-run paired comparison of `block` (out/full_block/*.csv) vs same-session `uniform` (out/same_session/*.csv).
Pairing: run r uses srand(r+1) in both arms => identical pre-processed start, then trajectories diverge.
Also verifies the same-session uniform mean equals the reference ES-TRMP row (results_ESapproach.ods)."""
import glob, os, re, numpy as np, pandas as pd
from scipy.stats import wilcoxon
rng = np.random.default_rng(0)
ref = pd.read_excel('results_ESapproach.ods', engine='odf', sheet_name='Sheet1')
ref.columns = ['inst','n','best','avg','sd','time','sdtime','bg','sbg']; ref['inst']=ref.inst.str.replace('.dat','',regex=False)
rows=[]; per={}
for f in sorted(glob.glob('out/same_session/*.csv')):
    b = os.path.basename(f)[:-4]; g = f'out/full_block/{b}.csv'
    if not os.path.exists(g) or not os.path.exists(f'out/same_session/{b}.row'): continue
    u = pd.read_csv(f).sort_values('run'); k = pd.read_csv(g).sort_values('run')
    if len(u)!=20 or len(k)!=20: continue
    ub, kb = u.best.values, k.best.values; pct = 100*(kb-ub)/ub
    r = ref[ref.inst==b].iloc[0]; n=int(u.n.iloc[0])
    p = wilcoxon(kb,ub).pvalue if np.any(kb!=ub) else 1.0
    per[b]=pct
    rows.append(dict(inst=b,n=n,ap=re.search(r's(0[346])i',b).group(1),uni_mean=ub.mean(),blk_mean=kb.mean(),
        ref_mean=r.avg, uni_eq_ref=abs(ub.mean()-r.avg)<1e-3, d_pct=pct.mean(), W=int((kb<ub-1e-9).sum()), T=int((np.abs(kb-ub)<=1e-9).sum()),
        L=int((kb>ub+1e-9).sum()), p=p, sd_u=ub.std(), sd_b=kb.std(), dz=pct.mean()/pct.std(ddof=1) if pct.std(ddof=1)>0 else np.nan))
d=pd.DataFrame(rows).sort_values(['n','inst']).reset_index(drop=True)
if d.empty: print('no complete pairs yet'); raise SystemExit
# Holm across instances
order=np.argsort(d.p.values); m=len(d); holm=np.empty(m); run=0
for i,idx in enumerate(order): run=max(run,(m-i)*d.p.values[idx]); holm[idx]=min(1,run)
d['p_holm']=holm
pd.set_option('display.width',200)
print(f"{len(d)} instances with 20 paired runs. negative % = block better. Same-session uniform == reference mean on {int(d.uni_eq_ref.sum())}/{len(d)} instances.\n")
print(d[['inst','n','uni_mean','blk_mean','d_pct','W','T','L','p','p_holm','sd_u','sd_b','dz']].round(3).to_string(index=False))
def boot(vals_by_inst):
    out=[]
    for _ in range(4000):
        insts=rng.integers(0,len(vals_by_inst),len(vals_by_inst))
        out.append(np.mean([rng.choice(vals_by_inst[i],len(vals_by_inst[i])).mean() for i in insts]))
    return np.percentile(out,[2.5,97.5])
print("\n== pooled (cluster bootstrap over instances then runs; Wilcoxon over instance means) ==")
for name,sel in [('n~100',d.n<=100),('n~200 (198-200)',(d.n>=198)&(d.n<=200)),('n=400',d.n==400),('n>=198',d.n>=198),('all subset',d.n>0)]:
    s=d[sel]
    if len(s)==0: continue
    lo,hi=boot([per[i] for i in s.inst])
    pw=wilcoxon(s.blk_mean,s.uni_mean).pvalue if len(s)>=6 else float('nan')
    allr=np.concatenate([per[i] for i in s.inst])
    print(f"{name:16s} instances={len(s):2d}  mean %diff={s.d_pct.mean():+6.2f}  95% CI [{lo:+.2f},{hi:+.2f}]  runs better={int((allr<0).sum())}/{len(allr)}  Wilcoxon(instance means) p={pw:.4f}")
print(f"\nSD ratio (block/uniform), median over n>=198 instances: {np.median((d.sd_b/d.sd_u)[d.n>=198]):.2f}")
