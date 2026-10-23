"""Story E4, entries: fills at the snapshot's touch with its hash (criterion 1), protection first, no fill on a thin or
invalid quote, partial fills unwound with their legging cost (criterion 2), the risk manager's refusal (C2, issue #85)
and the point-in-time rule (never a later quote)."""

import csv
import hashlib
from datetime import date, timedelta

import pytest

from fno.books.account import PaperAccount
from fno.books.equity import trade_positions
from fno.config import load_app_config
from fno.constants import (
    BOOK1_RULES,
    BOOK2_HYBRID,
    FILL_OPEN,
    FILL_UNWIND,
    OPTION_CALL,
    OPTION_PUT,
    OUTCOME_EXIT_ORDERED,
    OUTCOME_NOT_OPENED,
    OUTCOME_OPENED,
    OUTCOME_PARTIAL_FILL,
    OUTCOME_REFUSED,
    PROTECTION_NOT_BUYABLE,
    SHORT_LEG_NOT_SELLABLE,
    SIDE_BUY,
    SIDE_SELL,
)
from fno.costs import order_charges
from fno.desk.records import DeskRecords
from fno.desk.snapshot import SnapshotError
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.risk.book_view import load_risk_book
from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.wiring import build_risk_manager
from tests.margin_tables import local_tables
from tests.stress_factor_files import factor_file

from .builders import (
    CHARGES,
    DAY,
    LOT,
    STRATEGY,
    at,
    contract,
    decision_market,
    enter,
    fly_order,
    fly_proposal,
    fly_rows,
    write_snapshot,
)

CE, PE = OPTION_CALL, OPTION_PUT


def records(root, book=BOOK1_RULES):
    return DeskRecords(PaperAccount(root, book))


def charges(price, side):
    return order_charges(price, LOT, side, CHARGES)


@pytest.fixture
def execution(store):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))


def test_each_fill_is_at_the_snapshot_ask_or_bid_with_its_hash_and_protection_first(root, store, snapshots,
                                                                                    entry_desk, execution):  # fmt: skip
    result = enter(root, snapshots, entry_desk, fly_order())
    assert result.outcome == OUTCOME_OPENED
    rows = records(root).fill_rows()
    expected = [(25200, CE, SIDE_BUY, 71.0), (24800, PE, SIDE_BUY, 60.5), (25000, CE, SIDE_SELL, 150.0),
                (25000, PE, SIDE_SELL, 140.0)]  # fmt: skip
    assert [(float(r["strike"]), r["type"], r["side"], float(r["price"])) for r in rows] == expected
    digest = hashlib.sha256(store.get(QuoteSnapshotRecorder.path(DAY, "exec.csv"))).hexdigest()
    assert {(r["snapshot_id"], r["snapshot_sha256"], r["action"], r["decision_id"]) for r in rows} == {
        ("exec", digest, FILL_OPEN, "d-t1")
    }
    assert all(r["units"] == "65" and r["quote_age_unknown"] == "True" and r["book"] == BOOK1_RULES for r in rows)
    assert {r["strategy"] for r in rows} == {STRATEGY}  # E6 scores each version by this tag
    assert not {"quote_bid", "quote_ask"} & set(rows[0])  # story E2b: the touch stays in the hash-checked snapshot
    # The money (E1's ledger): hand computation, premium at the touch minus C1's charges on each fill price.
    premium = (150.0 + 140.0 - 71.0 - 60.5) * LOT  # Rs 10,302.50 received
    cost = charges(71.0, SIDE_BUY) + charges(60.5, SIDE_BUY) + charges(150.0, SIDE_SELL) + charges(140.0, SIDE_SELL)
    account = PaperAccount(root, BOOK1_RULES)
    assert premium == 10302.5
    assert account.summary()["cash_rs"] == pytest.approx(2_000_000 + premium - cost, abs=1e-9)
    assert [f.fill_id for f in account.fills()] == [r["fill_id"] for r in rows]


def test_a_snapshot_finished_after_the_run_s_clock_is_never_priced(root, snapshots, entry_desk, clock, execution):
    clock.set(at(15, 15, 39))  # one second before the capture finished: its quotes are later prices
    with pytest.raises(SnapshotError, match="after the run's time"):
        enter(root, snapshots, entry_desk, fly_order())
    assert PaperAccount(root, BOOK1_RULES).fills() == [] and records(root).fill_rows() == []


def test_a_quote_file_changed_after_recording_or_from_another_day_is_refused(store, snapshots):
    write_snapshot(store, "changed", fly_rows(), at(15, 15), at(15, 15, 40), sha="0" * 64)
    with pytest.raises(SnapshotError, match="hash"):
        snapshots.snapshot(DAY, "changed")
    yesterday = DAY - timedelta(days=1)
    write_snapshot(store, "old", fly_rows(), at(15, 15, day=yesterday), at(15, 16, day=yesterday), day=DAY)
    with pytest.raises(SnapshotError, match="captured on"):
        snapshots.snapshot(DAY, "old")
    with pytest.raises(SnapshotError, match="not in the quote store"):
        snapshots.snapshot(DAY, "missing")


