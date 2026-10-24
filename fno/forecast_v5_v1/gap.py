"""The measure-gap table (story G14, "The measure gap"; amendment 1 section 5): one row per session that has both an
ok candle row and an ok live row. The pairs and their ratio are W8's (G7b's pairing, the one calculation of the
back-fill / live drift); this module only prints them, so the two can never disagree. W8's review alert is G7b's."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from .records import INPUT_MEASURE

HEADER = ("| Session | Live quote RV | Candle RV (15m bars) | Candle / live |", "|---|---|---|---|")
NO_PAIRS = "no session has both an ok candle row and an ok live row yet"


class PairedRv(Protocol):
    """One of G7b's pairs (amendment 1: day, live, candle, ratio = candle / live)."""

    day: date
    live: float
    candle: float
    ratio: float


def gap_table(pairs: Sequence[PairedRv]) -> list[str]:
    """The labelled table, oldest session first."""
    lines = [f"Measure gap: {INPUT_MEASURE}"]
    if not pairs:
        return [*lines, NO_PAIRS]
    rows = [f"| {p.day:%d %b %Y} | {p.live:.6e} | {p.candle:.6e} | {p.ratio:.3f} |" for p in sorted(pairs, key=_day)]
    return [*lines, *HEADER, *rows]


def _day(pair: PairedRv) -> date:
    return pair.day
