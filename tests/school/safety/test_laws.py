"""Story MS-P1d criteria 2, 3, 4, 5 and 11: no law changes a proposal; the daily stop refuses entries but never an
exit, and a risk-reducing close needs valid two-sided quotes; the brake pauses, holds and lifts only on a review row,
while exits continue; the quote gate refuses a missing or one-sided quote, size above the displayed size (with what
this account already took here) and protection that cannot be sold back; every law conforms and every reason is
kept."""

import copy
from dataclasses import FrozenInstanceError, replace

import pytest

from fno.risk.rules import MarginRoom
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.school.constants import ExitState, RefusalReason, RoadCode
from fno.school.contracts.decisions import LegSpec
from fno.school.contracts.snapshot import ContractKey
from fno.school.safety.account_laws import BrakeLaw, DailyStopLaw, ProtectedLaw
from fno.school.safety.c2_laws import C2Law, margin_numbers
from fno.school.safety.law_set import SafetyLaws, refusals
from fno.school.safety.margin_law import margin_not_checked
from fno.school.safety.quote_laws import GATE_REASONS, ImpossiblePriceLaw, QuoteGateLaw
from fno.school.safety.wiring import build_safety_laws
from tests.school.accounts.account_builders import NEXT, accounts, marks, opening, spread_quotes
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c
from tests.school.execution.school_builders import AT, fills

from .law_builders import CFG, SETTINGS, FixedMargin, held, view

ALL = build_safety_laws(CFG, SETTINGS, {RoadCode.BANKNIFTY_MONTHLY: b.snapshot()})


def test_the_laws_in_their_fixed_order():
    assert [law.name for law in ALL.laws] == [
        "protected", "max_loss", "bucket_cap", "open_risk", "new_risk_day", "margin_room", "daily_stop",
        *(f"quote_gate:{reason}" for reason in GATE_REASONS), "impossible_price", "brake",
    ]  # fmt: skip


@pytest.mark.parametrize("law", ALL.laws, ids=lambda law: law.name)
def test_no_law_changes_a_proposal(law):
    for proposal in (b.put_spread(), b.put_spread(10_001), replace(b.put_spread(), legs=b.put_spread().legs[:1])):
        before = copy.deepcopy(proposal)
        law.check(proposal, view(), b.snapshot(), b.SESSION)
        assert proposal == before
    with pytest.raises(FrozenInstanceError):
        b.put_spread().lot = 60  # a law could not resize one if it tried


def test_every_reason_is_kept():
    naked = replace(b.put_spread(10_001), legs=b.put_spread().legs[:1])
    found = refusals(ALL.check(naked, view(loss_since_previous_slot=30_000), b.snapshot(quotes={}), b.SESSION))
    assert {RefusalReason.UNPROTECTED, RefusalReason.MAX_LOSS, RefusalReason.DAILY_STOP,
            RefusalReason.MISSING_QUOTE} <= set(found)  # fmt: skip


def test_a_clean_proposal_passes_every_law_but_margin_room_without_margin_rows():
    """Orchestrator, 22 Oct 2026 (revised): no usable margin row refuses, noted, never a guessed margin."""
    results = ALL.check(b.put_spread(), view(), b.snapshot(), b.SESSION)
    assert refusals(results) == (RefusalReason.MARGIN_ROOM,) and margin_not_checked(results[5])


@pytest.mark.parametrize(
    "legs",
    [
        (LegSpec(b.key(1000.0), "sell", 1),),  # naked short
        (LegSpec(b.key(1000.0), "sell", 2), LegSpec(b.key(900.0), "buy", 1)),  # more sold than bought
        (LegSpec(b.key(1000.0), "sell", 1), LegSpec(b.key(900.0, b.OptionKind.CALL), "buy", 1)),  # wrong type
        (
            LegSpec(b.key(1000.0), "sell", 1),
            LegSpec(ContractKey(b.EXPIRY.replace(day=30), 900.0, b.OptionKind.PUT), "buy", 1),
        ),  # another expiry  # fmt: skip
    ],
)
def test_only_protected_structures_pass(legs):
    assert ProtectedLaw().check(replace(b.put_spread(), legs=legs), view(), b.snapshot(), b.SESSION).reason == (
        RefusalReason.UNPROTECTED
    )


