"""REH1j (the full dry run, 24 Oct): a step not live in real runs is exercised in a rehearsal and recorded `not_live`,
as the real day records it, with what it did under `exercised` (J1), its files kept (J2); a command fno has not built
is `not_built`, never run and never alerted (J3); the public log names each reason by its own code (J1, J3)."""

from datetime import date

from fno.constants import STEP_FAILED, STEP_NOT_BUILT, STEP_NOT_LIVE, STEP_OK
from fno.daily.processes import Process, Processes
from fno.daily.public_log import PublicResult, ReasonRegistry
from fno.daily.reason_codes import COMMON, STEP_TEMPLATES
from fno.daily.steps import Alerted, CommandStep, LiveFrom
from fno.desk.daily_ports import DayStep
from fno.desk.daily_steps import StepOutcome
from fno.rehearsal.built_commands import NOT_BUILT
from fno.rehearsal.live_wiring import NOT_LIVE_UNSET, NOT_LIVE_UNTIL, NotLiveInRealRuns, command_of, rehearsed_not_live

DAY = date(2026, 10, 23)
UNTIL = NOT_LIVE_UNTIL.format(day=DAY, live_from=date(2026, 10, 26))
MISSING = ("margins", "stress-broker-check")


class Ended(Process):
    def __init__(self, code: int, lines: list[str]):
        self.code, self.printed = code, lines

    def poll(self):
        return self.code

    def lines(self):
        return self.printed

    def errors(self):
        return []

    def stop(self):
        return None

    def alerted(self):
        return False


class Children(Processes):
    def __init__(self, code: int = 0, lines=("done",)):
        self.code, self.printed, self.started = code, list(lines), []

    def start(self, arguments, hold=None):
        self.started.append(tuple(arguments))
        return Ended(self.code, self.printed)


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "sent"


class Fixed(DayStep):
    def __init__(self, result: dict, paths=()):
        self.result, self.paths = result, tuple(paths)

    def run(self, day):
        return StepOutcome({"given": "inputs"}, dict(self.result), self.paths)


def command_step(arguments, children, alerts, name="margin_check"):
    step = CommandStep(children, lambda day: arguments, ("research/data/margins",), lambda specs: ["a.csv"])
    return Alerted(name, LiveFrom(step, DAY), alerts)


def built_by_the_real_parser(arguments):
    from fno.rehearsal.built_commands import is_built

    return is_built(arguments)


# J1: not counted, its outcome kept beside


def test_a_failing_not_live_step_is_recorded_not_live_with_what_it_did():
    failed = {"status": STEP_FAILED, "reason": "no receipts under data/premium_ranges/v1"}
    done = NotLiveInRealRuns(Fixed(failed), NOT_LIVE_UNSET).run(DAY)
    assert done.result == {"status": STEP_NOT_LIVE, "reason": NOT_LIVE_UNSET, "exercised": failed}
    assert done.inputs == {"given": "inputs"}


def test_an_ok_not_live_step_is_not_live_with_an_ok_exercise():
    done = NotLiveInRealRuns(Fixed({"status": STEP_OK, "reason": "posted"}), UNTIL).run(DAY)
    assert done.result["status"] == STEP_NOT_LIVE and done.result["exercised"]["status"] == STEP_OK


def test_a_live_step_is_never_wrapped_and_its_failure_stays_a_failure():
    steps = {"card": Fixed({"status": STEP_FAILED, "reason": "x"}), "weather": Fixed({"status": STEP_OK})}
    wrapped = rehearsed_not_live(steps, {"card": NOT_LIVE_UNSET})
    assert wrapped["weather"] is steps["weather"]
    assert wrapped["weather"].run(DAY).result["status"] == STEP_OK
    assert isinstance(wrapped["card"], NotLiveInRealRuns)


