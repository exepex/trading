"""Story MS-P1j: the per-road quote-refusal share, the "why refused" breakdown over every reason a decision carried
(Judge I's note), and margin-not-checked causes counted by name, never by quoting a note."""

from dataclasses import replace

from fno.school.constants import SLOT_1500, NoTradeReason, Outcome, RefusalReason, RoadCode
from fno.school.contracts.decisions import Decision
from fno.school.contracts.records import DecisionRecord
from fno.school.contracts.safety import LawResult
from fno.school.fleet.quote_share import quote_shares, reason_counts, share_lines
from fno.school.safety.margin_law import MARGIN_NOT_CHECKED
from tests.school.contracts import builders as b

ROAD = RoadCode.BANKNIFTY_MONTHLY
SECRET_LEG = "PE 1000 2026-11-23"


def record(*failed: tuple[str, RefusalReason, str], road: RoadCode = ROAD) -> DecisionRecord:
    results = tuple(LawResult(law, False, reason, note=note) for law, reason, note in failed)
    if failed:
        decision = replace(b.decision(), road=road, outcome=Outcome.REFUSED, reason=failed[0][1])
    else:
        decision = Decision("CS1@1", road, b.SESSION, Outcome.NO_TRADE, NoTradeReason.RULE_NOT_FIRED)
    return DecisionRecord(b.SESSION, SLOT_1500, road, "ab" * 32, "s", "cd" * 32, None, decision, results)


MISSING = ("quote_gate:missing_quote", RefusalReason.MISSING_QUOTE, "")
MAX_LOSS = ("max_loss", RefusalReason.MAX_LOSS, "")
MARGIN = ("margin_room", RefusalReason.MARGIN_ROOM, f"{MARGIN_NOT_CHECKED}no valid two-sided quote: {SECRET_LEG}")


def test_the_share_counts_a_decision_once_when_any_quote_law_refused_it():
    records = (record(MISSING, MAX_LOSS), record(MAX_LOSS), record())
    [share] = quote_shares(records)
    assert (share.road, share.scheduled, share.quote_refused) == (ROAD, 3, 1)


def test_the_breakdown_counts_every_reason_a_decision_carried_and_says_so():
    records = (record(MISSING, MAX_LOSS, MARGIN), record(MAX_LOSS))
    assert reason_counts(records) == {(ROAD, RefusalReason.MISSING_QUOTE): 1, (ROAD, RefusalReason.MAX_LOSS): 2,
                                      (ROAD, RefusalReason.MARGIN_ROOM): 1}  # fmt: skip
    [line] = [line for line in share_lines(records) if "reasons" in line]
    assert "a decision can have several" in line and "max_loss x2" in line and "missing_quote x1" in line


def test_a_margin_cause_is_counted_by_name_and_no_line_quotes_a_note():
    lines = share_lines((record(MARGIN), record(MARGIN)))
    assert f"{ROAD}: margin not checked (no valid two-sided quote) x2" in lines
    assert not any(SECRET_LEG in line for line in lines)


FINNIFTY = RoadCode.FINNIFTY_MONTHLY


def driver_stop(road: RoadCode = FINNIFTY, reason: NoTradeReason = NoTradeReason.NO_VALID_QUOTES) -> DecisionRecord:
    decision = Decision("CS1@1", road, b.SESSION, Outcome.NO_TRADE, reason)
    return DecisionRecord(b.SESSION, SLOT_1500, road, "ab" * 32, "s", "cd" * 32, None, decision, ())


def test_drivers_that_stop_on_no_valid_quotes_are_counted_beside_the_law_refusals():
    """Dry run 1 (23 Oct, P-e1): "FINNIFTY-M: 0 of 9 refused for quotes" while 6 decisions were no_valid_quotes."""
    records = tuple(driver_stop() for _ in range(6)) + tuple(record(road=FINNIFTY) for _ in range(3))
    [share] = quote_shares(records)
    assert (share.scheduled, share.quote_refused, share.driver_stops) == (9, 0, 6)
    assert "FINNIFTY-M: 0 of 9 refused for quotes (0%); 6 more ended no_valid_quotes in the driver" in share_lines(
        records
    )


def test_the_line_is_byte_identical_when_no_driver_stopped_on_quotes():
    records = (record(MISSING), record(), driver_stop(reason=NoTradeReason.RULE_NOT_FIRED, road=ROAD))
    assert [line for line in share_lines(records) if "refused for quotes" in line] == [
        f"{ROAD}: 1 of 3 refused for quotes (33%)"
    ]


def test_a_decision_a_law_refused_is_not_also_counted_as_a_driver_stop():
    both = replace(record(MISSING), decision=Decision("CS1@1", ROAD, b.SESSION, Outcome.NO_TRADE,
                                                      NoTradeReason.NO_VALID_QUOTES))  # fmt: skip
    [share] = quote_shares((both,))
    assert (share.quote_refused, share.driver_stops) == (1, 0)


def test_another_no_trade_reason_and_another_outcome_are_not_driver_stops():
    refused_for_other = record(MAX_LOSS)
    [share] = quote_shares((driver_stop(reason=NoTradeReason.N0, road=ROAD), refused_for_other))
    assert share.driver_stops == 0
