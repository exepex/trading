"""Protocol v4's 14:30-14:40 capture as a quote part of the daily run (story G10 completion, criteria 1-2): A4e's named
window (`quotes record --window v4`), unchanged, started with the 3 pm parts at the run's start and waiting inside A4e's
recorder for 14:30. Its times and dataset come from A4e's window in `config.yaml`, never copied; it is live from
`daily.live_from.v4_pack` and commits its own files as soon as it ends (it shares none with NIFTY's 14:55 part)."""

from __future__ import annotations

from datetime import date, datetime

from ..constants import V4_PACK_LIVE_KEY
from ..quotes.recorder import DATASET
from ..quotes.window import QuoteWindow
from .quote_parts import START_MARGIN, QuotePart, earliest_start

V4_PART = "v4"
V4_STEM = "nifty"  # A4e's named window records NIFTY under A4's own stem, in its own dataset


def v4_quotes(window: QuoteWindow) -> str:
    """The pathspec of the window's own dataset folder: its sidecars and canonical markers (raw rows: Drive only)."""
    return f":(glob)research/data/quotes/{window.dataset(DATASET)}/**"


def v4_part(window: QuoteWindow) -> QuotePart:
    return QuotePart(
        V4_PART,
        ("quotes", "record", "--window", window.name),
        (v4_quotes(window),),
        not_before=_shortly_before(window),
        canonicals=((window.dataset(DATASET), V4_STEM),),
        window_end=window.end,
        live_key=V4_PACK_LIVE_KEY,
        apart=True,
    )


def _shortly_before(window: QuoteWindow):
    """O1's margin before the window's start, never earlier than the parts' one early limit (`earliest_start`, A4's
    shared `earliest_waiting_start`): the recorder then waits minutes, not half an hour (a rehearsal runs at real speed
    while a recorder runs, REH1)."""
    shortly = (datetime.combine(date.min, window.start) - START_MARGIN).time()
    return max(shortly, earliest_start(window.start))
