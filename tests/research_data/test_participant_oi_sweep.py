"""Judge 16: `python -m fno participant-oi sweep` catches a rewrite months after release, which the recorder's 5-session
recheck misses, and the moved write time holds that day back in the wired rule."""

from datetime import date, datetime

import fno.composition
from fno.cli import main
from fno.models import IST
from fno.research_data.availability import LastWriteBoundRule, NextSessionRule
from fno.research_data.calendar import CsvSessionCalendar
from fno.research_data.last_written import latest_writes
from fno.research_data.write_sweep import LastWriteSweep, read_sweeps
from fno.storage.raw_source import ParticipantOiSource, RawFileSource, RawSourceUnavailable

SOURCE = "https://nsearchives.nseindia.com/content/circulars/FAOP65588.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2025-12-25,holiday,Christmas,{SOURCE}\n")
JAN_15, JAN_16 = date(2025, 1, 15), date(2025, 1, 16)


def at(day: date, hour: int) -> datetime:
    return datetime(day.year, day.month, day.day, hour, tzinfo=IST)


class HeadersOnlyArchive(RawFileSource):
    def __init__(self, writes):
        self.writes, self.asked = writes, []

    def fetch(self, path):
        raise AssertionError("a sweep asks for headers only")

    def last_written(self, path):
        self.asked.append(path)
        answer = self.writes[path]
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_a_rewrite_months_later_is_logged_and_holds_the_day_back(tmp_path):
    recorded = {JAN_15: at(JAN_15, 19), JAN_16: at(JAN_16, 19), date(2025, 1, 17): at(date(2025, 1, 17), 19)}
    archive = HeadersOnlyArchive({
        ParticipantOiSource.path_for(JAN_15): at(date(2025, 6, 2), 18),  # rewritten four months later
        ParticipantOiSource.path_for(JAN_16): at(JAN_16, 19),  # unchanged
        ParticipantOiSource.path_for(date(2025, 1, 17)): RawSourceUnavailable("down"),
    })  # fmt: skip
    log = tmp_path / "last_modified_sweeps.csv"
    result = LastWriteSweep(archive, ParticipantOiSource.path_for, log, lambda: at(date(2025, 7, 1), 6)).run(recorded)
    assert (result.checked, result.moved, result.unanswered) == (
        3,
        [(JAN_15, at(JAN_15, 19), at(date(2025, 6, 2), 18))],
        [date(2025, 1, 17)],
    )
    assert log.read_text().splitlines()[0] == "day,checked_at,last_modified" and len(log.read_text().splitlines()) == 2
    written = latest_writes(recorded, read_sweeps(log))
    rule = LastWriteBoundRule(
        NextSessionRule(CALENDAR, at(JAN_15, 15).time()), CALENDAR, at(JAN_15, 15).time(), written
    )
    assert rule.usable_from(JAN_15) == at(date(2025, 6, 3), 15)  # not before the bytes NSE serves now were written
    assert rule.usable_from(JAN_16) == at(date(2025, 1, 17), 15)  # unchanged day: next session


def test_the_nse_source_asks_for_headers_only(monkeypatch):
    class Session:
        def __init__(self):
            self.heads = []

        def head(self, url, timeout=None):
            self.heads.append(url)
            return type("R", (), {"status_code": 200, "headers": {"Last-Modified": "Wed, 15 Jan 2025 13:30:03 GMT"},
                                  "raise_for_status": lambda self: None})()  # fmt: skip

        def get(self, url, timeout=None):
            raise AssertionError("no body for a sweep")

    session = Session()
    written = ParticipantOiSource(session).last_written(ParticipantOiSource.path_for(date(2024, 1, 15)))
    assert written == datetime(2025, 1, 15, 19, 0, 3, tzinfo=IST)
    assert session.heads == ["https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_15012024.csv"]


def test_the_sweep_command_alerts_on_a_moved_write_and_on_no_answer(monkeypatch, capsys, tmp_path):
    archive = HeadersOnlyArchive({ParticipantOiSource.path_for(JAN_15): at(date(2025, 6, 2), 18)})
    sweep = LastWriteSweep(archive, ParticipantOiSource.path_for, tmp_path / "s.csv")
    monkeypatch.setattr(fno.composition, "build_last_write_sweep", lambda: sweep)
    monkeypatch.setattr(fno.composition, "participant_oi_last_writes", lambda: {JAN_15: at(JAN_15, 19)})
    assert main(["participant-oi", "sweep"]) == 1
    out = capsys.readouterr().out
    assert "MOVED 2025-01-15" in out and "sweep: 1 files checked, 1 moved, 0 unanswered" in out
    archive.writes[ParticipantOiSource.path_for(JAN_15)] = at(JAN_15, 19)
    monkeypatch.setattr(
        fno.composition,
        "build_last_write_sweep",
        lambda: LastWriteSweep(archive, ParticipantOiSource.path_for, tmp_path / "t.csv"),
    )
    assert main(["participant-oi", "sweep"]) == 0


def test_the_wired_rule_reads_the_sweep_log(monkeypatch, tmp_path):
    log = tmp_path / "last_modified_sweeps.csv"
    log.write_text("day,checked_at,last_modified\n2026-10-09,2026-11-02T06:00:00+05:30,2026-10-30T18:00:00+05:30\n")
    monkeypatch.setattr(fno.composition, "PARTICIPANT_OI_SWEEPS", log)
    rule = fno.composition.build_participant_oi_rule()
    assert rule.usable_from(date(2026, 10, 9)) == at(date(2026, 11, 2), 15)  # 30 Oct 18:00 write: next session
    assert rule.usable_from(date(2026, 10, 8)) == at(date(2026, 10, 9), 15)
