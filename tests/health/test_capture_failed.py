"""Story O10: a failed capture run gives one committed row, and one #fno-desk line only when the run posted nothing.
The run and job JSON are trimmed from real runs: participant-oi-release 38801338770 (cancelled by its 350-minute
timeout) and quote-recorder-nse 38745053176 (failed in its alert step)."""

from __future__ import annotations

from argparse import Namespace
from datetime import date

import pytest
import requests

from fno.alerts.sender import NOT_SENT, SENT, AlertSender
from fno.health.capture_cli import cmd_capture_failed
from fno.health.capture_errors import COLUMNS, MAX_MESSAGE, CaptureError, CaptureErrorLog
from fno.health.run_failures import GitHubRuns, RunSource, RunSourceError, capture_error

OI_URL = "https://github.com/exepex/trading/actions/runs/38801338770"
NSE_URL = "https://github.com/exepex/trading/actions/runs/38745053176"


def steps(*pairs):
    return [{"name": name, "conclusion": conclusion} for name, conclusion in pairs]


def oi_run(conclusion="cancelled"):
    run = {
        "name": "participant-oi-release",
        "conclusion": conclusion,
        "html_url": OI_URL,
        "run_started_at": "2026-10-15T20:21:58Z",
    }  # 01:51 IST on 16 Oct
    jobs = [
        {
            "name": "release",
            "conclusion": conclusion,
            "steps": steps(
                ("Set up job", "success"),
                ("Watch NSE's archive until today's file appears (A8)", "cancelled"),
                ("Commit the check log", "skipped"),
                ("Alert", "skipped"),
                ("Complete job", "success"),
            ),
        }
    ]
    return run, jobs


def nse_run():
    run = {
        "name": "quote-recorder-nse",
        "conclusion": "failure",
        "html_url": NSE_URL,
        "run_started_at": "2026-10-15T13:42:54Z",
    }
    jobs = [
        {
            "name": "record",
            "conclusion": "failure",
            "steps": steps(
                (
                    "Record NSE's 3 pm quotes (A4 rules, own dataset)",
                    "success",
                ),  # continue-on-error: GitHub says success
                ("Commit the snapshot", "success"),
                ("One line to", "failure"),
                ("Alert", "skipped"),
            ),
        }
    ]
    return run, jobs


class Runs(RunSource):
    def __init__(self, run_and_jobs):
        self.answer = run_and_jobs

    def run(self, run_id):
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


class Sender(AlertSender):
    def __init__(self, outcome=SENT):
        self.outcome, self.sent = outcome, []

    def send(self, text):
        self.sent.append(text)
        return self.outcome


def call(tmp_path, run_and_jobs, sender=None):
    lines, log, sender = [], CaptureErrorLog(tmp_path / "capture_errors.csv"), sender or Sender()
    code = cmd_capture_failed(Namespace(run_id=1), lines.append, Runs(run_and_jobs), log, sender)
    return code, log, sender, lines


def test_cancelled_run_gives_one_row_and_one_line(tmp_path):
    code, log, sender, _ = call(tmp_path, oi_run())
    [row] = log.rows()
    assert code == 0
    assert row == CaptureError(
        date(2026, 10, 16),
        "participant-oi-release",
        "release / Watch NSE's archive until today's file appears (A8)",
        "cancelled",
        "release / Watch NSE's archive until today's file appears (A8): cancelled",
        OI_URL,
    )
    assert len(sender.sent) == 1 and "cancelled" in sender.sent[0] and OI_URL in sender.sent[0]


def test_timed_out_run_alerts(tmp_path):
    _, log, sender, _ = call(tmp_path, oi_run("timed_out"))
    assert log.rows()[0].kind == "timed_out" and len(sender.sent) == 1


def test_failed_run_records_but_does_not_post_twice(tmp_path):
    code, log, sender, _ = call(tmp_path, nse_run())
    [row] = log.rows()
    assert (code, row.step, row.kind, row.run_url) == (0, "record / One line to", "failure", NSE_URL)
    assert sender.sent == []  # the workflow's own step already posted


@pytest.mark.parametrize("conclusion", ["success", "skipped", "neutral"])
def test_a_good_run_writes_nothing(tmp_path, conclusion):
    code, log, sender, lines = call(tmp_path, oi_run(conclusion))
    assert (code, log.rows(), sender.sent) == (0, [], [])
    assert "nothing to record" in lines[0]


