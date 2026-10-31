"""Generate src/diag_es.c from the untouched baseline: adds an evaluation-call counter,
a fixed-kappa CLI option and a per-mutation log. No algorithmic change."""
import re,sys
s=open('es_pre_sfFIN.c').read()
def rep(old,new,cnt=1):
    global s
    assert s.count(old)==cnt,(old,s.count(old))
    s=s.replace(old,new)
rep("clock_t utimer,butimer_mut;","long long eval_calls=0; int fixed_kappa=4,nruns=20; FILE *dlog=NULL;\nclock_t utimer,butimer_mut;")
rep("double findcost_d(int *ind,int sub) // sub is element to remove=d //F\n{\nint i,j;","double findcost_d(int *ind,int sub) // sub is element to remove=d //F\n{\neval_calls++;\nint i,j;")
rep("if(argc != 4)","if(argc < 4)")
rep("  outfile=fopen(argv[3],\"a\");","  fixed_kappa=argc>4?atoi(argv[4]):4; nruns=argc>5?atoi(argv[5]):20; dlog=argc>6?fopen(argv[6],\"w\"):NULL;\n  outfile=fopen(argv[3],\"a\");")
rep("for(trn=0;trn<tit;++trn)","for(trn=0;trn<nruns;++trn)")
rep("\td=4;\n\n\t//***************initialization pop","\td=fixed_kappa;\n\n\t//***************initialization pop")
rep("\t\tmut_cost=pert_d(rec);\n\t\txdf=isequal(record,mut_cost);",
"""\t\t\t{ long long e0=eval_calls; double fp=record; int ke=d; if(ke>grp/2) ke=grp/2; if(ke<1) ke=1;
\t\tmut_cost=pert_d(rec);
\t\txdf=isequal(record,mut_cost);
\t\t\tif(dlog) fprintf(dlog,"M %d %d %d %.6f %.6f %lld %d %d\\n",trn,itr,ke,fp,mut_cost,eval_calls-e0,(int)(((record-mut_cost)>=ACC)||xdf),(int)((record-mut_cost)>=ACC)); }""")
rep("\t\t\td=4; //setting d again to 4","\t\t\td=fixed_kappa; //setting d again")
rep("shake_cost=pert_d(rec); //SHUFFLING","{ long long e0=eval_calls; shake_cost=pert_d(rec); if(dlog) fprintf(dlog,\"S %d %d %d %.6f %.6f %lld\\n\",trn,itr,d,record,shake_cost,eval_calls-e0); } //SHUFFLING")
rep("valt[trn]=record_min; // saving best of every run","valt[trn]=record_min; if(dlog) fprintf(dlog,\"R %d %.6f %lld %.3f\\n\",trn,record_min,eval_calls,(double)(clock()-utimer)/CLOCKS_PER_SEC); eval_calls=0;")
open('src/diag_es.c','w').write(s)
