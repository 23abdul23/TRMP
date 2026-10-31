#ifndef TRMP_H
#define TRMP_H
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define u01 ((double) rand()/(RAND_MAX+1.0))
#define COVMAX 701
#define MMAX 502
#define PI 3.1415926
#define TOPI 6.2831852
#define ACC 1e-7
#define SPO 50
#define zl 100

enum { POLICY_UNIFORM = 0, POLICY_COST_GREEDY = 1, POLICY_HISTORY = 2, POLICY_BLOCK = 3 };
double history_costs(const int *ind, double *h);   /* see destroy_repair.c */

extern int sen, grp, initpop_count, opp_count, ind_maxc, pert_cnt;
extern double record, record_min, init_ang[MMAX], wt[COVMAX][MMAX], cost[SPO];
extern int act[COVMAX][MMAX], nact[COVMAX], pop[SPO][COVMAX];
extern int rec[COVMAX], mutant[COVMAX];
extern clock_t butimer_mut;

/* Evaluation accounting. Only findcost_d (the call the mutation/repair makes per candidate
 * position) is counted: calls = number of candidate evaluations (paper's "objective
 * evaluations"), units = sum of prefix lengths actually scanned (true work). */
extern long long eval_calls, eval_units;

int    load_instance(const char *instfile, const char *initfile);
double findcost(int *ind);
double findcost_d(int *ind, int sub);
int    isequal(double a, double b);
int    unique(int *ind, double csts, int indx);
double fun_neh(int *a);
void   init_pop1(int popsize);
/* per-position transition costs D(S_{i-1}, g_{rho_i}) of a full permutation; returns total. */
double position_costs(const int *perm, double *pc);

/* destroy-and-repair. kappa = requested destruction size (clamped to n/2 as in the baseline).
 * Result permutation is written to the global `mutant`; returns its full cost. */
double pert_d(int *a, int kappa, int policy);
int    effective_kappa(int kappa);
#endif
