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

from .panels import cached_rows, lots_from_rows, panel_from_rows
from .runner import BANKNIFTY, NIFTY, Market

FIRST_DAY, LAST_FILE_DAY = date(2019, 1, 1), date(2026, 10, 20)


def sessions(calendar, first: date = FIRST_DAY, last: date = LAST_FILE_DAY) -> list[date]:
    return [d for d in calendar.sessions(first, last) if calendar.session_kind(d) == "regular"]


def markets() -> dict[str, Market]:
    calendar = build_session_calendar()
    fo_files, _ = build_nifty_panel_files()
    rows = cached_rows((NIFTY, BANKNIFTY), sessions(calendar), fo_files, options_for=(BANKNIFTY,))
    outcomes = Outcomes(g13b.build_closes(g13b.build_tables(g13b.build_store())))
    chain = settlement_chain(build_nse_fo_library(), build_nse_legacy_fo_library())

    def settled(index: str):
        def price(expiry: date) -> float | None:
            return settle(index, expiry, chain, outcomes.close).price

        return price

    nifty_panel: NiftyPanel = read_nifty_panel(PANEL_FOLDER, keep=cycle_rows)
    bank_panel = panel_from_rows(rows[BANKNIFTY], lambda day: outcomes.close(BANKNIFTY, day), {})
    return {
        NIFTY: Market(NIFTY, nifty_panel, lots_from_rows(rows[NIFTY]), settled(NIFTY)),
        BANKNIFTY: Market(BANKNIFTY, bank_panel, lots_from_rows(rows[BANKNIFTY]), settled(BANKNIFTY)),
    }


def calendar():
    return build_session_calendar()
