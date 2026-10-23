"""Story MS-P1j: a rerun after a crash at any point between the seal and the counts' commit completes the session
exactly as one clean run would; the shared displayed size serves entries before exits, and records only what it can
serve; the switch and the pairing checks."""

import csv
from argparse import Namespace
from dataclasses import dataclass, replace
from datetime import datetime, time
from types import SimpleNamespace

from fno.models import IST
from fno.school import cli, wiring
from fno.school.constants import (
    SCHOOL_OFF_LINE,
    SLOT_1500,
    ExitReason,
    Outcome,
    RecordKind,
    RefusalReason,
    UnavailableReason,
)
from fno.school.contracts.accounts import FillResult
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.fleet import RunMode, SessionRun
from fno.school.dashcam.names import counts_path
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.counts_file import opportunity_path
from fno.school.fleet.ledgers import open_positions
from tests.school.contracts import builders as b
from tests.school.contracts.test_settings import GOOD
from tests.school.fleet.rig import DAY2, OPEN_ROAD, Rig, all_roads

CS1, REF = all_roads("CS1"), all_roads("REF")
LAWS = (FakeMaxLossLaw(10_000),)


def trader(card=CS1, **kwargs) -> FakeDriver:
    return FakeDriver(card, b.put_spread(), **kwargs)


@dataclass
class CountingDriver(FakeDriver):
    calls: int = 0

    def decide(self, road_day, snapshot, history, positions):
        self.calls += 1
        return super().decide(road_day, snapshot, history, positions)


def thin(size: int = 30) -> dict:
    quotes = {key: replace(quote, bid_qty=size, ask_qty=size) for key, quote in b.snapshot().quotes.items()}
    return {(OPEN_ROAD, s): replace(b.snapshot(quotes=quotes), session=s) for s in (b.SESSION, DAY2)}


def counts_files(root, session) -> dict:
    return {p: (root / p).read_bytes() for p in (counts_path(session, SLOT_1500), opportunity_path(session, SLOT_1500))}


def crash_after(rig: Rig, root, session, *kinds: RecordKind) -> None:
    """As if the run stopped before sealing `kinds` and writing the counts (the ledgers keep what was recorded)."""
    for kind in kinds:
        del rig.dashcam.files[(session, SLOT_1500, kind)]
    for path in counts_files(root, session):
        (root / path).unlink()


def entries(rig: Rig) -> list:
    return [e for ledger in rig.accounts.ledgers.values() for e in ledger]


def recording(rig: Rig) -> list:
    """Every account and ticket record the fleet makes from now on (the fakes ignore an equal entry twice; d's store
    refuses a second opening, so a rerun must ask for none)."""
    made = []
    for store in (rig.accounts, rig.ticket_accounts):
        real = store.record
        store.record = lambda driver_id, entry, real=real: (made.append(entry), real(driver_id, entry))
    return made


def test_a_rerun_after_the_fills_serves_the_shared_size_as_the_clean_run_did(tmp_path):
    clean = Rig(tmp_path / "clean", (trader(), trader(REF)), LAWS, snapshots=thin())
    clean.fleet.run(b.SESSION, RunMode.REPLAY)
    rig = Rig(tmp_path / "crash", (trader(), trader(REF)), LAWS, snapshots=thin())
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    crash_after(rig, tmp_path / "crash", b.SESSION, RecordKind.OUTCOMES, RecordKind.DRIFT)
    made = recording(rig)
    rig.fleet.clock = FixedClock(datetime.combine(b.SESSION, time(16, 0), IST))
    rig.fleet.books.fills.enter = lambda *args: FillResult(refused=(RefusalReason.STALE_SEAL,))  # law 6, after 15:30
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert made == [] and len(entries(rig)) == 1 and entries(rig) == entries(clean)
    # The entry the size could not serve is priced again: after the close it is `stale_seal` (law 6), so only its
    # fillable count can differ from the clean run's; what executed never does.
    assert executed(tmp_path / "crash") == executed(tmp_path / "clean")


def test_a_rerun_before_the_close_writes_the_clean_run_s_counts(tmp_path):
    clean = Rig(tmp_path / "clean", (trader(), trader(REF)), LAWS, snapshots=thin())
    clean.fleet.run(b.SESSION, RunMode.REPLAY)
    rig = Rig(tmp_path / "crash", (trader(), trader(REF)), LAWS, snapshots=thin())
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    crash_after(rig, tmp_path / "crash", b.SESSION, RecordKind.OUTCOMES, RecordKind.DRIFT)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert counts_files(tmp_path / "crash", b.SESSION) == counts_files(tmp_path / "clean", b.SESSION)


def executed(root) -> set:
    rows = csv.DictReader((root / opportunity_path(b.SESSION, SLOT_1500)).open())
    return {(row["road"], row["driver"], row["executed"]) for row in rows}


def test_a_rerun_after_an_exit_records_it_once_and_seals_its_outcome(tmp_path):
    rig = Rig(tmp_path, (trader(exit_reason=ExitReason.SESSIONS_HELD),), LAWS)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    files = dict(rig.dashcam.files)
    crash_after(rig, tmp_path, DAY2, RecordKind.OUTCOMES, RecordKind.DRIFT)
    made = recording(rig)
    rig.fleet.run(DAY2, RunMode.REPLAY)
    assert made == [] and rig.dashcam.files == files
    assert len(rig.dashcam.read(rig.dashcam.find(DAY2, SLOT_1500, RecordKind.OUTCOMES))) == 1


def test_a_rerun_after_the_counts_write_commits_them(tmp_path):
    rig = Rig(tmp_path, (trader(),), LAWS)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    commits = []
    rig.fleet.counts.committer = Namespace(commit=commits.append)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert len(commits) == 1


