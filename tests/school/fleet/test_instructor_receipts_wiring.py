"""Story MS-P1j with MS-INS part e (judge 523): the run's receipts reach every reader in the instructor's session run:
the path reader's dashcam and the instructor's own store; and without them each builds its own publisher, which
commits and pushes (part e's standalone command is unchanged)."""

from datetime import date
from types import SimpleNamespace

import pytest

from fno.config import ROOT, load_config
from fno.school import instructor_step_wiring
from fno.school.dashcam import wiring as dashcam_wiring
from fno.school.instructor import wiring as instructor_wiring
from fno.storage.receipt_publisher import GitReceiptPublisher

CFG = load_config(ROOT / "config.yaml")
RUN_RECEIPTS = object()  # stands for the run's `RunReceipts`


@pytest.fixture(autouse=True)
def no_drive(monkeypatch):
    """No Drive, no captures: only the receipts' route is under test."""
    for module in (instructor_wiring, dashcam_wiring):
        monkeypatch.setattr(module, "build_data_store", lambda *a, **k: SimpleNamespace(area="data"))
        monkeypatch.setattr(module, "build_drive_cache", lambda *a, **k: None)
    roads = SimpleNamespace(catalogue=None, snapshots=None, calendar=None)
    monkeypatch.setattr(instructor_wiring, "build_road_services", lambda: roads)
    monkeypatch.setattr(instructor_wiring, "build_settlement_source", lambda: None)
    monkeypatch.setattr(instructor_wiring, "build_classifier", lambda config: None)


def test_the_run_s_receipts_reach_the_path_reader_s_dashcam_and_the_store():
    assert instructor_wiring.build_path_reader(RUN_RECEIPTS).dashcam.publisher is RUN_RECEIPTS
    assert instructor_wiring.build_instructor_store(publisher=RUN_RECEIPTS).publisher is RUN_RECEIPTS
    store = object()
    run = instructor_wiring.build_instructor_run(CFG, store, RUN_RECEIPTS)
    assert run.store is store and run.reader.dashcam.publisher is RUN_RECEIPTS


def test_without_them_each_builds_the_publisher_that_commits_and_pushes():
    run = instructor_wiring.build_instructor_run(CFG)
    assert isinstance(run.reader.dashcam.publisher, GitReceiptPublisher)
    assert isinstance(run.store.publisher, GitReceiptPublisher)


def test_every_session_call_builds_its_own_path_reader_never_one_held_across_runs(monkeypatch):
    """Judge K's note (via the INS builder): the path reader caches the files it read, so it is right only for one
    run; each call of the step's work builds a new one, with an empty cache."""
    readers = []

    class Recorded:
        def __init__(self, reader, *rest):
            readers.append(reader)

        def for_session(self, session, write):
            return SimpleNamespace(classifications=())

    monkeypatch.setattr(instructor_wiring, "InstructorRun", Recorded)
    monkeypatch.setattr(instructor_step_wiring, "build_instructor_store", lambda publisher: None)
    for _ in range(2):
        instructor_step_wiring.instructor_work(CFG, RUN_RECEIPTS, date(2026, 10, 22))
    assert len(readers) == 2 and readers[0] is not readers[1]
    assert all(reader._files == {} for reader in readers)
