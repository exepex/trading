"""Story MS-P1j: reruns, the slot's running view, tickets, shared displayed size and the counts files."""

import csv
from dataclasses import dataclass, replace

from fno.school.constants import (
    SLOT_1500,
    ClosureReason,
    ExitReason,
    NoTradeReason,
    Outcome,
    RecordKind,
    RefusalReason,
    RoadCode,
    TicketReason,
)
from fno.school.contracts.decisions import Decision
from fno.school.contracts.fleet import RunMode
from fno.school.contracts.records import DecisionRecord, OutcomeRecord
from fno.school.contracts.safety import LawResult
from fno.school.dashcam.names import counts_path
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.counts_file import opportunity_path
from tests.school.contracts import builders as b
from tests.school.fleet.rig import DAY2, OPEN_ROAD, Rig, all_roads

CS1, REF = all_roads("CS1"), all_roads("REF")
TWO = (RoadCode.BANKNIFTY_MONTHLY, RoadCode.FINNIFTY_MONTHLY)


def trader(card=CS1, **kwargs) -> FakeDriver:
    return FakeDriver(card, b.put_spread(), **kwargs)


def sealed(rig, session):
    seal = rig.dashcam.find(session, SLOT_1500, RecordKind.DECISIONS)
    return tuple(r for r in rig.dashcam.read(seal) if isinstance(r, DecisionRecord))


@dataclass
class SlotCap:
    """A law that adds up the slot: refuses once the account's open positions (accepted ones included) reach `most`."""

    most: int
    name: str = "open_risk"

    def check(self, proposal, account, snapshot, session):
        held = len(account.open_positions)
        return LawResult(self.name, held < self.most, None if held < self.most else RefusalReason.OPEN_RISK)


def test_a_rerun_of_a_complete_session_seals_and_fills_nothing(tmp_path):
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(10_000),))
    first = rig.fleet.run(b.SESSION, RunMode.REPLAY)
    files = dict(rig.dashcam.files)
    again = rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert again.decisions == first.decisions and again.fills == () and rig.dashcam.files == files
    assert len(rig.accounts.ledgers["CS1@1"]) == 1


def test_a_rerun_after_a_crash_between_the_seal_and_the_fills_fills_once(tmp_path):
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(10_000),))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.accounts.ledgers.clear()  # as if the fills never happened
    for key in [k for k in rig.dashcam.files if k[2] != RecordKind.DECISIONS]:
        del rig.dashcam.files[key]
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert len(rig.accounts.ledgers["CS1@1"]) == 1


def test_the_slot_s_caps_see_the_trades_already_accepted(tmp_path):
    rig = Rig(tmp_path, (trader(),), (SlotCap(1),), open_roads=TWO)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    outcomes = sorted((r.road, r.decision.outcome, r.decision.reason) for r in sealed(rig, b.SESSION) if r.road in TWO)
    assert outcomes == [(RoadCode.BANKNIFTY_MONTHLY, Outcome.TRADE, ""),
                        (RoadCode.FINNIFTY_MONTHLY, Outcome.TICKET, TicketReason.ACCOUNT_LIMIT)]  # fmt: skip
    assert len(rig.accounts.ledgers["CS1@1"]) == 1 and len(rig.ticket_accounts.ledgers["CS1@1"]) == 1


def test_a_rule_beyond_the_slot_limit_is_a_ticket_in_its_own_ledger_and_its_outcome_says_so(tmp_path):
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(10_000),), max_new=0)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    [ticket] = [r for r in sealed(rig, b.SESSION) if r.road == OPEN_ROAD]
    assert (ticket.decision.outcome, ticket.decision.reason) == (Outcome.TICKET, TicketReason.TRADE_LIMIT)
    assert rig.accounts.ledgers == {} and len(rig.ticket_accounts.ledgers["CS1@1"]) == 1
    rig.fleet.drivers = (trader(exit_reason=ExitReason.SESSIONS_HELD),)
    rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    seal = rig.dashcam.find(DAY2, SLOT_1500, RecordKind.OUTCOMES)
    [outcome] = rig.dashcam.read(seal)
    assert isinstance(outcome, OutcomeRecord) and outcome.is_ticket


