"""Story STR1b criterion 2: scoreboard B counts C2's capital tied at entry (broker margin plus premium paid), never the
owner's stress reserve, which it reports apart. The record's figures come from C2's `margin_room` verdict."""

from datetime import date

from fno.books.versions import Segment
from fno.scoreboard.entry_facts import entry_facts
from tests.scoreboard.builders import record

SEGMENT = Segment("book1_rules", "book1_rules-v1", "matches")


def test_entry_facts_take_capital_tied_and_the_stress_reserve_apart():
    chosen = record("book1_rules", date(2026, 10, 14), "2026-10-14T1500", "o1", max_loss=6000.0, margin=35_214.75,
                    reserve=0.0)  # fmt: skip
    facts = entry_facts(chosen, SEGMENT, overridden=False)
    assert (facts.capital_tied, facts.stress_reserve) == (35_214.75, 0.0)


def test_a_record_with_a_stress_reserve_keeps_it_out_of_capital_tied():
    chosen = record("book1_rules", date(2026, 10, 14), "2026-10-14T1500", "o2", max_loss=6000.0, margin=112_600.0,
                    reserve=400.0)  # fmt: skip
    facts = entry_facts(chosen, SEGMENT, overridden=False)
    assert facts.capital_tied == 112_600.0 and facts.stress_reserve == 400.0


def test_a_trade_whose_record_has_no_capital_is_listed_not_dropped_silently():
    """An owner override after C2 could not compute a margin: the record's margin verdict has no numbers."""
    from fno.scoreboard.sections import _risk

    chosen = record("book1_rules", date(2026, 10, 14), "2026-10-14T1500", "o3", max_loss=6000.0)
    chosen["risk"]["verdicts"][0]["numbers"] = {}
    facts = entry_facts(chosen, SEGMENT, overridden=True)

    class Trade:
        trade_id, entry = "o3", facts

    class Series:
        days, risk_days, net_per_risk = (), 0.0, None

    assert facts.capital_tied is None and _risk([Trade()], Series())["no_capital"] == ["o3"]
