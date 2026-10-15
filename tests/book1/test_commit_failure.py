"""Story E5b criteria 0-5 with real git and a bare origin: one Book 1 decision a day, and `fno desk book1` on a failed
commit (one alert, the same line printed, exit code 1, no traceback; the rerun commits the recorded decision)."""

import shutil
from argparse import Namespace
from datetime import date

import pytest

from fno.books import book1_cli
from fno.books.book1 import Book1Day
from fno.constants import BOOK1_RULES
from fno.desk.pending_commit import PendingCommitter
from fno.desk.private_files import PrivateFilesUnavailable
from fno.playbook.decision_run import DecisionRun
from fno.playbook.decision_store import DecisionStore
from tests.decisions.builders import CONTEXT, doc, snapshot
from tests.playbook.evaluation_builders import Counts, FixedValues, OwnShadowBooks, chain_market
from tests.risk.builders import START, book

from .builders import DAYS, Alerts, FixedInputs, git_book1, priced_evaluator
from .test_rerun_c4_log import checkout, git

DAY = DAYS[0]
RAW_QUOTE = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261013_151500.csv"


class CountedRun(DecisionRun):
    def __init__(self, root):
        super().__init__(priced_evaluator(), DecisionStore(root, BOOK1_RULES))
        self.decisions = 0

    def decide(self, *args):
        self.decisions += 1
        return super().decide(*args)


class LessCash(FixedInputs):
    """The same day with Rs 1,000 less cash in the book: a changed input."""

    def day(self, day: date) -> Book1Day:
        return Book1Day(chain_market(day=day), FixedValues(), book(cash=START - 1000), Counts(), OwnShadowBooks(),
                        CONTEXT)  # fmt: skip


class Desk:
    """`fno desk book1` on one checkout: its counted decision run, alerts and inputs survive across reruns."""

    def __init__(self, root, monkeypatch, capsys):
        self.root, self.run, self.alerts, self.inputs, self.capsys = root, CountedRun(root), Alerts(), None, capsys
        monkeypatch.setattr("fno.books.book1_wiring.build_book1", lambda cfg: self.book1())
        monkeypatch.setattr("fno.composition.build_alert_sender", lambda: self.alerts)
        self.downloads = []  # story E2c's shared download: Drive is not tested here, only that it is asked for
        monkeypatch.setattr("fno.desk.wiring.download_private_records", lambda day=None: self.downloads.append(day))

    def book1(self):
        return git_book1(self.root, snapshot(doc("sc-a")), self.run, self.alerts, self.inputs)

    def __call__(self, commit_run=None) -> tuple[int, str]:
        code = book1_cli.cmd_book1(Namespace(day=DAY, commit_run=commit_run))
        return code, self.capsys.readouterr().out

    def runs(self) -> list[str]:
        return [run.name for run in DecisionStore(self.root, BOOK1_RULES).runs(DAY)]

    def origin_runs(self) -> set[str]:
        folder = f"origin/main:journal/{BOOK1_RULES}/decisions/{DAY}"
        listed = git(self.root, "ls-tree", "-d", "--name-only", folder) if self._has_origin_day() else ""
        return set(listed.split())

    def _has_origin_day(self) -> bool:
        git(self.root, "fetch", "-q", "origin", "main")
        return f"journal/{BOOK1_RULES}/decisions/{DAY}" in git(self.root, "ls-tree", "-r", "--name-only", "origin/main")

    def run_bytes(self) -> dict[str, bytes]:
        (run,) = DecisionStore(self.root, BOOK1_RULES).runs(DAY)
        return {p.name: p.read_bytes() for p in run.iterdir()}


@pytest.fixture
def desk(tmp_path, monkeypatch, capsys):
    return Desk(checkout(tmp_path), monkeypatch, capsys)


def stage_raw_quote(root):
    (root / RAW_QUOTE).parent.mkdir(parents=True, exist_ok=True)
    (root / RAW_QUOTE).write_text("contract_id,bid,ask\n", encoding="utf-8")
    git(root, "add", "--", RAW_QUOTE)


def unstage_raw_quote(root):
    git(root, "rm", "-q", "--cached", "--", RAW_QUOTE)
    (root / RAW_QUOTE).unlink()


