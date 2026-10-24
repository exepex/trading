"""The measure-gap table (story G14, "The measure gap"; amendment 1 section 5): one row per session that has both an
ok candle row and an ok live row. The pairs are W8's (G7b's `backfill_pairs`: day, back-filled `RV_s`, live `RV_s`),
the same pairs its drift line reads, so the two can never disagree; this module prints each pair with its ratio,
candle / live, as W8's drift line divides it. W8's review alert is G7b's."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from .records import INPUT_MEASURE

HEADER = ("| Session | Live quote RV | Candle RV (15m bars) | Candle / live |", "|---|---|---|---|")
NO_PAIRS = "no session has both an ok candle row and an ok live row yet"
Pair = tuple[date, float | None, float | None]  # (day, candle, live), G7b's order


def gap_table(pairs: Sequence[Pair]) -> list[str]:
    """The labelled table, oldest session first; a pair missing either side is not a row."""
    both = sorted((day, candle, live) for day, candle, live in pairs if candle and live)
    lines = [f"Measure gap: {INPUT_MEASURE}"]
    if not both:
        return [*lines, NO_PAIRS]
    rows = [f"| {day:%d %b %Y} | {live:.6e} | {candle:.6e} | {candle / live:.3f} |" for day, candle, live in both]
    return [*lines, *HEADER, *rows]
