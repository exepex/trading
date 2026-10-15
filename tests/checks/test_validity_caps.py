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
from fno.checks.validity_money import entry_cash_flow, max_loss
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


UNITS = {leg.contract: leg.leg.side * LOT for leg in LEGS}


def _held(trade_id: str, structure: str = "SF") -> Position:
    return Position(trade_id, UNITS, CASH, (structure, 200.0, 1))


def _books(*positions: Position, start: float = BOOKS_START, session=(), **profile) -> dict:
    account = AccountFacts(BOOKS_START + 0.0, ((date(2026, 10, 1), start),), (), tuple(positions), tuple(session))
    return {"account": account, "owner_limits": limits(RISK_PROFILE_BOOKS, **profile)}


def _total(report, check_name: str, group: str) -> float:
    return next(r for r in report.results if r.name == check_name).numbers[group]["total_rs"]


def _terms(*positions: Position):
    return {p.trade_id: p.terms for p in positions}


def _one_trade_loss() -> float:
    report = check(**_books())
    return _total(report, "bucket_cap", "bucket NIFTY/short_volatility")


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


def test_new_risk_counts_only_this_sessions_trades_even_closed_ones():
    """Owner, "3 A": a round trip today (held, then flat) still counts at its largest maximum loss; an open trade
    from an earlier session (not in the session list) does not."""
    one = _one_trade_loss()
    round_trip = ("rt", ((UNITS, CASH), ({}, CASH + 500.0)))
    report = check(proposal(open_terms=_terms(_held("earlier"))), **_books(_held("earlier"), session=[round_trip]))
    group = next(r for r in report.results if r.name == "new_risk_per_day").numbers["trades opened this session"]
    assert set(group["counted_rs"]) == {"rt", proposal().opportunity_id}
    assert group["total_rs"] == pytest.approx(2 * one, abs=0.02)


@pytest.mark.parametrize(("slack", "ok"), [(0.01, True), (0.0, True), (-0.02, False)])
def test_new_risk_cap_at_and_over_its_number_with_a_closed_round_trip(slack, ok):
    one = _one_trade_loss()
    session = [("rt", ((UNITS, CASH), ({}, CASH)))]
    total = _total(check(**_books(session=session)), "new_risk_per_day", "trades opened this session")
    report = check(**_books(session=session, new_risk_per_day_rs=round(total, 2) + slack))
    assert total == pytest.approx(2 * one, abs=0.02) and report.ok is ok
    assert ok or failed(report) == {"new_risk_per_day"}


def test_a_two_sided_position_counts_its_full_loss_in_each_bucket():
    """Owner, "1 B": a held position listed with two sides is in both buckets; a proposal sharing either sees it."""
    sides = {"SF": ["short_volatility", "bullish"], "SC": "short_volatility", "BF": "long_volatility"}
    held = (_held("two_sided"),)
    one = _one_trade_loss()
    report = check(proposal("SC", open_terms=_terms(*held)), **_books(*held, bucket_sides=sides))
    assert _total(report, "bucket_cap", "bucket NIFTY/short_volatility") > one  # the held fly is counted
    sided = check(proposal(open_terms=_terms(*held)), **_books(*held, bucket_sides=sides))
    shared = {"bucket NIFTY/short_volatility", "bucket NIFTY/bullish"}
    numbers = next(r for r in sided.results if r.name == "bucket_cap").numbers
    assert shared <= set(numbers) and all(numbers[g]["total_rs"] == pytest.approx(2 * one, abs=0.02) for g in shared)
    tight = check(proposal(open_terms=_terms(*held)), **_books(*held, bucket_sides=sides, bucket_cap_rs=2 * one - 1))
    assert failed(tight) == {"bucket_cap"}


def test_open_risk_cap_counts_every_bucket():
    held = (_held("h1"), _held("h2", structure="BF"))
    one = _one_trade_loss()
    report = check(proposal(open_terms=_terms(*held)), **_books(*held, open_risk_cap_rs=2 * one))
    assert failed(report) == {"open_risk_cap"}


def test_an_unmapped_open_structure_fails_the_caps_that_read_it():
    unmapped = (_held("h1", structure="XX"),)
    report = check(proposal(open_terms=_terms(*unmapped)), **_books(*unmapped))
    caps = [r for r in report.failures if r.name in ("bucket_cap", "open_risk_cap")]
    assert len(caps) == 2 and all("unmapped" in r.reason for r in caps)  # as C2: the caps that read held buckets
    assert failed(report) == {"bucket_cap", "open_risk_cap", "margin_room"}  # no margin row for XX either


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


@pytest.mark.parametrize("key", ["bucket_cap_rs", "bucket_sides", "margin_max_age_sessions", "paper_account_rs"])
def test_c4_refuses_to_start_on_a_books_setting_missing_never_a_crash_later(key):
    from fno.checks.validity_settings import ValidityLimitsError

    with pytest.raises(ValidityLimitsError, match="risk.profiles.books"):
        limits(RISK_PROFILE_BOOKS, **{key: None})


def test_c4_treats_a_day_the_calendar_cannot_answer_as_a_stale_margin():
    def no_calendar(day):
        raise ValueError("calendar has no 2031")

    settings = replace(limits(RISK_PROFILE_BOOKS).margins, session_kind=no_calendar)
    assert not settings.fresh(date(2031, 1, 2), date(2031, 1, 2))


