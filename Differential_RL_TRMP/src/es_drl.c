/* ES-TRMP driver with evaluation accounting and optional state/iteration logging.
 *
 * Modes (Phase 2): only `baseline` -- the published ES-TRMP loop (eta=100, delta ladder,
 * kappa fixed). Logic of the main loop is transcribed from es_pre_sfFIN.c lines 115-255;
 * RNG call order is unchanged (srand(run+1) per run; the baseline's CLI seed is dead code and
 * is deliberately NOT reproduced as a seed -- see docs/DECISION.md).
 * Logging never touches rand(), so enabling it cannot change the search.
 */
#include "trmp.h"
#include <string.h>

#define MAXRUNS 50
#define WIN 50          /* w, window of the recent-success-rate feature (paper sec. 17.2) */
#define ETA 100         /* baseline stagnation threshold */

static int cmp_desc(const void *a, const void *b){ double x=*(double*)a,y=*(double*)b; return (x<y)-(x>y); }

static double zeta_of(const int *perm)   /* share of f from worst 10% positions */
{
  static double pc[COVMAX], srt[COVMAX]; int i,k;
  double tot=position_costs(perm,pc), s=0;
  for(i=0;i<grp;++i) srt[i]=pc[i];
  qsort(srt,grp,sizeof(double),cmp_desc);
  k=(int)ceil(0.1*grp); if(k<1)k=1;
  for(i=0;i<k;++i) s+=srt[i];
  return tot>0? s/tot : 0.0;
}

