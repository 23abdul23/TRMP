/* Sanity check on a REAL instance: for every destroy policy, pert_d() must return a valid permutation of
 * all groups whose reported cost equals an independent full recomputation (findcost). Run from project root.
 * build: gcc -O2 -I src -o out/test_policy_real tests/test_policy_real.c src/trmp_core.c src/destroy_repair.c -lm
 * usage: out/test_policy_real instances/<file>.dat */
#include "trmp.h"
#include <assert.h>
int main(int argc, char **argv)
{
  if (argc < 2 || load_instance(argv[1], "init_state.dat")) return 1;
  int seen[COVMAX], i, t, pol; srand(7);
  for (pol = POLICY_UNIFORM; pol <= POLICY_BLOCK; pol++) {
    for (i = 0; i < grp; ++i) rec[i] = i;
    double worst = 0; long moved = 0;
    for (t = 0; t < 300; t++) {
      double c = pert_d(rec, 4, pol);
      for (i = 0; i < grp; ++i) seen[i] = 0;
      for (i = 0; i < grp; ++i) { assert(mutant[i] >= 0 && mutant[i] < grp); seen[mutant[i]]++; }
      for (i = 0; i < grp; ++i) assert(seen[i] == 1);
      double d = fabs(c - findcost(mutant)); if (d > worst) worst = d;
      for (i = 0; i < grp; ++i) if (rec[i] != mutant[i]) { moved++; break; }
      for (i = 0; i < grp; ++i) rec[i] = mutant[i];   /* random walk (accept all) */
    }
    printf("policy %d: max |reported-recomputed| = %.3e, mutations changing the permutation: %ld/300\n", pol, worst, moved);
    assert(worst < 1e-6);
  }
  puts("real-instance policy check passed"); return 0;
}
