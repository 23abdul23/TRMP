/* Unit tests of the learner on toy MDPs with known answers.
 * build: gcc -O2 -I src -o out/test_rl tests/test_rl.c src/rl_diff.c -lm */
#include "rl_diff.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
static int near(double a, double b, double t) { return fabs(a - b) < t; }

int main(void)
{
  RL r; int t, s;
  /* T1 two-state cycle A -(r=1)-> B -(r=0)-> A, one action, tau=1: rate 0.5, Q(A)-Q(B)=0.5 */
  rl_init(&r, 2, 1, RL_DIFF, 0.1, 0.2, 0.0, 1);
  for (t = 0, s = 0; t < 40000; ++t) { int s2 = 1 - s; rl_update(&r, s, 0, s == 0 ? 1.0 : 0.0, 1.0, s2); s = s2; }
  assert(near(r.Rbar, 0.5, 0.02)); assert(near(r.Q[0][0] - r.Q[1][0], 0.5, 0.05));
  /* T2 same cycle but every transition lasts tau=2: rate per unit time is 0.25.
   * A wrong sign / missing tau on the Rbar term would not converge to this value. */
  rl_init(&r, 2, 1, RL_DIFF, 0.1, 0.2, 0.0, 1);
  for (t = 0, s = 0; t < 40000; ++t) { int s2 = 1 - s; rl_update(&r, s, 0, s == 0 ? 1.0 : 0.0, 2.0, s2); s = s2; }
  assert(near(r.Rbar, 0.25, 0.02));
  /* T3 one state, two actions: a0 r=1,tau=1 (rate 1.0); a1 r=3,tau=4 (rate 0.75).
   * differential/SMDP must prefer a0; discounted (no tau) prefers a1 (3 > 1). */
  for (int algo = 0; algo < 2; ++algo) {
    rl_init(&r, 1, 2, algo, 0.1, 0.2, 0.9, 7);
    for (t = 0; t < 30000; ++t) {
      int a = rl_select(&r, 0, 0.2);
      rl_update(&r, 0, a, a == 0 ? 1.0 : 3.0, a == 0 ? 1.0 : 4.0, 0);
    }
    if (algo == RL_DIFF) { assert(rl_greedy(&r, 0) == 0); assert(near(r.Rbar, 1.0, 0.1)); assert(r.Q[0][0] - r.Q[0][1] > 0.5); }
    else assert(rl_greedy(&r, 0) == 1);
  }
  /* T4 private RNG in [0,1), roughly uniform */
  rl_init(&r, 1, 1, RL_DIFF, 0.1, 0.2, 0, 3); double m = 0;
  for (t = 0; t < 100000; ++t) { double x = rl_rand(&r); assert(x >= 0 && x < 1); m += x; }
  assert(near(m / 100000, 0.5, 0.01));
  puts("rl unit tests passed"); return 0;
}
