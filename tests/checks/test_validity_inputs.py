"""Judge 83: C4's own readers and pricing.
- The ledger as C4 reads it is checked against E1 and C2's reading of the same ledger, as an independent cross-check.
- NSE's listing gives lot sizes and monthly expiries.
- Black-76 is checked against a textbook value.
- The implied volatility and the parity forward are checked by round trip."""

import math
from datetime import date, datetime

import pytest

from fno.accounting.ledgers import Order
from fno.books.account import PaperAccount
from fno.books.equity import Mark, account_state, trade_positions
from fno.books.fills import Fill
from fno.checks.validity_account import AccountProblem, LedgerAccounts, restart_days
from fno.checks.validity_listing import NseListing, monthly_expiries
from fno.checks.validity_pricing import PricedLeg, PricingProblem, black76, implied_vol, parity_forward
from fno.composition import open_account_writer
from fno.config import ROOT, load_config
from fno.constants import BOOK1_RULES
from fno.models import IST
from fno.risk.book_view import closed_equity_series
from tests.checks.validity_sources import FILE_DAY, NseFiles, nse_file

CHARGES = load_config(ROOT / "config.yaml")["charges"]


def _fill(fill_id, trade, contract, side, price, day, hour=15):
    when = datetime(2026, 10, day, hour, 15, tzinfo=IST)
    return Fill.priced(fill_id, trade, when, contract, Order(side, price, 65, 1.0), CHARGES)


@pytest.fixture
def ledger(tmp_path):
    """Trade a opened 6 Oct and closed 8 Oct; trade b opened 9 Oct and still open; a fill at 15:15 on 14 Oct."""
    with open_account_writer(BOOK1_RULES, tmp_path) as writer:
        writer.start(date(2026, 10, 1))
        for fill in (
            _fill("1", "a", "X1CE", "sell", 100.0, 6), _fill("2", "a", "X2CE", "buy", 40.0, 6),
            _fill("3", "a", "X1CE", "buy", 150.0, 8), _fill("4", "a", "X2CE", "sell", 60.0, 8),
            _fill("5", "b", "X1PE", "sell", 90.0, 9), _fill("6", "b", "X2PE", "buy", 30.0, 9),
            _fill("7", "c", "X3CE", "sell", 20.0, 14),
        ):  # fmt: skip
            writer.apply_fill(fill)
    return tmp_path


def test_c4_reads_the_ledger_as_e1_and_c2_do(ledger):
    facts = LedgerAccounts(ledger).facts(BOOK1_RULES, datetime(2026, 10, 14, 15, 0, tzinfo=IST))
    account = PaperAccount(ledger, BOOK1_RULES)
    fills = [f for f in account.fills() if f.fill_id != "7"]  # E4's 15:15 fill comes after the 15:00 cutoff
    trades = list(trade_positions(fills).values())
    assert facts.closed_equity == closed_equity_series(date(2026, 10, 1), 500_000.0, trades)
    marks = {c: Mark(1.0) for c in ("X1PE", "X2PE")}
    state = account_state(500_000.0, fills, marks)
    assert facts.cash == pytest.approx(state.cash, abs=1e-9)
    (position,) = facts.positions
    assert position.trade_id == "b" and position.units == {"X1PE": -65, "X2PE": 65}


def test_a_ledger_that_was_never_started_fails_closed(tmp_path):
    with pytest.raises(AccountProblem, match="not been started"):
        LedgerAccounts(tmp_path).facts(BOOK1_RULES, datetime(2026, 10, 14, 15, 0, tzinfo=IST))


def test_restarts_dated_after_the_day_wait_and_a_bad_row_fails_closed():
    rows = [{"date": "2026-10-10", "action": "restart_brake", "reason": "owner", "entered_by": "owner"},
            {"date": "2026-10-20", "action": "restart_brake", "reason": "owner", "entered_by": "owner"}]  # fmt: skip
    assert restart_days(rows, date(2026, 10, 14)) == (date(2026, 10, 10),)
    with pytest.raises(AccountProblem):
        restart_days([rows[0] | {"action": "loosen"}], date(2026, 10, 14))


