"""Story A7: the 3 pm quote recorder asks NSE's session calendar "is today a session", never the weekday."""

from datetime import date, datetime

import pytest

from fno import composition
from fno.alerts.sender import AlertSender
from fno.models import IST
from fno.quotes.cli import record_today
from fno.quotes.recorder import MUHURAT_ONLY, NO_SAME_DAY_TRADES, QuoteSnapshotRecorder
from fno.research_data.calendar import CalendarError, CsvSessionCalendar, SessionCalendar
from fno.storage.raw_store import LocalFolderStore
from fno.storage.wiring import build_session_calendar

from .test_quote_recorder import Clock, FakeProvider, files
from .test_recorder_baseline import BASELINE, SCENARIOS, _files

SOURCE = "https://nsearchives.nseindia.com/content/circulars/FAOP71777.pdf"
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n"
    f"2026-10-17,special,test Saturday session,{SOURCE}\n"
    f"2026-10-20,holiday,Dussehra,{SOURCE}\n"
    f"2026-11-08,muhurat,Diwali muhurat Sun evening,{SOURCE}\n"
)  # covers 2026 only
SATURDAY = datetime(2026, 10, 17, 14, 55, tzinfo=IST)
TUESDAY = datetime(2026, 10, 13, 14, 55, tzinfo=IST)


class NoCalls:
    """A provider that fails the test if the recorder asks it anything: closed days must not reach the provider."""

    name = "none"

    def __getattr__(self, attr):
        raise AssertionError(f"the recorder called {attr} on a closed day")


class Alerts(AlertSender):
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


def recorder(folder, provider, start, calendar: SessionCalendar = CALENDAR):
    clock = Clock(start)
    return QuoteSnapshotRecorder(provider, LocalFolderStore(folder), clock.now, clock.sleep, calendar=calendar)


def test_a_special_saturday_session_is_recorded_with_a_canonical_snapshot(tmp_path):
    rec = recorder(tmp_path, FakeProvider(traded=datetime(2026, 10, 17, 14, 58, tzinfo=IST)), SATURDAY)
    result = rec.record()
    assert result.status == "recorded" and result.complete and result.rows == 12
    assert rec.canonical(SATURDAY.date()) == result.snapshot_id


def test_a_weekday_holiday_records_nothing_and_never_asks_the_provider(tmp_path):
    rec = recorder(tmp_path, NoCalls(), datetime(2026, 10, 20, 14, 55, tzinfo=IST))
    result = rec.record()
    assert (result.status, result.reason) == ("not a trading day", "") and files(tmp_path) == []


def test_an_ordinary_weekend_day_is_closed_and_a_muhurat_day_says_why(tmp_path):
    assert recorder(tmp_path, NoCalls(), datetime(2026, 10, 18, 14, 55, tzinfo=IST)).record().status == (
        "not a trading day"
    )
    muhurat = recorder(tmp_path, NoCalls(), datetime(2026, 11, 8, 14, 55, tzinfo=IST)).record()
    assert (muhurat.status, muhurat.reason) == ("not a trading day", MUHURAT_ONLY) and files(tmp_path) == []


def test_a_session_without_same_day_trades_is_kept_incomplete_retried_and_ends_none(tmp_path):
    yesterday = datetime(2026, 10, 12, 15, 29, tzinfo=IST)
    rec = recorder(tmp_path, FakeProvider(traded=yesterday), TUESDAY)
    result = rec.record()
    assert (result.status, result.complete, result.reason) == ("recorded", False, NO_SAME_DAY_TRADES)
    names = files(tmp_path)
    assert sum(n.endswith(".csv") for n in names) > 1  # every attempt in the window is kept
    assert all(NO_SAME_DAY_TRADES in p.read_text() for p in tmp_path.rglob("*.meta.json"))
    assert rec.canonical(TUESDAY.date()) == "none"  # the day is not skipped: its canonical says none


