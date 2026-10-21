"""NSE's day list call and the lazy member (story A21 part 2): one GET with a hard 5 s timeout and no retry, every
failure named; a member that cannot be built is one O10 row and one alert a day, never a broken recorder."""

import pytest
import requests

from fno.announcements_live import wiring
from fno.announcements_live.constants import REQUEST_TIMEOUT
from fno.announcements_live.source import NseDayList, PollFailed

from .helpers import DAY, Clock, at


class Response:
    def __init__(self, status, content):
        self.status_code, self.content = status, content


class Session:
    def __init__(self, answer):
        self.answer, self.headers, self.calls = answer, {}, []

    def get(self, url, timeout):
        self.calls.append((url, timeout))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def test_one_get_of_a12s_url_with_a_5_s_timeout_and_the_arrival_time():
    session = Session(Response(200, b'[{"seq_id": "1"}]'))
    found = NseDayList(Clock(at("10:00")), session).day_list(DAY)
    [(url, timeout)] = session.calls
    assert "corporate-announcements?index=equities&from_date=19-10-2026&to_date=19-10-2026" in url
    assert timeout == REQUEST_TIMEOUT and sum(REQUEST_TIMEOUT) == 5.0
    assert found.items == [{"seq_id": "1"}] and found.arrived_at == at("10:00", 1)


@pytest.mark.parametrize(
    ("answer", "kind"),
    [(Response(403, b""), "refused_403"), (Response(429, b""), "refused_429"), (requests.Timeout(), "timeout"),
     (requests.ConnectionError(), "unreachable"), (Response(200, b"<html>"), "bad_json"),
     (Response(200, b'{"error": 1}'), "bad_json")],
)  # fmt: skip
def test_every_failure_is_named_and_tried_once(answer, kind):
    session = Session(answer)
    with pytest.raises(PollFailed) as failed:
        NseDayList(Clock(at("10:00")), session).day_list(DAY)
    assert failed.value.kind == kind and len(session.calls) == 1


def test_a_member_that_cannot_be_built_records_once_a_day_and_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(wiring, "DRY_RUN_FOLDER", tmp_path)

    def broken(dry_run):
        raise RuntimeError("set FNO_GDRIVE_FOLDER_ID")

    monkeypatch.setattr(wiring, "build_announcements_poller", broken)
    member = wiring.LazyAnnouncementsPoller(dry_run=True)
    for mark in ("10:00", "10:15"):
        with pytest.raises(RuntimeError):
            member.after_mark(DAY, at(mark), None, "good")
    rows = (tmp_path / "errors.csv").read_text().splitlines()
    assert len(rows) == 2 and "not_built" in rows[1]  # the header and one row for the day
    assert member.paths == wiring.COMMIT_PATHS
