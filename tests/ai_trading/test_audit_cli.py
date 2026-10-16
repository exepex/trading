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
    assert not_captured(tmp_path, f"{DAY:%Y-%m}", [], "2026-10-20") == [(DAY.isoformat(), "book2_hybrid",
                                                                           "https://x.invalid/cse_abc")]  # fmt: skip
    assert not_captured(tmp_path, f"{DAY:%Y-%m}", [{"session_id": "session_abc"}], "2026-10-20") == []
