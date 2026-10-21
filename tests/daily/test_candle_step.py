"""Story A16b-d: the candle back-fill as the daily run's last step, started after A16's last mark, committing only its
own files, alerted once when it fails, and named without importing Groww code."""

import subprocess
import sys
from datetime import date, datetime, time

from fno.config import ROOT, load_app_config
from fno.constants import DAILY_RUN_STEPS, STEP_FAILED, STEP_OK
from fno.daily.steps import Alerted, CommandStep, NotBefore
from fno.intraday import backfill_daily
from fno.intraday.backfill_daily import CATCH_UP_COMMAND, CATCH_UP_FROM, candle_folders
from fno.intraday.candle_rv_table import CandleRvTable
from fno.intraday.slots import marks
from fno.models import IST
from tests.timetable.fakes import Clock

from .fakes import FakeProcesses, RecordedStep

DAY = date(2026, 10, 14)


def _built_steps(monkeypatch) -> dict:
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda cfg, root: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    wiring.build_day_runner(load_app_config())
    return seen["day_steps"]


def test_the_catch_up_runs_after_a16_s_last_mark_just_before_the_lab_report_committing_only_its_own_files(monkeypatch):
    step = _built_steps(monkeypatch)["candles"]
    assert (
        DAILY_RUN_STEPS[-4:] == ("candles", "lab_close", "close_read", "close_recheck")
        and isinstance(step, Alerted)
        and step.name == "candles"
    )
    waiting = step.step
    assert isinstance(waiting, NotBefore) and isinstance(waiting.step, CommandStep)
    assert waiting.at == CATCH_UP_FROM == time(15, 33) and marks(DAY)[-1].time() == time(15, 30)
    assert waiting.step.arguments(DAY) == ("intraday", "backfill") and waiting.step.pathspecs == candle_folders()


def test_the_pathspecs_are_the_back_fill_s_own_files_and_nothing_wider():
    assert candle_folders() == (
        "research/data/intraday/rv-candle/",
        "research/data/manifests/groww-candles/",
        "research/data/manifests/index-close.csv",
    )
    table_root = CandleRvTable.pattern.split("/", 1)[0]
    assert candle_folders()[0] == f"{(backfill_daily.CANDLE_FOLDER / table_root).relative_to(ROOT).as_posix()}/"
    assert backfill_daily.DEFERRALS.parent.name == table_root  # deferred.csv sits with the rows


def test_before_its_time_the_step_waits_through_the_run_s_waiter_and_after_it_starts_at_once():
    clock, calls = Clock(), []
    clock.now = datetime(2026, 10, 14, 15, 20, tzinfo=IST)
    waited = []

    class Waiter:
        def until(self, moment):
            waited.append(moment)
            clock.until(moment)

    NotBefore(RecordedStep("candles", calls), CATCH_UP_FROM, Waiter()).run(DAY)
    assert waited == [datetime(2026, 10, 14, 15, 33, tzinfo=IST)] and clock() == waited[0] and calls == ["candles"]
    clock.now = datetime(2026, 10, 14, 15, 40, tzinfo=IST)
    NotBefore(RecordedStep("candles", calls), CATCH_UP_FROM, Waiter()).run(DAY)
    assert clock() == datetime(2026, 10, 14, 15, 40, tzinfo=IST) and calls == ["candles", "candles"]


def _step(clock, code, lines, alerts, changed=lambda specs: ["research/data/intraday/rv-candle/2026/x.csv"]):
    processes = FakeProcesses(clock, {CATCH_UP_COMMAND: (datetime(2026, 10, 14, 15, 34, tzinfo=IST), code, lines)})
    command = CommandStep(processes, lambda day: CATCH_UP_COMMAND, candle_folders(), changed, sleep=clock.advance)
    return Alerted("candles", NotBefore(command, CATCH_UP_FROM, clock), alerts), processes


def test_a_deferred_session_is_failed_with_one_alert_and_a_clean_run_commits_its_files_only(alerts):
    clock = Clock()
    failed, processes = _step(clock, 1, ["sessions 1: 0 written now, 0 held before, 1 deferred"], alerts)
    done = failed.run(DAY)
    assert processes.started == [(datetime(2026, 10, 14, 15, 33, tzinfo=IST), CATCH_UP_COMMAND)]
    assert done.result["status"] == STEP_FAILED and len(alerts.sent) == 1 and "step candles failed" in alerts.sent[0]
    asked = []
    clean, _ = _step(Clock(), 0, ["sessions 1: 1 written now"], alerts, lambda specs: asked.append(specs) or ["a.csv"])
    assert clean.run(DAY).result["status"] == STEP_OK and asked == [candle_folders()] and len(alerts.sent) == 1


def test_naming_the_step_imports_no_groww_code():
    probe = "import sys, fno.intraday.backfill_daily; print([m for m in sys.modules if 'groww' in m.lower()])"
    out = subprocess.run([sys.executable, "-c", probe], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    assert out.strip() == "[]"
