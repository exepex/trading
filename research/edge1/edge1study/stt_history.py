"""Protocol section 9's historical-STT side run: each order charged at the STT rate of its own trade date. Reported
beside the decided figure (today's 0.15% on every date), never decided on.

Sources, checked in the build: Finance Act 2023 (options premium 0.05% to 0.0625% from 1 Apr 2023; NSE circular
FATAX56235), Finance (No. 2) Act 2024 (0.0625% to 0.1% from 1 Oct 2024), Budget 2026 (0.1% to 0.15% on premium and
0.125% to 0.15% on exercise from 1 Apr 2026; NSE/FATAX/73524, the source of `config.yaml`'s exercise note)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

# (first trade date, STT on sold premium %, STT on exercise %), oldest first; the first row covers 2019 onwards
SCHEDULE = (
    (date(2016, 6, 1), 0.05, 0.125),
    (date(2023, 4, 1), 0.0625, 0.125),
    (date(2024, 10, 1), 0.1, 0.125),
    (date(2026, 4, 1), 0.15, 0.15),
)


def rates_on(day: date) -> tuple[float, float]:
    found = [row for row in SCHEDULE if row[0] <= day]
    if not found:
        raise ValueError(f"no STT rate known for {day}")
    return found[-1][1], found[-1][2]


def charges_on(charges: Mapping[str, float]):
    """`charges` with its two STT rates replaced by those of a trade date; every other charge as decided."""

    def on(day: date) -> dict:
        sell, exercise = rates_on(day)
        return {**charges, "stt_sell_pct": sell, "stt_exercise_pct": exercise}

    return on
