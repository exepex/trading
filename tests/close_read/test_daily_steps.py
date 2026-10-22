"""A4h criteria 5 and 6: O1's `close_read` (15:40) and `close_recheck` (16:00) are the run's last two steps, after
`candles` (FL1-1d removed `lab_close`; while it existed they followed it, judge 440 add. 1); each
Alerted(LiveFrom(NotBefore(CommandStep))) on A4h's own receipts, not live until its date; the reader never reaches
Groww."""

import ast
from datetime import date, time
from pathlib import Path

import pytest

from fno.close_read.constants import CLOSE_READ_FROM, CLOSE_RECHECK_FROM
from fno.close_read.wiring import receipt_pathspecs
from fno.config import ROOT, load_app_config
from fno.constants import DAILY_RUN_STEPS, STEP_NOT_LIVE
from fno.daily.steps import Alerted, CommandStep, LiveFrom, NotBefore
from tests.daily.live_dates import without_live_dates

DAY = date(2026, 10, 21)


def _steps(monkeypatch, cfg=None):
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda *args: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    wiring.build_day_runner(cfg or load_app_config())
    return seen["day_steps"]


def test_both_reads_are_the_real_tuple_s_last_two_after_the_candles():
    assert DAILY_RUN_STEPS[-3:] == ("candles", "close_read", "close_recheck")


@pytest.mark.parametrize(
    ("name", "gate", "arguments"),
    [("close_read", CLOSE_READ_FROM, ("closes", "read")), ("close_recheck", CLOSE_RECHECK_FROM,
                                                            ("closes", "read", "--recheck"))],
)  # fmt: skip
def test_each_step_waits_for_its_gate_and_commits_only_a4h_s_receipts(monkeypatch, name, gate, arguments):
    step = _steps(monkeypatch)[name]
    assert isinstance(step, Alerted) and step.name == name and isinstance(step.step, LiveFrom)
    waiting = step.step.step
    assert isinstance(waiting, NotBefore) and waiting.at == gate and isinstance(waiting.step, CommandStep)
    assert tuple(waiting.step.arguments(DAY)) == arguments and waiting.step.pathspecs == receipt_pathspecs()
    assert receipt_pathspecs() == ("receipts/data/closes/",) and (
        time(15, 40), time(16, 0)) == (CLOSE_READ_FROM, CLOSE_RECHECK_FROM)  # fmt: skip


@pytest.mark.parametrize("name", ["close_read", "close_recheck"])
def test_not_live_neither_waits_nor_reads(monkeypatch, name):
    step = _steps(monkeypatch, without_live_dates())[name]
    waited = []
    step.step.step.waiter = type("Waiter", (), {"until": lambda self, at: waited.append(at)})()
    assert step.step.live_from is None and step.run(DAY).result["status"] == STEP_NOT_LIVE and waited == []


def test_the_reader_imports_no_groww_and_no_order_code():
    imported = set()
    for file in Path(ROOT, "fno", "close_read").glob("*.py"):
        for node in ast.walk(ast.parse(file.read_text())):
            if isinstance(node, ast.ImportFrom):
                imported.add(f"{'.' * node.level}{node.module or ''}")
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
    assert imported and not [m for m in imported if "groww" in m.lower() or "order" in m.lower() or "desk" in m]
