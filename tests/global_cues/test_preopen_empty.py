"""Story A17f criteria 1, 3, 4 and 5 through the real reader: a listed TWSE closure reads nothing (Monday 26 Oct 2026),
an empty Yahoo answer is `no session data` (not a failure) with its reason in the private row, the lines, the alert and
O10's row, a changed layout is still a failure, and every answer is archived in Drive before it is parsed. Every level
here is made up; no line, alert or repository file may hold one."""

import json
from datetime import date, datetime, time

import pytest
import requests

from fno.global_cues import preopen_cli
from fno.global_cues.market_closures import load_closures
from fno.global_cues.markets import TAIPEI, TOKYO
from fno.global_cues.preopen import CLOSED, FAILED, LIVE, NO_DATA, PreopenReader
from fno.global_cues.preopen_calendar import ClosureCalendar
from fno.global_cues.preopen_outcome import FAILURE, INCOMPLETE
from fno.global_cues.snapshot_log import SnapshotLog
from fno.global_cues.wiring import TWSE_CLOSURES_FILE
from fno.global_cues.yahoo_source import YahooBlocked, YahooChartSource, YahooGate
from fno.models import IST
from fno.storage.raw_store import LocalFolderStore
from fno.storage.row_log import CsvRowLog
from tests.global_cues.world_fakes import CannedResponse, CountingSession, utc, yahoo_chart

LEVEL = 23456.78  # made up
SETTLED = frozenset({"taiex", "nikkei225"})


def chart(zone="Asia/Taipei", **result):
    body = {"meta": {"exchangeTimezoneName": zone}, "indicators": {"quote": [{}]}, **result}
    return json.dumps({"chart": {"result": [body], "error": None}}).encode()


EMPTY_ANSWERS = {
    "an empty quote object": chart(),
    "empty arrays": chart(timestamp=[], indicators={"quote": [{"close": []}]}),
    "only null closes": chart(
        timestamp=[utc(date(2026, 10, 23), time(2, 0))], indicators={"quote": [{"close": [None]}]}
    ),
    "no quote object": chart(indicators={"quote": []}),
}
CHANGED_LAYOUTS = {
    "a quote without close": chart(timestamp=[1], indicators={"quote": [{"open": [LEVEL], "Close": [LEVEL]}]}),
    "a quote without close, no timestamps": chart(indicators={"quote": [{"open": [LEVEL]}]}),
    "more timestamps than closes": chart(timestamp=[1, 2], indicators={"quote": [{"close": []}]}),
    "a null close list": chart(timestamp=[1], indicators={"quote": [{"close": None}]}),
    "a number for timestamps": chart(timestamp=5, indicators={"quote": [{"close": [LEVEL]}]}),
    "a number for closes": chart(timestamp=[1], indicators={"quote": [{"close": 7}]}),
    "no meta": json.dumps({"chart": {"result": [{"indicators": {"quote": [{}]}}]}}).encode(),
    "no indicators.quote": json.dumps(
        {"chart": {"result": [{"meta": {"exchangeTimezoneName": "Asia/Taipei"}}]}}
    ).encode(),
    "uneven lengths": chart(timestamp=[1, 2], indicators={"quote": [{"close": [LEVEL]}]}),
}


def at(day, hour=8, minute=55):
    return lambda: datetime.combine(day, time(hour, minute), tzinfo=IST)


def taiex():
    return YahooChartSource("taiex_yahoo", "^TWII", TAIPEI, 10, True, YahooGate())


def nikkei():
    return YahooChartSource("nikkei225_yahoo", "^N225", TOKYO, 7, True, YahooGate())


def build(tmp_path, session, clock, calendar_file=TWSE_CLOSURES_FILE):
    calendars = {"taiex": ClosureCalendar("TWSE", lambda: load_closures(calendar_file, "twse_closures.csv"))}
    rows = CsvRowLog(tmp_path / "private" / "rows.csv")
    reader = PreopenReader(session, LocalFolderStore(tmp_path / "drive"), SnapshotLog(tmp_path / "log"), rows,
                           lambda index, seen: ("", ""), clock, calendars, SETTLED)  # fmt: skip
    return reader, rows


def archived(tmp_path):
    return sorted(p.name for p in (tmp_path / "drive").rglob("*.json")) if (tmp_path / "drive").exists() else []


@pytest.fixture
def desk(monkeypatch, tmp_path):
    """The command's alert, O10 log and commit, faked; returns (sent alerts, O10 log)."""
    from fno.health.capture_errors import CaptureErrorLog

    sent, errors = [], CaptureErrorLog(tmp_path / "capture_errors.csv")
    sender = type("S", (), {"send": lambda self, text: sent.append(text) or "sent"})()
    monkeypatch.setattr("fno.composition.build_alert_sender", lambda: sender)
    monkeypatch.setattr("fno.health.wiring.build_capture_error_log", lambda: errors)
    committer = type("C", (), {"commit": lambda self, what: "pre-open logs committed and pushed (1 file(s))"})()
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen_committers", lambda: [committer])
    return sent, errors


