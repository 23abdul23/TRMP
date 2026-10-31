/* Lifted verbatim from es_pre_sfFIN.c (Srivastava & Singh, 2018 ES-TRMP) except where marked
 * [instr] (evaluation counters) or [new] (load_instance, position_costs). */
#include "trmp.h"

int sen, grp, initpop_count, opp_count, ind_maxc, pert_cnt;
double record = 1e20, record_min = 1e20, init_ang[MMAX], wt[COVMAX][MMAX], cost[SPO];
int act[COVMAX][MMAX], nact[COVMAX], pop[SPO][COVMAX];
int rec[COVMAX], mutant[COVMAX];
clock_t butimer_mut;
long long eval_calls = 0, eval_units = 0;   /* [instr] */

/* [new] same parsing as baseline main(), lines 70-106 */
int load_instance(const char *instfile, const char *initfile)
{
  FILE *infile, *f2; int i, j, zz; double xx;
  infile = fopen(instfile, "r");
  if (!infile) { fprintf(stderr, "unable to open instance %s\n", instfile); return 1; }
  if (fscanf(infile, "%d%d%d%lf", &sen, &zz, &grp, &xx) != 4) return 1;
  for (i = 0; i < grp; ++i) {
    nact[i] = 0;
    for (j = 0; j < sen; ++j) {
      if (fscanf(infile, "%lf", &wt[i][j]) != 1) return 1;
      if (wt[i][j] < 7) act[i][nact[i]++] = j;
    }
  }
  fclose(infile);
  f2 = fopen(initfile, "r");
  if (!f2) { fprintf(stderr, "unable to read init angle file %s\n", initfile); return 1; }
  if (fscanf(f2, "%d", &i) != 1 || i < sen) { fprintf(stderr, "insufficient initial angles\n"); return 1; }
  for (j = 0; j < sen; ++j) if (fscanf(f2, "%lf", &init_ang[j]) != 1) return 1;
  fclose(f2);
  return 0;
}

//-----------------------------initpop_neh--------------------------------
void init_pop1(int popsize)
{
    int i,j,mxind=0,nu,k,u[COVMAX],tmp[COVMAX],c; //mxind is pop element who having min cost value
    double cst=0;
    int opp_pop[COVMAX],lb,ub,chk;
    double opp_popcst,popcst;
    record=1e20;
    ind_maxc =0;
    initpop_count=opp_count=0;
    
    
    
    //______________________________
    if((grp%2)==0)
    chk=(grp/2);
    else
    chk=((int)(grp/2)+1);
    
    //__________________________________
    
    for(i=0;i<popsize;++i)
    {
		initpop_count++;
        nu=grp;
        for(j=0;j<grp;++j)
        {
            u[j]=j;
        }
        for(j=0;j<grp;++j)
        {
            k=(int)(u01*nu);
            pop[i][j]=u[k];
            nu--;
            u[k]=u[nu];
        }
        //----------------temp holding before neh pop-------------
        for(c=0;c<grp;++c)
        tmp[c]=pop[i][c];
        
        
        for(lb=0,ub=(grp-1);lb<chk;++lb,--ub)
			{
				 if(lb%2==0)
				 {			 
				 opp_pop[lb]=pop[i][ub];
				 opp_pop[ub]=pop[i][lb];
				 }
				 else
				 {
				 opp_pop[lb]=pop[i][lb];
				 opp_pop[ub]=pop[i][ub];
				 }
			 	
			}
        //****************************rmve end**********
       
        
        
        //tmp_cst=findcost(&pop[i][0]);
        //------------------------------
        
        //------------fun neh begin---------
			popcst=fun_neh(pop[i]);									//cost[i]=fun_neh(pop[i]);
			opp_popcst=fun_neh(opp_pop);
        //------------fun neh end---------
        
        
        if((popcst-opp_popcst)>=ACC)
        {
			cost[i]=opp_popcst;
			for(c=0;c<grp;++c)
			pop[i][c]=opp_pop[c];
			opp_count++;
	    }
	    else
	    {
				cost[i]=popcst;
		}
     // cost[i]=findcost(&pop[i][0]);
      
        if (!unique(pop[i],cost[i],i-1))
        {
			//pert_d(pop[i]);
			for(c=0;c<grp;++c)
			pop[i][c]=tmp[c];
			
			cost[i]=findcost(&pop[i][0]);
				 
			if (!unique(pop[i],cost[i],i-1))
			{
			i--;
			continue;
			}
			
        }
        
       if(record-cost[i]>=ACC)
        {
            butimer_mut=clock();
            record=cost[i];
            record_min=record;
            mxind=i;
        }
        if (cst<=cost[i])
        {
             ind_maxc=i;
             cst=cost[i];
        }
    }
    //printf("\n mxind is ->%d\n",mxind);


    for(i=0;i<grp;++i)
    rec[i]=pop[mxind][i];
    printf("min record in init_pop is %lf\n",record);

}

