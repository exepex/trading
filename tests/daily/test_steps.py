"""Story O1, criteria 2 and 6: an O1 command's status from its exit code and printed lines, `live_from`, the alert
rule, the settings, and the command's one line."""

import inspect
from argparse import Namespace
from datetime import date, timedelta

from fno.config import ALLOWED_APP_KEYS, load_app_config
from fno.constants import STEP_FAILED, STEP_NOT_LIVE, STEP_OK, STEP_REFUSED
from fno.daily import cli as daily_cli
from fno.daily.steps import COMMAND_LIMIT_SECONDS, NOTHING_WRITTEN, Alerted, CommandStep, LiveFrom, outcome
from fno.daily.wiring import MARGIN_CHECK, live_dates
from fno.forecast_v4_rules import cli as v4_cli
from fno.weather import cli as weather_cli
from tests.timetable.fakes import Clock

from .fakes import FakeProcesses, QuietLocks, RecordedStep

DAY = date(2026, 10, 14)


def test_exit_zero_is_ok_a_printed_refusal_is_refused_anything_else_failed():
    assert outcome(("x",), 0, ["weather 2026-10-14: 9 rows"]).result["status"] == STEP_OK
    refused = outcome(("x",), 0, [f"weather 2026-10-14: {NOTHING_WRITTEN} at or after the 15:00 cutoff"]).result
    assert refused["status"] == STEP_REFUSED and refused["reason"].endswith("cutoff")
    assert outcome(("x",), 1, []).result == {"status": STEP_FAILED, "reason": "exit code 1, nothing printed",
                                             "exit_code": 1, "lines": []}  # fmt: skip


def test_the_refusal_phrase_is_the_one_the_weather_and_v4_commands_print():
    """If either command changes how it prints a refusal, this fails before a refusal is read as ok."""
    assert all(NOTHING_WRITTEN in inspect.getsource(module) for module in (weather_cli, v4_cli))


def test_a_command_step_commits_the_files_it_changed_under_its_pathspecs_only():
    clock = Clock()
    processes = FakeProcesses(clock, {("weather", "capture"): (clock(), 0, ["weather: 9 rows"])})
    asked = []
    step = CommandStep(processes, lambda day: ("weather", "capture"), ("research/forecasts/v4/",),
                       lambda specs: asked.append(specs) or ["a.csv"], sleep=clock.advance)  # fmt: skip
    done = step.run(DAY)
    assert done.paths == ("a.csv",) and asked == [("research/forecasts/v4/",)] and done.result["status"] == STEP_OK
    no_specs = CommandStep(processes, lambda day: ("weather", "capture"), (), lambda specs: 1 / 0, sleep=clock.advance)
    assert no_specs.run(DAY).paths == ()  # Book 1 commits its own: nothing else is ever swept up


def test_before_its_live_date_or_with_none_a_step_is_not_live_and_calls_nothing():
    calls = []
    for live_from in (None, date(2026, 10, 15)):
        done = LiveFrom(RecordedStep("weather", calls), live_from).run(DAY)
        assert done.result["status"] == STEP_NOT_LIVE
    assert calls == []
    assert LiveFrom(RecordedStep("weather", calls), DAY).run(DAY).result["status"] == STEP_OK and calls == ["weather"]


def test_not_live_and_ok_are_never_alerted_a_raise_always_is(alerts):
    Alerted("card", LiveFrom(RecordedStep("card", []), None), alerts).run(DAY)
    Alerted("card", RecordedStep("card", []), alerts).run(DAY)
    assert alerts.sent == []
    quiet = Alerted("quotes_done", RecordedStep("q", [], {"status": STEP_FAILED, "reason": "nse"}), alerts, False)
    assert quiet.run(DAY).result["status"] == STEP_FAILED and alerts.sent == []  # the parts alert for themselves
    Alerted("quotes_done", RecordedStep("q", [], raises=OSError("disk")), alerts, False).run(DAY)
    assert alerts.sent == ["F&O daily run 2026-10-14: step quotes_done failed: OSError: disk; the run goes on"]


def test_the_live_dates_come_from_config_phase_1_from_22_oct():
    assert "daily" in ALLOWED_APP_KEYS
    phase_1 = date(2026, 10, 22)  # owner, 21 Oct (DESK_DECISIONS c58788bc): G13, G13b and FL1-1 live
    assert live_dates(load_app_config()) == {
        "margin_check": None, "card": None, "owner_timing_fills": None,
        "weather": phase_1,  # M1, on before the v4 freeze (owner, 21 Oct, DESK_DECISIONS 3a24ba24; response 299)
        "forecasts_v4": phase_1,  # G7's rule forecasts, the same; uncounted until the day after `Frozen on:`
        "price_distribution": phase_1,  # story G13
        "price_distribution_scores": phase_1,  # G13's daily scores
        "price_ranges": phase_1,  # story G13b
        "price_range_scores": phase_1,  # G13b's daily scores and seals
        "lab_close": None,  # story FL1-1: held until its HTML report is signed off (owner, f21a8966)
    }  # fmt: skip
    assert live_dates({"daily": {"live_from": {"card": "2026-10-20"}}})["card"] == date(2026, 10, 20)


def test_the_command_prints_the_runner_s_one_line_and_returns_its_code(monkeypatch):
    class Runner:
        def run(self, day):
            return 1, f"day done with problems: weather ({day})"

    monkeypatch.setattr("fno.daily.wiring.build_day_runner", lambda cfg: Runner())
    printed = []
    assert daily_cli.cmd_daily_run(Namespace(day=DAY), out=printed.append) == 1
    assert printed == ["day done with problems: weather (2026-10-14)"]


