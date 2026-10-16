"""Story O8b: once, when NSE's calendar ends in fewer than `calendar_horizon_days` days, the health message carries one
line asking for the next year's holiday rows; the calendar's SHA-256 in a marker keeps it from repeating, and a changed
calendar re-arms it. The marker is written only after Slack accepted the message, never by a dry run."""

from datetime import date
from types import SimpleNamespace

import pytest

from fno.alerts.sender import SENT
from fno.config import load_app_config
from fno.health import cli as health_cli
from fno.health.checker import HealthCheck, HealthRun
from fno.health.horizon import HORIZON_MARKER, CalendarHorizon
from fno.health.report import message, verdict
from fno.health.run_record import RunRecord
from fno.health.wiring import build_health_check

from .fakes import CALENDAR, DAY, ist

LAST = date(2026, 12, 31)


def _horizon(tmp_path, sha="aaa", days=45):
    return CalendarHorizon(LAST, sha, tmp_path / "marker.txt", days)


@pytest.mark.parametrize(("day", "warns"), [(date(2026, 11, 16), False), (date(2026, 11, 17), True),
                                            (date(2026, 12, 31), True)])  # fmt: skip
def test_the_line_appears_only_when_fewer_than_45_days_are_left(tmp_path, day, warns):
    line = _horizon(tmp_path).warning(day)
    assert (line is not None) is warns
    assert not warns or line.startswith(f"NSE calendar covers only to 31 Dec 2026 ({(LAST - day).days} days left)")


def test_once_marked_the_same_calendar_never_warns_again_and_a_new_calendar_does(tmp_path):
    horizon = _horizon(tmp_path)
    horizon.mark()
    assert horizon.warning(date(2026, 11, 20)) is None
    assert (tmp_path / "marker.txt").read_text() == "aaa\n"
    assert _horizon(tmp_path, sha="bbb").warning(date(2026, 11, 20)) is not None  # the calendar changed: re-armed


def test_the_real_settings_and_calendar_warn_for_2027_from_17_november(tmp_path):
    horizon = build_health_check(load_app_config(), root=tmp_path).horizon
    assert horizon.days == 45 and horizon.last == LAST and horizon.marker == tmp_path / HORIZON_MARKER
    line = horizon.warning(date(2026, 11, 17))
    assert "add every row of NSE's 2027 holiday circular to" in line and line.endswith("stops on 1 Jan 2027")
    assert horizon.warning(date(2026, 11, 16)) is None


def test_the_warning_is_one_problem_line_of_the_message(tmp_path):
    check = HealthCheck([], CALENDAR, RunRecord(tmp_path / "runs.csv"), 6, _horizon(tmp_path))
    run = check.run(ist(date(2026, 11, 19), 17, 51))
    lines = message(run).splitlines()
    assert verdict(run) == "1 problem" and lines[1].startswith("- NSE calendar covers only to 31 Dec 2026")


class Sender:
    def __init__(self, outcome):
        self.outcome = outcome

    def send(self, text):
        return self.outcome


def _cli(monkeypatch, tmp_path, outcome=SENT, dry_run=False, warnings=("NSE calendar covers only to ...",)):
    horizon = _horizon(tmp_path)
    run = HealthRun(DAY, (DAY,), ("A",), (), (), tuple(warnings))
    monkeypatch.setattr("fno.health.wiring.build_health_check",
                        lambda cfg: SimpleNamespace(run=lambda now: run, horizon=horizon))  # fmt: skip
    monkeypatch.setattr("fno.health.wiring.build_run_record", lambda: RunRecord(tmp_path / "runs.csv"))
    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: Sender(outcome))
    code = health_cli.cmd_health(SimpleNamespace(at=ist(DAY, 17, 51), dry_run=dry_run), out=lambda line: None)
    return code, (tmp_path / "marker.txt").is_file()


def test_the_marker_is_written_after_slack_accepted_the_warning(monkeypatch, tmp_path):
    assert _cli(monkeypatch, tmp_path) == (0, True)


@pytest.mark.parametrize(("outcome", "dry_run", "code"), [("alert NOT sent: token_revoked", False, 1), (SENT, True, 0)])
def test_a_refused_post_or_a_dry_run_never_marks_so_the_warning_comes_again(monkeypatch, tmp_path, outcome, dry_run,
                                                                           code):  # fmt: skip
    assert _cli(monkeypatch, tmp_path, outcome=outcome, dry_run=dry_run) == (code, False)


def test_a_run_without_a_warning_never_marks(monkeypatch, tmp_path):
    assert _cli(monkeypatch, tmp_path, warnings=()) == (0, False)
