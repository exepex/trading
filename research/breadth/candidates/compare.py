"""Response 198 (exploratory, one window, no freeze): three candidate tests for a BR1 v2 on study 3's null paths.

- **A, the v4 crash gate as frozen:** a look's window is judged only with at least 5 NIFTY 2% days and not more than
  10% of them (`judgeable`, `crash_dominated`); otherwise no claim.
- **B, the daily sign test:** the frozen test on sign(d); its own null is the median-centred series. It must also pass
  on study 3's mean-centred null (the meaning check).
- **C, the calibrated threshold:** Holm at alpha*, the largest alpha on a 0.0005 grid up to 0.02 that keeps every
  limit on paths drawn from 2024's days, checked on paths drawn from 2025's days.

A member's p is the frozen `confirmatory_test(series, 5, k)`. It is computed exactly whenever the batch-means p is at
most `cap` (the larger p of the two can be at most cap only then), else the batch-means p stands (it is above cap)."""

from multiprocessing import Pool

import numpy as np

from fno.forecast_v4.confirmatory import (
    CRASH_SHARE,
    MIN_EVENT_DAYS,
    batch_means_p,
    confirmatory_test,
)  # fmt: skip

BLOCK, K = 5, 3
GRID = np.round(np.arange(0.0005, 0.02 + 1e-12, 0.0005), 4)


def _p(task: tuple) -> float:
    series, k, cap = task
    batch = batch_means_p(series, BLOCK)
    return batch if batch > cap else confirmatory_test(series, BLOCK, k).p_value


def p_values(paths: np.ndarray, look: int, cap: float, pool: Pool) -> np.ndarray:
    """paths: (3, P, L). Each member's p on each path's first `look` days, exact up to `cap`: shape (3, P)."""
    tasks = [(paths[m, i, :look], m, cap) for m in range(paths.shape[0]) for i in range(paths.shape[1])]
    return np.array(pool.map(_p, tasks, chunksize=16)).reshape(paths.shape[0], paths.shape[1])


def _path_claims(task: tuple) -> bool:
    """Holm's any-claim on one path: members in order of their batch-means p, stopping at the first whose exact p is
    at most alpha / K (the same decision as computing every member's p)."""
    members, step = task
    batches = [batch_means_p(series, BLOCK) for series in members]
    for k in np.argsort(batches, kind="stable"):
        if batches[k] > step:
            return False
        if confirmatory_test(members[k], BLOCK, int(k)).p_value <= step:
            return True
    return False


def path_claims(paths: np.ndarray, look: int, alpha: float, pool: Pool) -> np.ndarray:
    """paths: (3, P, L). Whether Holm at alpha claims any member on each path's first `look` days: shape (P,)."""
    tasks = [(paths[:, i, :look], alpha / K) for i in range(paths.shape[1])]
    return np.array(pool.map(_path_claims, tasks, chunksize=8))


def any_claim(ps: np.ndarray, alpha: float) -> np.ndarray:
    """Holm at alpha claims some member exactly when the smallest p is at most alpha / K."""
    return ps.min(axis=0) <= alpha / K


def member_claimed(ps: np.ndarray, member: int, alpha: float) -> np.ndarray:
    """Holm step-down: the member is claimed when every p ranked at or before it passes its step alpha / (K - j)."""
    order = np.argsort(ps, axis=0, kind="stable")
    ranked = np.take_along_axis(ps, order, axis=0)
    steps = alpha / (K - np.arange(K))[:, None]
    passed = np.cumprod(ranked <= steps, axis=0).astype(bool)
    position = np.argmax(order == member, axis=0)
    return passed[position, np.arange(ps.shape[1])]


def judgeable(big_paths: np.ndarray, look: int) -> np.ndarray:
    """v4's gate on each path's first `look` days: at least 5 2% days and not crash-dominated."""
    count = big_paths[:, :look].sum(axis=1)
    return (count >= MIN_EVENT_DAYS) & ~(count > CRASH_SHARE * look)


def rates(first: np.ndarray, second: np.ndarray) -> dict:
    """The share with a claim at look 1, at look 2 and at either, with binomial standard errors."""
    out = {}
    for name, hit in (("look1", first), ("look2", second), ("either", first | second)):
        share = float(hit.mean())
        out[name], out[f"{name}_se"] = share, float(np.sqrt(share * (1 - share) / len(hit)))
    return out


def within(r: dict, look_limit: float = 0.025, either_limit: float = 0.045) -> bool:
    return r["look1"] <= look_limit and r["look2"] <= look_limit and r["either"] <= either_limit


def median_centred(members: np.ndarray) -> np.ndarray:
    return members - np.median(members, axis=1, keepdims=True)


def calibrated_alpha(ps_by_population: dict, looks: tuple[int, int]) -> float | None:
    """The largest grid alpha keeping every population's and sign's false-claim limits; None when none does.
    ps_by_population: name -> ((3, P) p at look 1, (3, P) p at look 2)."""
    best = None
    for alpha in GRID:
        if all(within(rates(any_claim(p1, alpha), any_claim(p2, alpha))) for p1, p2 in ps_by_population.values()):
            best = float(alpha)
    return best