def test_a_rerun_after_the_outcomes_seal_still_seals_the_drift_and_writes_the_counts(tmp_path):
    rig = Rig(tmp_path, (trader(),), LAWS)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    files, counts = dict(rig.dashcam.files), counts_files(tmp_path, b.SESSION)
    crash_after(rig, tmp_path, b.SESSION, RecordKind.DRIFT)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert rig.dashcam.files == files and counts_files(tmp_path, b.SESSION) == counts
    assert len(entries(rig)) == 1


def test_a_rerun_of_a_sealed_session_never_asks_a_driver_again(tmp_path):
    driver = CountingDriver(CS1, b.put_spread())
    rig = Rig(tmp_path, (driver,), LAWS)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    asked = driver.calls
    crash_after(rig, tmp_path, b.SESSION, RecordKind.OUTCOMES, RecordKind.DRIFT)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert asked > 0 and driver.calls == asked


def test_entries_take_the_shared_size_before_exits_and_an_exit_without_size_waits(tmp_path):
    rig = Rig(tmp_path, (trader(),), LAWS, snapshots=thin(60))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)  # CS1 opens; on DAY2 it exits while REF enters the same structure
    rig.fleet.drivers = (
        trader(exit_reason=ExitReason.SESSIONS_HELD),
        FakeDriver(
            REF,
            b.proposal_with(
                legs=tuple(replace(leg, side="buy" if leg.side == "sell" else "sell") for leg in b.put_spread().legs)
            ),
        ),
    )
    rig.snapshots.update(thin(30))
    rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    assert len(rig.accounts.ledgers["REF@1"]) == 1, "the entry was served first"
    assert [p.position_id for p in open_positions(tuple(rig.accounts.ledgers["CS1@1"]))], "the exit waits"
    assert rig.dashcam.read(rig.dashcam.find(DAY2, SLOT_1500, RecordKind.OUTCOMES)) == ()


def test_a_ticket_the_shared_size_cannot_serve_is_not_opened(tmp_path):
    rig = Rig(tmp_path, (trader(), trader(REF)), LAWS, snapshots=thin(), max_new=0)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert sum(len(ledger) for ledger in rig.ticket_accounts.ledgers.values()) == 1


def test_a_snapshot_of_another_road_offered_for_an_exit_review_is_a_driver_error(tmp_path):
    rig = Rig(tmp_path, (trader(exit_reason=ExitReason.SESSIONS_HELD),), LAWS)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    other = next(code for code in all_roads("X").roads if code != OPEN_ROAD)
    rig.snapshots[(OPEN_ROAD, DAY2)] = replace(rig.snapshots[(OPEN_ROAD, DAY2)], road=other)
    run = rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    [mine] = [r for r in run.decisions if r.road == OPEN_ROAD]
    assert (mine.decision.outcome, mine.decision.reason) == (Outcome.UNAVAILABLE, UnavailableReason.DRIVER_ERROR)
    assert len(rig.accounts.ledgers["CS1@1"]) == 1, "no exit"


def test_the_run_command_with_the_switch_off_prints_the_off_line_and_builds_nothing(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a store was built with the switch off")

    for name in ("fleet_on", "build_dashcam", "build_account_sync", "GitManifestRecorder"):
        monkeypatch.setattr(wiring, name, refuse)
    monkeypatch.setattr(cli, "load_app_config", lambda: {"school": {**GOOD, "enabled": False}})
    said = []
    assert cli.cmd_run(Namespace(session=b.SESSION, replay=None), said.append) == 0
    assert said == [SCHOOL_OFF_LINE]


def test_no_ledger_ever_holds_more_than_the_displayed_size_could_serve(tmp_path):
    """Orchestrator's ruling c: by construction, every account and ticket fill recorded at one snapshot fits its
    displayed size together; three accounts and their tickets compete on 60 units, then exits beside new entries."""
    drivers = (trader(), trader(REF), trader(all_roads("DR1")))
    rig = Rig(tmp_path, drivers, LAWS, snapshots=thin(60), max_new=0)
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    rig.fleet.drivers, rig.fleet.settings = (*(trader(d.card, exit_reason=ExitReason.SESSIONS_HELD) for d in drivers),
                                             ), replace(rig.fleet.settings, max_new_trades_per_slot=5)  # fmt: skip
    rig.at(DAY2).fleet.run(DAY2, RunMode.REPLAY)
    for session in (b.SESSION, DAY2):
        used: dict = {}
        for store in (rig.accounts, rig.ticket_accounts):
            for entry in (e for ledger in store.ledgers.values() for e in ledger):
                if entry.fill.filled_at.date() == session:
                    for leg in entry.fill.legs:
                        used[(leg.key, leg.side)] = used.get((leg.key, leg.side), 0) + leg.units
        assert used and max(used.values()) <= 60, session


def test_a_replay_runs_with_the_pilot_s_switch_off_and_on_the_config_as_given(monkeypatch, tmp_path):
    """The replay root has no switch: the config is passed as it is, never a copy with the switch forced on."""
    off = {"school": {**GOOD, "enabled": False}}
    given = []

    def replay_fleet(cfg, session, folder):
        given.append(cfg)
        return SimpleNamespace(run=lambda s, mode: SessionRun(s, mode, "", ()))

    monkeypatch.setattr(cli, "load_app_config", lambda: off)
    monkeypatch.setattr("fno.school.replay_wiring.build_replay_fleet", replay_fleet)
    said = []
    assert cli.cmd_run(Namespace(session=b.SESSION, replay=tmp_path), said.append) == 0
    assert given == [off] and given[0] is off and SCHOOL_OFF_LINE not in said
