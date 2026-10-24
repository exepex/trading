"""FL1-1d-2: the evening's read-only release check. FII and DII cash count as out only when NSE's answer names the
session (its API answers with its latest day and no time); an unreachable NSE says nothing; each check is appended
to the log in A8's format, and the lines say when each file was last written, in IST."""

import json
from datetime import UTC, date, datetime

from fno.forecast_lab.release import FlowsRelease, ReleaseChecks
from fno.research_data.release_times import ReleaseCheck, ReleaseLog
from fno.storage.raw_source import PublishedFile, RawSourceUnavailable
from tests.forecast_lab.builders import at

WED = date(2026, 10, 21)


def answer(day_text):
    return json.dumps([{"category": "FII/FPI", "date": day_text, "netValue": "1.0"}]).encode()


class Source:
    def __init__(self, data=None, down=False):
        self.data, self.down, self.paths = data, down, []

    def fetch_published(self, path):
        self.paths.append(path)
        if self.down:
            raise RawSourceUnavailable("NSE did not answer")
        return PublishedFile(self.data, None) if self.data is not None else None


def flows(tmp_path, source):
    return FlowsRelease(source, lambda day: f"flows/{day}", ReleaseLog(tmp_path / "release_checks.csv"),
                        lambda: at(WED, 19, 55))  # fmt: skip


def test_fii_dii_is_out_only_when_nse_names_the_session(tmp_path):
    assert flows(tmp_path, Source(answer("21-Oct-2026"))).check(WED).outcome == "present"
    assert flows(tmp_path, Source(answer("20-Oct-2026"))).check(WED).outcome == "absent"
    assert flows(tmp_path, Source(b"<html>")).check(WED).outcome == "absent"
    assert flows(tmp_path, Source(down=True)).check(WED).outcome == "unreachable"
    log = ReleaseLog(tmp_path / "release_checks.csv").checks()
    assert [c.outcome for c in log] == ["present", "absent", "absent", "unreachable"]
    assert log[0].sha256 and not log[1].sha256


def test_each_line_says_the_outcome_and_the_last_write_in_ist():
    class Fixed:
        def __init__(self, check):
            self.check_made = check

        def check(self, day):
            return self.check_made

    written = ReleaseCheck(WED, at(WED, 19, 55), "present", "x", datetime(2026, 10, 21, 13, 44, 3, tzinfo=UTC))
    absent = ReleaseCheck(WED, at(WED, 19, 55), "absent")
    lines = ReleaseChecks({"fo-bhavcopy": Fixed(written), "fii-dii-cash": Fixed(absent)}).run(WED)
    assert lines == ["release check fo-bhavcopy 2026-10-21: present (last written 19:14 IST)",
                     "release check fii-dii-cash 2026-10-21: absent"]  # fmt: skip
