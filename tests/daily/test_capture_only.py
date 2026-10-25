"""Story STAB1 (owner, 25 Oct 2026: "We are not doing any kind of forecasting ... Data capture will never stop"): with
the repository's own `config.yaml`, no forecast, score, card, recommendation, AI fire or school decision is a live step
of the daily run, the lab's editions and the recommender's check build nothing, and no forecasting workflow has a
trigger; every capture keeps its step, its part and its trigger."""

from argparse import Namespace
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import yaml

from fno.config import ROOT, load_app_config
from fno.constants import DAILY_RUN_STEPS, STEP_NOT_LIVE, V4_RELEASE_STEP
from fno.daily.quote_steps import StartQuoteParts
from fno.daily.steps import Alerted, CommandStep, LiveFrom, NotBefore
from fno.daily.wiring import live_dates
from fno.desk.run_log import problem_steps
from fno.models import IST
from tests.timetable.fakes import Clock

from .test_candle_step import _built_steps


from .test_v4_part import run as part_run


def _built_runner(monkeypatch, day):
    """The real wiring with the real config for `day` (so the AI books' live dates are read for that session)."""
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda cfg, root: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    runner = wiring.build_day_runner(load_app_config(), day=day)
    return runner, seen["day_steps"]


SESSIONS = (date(2026, 10, 26), date(2026, 10, 27), date(2026, 11, 2))  # Monday, Tuesday, the next Monday
FORECASTING_STEPS = (
    "weather", "forecasts_v4", V4_RELEASE_STEP, "v4_deadline", "forecasts_v4_pack", "card", "price_distribution",
    "price_distribution_scores", "price_ranges", "price_range_scores", "premium_ranges", "premium_range_scores",
    "recommend", "ai_fire", "ai_collect",
)  # fmt: skip
CAPTURE_LIVE_FROM = {"close_read": date(2026, 10, 23), "close_recheck": date(2026, 10, 23),
                     "v4_pack": date(2026, 10, 26)}  # fmt: skip


def test_every_forecasting_step_of_the_daily_run_is_not_live_on_the_first_session_and_after(monkeypatch):
    for day in SESSIONS:  # built per session: the AI books' live dates are read for that day
        _, steps = _built_runner(monkeypatch, day)
        for name in FORECASTING_STEPS:
            assert name in DAILY_RUN_STEPS and name in steps
            result = steps[name].run(day).result
            assert result["status"] == STEP_NOT_LIVE, (name, day, result)


def test_the_repository_config_holds_exactly_the_capture_dates_and_the_ai_go_live_date():
    """Every other `daily.live_from` key is null. `ai_books_v4` keeps its date on purpose: null would restart the v2 AI
    fire and collection (fno/ai/fire.py, fno/ai/collect.py)."""
    from fno.ai.wiring import v4_live_from

    raw = load_app_config()["daily"]["live_from"]
    dated = {key: str(value) for key, value in raw.items() if value}
    assert dated == {
        "ai_books_v4": "2026-10-26", "v4_pack": "2026-10-26", "close_read": "2026-10-23", "close_recheck": "2026-10-23",
    }  # fmt: skip
    assert v4_live_from(load_app_config()) == date(2026, 10, 26)
    assert (
        live_dates(load_app_config())[V4_RELEASE_STEP] is None
    )  # the release has its own key, apart from the capture's


def test_the_other_switches_are_off_in_the_repository_config():
    config = load_app_config()
    assert config["forecast_lab"]["live_from"] == {"morning": None, "evening": None}
    assert config["school"]["enabled"] is False and config["school"]["reports"] is False


def test_the_captures_keep_their_steps_and_their_dates(monkeypatch):
    steps = _built_steps(monkeypatch)
    for name in ("quotes", "quotes_done", "candles", "close_read", "close_recheck", "margin_check"):
        assert name in DAILY_RUN_STEPS and isinstance(steps[name], Alerted)
    assert isinstance(steps["quotes"].step, StartQuoteParts)
    assert isinstance(steps["candles"].step, NotBefore) and isinstance(steps["candles"].step.step, CommandStep)
    for name in ("close_read", "close_recheck"):
        assert isinstance(steps[name].step, LiveFrom) and steps[name].step.live_from == CAPTURE_LIVE_FROM[name]
    live = live_dates(load_app_config())
    assert {key: live[key] for key in CAPTURE_LIVE_FROM} == CAPTURE_LIVE_FROM


