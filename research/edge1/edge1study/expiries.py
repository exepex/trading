"""A monthly contract's one expiry date (protocol section 3, revision 6).

NSE moved the expiry of contracts already listed: the 29 Jun 2023 holiday (to 28 Jun), BANKNIFTY's switch to
Wednesday (Mar-Apr 2024), back to Thursday (Jan-Mar 2025) and both indices' switch to Tuesday (Sep 2025). The files
before a move carry the old date, so the same contract appears under two dates, and a cycle entered before the move
finds no price after it and no settlement. Every date a monthly future carries is therefore relabelled, on each day,
to the date the same contract carried on its last listed day (the date it really expired); options of that date on
that day are the same contract and move with it. A date no future carries that day (a weekly) is left alone."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date

from fno.research_data.panel_reader import FutureQuote, NiftyPanel

from .day_files import DayRows


def final_expiries(futures: Mapping[date, Sequence[FutureQuote]]) -> dict[date, date]:
    """Each date a monthly future carried -> that contract's date on its last listed day (one future a month)."""
    last: dict[tuple[int, int], tuple[date, date]] = {}
    for day, quotes in futures.items():
        for quote in quotes:
            key = (quote.expiry.year, quote.expiry.month)
            if key not in last or day > last[key][0]:
                last[key] = (day, quote.expiry)
    return {q.expiry: last[(q.expiry.year, q.expiry.month)][1] for quotes in futures.values() for q in quotes}


def _on_day(quotes: Sequence, futures_today: Sequence[FutureQuote], finals: Mapping[date, date]) -> tuple:
    moved = {f.expiry for f in futures_today}
    return tuple(q._replace(expiry=finals[q.expiry]) if q.expiry in moved else q for q in quotes)


def relabelled_panel(panel: NiftyPanel) -> NiftyPanel:
    finals = final_expiries(panel.futures)
    futures = {d: _on_day(q, q, finals) for d, q in panel.futures.items()}
    options = {d: _on_day(q, panel.futures.get(d, ()), finals) for d, q in panel.options.items()}
    return NiftyPanel(panel.sessions, options, futures)


def relabelled_rows(rows: Sequence[DayRows]) -> list[DayRows]:
    finals = final_expiries({r.day: r.futures for r in rows})
    out = []
    for r in rows:
        moved = {f.expiry for f in r.futures}
        lots = {finals[e] if e in moved else e: lot for e, lot in r.lots.items()}
        options, futures = _on_day(r.options, r.futures, finals), _on_day(r.futures, r.futures, finals)
        out.append(replace(r, options=options, futures=futures, lots=lots))
    return out
