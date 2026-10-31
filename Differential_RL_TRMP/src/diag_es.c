# include<stdio.h>
# include<stdlib.h>
# include<math.h>
# include<sys/types.h>
# include<time.h>

# define u01 ((double) rand()/(RAND_MAX+1.0))
# define COVMAX 701 // total group
# define MMAX 502 //no. of sensors
# define PI 3.1415926
# define TOPI 6.2831852
# define ACC 1e-7
# define SPO 50
# define tit 20 // total no. of run
# define zl 100

long long eval_calls=0; int fixed_kappa=4,nruns=20; FILE *dlog=NULL;
clock_t utimer,butimer_mut;
double utime,butime_mut;
int initpop_count,opp_count;
int SPOP;
int maxit;
//_______________________
int d;
int pert_cnt,replace_cnt,noimprv;
//______________________
int sen,grp,pop_size;
int ind_maxc;// ind_maxc holding index of max element in pop
double record=1e20,record_min=1e20; // record is holding the minimum cost
double init_ang[MMAX];
int act[COVMAX][MMAX],nact[COVMAX], pop[SPO][COVMAX];
double wt[COVMAX][MMAX], cost[SPO];
int rec[COVMAX],minrec[COVMAX]; // rec is having best element from pop
int best_pop[COVMAX];
int mutant[COVMAX];// mutant individual

double mut_cost,shake_cost;
double findcost(int *);
double findcost_d(int *,int);
void init_pop1(int);
int unique(int *,double,int);
double fun_neh(int *a);
double pert_d(int *a);
int isequal(double a, double b);



