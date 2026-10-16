"""Study 3 (story BR1a): the null and size check of the claim rule and of futility, on real daily differences.

- **Members:** the three registered-baseline pairs' daily mean differences (v4's sign: negative favours the second
  baseline). Each is centred on its own mean **within the population tested** (the whole window, or the worst year
  alone): no true skill, with the real skew, tails, crash days and dependence kept.
- **Paths:** circular block bootstrap, 63-session blocks, the **same block starts for all three members and for the
  primary's daily loss** in each path (ChatGPT review 121), seed words (20261016, population).
- **The test, as frozen:** a member's p is `confirmatory_test(series, block=5, k=member)`. That p is the larger of the
  batch-means p and the studentized-bootstrap p. Holm claims at least one member exactly when the smallest p is at
  most rate / 3, so the bootstrap runs only when a member's batch-means p is at most rate / 3. That gives the same
  decisions as running it everywhere. Futility closures are ignored in the false-claim count, so
  that count is an upper bound whatever futility threshold is chosen later.
- **The single loop:** for each rate in (0.02, 0.015, 0.01, 0.005): the look counts at that rate (`stats.look_counts`,
  the worst inflated variance from study 2, delta from study 1); false claim at look 1, look 2 and either, **for each
  sign separately**, overall and in the worst year. The first rate within every limit is selected; none: postponed.
- **False futility,** at the selected rate's look 1: each member shifted to a true improvement of delta (added to the
  series in the improving direction, for each sign its own), the share of member-paths declared futile by
  `futility_p` (margin 0.02, the primary's daily losses). Its threshold steps down (0.025, then 0.015, 0.01, 0.005)
  until the rate is at most 0.035, or futility is dropped.
"""

import numpy as np

from fno.forecast_v4.confirmatory import batch_means_p, confirmatory_test, futility_p

from .stats import MINIMUM_EFFECT, TEST_BLOCK

SEED, PATHS, BLOCK = 20261016, 2000, 63
RATES = (0.02, 0.015, 0.01, 0.005)
FUTILITY_THRESHOLDS = (0.025, 0.015, 0.01, 0.005)
LOOK_LIMIT, EITHER_LIMIT, FUTILITY_LIMIT = 0.025, 0.045, 0.035
SIGNS = (1, -1)
ROLLING_STEP = 21


def centred(members: np.ndarray) -> np.ndarray:
    """members: (3, days) for one population; each row minus its own mean in that population."""
    return members - members.mean(axis=1, keepdims=True)


def block_paths(length: int, paths: int, path_length: int, population: int) -> np.ndarray:
    """(paths, path_length) day indices: circular 63-session blocks, one draw of starts per path shared by every
    series of that path."""
    rng = np.random.default_rng(np.random.SeedSequence([SEED, population]))
    blocks = -(-path_length // BLOCK)
    starts = rng.integers(0, length, size=(paths, blocks))
    return ((starts[:, :, None] + np.arange(BLOCK)) % length).reshape(paths, blocks * BLOCK)[:, :path_length]


def member_p(series: np.ndarray, member: int, first_step: float) -> float:
    """The frozen test's p. The bootstrap runs only when the batch-means p is at most Holm's first step, the only case
    where the larger of the two can be."""
    batch = batch_means_p(series, TEST_BLOCK)
    return batch if batch > first_step else confirmatory_test(series, TEST_BLOCK, member).p_value


def holm_claims(ps: list[float], rate: float) -> bool:
    """Holm at the rate claims at least one of the K members exactly when the smallest p is at most rate / K."""
    return min(ps) <= rate / len(ps)


def false_claims(paths: np.ndarray, looks: tuple[int, int], rate: float) -> dict:
    """paths: (3, paths, length) member series. The share of paths with a claim at each look and at either."""
    at = {look: np.zeros(paths.shape[1], dtype=bool) for look in looks}
    for i in range(paths.shape[1]):
        for look in looks:
            ps = [member_p(paths[m, i, :look], m, rate / paths.shape[0]) for m in range(paths.shape[0])]
            at[look][i] = holm_claims(ps, rate)
    first, second = looks
    return {"look1": float(at[first].mean()), "look2": float(at[second].mean()),
            "either": float((at[first] | at[second]).mean())}  # fmt: skip


def within_limits(rates: dict) -> bool:
    return rates["look1"] <= LOOK_LIMIT and rates["look2"] <= LOOK_LIMIT and rates["either"] <= EITHER_LIMIT


def select_rate(results: list[dict]) -> float | None:
    """The first rate whose every population and sign is within the limits; None: claims postponed."""
    for result in results:
        if all(within_limits(r) for r in result["false_claim"].values()):
            return result["rate"]
    return None


def population_paths(members: np.ndarray, losses: np.ndarray, length: int, population: int) -> tuple:
    index = block_paths(members.shape[1], PATHS, length, population)
    return centred(members)[:, index], losses[index]


def false_futility(member_paths: np.ndarray, loss_paths: np.ndarray, look1: int, delta: float, threshold: float):
    """The share of member-paths declared futile when each has a true improvement of delta (v4's sign: -delta)."""
    futile, total = 0, 0
    for m in range(member_paths.shape[0]):
        for i in range(member_paths.shape[1]):
            series = member_paths[m, i, :look1] - delta
            futile += futility_p(series, loss_paths[i, :look1], TEST_BLOCK, MINIMUM_EFFECT, threshold) <= 0.025
            total += 1
    return futile / total


def rolling_windows(members: np.ndarray, length: int, rate: float, looks: tuple[int, int]) -> dict:
    """Descriptive: the real (non-bootstrap) windows, one start every 21 sessions, centred like the paths."""
    series = centred(members)
    starts = range(0, max(0, series.shape[1] - length + 1), ROLLING_STEP)
    windows = np.stack([series[:, s : s + length] for s in starts], axis=1) if len(starts) else None
    return {"windows": len(starts), "false_claim": false_claims(windows, looks, rate) if windows is not None else None}
