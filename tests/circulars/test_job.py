"""A20b criterion 9: the hourly job alerts once per episode. A new problem alerts once, naming every new problem; the
same problem next run posts nothing, still exits 1 and marks the step as having spoken; a cleared problem posts one
"recovered" line; a one-off event always alerts and is never kept open; the state holds keys only. Unread earlier
parts stop the capture; receipts not committed is a problem."""

from datetime import date

from fno.alerts.dry_run import DryRunAlertSender
from fno.circulars.episodes import OpenProblems
from fno.circulars.job import CircularsJob
from fno.circulars.model import Problem
from fno.storage.manifest_commit import ManifestRecorder

D16 = date(2026, 10, 16)


class Capture:
    def __init__(self, *runs):
        self.runs, self.calls = list(runs), 0

    def run(self, day, rows):
        self.calls += 1
        return list(self.runs.pop(0))


class Recorder(ManifestRecorder):
    def __init__(self, outcome="receipts committed and pushed (1 file(s))"):
        self.outcome = outcome

    def pending(self):
        return []

    def commit(self, what):
        return self.outcome


def make(tmp_path, capture, seen=list, recorder=None):
    alerts, spoken = DryRunAlertSender(), []
    job = CircularsJob(seen, capture, [recorder or Recorder()], OpenProblems(tmp_path / "open.txt"), alerts,
                       lambda: spoken.append(True), "RUN", [].append)  # fmt: skip
    return job, alerts, spoken


NSE_DOWN = Problem("nse:list", "nse: list NOT read: HTTP 403")
SEBI_STALE = Problem("sebi:stale", "sebi: stale")


def test_one_alert_per_episode_then_quiet_then_recovered(tmp_path):
    job, alerts, spoken = make(tmp_path, Capture([NSE_DOWN], [NSE_DOWN], [NSE_DOWN, SEBI_STALE], []))
    assert job.run(D16) == 1 and len(alerts.would_send) == 1 and "HTTP 403" in alerts.would_send[0]
    assert job.run(D16) == 1 and len(alerts.would_send) == 1 and spoken == [True]  # known: quiet, step marked
    assert job.run(D16) == 1 and len(alerts.would_send) == 2 and "sebi: stale" in alerts.would_send[1]
    assert "HTTP 403" not in alerts.would_send[1]  # only the new problem is named
    assert job.run(D16) == 0 and "recovered: nse:list, sebi:stale" in alerts.would_send[2]
    assert (tmp_path / "open.txt").read_text() == ""


def test_the_state_file_holds_keys_only(tmp_path):
    job, _, _ = make(tmp_path, Capture([NSE_DOWN, Problem("file:nse:NSE/FAOP/1", "https://x/y.pdf: HTTP 403")]))
    job.run(D16)
    assert (tmp_path / "open.txt").read_text() == "file:nse:NSE/FAOP/1\nnse:list\n"


def test_a_one_off_event_always_alerts_and_is_never_kept_open(tmp_path):
    abandoned = Problem("file:nse:1:abandoned", "abandoned", episode=False)
    job, alerts, _ = make(tmp_path, Capture([abandoned], []))
    assert job.run(D16) == 1 and len(alerts.would_send) == 1
    assert job.run(D16) == 0 and len(alerts.would_send) == 1  # no "recovered" line for a one-off


def test_unread_earlier_parts_stop_the_capture(tmp_path):
    def unreadable():
        raise OSError("drive down")

    capture = Capture([])
    job, alerts, _ = make(tmp_path, capture, seen=unreadable)
    assert job.run(D16) == 1 and capture.calls == 0 and "earlier circulars NOT read" in alerts.would_send[0]


def test_a_failed_list_write_is_a_named_problem(tmp_path):
    class Failing:
        def run(self, day, rows):
            raise OSError("drive 503")

    job, alerts, _ = make(tmp_path, Failing())
    assert job.run(D16) == 1 and "new circulars NOT saved" in alerts.would_send[0]


def test_receipts_not_committed_is_a_problem_every_time(tmp_path):
    recorder = Recorder("receipts NOT committed: push failed: rejected. Commit receipts/ by hand")
    job, alerts, _ = make(tmp_path, Capture([], []), recorder=recorder)
    assert job.run(D16) == 1 and job.run(D16) == 1 and len(alerts.would_send) == 2


def test_a_clean_run_sends_nothing(tmp_path):
    job, alerts, spoken = make(tmp_path, Capture([]))
    assert job.run(D16) == 0 and alerts.would_send == [] and spoken == []
