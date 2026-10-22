"""Law 3's margin room on MS-P1m's margin per trade (story section 6 item 7, revised; MS-P1m): C2's `MarginRoom`
unedited, each trade priced from its own `RoadTradeTerms` (index, expiry, legs, lot), and C2's proposal and open
trades built from the same terms by MS-P1m's factories. A margin that cannot be read refuses, with the note "margin
not checked: <cause>"; C2's own refusal for want of room carries no such note."""

from dataclasses import replace

import pytest

from fno.nse_margins.road_trades import RoadTradeTerms
from fno.risk.inputs import RiskInputError
from fno.risk.trade_costs import SimulatorTradeCosts
from fno.school.constants import RefusalReason, RoadCode
from fno.school.safety.c2_inputs import c2_inputs
from fno.school.safety.margin_law import MARGIN_NOT_CHECKED, margin_not_checked, margin_room_law
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c

from .law_builders import CFG, FixedMargin, MarginByIndex, NoMargin, held, view

COSTS = SimulatorTradeCosts(CFG["charges"])
NIFTY, BANKNIFTY = RoadCode.NIFTY_MONTHLY, RoadCode.BANKNIFTY_MONTHLY
POOR = view(cash=1_000.0, equity=1_000.0)


def check(margin, account=None, road=BANKNIFTY, slot=None):
    law = margin_room_law(margin, COSTS, slot or {})
    return law.check(b.put_spread(), account or view(), b.snapshot(road), b.SESSION)


def test_a_readable_margin_is_checked_by_c2_and_fails_closed_without_room():
    passed = check(FixedMargin())
    assert passed.passed and passed.value is not None and passed.note == "" and not margin_not_checked(passed)
    refused = check(FixedMargin(), POOR)
    assert refused.reason == RefusalReason.MARGIN_ROOM and refused.note == "" and not margin_not_checked(refused)
    c.check_safety_law(margin_room_law(FixedMargin(), COSTS, {}), (b.put_spread(), view()), (b.put_spread(), POOR),
                       b.snapshot())  # fmt: skip


def test_an_unreadable_margin_refuses_with_its_named_cause_never_a_number():
    refused = check(NoMargin())
    assert not refused.passed and refused.reason == RefusalReason.MARGIN_ROOM and margin_not_checked(refused)
    assert refused.note.startswith(MARGIN_NOT_CHECKED) and "SPAN file" in refused.note
    assert (refused.limit, refused.value) == (None, None)


class OnlyNifty(MarginByIndex):
    """Reads NIFTY's margin; any other index refuses by name, as MS-P1m's margin does for a missing part."""

    def margin(self, terms, day):
        if terms.underlying != "NIFTY":
            raise RiskInputError(f"school margin: no {terms.underlying} part in the session's SPAN file")
        return super().margin(terms, day)

    margin_at_entry = broker_margin = margin


def test_a_held_position_whose_margin_cannot_be_read_refuses_the_account_s_entries():
    other = held("h1", road=BANKNIFTY)
    refused = check(OnlyNifty(), view(open_positions=(other,)), road=NIFTY)
    assert margin_not_checked(refused) and "no BANKNIFTY part" in refused.note
    assert check(OnlyNifty(), road=NIFTY).passed


def test_equal_c2_terms_on_two_indices_get_their_own_margins():
    """MS-P1m's seam: the margin is read from each trade's own terms, so a NIFTY and a BANKNIFTY PCS 100 x 1 lot
    (equal structure, width and lots) are priced 5,000 and 9,000, never one for both."""
    nifty = held("n1", road=NIFTY)
    slot = {NIFTY: b.snapshot(NIFTY), BANKNIFTY: b.snapshot()}
    law = margin_room_law(MarginByIndex(), COSTS, slot)
    result = law.check(b.put_spread(), view(open_positions=(nifty,)), b.snapshot(), b.SESSION)
    assert result.passed and result.value == pytest.approx(5_000.0 + 9_000.0)


def test_c2_s_units_and_margin_come_from_one_set_of_terms():
    """MS-P1m's self-review case (a lot of 1 inside a 65-unit proposal needed Rs 840, not Rs 54,600): d builds C2's
    proposal and open trades through MS-P1m's factories, so C2's units are always lots x the terms' lot."""
    nifty = held("n1", road=NIFTY)
    slot = {NIFTY: b.snapshot(NIFTY)}
    inputs = c2_inputs(replace(b.put_spread(), lot=65), NIFTY, view(open_positions=(nifty,)), slot, b.SESSION)
    terms = inputs.proposal.terms
    assert isinstance(terms, RoadTradeTerms) and (terms.underlying, terms.lot, terms.lots) == ("NIFTY", 65, 1)
    assert inputs.proposal.lot_size == terms.lot and inputs.proposal.units == 65
    held_trade = inputs.book.open_trades[0]
    assert isinstance(held_trade.terms, RoadTradeTerms)
    assert sorted(held_trade.units.values()) == [-30, 30] == [s * held_trade.terms.lot for s in (-1, 1)]


def test_terms_of_two_expiries_or_a_leg_ratio_are_refused_before_c2():
    """C2's terms carry one expiry and one lot count; a calendar or a ratio cannot be sized, so every C2 law refuses."""
    later = b.ContractKey(b.EXPIRY.replace(day=30), 900.0, b.OptionKind.PUT)
    calendar = replace(b.put_spread(), legs=(b.put_spread().legs[0], replace(b.put_spread().legs[1], key=later)))
    ratio = replace(b.put_spread(), legs=(b.put_spread().legs[0], replace(b.put_spread().legs[1], lots=2)))
    for odd in (calendar, ratio):
        with pytest.raises(RiskInputError, match="C2 sizes one each"):
            c2_inputs(odd, BANKNIFTY, view(), {BANKNIFTY: b.snapshot()}, b.SESSION)