def reject_pushes(origin, on=True):
    hook = origin / "hooks" / "pre-receive"
    if on:
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
    else:
        hook.unlink()


def failed_once(desk, cause) -> str:
    """Criterion 1: exactly one alert, the same line printed, exit code 1 (and no exception: no traceback)."""
    code, out = desk()
    assert code == 1 and len(desk.alerts.sent) == 1 and out == desk.alerts.sent[0] + "\n"
    assert out.startswith(f"F&O Book 1 {DAY}: decision NOT committed: ") and cause in out
    return out


def test_a_staged_raw_quote_file_fails_once_and_the_rerun_commits_the_recorded_decision(desk):
    stage_raw_quote(desk.root)
    failed_once(desk, "nifty_20261013_151500.csv")
    recorded = desk.run_bytes()
    unstage_raw_quote(desk.root)
    code, out = desk()
    assert code == 0 and "committed on this rerun as recorded" in out and desk.run.decisions == 1  # criterion 2
    assert desk.origin_runs() == {f"{DAY}-r1"} and desk.run_bytes() == recorded


def test_an_unreachable_origin_fails_once_before_anything_is_decided(desk, tmp_path):
    shutil.move(tmp_path / "origin.git", tmp_path / "away.git")
    failed_once(desk, "origin could not be checked")
    assert desk.runs() == [] and desk.run.decisions == 0
    shutil.move(tmp_path / "away.git", tmp_path / "origin.git")
    assert desk()[0] == 0 and desk.run.decisions == 1 and desk.origin_runs() == {f"{DAY}-r1"}


def test_a_push_rejected_three_times_fails_once_and_the_rerun_pushes_the_local_commit(desk, tmp_path):
    reject_pushes(tmp_path / "origin.git")
    failed_once(desk, "rejected 3 times")
    assert desk.origin_runs() == set()
    reject_pushes(tmp_path / "origin.git", on=False)
    code, out = desk()
    assert code == 0 and desk.run.decisions == 1 and desk.origin_runs() == {f"{DAY}-r1"}


def test_a_decision_file_changed_after_the_failure_stops_the_rerun_named(desk):
    """Criterion 3."""
    stage_raw_quote(desk.root)
    failed_once(desk, "raw")
    unstage_raw_quote(desk.root)
    (run,) = DecisionStore(desk.root, BOOK1_RULES).runs(DAY)
    (run / "inputs.json").write_text("{}\n", encoding="utf-8")
    code, out = desk()
    assert code == 1 and "changed since they were recorded" in out and "inputs.json" in out
    assert desk.origin_runs() == set() and desk.run.decisions == 1


def test_changed_inputs_on_a_committed_day_are_alerted_and_never_decided_again(desk):
    """Criterion 0, the committed state; and an unchanged rerun is "already decided" with no alert."""
    assert desk()[0] == 0
    recorded = desk.run_bytes()
    code, out = desk()
    assert code == 0 and "already decided" in out and desk.alerts.sent == []
    desk.inputs = LessCash()
    code, out = desk()
    assert code == 0 and "already decided" in out and desk.run.decisions == 1 and desk.run_bytes() == recorded
    (alert,) = desk.alerts.sent
    assert f"inputs changed after decision {DAY}-r1 (inputs.json: book)" in alert and "not decided again" in alert


def test_changed_inputs_in_the_marker_state_are_alerted_and_the_recorded_decision_committed(desk):
    """Criterion 0, the state recorded only by the pending marker."""
    stage_raw_quote(desk.root)
    failed_once(desk, "raw")
    recorded = desk.run_bytes()
    unstage_raw_quote(desk.root)
    desk.inputs = LessCash()
    code, out = desk()
    assert code == 0 and "committed on this rerun as recorded" in out
    assert desk.run.decisions == 1 and desk.run_bytes() == recorded and desk.origin_runs() == {f"{DAY}-r1"}
    assert "(inputs.json: book)" in desk.alerts.sent[-1]


def on_disk_only(desk):
    """A stop between the decision and the marker: the run on disk, neither committed nor in the marker."""
    stage_raw_quote(desk.root)
    failed_once(desk, "raw")
    unstage_raw_quote(desk.root)
    (desk.root / "journal" / "runs" / ".pending_book1.json").unlink()
    desk.alerts.sent.clear()


