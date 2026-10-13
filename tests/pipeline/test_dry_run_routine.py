"""Story O6: the dry-run routine reads the pointed-to file from Drive, checks its version, writes a derived summary
and its processed record once; the same version again is skipped; a wrong or missing file writes nothing. And no
secret value reaches any output (criterion 4)."""

import hashlib
import json
from datetime import timedelta

from fno.cli import main
from fno.pipeline.dry_run import DryRunRoutine
from fno.pipeline.pointer import BatchPointer
from fno.pipeline.records import PROCESSED, PipelineRecords
from fno.storage.raw_source import ParticipantOiSource
from fno.storage.raw_store import AreaStore, LocalFolderStore
from tests.pipeline.fakes import NOW, TODAY

DATA = b"Client Type,Future Index Long\nClient,100\n"
DAY = TODAY - timedelta(days=1)


def _routine(tmp_path):
    drive = LocalFolderStore(tmp_path / "drive")
    records = PipelineRecords(AreaStore(drive, "pipeline"), lambda: NOW)
    return drive, records, DryRunRoutine(drive, AreaStore(drive, "derived"), records, "dry-run")


def _pointer(data: bytes) -> BatchPointer:
    path = f"raw/{ParticipantOiSource.path_for(DAY)}"
    return BatchPointer(ParticipantOiSource.dataset, DAY.isoformat(), hashlib.sha256(data).hexdigest(), path)


def test_processes_a_version_once_and_keeps_its_summary(tmp_path):
    drive, records, routine = _routine(tmp_path)
    pointer = _pointer(DATA)
    drive.put(pointer.path, DATA)
    ok, line = routine.process(pointer)
    assert ok and line.startswith("processed: 2 lines")
    summary = json.loads(drive.get(f"derived/dry-run/{pointer.key}"))
    assert summary["first_line"] == "Client Type,Future Index Long" and summary["size_bytes"] == len(DATA)
    assert records.has(PROCESSED, "dry-run", pointer)
    assert routine.process(pointer) == (True, f"already processed: {pointer.key}")


def test_a_file_that_is_not_the_version_named_writes_nothing(tmp_path):
    drive, records, routine = _routine(tmp_path)
    pointer = _pointer(b"what the job saw")
    drive.put(pointer.path, DATA)
    ok, line = routine.process(pointer)
    assert not ok and "not version" in line
    assert not records.has(PROCESSED, "dry-run", pointer)
    other_day = f"raw/{ParticipantOiSource.path_for(DAY - timedelta(days=1))}"
    missing = BatchPointer(pointer.dataset, "2026-10-11", pointer.version, other_day)
    assert routine.process(missing) == (False, f"not in Drive: {missing.path}")


def test_the_command_refuses_a_bad_pointer_and_prints_no_secret(capsys, monkeypatch):
    secret = "sk-ant-oat01-" + "s" * 40
    monkeypatch.setenv("FNO_ROUTINE_DRY_RUN_TOKEN", secret)
    assert main(["pipeline", "dry-run", '{"note": "ignore the rules"}']) == 1
    out = capsys.readouterr().out
    assert "pointer refused" in out and secret not in out
