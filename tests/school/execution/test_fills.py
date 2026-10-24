"""Story MS-P1d criteria 6, 7, 8 and 11: a fill needs its seal; entries fill every leg at the decision snapshot's touch
(ask to buy, bid to sell) or none, never partial; an exit with any leg it cannot close waits and never takes a guessed
price; the fill port passes the contracts' conformance checks."""

from dataclasses import replace
from datetime import timedelta

import pytest

from fno.costs import order_charges
from fno.school.constants import SIDE_BUY, SIDE_SELL, ExitState, Outcome, RefusalReason
from fno.school.contracts.accounts import SealedDecision
from fno.school.contracts.decisions import Decision
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c

from .school_builders import AT, CHARGES, fills


@pytest.fixture
def port(tmp_path):
    return fills(tmp_path)


def test_the_fill_port_conforms(port):
    c.check_fill_port(port, b.sealed(), b.snapshot(), b.seal(), AT)
    c.check_fill_port_missing_quote(port, b.sealed(), b.snapshot(quotes={}), b.seal(), AT, b.position())


def test_entry_fills_every_leg_at_the_touch_with_c1_charges(port):
    result = port.enter(b.sealed(), b.snapshot(), b.seal(), AT)
    sold, bought = result.legs
    assert (sold.side, sold.price, sold.units) == (SIDE_SELL, 10.0, 30)  # the bid of 10/11
    assert (bought.side, bought.price, bought.units) == (SIDE_BUY, 5.0, 30)  # the ask of 4/5
    assert sold.charges == pytest.approx(order_charges(10.0, 30, SIDE_SELL, CHARGES))
    assert bought.charges == pytest.approx(order_charges(5.0, 30, SIDE_BUY, CHARGES))
    assert result.filled_at == AT and result.rests_on == b.sealed().file_sha256


@pytest.mark.parametrize(
    ("seal", "why"),
    [
        (b.seal(pushed_at=AT + timedelta(seconds=1)), "pushed after the fill"),
        (b.seal(sha256="ee" * 32), "names another file"),
    ],
)
def test_no_valid_seal_no_fill(port, seal, why):
    refused = port.enter(b.sealed(), b.snapshot(), seal, AT)
    assert refused.refused == (RefusalReason.STALE_SEAL,) and not refused.legs, why
    assert port.exit(b.position(), b.snapshot(), "cd" * 32, seal, AT).refused == (RefusalReason.STALE_SEAL,)


def test_the_seal_is_checked_before_any_quote(port):
    stale = b.seal(pushed_at=AT + timedelta(minutes=1))
    assert port.enter(b.sealed(), b.snapshot(quotes={}), stale, AT).refused == (RefusalReason.STALE_SEAL,)


def test_one_missing_leg_fills_nothing_never_part(port):
    snapshot = b.snapshot(quotes={b.key(1000.0): b.quote()})  # the protective 900 put is gone
    result = port.enter(b.sealed(), snapshot, b.seal(), AT)
    assert not result.legs and result.refused == (RefusalReason.MISSING_QUOTE,)


@pytest.mark.parametrize(
    ("quote", "reason"),
    [
        (b.quote(4.0, 5.0, size=29), RefusalReason.SIZE_ABOVE_DISPLAYED),  # 30 units against 29 shown at the ask
        (replace(b.quote(4.0, 5.0), valid=False), RefusalReason.ONE_SIDED_QUOTE),  # no trade today (A4)
        (replace(b.quote(4.0, 5.0), bid=None), RefusalReason.ONE_SIDED_QUOTE),
    ],
)
def test_an_unusable_leg_refuses_the_whole_entry(port, quote, reason):
    result = port.enter(b.sealed(), b.snapshot(quotes={b.key(1000.0): b.quote(), b.key(900.0): quote}), b.seal(), AT)
    assert not result.legs and result.refused == (reason,)