@pytest.mark.parametrize(
    ("as_of", "day", "fresh"),
    [
        (date(2026, 11, 6), date(2026, 11, 9), True),  # Sun 8 Nov muhurat is not a trading day (A14 writes no row)
        (date(2026, 11, 5), date(2026, 11, 9), False),
        (date(2026, 1, 30), date(2026, 2, 2), False),  # Sun 1 Feb special session is one
        (date(2026, 10, 16), date(2026, 10, 19), True),
    ],
)
def test_c4_counts_margin_age_in_a14s_trading_days(as_of, day, fresh):
    assert limits(RISK_PROFILE_BOOKS).margins.fresh(as_of, day) is fresh


def test_c4_refuses_an_unsigned_restart_row_on_its_own():
    """Judge 105 should-fix 2: C4 requires `entered_by` itself, as C2 does."""
    from fno.checks.validity_account import AccountProblem, restart_days

    row = {"date": "2026-10-07", "action": "restart_brake", "reason": "reviewed", "entered_by": ""}
    with pytest.raises(AccountProblem, match="malformed"):
        restart_days([row], DAY)
    assert restart_days([row | {"entered_by": "owner"}], DAY) == (date(2026, 10, 7),)


@pytest.mark.parametrize(("limit", "ok"), [(30.0, True), (30.01, True), (29.99, False)])
def test_each_c4_cap_passes_at_exactly_its_limit(limit, ok):
    """Judge 105 N1: C4's cap arithmetic passes at the limit and refuses a paisa under it."""
    from fno.checks.validity_caps import _cap

    assert _cap("bucket_cap", [("g", {"a": 10.0, "b": 20.0})], limit).ok is ok
    assert _cap("bucket_cap", [("g1", {"a": 1.0}), ("g2", {"a": 10.0, "b": 20.0})], limit).ok is ok  # every group


def test_c4_does_not_count_a_held_position_of_the_other_side():
    """Judge 105 N2: same group (NIFTY), other side: a held short fly is not in a long fly's bucket."""
    held = (_held("short_vol"),)
    report = check(proposal("BF", open_terms=_terms(*held)), **_books(*held))
    numbers = next(r for r in report.results if r.name == "bucket_cap").numbers
    assert set(numbers["bucket NIFTY/long_volatility"]["counted_rs"]) == {proposal("BF").opportunity_id}


def test_c4_counts_a_locked_in_held_position_as_zero_never_negative():
    """Judge 105 N5: a position that can no longer lose is not room for another trade."""
    store = committed_store()
    evidence, _ = EvidenceReader(store, DATASET).read(DAY, committed_record(store, DAY, "exec"))
    chain = PricedChain(evidence, DAY, 0.065)
    assert held_max_loss(replace(_held("locked"), cash_flow=1_000_000.0), chain, CHARGES) == 0.0


def test_c4_refuses_a_position_on_two_underlyings():
    """Judge 105 N17: NIFTY and BANKNIFTY legs in one position are not one bucket."""
    from fno.checks.validity_caps import CapProblem, buckets_of

    with pytest.raises(CapProblem, match="unmapped"):
        buckets_of("SF", ["NIFTY26OCT25000CE", "BANKNIFTY26OCT52000PE"], {"SF": "short_volatility"})
    assert buckets_of("SF", ["NIFTY26OCT25000CE"], {"SF": "short_volatility"}) == (("NIFTY", "short_volatility"),)


def test_c4_counts_a_two_lot_proposal_at_its_units():
    """Judge 105 N19: the proposal's loss is on lots x lot size, not one lot."""
    two = proposal(lots=2)
    report = check(two, **_books())
    total = _total(report, "bucket_cap", "bucket NIFTY/short_volatility")
    legs = [leg.leg for leg in two.legs]
    assert total == pytest.approx(max_loss(legs, 2 * LOT, CHARGES).total, abs=0.01)
    assert total > 1.9 * _one_trade_loss()


@pytest.mark.parametrize(
    ("key", "value"),
    [("bucket_cap_rs", "30000"), ("bucket_cap_rs", True), ("rules", "paper_account"), ("bucket_sides", []),
     ("margin_max_age_sessions", 0)],
)  # fmt: skip
def test_c4_checks_its_own_value_types(key, value):
    """Judge 105 minor 2: C4 does not rely on C2's start-up check for malformed values."""
    from fno.checks.validity_settings import ValidityLimitsError

    with pytest.raises(ValidityLimitsError):
        limits(RISK_PROFILE_BOOKS, **{key: value})


@pytest.mark.parametrize(
    ("code", "sides"),
    [("PCS", {"bullish", "short_volatility"}), ("CCS", {"bearish", "short_volatility"}),
     ("CDS", {"bullish", "long_volatility"}), ("PDS", {"bearish", "long_volatility"}),
     ("LC", {"bullish", "long_volatility"}), ("LP", {"bearish", "long_volatility"})],
)  # fmt: skip
def test_c4_puts_each_real_vertical_in_its_two_owner_buckets(code, sides):
    """Owner "1 B" with STR1's real codes and legs, the repository's bucket_sides; a held short fly is counted only
    in the short-volatility bucket, at its full maximum loss."""
    from tests.checks.test_validity_shapes import ONE_SIDE, ROWS
    from tests.checks.validity_proposal_builder import one_side_proposal

    spec, width = ONE_SIDE[code]
    held = (_held("fly"),)
    report = check(
        one_side_proposal(code, spec, width, open_terms=_terms(*held)), margins=Margins(ROWS), **_books(*held)
    )
    numbers = next(r for r in report.results if r.name == "bucket_cap").numbers
    assert {g.removeprefix("bucket NIFTY/") for g in numbers if g != "limit_rs"} == sides
    for group, counted in numbers.items():
        if group != "limit_rs":
            assert ("fly" in counted["counted_rs"]) is (group == "bucket NIFTY/short_volatility")
