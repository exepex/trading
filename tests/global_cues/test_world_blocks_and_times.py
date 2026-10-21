"""Story A17e, criteria 8 and 4: a Yahoo block stops that cue with exactly one request and no other way tried, while
the run's other cues still run; each market's close is known at, never before, its boundary in IST."""

from datetime import date, datetime, timedelta

import pytest

from fno.global_cues.as_of import OPEN, value_for
from fno.global_cues.collector import CueCollector
from fno.global_cues.job import GlobalCueJob
from fno.global_cues.markets import (
    EURO_STOXX,
    FRANKFURT,
    HONG_KONG,
    LONDON,
    SEOUL,
    SHANGHAI,
    SINGAPORE,
    SYDNEY,
    TAIPEI,
    TOKYO,
)
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.yahoo_source import YahooBlocked, YahooChartSource
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from tests.global_cues.fakes import FakeSource, csv_table, fake_file
from tests.global_cues.world_fakes import CannedResponse, CountingSession

CONSENT = b'<html><form action="https://consent.yahoo.com/v2/collectConsent">Before you continue</form></html>'
CAPTCHA = b"<!doctype html><html><title>Are you a robot?</title><div class='captcha'></div></html>"
BLOCKS = [
    CannedResponse(401, b'{"finance":{"error":"Unauthorized"}}'),
    CannedResponse(403, b"Forbidden"),
    CannedResponse(429, b"Too Many Requests"),
    CannedResponse(302, b"", "https://guce.yahoo.com/consent"),
    CannedResponse(200, CONSENT),
    CannedResponse(200, CAPTCHA),
]


def nikkei_yahoo():
    return YahooChartSource("nikkei225_yahoo", "^N225", TOKYO, 7, True)


@pytest.mark.parametrize("answer", BLOCKS, ids=["401", "403", "429", "redirect", "consent", "captcha"])
def test_a_block_stops_the_cue_after_one_plain_request_with_nothing_changed(answer):
    session, source = CountingSession(answer), nikkei_yahoo()
    session.headers["User-Agent"] = "fno-desk test"
    request = source.requests(date(2026, 10, 1), date(2026, 10, 21))[0]
    with pytest.raises(YahooBlocked, match="never retried another way"):
        source.download(session, request)
    assert len(session.calls) == 1  # no retry
    url, headers, kwargs = session.calls[0]
    assert url == request.url and headers["User-Agent"] == "fno-desk test" and "Cookie" not in headers
    assert kwargs["allow_redirects"] is False and "cookies" not in kwargs and "proxies" not in kwargs


def test_a_blocked_cue_writes_nothing_and_the_other_cues_of_the_run_still_run(tmp_path):
    class Blocked(YahooChartSource):
        def download(self, session, request):
            return super().download(CountingSession(BLOCKS[0]), request)

    blocked = Blocked("nikkei225_yahoo", "^N225", TOKYO, 7, True)
    other = FakeSource({"a.csv": fake_file(("2026-10-20", 1.0), ("2026-10-21", 2.0))})
    tables = {s.cue: csv_table(tmp_path / "t", s.cue, lambda d: d) for s in (blocked, other)}
    collector = CueCollector(None, LocalFolderStore(tmp_path / "drive"), SnapshotLog(tmp_path / "log"),
                             lambda: datetime(2026, 10, 22, 5, 30, tzinfo=IST))  # fmt: skip

    class NoChecks:
        def write(self):
            return []

    lines, ok = GlobalCueJob(collector, tables, NoChecks()).run([blocked, other], date(2026, 10, 1), date(2026, 10, 21))
    assert not ok and lines[0].startswith("nikkei225_yahoo: FAILED, download failed") and "HTTP 401" in lines[0]
    assert lines[1].startswith("fake: 2 dates added") and tables["nikkei225_yahoo"].rows() == []
    assert not list((tmp_path / "drive").rglob("*n225*"))  # nothing archived for the blocked cue


def test_a_good_answer_passes_the_block_rule():
    body = b'{"chart":{"result":[]}}'
    request = nikkei_yahoo().requests(date(2026, 10, 1), date(2026, 10, 2))[0]
    assert nikkei_yahoo().download(CountingSession(CannedResponse(200, body)), request) == body


BOUNDARIES = [  # (market, a value date, its close in IST)
    (TOKYO, date(2026, 10, 21), datetime(2026, 10, 21, 12, 0, tzinfo=IST)),
    (SEOUL, date(2026, 10, 21), datetime(2026, 10, 21, 12, 0, tzinfo=IST)),
    (SHANGHAI, date(2026, 10, 21), datetime(2026, 10, 21, 12, 30, tzinfo=IST)),
    (TAIPEI, date(2026, 10, 21), datetime(2026, 10, 21, 11, 0, tzinfo=IST)),
    (HONG_KONG, date(2026, 10, 21), datetime(2026, 10, 21, 13, 40, tzinfo=IST)),
    (SINGAPORE, date(2026, 10, 21), datetime(2026, 10, 21, 14, 30, tzinfo=IST)),
    (SYDNEY, date(2026, 10, 21), datetime(2026, 10, 21, 10, 40, tzinfo=IST)),  # Australian summer time (from 4 Oct)
    (SYDNEY, date(2026, 10, 2), datetime(2026, 10, 2, 11, 40, tzinfo=IST)),  # winter, two days before the change
    (SYDNEY, date(2026, 4, 6), datetime(2026, 4, 6, 11, 40, tzinfo=IST)),  # winter again from 5 Apr
    (LONDON, date(2026, 10, 21), datetime(2026, 10, 21, 21, 5, tzinfo=IST)),  # British summer time until 25 Oct
    (LONDON, date(2026, 10, 26), datetime(2026, 10, 26, 22, 5, tzinfo=IST)),
    (FRANKFURT, date(2026, 10, 21), datetime(2026, 10, 21, 21, 5, tzinfo=IST)),
    (FRANKFURT, date(2026, 3, 27), datetime(2026, 3, 27, 22, 5, tzinfo=IST)),  # before the 29 Mar change
    (EURO_STOXX, date(2026, 10, 26), datetime(2026, 10, 26, 22, 20, tzinfo=IST)),
]


@pytest.mark.parametrize(("market", "day", "close"), BOUNDARIES)
def test_a_close_is_known_at_its_boundary_and_not_a_minute_before(market, day, close):
    assert market.available_at(day) == close
    row = [{"value_date": day.isoformat(), "first_seen_at": close.isoformat(), "value": "1"}]
    for cutoff, usable in ((close - timedelta(minutes=1), False), (close, False), (close + timedelta(minutes=1), True)):
        found = value_for(row, cutoff.date(), cutoff.time(), False, market.available_at)
        assert (found is not None) is usable, (cutoff, usable)  # known strictly after the close


def test_a_same_day_asian_close_is_never_known_at_the_open_and_the_previous_days_is():
    rows = [{"value_date": d, "first_seen_at": "", "value": "1"} for d in ("2026-10-20", "2026-10-21")]
    for market in (TOKYO, SEOUL, SHANGHAI, TAIPEI, HONG_KONG, SINGAPORE, SYDNEY):
        found = value_for(rows, date(2026, 10, 21), OPEN, False, market.available_at)
        assert found["value_date"] == "2026-10-20"
    assert value_for([], date(2026, 10, 21), OPEN, False, TOKYO.available_at) is None  # empty: no label at all