int main(int argc, char **argv)
{
  const char *inst=NULL,*initf="init_state.dat",*mode="baseline",*resout=NULL,*runscsv=NULL,
             *iterlog=NULL,*statelog=NULL;
  int nruns=20,kappa0=4,maxit=4000,i,trn,policy=POLICY_UNIFORM,ismix=0; double mixp=0; const char *mutlog=NULL;
  for(i=1;i<argc;++i){
    if(!strcmp(argv[i],"--instance")) inst=argv[++i];
    else if(!strcmp(argv[i],"--init")) initf=argv[++i];
    else if(!strcmp(argv[i],"--mode")) mode=argv[++i];
    else if(!strcmp(argv[i],"--out")) resout=argv[++i];
    else if(!strcmp(argv[i],"--runs")) nruns=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--kappa")) kappa0=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--iters")) maxit=atoi(argv[++i]);
    else if(!strcmp(argv[i],"--runs-csv")) runscsv=argv[++i];
    else if(!strcmp(argv[i],"--iter-log")) iterlog=argv[++i];
    else if(!strcmp(argv[i],"--state-log")) statelog=argv[++i];
    else if(!strcmp(argv[i],"--mut-log")) mutlog=argv[++i];
    else if(!strcmp(argv[i],"--policy")){ i++;
      if(!strncmp(argv[i],"mix:",4)){ mixp=atof(argv[i]+4); policy=POLICY_BLOCK; ismix=1; }   /* [T4] block w.p. p else uniform */
      else if(!strcmp(argv[i],"block-rord")) policy=POLICY_BLOCK_RORD;                          /* [T3] controls */
      else if(!strcmp(argv[i],"uniform-sorted")) policy=POLICY_UNIF_SORTED;
      else if(!strcmp(argv[i],"wrap")) policy=POLICY_WRAP;
      else if(!strcmp(argv[i],"uniform")) policy=POLICY_UNIFORM; else if(!strcmp(argv[i],"cost-greedy")) policy=POLICY_COST_GREEDY;
      else if(!strcmp(argv[i],"history-aware")) policy=POLICY_HISTORY; else if(!strcmp(argv[i],"block")) policy=POLICY_BLOCK;
      else { fprintf(stderr,"unknown policy %s\n",argv[i]); return 1; } }
    else { fprintf(stderr,"unknown arg %s\n",argv[i]); return 1; }
  }
  if(!inst||nruns<1||nruns>MAXRUNS){ fprintf(stderr,"usage: es_drl --instance F [--mode baseline] [--out F] [--runs N<=50] [--kappa K] [--iters N] [--runs-csv F] [--iter-log F] [--state-log F] [--init F]\n"); return 1; }
  if(strcmp(mode,"baseline")){ fprintf(stderr,"mode %s not implemented yet\n",mode); return 1; }
  if(load_instance(inst,initf)) return 1;

  FILE *fo=resout?fopen(resout,"a"):NULL, *fr=NULL, *fi=iterlog?fopen(iterlog,"w"):NULL, *fs=statelog?fopen(statelog,"w"):NULL, *fm=mutlog?fopen(mutlog,"w"):NULL;
  if(runscsv){ fr=fopen(runscsv,"a"); if(fr&&ftell(fr)==0)
    fprintf(fr,"instance,n,run,best,best_iter,iters,shuffles,pp_calls,evals_calls,evals_units,acc_strict,acc_tie,wall_s\n"); }
  if(fm) fprintf(fm,"run,itr,op,noimprv,evals,f_par,f_off,dcalls,acc,strict,cls,disp,kt,rem_cost,span\n");
  if(fs) fprintf(fs,"run,itr,evals_calls,u,beta,psi_strict,psi_acc,theta,zeta\n");

  double valt[MAXRUNS],vtm[MAXRUNS],vit_mut[MAXRUNS],best=1e9,av=0,avt=0,avit_mut=0,sd=0,sdt=0,sdit_mut=0;

  for(trn=0;trn<nruns;++trn)
  {
    clock_t t0=clock();
    srand(trn+1);
    int SPOP=20, pop_size=SPOP;
    if(grp<4) pop_size=grp;
    int itr=0,bnc_mut=0,noimprv=0,shk_cnt=0,d=kappa0, xdf;
    long long acc_strict=0,acc_tie=0;
    double mut_cost,shake_cost;
    ind_maxc=pert_cnt=0; record_min=record=1e20; mut_cost=shake_cost=1e20;

    long long c_pre=eval_calls, u_pre=eval_units;
    init_pop1(pop_size);
    long long pp_calls=eval_calls-c_pre;
    long long e_start=eval_calls, u_start=eval_units;

    int minrec[COVMAX], j;
    char win[WIN]; int wpos=0,wcnt=0,wsum_s=0,wsum_a=0; char win_a[WIN];
    memset(win,0,sizeof win); memset(win_a,0,sizeof win_a);
    double zeta=0; int zvalid=0;
    unsigned long long xs=0x9E3779B97F4A7C15ULL*(unsigned long long)(trn+1)+1ULL; /* [T4] private RNG (xorshift64*), never touches rand() */
    int parent[COVMAX], pos_p[COVMAX], pos_o[COVMAX];

    while(itr<maxit)
    {
      long long e0=eval_calls; double fp=record;
      if(fs){
        if(!zvalid){ zeta=zeta_of(rec); zvalid=1; }
        double u=(double)noimprv/ETA, beta=(double)itr/maxit,
               ps=wcnt?(double)wsum_s/wcnt:0, pa=wcnt?(double)wsum_a/wcnt:0,
               th=(record-record_min)/(record_min>0?record_min:1);
        fprintf(fs,"%d,%d,%lld,%.4f,%.4f,%.4f,%.4f,%.6f,%.4f\n",trn,itr,e0-e_start,u,beta,ps,pa,th,zeta);
      }
      int pol=policy;
      if(ismix){ xs^=xs>>12; xs^=xs<<25; xs^=xs>>27; double rr=(double)((xs*2685821657736338717ULL)>>11)/9007199254740992.0; pol=(rr<mixp)?POLICY_BLOCK:POLICY_UNIFORM; }
      if(fm){ diag_removed=1; for(i=0;i<grp;++i) parent[i]=rec[i]; }
      mut_cost=pert_d(rec,d,pol);   /* shuffle below stays uniform (baseline) */
      diag_removed=0;
      xdf=isequal(record,mut_cost);
      int strict=((record-mut_cost)>=ACC), accepted=(strict||xdf);
      if(fi) fprintf(fi,"M %d %d %d %.6f %.6f %lld %d %d\n",trn,itr,effective_kappa(d),fp,mut_cost,eval_calls-e0,accepted,strict);
      if(fm){   /* [T3] per-mutation diagnostics: class, displacement, Kendall-tau distance, removed-set cost */
        int cls, same=1; double disp=0; long kt=-1;
        for(i=0;i<grp;++i){ if(mutant[i]!=parent[i]){ same=0; break; } }
        if(same) cls=0; else if(fabs(mut_cost-fp)<1e-7) cls=1; else if(mut_cost>fp) cls=2; else cls=3;
        if(!same){
          for(i=0;i<grp;++i){ pos_p[parent[i]]=i; pos_o[mutant[i]]=i; }
          for(i=0;i<grp;++i) disp+=abs(pos_p[i]-pos_o[i]);
          disp/=grp;
          if(grp<=250){ kt=0; for(i=0;i<grp;++i) for(j=i+1;j<grp;++j){ int a=mutant[i],b=mutant[j]; if(pos_p[a]>pos_p[b]) kt++; } }
        }
        fprintf(fm,"%d,%d,%d,%d,%lld,%.6f,%.6f,%lld,%d,%d,%d,%.4f,%ld,%.4f,%d\n",trn,itr,pol,noimprv,e0-e_start,fp,mut_cost,eval_calls-e0,accepted,strict,cls,disp,kt,last_removed_cost,last_span);
      }
      /* window bookkeeping (log only) */
      if(wcnt==WIN){ wsum_s-=win[wpos]; wsum_a-=win_a[wpos]; } else wcnt++;
      win[wpos]=strict; win_a[wpos]=accepted; wsum_s+=strict; wsum_a+=accepted; wpos=(wpos+1)%WIN;

      if(accepted)  // if trial cost is minimum
      {
        butimer_mut=clock();
        if(xdf==0) noimprv=0;
        if(strict) acc_strict++; else acc_tie++;
        record=mut_cost;
        for(i=0;i<grp;++i) rec[i]=mutant[i];
        zvalid=0;
      }
      if((record_min-record)>=ACC)
      {
        record_min=record; bnc_mut=itr;
        for(i=0;i<grp;++i) minrec[i]=rec[i];
      }
      if(noimprv>=ETA)
      {
        long long es=eval_calls;
        noimprv=0; shk_cnt++;
        if(grp>=200) d=40; else if(grp>100) d=20; else if(grp>50) d=10; else d=(int)(grp/7);
        if(d<=4) d=4;
        shake_cost=pert_d(rec,d,POLICY_UNIFORM);   // SHUFFLING
        if(fi) fprintf(fi,"S %d %d %d %.6f %.6f %lld\n",trn,itr,effective_kappa(d),record,shake_cost,eval_calls-es);
        if(fm) fprintf(fm,"%d,%d,-1,%d,%lld,%.6f,%.6f,%lld,1,0,-1,0,-1,0,0\n",trn,itr,noimprv,es-e_start,record,shake_cost,eval_calls-es);
        d=kappa0;
        record=shake_cost; zvalid=0;
        for(i=0;i<grp;++i) rec[i]=mutant[i];
        if((record_min-record)>=ACC){ record_min=record; for(i=0;i<grp;++i) minrec[i]=rec[i]; }
      }
      noimprv++; itr++;
    }
    (void)j; (void)shake_cost; (void)u_pre;
    double utime=(double)(clock()-t0)/CLOCKS_PER_SEC;
    valt[trn]=record_min; vtm[trn]=utime; vit_mut[trn]=bnc_mut;
    av+=record_min; avt+=utime; avit_mut+=bnc_mut;
    if((best-record_min)>=ACC) best=record_min;
    if(fr) fprintf(fr,"%s,%d,%d,%.6f,%d,%d,%d,%lld,%lld,%lld,%lld,%lld,%.3f\n",inst,grp,trn,record_min,bnc_mut,itr,shk_cnt,
                   pp_calls,eval_calls-e_start,eval_units-u_start,acc_strict,acc_tie,utime);
  }
  av/=nruns; avt/=nruns; avit_mut/=nruns;
  for(i=0;i<nruns;++i){ sd+=(valt[i]-av)*(valt[i]-av); sdt+=(vtm[i]-avt)*(vtm[i]-avt); sdit_mut+=(vit_mut[i]-avit_mut)*(vit_mut[i]-avit_mut); }
  sd=sqrt(sd/nruns); sdt=sqrt(sdt/nruns); sdit_mut=sqrt(sdit_mut/nruns);
  /* same row format as the baseline results file */
  FILE *out=fo?fo:stdout;
  fprintf(out,"%s\t%d\t%.3lf\t%.3lf\t%.3lf\t%.3lf\t%.3lf\t%.3lf\t%.3lf\n",inst,grp,best,av,sd,avt,sdt,avit_mut,sdit_mut);
  if(fo) fclose(fo); if(fr) fclose(fr); if(fi) fclose(fi); if(fs) fclose(fs); if(fm) fclose(fm);
  return 0;
}
