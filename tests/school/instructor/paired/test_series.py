"""Part d's values and series (story MS-INS, criteria 1-4 and 9): abstentions worth 0 and counted, one point per
session, the cut at the first open pair, and what is left out."""

from dataclasses import replace
from datetime import date

import pytest

from fno.school.constants import SLOT_1500, Outcome, RoadCode
from fno.school.contracts.decisions import Decision
from fno.school.contracts.records import DecisionRecord
from fno.school.instructor.contracts import Measure
from fno.school.instructor.paired.series import paired_series
from fno.school.instructor.paired.values import RoadSlot, SlotStatus, road_slot
from tests.school.contracts.builders import put_spread
from tests.school.instructor.builders import outcome

A, B = RoadCode.NIFTY_MONTHLY, RoadCode.BANKNIFTY_MONTHLY
S1, S2, S3 = date(2026, 12, 1), date(2026, 12, 2), date(2026, 12, 3)
C, AB, OP, UN = SlotStatus.CLOSED, SlotStatus.ABSTAINED, SlotStatus.OPEN, SlotStatus.UNAVAILABLE


def slots(driver, rows):
    return {(s, r): RoadSlot(s, r, driver, status, ror, ticket) for s, r, status, ror, ticket in rows}


DRIVER = slots("CS1@1", [(S1, A, C, 0.20, False), (S1, B, AB, None, False), (S2, A, C, -0.10, True),
                         (S2, B, C, 0.05, False), (S3, A, C, 0.30, False), (S3, B, C, 0.00, False)])  # fmt: skip
CONTROL = slots("RC1@1", [(S1, A, C, -0.10, False), (S1, B, C, 0.10, False), (S2, A, AB, None, False),
                          (S2, B, C, -0.05, False), (S3, A, C, 0.10, True), (S3, B, AB, None, False)])  # fmt: skip


def test_the_hand_computed_pairs_over_three_sessions_and_two_roads():
    """S1: (0.20 - -0.10, 0 - 0.10) -> mean 0.10; S2: (-0.10 - 0, 0.05 - -0.05) -> mean 0.00; S3: (0.30 - 0.10,
    0 - 0) -> mean 0.10. Abstentions: driver 1 (S1 B), control 2 (S2 A, S3 B). Executed only: the driver's ticket
    on S2 A and the control's on S3 A count as 0 and as abstentions: S2 -> (0 - 0, 0.10) mean 0.05; S3 -> (0.30 - 0,
    0) mean 0.15."""
    per = paired_series(DRIVER, CONTROL, set(DRIVER), Measure.PER_OPPORTUNITY)
    assert per.days == (S1, S2, S3) and per.values == pytest.approx((0.10, 0.00, 0.10))
    assert (per.road_slots, per.driver_abstentions, per.control_abstentions, per.unavailable, per.after_cut) == (
        6, 1, 2, 0, 0)  # fmt: skip
    executed = paired_series(DRIVER, CONTROL, set(DRIVER), Measure.EXECUTED)
    assert executed.values == pytest.approx((0.10, 0.05, 0.15))
    assert (executed.driver_abstentions, executed.control_abstentions) == (2, 3)


def test_five_roads_on_one_session_are_one_point():
    roads = tuple(RoadCode)
    driver = slots("D@1", [(S1, r, C, 0.1 * i, False) for i, r in enumerate(roads)])
    control = slots("N0@1", [(S1, r, AB, None, False) for r in roads])
    series = paired_series(driver, control, set(driver), Measure.PER_OPPORTUNITY)
    assert len(series.days) == 1 and series.road_slots == 5 and series.values == pytest.approx((0.2,))


def test_the_series_stops_at_the_first_open_pair_and_counts_what_closed_after_it():
    driver = {**DRIVER, (S2, B): replace(DRIVER[(S2, B)], status=OP, return_on_risk=None)}
    series = paired_series(driver, CONTROL, set(driver), Measure.PER_OPPORTUNITY)
    assert series.days == (S1,) and series.after_cut == 3  # S2 A, and S3's two pairs


def test_an_unavailable_slot_on_either_side_is_left_out_and_counted():
    control = {**CONTROL, (S1, A): replace(CONTROL[(S1, A)], status=UN, return_on_risk=None)}
    series = paired_series(DRIVER, control, set(DRIVER), Measure.PER_OPPORTUNITY)
    assert series.unavailable == 1 and series.values[0] == pytest.approx(-0.10)  # only S1 B: 0 - 0.10


def test_only_the_common_road_days_are_paired_and_none_gives_an_empty_series():
    series = paired_series(DRIVER, CONTROL, {(S3, A)}, Measure.PER_OPPORTUNITY)
    assert series.days == (S3,) and series.road_slots == 1
    assert paired_series(DRIVER, CONTROL, set(), Measure.PER_OPPORTUNITY).days == ()


def _record(result: Outcome, reason: str = "") -> DecisionRecord:
    proposal = put_spread() if result in (Outcome.TRADE, Outcome.TICKET, Outcome.REFUSED) else None
    reason = reason or {Outcome.TICKET: "trade_limit", Outcome.NO_TRADE: "rule_not_fired", Outcome.REFUSED: "max_loss",
                        Outcome.UNAVAILABLE: "driver_error"}.get(result, "")  # fmt: skip
    return DecisionRecord(
        S1, SLOT_1500, B, "aa" * 32, "x", "ab" * 32, None, Decision("CS1@1", B, S1, result, reason, proposal)
    )


@pytest.mark.parametrize("result, status", [(Outcome.NO_TRADE, AB), (Outcome.REFUSED, AB), (Outcome.UNAVAILABLE, UN),
                                            (Outcome.TRADE, OP)])  # fmt: skip
def test_each_decision_outcome_maps_to_its_slot(result, status):
    assert road_slot(_record(result), {}, ()).status == status


def test_a_closed_entry_takes_its_return_on_risk_and_an_unfilled_one_is_unavailable():
    record, key = _record(Outcome.TICKET), ("CS1@1", B, S1)
    closed = {key: replace(outcome("cd" * 32), is_ticket=True)}
    slot = road_slot(record, closed, ())
    assert slot.status == C and slot.return_on_risk == closed[key].return_on_risk and slot.is_ticket
    assert road_slot(record, closed, {key}).status == UN


def test_a_road_slot_has_a_return_exactly_when_closed():
    with pytest.raises(ValueError):
        RoadSlot(S1, A, "D@1", C)
    with pytest.raises(ValueError):
        RoadSlot(S1, A, "D@1", AB, 0.0)