def test_the_daily_stop_refuses_entries_after_a_real_loss_but_never_an_exit(tmp_path):
    port, entry = accounts(tmp_path), opening(tmp_path, lots=10)
    port.view("CS1@1", marks(), b.SESSION)
    port.record("CS1@1", entry)
    lost = port.view("CS1@1", marks(spread_quotes(100.0, 4.5), NEXT), NEXT)
    assert lost.loss_since_previous_slot >= 25_000
    assert not DailyStopLaw(25_000).check(b.put_spread(), lost, b.snapshot(), NEXT).passed
    closing = fills(tmp_path).exit(entry.position, b.snapshot(quotes=spread_quotes(100.0, 4.5)), "cd" * 32, b.seal(),
                                   AT)  # fmt: skip
    assert closing.filled, "the fill port's exit never asks the laws"
    one_sided = {**spread_quotes(100.0, 4.5), b.key(1000.0): replace(b.quote(99.5, 100.5), bid=None)}
    assert fills(tmp_path).exit(entry.position, b.snapshot(quotes=one_sided), "cd" * 32, b.seal(), AT).state == (
        ExitState.EXIT_WAITING_QUOTE
    )


def test_the_brake_pauses_holds_and_lifts_only_on_a_review():
    law = BrakeLaw(120_000)
    engaged = view(equity=1_880_000, brake_engaged_on=b.SESSION)
    assert law.check(b.put_spread(), engaged, b.snapshot(), b.SESSION).reason == RefusalReason.BRAKE
    recovered = view(equity=2_100_000, equity_high=2_100_000, brake_engaged_on=b.SESSION)
    assert not law.check(b.put_spread(), recovered, b.snapshot(), b.SESSION).passed, "held across sessions"
    lifted = view(brake_engaged_on=b.SESSION, brake_lifted_on=b.SESSION)
    assert law.check(b.put_spread(), lifted, b.snapshot(), b.SESSION).passed


def test_exits_continue_under_the_brake(tmp_path):
    entry = opening(tmp_path)
    assert fills(tmp_path).exit(entry.position, b.snapshot(), "cd" * 32, b.seal(), AT).filled


@pytest.mark.parametrize(
    ("quotes", "reason"),
    [
        ({b.key(1000.0): b.quote()}, RefusalReason.MISSING_QUOTE),
        ({b.key(1000.0): b.quote(), b.key(900.0): replace(b.quote(4.0, 5.0), ask=None)}, RefusalReason.ONE_SIDED_QUOTE),
        ({b.key(1000.0): b.quote(), b.key(900.0): replace(b.quote(4.0, 5.0), valid=False)},
         RefusalReason.ONE_SIDED_QUOTE),
        ({b.key(1000.0): b.quote(size=29), b.key(900.0): b.quote(4.0, 5.0)}, RefusalReason.SIZE_ABOVE_DISPLAYED),
        ({b.key(1000.0): b.quote(), b.key(900.0): replace(b.quote(4.0, 5.0), bid_qty=29)},
         RefusalReason.PROTECTION_UNSELLABLE),
    ],
)  # fmt: skip
def test_the_quote_gate_refuses_each_problem_with_its_own_reason(quotes, reason):
    found = refusals(ALL.check(b.put_spread(), view(), b.snapshot(quotes=quotes), b.SESSION))
    assert reason in found and not set(found) & (set(GATE_REASONS) - {reason})