@pytest.mark.parametrize("size, outcome", [(64, OUTCOME_NOT_OPENED), (65, OUTCOME_OPENED)])
def test_a_leg_fills_only_when_the_size_at_the_touch_covers_its_units(root, store, snapshots, entry_desk, size,
                                                                      outcome):  # fmt: skip
    write_snapshot(store, "exec", fly_rows({(25200, CE): {"size": size}}), at(15, 15), at(15, 15, 40))
    result = enter(root, snapshots, entry_desk, fly_order())
    assert result.outcome == outcome
    if outcome == OUTCOME_NOT_OPENED:
        assert result.reason == f"{PROTECTION_NOT_BUYABLE} ({contract(25200, CE)}, 65 units)"  # story E4c's code
        assert "64" not in result.reason  # the size shown is a quote figure: never in the public reason
        (events,) = root.rglob("desk_events.csv")
        (row,) = csv.DictReader(events.open())
        assert row["reason"] == result.reason  # the committed row carries the same reason, no size
        assert PaperAccount(root, BOOK1_RULES).fills() == []


@pytest.mark.parametrize("change", [None, {"valid": False, "reason": "no trade today"}, {"ask": None}])
def test_a_protective_leg_without_a_valid_quote_opens_nothing(root, store, snapshots, entry_desk, change):
    write_snapshot(store, "exec", fly_rows({(25200, CE): change}), at(15, 15), at(15, 15, 40))
    result = enter(root, snapshots, entry_desk, fly_order())
    assert result.outcome == OUTCOME_NOT_OPENED
    assert result.reason == f"{PROTECTION_NOT_BUYABLE} ({contract(25200, CE)}, 65 units)"  # story E4c
    assert PaperAccount(root, BOOK1_RULES).fills() == [] and records(root).fill_rows() == []


def test_a_second_protective_leg_failing_buys_nothing(root, store, snapshots, entry_desk):
    """Story E4c (decision 43): the second protective leg is checked before the first is bought."""
    write_snapshot(store, "exec", fly_rows({(24800, PE): None}), at(15, 15), at(15, 15, 40))
    result = enter(root, snapshots, entry_desk, fly_order())
    assert (result.outcome, result.reason) == (
        OUTCOME_NOT_OPENED,
        f"{PROTECTION_NOT_BUYABLE} ({contract(24800, PE)}, 65 units)",
    )
    assert result.legging_cost_rs is None and PaperAccount(root, BOOK1_RULES).fills() == []
    assert records(root).fill_rows() == []


def test_the_guard_unwinds_the_first_protective_leg_when_the_second_fails_after_the_check(
    root, store, snapshots, entry_desk, check_passed
):
    """E4 criterion 2's assertions, unchanged, now through the guard (story E4c, decision 43)."""
    write_snapshot(store, "exec", fly_rows({(24800, PE): None}), at(15, 15), at(15, 15, 40))
    result = enter(root, snapshots, entry_desk, fly_order())
    assert result.outcome == OUTCOME_PARTIAL_FILL and "no quote in the snapshot" in result.reason
    assert result.legging_cost_rs == pytest.approx(
        (71.0 - 70.0) * LOT + charges(71.0, SIDE_BUY) + charges(70.0, SIDE_SELL)
    )
    assert not trade_positions(PaperAccount(root, BOOK1_RULES).fills())["t1"].is_open


def test_a_short_leg_that_cannot_be_sold_buys_no_protection(root, store, snapshots, entry_desk):
    """Story E4c: E4's unwind path for a short leg becomes a refusal before any leg fills; no legging cost."""
    write_snapshot(store, "exec", fly_rows({(25000, PE): {"valid": False}}), at(15, 15), at(15, 15, 40))
    result = enter(root, snapshots, entry_desk, fly_order())
    assert (result.outcome, result.reason) == (
        OUTCOME_NOT_OPENED,
        f"{SHORT_LEG_NOT_SELLABLE} ({contract(25000, PE)}, 65 units)",
    )
    assert result.legging_cost_rs is None and PaperAccount(root, BOOK1_RULES).fills() == []


