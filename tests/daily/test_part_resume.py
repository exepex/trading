"""Story O1, gap F1 (judge 412 add. 2-3, judge 417): a rerun resumes the 3 pm parts. A part whose earlier recorder is
alive is adopted (never a second recorder), within `finish`'s bound; one whose markers all exist is taken as recorded
earlier; one whose window is open is restarted; any other fails with one alert. NIFTY still commits first."""

from datetime import date, datetime

from fno.constants import STEP_FAILED, STEP_OK
from fno.daily.part_locks import PART_LOCKS
from fno.daily.quote_parts import NOT_IN_THIS_RUN, QUOTE_PARTS, QuoteParts
from fno.models import IST
from tests.timetable.fakes import Clock

from .fakes import FakeProcesses, RecordingCommitter, part_files, tracking

DAY = date(2026, 10, 14)
NIFTY, NSE, INDICES = (part.arguments for part in QUOTE_PARTS)
NIFTY_SPEC, NSE_SPEC = (part.pathspecs[0] for part in QUOTE_PARTS[:2])


def at(hour, minute):
    return datetime(2026, 10, 14, hour, minute, tzinfo=IST)


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent"


def script(nifty=(14, 56), nse=(14, 57), indices=(15, 12)):
    return {NIFTY: (at(*nifty), 0, ["recorded: nifty"]), NSE: (at(*nse), 0, ["recorded: nse"]),
            INDICES: (at(*indices), 0, ["recorded: 3 indices"])}  # fmt: skip


class Run:
    """One run of the parts in the one container (`folder`: its checkout, so its lock files are shared)."""

    def __init__(self, folder, clock, times=None, recorded=None, files=None):
        self.alerts, self.commits = Alerts(), []
        self.processes = FakeProcesses(clock, times or script())
        self.parts = QuoteParts(QUOTE_PARTS, self.processes, RecordingCommitter(clock, self.commits),
                                part_files(files or {}), self.alerts, clock, *tracking(folder, recorded))  # fmt: skip

    def started(self):
        return [arguments for _, arguments in self.processes.started]

    def committed(self):
        return [message.split()[-1] for _, message, _ in self.commits]


def crashed_run(tmp_path, clock, times=None):
    """A run that started NIFTY and NSE at 14:38 and then died; its recorders live on (each holds its lock)."""
    clock.now = at(14, 38)
    crashed = Run(tmp_path, clock, times)
    crashed.parts.start(DAY)
    assert crashed.started() == [NIFTY, NSE]
    return crashed


def test_a_live_part_of_a_crashed_run_is_adopted_never_started_twice_and_nifty_commits_first(tmp_path):
    clock = Clock()
    crashed = crashed_run(tmp_path, clock, script(nifty=(15, 0), nse=(14, 57)))
    clock.now = at(14, 45)
    rerun = Run(tmp_path, clock, recorded={"nifty": "abc1234", "nse": "def5678"},
                files={NIFTY_SPEC: ["nifty.canonical"], NSE_SPEC: ["nse.canonical"]})  # fmt: skip
    rerun.parts.resume(DAY)
    assert rerun.started() == [] and rerun.parts.how == {"nifty": "adopted", "nse": "adopted", "indices": "restarted"}
    clock.now = at(14, 58)
    crashed.processes.made[NSE].poll()  # NSE's recorder ends: the kernel frees its lock
    rerun.parts.service()
    assert rerun.committed() == []  # NSE waits for NIFTY's commit
    clock.now = at(15, 0)
    crashed.processes.made[NIFTY].poll()
    results = rerun.parts.finish(clock.until)
    assert rerun.committed() == ["nifty", "nse"] and rerun.started() == [INDICES]  # the indices start after NIFTY
    assert results["nifty"] | {"lines": None} == results["nifty"] | {
        "status": STEP_OK, "reason": "recorded earlier (commit abc1234)", "how": "adopted",
        "started_at": at(14, 38).isoformat(), "lines": None}  # fmt: skip
    assert results["indices"]["how"] == "restarted" and rerun.alerts.sent == []


