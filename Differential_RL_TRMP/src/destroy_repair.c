/* Destroy-and-repair mutation. Body lifted verbatim from pert_d() in es_pre_sfFIN.c.
 * Changes: (1) kappa is a parameter instead of the global `d`; (2) a `policy` hook marks where
 * the destroy selection will be replaced (Stage R2). With POLICY_UNIFORM the sequence of rand()
 * calls and every output is identical to the baseline. */
#include "trmp.h"

int effective_kappa(int kappa)   /* the clamping pert_d applies, exposed for logging */
{
  int dd = kappa, hd = (int)(grp/2);
  if (dd > hd) dd = (int)(grp*0.5);
  if (dd < 1) dd = 1;
  return dd;
}

/* [R2] history cost of each position: the part of D(S_{i-1}, g_i) caused by sensors whose current
 * orientation was set by a DISTANT predecessor, i.e. the last group that contained sensor s sits at
 * a position <= i-2 inside the permutation (the initial state g0 is not counted as a predecessor).
 * These are the multi-predecessor dependencies unique to TRMP. Returns the total cost.
 * No eval accounting and no rand(): it is learning/diagnostic overhead, not search budget. */
double history_costs(const int *ind, double *h)
{
  int i, j, s, lastpos[MMAX]; double st[MMAX], f, c, tot = 0;
  for (s = 0; s < sen; ++s) { st[s] = init_ang[s]; lastpos[s] = -1; }
  for (i = 0; i < grp; ++i) {
    c = 0;
    for (j = 0; j < nact[ind[i]]; ++j) {
      s = act[ind[i]][j];
      f = fabs(st[s] - wt[ind[i]][s]); f = (f <= PI) ? f : TOPI - f;
      if (lastpos[s] >= 0 && lastpos[s] <= i - 2) c += f;
      tot += f; st[s] = wt[ind[i]][s]; lastpos[s] = i;
    }
    h[i] = c;
  }
  return tot;
}

/* [R2] choose `dd` distinct positions to remove. Weighted policies sample WITHOUT replacement with
 * probability proportional to weight (+tiny epsilon so zero-weight positions stay reachable and an
 * all-zero weight vector degenerates to uniform). Output sel[] in ascending position order for block,
 * draw order otherwise. */
static void select_positions(const int *a, int dd, int policy, int *sel)
{
  double w[COVMAX], tot, r, acc; int i, k, used[COVMAX];
  if (policy == POLICY_BLOCK) {
    int s0 = (int)(u01 * (grp - dd + 1));
    for (k = 0; k < dd; ++k) sel[k] = s0 + k;
    return;
  }
  if (policy == POLICY_COST_GREEDY) position_costs(a, w);
  else history_costs(a, w);
  for (i = 0; i < grp; ++i) { w[i] += 1e-9; used[i] = 0; }
  for (k = 0; k < dd; ++k) {
    tot = 0; for (i = 0; i < grp; ++i) if (!used[i]) tot += w[i];
    r = u01 * tot; acc = 0; sel[k] = -1;
    for (i = 0; i < grp; ++i) { if (used[i]) continue; acc += w[i]; if (r < acc) { sel[k] = i; break; } }
    if (sel[k] < 0) for (i = grp - 1; i >= 0; --i) if (!used[i]) { sel[k] = i; break; }
    used[sel[k]] = 1;
  }
}

double pert_d(int *a, int kappa, int policy)
{
    int i,j,nu=grp,z,dd=kappa,k,r,mxind1=0,x,dd1=1,hd; // taking d from #define d
    int tgt[COVMAX], seq[COVMAX],sub[zl],rem[COVMAX];
    int index[COVMAX],temp[COVMAX][COVMAX];
    double tempcost[COVMAX],record1;
    
     pert_cnt++;
    if(policy<POLICY_UNIFORM || policy>POLICY_BLOCK){ fprintf(stderr,"unknown destroy policy %d\n",policy); exit(2); }
    hd=(int)(grp/2);// hd is half of grp value
    if(dd>hd)
    {
        
        dd=(int)(grp*0.5);
                
    }
 if(dd<1)
   dd=1;
    
    
    for(i=0;i<grp;++i)
    {
        seq[i]=tgt[i]=a[i];
        index[tgt[i]]=i;
    }

    
    if(policy==POLICY_UNIFORM)
    {
    for(i=0;i<dd;++i) // loop chooses d random element in array
    {
      z=(int)(u01*nu);

      sub[i]=seq[z];
      tgt[index[seq[z]]]=-404;// to represent this element has to remove
      nu--;
      seq[z]=seq[nu];
    }
    }
    else   /* [R2] non-uniform destroy selection; repair below is unchanged */
    {
      int sel[COVMAX];
      select_positions(a,dd,policy,sel);
      for(i=0;i<dd;++i){ sub[i]=a[sel[i]]; tgt[sel[i]]=-404; }
    }

    for(i=0,j=0;i<grp;i++,j++)// sub array after removing d elements
    {
		if(tgt[i]==-404)
			{
			j--;
			}
		else
			{
			rem[j]=tgt[i];// sub array after removing d elements
			}
    }


//////////////////////////////////////////////////////////////////////////////////////////
	dd1=(grp-dd);
	x=dd;
	for(r=0;r<dd;r++)// replace 1 by d
	{
	  dd1++;// increasing dd(d) by 1 to insert 1 element from sub array to rem array
	  x--;
	  record1=1e20; // every time record1 is reinitiated
	//r=0;
		for(i=0;i<dd1;++i)
		{
			 for(j=0,k=0;j<dd1;++j,++k)
			 {
				  if(i==j)
				  {
				  temp[i][j]=sub[r];
				   k--;
				  }
				  else
				  temp[i][j]=rem[k];
			 }
			tempcost[i]=findcost_d(&temp[i][0],x);

			if(record1-tempcost[i]>=ACC)
					{
						record1=tempcost[i];
						mxind1=i;
					}
		}
	
	for(i=0;i<dd1;++i)
	rem[i]=temp[mxind1][i];
	

	}

	for(i=0;i<grp;++i)
	{
	 mutant[i]=rem[i];
	}
	
return(record1);


}
