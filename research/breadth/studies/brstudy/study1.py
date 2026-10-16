"""Study 1 (story BR1a): the spot proxy, then the primary baseline.

1. On the overlap sessions (both file formats, 2024-01-01 to 2024-07-05), the outcome Y of every (u, t) scored in both
   is computed from each format: `UndrlygPric` (UDiFF) and the near-month future (legacy). The agreement is the share
   of equal Y. At 97% or more, the studies use 2019-2025; below, every study uses 2024-2025 alone.
2. On that window, the primary baseline is the registered baseline (`market`, `trail60`, `cal60`) with the lowest mean
   Brier over every scored (u, t); a tie at 4 decimals goes to the earlier one. Each baseline's daily-mean Brier also
   gets a batch-means 95% interval."""

from .daily import outcomes
from .stats import batch_interval

AGREEMENT_LIMIT = 0.97
FULL_WINDOW, FALLBACK_WINDOW = ("2019-01-01", "2025-12-31"), ("2024-01-01", "2025-12-31")
REGISTERED = ("market", "trail60", "cal60")


def outcome_y(table: dict) -> dict[tuple[str, str], int]:
    sessions = sorted({d for rows in table.values() for d in rows})
    found = {}
    for u, rows in table.items():
        for day, value in outcomes(rows, sessions).items():
            if value is not None:
                found[(u, day)] = value[0]
    return found


def agreement(legacy_table: dict, udiff_table: dict) -> dict:
    proxy, spot = outcome_y(legacy_table), outcome_y(udiff_table)
    both = sorted(set(proxy) & set(spot))
    equal = sum(proxy[k] == spot[k] for k in both)
    share = equal / len(both) if both else 0.0
    window = FULL_WINDOW if share >= AGREEMENT_LIMIT else FALLBACK_WINDOW
    return {"pairs_compared": len(both), "equal": equal, "agreement": share, "limit": AGREEMENT_LIMIT,
            "window": list(window)}  # fmt: skip


def primary_baseline(scored: dict, losses: list[dict], window: tuple[str, str]) -> dict:
    first, last = window
    totals, count = dict.fromkeys(REGISTERED, 0.0), 0
    for days in scored.values():
        for day, (y, p) in days.items():
            if first <= day <= last:
                count += 1
                for b in REGISTERED:
                    totals[b] += (p[b] - y) ** 2
    means = {b: round(totals[b] / count, 4) for b in REGISTERED}
    primary = min(REGISTERED, key=lambda b: (means[b], REGISTERED.index(b)))
    daily = [row for row in losses if first <= row["day"] <= last]
    intervals = {b: batch_interval([row[b] for row in daily]) for b in REGISTERED}
    return {"window": list(window), "scored_pairs": count, "mean_brier": {b: totals[b] / count for b in REGISTERED},
            "mean_brier_4dp": means, "daily_mean_interval_95": intervals, "primary": primary,
            "delta": 0.02 * totals[primary] / count}  # fmt: skip