def test_a_part_still_held_past_the_bound_fails_with_the_hand_fix_and_its_files_are_not_committed(tmp_path):
    clock = Clock()
    crashed_run(tmp_path, clock, script(nifty=(23, 0)))  # NIFTY's earlier recorder never ends today
    clock.now = at(14, 45)
    rerun = Run(tmp_path, clock, recorded={"nse": "def5678"}, files={NIFTY_SPEC: ["nifty.half-written"]})
    rerun.parts.resume(DAY)
    results = rerun.parts.finish(clock.until, at(15, 15))
    lock = tmp_path / PART_LOCKS / f"{DAY}_nifty.lock"
    assert results["nifty"]["status"] == STEP_FAILED and results["nifty"]["how"] == "adopted"
    assert results["nifty"]["reason"] == (
        f"still running after 20 minutes, held by an earlier run's recorder: a 3 pm recorder of an earlier run still "
        f"holds {lock}: stop it, then rerun"
    )
    assert [text for text in rerun.alerts.sent if "part nifty" in text] == [
        f"F&O daily run {DAY}: 3 pm quote part nifty failed: {results['nifty']['reason']}; the day's nifty record may "
        "be missing: check its sidecar and canonical marker"
    ]
    assert "nifty" not in rerun.committed() and rerun.started() == []  # never stopped, never a second recorder
    assert at(15, 5) <= clock() <= at(15, 15)  # the bound: 20 minutes from 14:45, not before fills_by


def test_a_stopped_run_s_parts_are_recorded_earlier_with_no_alert_and_their_leftover_files_committed(tmp_path):
    clock = Clock()
    clock.now = at(15, 30)
    rerun = Run(tmp_path, clock, recorded={"nifty": "abc1234", "nse": "def5678", "indices": "0a1b2c3"},
                files={NSE_SPEC: ["nse.meta.json"]})  # fmt: skip
    rerun.parts.resume(DAY)
    results = rerun.parts.finish(clock.until)
    assert {name: (r["status"], r["how"]) for name, r in results.items()} == dict.fromkeys(
        ("nifty", "nse", "indices"), (STEP_OK, "earlier run"))  # fmt: skip
    assert results["nifty"]["commit"] == "abc1234" and rerun.committed() == ["nse"] and rerun.alerts.sent == []


def test_a_rerun_while_the_windows_are_open_restarts_the_parts_of_a_killed_container(tmp_path):
    clock = Clock()
    crashed = crashed_run(tmp_path, clock)
    for process in crashed.processes.made.values():
        process.stop()  # the container died: its recorders with it
    clock.now = at(14, 50)
    rerun = Run(tmp_path, clock)
    rerun.parts.resume(DAY)
    assert rerun.started() == [NIFTY, NSE] and rerun.parts.how["nifty"] == "restarted"
    results = rerun.parts.finish(clock.until, at(15, 15))  # as the runner calls it: not before the desk's fills_by
    assert rerun.started() == [NIFTY, NSE, INDICES] and all(r["status"] == STEP_OK for r in results.values())
    assert results["nifty"]["started_at"] == at(14, 50).isoformat() and rerun.alerts.sent == []


def test_a_rerun_after_15_10_fails_nifty_and_nse_with_one_alert_each_and_restarts_the_open_indices(tmp_path):
    clock = Clock()
    clock.now = at(15, 11)
    rerun = Run(tmp_path, clock)
    rerun.parts.resume(DAY)
    results = rerun.parts.finish(clock.until)
    assert results["nifty"]["reason"] == results["nse"]["reason"] == NOT_IN_THIS_RUN
    assert rerun.started() == [INDICES] and results["indices"]["how"] == "restarted"
    assert len(rerun.alerts.sent) == 2 and all(NOT_IN_THIS_RUN in text for text in rerun.alerts.sent)


def test_a_rerun_after_15_13_fails_the_indices_part_too(tmp_path):
    clock = Clock()
    clock.now = at(15, 14)
    rerun = Run(tmp_path, clock)
    rerun.parts.resume(DAY)
    results = rerun.parts.finish(clock.until)
    assert {name: r["reason"] for name, r in results.items()} == dict.fromkeys(("nifty", "nse", "indices"),
                                                                               NOT_IN_THIS_RUN)  # fmt: skip
    assert rerun.started() == [] and len(rerun.alerts.sent) == 3


def test_a_second_run_s_start_adopts_a_part_another_live_run_holds(tmp_path):
    clock = Clock()
    crashed_run(tmp_path, clock)
    second = Run(tmp_path, clock)
    second.parts.start(DAY)  # the routine started twice in one container
    assert second.started() == [] and second.parts.how == {"nifty": "adopted", "nse": "adopted"}
