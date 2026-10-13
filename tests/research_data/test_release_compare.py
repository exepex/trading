"""Story O6 criterion 1: the routine's and the Actions copy's release logs, compared day by day."""

from datetime import date, datetime, timedelta

from fno.models import IST
from fno.research_data.release_compare import ReleaseLogComparison
from fno.research_data.release_times import ReleaseCheck

DAY = date(2026, 10, 14)
INTERVAL = timedelta(minutes=5)


def _at(hour: int, minute: int) -> datetime:
    return datetime(2026, 10, 14, hour, minute, tzinfo=IST)


def _log(present_at: datetime, sha: str = "a" * 64) -> list[ReleaseCheck]:
    return [ReleaseCheck(DAY, _at(17, 11), "absent"), ReleaseCheck(DAY, present_at, "present", sha)]


def test_same_file_seen_within_one_interval_is_the_same_output():
    lines = ReleaseLogComparison(_log(_at(18, 1)), _log(_at(18, 4)), INTERVAL).lines()
    assert lines[0].endswith("; same") and lines[-1].startswith("1 of 1 days the same")


def test_another_file_or_a_late_sighting_differs_and_a_lone_run_is_named():
    assert ReleaseLogComparison(_log(_at(18, 1)), _log(_at(18, 1), "b" * 64), INTERVAL).lines()[0].endswith("DIFFERENT")
    assert ReleaseLogComparison(_log(_at(18, 1)), _log(_at(18, 30)), INTERVAL).lines()[0].endswith("DIFFERENT")
    assert ReleaseLogComparison(_log(_at(18, 1)), [], INTERVAL).lines()[0].endswith("only one ran")