def test_the_v4_capture_part_is_a_part_of_every_session_though_the_release_is_off(tmp_path):
    """The coupling STAB1 removed: `v4_pack` gates the 14:32-14:40 capture and `v4_release` the release and the 15:10
    check. A part that is a part of the day starts; the release records `not_live` in the same run."""
    live = live_dates(load_app_config())
    for day in SESSIONS:
        clock = Clock()
        clock.now = datetime(day.year, day.month, day.day, 14, 7, tzinfo=IST)
        parts, _, _, _ = part_run(tmp_path / str(day), clock, live=live["v4_pack"])
        started = StartQuoteParts(parts).run(day)
        assert set(started.inputs["parts"]) == {"nifty", "nse", "indices", "v4"}, day
    assert live["v4_pack"] is not None and live[V4_RELEASE_STEP] is None


def test_switched_off_steps_are_no_problem_of_the_day():
    """The run's last line, the card and the health check read `problem_steps`: a not-live step is not one."""
    steps = {name: {"result": {"status": STEP_NOT_LIVE, "reason": "no live date set"}} for name in FORECASTING_STEPS}
    assert problem_steps(steps) == []


def test_the_school_step_prints_school_off_and_builds_nothing(monkeypatch):
    from fno.school import wiring
    from fno.school.cli import cmd_run

    monkeypatch.setattr(wiring, "build_alert_sender", lambda: (_ for _ in ()).throw(AssertionError("built")))
    printed = []
    assert cmd_run(Namespace(session=SESSIONS[0], replay=None), out=printed.append) == 0
    assert printed == ["school off"]


def test_a_lab_edition_without_a_live_date_builds_no_composer_reads_no_record_and_exits_clean(monkeypatch):
    """`lab open` and `lab close` at 08:38 and 19:53: not live, so no Drive sign-in, no Drive sync of G13b's
    records, no record read."""
    from fno.forecast_lab import wiring
    from fno.forecast_lab.constants import EVENING, MORNING

    def forbidden(*args, **kwargs):
        raise AssertionError("a not-live edition built or read something")

    nothing = SimpleNamespace(posted=forbidden, alerted=forbidden, report=forbidden)
    monkeypatch.setattr(wiring, "build_composer", forbidden)
    monkeypatch.setattr(wiring, "records", forbidden)  # building the records signs in to Drive
    monkeypatch.setattr(wiring, "build_forecast_poster", lambda env=None: nothing)
    monkeypatch.setattr(wiring, "build_alert_sender", lambda: nothing)
    for edition in (MORNING, EVENING):
        result = wiring.build_edition(edition).run(SESSIONS[0])
        assert result.failed is False and len(result.lines) == 1 and "not live" in result.lines[0], result.lines


def _triggers(name: str) -> set[str]:
    return set(yaml.safe_load((ROOT / ".github/workflows" / f"{name}.yml").read_text(encoding="utf-8"))[True])


FORECASTING_WORKFLOWS = ("forecast-capture", "forecast-scores", "v4-fire", "postmortem-weekly")
FORECASTING_COMMANDS = ("fno forecast", "fno ai ", "forecast-scores", "forecast-v4", "fno postmortem", "fno lab",
                        "fno card", "pricedist", "pricerange", "premrange", "weather capture", "fno recommend",
                        "fno school", "v4-pack")  # fmt: skip


def test_the_forecasting_workflows_have_no_automatic_trigger():
    for name in FORECASTING_WORKFLOWS:
        assert _triggers(name) == {"workflow_dispatch"}, name


def test_no_workflow_that_runs_a_forecasting_command_has_an_automatic_trigger():
    for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        runs = " ".join(
            step.get("run", "") for job in yaml.safe_load(path.read_text(encoding="utf-8"))["jobs"].values()
            for step in job.get("steps", [])
        )  # fmt: skip
        if any(command in runs for command in FORECASTING_COMMANDS):
            assert _triggers(path.stem) == {"workflow_dispatch"}, path.name


def test_exactly_these_workflows_are_manual_only_so_no_capture_lost_its_trigger():
    names = [p.stem for p in Path(ROOT / ".github/workflows").glob("*.yml")]
    manual = {name for name in names if _triggers(name) == {"workflow_dispatch"}}
    assert manual == {*FORECASTING_WORKFLOWS, "routine-fire-probe"}


def test_the_built_run_gives_its_quote_parts_the_capture_key_not_the_release_key(monkeypatch):
    """`build_day_runner` hands QuoteParts the real dates, so the v4 part is live, the release not."""
    runner, steps = _built_runner(monkeypatch, SESSIONS[0])
    assert runner.parts.live["v4_pack"] == date(2026, 10, 26) and runner.parts.live[V4_RELEASE_STEP] is None
    assert steps[V4_RELEASE_STEP].step.live_from is None
