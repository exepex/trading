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
    args = SimpleNamespace(budget_cmd="record-usage", export=good, purpose="development", book="", role="judge")
    assert cli.cmd_budget(args) == 0 and len(UsageLedger(tmp_path).rows()) == 2
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(export(TWO_DAYS, has_more=True)), encoding="utf-8")
    assert cli.cmd_budget(SimpleNamespace(**{**vars(args), "export": bad})) == 1
    assert "refused: the export has no page with has_more false" in capsys.readouterr().out
