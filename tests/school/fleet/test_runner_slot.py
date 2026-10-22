"""Story MS-P1j: reruns, the slot's running view, tickets, shared displayed size and the counts files."""

import csv
from dataclasses import dataclass, replace

from fno.school.constants import SLOT_1500, ExitReason, Outcome, RecordKind, RefusalReason, RoadCode, TicketReason
from fno.school.contracts.fleet import RunMode
from fno.school.contracts.records import DecisionRecord, OutcomeRecord
from fno.school.contracts.safety import LawResult
from fno.school.dashcam.names import counts_path
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.counts_file import opportunity_path
from tests.school.contracts import builders as b
from tests.school.fleet.rig import DAY2, OPEN_ROAD, Rig

CS1, REF = b.card("CS1"), b.card("REF")
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
    rig = Rig(tmp_path, (trader(), FakeDriver(b.card("N0"))), (FakeMaxLossLaw(10_000),))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    outcomes = list(csv.DictReader((tmp_path / counts_path(b.SESSION, SLOT_1500)).open()))
    assert sum(int(row["count"]) for row in outcomes) == 10  # 5 roads x 2 drivers
    opportunity = list(csv.DictReader((tmp_path / opportunity_path(b.SESSION, SLOT_1500)).open()))
    assert len(opportunity) == 10 and all(not set(row) - {"session", "road", "driver", "eligible", "fillable",
                                                          "executed"} for row in opportunity)  # fmt: skip