def test_nse_listing_gives_lots_and_monthly_expiries():
    listing, problems = NseListing(NseFiles()).read(date(2026, 10, 14))
    assert problems == [] and listing.file_day == FILE_DAY
    assert listing.monthly_expiries == ("2026-10-27", "2026-11-24") and listing.lot_sizes["2026-10-27"] == {65}
    assert monthly_expiries(["2026-11-03", "2026-11-24", "2026-11-10"]) == ("2026-11-24",)


def test_nse_listing_reads_the_newest_file_before_the_day_never_the_days_own():
    files = NseFiles({date(2026, 10, 14): nse_file(lot=75), date(2026, 10, 12): nse_file()})
    listing, _ = NseListing(files).read(date(2026, 10, 14))
    assert listing.file_day == date(2026, 10, 12) and listing.lot_sizes["2026-10-27"] == {65}


def test_black76_matches_a_textbook_value():
    """Hull, Options, Futures and Other Derivatives, futures option: F = K = 20, r = 9%, T = 4 months, sigma = 25%:
    put = call = 1.12."""
    assert black76("PE", 20.0, 20.0, 4 / 12, 0.09, 0.25) == pytest.approx(1.1166, abs=1e-4)
    assert black76("CE", 20.0, 20.0, 4 / 12, 0.09, 0.25) == pytest.approx(1.1166, abs=1e-4)


def test_the_implied_volatility_and_the_parity_forward_round_trip():
    price = black76("CE", 25_100.0, 25_300.0, 30 / 365, 0.065, 0.14)
    assert implied_vol(price, "CE", 25_100.0, 25_300.0, 30 / 365, 0.065) == pytest.approx(0.14, abs=1e-9)
    calls = {k: black76("CE", 25_100.0, k, 30 / 365, 0.065, 0.14) for k in (25_000.0, 25_100.0, 25_200.0)}
    puts = {k: black76("PE", 25_100.0, k, 30 / 365, 0.065, 0.14) for k in calls}
    assert parity_forward(calls, puts, 30 / 365, 0.065) == pytest.approx(25_100.0, abs=1e-6)
    with pytest.raises(PricingProblem):
        implied_vol(0.001, "CE", 25_100.0, 24_000.0, 30 / 365, 0.065)  # below intrinsic value: no volatility


def test_the_forward_comes_from_the_strike_where_call_and_put_are_closest():
    """Market quotes, not model ones: parity gives a different forward at each strike; 25,100 (C - P = 2) is used."""
    calls, puts = {25_000.0: 150.0, 25_100.0: 100.0, 25_200.0: 60.0}, {25_000.0: 52.0, 25_100.0: 98.0, 25_200.0: 160.0}
    assert parity_forward(calls, puts, 30 / 365, 0.065) == pytest.approx(25_100 + math.exp(0.065 * 30 / 365) * 2)


def test_a_shock_moves_the_forward_scales_the_volatility_and_lets_days_pass():
    leg = PricedLeg("CE", 25_200.0, date(2026, 11, 13), 120.0, 25_000.0, 0.15)
    day = date(2026, 10, 14)  # 30 days to expiry
    assert leg.value(day, 0.065) == pytest.approx(black76("CE", 25_000.0, 25_200.0, 30 / 365, 0.065, 0.15))
    shocked = leg.value(day, 0.065, move_pct=-8, sigma_factor=2.0, sigma_add=0.05, days=1)
    assert shocked == pytest.approx(black76("CE", 23_000.0, 25_200.0, 29 / 365, 0.065, 0.35))
    assert leg.value(day, 0.065, days=30) == 0.0  # at expiry: intrinsic value, out of the money
