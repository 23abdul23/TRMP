"""Compare out/phase0/*.txt (our rebuild of the baseline) with results_ESapproach.ods Sheet1 (reference)."""
import glob, os, pandas as pd, numpy as np
ref = pd.read_excel('results_ESapproach.ods', engine='odf', sheet_name='Sheet1')
ref.columns = ['inst','n','best','avg','sd','time','sdtime','bestgen','sdbestgen']
ref['inst'] = ref['inst'].str.replace('.dat','',regex=False)
rows=[]
for f in sorted(glob.glob('out/phase0/*.txt')):
    t=open(f).read().split()
    if len(t)<9: continue
    rows.append(dict(inst=os.path.basename(t[0]).replace('.dat',''),n=int(t[1]),best=float(t[2]),avg=float(t[3]),sd=float(t[4]),time=float(t[5]),bestgen=float(t[7]),sdbestgen=float(t[8])))
new=pd.DataFrame(rows).merge(ref,on='inst',suffixes=('','_ref'))
for c in ['best','avg','sd','bestgen','sdbestgen']: new[c+'_d']=(new[c]-new[c+'_ref']).abs()
exact=(new[[c+'_d' for c in ['best','avg','sd','bestgen','sdbestgen']]].max(axis=1)<1e-3)
print(f"instances compared: {len(new)}   exact match (all of best/avg/SD/best-iter mean+SD within 1e-3): {int(exact.sum())}")
print(new.loc[~exact,['inst','n','best','best_ref','avg','avg_ref','sd','sd_ref','bestgen','bestgen_ref']].to_string(index=False))
print(f"\nmean time/instance: ours {new['time'].mean():.2f}s vs reference {new['time_ref'].mean():.2f}s (hardware differs; contention from parallel jobs inflates ours)")
