"""Story MS-P1c follow-up in the fleet (orchestrator's go, 23 Oct 2026): a run that stopped after a file reached Drive
and before its receipt's push is completed by its rerun from the stored file, whatever the rerun would decide now; a
stored file of another card version stops the run by name. a's `FakeDashcam` refuses other bytes over a stored file,
as Drive does."""

from dataclasses import replace

import pytest

from fno.school.constants import FLEET_STOPPED, SLOT_1500, Outcome, RecordKind, RoadCode
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.fleet import RunMode
from fno.school.contracts.records import DecisionRecord
from fno.school.contracts.slot_file import decode_slot_file, encode_slot_file
from fno.school.fakes import FakeDashcam, FakeDriver, FakeMaxLossLaw
from fno.school.fleet.entry_mids import DashcamEntryMids
from fno.school.fleet.replay_store import ReplayDashcam
from tests.school.contracts import builders as b
from tests.school.contracts import conformance as c
from tests.school.contracts.test_records import outcome_record, trade_record
from tests.school.fleet.rig import Rig, all_roads

LAWS = (FakeMaxLossLaw(10_000),)
STOPPED = "stopped before the receipt's push"


class StopsBeforePush(FakeDashcam):
    """Saves one kind's file to "Drive" and stops before its receipt, once."""

    def __init__(self, kind: RecordKind):
        super().__init__()
        self.stop_at = kind

    def seal(self, session, slot, kind, records):
        if kind == self.stop_at:
            self.stop_at = None
            self.stored[(session, slot, kind)] = encode_slot_file(records)
            raise RuntimeError(STOPPED)
        return super().seal(session, slot, kind, records)


def stopped_rig(tmp_path, kind: RecordKind, **options) -> Rig:
    rig = Rig(tmp_path, (FakeDriver(all_roads("CS1"), b.put_spread()),), LAWS, **options)
    rig.dashcam = rig.fleet.dashcam = StopsBeforePush(kind)
    rig.fleet.entry_mids = DashcamEntryMids(rig.dashcam)
    with pytest.raises(RuntimeError, match=STOPPED):
        rig.fleet.run(b.SESSION, RunMode.RECORD)
    return rig


def sealed_decisions(rig):
    seal = rig.dashcam.find(b.SESSION, SLOT_1500, RecordKind.DECISIONS)
    return [r for r in rig.dashcam.read(seal) if isinstance(r, DecisionRecord)]


def test_a_rerun_completes_the_session_from_its_stored_decisions_not_what_it_would_decide_now(tmp_path):
    rig = stopped_rig(tmp_path, RecordKind.DECISIONS)
    rig.fleet.drivers = (FakeDriver(all_roads("CS1")),)  # the same card now proposes nothing (e.g. past its limit)
    run = rig.fleet.run(b.SESSION, RunMode.RECORD)
    assert run.status == "" and run.decisions_seal is not None
    trades = [r for r in sealed_decisions(rig) if r.decision.outcome == Outcome.TRADE]
    assert trades and run.decisions == tuple(sealed_decisions(rig)), "the stored decisions are the session's record"
    assert rig.accounts.ledgers, "the stored trades were filled"


def test_a_stored_file_of_another_card_version_stops_the_run_by_name_and_fills_nothing(tmp_path):
    rig = stopped_rig(tmp_path, RecordKind.DECISIONS)
    edited = replace(rig.fleet.drivers[0].card, card_sha256="0" * 64)  # the card edited between the two runs
    rig.fleet.drivers = (FakeDriver(edited, b.put_spread()),)
    run = rig.fleet.run(b.SESSION, RunMode.RECORD)
    assert run.status.startswith(FLEET_STOPPED) and "dashcam stuck: stored file unverifiable" in run.status
    assert "not this fleet's" in run.status and run.decisions_seal is None
    assert rig.dashcam.find(b.SESSION, SLOT_1500, RecordKind.DECISIONS) is None and not rig.accounts.ledgers


def test_a_rerun_after_a_stop_at_the_drift_file_adopts_it_and_writes_the_counts(tmp_path):
    """On a NIFTY road (the only one with drift rows): the stopped run read a 15:15 touch, the rerun reads none, so
    its rows differ; the stored rows stand."""
    rig = stopped_rig(tmp_path, RecordKind.DRIFT, open_roads=(RoadCode.NIFTY_MONTHLY,))
    key = (b.SESSION, SLOT_1500, RecordKind.DRIFT)
    stored = tuple(replace(row, price_1515=12.5) for row in decode_slot_file(rig.dashcam.stored[key]))
    assert stored, "the trade's legs give drift rows"
    rig.dashcam.stored[key] = encode_slot_file(stored)
    run = rig.fleet.run(b.SESSION, RunMode.RECORD)
    assert run.status == "" and rig.dashcam.read(rig.dashcam.find(*key)) == stored
    assert rig.fleet.counts.written(b.SESSION, SLOT_1500)


def test_the_replay_dashcam_conforms_and_recovers_only_what_it_sealed(tmp_path):
    """A local file is its own seal: `recover` is `find`, so a replay never adopts anything."""
    store = ReplayDashcam(tmp_path, FixedClock(b.SLOT_AT))
    c.check_dashcam(store, b.SESSION, SLOT_1500, (trade_record(),), (outcome_record(),))
