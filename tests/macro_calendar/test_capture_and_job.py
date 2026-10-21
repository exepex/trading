"""A20c criteria 11, 13 and 14: each calendar read whole becomes one snapshot part with the run's time; its document
is kept once under its SHA-256; a failed or unconfigured calendar is a problem and the others still run; the last
future date 30 days ahead is fine, 29 stale; a Drive failure is named; the job alerts once naming every problem; the
workflow and the committer paths."""

import hashlib
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import yaml

from fno.alerts.dry_run import DryRunAlertSender
from fno.macro_calendar.capture import DOCUMENTS, TABLE, CalendarCapture
from fno.macro_calendar.job import MacroCalendarJob
from fno.macro_calendar.model import BLS, COLUMNS, US_CPI, US_FOMC, Calendar, CalendarFailed, ReleaseDate
from fno.macro_calendar.unconfigured import UnconfiguredCalendar
from fno.storage.data_store import DataStore
from fno.storage.data_wiring import build_receipt_committer
from fno.storage.manifest_commit import ManifestRecorder
from fno.storage.part_table import read_parts
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

D16 = date(2026, 10, 16)
NOW = datetime(2026, 10, 16, 2, 0, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]


class Fake:
    def __init__(self, source, last=D16 + timedelta(days=60), error=None, document=b"doc"):
        self.source, self.last, self.error, self.document = source, last, error, document

    def fetch(self, today):
        if self.error:
            raise self.error
        dates = (ReleaseDate(US_FOMC, today + timedelta(days=10), "u"), ReleaseDate(US_FOMC, self.last, "u"))
        return Calendar(dates, self.document, "html", (date(today.year, 1, 1), date(today.year + 1, 12, 31)))


def capture(tmp_path, calendars, run="20261016T020000Z-aaaaaa", drive=None):
    drive = drive or LocalFolderStore(tmp_path / "drive")
    store = DataStore(drive, "data", ReceiptFolder(tmp_path / "receipts"), "macro-calendar", run)
    return drive, CalendarCapture(calendars, store, clock=lambda: NOW, out=[].append)


def snapshot(tmp_path, source):
    folder = tmp_path / "drive" / "data" / TABLE.format(source=source)
    return read_parts(folder, COLUMNS) if folder.exists() else []


def test_a_calendar_becomes_one_snapshot_part_and_its_document_is_kept_once(tmp_path):
    drive, cap = capture(tmp_path, [Fake("fed")])
    assert cap.run(D16) == []
    rows = snapshot(tmp_path, "fed")
    assert [(r["kind"], r["date"], r["source"], r["seen_at"], r["period_end"]) for r in rows] == [
        ("us_fomc", "2026-10-26", "fed", NOW.isoformat(), "2027-12-31"),
        ("us_fomc", "2026-12-15", "fed", NOW.isoformat(), "2027-12-31"),
    ]  # fmt: skip
    path = DOCUMENTS.format(source="fed", sha256=hashlib.sha256(b"doc").hexdigest(), extension="html")
    assert drive.get(f"data/{path}") == b"doc"

    class Counting(LocalFolderStore):
        puts: list = []

        def put(self, path, data):
            self.puts.append(path)
            super().put(path, data)

    counting = Counting(tmp_path / "drive")
    capture(tmp_path, [Fake("fed")], run="20261017T020000Z-bbbbbb", drive=counting)[1].run(D16)
    assert [p for p in counting.puts if "/documents/" in p] == []  # an unchanged document is not uploaded again


def test_a_failed_or_unconfigured_calendar_is_a_problem_and_the_others_still_run(tmp_path):
    calendars = [Fake("mospi", error=CalendarFailed("HTTP 403")), UnconfiguredCalendar(BLS, (US_CPI,)), Fake("fed")]
    problems = capture(tmp_path, calendars)[1].run(D16)
    assert problems[0] == "mospi: calendar NOT read: HTTP 403" and "us_cpi: no source configured" in problems[1]
    assert len(problems) == 2 and snapshot(tmp_path, "fed") and not snapshot(tmp_path, "mospi")


def test_the_last_future_date_30_days_ahead_is_fine_and_29_is_stale(tmp_path):
    assert capture(tmp_path, [Fake("fed", last=D16 + timedelta(days=30))])[1].run(D16) == []
    problems = capture(tmp_path, [Fake("fed", last=D16 + timedelta(days=29))], run="r2-aaaaaa")[1].run(D16)
    assert len(problems) == 1 and problems[0].startswith("fed: stale: its last future date is 2026-11-14")


def test_a_drive_failure_is_named_and_the_others_still_run(tmp_path):
    class Down(LocalFolderStore):
        def put(self, path, data):
            raise OSError("drive 503")

    _, cap = capture(tmp_path, [Fake("fed"), Fake("mospi")], drive=Down(tmp_path / "drive"))
    assert cap.run(D16) == [
        "fed: snapshot NOT saved to Drive: drive 503",
        "mospi: snapshot NOT saved to Drive: drive 503",
    ]


class Recorder(ManifestRecorder):
    def __init__(self, outcome="receipts committed and pushed (2 file(s))"):
        self.outcome = outcome

    def pending(self):
        return []

    def commit(self, what):
        return self.outcome


class Capture:
    def __init__(self, problems):
        self.problems = problems

    def run(self, day):
        return list(self.problems)


def test_the_job_alerts_once_naming_every_problem_and_a_clean_run_sends_nothing():
    alerts = DryRunAlertSender()
    assert MacroCalendarJob(Capture(["a", "b"]), Recorder(), alerts, "RUN", [].append).run(D16) == 1
    assert len(alerts.would_send) == 1 and "a; b" in alerts.would_send[0] and "RUN" in alerts.would_send[0]
    quiet = DryRunAlertSender()
    assert MacroCalendarJob(Capture([]), Recorder(), quiet, "RUN", [].append).run(D16) == 0 and quiet.would_send == []
    failed = Recorder("receipts NOT committed: push failed")
    assert MacroCalendarJob(Capture([]), failed, alerts, "RUN", [].append).run(D16) == 1


def test_the_workflow_runs_daily_at_07_30_ist_with_the_crash_only_alert_line():
    flow = yaml.safe_load((ROOT / ".github" / "workflows" / "macro-calendar.yml").read_text())
    assert [s["cron"] for s in flow[True]["schedule"]] == ["0 2 * * *"] and flow["permissions"] == {"contents": "write"}
    steps = flow["jobs"]["calendar"]["steps"]
    assert next(s for s in steps if s.get("id") == "calendar")["run"] == "python -m fno macro-calendar"
    alert = steps[-1]
    assert alert["name"].startswith("Alert") and alert["if"].startswith("${{ failure() }}")  # O10's watcher sees it ran
    assert alert["env"] == {"POSTED": "${{ steps.calendar.outputs.posted }}"}
    assert alert["run"].startswith('if [ "$POSTED" = "true" ]; then') and "exit 0; fi" in alert["run"].splitlines()[0]
    assert all("#" not in step.get("name", "") for step in steps)  # a " #" would cut the name (YAML comment)
    for name, value in flow["jobs"]["calendar"]["env"].items():
        assert value == f"${{{{ secrets.{name} }}}}", name


def test_the_job_commits_only_receipts():
    assert build_receipt_committer().folder == "receipts"
