"""Story E3's real parts, one by one: the timetable in config.yaml, the recorder's second capture, the pack's retry
while the canonical snapshot is not committed, D3's committed decisions read at the deadline, the written-once
"no decision (late)" record, and Book 1's D6 version kept current (judge 80 follow-up a)."""

from dataclasses import replace
from datetime import date, datetime, time

import pytest

from fno.books.version_registry import VersionRegistry, VersionRow
from fno.config import ALLOWED_APP_KEYS, load_app_config
from fno.constants import BOOK1_RULES
from fno.desk.book_versions import NONE_YET, Book1Versions
from fno.desk.committed_decisions import D3CommittedDecisions, RunNotRecorded
from fno.desk.no_decision import write_no_decision
from fno.desk.pack_items import PackError
from fno.desk.timetable import TimetableError, timetable_from_config
from fno.models import IST
from fno.playbook.decision_run import playbook_digest
from fno.playbook.decision_store import SUMS_FILE, DecisionStore
from fno.playbook.loader import Playbook
from fno.playbook.registry import RegistryRow
from tests.desk.builders import at
from tests.playbook.evaluation_builders import strategy
from tests.quotes.test_quote_recorder import FakeProvider, recorder

from .fakes import C4, TIMETABLE, Clock, Commits, FakePacks, daily_run
from .test_daily_run import BOOKS, NORMAL, Decisions, Rules

DAY = date(2026, 10, 14)
HEAD = "a" * 40


def test_the_timetable_is_read_from_config_and_must_be_in_order():
    assert "desk" in ALLOWED_APP_KEYS
    assert (TIMETABLE.decision_deadline, TIMETABLE.execution_snapshot, TIMETABLE.lock_lease_seconds) == (
        time(15, 12), time(15, 15), 60.0)  # fmt: skip
    cfg = load_app_config()
    swapped = {**cfg["desk"]["timetable"], "decision_deadline": "15:16"}
    with pytest.raises(TimetableError, match="strictly in this order"):
        timetable_from_config({"desk": {"timetable": swapped}})
    with pytest.raises(TimetableError, match="below the fills window"):
        timetable_from_config({"desk": {"timetable": {**cfg["desk"]["timetable"], "lock_lease_seconds": 600}}})
    with pytest.raises(TimetableError, match="fills_by"):
        timetable_from_config({"desk": {"timetable": {k: v for k, v in swapped.items() if k != "fills_by"}}})


def test_the_recorder_s_second_capture_is_never_canonical(tmp_path):
    early, _ = recorder(tmp_path / "early", FakeProvider(), datetime(2026, 10, 13, 15, 15, tzinfo=IST))
    assert early.capture().complete and early.canonical(date(2026, 10, 13)) is None  # even with no 3 pm canonical
    rec, _ = recorder(tmp_path, FakeProvider(), datetime(2026, 10, 13, 14, 55, tzinfo=IST))
    canonical = rec.record().snapshot_id
    rec.now = lambda: datetime(2026, 10, 13, 15, 15, tzinfo=IST)
    second = rec.capture()
    assert (
        second.status == "recorded"
        and second.snapshot_id != canonical
        and rec.canonical(date(2026, 10, 13)) == canonical
    )
    rec.now = lambda: datetime(2026, 10, 18, 15, 15, tzinfo=IST)  # a Sunday
    assert rec.capture().status == "not a trading day"


class LatePacks(FakePacks):
    """The canonical snapshot is committed only after `failures` refused attempts."""

    def __init__(self, failures):
        super().__init__()
        self.failures, self.tries = failures, 0

    def build(self, day):
        self.tries += 1
        if self.tries <= self.failures:
            raise PackError("no canonical A4 snapshot yet")
        return super().build(day)


@pytest.mark.parametrize(("failures", "built"), [(3, True), (100, False)])
def test_the_pack_waits_for_the_canonical_snapshot_until_the_recorder_s_window_ends(root, tmp_path, alerts, failures,
                                                                                      built):  # fmt: skip
    run, clock, *_ = daily_run(root, tmp_path, alerts, BOOKS, Decisions(), C4(), Rules())
    run.steps.packs = LatePacks(failures)
    clock.now = at(14, 50)
    log = run.run(NORMAL)
    assert log.result("pack")["built"] is built
    assert datetime.fromisoformat(log.steps["pack"]["finished_at"]) <= at(15, 10)
    if not built:  # no pack: no new trade, but the run goes on to its exits
        assert "exits" in log.steps and "no new trade" not in log.result("pack")["reason"]


class Commits_:
    """D3's git view: each run's holding commit and committer time."""

    def __init__(self, added):
        self.added = added

    def added_in(self, path):
        return self.added.get(path)

    def observed(self):
        return "origin-head"

    def is_ancestor(self, older, newer):
        return False  # parallel commits: the commit time orders them


