"""Story O6 criteria 2 and 3: a download that finds new data fires its routine once per batch and version, no new
data fires nothing, a republished file fires again; a failed fire, a refused token or a refused Drive write posts a
clear line to #fno-desk and fails the run."""

import json
from datetime import timedelta

import pytest

from fno.pipeline.batches import ManifestBatches
from fno.pipeline.dispatcher import BatchDispatcher
from fno.pipeline.records import FIRED, PipelineRecords
from fno.pipeline.run import PipelineRun
from fno.pipeline.run_summary import RunSummaryStore
from fno.pipeline.trigger import RoutineFireTrigger
from fno.storage.manifest_folder import ManifestFolder
from fno.storage.raw_source import ParticipantOiSource
from fno.storage.raw_store import LocalFolderStore
from fno.storage.revisions import RevisionIndex
from tests.pipeline.fakes import NOW, TODAY, FakeTrigger, RecordingAlerts, RefusingStore, add_day, add_revision
from tests.pipeline.test_trigger_and_pointer import FakeResponse, FakeSession

DAY = TODAY - timedelta(days=1)


@pytest.fixture
def desk(tmp_path):
    class Desk:
        manifests = ManifestFolder(tmp_path / "manifests")
        revisions = RevisionIndex(tmp_path / "revisions", [ParticipantOiSource])
        drive = LocalFolderStore(tmp_path / "drive" / "pipeline")
        alerts = RecordingAlerts()
        printed: list[str] = []

        def run(self, trigger, store=None, run_id="1-1", download="success"):
            finder = ManifestBatches(ParticipantOiSource, self.manifests, self.revisions, DAY, ("raw", "revisions"))
            store = store or self.drive
            dispatcher = BatchDispatcher(PipelineRecords(store, _now), trigger)
            job = PipelineRun("participant-oi-release", finder, dispatcher, RunSummaryStore(store), self.alerts, _now,
                              self.printed.append)  # fmt: skip
            return job.run(run_id, download)

    return Desk()


def _now():
    return NOW


def test_new_data_fires_once_and_a_second_run_fires_nothing(desk):
    sha = add_day(desk.manifests, DAY, b"client,dii,fii,pro\n1,2,3,4\n")
    trigger = FakeTrigger()
    assert desk.run(trigger) == 0
    assert [(p.batch, p.version) for p in trigger.fired] == [(DAY.isoformat(), sha)]
    assert trigger.fired[0].path == f"raw/{ParticipantOiSource.path_for(DAY)}"
    assert desk.run(trigger, run_id="2-1") == 0
    assert len(trigger.fired) == 1  # same batch and version: already fired
    assert "0 fired to dry-run, 1 already fired, 0 failed" in desk.alerts.lines[-1]


def test_no_new_data_fires_nothing_and_still_reports_one_line(desk):
    add_day(desk.manifests, DAY - timedelta(days=30), b"old")  # outside the window
    trigger = FakeTrigger()
    assert desk.run(trigger) == 0
    assert trigger.fired == []
    assert len(desk.alerts.lines) == 1 and "0 batches in window" in desk.alerts.lines[0]


def test_a_republished_file_fires_again_once_and_the_first_version_is_kept(desk):
    first = add_day(desk.manifests, DAY, b"version 1\n")
    trigger = FakeTrigger()
    desk.run(trigger)
    second = add_revision(desk.revisions, DAY, b"version 2, rewritten by NSE\n")
    desk.run(trigger, run_id="2-1")
    desk.run(trigger, run_id="3-1")
    assert [p.version for p in trigger.fired] == [first, second]
    assert trigger.fired[1].path.startswith(f"revisions/{ParticipantOiSource.path_for(DAY)}/")
    records = PipelineRecords(desk.drive, _now)
    assert all(records.has(FIRED, "dry-run", p) for p in trigger.fired)  # both versions' records stay


def test_the_run_summary_lists_every_batch_in_drive(desk):
    add_day(desk.manifests, DAY, b"a\n")
    desk.run(FakeTrigger(), run_id="77-2")
    summary = json.loads(desk.drive.get("runs/participant-oi-release/2026/10/77-2.json"))
    assert summary["download"] == "success" and [b["outcome"] for b in summary["batches"]] == ["fired"]


def test_a_failed_fire_alerts_leaves_no_record_and_the_next_run_fires(desk):
    add_day(desk.manifests, DAY, b"a\n")
    failing = FakeTrigger(failure="HTTP 401: the routine's token was refused (expired or revoked)")
    assert desk.run(failing) == 1
    assert any("fire failed: HTTP 401" in line and DAY.isoformat() in line for line in desk.alerts.lines)
    working = FakeTrigger()
    assert desk.run(working, run_id="2-1") == 0
    assert len(working.fired) == 1


def test_a_refused_drive_record_is_alerted(desk):
    add_day(desk.manifests, DAY, b"a\n")
    store = RefusingStore(desk.drive)
    assert desk.run(FakeTrigger(), store=store) == 1
    assert any("Drive refused" in line for line in desk.alerts.lines)


def test_drive_refusing_the_sign_in_alerts_and_fails(desk):
    add_day(desk.manifests, DAY, b"a\n")
    trigger = FakeTrigger()
    assert desk.run(trigger, store=RefusingStore(desk.drive, refuse_reads=True)) == 1
    assert trigger.fired == []
    assert len(desk.alerts.lines) == 1 and "sign-in" in desk.alerts.lines[0]


def test_a_failed_download_fails_the_run_even_with_nothing_to_fire(desk):
    assert desk.run(FakeTrigger(), download="failure") == 1
    assert "download failure" in desk.alerts.lines[-1]


def test_a_refused_token_never_reaches_any_output_or_file(desk, tmp_path):
    secret = "sk-ant-oat01-" + "t" * 40
    session = FakeSession(FakeResponse(401))
    add_day(desk.manifests, DAY, b"a\n")
    assert desk.run(RoutineFireTrigger("dry-run", "trig_1", secret, session)) == 1
    written = b"".join(p.read_bytes() for p in tmp_path.rglob("*") if p.is_file())
    assert secret not in "\n".join(desk.alerts.lines + desk.printed) and secret.encode() not in written
    assert any("token was refused" in line for line in desk.alerts.lines)