def test_the_public_log_names_each_reason_by_its_own_code():
    public = PublicResult(ReasonRegistry(COMMON, STEP_TEMPLATES))
    for note, code in ((NOT_LIVE_UNSET, "rehearsal:NOT_LIVE_UNSET"), (UNTIL, "rehearsal:NOT_LIVE_UNTIL"),
                       (NOT_BUILT.format(command="margins stress-broker-check"), "rehearsal:NOT_BUILT")):  # fmt: skip
        assert public.public("margin_check", {"reason": note})["reason"] == code


# J2: its files kept for the rehearsal's commit


def test_a_not_live_step_s_files_are_kept():
    done = NotLiveInRealRuns(Fixed({"status": STEP_OK}, paths=("receipts/x.sha256",)), NOT_LIVE_UNSET).run(DAY)
    assert done.paths == ("receipts/x.sha256",)


# J3: not built, never run, never alerted


def test_a_not_live_command_fno_has_not_built_is_not_built_never_run_never_alerted():
    children, alerts = Children(code=2), Alerts()
    step = NotLiveInRealRuns(command_step(MISSING, children, alerts), NOT_LIVE_UNSET, built_by_the_real_parser)
    done = step.run(DAY)
    assert done.result == {"status": STEP_NOT_LIVE, "reason": NOT_LIVE_UNSET,
                           "exercised": {"status": STEP_NOT_BUILT,
                                         "reason": "no command 'margins stress-broker-check' in fno"}}  # fmt: skip
    assert done.inputs == {"command": list(MISSING)}
    assert (children.started, alerts.sent) == ([], [])


def test_a_not_live_command_that_exists_runs():
    children, alerts = Children(code=0), Alerts()
    step = NotLiveInRealRuns(command_step(("margins", "stress-factor"), children, alerts), UNTIL)
    done = step.run(DAY)
    assert children.started == [("margins", "stress-factor")]
    assert done.result["exercised"]["status"] == STEP_OK and done.paths == ("a.csv",)


def test_a_live_step_with_a_missing_command_still_runs_and_fails():
    children, alerts = Children(code=2, lines=["fno: error: invalid choice"]), Alerts()
    step = rehearsed_not_live({"margin_check": command_step(MISSING, children, alerts)}, {})["margin_check"]
    assert step.run(DAY).result["status"] == STEP_FAILED
    assert children.started == [MISSING] and len(alerts.sent) == 1


def test_a_step_that_runs_no_command_is_never_checked():
    def never(arguments):
        raise AssertionError("checked a step with no command")

    assert command_of(Fixed({"status": STEP_OK})) is None
    assert NotLiveInRealRuns(Fixed({"status": STEP_OK}), NOT_LIVE_UNSET, never).run(DAY).result["status"] == "not_live"


def test_the_command_is_found_through_every_decorator_of_the_real_daily_run(monkeypatch, tmp_path):
    from fno.config import load_app_config
    from fno.constants import ENV_FNO_REHEARSAL
    from fno.daily import wiring
    from fno.rehearsal.mode import Rehearsal

    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(DAY, tmp_path, tmp_path).to_env())
    monkeypatch.setenv("FNO_SLACK_BOT_TOKEN", "xoxb-test")
    steps = wiring.build_day_runner(load_app_config(), sleep=lambda seconds: None).daily_run.day_steps
    wrapped = {name: step for name, step in steps.items() if isinstance(step, NotLiveInRealRuns)}
    assert wrapped and all(step.command for step in wrapped.values())  # each found under its decorators
    commands = {name: tuple(step.command(DAY)) for name, step in wrapped.items()}
    assert all(commands.values())
    if "margin_check" in wrapped:  # not live until A14c's code lands
        assert commands["margin_check"] == wiring.MARGIN_CHECK


def test_a_command_lookup_that_raises_is_recorded_never_a_crash():
    def broken(arguments):
        raise OSError("the parser could not be built")

    children, alerts = Children(), Alerts()
    done = NotLiveInRealRuns(command_step(MISSING, children, alerts), NOT_LIVE_UNSET, broken).run(DAY)
    assert done.result["status"] == STEP_NOT_LIVE
    assert done.result["exercised"] == {"status": STEP_FAILED, "reason": "OSError: the parser could not be built"}
    assert children.started == []
