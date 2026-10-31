/* Unit checks on a hand-built 3-group / 2-sensor instance (angles in radians, absent = 9).
 * build: gcc -O2 -I src -o out/test_unit tests/test_unit.c src/trmp_core.c src/destroy_repair.c -lm */
#include "trmp.h"
#include <assert.h>
static int near(double a,double b){return fabs(a-b)<1e-9;}
int main(void){
  sen=2; grp=3; init_ang[0]=0; init_ang[1]=3.0;
  /* g0: sensor0->1.0, sensor1 absent | g1: s0 absent, s1->6.0 (wrap: |3-6|=3 < pi -> 3) | g2: s0->5.5 (|1-5.5|=4.5>pi -> 2pi-4.5), s1->0.5 */
  double W[3][2]={{1.0,9},{9,6.0},{5.5,0.5}};
  for(int i=0;i<3;i++){nact[i]=0;for(int j=0;j<2;j++){wt[i][j]=W[i][j]; if(W[i][j]<7) act[i][nact[i]++]=j;}}
  int p[3]={0,1,2}; double pc[3];
  double c=findcost(p);
  double expect=1.0 + 3.0 + (TOPI-4.5) + (TOPI-5.5);   /* g2 s1: 6.0->0.5 = 5.5 > pi -> 2pi-5.5 */
  assert(near(c,expect)); 
  assert(near(position_costs(p,pc),expect)); assert(near(pc[0],1.0)&&near(pc[1],3.0)&&near(pc[2],(TOPI-4.5)+(TOPI-5.5)));
  long long e0=eval_calls; double c2=findcost_d(p,1);   /* prefix of length 2 */
  assert(near(c2,4.0)); assert(eval_calls==e0+1 && eval_units>=2);
  assert(effective_kappa(8)==1 && effective_kappa(0)==1);  /* grp=3 -> clamp to grp/2=1 */
  puts("unit tests passed"); return 0; }
