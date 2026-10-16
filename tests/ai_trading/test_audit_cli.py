"""Story F1t criterion 12: decision sessions are audited by the forecasts' rule into their own records, which the
decision stop rule reads; the forecasts' audits are untouched."""

import json
from argparse import Namespace

from fno.ai.audit_plan import fired_sessions
from fno.ai.paths import transcript_audit_path as forecast_audit_path
from fno.ai_trading.cli import cmd_ai_trading
from fno.ai_trading.paths import DECISIONS_FOLDER, fired_path, transcript_audit_path

from .builders import DAY


def fire_log(root, entry):
    path = root / fired_path(DAY)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"book2_hybrid": entry}))


def record(**changes):
    args = {"ai_trading_cmd": "audit-record", "day": DAY, "book": "book2_hybrid", "breach": ["file_outside_input"],
            "evidence": "read journal/book3_ai/decisions", "auditor": "judge E", "session": ""}  # fmt: skip
    return Namespace(**(args | changes))


def test_a_decision_session_audit_is_recorded_once_in_the_decision_folder(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fno.config.ROOT", tmp_path)
    fire_log(tmp_path, {"state": "fired", "fired": True, "version": "v1", "session": "https://example.invalid/s"})
    assert cmd_ai_trading(record()) == 0
    saved = json.loads((tmp_path / transcript_audit_path(DAY, "book2_hybrid")).read_text())
    assert saved["result"] == "breach" and saved["session"] == "https://example.invalid/s"
    assert not (tmp_path / forecast_audit_path(DAY, "book2_hybrid")).exists()
    assert cmd_ai_trading(record()) == 1 and "already exists" in capsys.readouterr().out


def test_a_fire_unknown_session_is_auditable_by_its_link_and_a_not_fired_one_is_not(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("fno.config.ROOT", tmp_path)
    fire_log(tmp_path, {"state": "fire_unknown", "fired": None, "version": "v1"})
    assert cmd_ai_trading(record(session="https://example.invalid/found", breach=[])) == 0
    fire_log(tmp_path, {"state": "not_fired", "fired": False, "version": "v1"})
    (tmp_path / transcript_audit_path(DAY, "book2_hybrid")).unlink()
    assert cmd_ai_trading(record()) == 1 and "was not fired" in capsys.readouterr().out


def test_fired_decision_sessions_are_read_from_their_own_folder(tmp_path):
    fire_log(tmp_path, {"state": "fired", "fired": True, "version": "v1"})
    assert [s.book for s in fired_sessions(tmp_path, DECISIONS_FOLDER)] == ["book2_hybrid"]
    assert fired_sessions(tmp_path) == []  # the forecasts' folder holds none


def test_a_fired_decision_session_counts_for_f8_s_capture_coverage(tmp_path):
    from fno.budget.capture_coverage import not_captured

    fire_log(tmp_path, {"state": "fired", "fired": True, "version": "v1", "session": "https://x.invalid/cse_abc"})
    expected = (DAY.isoformat(), "book2_hybrid", "https://x.invalid/cse_abc", "decision")
    assert not_captured(tmp_path, f"{DAY:%Y-%m}", [], "2026-10-20") == [expected]
    assert not_captured(tmp_path, f"{DAY:%Y-%m}", [{"session_id": "session_abc"}], "2026-10-20") == []


def _timing(root, book, run, session):
    from fno.ai.paths import timing_path

    path = root / timing_path(DAY, book, run)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"session_id": session, "model": "", "started_at": "2026-10-19T15:00:00+05:30",
                                "ended_at": "2026-10-19T15:11:00+05:30"}))  # fmt: skip


def test_f8c_a_forecast_and_a_decision_run_of_one_book_are_two_rows_with_their_roles(tmp_path):
    from fno.ai.usage_record import BookUsageRecorder
    from fno.budget.usage_ledger import UsageLedger

    _timing(tmp_path, "book2_hybrid", "", "session_forecast")
    _timing(tmp_path, "book2_hybrid", "decision", "session_decision")
    ledger = UsageLedger(tmp_path)
    BookUsageRecorder(tmp_path, ledger).record(DAY.replace(day=20))
    roles = {row["session_id"]: row["role_or_bundle"] for row in ledger.rows()}
    assert roles == {"session_forecast": "", "session_decision": "book2_hybrid trading decision"}


def test_f8c_book_and_role_refuses_an_unknown_run_and_a_non_ai_book():
    import pytest

    from fno.ai.usage_record import book_and_role

    for name in ("2026-10-19_book2_hybrid_lunch.timing.json", "2026-10-19_book1_rules.timing.json"):
        with pytest.raises(ValueError, match="not an AI book's run"):
            book_and_role(name)


def test_f8c_an_uncaptured_decision_run_is_alerted_as_the_decision_run(tmp_path):
    from fno.ai.usage_gaps import DECISION_NOT_CAPTURED, alert_usage_gaps
    from fno.budget.usage_ledger import UsageLedger

    class Alerts:
        sent = []

        def send(self, text):
            self.sent.append(text)
            return "sent"

    fire_log(tmp_path, {"state": "fired", "fired": True, "version": "v1", "session": "https://x.invalid/cse_abc"})
    alerts = Alerts()
    alert_usage_gaps(tmp_path, UsageLedger(tmp_path), DAY, alerts)
    assert alerts.sent == [DECISION_NOT_CAPTURED.format(day=DAY.isoformat(), book="book2_hybrid")]
    assert "book2_hybrid's trading decision run NOT captured" in alerts.sent[0]


def test_f8c_the_forecast_and_decision_starts_stay_apart_in_one_container(tmp_path):
    from datetime import datetime

    from fno.ai.run_timing import RunTiming
    from fno.models import IST
    from tests.ai.fakes import LocalCommitTransport

    from .builders import pointer

    times = iter([datetime(2026, 10, 19, 15, 0, tzinfo=IST), datetime(2026, 10, 19, 15, 10, tzinfo=IST)])
    forecast = RunTiming(tmp_path, LocalCommitTransport(tmp_path), lambda: next(times), "s")
    decision = RunTiming(tmp_path, LocalCommitTransport(tmp_path), lambda: next(times), "s", "decision")
    forecast.start(pointer(tmp_path))
    decision.start(pointer(tmp_path))
    assert forecast._started(pointer(tmp_path)) != decision._started(pointer(tmp_path))
    started = {json.loads(t._started(pointer(tmp_path)).read_text())["started_at"] for t in (forecast, decision)}
    assert len(started) == 2  # the second start is not mistaken for the first one's
