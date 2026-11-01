#include "rl_diff.h"
#include <string.h>

void rl_init(RL *r, int nS, int nA, int algo, double alpha, double eta_rl, double gamma, unsigned long long seed)
{
  memset(r, 0, sizeof *r);
  r->nS = nS; r->nA = nA; r->algo = algo; r->alpha = alpha; r->eta_rl = eta_rl; r->gamma = gamma;
  r->rng = seed ? seed : 0x9E3779B97F4A7C15ULL;
  for (int i = 0; i < 8; ++i) rl_rand(r);            /* warm up */
}

double rl_rand(RL *r)
{
  unsigned long long x = r->rng;
  x ^= x >> 12; x ^= x << 25; x ^= x >> 27; r->rng = x;
  return (double)((x * 0x2545F4914F6CDD1DULL) >> 11) * (1.0 / 9007199254740992.0);
}

int rl_greedy(RL *r, int s)
{
  int a, best = 0, nt = 1; double bq = r->Q[s][0];
  for (a = 1; a < r->nA; ++a) {
    double q = r->Q[s][a];
    if (q > bq + 1e-12) { bq = q; best = a; nt = 1; }
    else if (q >= bq - 1e-12) { nt++; if (rl_rand(r) * nt < 1.0) best = a; }   /* reservoir tie-break */
  }
  return best;
}

int rl_select(RL *r, int s, double eps)
{
  if (rl_rand(r) < eps) { int a = (int)(rl_rand(r) * r->nA); return a >= r->nA ? r->nA - 1 : a; }
  return rl_greedy(r, s);
}

double rl_update(RL *r, int s, int a, double rew, double tau, int s2)
{
  int b; double mx = r->Q[s2][0], delta;
  for (b = 1; b < r->nA; ++b) if (r->Q[s2][b] > mx) mx = r->Q[s2][b];
  if (r->algo == RL_DIFF) {
    delta = rew - r->Rbar * tau + mx - r->Q[s][a];
    r->Q[s][a] += r->alpha * delta;
    r->Rbar += r->eta_rl * r->alpha * delta;
  } else {
    delta = rew + r->gamma * mx - r->Q[s][a];
    r->Q[s][a] += r->alpha * delta;
  }
  r->visits[s][a]++;
  return delta;
}