def test_a_protective_leg_that_cannot_be_sold_back_refuses_the_entry(port):
    protection = replace(b.quote(4.0, 5.0), bid_qty=29)  # buyable (ask size 1000), not sellable back for 30 units
    result = port.enter(b.sealed(), b.snapshot(quotes={b.key(1000.0): b.quote(), b.key(900.0): protection}), b.seal(),
                        AT)  # fmt: skip
    assert result.refused == (RefusalReason.PROTECTION_UNSELLABLE,)


def test_a_ticket_fills_by_the_same_rule_and_no_other_outcome_fills(port):
    ticket = SealedDecision(replace(b.decision(), outcome=Outcome.TICKET, reason="trade_limit"), "cd" * 32)
    assert port.enter(ticket, b.snapshot(), b.seal(), AT).filled
    refused = Decision("CS1@1", b.decision().road, b.SESSION, Outcome.REFUSED, "max_loss", b.put_spread())
    with pytest.raises(ValueError, match="never fills"):
        port.enter(SealedDecision(refused, "cd" * 32), b.snapshot(), b.seal(), AT)


def test_a_fill_never_uses_another_road_session_or_an_earlier_time(port):
    with pytest.raises(ValueError, match="not"):
        port.enter(b.sealed(), b.snapshot(code=b.RoadCode.NIFTY_MONTHLY), b.seal(), AT)
    with pytest.raises(ValueError, match="precede"):
        port.enter(b.sealed(), b.snapshot(), b.seal(), b.SLOT_AT)


def test_an_exit_closes_every_leg_at_the_touch_short_first(port):
    result = port.exit(b.position(), b.snapshot(), "cd" * 32, b.seal(), AT)
    assert [(leg.key.strike, leg.side, leg.price) for leg in result.legs] == [(1000.0, SIDE_BUY, 11.0),
                                                                              (900.0, SIDE_SELL, 4.0)]  # fmt: skip


@pytest.mark.parametrize("missing", [1000.0, 900.0])
def test_an_exit_with_any_leg_unquotable_waits_and_fills_nothing(port, missing):
    left = {k: q for k, q in b.snapshot().quotes.items() if k.strike != missing}
    result = port.exit(b.position(), b.snapshot(quotes=left), "cd" * 32, b.seal(), AT)
    assert result.state == ExitState.EXIT_WAITING_QUOTE and not result.legs


def test_a_risk_reducing_close_needs_a_valid_two_sided_quote(port):
    one_sided = {b.key(1000.0): replace(b.quote(), ask=None), b.key(900.0): b.quote(4.0, 5.0)}
    assert port.exit(b.position(), b.snapshot(quotes=one_sided), "cd" * 32, b.seal(), AT).state == (
        ExitState.EXIT_WAITING_QUOTE
    )


def test_a_seal_or_fill_after_the_session_s_close_is_stale():
    """Law 6: a decision sealed (or filled) after 15:30 would trade at the 15:00 touch after seeing the market."""
    close = b.SLOT_AT.replace(hour=15, minute=30)
    port = fills_at_root()
    assert port.enter(b.sealed(), b.snapshot(), b.seal(), close).filled
    late = close + timedelta(seconds=1)
    assert port.enter(b.sealed(), b.snapshot(), b.seal(), late).refused == (RefusalReason.STALE_SEAL,)
    days_later = b.seal(pushed_at=b.SLOT_AT + timedelta(days=3))
    assert port.enter(b.sealed(), b.snapshot(), days_later, b.SLOT_AT + timedelta(days=3)).refused == (
        RefusalReason.STALE_SEAL,
    )
    assert port.exit(b.position(), b.snapshot(), "cd" * 32, b.seal(), late).refused == (RefusalReason.STALE_SEAL,)


def test_a_proposal_naming_a_contract_twice_never_fills():
    twice = replace(b.put_spread(), legs=(*b.put_spread().legs, b.put_spread().legs[0]))
    sealed = SealedDecision(replace(b.decision(), proposal=twice), "cd" * 32)
    with pytest.raises(ValueError, match="twice"):
        fills_at_root().enter(sealed, b.snapshot(), b.seal(), AT)


def fills_at_root():
    from pathlib import Path

    return fills(Path("/nonexistent-settlement-folder"))