def test_the_guard_unwinds_after_a_short_leg_fails_at_the_same_snapshot_with_its_legging_cost(
    root, store, snapshots, entry_desk, check_passed
):
    write_snapshot(store, "exec", fly_rows({(25000, PE): {"valid": False}}), at(15, 15), at(15, 15, 40))
    result = enter(root, snapshots, entry_desk, fly_order())
    assert result.outcome == OUTCOME_PARTIAL_FILL and "did not fill" in result.reason
    rows = records(root).fill_rows()
    unwind = [(r["contract"], r["side"], float(r["price"])) for r in rows if r["action"] == FILL_UNWIND]
    # Short leg bought back first (at the ask), then the protection sold (at the bid).
    assert unwind == [(contract(25000, CE), SIDE_BUY, 151.0), (contract(25200, CE), SIDE_SELL, 70.0),
                      (contract(24800, PE), SIDE_SELL, 60.0)]  # fmt: skip
    assert (-71.0 - 60.5 + 150.0 - 151.0 + 70.0 + 60.0) * LOT == -162.5  # premium lost to the spreads
    cost = sum(charges(p, s) for p, s in [(71.0, SIDE_BUY), (60.5, SIDE_BUY), (150.0, SIDE_SELL), (151.0, SIDE_BUY),
                                          (70.0, SIDE_SELL), (60.0, SIDE_SELL)])  # fmt: skip
    assert result.legging_cost_rs == pytest.approx(162.5 + cost, abs=1e-9)
    assert not trade_positions(PaperAccount(root, BOOK1_RULES).fills())["t1"].is_open  # the trade did not open


def test_an_unwind_leg_without_bid_size_stays_as_an_exit_order(root, store, snapshots, entry_desk, check_passed):
    """Through the guard (story E4c): the pending-unwind path is kept, with the same assertions."""
    changes = {(25000, PE): {"valid": False}, (24800, PE): {"bid_qty": 10}}
    write_snapshot(store, "exec", fly_rows(changes), at(15, 15), at(15, 15, 40))
    result = enter(root, snapshots, entry_desk, fly_order())
    assert result.outcome == OUTCOME_PARTIAL_FILL and result.legging_cost_rs is None
    events = [e["outcome"] for e in records(root).event_rows("t1")]
    assert events == [OUTCOME_PARTIAL_FILL, OUTCOME_EXIT_ORDERED]
    assert trade_positions(PaperAccount(root, BOOK1_RULES).fills())["t1"].units == {
        contract(25200, CE): 0,
        contract(24800, PE): 65,
        contract(25000, CE): 0,
    }


@pytest.mark.parametrize("margin_as_of, opens", [("2026-09-01", False), ("2026-10-13", True)])
def test_the_risk_manager_s_refusal_for_stale_margins_fills_nothing(root, store, snapshots, entry_desk, execution,
                                                                    margin_as_of, opens):  # fmt: skip
    margins = root / "margins.csv"
    margins.write_text(",".join(MARGIN_COLUMNS) + f"\nSF,200,40000,0,0,test calculator,{margin_as_of}\n")
    stressed = {"factor_file": str(factor_file(1.5, date(2026, 10, 12)))}  # the day before the decision
    cfg = load_app_config(overrides={"risk": {"stressed_margin": stressed}})
    market = decision_market()
    manager = build_risk_manager(cfg, root, tables=local_tables(margins))
    decision = manager.evaluate(fly_proposal(), load_risk_book(root, BOOK1_RULES, market, {}), market)
    assert decision.ok == opens, decision.reasons
    result = enter(root, snapshots, entry_desk, fly_order(risk=decision))
    assert (result.outcome == OUTCOME_OPENED) == opens
    if not opens:
        assert result.reason.startswith("risk manager refused") and "older than 1 session(s)" in result.reason
        assert PaperAccount(root, BOOK1_RULES).fills() == []


def test_entries_refused_before_any_leg(root, store, snapshots, entry_desk, execution):
    write_snapshot(store, "partial", fly_rows(), at(15, 15), at(15, 15, 40), complete=False)
    cases = [
        (fly_order("a", decided_at=at(15, 15, 1)), "exec", "not before the execution snapshot"),
        (fly_order("b", risk=fly_order("b", book=BOOK2_HYBRID).risk), "exec", "risk decision is for book2_hybrid"),
        (fly_order("c"), "partial", "is incomplete: no new risk"),
    ]
    for order, snapshot_id, reason in cases:
        result = enter(root, snapshots, entry_desk, order, snapshot_id)
        assert result.outcome == OUTCOME_REFUSED and reason in result.reason
    assert PaperAccount(root, BOOK1_RULES).fills() == []
    assert [e["outcome"] for e in records(root).event_rows()] == [
        OUTCOME_REFUSED
    ] * 3  # refusals, apart from fill failures (E6)


def test_a_rerun_repeats_nothing(root, snapshots, entry_desk, execution):
    first = enter(root, snapshots, entry_desk, fly_order())
    ledger = PaperAccount(root, BOOK1_RULES).ledger_rows()
    assert enter(root, snapshots, entry_desk, fly_order()) == first
    assert PaperAccount(root, BOOK1_RULES).ledger_rows() == ledger and len(records(root).fill_rows()) == 4
