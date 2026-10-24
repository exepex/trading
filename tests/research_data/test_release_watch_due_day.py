"""Story O10: `participant-oi watch` watches the file still due. participant-oi-release's 22:45 IST slot started at
01:51-03:22 IST on 13-15 Oct 2026 and watched the next day's file until GitHub's timeout cancelled it (runs 4, 6, 8)."""

from datetime import date, datetime, time, timedelta

import pytest

import fno.composition
from fno.cli import main
from fno.constants import RELEASE_ABSENT
from fno.models import IST
from fno.research_data import participant_oi_cli
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.release_times import ReleaseLog, ReleaseTimeRecorder
from fno.storage.raw_source import ParticipantOiSource, RawFileSource

SOURCE = "https://nsearchives.nseindia.com/content/circulars/FAOP71777.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-20,holiday,Diwali (test),{SOURCE}\n")


class NotYetPublished(RawFileSource):
    def __init__(self):
        self.asked = []

    def fetch(self, path):
        self.asked.append(path)
        return None


class FakeRecorder:
    watched: list[tuple[date, datetime]] = []

    def __init__(self, log=None):
        pass

    def recheck_recent(self, day):
        return []

    def watch(self, day, until, every):
        self.watched.append((day, until))
        return None


@pytest.mark.parametrize(
    ("now", "day"),
    [
        (datetime(2026, 10, 16, 1, 52, tzinfo=IST), date(2026, 10, 15)),  # the late second slot: the evening before
        (datetime(2026, 10, 16, 11, 59, tzinfo=IST), date(2026, 10, 15)),
        (datetime(2026, 10, 16, 12, 0, tzinfo=IST), date(2026, 10, 16)),
        (datetime(2026, 10, 16, 17, 11, tzinfo=IST), date(2026, 10, 16)),  # on time: today
    ],
)
def test_watch_takes_the_due_day(monkeypatch, now, day):
    monkeypatch.setattr(FakeRecorder, "watched", [])
    monkeypatch.setattr(participant_oi_cli, "now_ist", lambda: now)
    monkeypatch.setattr(fno.composition, "build_release_time_recorder", FakeRecorder)
    assert main(["participant-oi", "watch", "--until", "23:30"]) == 0
    assert FakeRecorder.watched == [(day, datetime.combine(day, time(23, 30), IST))]


def test_an_explicit_day_wins(monkeypatch):
    monkeypatch.setattr(FakeRecorder, "watched", [])
    monkeypatch.setattr(participant_oi_cli, "now_ist", lambda: datetime(2026, 10, 16, 1, 52, tzinfo=IST))
    monkeypatch.setattr(fno.composition, "build_release_time_recorder", FakeRecorder)
    main(["participant-oi", "watch", "--day", "2026-10-14"])
    assert FakeRecorder.watched[0][0] == date(2026, 10, 14)


def test_a_watch_whose_window_has_passed_checks_once_and_returns(tmp_path):
    """The late slot's real path: the due day (15 Oct) with `until` 15 Oct 23:30, run at 16 Oct 01:52: one check."""
    day, sleeps, archive = date(2026, 10, 15), [], NotYetPublished()
    log = ReleaseLog(tmp_path / "release_checks.csv")
    recorder = ReleaseTimeRecorder(archive, ParticipantOiSource.path_for, CALENDAR, log,
                                   lambda: datetime(2026, 10, 16, 1, 52, tzinfo=IST), sleeps.append)  # fmt: skip
    check = recorder.watch(day, datetime.combine(day, time(23, 30), IST), timedelta(minutes=5))
    assert check.outcome == RELEASE_ABSENT and archive.asked == [ParticipantOiSource.path_for(day)] and sleeps == []


def test_due_day_prints_the_evening_before_after_midnight(monkeypatch, capsys):
    monkeypatch.setattr(participant_oi_cli, "now_ist", lambda: datetime(2026, 10, 16, 1, 52, tzinfo=IST))
    assert main(["participant-oi", "due-day"]) == 0
    assert capsys.readouterr().out.strip() == "2026-10-15"


def test_the_release_workflow_gives_one_day_to_the_watch_and_the_librarian():
    """Judge 350 SF2: the day is computed once; no step computes its own from the clock."""
    from pathlib import Path

    import yaml

    workflow = Path(__file__).resolve().parents[2] / ".github/workflows/participant-oi-release.yml"
    steps = {s.get("id"): s for s in yaml.safe_load(workflow.read_text(encoding="utf-8"))["jobs"]["release"]["steps"]}
    assert "participant-oi due-day" in steps["due"]["run"]
    for step in ("watch", "librarian"):
        assert steps[step]["env"]["DAY"] == "${{ steps.due.outputs.day }}"
        assert "date +%F" not in steps[step]["run"] and '"$DAY"' in steps[step]["run"]
    assert '--day "$DAY"' in steps["watch"]["run"]
    assert '--from "$DAY" --to "$DAY"' in steps["librarian"]["run"]
