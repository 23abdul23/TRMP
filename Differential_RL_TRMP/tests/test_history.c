/* Hand-built 5-group / 2-sensor instance for the history-aware destroy score (angles in radians, absent = 9).
 * build: gcc -O2 -I src -o out/test_history tests/test_history.c src/trmp_core.c src/destroy_repair.c -lm
 *
 * schedule A B C D E (positions 0..4), init state s0=0, s1=3:
 *   A: s0->1.0            cost 1.0  (init state is not a predecessor)
 *   B: s1->2.0            cost 1.0
 *   C: s1->2.5            cost 0.5  (s1 last set by B at position 1 = immediate predecessor -> not history)
 *   D: s0->1.5            cost 0.5  (s0 last set by A at position 0 = distant, 0 <= 3-2 -> history 0.5)
 *   E: s0->0.5, s1->3.0   cost 1.0+0.5; s0 last set by D (immediate -> no), s1 last set by C at 2 <= 4-2 -> history 0.5
 * expected history h = [0,0,0,0.5,0.5], position cost = [1,1,0.5,0.5,1.5], total 4.5
 */
#include "trmp.h"
#include <assert.h>
static int near(double a, double b) { return fabs(a - b) < 1e-9; }
int main(void)
{
  sen = 2; grp = 5; init_ang[0] = 0; init_ang[1] = 3.0;
  double W[5][2] = {{1.0, 9}, {9, 2.0}, {9, 2.5}, {1.5, 9}, {0.5, 3.0}};
  for (int i = 0; i < 5; i++) { nact[i] = 0; for (int j = 0; j < 2; j++) { wt[i][j] = W[i][j]; if (W[i][j] < 7) act[i][nact[i]++] = j; } }
  int p[5] = {0, 1, 2, 3, 4}; double pc[5], h[5];
  assert(near(position_costs(p, pc), 4.5));
  double e[5] = {1, 1, 0.5, 0.5, 1.5}, eh[5] = {0, 0, 0, 0.5, 0.5};
  for (int i = 0; i < 5; i++) assert(near(pc[i], e[i]));
  assert(near(history_costs(p, h), 4.5));
  for (int i = 0; i < 5; i++) assert(near(h[i], eh[i]));
  /* every policy must return a valid permutation whose reported cost equals the recomputed cost */
  for (int pol = POLICY_UNIFORM; pol <= POLICY_BLOCK; pol++)
    for (int t = 0; t < 200; t++) {
      for (int i = 0; i < 5; i++) rec[i] = p[i];
      double c = pert_d(rec, 2, pol); int seen[5] = {0, 0, 0, 0, 0};
      for (int i = 0; i < 5; i++) { assert(mutant[i] >= 0 && mutant[i] < 5); seen[mutant[i]]++; }
      for (int i = 0; i < 5; i++) assert(seen[i] == 1);
      assert(near(c, findcost(mutant)));
    }
  puts("history / policy tests passed"); return 0;
}
