"""Story O1 (asked by E8, judge 203 should-fix 1): the run fetches the whole git history before the day starts; a
failed fetch is one alert and the day goes on."""

import shutil
import subprocess

from fno.daily.history import WholeHistory
from fno.daily.runner import DayRunner
from fno.desk.git_sync import Git


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def shallow_clone(tmp_path):
    origin = tmp_path / "origin"
    origin.mkdir()
    git(origin, "init", "-q", "-b", "main")
    for key, value in (("user.email", "t@example.org"), ("user.name", "t")):
        git(origin, "config", key, value)
    for n in range(3):
        (origin / "f.txt").write_text(str(n))
        git(origin, "add", "f.txt")
        git(origin, "commit", "-q", "-m", f"c{n}")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{origin}", str(clone)], check=True)
    return origin, clone


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


def test_a_shallow_checkout_gets_its_whole_history_and_a_whole_one_is_left_alone(tmp_path):
    _, clone = shallow_clone(tmp_path)
    assert git(clone, "rev-parse", "--is-shallow-repository") == "true"
    assert Git(clone).unshallow() is True
    assert (
        git(clone, "rev-parse", "--is-shallow-repository") == "false"
        and git(clone, "rev-list", "--count", "HEAD") == "3"
    )
    assert Git(clone).unshallow() is False


def test_a_failed_fetch_is_one_alert_and_the_day_goes_on(tmp_path):
    origin, clone = shallow_clone(tmp_path)
    shutil.rmtree(origin)
    alerts = Alerts()
    WholeHistory(Git(clone), alerts)()
    (sent,) = alerts.sent
    assert "checkout is shallow" in sent and "exits run" in sent


def test_the_runner_starts_the_parts_then_takes_the_whole_history_then_runs_the_day(tmp_path):
    from datetime import date

    order = []

    class Run:
        steps = type("Steps", (), {"root": tmp_path, "timetable": None})()

        def run(self, day):
            order.append("day")
            return type("Log", (), {"steps": {}})()

    class Parts:
        def start(self, day):
            order.append("parts")

        def busy(self):
            return False

    DayRunner(Run(), Parts(), waiter=None, before=lambda: order.append("history")).run(date(2026, 10, 14))
    assert order == ["parts", "history", "day"]


def test_a_hung_fetch_is_stopped_at_its_limit_and_is_one_alert(tmp_path):
    """Judge 178 addendum 10 (made a must by the orchestrator): a fetch that never answers cannot hold the day."""
    _, clone = shallow_clone(tmp_path)
    real = subprocess.run

    def hung(command, **options):
        if command[:2] == ["git", "fetch"]:
            raise subprocess.TimeoutExpired(command, options["timeout"])
        return real(command, **options)

    alerts = Alerts()
    WholeHistory(Git(clone, run=hung), alerts)()
    (sent,) = alerts.sent
    assert "ran past 120 s and was stopped" in sent
    assert git(clone, "rev-parse", "--is-shallow-repository") == "true"
