"""G13 criterion 9: O1's `price_distribution` step. Wired as Alerted(LiveFrom(CommandStep)) with G13's receipts as its
only pathspecs and run after the card; not live without a date; a partial write is `failed` with one alert and its
receipts committed; no chain is `refused` with one alert; G13's command sends none of its own."""

from datetime import date, datetime

from fno.alerts.dry_run import DryRunAlertSender
from fno.config import load_app_config
from fno.constants import DAILY_RUN_STEPS, STEP_FAILED, STEP_NOT_LIVE, STEP_REFUSED
from fno.daily.steps import Alerted, CommandStep, LiveFrom
from fno.price_distribution.folders import receipt_pathspecs
from tests.daily.fakes import FakeProcesses
from tests.daily.live_dates import without_live_dates
from tests.timetable.fakes import Clock

DAY = date(2026, 10, 16)
ARGUMENTS = ("pricedist", "record", "--day", DAY.isoformat(), "--live")


def built_step(monkeypatch, cfg=None):
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda cfg, root: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    wiring.build_day_runner(cfg or load_app_config())
    return seen["day_steps"]["price_distribution"]


def test_the_step_is_wired_after_the_card_with_g13_s_receipts_only(monkeypatch):
    step = built_step(monkeypatch)
    assert isinstance(step, Alerted) and isinstance(step.step, LiveFrom) and isinstance(step.step.step, CommandStep)
    command = step.step.step
    assert tuple(command.arguments(DAY)) == ARGUMENTS and tuple(command.pathspecs) == receipt_pathspecs()
    assert receipt_pathspecs() == ("receipts/data/price_distribution/v1/",)
    assert DAILY_RUN_STEPS.index("price_distribution") == DAILY_RUN_STEPS.index("card") + 1


def test_without_a_live_date_the_step_is_not_live_and_calls_nothing(monkeypatch):
    step = built_step(monkeypatch, without_live_dates())
    assert step.step.live_from is None
    assert step.run(DAY).result["status"] == STEP_NOT_LIVE


def run(code, lines, changed=("receipts/data/price_distribution/v1/live/2026/10/nifty_2026-10-16.json.sha256",)):
    clock = Clock()
    clock.now = datetime(2026, 10, 16, 15, 40)
    processes = FakeProcesses(clock, {ARGUMENTS: (clock.now, code, lines)})
    asked = []
    command = CommandStep(processes, lambda day: ARGUMENTS, receipt_pathspecs(),
                          lambda specs: asked.append(tuple(specs)) or list(changed))  # fmt: skip
    alerts = DryRunAlertSender()
    done = Alerted("price_distribution", LiveFrom(command, DAY), alerts).run(DAY)
    return done, alerts, asked


def test_a_partial_write_fails_with_one_alert_and_commits_its_receipts():
    done, alerts, asked = run(1, ["NIFTY: recorded (1 problems)", "written with problems: NIFTY e2 missing"])
    assert done.result["status"] == STEP_FAILED and done.result["reason"].startswith("written with problems")
    assert len(alerts.would_send) == 1 and asked == [receipt_pathspecs()] and done.paths


def test_no_chain_at_all_is_refused_with_one_alert():
    done, alerts, _ = run(0, ["nothing written: no 3 pm chain for any underlying (NIFTY: no canonical 3 pm chain)"])
    assert done.result["status"] == STEP_REFUSED and len(alerts.would_send) == 1


def test_a_good_day_sends_no_alert():
    done, alerts, _ = run(0, ["NIFTY: recorded (0 problems)", "recorded"])
    assert done.result["status"] == "ok" and alerts.would_send == []