def test_two_accounts_on_one_displayed_size_one_entry_is_size_shared_and_stays_counted(tmp_path):
    thin = {key: replace(quote, bid_qty=30, ask_qty=30) for key, quote in b.snapshot().quotes.items()}
    snapshots = {(OPEN_ROAD, s): replace(b.snapshot(quotes=thin), session=s) for s in (b.SESSION, DAY2)}
    rig = Rig(tmp_path, (trader(), trader(REF)), (FakeMaxLossLaw(10_000),), snapshots=snapshots)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert sum(len(rig.accounts.ledgers.get(d, ())) for d in ("CS1@1", "REF@1")) == 1
    rows = list(csv.DictReader((tmp_path / opportunity_path(b.SESSION, SLOT_1500)).open()))
    mine = {
        row["driver"]: (row["eligible"], row["fillable"], row["executed"]) for row in rows if row["road"] == OPEN_ROAD
    }
    assert sorted(mine.values()) == [("1", "1", "0"), ("1", "1", "1")]


def test_both_counts_files_are_written_with_every_scheduled_decision(tmp_path):
    rig = Rig(tmp_path, (trader(), FakeDriver(all_roads("N0"))), (FakeMaxLossLaw(10_000),))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    outcomes = list(csv.DictReader((tmp_path / counts_path(b.SESSION, SLOT_1500)).open()))
    assert sum(int(row["count"]) for row in outcomes) == 10  # 5 roads x 2 drivers
    opportunity = list(csv.DictReader((tmp_path / opportunity_path(b.SESSION, SLOT_1500)).open()))
    assert len(opportunity) == 10 and all(not set(row) - {"session", "road", "driver", "eligible", "fillable",
                                                          "executed"} for row in opportunity)  # fmt: skip


@dataclass
class OnePerRoad(FakeDriver):
    """A card's own "already holding" rule: no new position on a road it holds one on."""

    def decide(self, road_day, snapshot, history, positions):
        if positions:
            return Decision(self.card.driver_id, road_day.road.code, road_day.session, Outcome.NO_TRADE,
                            NoTradeReason.POSITION_OPEN)  # fmt: skip
        return super().decide(road_day, snapshot, history, positions)


def limit(rig, max_new: int):
    rig.fleet.settings = replace(rig.fleet.settings, max_new_trades_per_slot=max_new)


def test_a_held_ticket_never_blocks_a_real_entry_on_its_road(tmp_path):
    rig = Rig(tmp_path, (OnePerRoad(CS1, b.put_spread()),), (FakeMaxLossLaw(10_000),), max_new=0)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert len(rig.ticket_accounts.ledgers["CS1@1"]) == 1 and "CS1@1" not in rig.accounts.ledgers
    limit(rig, 5)
    rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    assert decision_on(rig, DAY2).outcome == Outcome.TRADE and len(rig.accounts.ledgers["CS1@1"]) == 1


def test_the_same_road_is_never_ticketed_twice(tmp_path):
    rig = Rig(tmp_path, (OnePerRoad(CS1, b.put_spread()),), (FakeMaxLossLaw(10_000),), max_new=0)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    second = decision_on(rig, DAY2)
    assert (second.outcome, second.reason) == (Outcome.NO_TRADE, NoTradeReason.POSITION_OPEN)
    assert len(rig.ticket_accounts.ledgers["CS1@1"]) == 1


def decision_on(rig, session):
    return next(r.decision for r in sealed(rig, session) if r.road == OPEN_ROAD)


def test_a_live_road_whose_capture_holds_an_unmeasured_quote_closes_by_name_and_never_trades(tmp_path):
    unmeasured = {
        k: replace(q, bid_qty=None, ask_qty=None, sizes_measured=False) for k, q in b.snapshot().quotes.items()
    }
    snapshots = {(OPEN_ROAD, s): replace(b.snapshot(quotes=unmeasured), session=s) for s in (b.SESSION, DAY2)}
    rig = Rig(tmp_path, (trader(),), (FakeMaxLossLaw(10_000),), snapshots=snapshots)
    run = rig.fleet.run(b.SESSION, RunMode.REPLAY)
    [mine] = [r for r in run.decisions if r.road == OPEN_ROAD]
    assert (mine.decision.outcome, mine.decision.reason) == (Outcome.ROAD_CLOSED, ClosureReason.SIZES_NOT_MEASURED)
    assert run.fills == () and rig.accounts.ledgers == {}
