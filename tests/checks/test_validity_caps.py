"""Story C5 in C4 (judge C, accepted by the orchestrator): for the books C4 drops the 3-open, stress and exposure checks
and recomputes the paper account, the bucket, open-risk and new-risk-per-day caps with its own arithmetic; the Manual
account keeps C2's original checks. A bucket breach C2 somehow allowed is refused by C4, and a trade the new caps allow
is not refused by C4's old checks."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from fno.checks.validity_account import AccountFacts, Position
from fno.checks.validity_caps import held_max_loss
from fno.checks.validity_chain import PricedChain
from fno.checks.validity_evidence import EvidenceReader
from fno.checks.validity_money import entry_cash_flow
from fno.constants import RISK_PROFILE_BOOKS
from fno.quotes.recorder import DATASET
from fno.risk.open_risk import HeldMaxLoss
from tests.checks.builders import committed_record
from tests.checks.validity_builders import DAY, SHAPES, check, committed_store, failed, legs_of, mid, proposal
from tests.checks.validity_sources import MARGIN_ROWS, Margins, limits
from tests.desk.builders import CHARGES, LOT
from tests.risk.builders import market as risk_market

BOOKS_START = 2_000_000.0
BOOKS_CHECKS = ["paper_account", "drawdown_brake", "bucket_cap", "open_risk_cap", "new_risk_per_day", "margin_room"]
LEGS = legs_of(SHAPES["SF"][0])
CASH = entry_cash_flow([leg.leg for leg in LEGS], LOT, CHARGES)


def _held(trade_id: str, opened_on: date | None = DAY - timedelta(days=3), structure: str = "SF") -> Position:
    units = {leg.contract: leg.leg.side * LOT for leg in LEGS}
    return Position(trade_id, units, CASH, (structure, 200.0, 1), opened_on)


def _books(*positions: Position, start: float = BOOKS_START, **profile) -> dict:
    account = AccountFacts(BOOKS_START + 0.0, ((date(2026, 10, 1), start),), (), tuple(positions))
    return {"account": account, "owner_limits": limits(RISK_PROFILE_BOOKS, **profile)}


def _terms(*positions: Position):
    return {p.trade_id: p.terms for p in positions}


def _one_trade_loss() -> float:
    report = check(**_books())
    return next(r for r in report.results if r.name == "bucket_cap").numbers["total_rs"]


def test_the_books_run_exactly_the_c5_checks_and_a_correct_trade_passes():
    report = check(**_books())
    assert report.ok, [r.reason for r in report.failures]
    names = [r.name for r in report.results]
    assert [n for n in names if n in BOOKS_CHECKS + ["open_trades", "stress_loss", "exposure_limit"]] == BOOKS_CHECKS


def test_four_open_trades_pass_for_the_books_but_the_manual_account_refuses_the_fourth():
    """A trade the new caps allow is not refused by C4's old 3-trade check (owner, 15 Oct 2026: "1 A")."""
    held = tuple(_held(f"h{i}") for i in range(3))
    report = check(proposal(open_terms=_terms(*held)), **_books(*held))
    assert report.ok, [r.reason for r in report.failures]
    manual = AccountFacts(500_000.0, ((date(2026, 10, 1), 500_000.0),), (), held)
    assert "open_trades" in failed(check(proposal(open_terms=_terms(*held)), account=manual))


def test_a_bucket_breach_c2_allowed_is_refused_by_c4():
    """The proposal says every C2 verdict passed; C4's own sum is over the bucket cap, so C4 refuses it."""
    held = (_held("h1"),)
    one = _one_trade_loss()
    the_proposal = proposal(open_terms=_terms(*held), risk_verdicts_ok=True)
    over = check(the_proposal, **_books(*held, bucket_cap_rs=2 * one - 0.01))
    assert failed(over) == {"bucket_cap"} and "bucket NIFTY/short_volatility" in over.failures[0].reason
    at = check(the_proposal, **_books(*held, bucket_cap_rs=round(2 * one, 2) + 0.01))
    assert at.ok, [r.reason for r in at.failures]


@pytest.mark.parametrize(("opened", "counted"), [(DAY, True), (DAY - timedelta(days=1), False)])
def test_new_risk_counts_only_trades_opened_this_session(opened, counted):
    held = (_held("h1", opened),)
    report = check(proposal(open_terms=_terms(*held)), **_books(*held))
    numbers = next(r for r in report.results if r.name == "new_risk_per_day").numbers
    assert ("h1" in numbers["counted_rs"]) is counted


def test_open_risk_cap_counts_every_bucket():
    held = (_held("h1"), _held("h2", structure="BF"))
    one = _one_trade_loss()
    report = check(proposal(open_terms=_terms(*held)), **_books(*held, open_risk_cap_rs=2 * one))
    assert failed(report) == {"open_risk_cap"}


def test_an_unmapped_structure_or_unknown_first_fill_day_fails_every_cap():
    unmapped = (_held("h1", structure="XX"),)
    report = check(proposal(open_terms=_terms(*unmapped)), **_books(*unmapped))
    caps = [r for r in report.failures if r.name in ("bucket_cap", "open_risk_cap", "new_risk_per_day")]
    assert len(caps) == 3 and all("unmapped" in r.reason for r in caps)
    assert failed(report) - {r.name for r in caps} == {"margin_room"}  # no margin row for XX either
    unknown = (_held("h1", opened_on=None),)
    assert failed(check(proposal(open_terms=_terms(*unknown)), **_books(*unknown))) >= {"new_risk_per_day"}


def test_a_book_opened_on_rs_5_lakh_is_refused_for_the_books():
    assert failed(check(**_books(start=500_000.0))) == {"paper_account"}


@pytest.mark.parametrize(("as_of", "ok"), [("2026-10-13", True), ("2026-10-12", False), ("2026-10-09", False)])
def test_books_margin_older_than_one_session_is_refused(as_of, ok):
    """Decision on Wed 14 Oct: the previous session's row (13 Oct) is fresh; 12 Oct (two sessions back) is not,
    though only two days old: C4's 7-day lookback stays for the Manual account only."""
    rows = [MARGIN_ROWS[0] | {"as_of": as_of}]
    report = check(margins=Margins(rows), **_books())
    assert report.ok is ok and (ok or failed(report) == {"margin_room"})
    manual = check(margins=Margins(rows))
    assert "margin_room" not in failed(manual)  # within 7 days for the Manual account


def test_c4s_held_maximum_loss_equals_c2s_on_the_same_position():
    """Two independent implementations of the same definition agree to the paisa."""
    store = committed_store()
    evidence, problems = EvidenceReader(store, DATASET).read(DAY, committed_record(store, DAY, "exec"))
    chain = PricedChain(evidence, DAY, 0.065)
    position = _held("h1")
    prices = {(leg.leg.strike, leg.leg.kind): mid(leg.leg.strike, leg.leg.kind) for leg in LEGS}
    the_market = risk_market(25_000.0, prices, DAY + timedelta(days=13), day=DAY)
    c2 = HeldMaxLoss(CHARGES).max_loss(position.units, position.cash_flow, the_market)
    assert problems == [] and c2 > 0
    assert held_max_loss(position, chain, CHARGES) == pytest.approx(c2, abs=0.01)
    assert held_max_loss(replace(position, units={}), chain, CHARGES) == 0.0