def run(monkeypatch, reader, pairs, clock):
    monkeypatch.setattr("fno.global_cues.wiring.build_preopen", lambda: (reader, pairs))
    out = []
    code = preopen_cli.cmd_preopen(out.append, now=clock, sleep=lambda s: None, is_session=lambda day: True)
    return code, out


def test_monday_26_oct_taiex_is_market_closed_with_no_request_and_the_run_is_good(monkeypatch, tmp_path, desk):
    session, clock = CountingSession(CannedResponse(200, chart())), at(date(2026, 10, 26))
    reader, rows = build(tmp_path, session, clock)
    code, out = run(monkeypatch, reader, [("taiex", taiex())], clock)
    assert (code, out[0]) == (0, "taiex: market closed (TWSE holiday: 臺灣光復暨金門古寧頭大捷紀念日)")
    assert session.calls == [] and archived(tmp_path) == [] and desk == ([], desk[1]) and desk[1].rows() == []
    (row,) = rows.rows()
    assert (row["status"], row["reason"], row["sha256"], row["level"]) == (CLOSED, "calendar: holiday", "", "")


def test_the_next_day_reads_yahoo(tmp_path):
    session = CountingSession(CannedResponse(200, chart()))
    reader, _ = build(tmp_path, session, at(date(2026, 10, 27)))
    assert reader.read(taiex(), "taiex").status == NO_DATA and len(session.calls) == 1


@pytest.mark.parametrize("name", EMPTY_ANSWERS)
def test_an_empty_answer_is_no_session_data_with_its_reason_archived_first(monkeypatch, tmp_path, desk, name):
    data, clock = EMPTY_ANSWERS[name], at(date(2026, 10, 27))
    reader, rows = build(tmp_path, CountingSession(CannedResponse(200, data)), clock)
    code, out = run(monkeypatch, reader, [("taiex", taiex())], clock)
    (row,) = rows.rows()
    sha = row["sha256"]
    assert out[0] == f"taiex: no session data (empty answer: closed unannounced or a Yahoo gap; raw {sha[:12]})"
    assert (row["status"], row["reason"]) == (NO_DATA, "empty answer: closed unannounced or a Yahoo gap")
    assert (
        archived(tmp_path) == ["085500_taiex_5m.json"] and sha in (tmp_path / "log" / "taiex_preopen.csv").read_text()
    )
    assert code == 1 and desk[0] == [
        preopen_cli.ALERT.format(what=f"taiex: no session data (empty answer; raw {sha[:12]})")
    ]
    assert [(r.kind, r.message) for r in desk[1].rows()] == [
        (INCOMPLETE, f"taiex: no session data (empty answer; raw {sha[:12]})")
    ]


@pytest.mark.parametrize("name", CHANGED_LAYOUTS)
def test_a_changed_layout_is_still_a_failure_and_its_raw_answer_is_kept(tmp_path, name):
    reader, rows = build(tmp_path, CountingSession(CannedResponse(200, CHANGED_LAYOUTS[name])), at(date(2026, 10, 27)))
    found = reader.read(taiex(), "taiex")
    (row,) = rows.rows()
    assert found.status == FAILED and found.problems[0].kind == FAILURE
    assert found.problems[0].text == f"taiex: failed (ValueError: changed layout; raw {row['sha256'][:12]})"
    assert (row["status"], row["reason"]) == (FAILED, "changed layout (ValueError)") and len(archived(tmp_path)) == 1


def test_one_close_among_nulls_is_a_level(tmp_path):
    points = [(utc(date(2026, 10, 27), time(3, 10)), None), (utc(date(2026, 10, 27), time(3, 15)), LEVEL)]
    data = yahoo_chart("Asia/Taipei", points, "^TWII")
    reader, _ = build(tmp_path, CountingSession(CannedResponse(200, data)), at(date(2026, 10, 27), 8, 50))
    assert reader.read(taiex(), "taiex").status == LIVE


def test_an_earlier_days_level_is_no_session_data_for_taiex_but_market_closed_for_a_market_without_a_calendar(
    tmp_path,
):
    yesterday = [(utc(date(2026, 10, 26), time(5, 25)), LEVEL)]
    reader, _ = build(
        tmp_path, CountingSession(CannedResponse(200, yahoo_chart("Asia/Taipei", yesterday))), at(date(2026, 10, 27))
    )
    found = reader.read(taiex(), "taiex")
    assert found.status == NO_DATA and "newest level from an earlier day" in found.lines[0]
    reader, _ = build(
        tmp_path / "b",
        CountingSession(CannedResponse(200, yahoo_chart("Asia/Tokyo", yesterday))),
        at(date(2026, 10, 27)),
    )
    assert reader.read(nikkei(), "nikkei225").status == CLOSED