def test_the_same_run_is_never_recorded_twice(tmp_path):
    call(tmp_path, oi_run())
    code, log, sender, lines = call(tmp_path, oi_run())
    assert (code, len(log.rows()), sender.sent) == (0, 1, [])
    assert lines == [f"already recorded: {OI_URL}"]


def test_without_slack_the_row_is_kept_and_the_run_fails(tmp_path):
    code, log, _, lines = call(tmp_path, oi_run(), Sender(NOT_SENT.format(reason="FNO_SLACK_BOT_TOKEN is not set")))
    assert code == 1 and len(log.rows()) == 1
    assert lines[-1] == "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"


def test_github_unreadable_fails_without_a_row(tmp_path):
    code, log, sender, lines = call(tmp_path, RunSourceError("HTTP 403 from GitHub's Actions API"))
    assert (code, log.rows(), sender.sent) == (1, [], [])
    assert "HTTP 403" in lines[0]


def test_a_run_cancelled_before_any_step(tmp_path):
    run, _ = oi_run()
    _, log, _, _ = call(tmp_path, (run, [{"name": "release", "conclusion": "cancelled", "steps": []}]))
    assert log.rows()[0].step == "release / before any step"
    assert capture_error(run, []).step == "before any step"


def test_message_is_one_short_line(tmp_path):
    run, jobs = oi_run()
    jobs[0]["steps"][1]["name"] = "first line\nsecond line " + "x" * 400
    call(tmp_path, (run, jobs))
    text = (tmp_path / "capture_errors.csv").read_text(encoding="utf-8")
    header, row = text.splitlines()
    assert header == ",".join(COLUMNS)
    assert "first line second line" in row
    assert all(len(field) <= MAX_MESSAGE for field in CaptureErrorLog(tmp_path / "capture_errors.csv").rows()[0].row())


class Response:
    def __init__(self, status, body):
        self.status_code, self.ok, self.body = status, status < 400, body

    def json(self):
        return self.body


def test_github_runs_reads_the_run_and_its_jobs():
    asked = []

    def get(url, params=None, headers=None, timeout=None):
        asked.append(url)
        return Response(200, {"jobs": ["job"]} if url.endswith("/jobs") else {"name": "run"})

    assert GitHubRuns("exepex/trading", "t", get).run(7) == ({"name": "run"}, ["job"])
    assert asked == [
        "https://api.github.com/repos/exepex/trading/actions/runs/7",
        "https://api.github.com/repos/exepex/trading/actions/runs/7/jobs",
    ]


def test_github_runs_names_the_problem_never_the_token():
    def refused(url, **kwargs):
        return Response(403, {})

    def down(url, **kwargs):
        raise requests.ConnectionError("secret-token")

    with pytest.raises(RunSourceError, match="HTTP 403"):
        GitHubRuns("exepex/trading", "secret-token", refused).run(7)
    with pytest.raises(RunSourceError) as error:
        GitHubRuns("exepex/trading", "secret-token", down).run(7)
    assert "secret-token" not in str(error.value)


def test_record_error_writes_one_row_for_a_routine(tmp_path):
    from fno.cli import main
    from fno.health import capture_cli

    log = CaptureErrorLog(tmp_path / "capture_errors.csv")
    lines = []
    args = Namespace(
        job="a14c-broker-check", step="fetch", kind="RuntimeError", message="Groww\nunreachable", run_url=""
    )
    assert capture_cli.cmd_record_error(args, lines.append, log, date(2026, 10, 16)) == 0
    assert log.rows() == [CaptureError(date(2026, 10, 16), "a14c-broker-check", "fetch", "RuntimeError",
                                       "Groww unreachable", "")]  # fmt: skip
    assert lines == ["2026-10-16,a14c-broker-check,fetch,RuntimeError,Groww unreachable,"]
    with pytest.raises(SystemExit):
        main(["health", "record-error", "--job", "x"])  # step and kind are required


def test_a_run_s_own_episode_rows_do_not_hide_its_cancel(tmp_path):
    """A long poller (A19) records its episodes with its run URL; a later timeout still gets the row and the line."""
    log = CaptureErrorLog(tmp_path / "capture_errors.csv")
    log.append(CaptureError(date(2026, 10, 16), "participant-oi-release", "et-markets", "http_error", "x", OI_URL))
    code, log, sender, _ = call(tmp_path, oi_run())
    assert code == 0 and [e.kind for e in log.rows()] == ["http_error", "cancelled"] and len(sender.sent) == 1


