"""Small statistics shared by the three studies: the daily mean's SD and lag-1 with the AR(1) inflation, the look
counts of story BR1a's single loop, and a batch-means 95% interval."""

import math
from statistics import NormalDist

import numpy as np

K, POWER, MINIMUM_EFFECT, TEST_BLOCK = 3, 0.8, 0.02, 5


def sd_lag1(series: np.ndarray) -> tuple[float, float]:
    x = np.asarray(series, dtype=float)
    return float(np.std(x, ddof=1)), float(np.corrcoef(x[:-1], x[1:])[0, 1])


def inflated_variance(series: np.ndarray) -> float:
    """SD^2 x (1 + lag1) / (1 - lag1): the long-run variance of an AR(1) mean (no inflation for lag1 <= 0)."""
    sd, lag1 = sd_lag1(series)
    return sd * sd * ((1 + lag1) / (1 - lag1) if lag1 > 0 else 1.0)


def look_counts(rate: float, variance: float, delta: float) -> tuple[int, int]:
    """(look 1, look 2) sessions: 80% power for the minimum effect delta, one-sided, z at 1 - rate / K."""
    z = NormalDist().inv_cdf(1 - rate / K) + NormalDist().inv_cdf(POWER)
    look2 = math.ceil(z * z * variance / (delta * delta))
    return math.ceil(look2 / 2), look2


def batch_interval(series: np.ndarray, block: int = TEST_BLOCK) -> tuple[float, float, float]:
    """(mean, low, high): the mean of the series and its 95% interval from consecutive batch means."""
    x = np.asarray(series, dtype=float)
    batches = len(x) // block
    means = x[len(x) - batches * block :].reshape(batches, block).mean(axis=1)
    half = NormalDist().inv_cdf(0.975) * float(np.std(means, ddof=1)) / math.sqrt(batches)
    mean = float(x.mean())
    return mean, mean - half, mean + half
