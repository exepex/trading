"""One scored row per (index, issue day, horizon): implied's quantiles from G13b's back-fill record and the outcome
`ln(target close / S_ref)` from G13b's `Outcomes`. Rows that are not `ok`, or have no outcome yet, are dropped
(protocol section 7)."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date

from .periods import period_of, sealed
from .scaling import LEVELS

IMPLIED, OK = "implied", "ok"
LQ = tuple(f"lq{round(p * 100):02d}" for p in LEVELS)


@dataclass(frozen=True)
class Row:
    underlying: str
    day: date
    horizon: str
    target_day: date
    s_ref: float
    quantiles: tuple[float, ...]
    outcome: float

    @property
    def period(self) -> str | None:
        return period_of(self.day)

    @property
    def cell(self) -> tuple[str, str]:
        return self.underlying, self.horizon


def implied_rows(records: Iterable[dict], close: Callable[[str, date], float | None], final_open: bool) -> list[Row]:
    """The seal comes first: a record of the final period is dropped before its outcome is ever looked up."""
    dated = ((date.fromisoformat(r["day"]), r) for r in records)
    rows = []
    for day, record in sealed(dated, final_open):
        for row in record.get("rows", []):
            if row["forecaster"] != IMPLIED or row["status"] != OK or not row["target_day"]:
                continue
            target = date.fromisoformat(row["target_day"])
            value = close(record["underlying"], target)
            if value is None:
                continue
            outcome = math.log(value / row["s_ref"])
            rows.append(Row(record["underlying"], day, row["horizon"], target, row["s_ref"],
                            tuple(row[k] for k in LQ), outcome))  # fmt: skip
    return sorted(rows, key=lambda r: (r.underlying, r.horizon, r.day))
