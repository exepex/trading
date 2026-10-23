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
from fno.school import fleet_wiring, instructor_step_wiring, replay_wiring, wiring
from fno.school.fleet.deferred_store import DeferredInstructorStore
from fno.school.fleet.replay_store import ReplayDashcam
from fno.school.fleet.run_receipts import RunReceipts
from fno.school.fleet.session_hook import StagedSessionStep, no_step
from fno.school.fleet.unfilled import UnfilledEntries
from fno.school.instructor.outputs.public_counts import counts_path as instructor_counts_path

CFG = load_config(ROOT / "config.yaml")
ON = {**CFG, "school": {**CFG["school"], "enabled": True}}
SESSION = date(2026, 10, 22)
REAL_STORES = {  # the pilot's real stores: where each one's builder is defined
    "build_dashcam": "fno.school.dashcam.wiring",
    "build_account_sync": "fno.school.accounts.wiring",
    "SessionFilesCommitter": "fno.school.fleet.counts_commit",
    "build_instructor_step": "fno.school.instructor_step_wiring",  # MS-INS's Drive store and receipts
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
        "instructor_step_wiring",
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
    assert fleet.after_outcomes is built["build_instructor_step"]


def test_the_record_root_names_the_instructor_s_counts_file_in_the_counts_commit(monkeypatch, tmp_path):
    """Judge B's should-fix (judge 507.9): the commit takes only named files, so the instructor's counts file is
    committed only if the record root names it; a replay names none."""
    for name in REAL_STORES:
        monkeypatch.setattr(wiring, name, lambda *a, **k: object())
    files = wiring.build_fleet(ON, root=tmp_path).counts.files(SESSION)
    assert set(instructor_step_wiring.instructor_files(SESSION)) <= set(files)
    assert str(instructor_counts_path(SESSION)) not in replay_wiring.build_replay_fleet(
        ON, SESSION, tmp_path
    ).counts.files(SESSION)


def test_a_replay_runs_no_step_after_its_outcomes(tmp_path):
    assert replay_wiring.build_replay_fleet(ON, SESSION, tmp_path).after_outcomes is no_step


class Built:
    """What the instructor's step is built from, recorded: no Drive, no git, no Slack."""

    def __init__(self, monkeypatch):
        self.stores, self.runs, self.counts = [], [], []
        monkeypatch.setattr(instructor_step_wiring, "build_alert_sender", lambda: SimpleNamespace(send=print))
        monkeypatch.setattr(instructor_step_wiring, "build_instructor_store", self.store)
        monkeypatch.setattr(instructor_step_wiring, "build_instructor_run", self.run)
        monkeypatch.setattr(instructor_step_wiring, "build_counts_file", lambda: SimpleNamespace(write=self.count))

    def store(self, publisher):
        real = SimpleNamespace(publisher=publisher, written=[], read=lambda session, kind: None)
        real.write = lambda session, kind, records: real.written.append(kind)
        self.stores.append(real)
        return real

    def run(self, cfg, store, publisher):
        self.runs.append((store, publisher))

        def for_session(session, write):
            store.write(session, "causes", ())
            return SimpleNamespace(classifications=("classified",))

        return SimpleNamespace(for_session=for_session)

    def count(self, session, classifications):
        self.counts.append((session, classifications))


def test_the_instructor_s_work_writes_nothing_and_reads_through_its_run_s_receipts(monkeypatch):
    """Judge 523: the work, on the step's thread, runs part e's session run over a deferred store and the run's
    receipts (which never fetch); its Drive files, receipts and counts file are written only by its writes."""
    built = Built(monkeypatch)
    step = instructor_step_wiring.build_instructor_step(ON)
    assert isinstance(step, StagedSessionStep) and step.name == "instructor"
    writes = step.work(SESSION)
    [(store, publisher)] = built.runs
    [real] = built.stores
    assert isinstance(store, DeferredInstructorStore) and store.store is real
    assert isinstance(publisher, RunReceipts) and real.publisher is publisher
    assert step.prepare == publisher.refresh, "the run fetches main once, on its own thread"
    assert real.written == [] and built.counts == [], "the work wrote"
    writes()
    assert real.written == ["causes"] and built.counts == [(SESSION, ("classified",))]


def test_the_step_s_files_are_its_counts_file_and_its_two_session_receipts():
    files = instructor_step_wiring.instructor_files(SESSION)
    assert files[0] == str(instructor_counts_path(SESSION))
    assert files[1:] == tuple(
        f"receipts/data/school/instructor/2026/10/22.{kind}.jsonl.gz.sha256" for kind in ("attribution", "causes")
    )


def test_unfilled_entries_read_the_record_s_stores_even_with_the_school_off(monkeypatch, tmp_path):
    """Judge 523 minor b: built from the record's own stores, never through the fleet (off, it builds none)."""
    built = {}
    for name in ("build_dashcam", "build_account_sync"):
        monkeypatch.setattr(wiring, name, lambda *a, name=name, **k: built.setdefault(name, object()))
    monkeypatch.setattr(wiring, "build_fill_port", lambda cfg: None)
    monkeypatch.setattr(wiring, "build_fleet", lambda *a, **k: (_ for _ in ()).throw(AssertionError("fleet built")))
    off = {**CFG, "school": {**CFG["school"], "enabled": False}}
    found = wiring.build_unfilled_entries(off, tmp_path)
    assert isinstance(found, UnfilledEntries) and found.dashcam is built["build_dashcam"]
    assert all(reader.sync is built["build_account_sync"] for reader in found.readers)


def test_the_record_root_alerts_a_refused_counts_commit_and_owns_its_earlier_unpushed_ones(monkeypatch, tmp_path):
    """Judge 507.13: the record's counts commit alerts #fno-desk by name; its run paths are the counts folder and the
    instructor's receipts, so an earlier session's unpushed commit there goes up with the next."""
    sent, made = object(), {}
    for name in REAL_STORES:
        monkeypatch.setattr(wiring, name, lambda *a, name=name, **k: made.setdefault(name, a) or object())
    monkeypatch.setattr(wiring, "build_alert_sender", lambda: SimpleNamespace(send=sent))
    fleet = wiring.build_fleet(ON, root=tmp_path)
    assert fleet.counts.alert is sent
    assert made["SessionFilesCommitter"][2] == ("research/school/counts/", instructor_step_wiring.RECEIPTS_PREFIX)
    assert instructor_step_wiring.RECEIPTS_PREFIX == "receipts/data/school/instructor/"
