"""E8 rule 11 and judge 203 condition 4: the step seals the availability file, then applies every waiting entry and
exit of the verdict accounts oldest order time first (an entry without a delivered card first of all); a refused file
or a failure ends it refused or failed, and the seal and the rewritten totals are committed with its entry. Before the
live date it only seals, and nothing it meets then blocks an entry (judge 203 early view 5)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fno.books.account import PaperAccount
from fno.books.daily_totals import write_daily_totals
from fno.constants import OUTCOME_ENTRY_PENDING, OUTCOME_EXIT_ORDERED, STEP_FAILED, STEP_NOT_LIVE, STEP_OK, STEP_REFUSED
from fno.desk.owner_timing.account_writes import StepAccountWrites
from fno.desk.owner_timing.availability import AvailabilityRefused, Seal
from fno.desk.owner_timing.live_switch import LiveFromStep
from fno.desk.owner_timing.order_times import CardTimes
from fno.desk.owner_timing.pending import OrderMissing, OrderSource
from fno.desk.owner_timing.step import OwnerTimingStep
from fno.desk.owner_timing.timed_reads import StepDeadline
from fno.desk.records import DeskEvent, DeskRecords
from fno.desk.wiring import open_desk_journal
from tests.desk.builders import STRATEGY, at, enter, fly_order, fly_rows, write_snapshot
from tests.desk_owner_timing.fakes import MemoryTimingLog, Settable, ist

BOOK = "book1_rules"
SEALS = Path("research/desk/availability_seals.csv")
MON, TUE = date(2026, 10, 12), date(2026, 10, 13)


class Sealer:
    def __init__(self, seal=None, refuse: str = ""):
        self.result, self.refuse = seal, refuse

    def seal(self, now):
        if self.refuse:
            raise AvailabilityRefused(self.refuse)
        return self.result


class Cards(CardTimes):
    def __init__(self, times: dict):
        self.times = times

    def delivered(self, day):
        return self.times.get(day)


class Orders(OrderSource):
    def __init__(self, missing: str = ""):
        self.missing = missing

    def order(self, pending):
        if pending.trade_id == self.missing:
            raise OrderMissing(f"no decision run for {pending.trade_id}")
        return fly_order(pending.trade_id)


class Applied:
    """Stands in for the entry and exit fills: the order items reach them, and what each returns."""

    def __init__(self, seen: list, outcome: str | None = "filled"):
        self.seen, self.outcome = seen, outcome

    def apply(self, *args):
        trade_id = args[0].proposal.trade_id if len(args) == 3 else args[1].trade_id
        self.seen.append(trade_id)
        return self.outcome


def handed_over(root, trade_id: str, day: date) -> None:
    with open_desk_journal(BOOK, root) as journal:
        journal.record_event(DeskEvent(f"{trade_id}:{OUTCOME_ENTRY_PENDING}", day, BOOK, STRATEGY, trade_id,
                                       f"d-{trade_id}", "", "", OUTCOME_ENTRY_PENDING, "handed over"))  # fmt: skip


def step(root, cards=None, alerts=None, sealer=None, orders=None, entry_outcome="filled"):
    seen: list[str] = []
    writes = StepAccountWrites(lambda book: open_desk_journal(book, root), root)
    built = OwnerTimingStep(
        (BOOK,), sealer or Sealer(), root / SEALS, writes, lambda book: DeskRecords(PaperAccount(root, book)),
        orders or Orders(), cards or Cards({}), alerts or MemoryTimingLog(), Applied(seen, entry_outcome),
        Applied(seen), StepDeadline(), Settable(ist(date(2026, 10, 15), 14, 33)),
    )  # fmt: skip
    return built, seen


def test_items_are_applied_oldest_order_time_first(root, store, snapshots, entry_desk):
    write_snapshot(store, "exec", fly_rows(), at(15, 15), at(15, 15, 40))
    enter(root, snapshots, entry_desk, fly_order("x1"))
    with open_desk_journal(BOOK, root) as journal:
        journal.record_event(DeskEvent(f"x1:{OUTCOME_EXIT_ORDERED}", TUE, BOOK, STRATEGY, "x1", "x1:exit_ordered",
                                       "", "", OUTCOME_EXIT_ORDERED, "time stop"))  # fmt: skip
    handed_over(root, "late", TUE)
    handed_over(root, "early", MON)
    handed_over(root, "nocard", date(2026, 10, 9))
    alerts = MemoryTimingLog()
    alerts.alerted(BOOK, "x1", ist(MON, 15, 40))
    cards = Cards({MON: ist(MON, 15, 16), TUE: ist(TUE, 15, 16)})
    built, seen = step(root, cards, alerts)
    outcome = built.run(date(2026, 10, 15))
    assert seen == ["nocard", "early", "x1", "late"]
    assert outcome.result["status"] == STEP_OK and outcome.result["reason"] == "4 applied, 0 waiting for their due mark"
    assert outcome.paths == (write_daily_totals(root, BOOK),)  # rewritten by the step, committed with its entry


def test_an_entry_before_its_due_mark_is_counted_as_waiting(root):
    handed_over(root, "t1", MON)
    built, _ = step(root, Cards({MON: ist(MON, 15, 16)}), entry_outcome=None)
    assert built.run(date(2026, 10, 15)).result["reason"] == "0 applied, 1 waiting for their due mark"


def test_a_refused_availability_file_refuses_the_step_before_any_item(root):
    handed_over(root, "t1", MON)
    built, seen = step(root, sealer=Sealer(refuse="a sealed line changed"))
    outcome = built.run(date(2026, 10, 15))
    assert outcome.result == {"status": STEP_REFUSED, "reason": "a sealed line changed"} and not seen
    assert outcome.paths == () and outcome.inputs == {"sealed": False}


def test_an_order_that_cannot_be_rebuilt_fails_the_step_and_keeps_the_seal(root):
    handed_over(root, "t1", MON)
    built, _ = step(root, sealer=Sealer(Seal(3, "ab" * 32)), orders=Orders(missing="t1"))
    outcome = built.run(date(2026, 10, 15))
    assert outcome.result["status"] == STEP_FAILED and outcome.result["reason"].startswith("OrderMissing")
    assert outcome.paths == (root / SEALS,) and outcome.inputs == {"sealed": True}


class Raising(Sealer):
    def seal(self, now):
        raise RuntimeError("Drive settings missing")


def test_before_the_live_date_it_only_seals_and_blocks_nothing(root, alerts):
    handed_over(root, "t1", MON)
    built, seen = step(root, sealer=Sealer(Seal(3, "ab" * 32)))
    outcome = LiveFromStep(date(2026, 11, 2), built, alerts).run(date(2026, 10, 15))
    assert outcome.result["status"] == STEP_NOT_LIVE and outcome.paths == (root / SEALS,) and not seen
    assert not alerts.sent
    assert LiveFromStep(date(2026, 10, 15), built, alerts).run(date(2026, 10, 15)).result["status"] == STEP_OK


def test_a_failed_seal_while_off_is_alerted_once_and_blocks_nothing(root, tmp_path, alerts):
    failed = LiveFromStep(None, step(root, sealer=Raising())[0], alerts).run(date(2026, 10, 15))
    assert (
        failed.result["status"] == STEP_NOT_LIVE and "sealing failed: Drive settings missing" in failed.result["reason"]
    )
    assert len(alerts.sent) == 1 and "sealing failed" in alerts.sent[0]