def test_the_size_this_account_already_took_here_counts():
    """E4d per account: a position this account entered at this snapshot holds 30 units of the 900 put's ask and its
    sell-back on the bid, so 59 shown no longer covers a second 30; another road's or session's position does not."""
    snapshot = b.snapshot(quotes={b.key(1000.0): b.quote(size=1000), b.key(900.0): b.quote(4.0, 5.0, size=59)})
    law = QuoteGateLaw(RefusalReason.SIZE_ABOVE_DISPLAYED)
    here = held("h1", (1100.0, 900.0))
    assert not law.check(b.put_spread(), view(opened_this_session=(here,)), snapshot, b.SESSION).passed
    for elsewhere in (replace(here, road=RoadCode.NIFTY_MONTHLY), replace(here, opened=b.SESSION.replace(day=1))):
        assert law.check(b.put_spread(), view(opened_this_session=(elsewhere,)), snapshot, b.SESSION).passed


def spread_to(long: float) -> object:
    return replace(b.put_spread(), legs=(LegSpec(b.key(1000.0), "sell", 1), LegSpec(b.key(long), "buy", 1)))


def ladder(count: int) -> tuple:
    return tuple(held(f"h{n}", (1000.0 + 100 * n, 900.0 + 100 * n)) for n in range(1, count + 1))


# One snapshot per law: the fixture's good 1000/900 puts plus a 700 put with the law's own problem; the passing
# proposal is the 1000/900 spread, the refusing one buys the 700 instead (or carries the account's problem).
BAD_700 = {
    "quote_gate:missing_quote": None,
    "quote_gate:one_sided_quote": replace(b.quote(1.0, 2.0), ask=None),
    "quote_gate:size_above_displayed": b.quote(1.0, 2.0, size=1),
    "quote_gate:protection_unsellable": replace(b.quote(1.0, 2.0), bid_qty=1),
    "impossible_price": b.quote(9.5, 10.0),  # bought for the credit received: a spread that cannot win
}
REFUSING = {
    "protected": (replace(b.put_spread(), legs=b.put_spread().legs[:1]), view()),
    "max_loss": (b.put_spread(10_001), view()),
    "bucket_cap": (b.put_spread(), view(open_positions=ladder(11))),
    "open_risk": (b.put_spread(), view(open_positions=ladder(60))),
    "new_risk_day": (b.put_spread(), view(opened_this_session=ladder(20))),
    "daily_stop": (b.put_spread(), view(loss_since_previous_slot=25_000)),
    "brake": (b.put_spread(), view(equity=1_880_000)),
    **{name: (spread_to(700.0), view()) for name in BAD_700},
}


@pytest.mark.parametrize("law", [law for law in ALL.laws if law.name != "margin_room"], ids=lambda law: law.name)
def test_every_law_conforms(law):
    quotes = dict(b.snapshot().quotes)
    if BAD_700.get(law.name) is not None:
        quotes[b.key(700.0)] = BAD_700[law.name]
    c.check_safety_law(law, (b.put_spread(), view()), REFUSING[law.name], b.snapshot(quotes=quotes))


def test_margin_room_conforms_with_a_margin_it_can_read():
    law = C2Law("margin_room", MarginRoom(FixedMargin(), SimulatorTradeCosts(CFG["charges"])),
                RefusalReason.MARGIN_ROOM, margin_numbers, {})  # fmt: skip
    c.check_safety_law(law, (b.put_spread(), view()), (b.put_spread(), view(cash=1_000.0, equity=1_000.0)),
                       b.snapshot())  # fmt: skip


def test_a_law_set_needs_distinct_names_and_its_own_session():
    with pytest.raises(ValueError, match="distinct"):
        SafetyLaws((DailyStopLaw(1), DailyStopLaw(2)))
    with pytest.raises(ValueError, match="own session"):
        ALL.check(b.put_spread(), view(), b.snapshot(), NEXT)


def test_impossible_price_is_judged_only_with_every_touch():
    assert ImpossiblePriceLaw().check(b.put_spread(), view(), b.snapshot(quotes={}), b.SESSION).passed
