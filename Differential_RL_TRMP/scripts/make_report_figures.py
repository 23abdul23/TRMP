"""Figures for docs/TRMP_RL_Project_Report.pdf. Numbers for fig7/fig8 are copied from docs/OPTION_B_RESULTS.md,
docs/OPTION_A_RESULTS.md and docs/TEST34_RESULTS.md (equal-evaluation best at 100% budget, % vs uniform kappa=4)."""
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
src=open('scripts/compare_full.py').read().split("print(\"negative")[0]; exec(src)   # builds dataframe d
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
G,R,B,K='#1b7837','#d6604d','#4575b4','#777777'
# fig6: full protocol per instance, grouped strip plot
fig,ax=plt.subplots(figsize=(8.6,4.3)); col={'2pi/3':'#4575b4','pi/2':'#1b7837','pi/3':'#d6604d'}
groups=[(1,50,'n ≤ 50\n(21 inst.)'),(51,100,'50 < n ≤ 100\n(10 inst.)'),(101,199,'100 < n < 200\n(5 inst.)'),(200,200,'n = 200\n(9 inst.)'),(400,400,'n = 400\n(15 inst.)')]
rng=np.random.default_rng(1)
for i,(lo,hi,lab) in enumerate(groups):
    g=d[(d.n>=lo)&(d.n<=hi)]
    for a_,c in col.items():
        s_=g[g.ap==a_]; ax.scatter(i+rng.uniform(-.22,.22,len(s_)),s_.d_avg,s=30,color=c,alpha=.9,edgecolor='white',linewidth=.5,label=f'aperture {a_.replace("pi","π")}' if i==0 else None)
    m=g.d_avg.mean(); ax.hlines(m,i-.33,i+.33,color='k',lw=2.2); ax.text(i+.36,m,f'{m:+.2f}%',va='center',fontsize=9.5,fontweight='bold')
ax.axhline(0,color='#444',lw=.8); ax.set_xticks(range(len(groups))); ax.set_xticklabels([g[2] for g in groups]); ax.set_xlim(-.6,4.9)
ax.set_ylabel('change in 20-run mean vs published ES-TRMP (%)\nnegative = better'); ax.set_ylim(-3.5,1.0)
ax.set_title('Contiguous destroy vs original ES-TRMP on all 60 instances (black bar = group mean)',fontsize=10); ax.legend(frameon=False,loc='lower left')
fig.tight_layout(); fig.savefig('docs/figures/fig6_full_protocol.png',dpi=170); plt.close()
# fig7: RL vs controls
fig,axs=plt.subplots(1,3,figsize=(11.2,3.9))
data={'n=100 (10 runs)':[('fixed κ=2',-0.442,K),('random κ',-0.485,K),('RL differential',-0.474,R),('RL discounted',-1.101,R),('block (no learning)',-0.97,G)],
      'n=198 (10 runs)':[('fixed κ=2',-0.007,K),('random κ',0.133,K),('RL differential',-0.149,R),('RL discounted',-0.054,R),('block (no learning)',-1.79,G)],
      'n=400 (3 runs; block 5)':[('fixed κ=2',-0.740,K),('RL differential',-0.252,R),('block (no learning)',-2.66,G)]}
for ax,(t,rows) in zip(axs,data.items()):
    y=np.arange(len(rows))[::-1]; ax.barh(y,[r[1] for r in rows],color=[r[2] for r in rows]); ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows])
    for yy,r in zip(y,rows): ax.text(r[1]+(-0.05 if r[1]<0 else 0.05),yy,f'{r[1]:+.2f}',va='center',ha='right' if r[1]<0 else 'left',fontsize=8.5)
    ax.axvline(0,color='#444',lw=.8); ax.set_title(t,fontsize=10); ax.set_xlim(-3.3,0.7); ax.set_xlabel('% vs uniform κ=4 (equal evaluations)')
fig.suptitle('RL (red) does not beat its κ-only controls (grey); the non-learning block operator (green) does',fontsize=10.5)
fig.tight_layout(); fig.savefig('docs/figures/fig7_rl_vs_controls.png',dpi=170); plt.close()
# fig8: attribution at n=198
rows=[('uniform κ=2 (control)',-0.007,K),('random κ (control)',0.133,K),('RL discounted γ=0.9',-0.054,R),('RL differential',-0.149,R),('uniform, sorted reinsertion',0.10,K),
      ('mix 25% block',-1.10,G),('mix 50% block',-1.13,G),('mix 75% block',-1.35,G),('wrap-around block',-1.56,G),('block, random reinsertion',-1.61,G),('block (contiguous destroy)',-1.79,G)]
fig,ax=plt.subplots(figsize=(8.2,4.6)); y=np.arange(len(rows))[::-1]
ax.barh(y,[r[1] for r in rows],color=[r[2] for r in rows]); ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows])
for yy,r in zip(y,rows): ax.text(r[1]+(-0.04 if r[1]<0 else 0.04),yy,f'{r[1]:+.2f}',va='center',ha='right' if r[1]<0 else 'left',fontsize=9)
ax.axvline(0,color='#444',lw=.8); ax.set_xlim(-2.2,0.5); ax.set_xlabel('best-so-far at equal evaluations, % vs uniform κ=4\n(n=198, 10 paired runs; negative = better; grey = controls, red = RL, green = contiguous removal)')
ax.set_title('n=198: learning arms ≈ 0, contiguous-removal arms ≈ −1.1 … −1.8 %',fontsize=10.5); fig.tight_layout()
fig.savefig('docs/figures/fig8_attribution_n198.png',dpi=170); plt.close(); print('ok')
