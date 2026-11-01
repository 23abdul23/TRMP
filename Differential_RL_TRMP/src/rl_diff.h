#ifndef RL_DIFF_H
#define RL_DIFF_H
/* Tabular (semi-Markov) average-reward "differential" Q-learning and a discounted twin.
 * Own xorshift RNG: exploration never touches rand(), so it cannot perturb the search stream. */
#define RL_MAXS 64
#define RL_MAXA 16
enum { RL_DIFF = 0, RL_DISC = 1 };

typedef struct {
  int nS, nA, algo;
  double alpha, eta_rl, gamma;
  double Q[RL_MAXS][RL_MAXA];
  long   visits[RL_MAXS][RL_MAXA];
  double Rbar;
  unsigned long long rng;
} RL;

void   rl_init(RL *r, int nS, int nA, int algo, double alpha, double eta_rl, double gamma, unsigned long long seed);
double rl_rand(RL *r);                               /* uniform [0,1) */
int    rl_greedy(RL *r, int s);                      /* argmax Q, random tie-break */
int    rl_select(RL *r, int s, double eps);          /* epsilon-greedy */
/* One update. diff : delta = rew - Rbar*tau + max_a Q(s2,a) - Q(s,a);  Q += alpha*delta;  Rbar += eta_rl*alpha*delta
 * disc : delta = rew + gamma*max_a Q(s2,a) - Q(s,a);                    Q += alpha*delta   (tau ignored)
 * returns delta */
double rl_update(RL *r, int s, int a, double rew, double tau, int s2);
#endif
