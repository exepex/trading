"""Story MS-P1j's composition root (Judge K, judge 512 should-fix 1): a replay builds no Drive dashcam, no account
sync and no committer, and every store it writes lives under its own folder; the record mode builds each of them."""

from datetime import date, datetime
from types import SimpleNamespace

import pytest

from fno.config import ROOT, load_config
from fno.models import IST
from fno.school import wiring
from fno.school.contracts.fleet import RunMode
from fno.school.fleet.replay_store import ReplayDashcam

CFG = load_config(ROOT / "config.yaml")
ON = {**CFG, "school": {**CFG["school"], "enabled": True}}
SESSION = date(2026, 10, 22)
OUTWARD = ("build_dashcam", "build_account_sync", "GitManifestRecorder")
READ_ONLY = {  # what the fleet only reads (captures, NSE's archives, the margin file), stubbed: no store is built here
    "build_road_services": lambda: SimpleNamespace(catalogue=None, snapshots=None, listing=None),
    "build_quality_gate": lambda listing: None,
    "build_fill_port": lambda cfg: None,
    "build_margin": lambda cfg: None,
    "build_capture_1515": lambda root: SimpleNamespace(for_session=None),
}


@pytest.fixture(autouse=True)
def read_only(monkeypatch):
    for name, stub in READ_ONLY.items():
        monkeypatch.setattr(wiring, name, stub)


def refuse(name):
    def builder(*args, **kwargs):
        raise AssertionError(f"a replay built {name}")

    return builder


def test_a_replay_builds_nothing_outward_and_writes_only_under_its_folder(monkeypatch, tmp_path):
    for name in OUTWARD:
        monkeypatch.setattr(wiring, name, refuse(name))
    fleet = wiring.build_fleet(ON, RunMode.REPLAY, SESSION, replay_folder=tmp_path)
    assert isinstance(fleet.dashcam, ReplayDashcam) and fleet.dashcam.folder.is_relative_to(tmp_path)
    for store in (fleet.books.accounts, fleet.books.ticket_entries):
        assert store.root.is_relative_to(tmp_path) and store.sync is None
    assert fleet.counts.root == tmp_path and fleet.counts.committer is None
    assert fleet.clock.now() == datetime.combine(SESSION, wiring.REPLAY_FILL_TIME, IST)


def test_a_replay_needs_its_folder():
    with pytest.raises(ValueError):
        wiring.build_fleet(ON, RunMode.REPLAY, SESSION)


def test_the_record_mode_builds_the_drive_dashcam_the_sync_and_the_committer(monkeypatch, tmp_path):
    built = {}
    for name in OUTWARD:
        monkeypatch.setattr(wiring, name, lambda *a, name=name, **k: built.setdefault(name, object()))
    fleet = wiring.build_fleet(ON, RunMode.RECORD, SESSION, root=tmp_path)
    assert fleet.dashcam is built["build_dashcam"] and fleet.counts.committer is built["GitManifestRecorder"]
    assert fleet.books.accounts.sync is built["build_account_sync"]