//------------------------------fun_neh-------------
double fun_neh(int *a)
{
    int f1[2],f2[2],hold[grp],temp[COVMAX][COVMAX];
    int i,j,k,dd1,dd,r,x,mxind1,ll=(grp-2);
    double f1_cst,f2_cst,record1,tempcost[COVMAX];

    if(grp==1)
    {
	return (findcost(a));	
	}
	
    for(i=0,j=1;i<2;++i,--j)
    {
        f1[i]=a[i];
        f2[i]=a[j];
    }
    
	
    f1_cst=findcost_d(f1,ll);
    
    f2_cst=findcost_d(f2,ll);
    if((f1_cst-f2_cst)>=ACC)
    {
        for(i=0;i<2;++i)
        hold[i]=f2[i];
    }
    else
    {
        for(i=0;i<2;++i)
        hold[i]=f1[i];
    }


    //---------------------
    dd=(grp-2);// dd means how many element to insert
    dd1=2;  //(grp-dd); // dd1 means how many element hv already inserted
	x=dd; // grp =7 x=5
	for(r=2;r<grp;r++) //for(r=0;r<dd;r++)
	{
	  dd1++;// increasing dd(d) by 1 to insert 1 element from a array to hold array
	  x--;
	  record1=1e20; // every time record1 is reinitiated
	//r=0;
		for(i=0;i<dd1;++i)
		{
		 for(j=0,k=0;j<dd1;++j,++k)
		 {
		  if(i==j)
		  {
		  temp[i][j]=a[r];
		   k--;
		  }
		  else
		  temp[i][j]=hold[k];
		 }
		tempcost[i]=findcost_d(&temp[i][0],x);

		if(record1-tempcost[i]>=ACC)
				{
					//printf("\n itr[%d]\t rec-tmpcst %lf \n",i,record1-tempcost[i]);
					record1=tempcost[i];
					mxind1=i;
				}
		}
	for(i=0;i<dd1;++i)
	hold[i]=temp[mxind1][i];

	}
		//------------------------
		for(i=0;i<grp;++i)
		{
		 a[i]=hold[i];
		}
		return (record1);
}

double findcost(int *ind) //F
{
int i,j;
double currstate [MMAX],csts=0, f;

    for(i=0;i<sen;++i)
    {
      currstate[i]=init_ang[i];
    }

    for(i=0;i<grp;i++)
    {
      for(j=0;j<nact[ind[i]];++j)
      {
        f=fabs(currstate[act[ind[i]][j]]-wt[ind[i]][act[ind[i]][j]]);
         if(f<=PI)
          csts+=f;
         else
           csts+=TOPI-f;

        if(f>TOPI) printf("error f>TOPI\n");
        currstate[act[ind[i]][j]]=wt [ind[i]][act[ind[i]][j]];
      }

    }
    return csts;
}

//_________________________________findcost_d______________________
double findcost_d(int *ind,int sub) // sub is element to remove=d //F
{
eval_calls++; eval_units += (grp-sub); /* [instr] */
int i,j;
double currstate [MMAX],csts=0, f;
for(i=0;i<sen;++i)
{
currstate[i]=init_ang[i];
}

for(i=0;i<(grp-sub);i++) // sub becoz of passing rem as arg in findcost
{
  for(j=0;j<nact[ind[i]];++j)
    {
      f=fabs(currstate[act[ind[i]][j]]-wt[ind[i]][act[ind[i]][j]]);
       if(f<=PI)
        csts+=f;
       else
         csts+=TOPI-f;
        if(f>TOPI) printf("error f>TOPI\n");
        currstate[act[ind[i]][j]]=wt [ind[i]][act[ind[i]][j]];
    }

}
return csts;
}

int isequal(double a, double b)
{
	double dif_csts;
	dif_csts=a-b;
	if(dif_csts<ACC)
	dif_csts=-dif_csts;
	if(dif_csts>ACC)
	return 0;
	else
	return 1;
}

int unique(int * ind, double csts,int indx) //F
{
 int i,j,fl;
double dx;

    for(i=0;i<indx;++i)
    {
        dx=csts-cost[i];
         if(dx<0)
          dx=-dx;
         if(dx>ACC)
            continue;

        fl=0;
        for(j=0;j<grp;++j)
        {
            if(ind[j]!=pop[i][j])
            {
                fl=1;
                break;
            }
        }
       if(fl==0)
        {
            return(0);
        }
    }
return(1);
}

/* [new] mirrors findcost() but records each position's contribution. No eval accounting:
 * state extraction is learning overhead and is not charged to the search budget. */
double position_costs(const int *ind, double *pc)
{
  int i, j; double currstate[MMAX], csts = 0, f, c;
  for (i = 0; i < sen; ++i) currstate[i] = init_ang[i];
  for (i = 0; i < grp; i++) {
    c = 0;
    for (j = 0; j < nact[ind[i]]; ++j) {
      f = fabs(currstate[act[ind[i]][j]] - wt[ind[i]][act[ind[i]][j]]);
      c += (f <= PI) ? f : TOPI - f;
      currstate[act[ind[i]][j]] = wt[ind[i]][act[ind[i]][j]];
    }
    pc[i] = c; csts += c;
  }
  return csts;
}
