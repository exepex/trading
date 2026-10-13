"""Story B2 on the repository's real NIFTY panel, 2024-26 only (the discovery period; 2019-2023 is experiment 1's
challenge period and is not read before the freeze).

Criterion 7: the cycle dates equal desk meeting 1's (research/2026-10-12-desk-meeting-1/results.json, `trades`), with
the protocol's next-day entry: meeting 1 entered on what is now the decision day. Criterion 5: every traded cycle of
every structure has a modelled maximum loss, charges and pads included, of at most Rs 10,000; a realised loss above the
cap is listed in the failure message, never hidden."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.composition import build_cycle_simulator, build_cycles, build_structures
from fno.config import load_app_config
from fno.constants import CycleStatus
from fno.research_data.expiries import DAYS_TO_EXPIRY
from fno.research_data.panel_reader import read_nifty_panel
from fno.research_engine.cycles import TradingDays, cycle_rows
from fno.storage.wiring import PANEL_FOLDER, build_session_calendar

MEETING_1 = Path(__file__).resolve().parents[2] / "research" / "2026-10-12-desk-meeting-1" / "results.json"
DISCOVERY_YEARS = (2024, 2025, 2026)
CAP = 10_000
JULY_2024 = date(2024, 7, 25)


@pytest.fixture(scope="module")
def panel():
    return read_nifty_panel(PANEL_FOLDER, DISCOVERY_YEARS, cycle_rows)


@pytest.fixture(scope="module")
def cycles(panel):
    return build_cycles(panel)


def test_cycle_dates_equal_meeting_1_with_next_day_entry(cycles):
    calendar = build_session_calendar()
    meeting = json.loads(MEETING_1.read_text(encoding="utf-8"))["trades"]
    expected = [
        (date.fromisoformat(t["expiry"]), date.fromisoformat(t["entry"]), date.fromisoformat(t["exit"]))
        for t in meeting
    ]
    assert len(meeting) == 33
    assert [(c.expiry, c.decision_day, c.exit_day) for c in cycles] == expected
    assert all(c.entry_day == calendar.next_session(c.decision_day) for c in cycles)
    assert all(c.has_entry_window for c in cycles)


def test_each_decision_day_is_the_first_trading_day_of_its_window(cycles):
    days = TradingDays(build_session_calendar())
    for c in cycles:
        window_start = c.expiry - timedelta(days=DAYS_TO_EXPIRY[1])
        earlier = [window_start + timedelta(n) for n in range((c.decision_day - window_start).days)]
        assert not any(days.is_trading_day(d) for d in earlier), c


def test_every_traded_cycle_is_within_the_loss_cap(panel, cycles):
    simulator = build_cycle_simulator(load_app_config(), panel)
    results = [simulator.simulate(c, s) for c in cycles for s in build_structures()]
    traded = [r for r in results if r.status == CycleStatus.TRADED]
    assert len(results) == 99 and len(traded) == 96  # the three BF cycles below are bad_prices
    over_model = [(r.structure, r.cycle.expiry, r.max_loss) for r in traded if r.max_loss > CAP]
    over_realised = [(r.structure, r.cycle.expiry, r.net) for r in traded if -r.net > CAP]
    assert not over_model, f"modelled maximum loss above the cap: {over_model}"
    assert not over_realised, f"realised loss above the cap (a data or code error to investigate): {over_realised}"
    above_model = [(r.structure, r.cycle.expiry) for r in traded if -r.net > r.max_loss]
    assert above_model == [("SF", JULY_2024)], f"realised loss above the modelled maximum: {above_model}"


def test_the_one_realised_loss_above_its_model_comes_from_exit_closes_above_the_width(panel, cycles):
    """July 2024 SF (width 300): at the 4 Jul exit the 23250/23550 call spread closed at 1168.65 - 867.40 = 301.25,
    more than the 300-point width it can ever pay, so the close-proxy exit cost more than the terminal worst case
    (realised -Rs 4,024 against a modelled Rs 2,886). Kept visible: the cap bounds the terminal payoff, not an exit
    at non-synchronous closes."""
    cycle = next(c for c in cycles if c.expiry == JULY_2024)
    result = build_cycle_simulator(load_app_config(), panel).simulate(cycle, build_structures()[0])
    calls = {leg.leg.strike: leg.exit.price for leg in result.legs if leg.leg.kind == "CE"}
    assert calls == {23250.0: 1168.65, 23550.0: 867.4} and calls[23250.0] - calls[23550.0] > result.width
    assert round(result.net) == -4024 and round(result.max_loss) == 2886


def test_the_three_long_flies_that_cannot_win_are_bad_prices(panel, cycles):
    """Owner decision of 13 Oct 2026: debit 100.15, 100.60 and 101.10 for a 100-point fly that pays at most 100. The
    wider widths broke the cap, so the narrowest listed width's problem is the status."""
    simulator = build_cycle_simulator(load_app_config(), panel)
    long_fly = build_structures()[2]
    bad = [c.expiry for c in cycles if simulator.simulate(c, long_fly).status == CycleStatus.BAD_PRICES]
    assert bad == [JULY_2024, date(2024, 8, 29), date(2026, 2, 24)]


def test_traded_exits_beyond_the_payoff_bounds_are_flagged(panel, cycles):
    """Report only (judge 25, owner decision of 13 Oct 2026): 4 of 96 traded exits close beyond what the position can
    pay at expiry; their net is counted in the results, never dropped."""
    simulator = build_cycle_simulator(load_app_config(), panel)
    flagged = {
        (s.code, c.expiry): round(r.net)
        for c in cycles
        for s in build_structures()
        if (r := simulator.simulate(c, s)).exit_outside_payoff
    }
    assert flagged == {
        ("SF", JULY_2024): -4024, ("BF", date(2024, 9, 26)): 7, ("BF", date(2024, 12, 26)): 637,
        ("BF", date(2026, 3, 30)): 1036,
    }  # fmt: skip