def test_the_command_exits_non_zero_and_alerts_on_the_cross_check(tmp_path, capsys):
    rec = recorder(tmp_path, FakeProvider(traded=datetime(2026, 10, 12, 15, 29, tzinfo=IST)), TUESDAY)
    alerts = Alerts()
    assert record_today(lambda: rec, alerts, False, "nse_sessions.csv") == 1
    assert len(alerts.sent) == 1 and NO_SAME_DAY_TRADES in alerts.sent[0]
    assert NO_SAME_DAY_TRADES in capsys.readouterr().out
    clock = Clock(datetime(2026, 10, 13, 20, 0, tzinfo=IST))  # a test attempt outside the window is no excuse either
    late = QuoteSnapshotRecorder(
        FakeProvider(traded=datetime(2026, 10, 12, 15, 29, tzinfo=IST)), LocalFolderStore(tmp_path / "late"),
        clock.now, clock.sleep, calendar=CALENDAR,
    )  # fmt: skip
    assert record_today(lambda: late, Alerts(), True, "nse_sessions.csv") == 1


def test_a_day_outside_the_calendar_fails_loudly_and_says_what_to_add(tmp_path, capsys):
    rec = recorder(tmp_path, NoCalls(), datetime(2027, 1, 1, 14, 55, tzinfo=IST))
    with pytest.raises(CalendarError, match="add every row of NSE's 2027 holiday circular"):
        rec.record()
    alerts = Alerts()
    assert record_today(lambda: rec, alerts, False, "research/data/calendar/nse_sessions.csv") == 1
    out = capsys.readouterr().out
    assert "nothing recorded" in out and "NSE's 2027 holiday circular" in out and "nse_sessions.csv" in out
    assert len(alerts.sent) == 1 and files(tmp_path) == []


def test_an_invalid_calendar_file_also_stops_the_command(capsys):
    def broken():
        raise CalendarError("line 3: every row needs an https source link")

    assert record_today(broken, Alerts(), False, "nse_sessions.csv") == 1
    assert "source link" in capsys.readouterr().out


@pytest.mark.parametrize(
    "start, traded, outside_window, code",
    [
        (TUESDAY, datetime(2026, 10, 13, 14, 58, tzinfo=IST), False, 0),  # recorded, complete
        (datetime(2026, 10, 20, 14, 55, tzinfo=IST), None, False, 0),  # holiday
        (datetime(2026, 10, 13, 9, 30, tzinfo=IST), None, False, 1),  # too early
    ],
)
def test_other_exit_codes_are_unchanged(tmp_path, start, traded, outside_window, code):
    rec = recorder(tmp_path, FakeProvider(traded=traded) if traded else NoCalls(), start)
    assert record_today(lambda: rec, Alerts(), outside_window, "nse_sessions.csv") == code


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_with_the_real_calendar_the_baseline_bytes_are_unchanged(tmp_path, name):
    make_provider, start, fallback = SCENARIOS[name]
    clock = Clock(start)
    QuoteSnapshotRecorder(
        make_provider(), LocalFolderStore(tmp_path), clock.now, clock.sleep, fallback=fallback,
        calendar=build_session_calendar(),
    ).record()  # fmt: skip
    assert _files(tmp_path) == _files(BASELINE / name)


def test_the_app_builds_the_recorder_with_the_repository_calendar(monkeypatch):
    monkeypatch.setattr(composition, "get_provider", lambda name, cfg: FakeProvider())
    calendar = composition.build_quote_recorder({}).calendar
    assert calendar.session_kind(date(2025, 2, 1)) == "special"  # Saturday Union Budget session
    assert calendar.session_kind(date(2026, 2, 1)) == "special"  # Sunday Union Budget session
    assert not calendar.is_session(date(2026, 10, 20))  # Dussehra, a Tuesday
    assert calendar.is_session(date(2026, 10, 13))  # the first real run
    assert calendar.calendar_sha256() == build_session_calendar().calendar_sha256()