def test_a_run_on_disk_only_is_named_with_the_hand_fix_and_commit_run_commits_it_as_recorded(desk):
    """Criterion 0, the on-disk-only state: never a quiet "already decided", never a new decision."""
    on_disk_only(desk)
    recorded = desk.run_bytes()
    desk.inputs = LessCash()
    code, out = desk()
    assert code == 0 and f"--commit-run {DAY}-r1" in out and desk.run.decisions == 1
    assert len(desk.alerts.sent) == 2 and "(inputs.json: book)" in desk.alerts.sent[0]  # the change, then the fix
    code, out = desk(commit_run=f"{DAY}-r1")
    assert code == 0 and "committed as recorded" in out and desk.run.decisions == 1
    assert desk.origin_runs() == {f"{DAY}-r1"} and desk.run_bytes() == recorded
    assert desk(commit_run=f"{DAY}-r1") == (1, f"Book 1 {DAY}: {DAY}-r1 is not a run on disk only (on origin): "
                                               "nothing committed\n")  # fmt: skip


def test_commit_run_refuses_an_edited_run(desk):
    on_disk_only(desk)
    (run,) = DecisionStore(desk.root, BOOK1_RULES).runs(DAY)
    (run / "inputs.json").write_text("{}\n", encoding="utf-8")
    code, out = desk(commit_run=f"{DAY}-r1")
    assert code == 1 and "was edited after it was written (inputs.json)" in out and desk.origin_runs() == set()


def test_a_second_checkout_finds_the_first_s_decision_on_origin(desk, tmp_path, monkeypatch, capsys):
    """Criterion 0, two checkouts one after the other: origin ends with one Book 1 run."""
    second = tmp_path / "second"
    git(tmp_path, "clone", "-q", str(tmp_path / "origin.git"), str(second))
    for key, value in (("user.email", "desk@example.invalid"), ("user.name", "desk")):
        git(second, "config", key, value)
    assert desk()[0] == 0
    other = Desk(second, monkeypatch, capsys)
    code, out = other()
    assert code == 0 and f"already decided ({DAY}-r1 on origin)" in out and other.run.decisions == 0
    assert desk.origin_runs() == {f"{DAY}-r1"}


def test_book1_s_marker_is_its_own_and_the_daily_run_recovers_nothing_of_it(desk):
    """Criterion 4."""
    stage_raw_quote(desk.root)
    failed_once(desk, "raw")
    unstage_raw_quote(desk.root)
    daily = PendingCommitter(None, desk.root)
    assert daily.marker.name == ".pending_commit.json" and not daily.marker.exists()
    assert (desk.root / "journal" / "runs" / ".pending_book1.json").is_file() and daily.recover() == ""


def test_a_successful_decision_prints_the_same_line_and_exits_0(desk):
    """Criterion 5."""
    code, out = desk()
    head = git(desk.root, "rev-parse", "HEAD").strip()
    assert (code, out) == (0, f"Book 1 {DAY}: decided ({DAY}-r1), committed {head}\n") and desk.alerts.sent == []


def test_drive_unreadable_decides_nothing_with_its_own_alert(desk, monkeypatch):
    """Judge 163 note a (E2c with E5b): a failed download is "nothing decided", never "decision NOT committed"."""

    def unreadable(day=None):
        raise PrivateFilesUnavailable("Drive answered 503")

    monkeypatch.setattr("fno.desk.wiring.download_private_records", unreadable)
    code, out = desk()
    assert code == 1 and desk.alerts.sent == [out.rstrip("\n")] and desk.runs() == [] and desk.run.decisions == 0
    assert out.startswith(f"F&O Book 1 {DAY}: nothing decided: Drive could not be read (Drive answered 503)")


def test_commit_run_works_with_drive_down_and_deciding_downloads_first(desk, monkeypatch):
    """Judge 163 note b: `--commit-run` reads no private record, so it never downloads; deciding downloads first."""
    on_disk_only(desk)
    assert desk.downloads == [DAY]  # the decide that failed had downloaded first
    monkeypatch.setattr("fno.desk.wiring.download_private_records", lambda day=None: pytest.fail("Drive was read"))
    code, out = desk(commit_run=f"{DAY}-r1")
    assert code == 0 and "committed as recorded" in out and desk.origin_runs() == {f"{DAY}-r1"}
