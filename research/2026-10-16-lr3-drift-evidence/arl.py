"""Average run lengths of a one-sided lower CUSUM by Markov chain (Brook-Evans), normal data, to check design 5.8."""
import numpy as np
from math import erf, sqrt
class norm:
    @staticmethod
    def cdf(x, loc=0.0):
        x = np.asarray(x, dtype=float) - loc
        return 0.5 * (1 + np.vectorize(erf)(x / sqrt(2)))

def arl(k, h, shift, m=400):
    # states: S in [0,h) discretised into m cells; S_{t}=max(0,S+y-k) with y~N(shift,1) (y = -z: positive = bad)
    w = h / m
    centers = (np.arange(m) + 0.5) * w
    P = np.zeros((m, m))
    for i, s in enumerate(centers):
        # to state 0 cell (S<=w/... treat S=0 mass into first cell)
        upper = (np.arange(1, m + 1)) * w
        lower = np.arange(m) * w
        cdf_u = norm.cdf(upper - s + k, loc=shift)
        cdf_l = norm.cdf(lower - s + k, loc=shift)
        P[i] = cdf_u - cdf_l
        P[i, 0] += norm.cdf(0 - s + k, loc=shift)  # reset to 0 lands in the first cell
    start = np.zeros(m); start[0] = 1
    N = np.linalg.solve(np.eye(m) - P, np.ones(m))
    return float(N[0])

for k, h in ((0.5, 4), (0.5, 5), (0.1, 4), (0.1, 5), (0.1, 8), (0.15, 6)):
    row = [f"k={k} h={h}"] + [f"shift {d}: {arl(k,h,d):,.0f}" for d in (0.0, 0.2, 0.3, 0.5, 1.0)]
    print(" | ".join(row))