def gate_failure():
    """forecast-capture.yml: the gate job crashed (it has no alert step) and `capture` (needs: gate) was skipped."""
    run = {"name": "forecast-capture", "conclusion": "failure", "html_url": OI_URL,
           "run_started_at": "2026-10-16T09:30:00Z"}  # fmt: skip
    jobs = [{"name": "gate", "conclusion": "failure", "steps": steps(("Set up job", "success"), ("Decide", "failure"))},
            {"name": "capture", "conclusion": "skipped", "steps": []}]  # fmt: skip
    return run, jobs


def test_a_failed_job_without_its_own_alert_step_gets_the_line(tmp_path):
    """Judge 350 SF1."""
    code, log, sender, _ = call(tmp_path, gate_failure())
    assert code == 0 and log.rows()[0].step == "gate / Decide" and len(sender.sent) == 1


def test_a_failed_job_whose_alert_step_was_skipped_gets_the_line(tmp_path):
    run, jobs = nse_run()
    jobs[0]["steps"][2]["conclusion"] = "skipped"
    jobs[0]["steps"].insert(0, {"name": "Commit identity", "conclusion": "failure"})
    _, _, sender, _ = call(tmp_path, (run, jobs))
    assert len(sender.sent) == 1


@pytest.mark.parametrize("conclusion", ["startup_failure", "action_required", "stale"])
def test_every_other_conclusion_alerts(tmp_path, conclusion):
    run, jobs = nse_run()
    run["conclusion"] = conclusion
    _, log, sender, _ = call(tmp_path, (run, jobs))
    assert log.rows()[0].kind == conclusion and len(sender.sent) == 1


def test_a_re_run_attempt_gets_its_own_row_and_line(tmp_path):
    """Judge 350 minor 2: a re-run cancelled again is a new failure, not a duplicate."""
    call(tmp_path, oi_run())
    run, jobs = oi_run()
    code, log, sender, _ = call(tmp_path, ({**run, "run_attempt": 2}, jobs))
    assert [e.run_url for e in log.rows()] == [OI_URL, f"{OI_URL}/attempts/2"] and len(sender.sent) == 1


def replaced_run(name, steps_ran):
    run = {"name": name, "conclusion": "cancelled", "html_url": OI_URL, "run_started_at": "2026-10-16T05:00:00Z"}
    ran = steps(("Set up job", "success")) if steps_ran else []
    return run, [{"name": "poll", "conclusion": "cancelled", "steps": ran}]


def test_a_replaced_news_run_is_neither_recorded_nor_alerted(tmp_path):
    """A19 (judge 352 SF2): a pending poller run cancelled for a newer one never polled; the newer run carries on."""
    code, log, sender, lines = call(tmp_path, replaced_run("news-capture", steps_ran=False))
    assert (code, log.rows(), sender.sent) == (0, [], []) and "nothing to record" in lines[0]


def test_a_replaced_data_checks_run_is_neither_recorded_nor_alerted(tmp_path):
    """O9b: a pending data-checks run cancelled for a newer one checked nothing; the newer run checks the same or a
    later committed state (it records nothing per push or per day). 23 Oct 2026 gave 24 such rows before this."""
    code, log, sender, lines = call(tmp_path, replaced_run("data-checks", steps_ran=False))
    assert (code, log.rows(), sender.sent) == (0, [], []) and "nothing to record" in lines[0]
    _, log, sender, _ = call(tmp_path, replaced_run("data-checks", steps_ran=True))
    assert len(log.rows()) == 1 and len(sender.sent) == 1  # cancelled after a step ran: a failure, as for news


def test_a_news_run_cancelled_after_a_step_ran_is_a_failure(tmp_path):
    _, log, sender, _ = call(tmp_path, replaced_run("news-capture", steps_ran=True))
    assert len(log.rows()) == 1 and len(sender.sent) == 1


def test_any_other_workflow_cancelled_before_a_step_is_a_lost_slot(tmp_path):
    _, log, sender, _ = call(tmp_path, replaced_run("nse-margins", steps_ran=False))
    assert log.rows()[0].step == "poll / before any step" and len(sender.sent) == 1