def test_the_wiring_gives_every_o1_step_and_a14c_s_check_runs_first_writing_one_file(monkeypatch):
    """Every name of DAILY_RUN_STEPS has a step (the desk's own, or O1's from the wiring); the quote parts start
    first, then A14c's check (judge 178 add. 1 note 6), which commits only its own file."""
    from fno.constants import DAILY_RUN_STEPS, DESK_RUN_STEPS
    from fno.daily import wiring

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda cfg, root: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    wiring.build_day_runner(load_app_config())
    assert set(seen["day_steps"]) | set(DESK_RUN_STEPS) == set(DAILY_RUN_STEPS)
    assert DAILY_RUN_STEPS[:3] == ("quotes", "owner_timing_fills", "margin_check") and wiring.MARGIN_CHECKS.endswith(
        "stress_broker_check.csv"
    )


def test_a_command_still_running_at_its_limit_is_stopped_and_failed_never_holding_the_day():
    """Judge 178 addendum 1, note 6: a hung Groww call in a command can never delay the 3 pm capture or the deadline."""
    clock = Clock()
    processes = FakeProcesses(clock, {("margins", "stress-broker-check"): (clock() + timedelta(hours=5), 0, [])})
    asked = []
    step = CommandStep(processes, lambda day: MARGIN_CHECK, ("x.csv",), lambda specs: asked.append(specs) or [],
                       sleep=clock.advance)  # fmt: skip
    done = step.run(DAY)
    assert done.result == {
        "status": STEP_FAILED,
        "reason": "stopped after 10 minutes without ending; nothing of it committed",  # no locks given: none removed
    }
    assert processes.made[MARGIN_CHECK].stopped and asked == [] and done.paths == ()
    assert clock() - processes.started[0][0] == timedelta(seconds=COMMAND_LIMIT_SECONDS)


def test_a_command_stopped_inside_its_own_git_commit_leaves_no_lock(tmp_path):
    """Story O2 (judge 204 addendum 2): Book 1's `desk book1` commits its own decision; stopped at the limit mid-commit,
    the locks its git took are removed (they were not there when it started), and one that was there stays."""
    (tmp_path / ".git" / "refs").mkdir(parents=True)
    (tmp_path / ".git" / "config.lock").write_text("")  # another writer's, older than the command
    clock = Clock()
    book1 = ("desk", "book1", "--day", DAY.isoformat())
    processes = FakeProcesses(clock, {book1: (clock() + timedelta(hours=5), 0, [])})

    class MidCommit(QuietLocks):
        def present(self):
            if processes.started:  # the command has started its commit
                (tmp_path / ".git" / "index.lock").write_text("")
            return super().present()

    step = CommandStep(
        processes, lambda day: book1, (), lambda specs: [], sleep=clock.advance, locks=MidCommit(tmp_path)
    )
    done = step.run(DAY)
    assert done.result["reason"].endswith("; the git lock files it left removed: .git/index.lock")
    assert not (tmp_path / ".git" / "index.lock").exists() and (tmp_path / ".git" / "config.lock").exists()


def test_an_alert_slack_did_not_take_is_printed_for_the_connector_one_it_took_is_not():
    """Every alert of the run (O1's and the desk's) goes through one sender; without Slack it is never lost silently."""
    from fno.alerts.sender import SENT, NoAlertSender
    from fno.daily.alerts import ReportedAlerts

    class Sent:
        def send(self, text):
            return SENT

    printed = []
    ReportedAlerts(Sent(), printed.append).send("F&O daily run: step weather failed")
    outcome = ReportedAlerts(NoAlertSender("FNO_SLACK_BOT_TOKEN is not set"), printed.append).send("step card failed")
    assert printed == [f"{outcome} | step card failed"] and outcome.startswith("alert NOT sent")


def test_the_desk_and_o1_share_that_one_sender(monkeypatch):
    from fno.daily import wiring
    from fno.daily.alerts import ReportedAlerts

    seen = {}
    monkeypatch.setattr("fno.desk.daily_wiring.build_daily_run", lambda *a, **k: seen.update(k) or object())
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_orders", lambda cfg, root: None)
    monkeypatch.setattr("fno.books.book1_wiring.build_book1_exit_rules", lambda *args: None)
    wiring.build_day_runner(load_app_config())
    assert isinstance(seen["alerts"], ReportedAlerts)


def test_every_sender_inside_the_built_run_is_its_one_reported_sender():
    """Judge 178 addendum 7, should-fix 9(b): no part of the run (desk, exit desk, Book 1's exit rules, data gate,
    O1's steps, the quote parts) keeps a sender of its own that would drop an unsent alert."""
    from fno.alerts.sender import AlertSender
    from fno.daily import wiring
    from fno.daily.alerts import ReportedAlerts

    runner = wiring.build_day_runner(load_app_config())
    shared, found, seen = runner.parts.alerts, [], set()

    def walk(value, depth=0):
        if isinstance(value, AlertSender):
            found.append(value)  # every place a sender is held, counted; its own inner Slack sender is not walked
            return
        if id(value) in seen or depth > 8 or isinstance(value, (str, bytes, int, float, type(None))):
            return
        seen.add(id(value))
        items = value.values() if isinstance(value, dict) else value if isinstance(value, (list, tuple, set)) else (
            vars(value).values() if hasattr(value, "__dict__") else ())  # fmt: skip
        for item in items:
            walk(item, depth + 1)

    walk(runner)
    assert isinstance(shared, ReportedAlerts) and len(found) > 3 and all(sender is shared for sender in found)
