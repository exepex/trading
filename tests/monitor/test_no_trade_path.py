"""LM1 criterion 1: nothing the monitor imports, directly or through its imports, can enter, exit, fill or order a
trade. The list is checked in a fresh interpreter, so other tests' imports cannot hide or add a module."""

from __future__ import annotations

import json
import subprocess
import sys

from fno.desk.exit_rules import ProfitTarget, StopLoss, TimeExit
from fno.monitor.checks import RULE_LABELS

LIST_IMPORTS = (
    "import json, sys, fno.monitor.wiring; print(json.dumps(sorted(m for m in sys.modules if m.startswith('fno'))))"
)
DESK_ALLOWED = {"fno.desk", "fno.desk.timetable"}  # the execution snapshot's time, read from config
TRADE_WORDS = ("execution", "entr", "exit", "fill", "order", "settle", "decid", "book", "groww", "broker")


def monitor_imports() -> list[str]:
    run = subprocess.run([sys.executable, "-c", LIST_IMPORTS], capture_output=True, text=True, check=True)
    return json.loads(run.stdout)


def test_the_monitor_imports_no_trade_path():
    imported = monitor_imports()
    assert "fno.monitor.wiring" in imported
    desk = {m for m in imported if m.startswith(("fno.desk", "fno.books", "fno.daily"))}
    assert desk <= DESK_ALLOWED, sorted(desk - DESK_ALLOWED)
    assert not [m for m in imported if any(word in m.rsplit(".", 1)[-1] for word in TRADE_WORDS)]


def test_rule_labels_follow_e4_rule_names():
    assert set(RULE_LABELS) == {ProfitTarget.name, StopLoss.name, TimeExit.name}
