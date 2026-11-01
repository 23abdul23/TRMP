"""Full-protocol comparison: `--policy block` (out/full_block/*.row, 20 runs, 4000 iters) vs the reference
ES-TRMP rows in results_ESapproach.ods Sheet1 (reproduced exactly by our rebuild, see DECISION.md section 2/9).
Instance-level paired Wilcoxon on the 20-run mean (and best); exploratory subgroups by n and aperture."""
import glob, os, re, numpy as np, pandas as pd
from scipy.stats import wilcoxon
ref = pd.read_excel('results_ESapproach.ods', engine='odf', sheet_name='Sheet1')
ref.columns = ['inst','n','best','avg','sd','time','sdtime','bestgen','sdbestgen']
ref['inst'] = ref['inst'].str.replace('.dat','',regex=False)
rows=[]
for f in sorted(glob.glob('out/full_block/*.row')):
    t=open(f).read().split()
    if len(t)<9: continue
    rows.append(dict(inst=os.path.basename(t[0]).replace('.dat',''),n_=int(t[1]),best_b=float(t[2]),avg_b=float(t[3]),sd_b=float(t[4]),time_b=float(t[5])))
d=pd.DataFrame(rows).merge(ref,on='inst')
if d.empty: print('no finished instances yet'); raise SystemExit
d['ap']=d.inst.str.extract(r's(0[346])i')[0].map({'03':'2pi/3','04':'pi/2','06':'pi/3'})
d['d_avg']=100*(d.avg_b-d.avg)/d.avg            # negative = block better
d['d_best']=100*(d.best_b-d.best)/d.best
d['sd_ratio']=np.where(d.sd>0, d.sd_b/d.sd, np.nan)
def summ(g,name):
    if len(g)==0: return
    w=int((g.avg_b<g.avg-1e-3).sum()); l=int((g.avg_b>g.avg+1e-3).sum()); t=len(g)-w-l
    p=''
    nz=g[(g.avg_b-g.avg).abs()>1e-3]
    if len(nz)>=6:
        p=f" Wilcoxon(mean) p={wilcoxon(nz.avg_b,nz.avg).pvalue:.4f}"
    print(f"{name:28s} k={len(g):2d}  mean %diff(avg)={g.d_avg.mean():+6.2f}  median={g.d_avg.median():+6.2f}  best %diff={g.d_best.mean():+6.2f}  W/T/L={w}/{t}/{l}  SD ratio(med)={np.nanmedian(g.sd_ratio) if g.sd_ratio.notna().any() else float('nan'):.2f}{p}")
print("negative % = block better than published ES-TRMP (same 4000 iterations, 20 runs, seeds 1..20)\n")
summ(d,'all finished')
for lo,hi,nm in [(1,50,'n<=50'),(51,100,'50<n<=100'),(101,199,'100<n<200'),(200,200,'n=200'),(201,401,'n=400')]:
    summ(d[(d.n>=lo)&(d.n<=hi)],nm)
summ(d[d.n>=198],'n>=198 (headline)')
for a in ['2pi/3','pi/2','pi/3']: summ(d[(d.n>=198)&(d.ap==a)],f'n>=198, phi={a}')
print()
print(d.sort_values(['n','inst'])[['inst','n','avg','avg_b','d_avg','best','best_b','d_best','sd','sd_b']].round(3).to_string(index=False))
