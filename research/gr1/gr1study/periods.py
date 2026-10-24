"""GR1's periods (protocol section 7) and the seal of the final period (section 12 (a)): run 1 drops every record
issued on or after 2025-01-01 at load, before any score, conditioner or outcome is computed."""

from __future__ import annotations

from datetime import date

TRAIN, SELECT, FINAL = "train", "select", "final"
TRAIN_FROM, SELECT_FROM, FINAL_FROM, FINAL_TO = date(2019, 1, 1), date(2024, 1, 1), date(2025, 1, 1), date(2026, 10, 20)
N0_TRAIN_FROM = date(2020, 1, 2)  # A16b's candles start here (section 11); C8 too (section 7)


def period_of(day: date) -> str | None:
    if TRAIN_FROM <= day < SELECT_FROM:
        return TRAIN
    if SELECT_FROM <= day < FINAL_FROM:
        return SELECT
    if FINAL_FROM <= day <= FINAL_TO:
        return FINAL
    return None


def sealed(days_and_items, final_open: bool):
    """Keeps (day, item) pairs of train and select only, unless run 2 opens the final period. Applied at load."""
    for day, item in days_and_items:
        period = period_of(day)
        if period in (TRAIN, SELECT) or (final_open and period == FINAL):
            yield day, item