def test_an_index_without_an_official_table_says_its_row_is_not_settled(tmp_path):
    reader, _ = build(tmp_path, CountingSession(CannedResponse(200, chart("Asia/Seoul"))), at(date(2026, 10, 27)))
    kospi = YahooChartSource("kospi_yahoo", "^KS11", TAIPEI, 10, False, YahooGate())
    assert reader.read(kospi, "kospi").lines[0].endswith("; no official table, not settled)")


def test_an_uncovered_year_reads_yahoo_and_alerts_a_failure(monkeypatch, tmp_path, desk):
    clock = at(date(2027, 1, 4))
    session = CountingSession(CannedResponse(200, chart()))
    reader, _ = build(tmp_path, session, clock)
    code, out = run(monkeypatch, reader, [("taiex", taiex())], clock)
    assert code == 1 and out[0] == "taiex: TWSE calendar has no 2027" and len(session.calls) == 1
    assert desk[0][0].startswith(
        "Omenix F&O pre-open Asian levels: taiex: TWSE calendar has no 2027; taiex: no session"
    )
    assert [r.kind for r in desk[1].rows()] == [FAILURE, INCOMPLETE]


def test_a_broken_calendar_fails_taiex_only_and_both_indexes_are_still_read(monkeypatch, tmp_path, desk):
    broken = tmp_path / "twse_closures.csv"
    broken.write_text("date,kind,description,source_url,sha256\n2026-01-01,covers,x,,\n2026-10-27,shut,x,,\n")
    clock = at(date(2026, 10, 27))
    data = yahoo_chart("Asia/Tokyo", [(utc(date(2026, 10, 27), time(3, 15)), LEVEL)])
    session = CountingSession(CannedResponse(200, data))
    reader, _ = build(tmp_path, session, clock, broken)
    code, out = run(monkeypatch, reader, [("taiex", taiex()), ("nikkei225", nikkei())], clock)
    assert code == 1 and len(session.calls) == 2 and out[0].startswith("taiex: calendar refused (ValueError)")
    assert desk[1].rows()[0].message.startswith("taiex: calendar refused (ValueError)")


def test_no_level_appears_in_any_line_alert_o10_row_or_committed_file(monkeypatch, tmp_path, desk):
    clock = at(date(2027, 1, 4))  # taiex: an uncovered year, so the run alerts and records
    data = yahoo_chart("Asia/Tokyo", [(utc(date(2027, 1, 4), time(3, 15)), LEVEL)])
    reader, rows = build(tmp_path, CountingSession(CannedResponse(200, data)), clock)
    code, out = run(monkeypatch, reader, [("nikkei225", nikkei()), ("taiex", taiex())], clock)
    committed = [p.read_text() for p in (tmp_path / "log").rglob("*.csv")] + [
        (tmp_path / "capture_errors.csv").read_text()
    ]
    assert code == 1 and rows.rows()[0]["level"] == repr(LEVEL)  # private, in Drive only
    assert not any(str(LEVEL) in text or "23456" in text for text in [*out, *desk[0], *committed])


def test_a_drive_failure_on_the_put_raises_before_any_parse_or_row(tmp_path):
    class Refusing(LocalFolderStore):
        def put(self, path, data):
            raise RuntimeError("Drive refused the write")

    reader, rows = build(tmp_path, CountingSession(CannedResponse(200, chart())), at(date(2026, 10, 27)))
    reader.archive = Refusing(tmp_path / "drive")
    with pytest.raises(RuntimeError):
        reader.read(taiex(), "taiex")
    assert rows.rows() == []


def test_a_block_or_a_network_error_archives_nothing_and_asks_once(tmp_path):
    for response in (CannedResponse(429, b"Too Many Requests"), CannedResponse(200, b"")):
        session = CountingSession(response)
        reader, rows = build(tmp_path, session, at(date(2026, 10, 27)))
        with pytest.raises(YahooBlocked):
            reader.read(taiex(), "taiex")
        assert len(session.calls) == 1 and archived(tmp_path) == [] and rows.rows() == []

    class Down(requests.Session):
        def get(self, url, **kwargs):
            raise requests.ConnectionError("no route")

    reader, rows = build(tmp_path, Down(), at(date(2026, 10, 27)))
    with pytest.raises(requests.ConnectionError):
        reader.read(taiex(), "taiex")
    assert archived(tmp_path) == [] and rows.rows() == []
