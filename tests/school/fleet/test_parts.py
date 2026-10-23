"""Story MS-P1j: the fleet's parts on their own (history, slot plan, running view, outcomes, entry mids)."""

import json
from dataclasses import replace
from datetime import date, timedelta

import pytest

from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.school.constants import ClosureReason, ExitReason, RecordKind, RoadCode
from fno.school.contracts.accounts import FilledLeg, FillResult, LedgerEntry
from fno.school.contracts.roads import OPEN, ROADS_BY_CODE, RoadStatus
from fno.school.contracts.snapshot import SnapshotUnavailable
from fno.school.fakes import FakeDashcam
from fno.school.fleet.entry_mids import DashcamEntryMids, EntryNotSealed
from fno.school.fleet.history import RecordedSpotHistory
from fno.school.fleet.outcomes import MidUnknown, outcome_record
from fno.school.fleet.running_view import driver_of, position_id, running_view
from fno.school.fleet.slot import plan_slot
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import trade_record
from tests.school.fleet.rig import days

ROAD = ROADS_BY_CODE[RoadCode.BANKNIFTY_MONTHLY]


def capture(folder, day: date, spot, complete=True, in_window=True, snapshot_id=None):
    snapshot_id = snapshot_id or f"{ROAD.stem}_{day:%Y%m%d}_150100"
    place = lambda name: folder / QuoteSnapshotRecorder.path(day, name, ROAD.dataset)  # noqa: E731
    place("x").parent.mkdir(parents=True, exist_ok=True)
    place(f"{ROAD.stem}_{day:%Y%m%d}.canonical").write_text(snapshot_id)
    place(f"{snapshot_id}.meta.json").write_text(
        json.dumps({"spot": spot, "complete": complete, "in_window": in_window})
    )


def test_the_history_holds_only_usable_canonical_captures_strictly_before_the_session(tmp_path):
    capture(tmp_path, date(2026, 10, 19), 100.0)
    capture(tmp_path, date(2026, 10, 21), 101.0, complete=False)
    capture(tmp_path, date(2026, 10, 22), 102.0, in_window=False)
    capture(tmp_path, date(2026, 10, 23), 103.0)
    capture(tmp_path, date(2026, 10, 26), 104.0)  # the session itself: never in its own history
    capture(tmp_path, date(2026, 10, 27), 105.0)  # later: never
    spots = RecordedSpotHistory(tmp_path).spots(ROAD, date(2026, 10, 26))
    assert [(p.session, p.spot) for p in spots] == [(date(2026, 10, 19), 100.0), (date(2026, 10, 23), 103.0)]


def test_a_none_marker_or_a_missing_sidecar_adds_no_point(tmp_path):
    capture(tmp_path, date(2026, 10, 19), 100.0, snapshot_id="none")
    capture(tmp_path, date(2026, 10, 21), 101.0)
    (tmp_path / QuoteSnapshotRecorder.path(date(2026, 10, 21), f"{ROAD.stem}_20261021_150100.meta.json",
                                           ROAD.dataset)).unlink()  # fmt: skip
    assert RecordedSpotHistory(tmp_path).spots(ROAD, date(2026, 10, 26)) == ()


class Gate:
    def __init__(self, status):
        self.status = status

    def check(self, road_day, snapshot):
        return self.status


class Snapshots:
    def __init__(self, failure=None):
        self.failure = failure

    def for_road(self, road_day):
        if self.failure:
            raise SnapshotUnavailable(self.failure, "the quote file's hash differs")
        return b.snapshot(road_day.road.code)


class Catalogue:
    def day(self, session):
        return days(session)


def test_the_slot_closes_a_road_by_the_catalogue_the_snapshot_or_the_gate():
    by_catalogue = plan_slot(b.SESSION, Catalogue(), Snapshots(), Gate(OPEN))
    assert len(by_catalogue.open) == 1 and len(by_catalogue.closed) == 4
    assert by_catalogue.closed[0].detail == "no canonical marker"
    by_source = plan_slot(b.SESSION, Catalogue(), Snapshots(ClosureReason.HASH_MISMATCH), Gate(OPEN))
    assert by_source.open == () and ClosureReason.HASH_MISMATCH in {r.reason for r in by_source.closed}
    gate = Gate(RoadStatus(ClosureReason.IMPOSSIBLE_PRICE, "a vertical outside its width"))
    by_gate = plan_slot(b.SESSION, Catalogue(), Snapshots(), gate)
    [closed] = [r for r in by_gate.closed if r.reason == ClosureReason.IMPOSSIBLE_PRICE]
    assert closed.snapshot is not None and by_gate.marks == {}


def test_the_running_view_adds_the_accepted_trades_as_positions_opened_now():
    view = running_view(b.account(), (b.decision(),))
    assert len(view.open_positions) == len(view.opened_this_session) == 1
    added = view.open_positions[0]
    assert added.entry_net == b.put_spread().net_premium - b.put_spread().costs and added.opened == b.SESSION
    with pytest.raises(ValueError):
        running_view(b.account("DB1@1"), (b.decision(),))


def test_an_outcome_values_both_fills_and_never_invents_a_mid():
    at = b.SLOT_AT + timedelta(minutes=4)
    entry = FillResult((FilledLeg(b.key(1000.0), "sell", 30, 10.0, 20.0),), filled_at=at, rests_on="cd" * 32)
    exit_ = FillResult((FilledLeg(b.key(1000.0), "buy", 30, 4.0, 20.0),), filled_at=at, rests_on="cd" * 32)
    opening = LedgerEntry(b.position(), entry, closes=False)
    closing = LedgerEntry(b.position(), exit_, closes=True, exit_reason=ExitReason.PROFIT_TARGET)
    outcome = outcome_record(opening, closing, {b.key(1000.0): 10.5}, {b.key(1000.0): 3.5}, False)
    assert (outcome.gross, outcome.costs, outcome.net) == (180.0, 40.0, 140.0)
    assert outcome.slippage_vs_mid == pytest.approx(0.5 * 30 + 0.5 * 30)
    assert outcome.return_on_risk == pytest.approx(140.0 / b.position().max_loss)
    with pytest.raises(MidUnknown):
        outcome_record(opening, closing, {}, {b.key(1000.0): 3.5}, False)
    settled = replace(closing, exit_reason=ExitReason.EXPIRY)
    assert outcome_record(opening, settled, {b.key(1000.0): 10.5}, {}, False).slippage_vs_mid == pytest.approx(15.0)


def test_an_entry_s_mids_come_from_its_own_sealed_record_or_raise(tmp_path):

    dashcam = FakeDashcam()
    with pytest.raises(EntryNotSealed):
        DashcamEntryMids(dashcam)(b.position())
    dashcam.seal(b.SESSION, "15:00", RecordKind.DECISIONS, (trade_record(),))
    assert DashcamEntryMids(dashcam)(b.position()) == {b.key(1000.0): b.quote().mid}


def test_driver_of_reads_back_the_driver_version_position_id_wrote():
    """Judge K's minor (judge 529): the fleet's own check reads a drift row's driver beside the ID's one builder."""
    decision = trade_record().decision
    assert driver_of(position_id(decision)) == decision.driver_id == "CS1@1"