//_______________________main begin______________________________________
int main(int argc, char * argv[])
{
  FILE *infile, *initfile, *outfile;
  int seed1,i,zz,j,trn,itr=0;
 
  double xx,best=1e9;
  double valt[50],vtm[50],bvtm_mut[50];
  double av=0,avt=0,avit=0,avit_mut=0,sd,sdit,sdt,sdit_mut;
  
  int vit[50],vit_mut[50],bnc_mut=0;
  
  
  int xdf,shk_cnt;
  


  if(argc < 4)
  {
    printf("argument error: seed input output\n");
     exit(1);
  }

  infile=fopen(argv[2],"r");
   if(infile==NULL)
   {
    printf("unable to open input file\n");
     exit(1);
    }

  fscanf(infile,"%d%d%d%lf",&sen,&zz,&grp,&xx); //reading sensor,group from instance file
   printf("\ngroup is %d\tand sensor is %d\n\n",grp,sen);

    for(i=0;i<grp;++i) // initialization act and nact array
    {
    nact[i]=0;
     for(j=0;j<sen;++j)
      {
        fscanf(infile,"%lf",&wt[i][j]);
        if(wt[i][j]<7)
        act[i][nact[i]++]=j;
      }
    }
// initialization of sensor angle i.e. s0
initfile=fopen("init_state.dat","r");
if(initfile==NULL)
{
printf("unable to read init angle file\n");
exit(1);
}
fscanf(initfile,"%d",&i);
if(i<sen)
{
printf("\a\n insufficient number of initial angle\n");
exit(1);
}
for(j=0;j<sen;++j)
{
fscanf(initfile,"%lf",&init_ang[j]); //reading initial angle in init array
}

  fixed_kappa=argc>4?atoi(argv[4]):4; nruns=argc>5?atoi(argv[5]):20; dlog=argc>6?fopen(argv[6],"w"):NULL;
  outfile=fopen(argv[3],"a");
  fflush(stdout);
  seed1=atoi(argv[1]);
  srand(seed1);
// -----------------------generation begins----------------/////////////////////////////////////


for(trn=(argc>7?atoi(argv[7]):0);trn<nruns;++trn)//tit must be less than 50 as vtm vit are 50 only
{
	utimer=clock();
    srand(trn+1);

	SPOP=20;
	maxit=4000;

	pop_size=SPOP;
	
	if(grp<4)
  	pop_size=grp; 
	
	printf("pop_size is %d\n",pop_size);
 
	itr=bnc_mut=ind_maxc=pert_cnt=noimprv=replace_cnt=shk_cnt=0;
	record_min=record=1e20;//reinitialising record in every iteration
	mut_cost=shake_cost=1e20;
	d=fixed_kappa;

	//***************initialization pop**********//
	init_pop1(pop_size);
	

//---------******************----------------run begin------------****************----------------------------

	while((itr<maxit))
	{
		 
			{ long long e0=eval_calls; double fp=record; int ke=d; if(ke>grp/2) ke=grp/2; if(ke<1) ke=1;
		mut_cost=pert_d(rec);
		xdf=isequal(record,mut_cost);
			if(dlog) fprintf(dlog,"M %d %d %d %.6f %.6f %lld %d %d\n",trn,itr,ke,fp,mut_cost,eval_calls-e0,(int)(((record-mut_cost)>=ACC)||xdf),(int)((record-mut_cost)>=ACC)); }
				
		if(((record-mut_cost)>=ACC) || (xdf==1)) // if trial cost is minimum
		{
			butimer_mut=clock();
					
			if(xdf==0)
			{
				noimprv=0;
			}

			record=mut_cost;// inserting cost of trial with the minimum cost

			for(i=0;i<grp;++i)// swapping trial with best population
			{
			   rec[i]=mutant[i];
			}

		}
		//________________________________
	 
		//________________________holding min_______________________ 
		if((record_min-record)>=ACC)
		{
			record_min=record;
			replace_cnt++;	
			bnc_mut=itr;	
			for(i=0;i<grp;++i)// swapping trial with best population
			{
			  minrec[i]=rec[i];
			}
		}
		//________________________holding min end_______________________	
			  
		if(noimprv>=100)
		{
			noimprv=0;
			shk_cnt++;
			if(grp>=200)
			d=40;
			else if(grp>100)
			d=20;
			else if(grp>50)
			d=10;
			else
			d=(int)(grp/7);
			
			if(d<=4)
			d=4;
				
			{ long long e0=eval_calls; shake_cost=pert_d(rec); if(dlog) fprintf(dlog,"S %d %d %d %.6f %.6f %lld\n",trn,itr,d,record,shake_cost,eval_calls-e0); } //SHUFFLING
			printf("shake d %d\t, shake cost %lf\t,earlier record %lf\n",d,shake_cost,record);
			
			d=fixed_kappa; //setting d again
			
			record=shake_cost;
				
			for(i=0;i<grp;++i)// swapping shuffled pop with best population
			{
			  rec[i]=mutant[i];
			}
				  
			//________________________holding min_______________________ 
			if((record_min-record)>=ACC)
			{
			 record_min=record;
				
				for(i=0;i<grp;++i)// swapping trial with best population
				{
					minrec[i]=rec[i];
				}
			}
			//________________________holding min end_______________________	 
				 
		}

		noimprv++;	
		itr++;
	}

	//---------******************----------------run terminated------------****************----------------------------

printf("d is %d\tpert_cnt %d\t replace_cnt %d\t shk_cnt %d\n",d,pert_cnt,replace_cnt,shk_cnt);
printf("\n  bnc_mut is %d\n",bnc_mut);

butime_mut=(double)(butimer_mut-utimer)/CLOCKS_PER_SEC;
utime=(double)(clock()-utimer)/CLOCKS_PER_SEC;

fflush(stdin);

valt[trn]=record_min; if(dlog) fprintf(dlog,"R %d %.6f %lld %.3f\n",trn,record_min,eval_calls,(double)(clock()-utimer)/CLOCKS_PER_SEC); eval_calls=0;
vtm[trn]=utime; // saving user time for every run
bvtm_mut[trn]=butime_mut;  // saving best record time in mutant generation
vit_mut[trn]=bnc_mut;  // saving best result generation number after perturbation
avit_mut+=bnc_mut;
av+=record_min; // finding total record sum
avt+=utime; // sum of user time



	if((best-record_min)>=ACC)
	{
		best=record_min;
		for(i=0;i<grp;++i)
		best_pop[i]=minrec[i];
	}
	
	
	
printf("\n\n end of gen \n\n\n");	
}

//********************-----------------end of generation--------------********************-------------------------------------

av/=tit; // average best value

avt/=tit; // average user time
avit/=tit; // average generation best
avit_mut/=tit;// av gen best in mut
sd=sdt=sdit=sdit_mut=0.0;
for(i=0;i<tit;++i) // calculating SD
{
	sd+=(valt[i]-av)*(valt[i]-av);
	
	sdt+=(vtm[i]-avt)*(vtm[i]-avt);
	sdit+=(vit[i]-avit)*(vit[i]-avit);
	sdit_mut+=(vit_mut[i]-avit_mut)*(vit_mut[i]-avit_mut);
}
sd=sqrt(sd/tit);

sdt=sqrt(sdt/tit);
sdit=sqrt(sdit/tit);
sdit_mut=sqrt(sdit_mut/tit);


fprintf(outfile,"%s\t%d\t%.3lf\t%.3lf\t%.3lf\t%.3lf\t%.3lf\t%.3lf\t%.3lf\n",argv[2],grp, best,av,sd, avt,sdt, avit_mut,sdit_mut);
printf("%s  %3d  %9.4lf  %9.4lf %9.4lf %6.2lf %6.2lf  %9.2lf %9.2lf\n",argv[2],grp, best,av,sd, avt,sdt, avit_mut,sdit_mut);

printf("best rec array\n");
for(i=0;i<grp;++i)
printf("%d\t",best_pop[i]);

return 0;
}
//______________________/// end of main__________________________////////////////////////////////////////////
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
//------------------------init neh end-----------
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

//------------------------------fun _neh end----------

//----------------------------end initpop no neh----------------------------


//______________________________PERT FUN____________________

double pert_d(int *a)// this fun is for neh initpop1
{
    int i,j,nu=grp,z,dd=d,k,r,mxind1=0,x,dd1=1,hd; // taking d from #define d
    int tgt[COVMAX], seq[COVMAX],sub[zl],rem[COVMAX];
    int index[COVMAX],temp[COVMAX][COVMAX];
    double tempcost[COVMAX],record1;
    
     pert_cnt++;
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

//___________________________________PERT FUN END__________________________________



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
eval_calls++;
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

//_________________________________findcost_d******end______________________



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


