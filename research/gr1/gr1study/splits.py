"""C9 (weekday) split at the expiry regime breaks (protocol section 6; judge 442 SF3), produced by both runs so no
split is ever computed after the final look. The break dates are pinned here and in a test:
- BANKNIFTY's weekly expiry moved from Thursday to Wednesday: the first F&O file listing a Wednesday weekly as the
  nearest expiry is 4 Sep 2023 (expiry 6 Sep; read from the archived files' expiry lists, 22 Oct 2026);
- BANKNIFTY's weeklies ended: the first file listing only the monthly is 14 Nov 2024 (read the same way);
- NIFTY's expiry moved to Tuesday from 1 Sep 2025 (NSE's circular, as recalled: reasoning only until run 2's own
  files confirm it; run 2 reports the first Tuesday expiry it reads)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from .candidates import Candidate, Context
from .evaluate import numbers
from .rows import Row

BREAKS: dict[str, tuple[date, ...]] = {
    "NIFTY": (date(2025, 9, 1),),
    "BANKNIFTY": (date(2023, 9, 4), date(2024, 11, 14)),
}


def segments(underlying: str, rows: Sequence[Row]) -> list[tuple[str, list[Row]]]:
    """The rows cut at the index's breaks: (label, rows) per non-empty piece, in date order."""
    edges = [r for r in BREAKS.get(underlying, ())]
    pieces, start = [], None
    for edge in [*edges, None]:
        part = [r for r in rows if (start is None or r.day >= start) and (edge is None or r.day < edge)]
        label = f"{start or 'start'} to {edge or 'end'}"
        if part:
            pieces.append((label, part))
        start = edge
    return pieces


def c9_split(underlying: str, candidate: Candidate, theta, rows: Sequence[Row], ctx: Context) -> list[dict]:
    """C9's numbers and C0's on each piece (reported, never decided on)."""
    return [{"segment": label, "c9": numbers(candidate, theta, part, ctx).as_dict(),
             "c0": numbers(None, None, part, ctx).as_dict()} for label, part in segments(underlying, rows)]  # fmt: skip
