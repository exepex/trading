"""Story BG1 criterion 4: the signal is data with the stop order and code jobs running; the dry run sends nothing."""

import json
from datetime import datetime

from fno.alerts.dry_run import DryRunAlertSender
from fno.budget.cap import CapSettings, cap_reading
from fno.budget.signal import send_alert, signal_data, write_signal
from fno.constants import AI_ROLE_STOP_ORDER

AT = datetime(2026, 10, 31, 18, 0)


def data_at(used):
    rows = [
        {"purpose": "books_and_roles", "minutes": str(used)},
        {"purpose": "development", "minutes": str(100 - used)},
    ]
    return signal_data("2026-10", cap_reading(rows, CapSettings(50, 80, 100, None)), 0, AT)


def test_a_stop_signal_carries_the_stop_order_and_keeps_code_jobs(tmp_path):
    data = data_at(55)
    assert data["level"] == "stop" and data["stop_ai_roles"] is True
    assert data["stop_order"] == list(AI_ROLE_STOP_ORDER) and data["code_jobs"] == "keep running"
    assert "analysts, then idea generator" in data["alert_text"] and "code jobs keep running" in data["alert_text"]
    written = json.loads(write_signal(tmp_path, data).read_text(encoding="utf-8"))
    assert written == data and (tmp_path / "accounting/budget/2026-10_signal.json").is_file()


def test_an_alert_is_dry_run_only(monkeypatch):
    import requests

    monkeypatch.setattr(requests.Session, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network")))
    sender, data = DryRunAlertSender(), data_at(42)
    assert data["level"] == "alert" and not data["stop_ai_roles"] and "84%" in data["alert_text"]
    outcome = send_alert(sender, data)
    assert outcome.startswith("dry run, nothing sent") and sender.would_send == [data["alert_text"]]


def test_below_the_alert_level_nothing_is_sent():
    sender = DryRunAlertSender()
    assert send_alert(sender, data_at(10)) == "no alert: below the alert level" and sender.would_send == []


def test_the_composition_root_wires_only_the_dry_run_sender():
    from fno.budget.wiring import build_budget_alert_sender

    assert type(build_budget_alert_sender()) is DryRunAlertSender
