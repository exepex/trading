"""Story MS-P1j's two roots (Judge K, judge 512 should-fix 1; orchestrator: by construction, not by convention): the
replay root and the shared fleet builder import none of the pilot's real stores, a replay built while those stores
refuse to exist still builds, and every store it writes lives under its folder; the record root builds all three."""

import ast
import inspect
from datetime import date, datetime
from types import SimpleNamespace

import pytest

from fno.config import ROOT, load_config
from fno.models import IST
from fno.school import fleet_wiring, replay_wiring, wiring
from fno.school.fleet.replay_store import ReplayDashcam
from fno.school.fleet.session_hook import IsolatedSessionStep, no_step
from fno.school.instructor.outputs.public_counts import counts_path as instructor_counts_path

CFG = load_config(ROOT / "config.yaml")
ON = {**CFG, "school": {**CFG["school"], "enabled": True}}
SESSION = date(2026, 10, 22)
REAL_STORES = {  # the pilot's real stores: where each one's builder is defined
    "build_dashcam": "fno.school.dashcam.wiring",
    "build_account_sync": "fno.school.accounts.wiring",
    "SessionFilesCommitter": "fno.school.fleet.counts_commit",
    "run_instructor_session": "fno.school.instructor.wiring",  # MS-INS's Drive store and receipts
}
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
        monkeypatch.setattr(fleet_wiring, name, stub)


def imported(module) -> set[str]:
    """Every module and name the module's source imports."""
    names = set()
    for node in ast.walk(ast.parse(inspect.getsource(module))):
        if isinstance(node, ast.ImportFrom):
            names |= {node.module or ""} | {alias.name for alias in node.names}
        elif isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
    return names


@pytest.mark.parametrize("module", [replay_wiring, fleet_wiring], ids=lambda m: m.__name__)
def test_the_replay_root_and_the_shared_builder_cannot_reach_a_real_store(module):
    names = imported(module)
    assert not names & set(REAL_STORES), "a real store's builder imported"
    assert not names & {
        "wiring",
        "dashcam.wiring",
        "storage.manifest_commit",
        "fleet.counts_commit",
        "instructor.wiring",
    }, "the record root or a real store"


def test_a_replay_builds_with_every_real_store_refusing_and_writes_only_under_its_folder(monkeypatch, tmp_path):
    def refuse(*args, **kwargs):
        raise AssertionError("a replay built a real store")

    for name, home in REAL_STORES.items():
        monkeypatch.setattr(f"{home}.{name}", refuse)
        monkeypatch.setattr(wiring, name, refuse)
    fleet = replay_wiring.build_replay_fleet(ON, SESSION, tmp_path)
    assert isinstance(fleet.dashcam, ReplayDashcam) and fleet.dashcam.folder.is_relative_to(tmp_path)
    for store in (fleet.books.accounts, fleet.books.ticket_entries):
        assert store.root.is_relative_to(tmp_path) and store.sync is None
    assert fleet.counts.root == tmp_path and fleet.counts.committer is None
    assert fleet.clock.now() == datetime.combine(SESSION, replay_wiring.REPLAY_FILL_TIME, IST)


def test_the_record_root_builds_the_drive_dashcam_the_sync_and_the_committer(monkeypatch, tmp_path):
    built = {}
    for name in REAL_STORES:
        monkeypatch.setattr(wiring, name, lambda *a, name=name, **k: built.setdefault(name, object()))
    fleet = wiring.build_fleet(ON, root=tmp_path)
    assert fleet.dashcam is built["build_dashcam"] and fleet.counts.committer is built["SessionFilesCommitter"]
    assert fleet.books.accounts.sync is built["build_account_sync"] and fleet.counts.root == tmp_path
    assert isinstance(fleet.after_outcomes, IsolatedSessionStep) and fleet.after_outcomes.name == "instructor"
    fleet.after_outcomes.work(SESSION)
    assert built["run_instructor_session"] is not None, "the record's step is the instructor's session run"


def test_the_record_root_names_the_instructor_s_counts_file_in_the_counts_commit(monkeypatch, tmp_path):
    """Judge B's should-fix (judge 507.9): the commit takes only named files, so the instructor's counts file is
    committed only if the record root names it; a replay names none."""
    for name in REAL_STORES:
        monkeypatch.setattr(wiring, name, lambda *a, **k: object())
    files = wiring.build_fleet(ON, root=tmp_path).counts.files(SESSION)
    assert str(instructor_counts_path(SESSION)) in files
    assert str(instructor_counts_path(SESSION)) not in replay_wiring.build_replay_fleet(
        ON, SESSION, tmp_path
    ).counts.files(SESSION)


def test_a_replay_runs_no_step_after_its_outcomes(tmp_path):
    assert replay_wiring.build_replay_fleet(ON, SESSION, tmp_path).after_outcomes is no_step
