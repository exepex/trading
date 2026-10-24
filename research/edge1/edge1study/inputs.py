"""The real inputs (protocol section 3), wired from the repository's existing readers. Only this module touches Drive or
the panel files; everything else takes plain objects, so the tests run on synthetic data.
- NIFTY: the committed panel, option rows with 21 or more days to expiry (all that T21, SL2 and TP50 read; EXP uses
  the settlement). Lots come from the F&O files.
- BANKNIFTY: the F&O files' monthly rows, with the index close from G13b's close table.
- Settlement: G13c's chain (E7 first, then the legacy FUTIDX row), cross-checked against the close as G13c does."""

from __future__ import annotations

from datetime import date

from fno.itm_chance.settlement import settle
from fno.itm_chance.wiring import settlement_chain
from fno.price_ranges import wiring as g13b
from fno.price_ranges.closes import Outcomes
from fno.research_data.panel_reader import NiftyPanel, read_nifty_panel
from fno.research_engine.cycles import cycle_rows
from fno.storage.wiring import (
    PANEL_FOLDER,
    build_nifty_panel_files,
    build_nse_fo_library,
    build_nse_legacy_fo_library,
    build_session_calendar,
)

from .expiries import relabelled_panel, relabelled_rows
from .lots import market_lots
from .panels import cached_rows, panel_from_rows
from .runner import BANKNIFTY, NIFTY, Market, sealed

FIRST_DAY, LAST_FILE_DAY = date(2019, 1, 1), date(2026, 10, 20)


def sessions(calendar, first: date = FIRST_DAY, last: date = LAST_FILE_DAY) -> list[date]:
    return [d for d in calendar.sessions(first, last) if calendar.session_kind(d) == "regular"]


def rows_through(rows: dict[str, list], through: date) -> dict[str, list]:
    """Run 1's seal at load: every index's day rows dated after `through` are dropped."""
    return {symbol: [r for r in found if r.day <= through] for symbol, found in rows.items()}


def markets(through: date | None = None) -> dict[str, Market]:
    """Both markets; with `through` (run 1's seal) nothing dated later is loaded: NIFTY's panel years stop at that
    year and every BANKNIFTY row, lot and NIFTY lot after it is dropped before a panel is built."""
    calendar = build_session_calendar()
    fo_files, _ = build_nifty_panel_files()
    rows = cached_rows((NIFTY, BANKNIFTY), sessions(calendar), fo_files, options_for=(BANKNIFTY,))
    if through is not None:
        rows = rows_through(rows, through)
    rows = {symbol: relabelled_rows(found) for symbol, found in rows.items()}  # after the seal: no later date leaks
    outcomes = Outcomes(g13b.build_closes(g13b.build_tables(g13b.build_store())))
    chain = settlement_chain(build_nse_fo_library(), build_nse_legacy_fo_library())

    def settled(index: str):
        def price(expiry: date) -> float | None:
            return settle(index, expiry, chain, outcomes.close).price

        return price

    years = range(FIRST_DAY.year, through.year + 1) if through is not None else None
    nifty_panel: NiftyPanel = read_nifty_panel(PANEL_FOLDER, years, keep=cycle_rows)
    if through is not None:
        nifty_panel = sealed(nifty_panel, through)
    nifty_panel = relabelled_panel(nifty_panel)
    bank_panel = panel_from_rows(rows[BANKNIFTY], lambda day: outcomes.close(BANKNIFTY, day), {})
    return {
        NIFTY: Market(NIFTY, nifty_panel, market_lots(NIFTY, rows[NIFTY]), settled(NIFTY)),
        BANKNIFTY: Market(BANKNIFTY, bank_panel, market_lots(BANKNIFTY, rows[BANKNIFTY]), settled(BANKNIFTY)),
    }


def calendar():
    return build_session_calendar()
