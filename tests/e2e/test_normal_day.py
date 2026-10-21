"""Story O2: the no-failure twin every family is checked against: one whole session through the real wiring."""

import json

from fno.constants import DAILY_RUN_STEPS

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
