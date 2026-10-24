"""Story MS-P1j: one test for each guard Judge K's plants deleted unseen (judge 512 should-fix 2)."""

from dataclasses import dataclass, replace

import pytest

from fno.school.constants import SLOT_1500, Outcome, RecordKind, RefusalReason, RoadCode, UnavailableReason
from fno.school.contracts.accounts import FilledLeg, FillResult, SettlementPrice
from fno.school.contracts.dashcam import ReplayConflict
from fno.school.contracts.fleet import RunMode
from fno.school.contracts.tickets import OpportunityCounts
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.counts_file import SessionCounts
from fno.school.fleet.quote_share import quote_shares
from fno.school.fleet.settle import settle_expired
from fno.school.tickets.shared_size import OwnedFill, allocate
from tests.school.contracts import builders as b
from tests.school.fleet.rig import DAY2, OPEN_ROAD, Rig, all_roads
from tests.school.fleet.test_quote_share import MISSING, record

CS1, REF = all_roads("CS1"), all_roads("REF")
LAWS = (FakeMaxLossLaw(10_000),)
NIFTY = RoadCode.NIFTY_MONTHLY


@dataclass
class OtherRoad(FakeDriver):
    """A driver that answers for another road than the one it was asked about."""

    def decide(self, road_day, snapshot, history, positions):
        decision = super().decide(road_day, snapshot, history, positions)
        return replace(decision, road=RoadCode.FINNIFTY_MONTHLY)


def test_a_decision_naming_another_road_is_the_driver_s_error_never_a_record_of_it(tmp_path):
    rig = Rig(tmp_path, (OtherRoad(CS1, b.put_spread()),), LAWS)
    run = rig.fleet.run(b.SESSION, RunMode.REPLAY)
    [mine] = [r for r in run.decisions if r.road == OPEN_ROAD]
    assert (mine.decision.outcome, mine.decision.reason) == (Outcome.UNAVAILABLE, UnavailableReason.DRIVER_ERROR)
    assert rig.accounts.ledgers == {}


def test_the_opportunity_counts_file_is_write_once(tmp_path):
    counts = SessionCounts(tmp_path, None)
    row = OpportunityCounts(b.SESSION, RoadCode.BANKNIFTY_MONTHLY, "CS1@1", 1, 1, 1)
    counts.write(b.SESSION, SLOT_1500, (), (row,))
    counts.write(b.SESSION, SLOT_1500, (), (row,))  # the same text again is a no-op
    with pytest.raises(ReplayConflict):
        counts.write(b.SESSION, SLOT_1500, (), (replace(row, executed=0),))


def test_drift_rows_are_made_only_for_the_entries_the_shared_size_served(tmp_path):
    thin = {k: replace(q, bid_qty=30, ask_qty=30) for k, q in b.snapshot().quotes.items()}
    snapshots = {(NIFTY, s): replace(b.snapshot(NIFTY, quotes=thin), road=NIFTY, session=s) for s in (b.SESSION, DAY2)}
    rig = Rig(tmp_path, (FakeDriver(CS1, b.put_spread()), FakeDriver(REF, b.put_spread())), LAWS,
              snapshots=snapshots, open_roads=(NIFTY,))  # fmt: skip
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    drift = rig.dashcam.read(rig.dashcam.find(b.SESSION, SLOT_1500, RecordKind.DRIFT))
    served = [e for ledger in rig.accounts.ledgers.values() for e in ledger]
    assert len(served) == 1 and len(drift) == len(served[0].fill.legs) == 2
    assert {row.position_id for row in drift} == {served[0].position.position_id}


def test_a_ticket_entry_takes_the_size_before_an_account_s_exit():
    def owned(owner, is_ticket=False, is_exit=False):
        legs = (FilledLeg(b.key(1000.0), "sell", 30, 10.0, 0.0),)
        return OwnedFill(owner, FillResult(legs, filled_at=b.SLOT_AT, rests_on="cd" * 32), is_ticket, is_exit)

    snapshot = b.snapshot(quotes={b.key(1000.0): replace(b.quote(), bid_qty=30)})
    for order in ((owned("A@1", is_exit=True), owned("Z@1", is_ticket=True)),
                  (owned("Z@1", is_ticket=True), owned("A@1", is_exit=True))):  # fmt: skip
        allocation = allocate(order, snapshot, SLOT_1500)
        assert [o.owner for o in allocation.servable] == ["Z@1"] and allocation.unservable[0].is_exit


def test_the_quote_share_counts_a_quote_refusal_the_named_reason_does_not_show():
    stopped_first = record(("daily_stop", RefusalReason.DAILY_STOP, ""), MISSING)
    assert stopped_first.decision.reason == RefusalReason.DAILY_STOP
    [share] = quote_shares((stopped_first,))
    assert share.quote_refused == 1


def test_a_position_expiring_on_the_session_itself_is_not_settled_before_its_settlement(tmp_path):
    priced = {("BANKNIFTY", b.EXPIRY): SettlementPrice(1_050.0, "ee" * 32)}  # known: only the date stops it
    rig = Rig(tmp_path, (FakeDriver(CS1, b.put_spread()),), LAWS, settlements=priced)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert settle_expired(rig.fleet.books, ("CS1@1",), b.EXPIRY) == ()
    assert len(rig.accounts.ledgers["CS1@1"]) == 1, "still open on its own expiry day"
