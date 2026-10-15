"""`python -m fno budget ...` on the repository and on a temporary ledger: prints, records, refuses; posts nothing."""

import json
import subprocess
import sys
from datetime import datetime
from types import SimpleNamespace

from fno import models
from fno.budget import cli, wiring
from fno.budget.usage_ledger import UsageLedger
from fno.config import ROOT
from tests.budget.exports import TWO_DAYS, export, write_export


def run(*args):
    return subprocess.run([sys.executable, "-m", "fno", "budget", *args], cwd=ROOT, capture_output=True, text=True)


def test_the_meter_and_the_stop_rule_print_on_the_repository():
    meter, stop = run("meter", "--month", "2026-10"), run("stop-rule")
    assert meter.returncode == stop.returncode == 0
    assert "Omenix F&O budget meter 2026-10" in meter.stdout and "Test A: not computable yet" in stop.stdout


def test_record_usage_writes_once_and_refuses_an_incomplete_export(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(wiring, "build_usage_ledger", lambda: UsageLedger(tmp_path))
    monkeypatch.setattr(models, "now_ist", lambda: datetime(2026, 10, 16, 9, 0, tzinfo=models.IST))
    good = write_export(tmp_path, export(TWO_DAYS))
    args = SimpleNamespace(
        budget_cmd="record-usage", export=good, self_timed=False, purpose="development", book="", role="judge"
    )
    assert cli.cmd_budget(args) == 0 and len(UsageLedger(tmp_path).rows()) == 2
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(export(TWO_DAYS, has_more=True)), encoding="utf-8")
    assert cli.cmd_budget(SimpleNamespace(**{**vars(args), "export": bad})) == 1
    assert "refused: the export's last page has has_more true" in capsys.readouterr().out


def test_a_bad_month_and_an_export_inside_the_repository_are_refused_not_tracebacks():
    month = run("meter", "--month", "2026-13")
    assert month.returncode == 1 and month.stdout.startswith("refused: --month '2026-13' is not YYYY-MM")
    inside = run("record-usage", "--export", "config.yaml", "--purpose", "development", "--role", "judge")
    assert inside.returncode == 1 and "is inside the repository" in inside.stdout and "Traceback" not in inside.stderr


def test_record_roster_merges_a_list_sessions_export(tmp_path, monkeypatch, capsys):
    from fno.budget.session_roster import SessionRoster

    monkeypatch.setattr(wiring, "build_session_roster", lambda: SessionRoster(tmp_path))
    path = tmp_path / "roster.json"
    page = {"data": [{"id": "session_01A", "created_at": "2026-10-14T03:00:00Z", "updated_at": "2026-10-14T05:00:00Z"}]}
    path.write_text(json.dumps({"captured_at": "2026-10-16T08:00:00+05:30", "limit": 20,
                                "pages": [{"after_id": None, "response": page}]}), encoding="utf-8")  # fmt: skip
    assert cli.cmd_budget(SimpleNamespace(budget_cmd="record-roster", export=path)) == 0
    assert "roster: 1 session(s) listed" in capsys.readouterr().out
