"""Story O2: the no-failure twin every family is checked against: one whole session through the real wiring."""

import json

from fno.constants import DAILY_RUN_STEPS
from fno.daily.full_log_archive import FULL_LOG_FILE

from .harness import OUTSIDE_SEAMS, fixture_day


def run_log(day) -> dict:
    return json.loads((day.root / "journal/runs" / f"{day.day}.json").read_text(encoding="utf-8"))


def test_a_normal_session_runs_every_step_in_order_alerts_nothing_and_ends_day_done(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    assert day.run() == (0, "day done")
    log = run_log(day)
    assert list(log["steps"]) == list(DAILY_RUN_STEPS) and day.slack.sent == []
    decided = log["steps"]["decisions"]["result"]["book1_rules"]
    assert decided["committed_at"] == "2026-10-14T14:58:00+05:30"  # git dated it by the fake clock
    assert {name: part["status"] for name, part in log["steps"]["quotes_done"]["result"]["parts"].items()} == {
        "nifty": "ok", "nse": "ok", "indices": "ok"}  # fmt: skip


def test_only_the_outside_services_are_replaced():
    """Criterion 6: the clock, Slack, Drive, NSE's archive, Groww's capture, the child commands, and the quote store's
    default folder; a new seam fails here until it is named and justified."""
    assert OUTSIDE_SEAMS == (
        "fno.models.datetime",
        "fno.composition.build_alert_sender",
        "fno.storage.wiring.build_owner_drive",
        "fno.storage.quote_wiring.build_owner_drive",
        "fno.storage.wiring.build_raw_stores",
        "fno.storage.wiring.build_nse_fo_library",
        "fno.desk.wiring.build_nse_fo_library",
        "fno.composition.build_nse_fo_library",
        "fno.composition.build_quote_recorder",
        "fno.daily.processes.ChildProcesses",
        "fno.storage.wiring.build_quote_store",
        "fno.desk.wiring.build_quote_store",
        "fno.composition.build_quote_store",
    )


def test_the_committed_log_holds_status_only_and_the_full_log_goes_once_to_drive(tmp_path, monkeypatch):
    """O1-status-only: the built run carries the policy. No command's lines in the committed log, the full log is
    private and local, and its one copy is in Drive's data area with its receipt committed."""
    day = fixture_day(tmp_path, monkeypatch)
    assert day.run() == (0, "day done")
    committed = (day.root / "journal/runs" / f"{day.day}.json").read_text(encoding="utf-8")
    assert '"lines"' not in committed and day.full_step("quotes_done")["parts"]["nifty"]["lines"]
    copies = [path for path in day.drive.files if path.startswith(f"data/{FULL_LOG_FILE.split('{')[0]}{day.day}/")]
    assert len(copies) == 1 and any(copies[0] in path for path in day.origin_files())  # its receipt, pushed


def test_drive_down_for_the_full_log_s_copy_alerts_once_and_changes_nothing_of_the_day(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    day.drive.down_areas = {"data"}
    assert day.run() == (0, "day done")  # a debugging copy never changes the day's outcome
    assert len(day.slack.sent) == 1 and "full run log NOT saved to Drive (DriveDown)" in day.slack.sent[0]
