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

double pert_d(int *a, int kappa, int policy)
{
    int i,j,nu=grp,z,dd=kappa,k,r,mxind1=0,x,dd1=1,hd; // taking d from #define d
    int tgt[COVMAX], seq[COVMAX],sub[zl],rem[COVMAX];
    int index[COVMAX],temp[COVMAX][COVMAX];
    double tempcost[COVMAX],record1;
    
     pert_cnt++;
    if(policy!=POLICY_UNIFORM){ fprintf(stderr,"destroy policy %d not implemented\n",policy); exit(2); }
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

    
    for(i=0;i<dd;++i) // loop chooses d random element in array
    {
      z=(int)(u01*nu);
      
      sub[i]=seq[z];
      tgt[index[seq[z]]]=-404;// to represent this element has to remove
      nu--;
      seq[z]=seq[nu];
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