def test_d3_decisions_are_read_at_the_deadline_and_the_fills_reread_only_the_recorded_run(tmp_path):
    store, deadline = DecisionStore(tmp_path, BOOK1_RULES), at(15, 12)
    for n in (1, 2, 3):
        (store.day_folder(DAY) / f"2026-10-14-r{n}").mkdir(parents=True)
    path = lambda n: f"journal/{BOOK1_RULES}/decisions/{DAY}/2026-10-14-r{n}/{SUMS_FILE}"  # noqa: E731
    git = Commits_({path(n): (f"c{n}", f"2026-10-14T15:{m}:00+05:30") for n, m in ((1, "03"), (2, "07"), (3, "12"))})
    source = D3CommittedDecisions(tmp_path, git)
    assert source.observe() == "origin-head"
    decision = source.committed(BOOK1_RULES, DAY, deadline)
    # story D3b: the FIRST timely run (r1 at 15:03), never the latest (r2 at 15:07, which E3 used to take); r3 is late
    assert (decision.run_id, decision.commit, decision.committed_at) == ("2026-10-14-r1", "c1", at(15, 3))
    assert [r["run_id"] for r in source.others(BOOK1_RULES, DAY, decision.run_id)] == ["2026-10-14-r2", "2026-10-14-r3"]
    assert source.recorded(BOOK1_RULES, DAY, "2026-10-14-r1", "c1") == decision
    with pytest.raises(RunNotRecorded, match="not held by the recorded commit c9"):
        source.recorded(BOOK1_RULES, DAY, "2026-10-14-r1", "c9")
    with pytest.raises(RunNotRecorded):
        source.recorded(BOOK1_RULES, DAY, "2026-10-14-r7", "c7")
    assert D3CommittedDecisions(tmp_path, Commits_({})).committed(BOOK1_RULES, DAY, deadline) is None


def test_the_no_decision_record_is_written_once(tmp_path):
    path = write_no_decision(tmp_path, BOOK1_RULES, DAY, at(15, 12), "nothing committed")
    assert write_no_decision(tmp_path, BOOK1_RULES, DAY, at(15, 12), "nothing committed") == path
    with pytest.raises(FileExistsError, match="written once"):
        write_no_decision(tmp_path, BOOK1_RULES, DAY, at(15, 12), "another reason")


class Loader:
    def __init__(self, playbook):
        self.playbook = playbook

    def load(self):
        return self.playbook


class History:
    def first_commit_containing(self, text, path):
        return "c" * 40

    def is_ancestor(self, older, newer):
        return True


def keeper(tmp_path, playbook):
    registry = VersionRegistry(tmp_path / "versions.csv")
    commits = Commits(Clock())
    return Book1Versions(Loader(playbook), registry, History(), lambda: HEAD, commits), registry, commits


def paper_playbook(changes):
    version = strategy("sc-a")
    rows = [
        RegistryRow("sc-a", 1, version.parameters_sha256, status, day, "owner", "abcdef1") for status, day in changes
    ]
    return Playbook((replace(version, status=changes[-1][0]),), tuple(rows))


def test_book1_s_version_follows_a_status_change_before_the_day_s_decisions(tmp_path):
    approved = paper_playbook([("paper", date(2026, 10, 10))])
    versions, registry, commits = keeper(tmp_path, approved)
    assert versions.keep(DAY) == NONE_YET and registry.rows() == []  # the first version is the owner's
    registry.append(VersionRow(BOOK1_RULES, "v1", date(2026, 10, 12), HEAD,
                               {"playbook": playbook_digest(approved, DAY), "config": "cfg"}, "owner"))  # fmt: skip
    assert versions.keep(DAY).startswith("Book 1 version v1 unchanged") and commits.made == []
    paused = paper_playbook([("paper", date(2026, 10, 10)), ("paused", DAY)])  # a pause dated today
    versions, registry, commits = keeper(tmp_path, paused)
    line = versions.keep(DAY)
    new = registry.rows()[-1]
    assert line.startswith("Book 1 version v1+20261014 registered from 2026-10-14") and new.starts_on == DAY
    assert new.components == {"playbook": playbook_digest(paused, DAY), "config": "cfg"} and len(commits.made) == 1
    resumed = paper_playbook([("paper", date(2026, 10, 10)), ("paused", DAY), ("paper", DAY)])  # resumed the same day
    versions, *_ = keeper(tmp_path, resumed)
    assert versions.keep(DAY).startswith("Book 1 version NOT renewed")  # D6: one version per book per day; owner's
    assert versions.keep(date(2026, 10, 15)).startswith("Book 1 version v1+20261015 registered")
