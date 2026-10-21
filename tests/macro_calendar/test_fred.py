"""A20c, US part: FRED's release-dates answers (documented format: release_dates rows of release_id and date) give the
CPI (release 10) and payrolls (release 50) dates from the run's year on; the key never appears in a message or a kept
document; a refused, unreadable or past-only answer fails; no key means "not configured"."""

import json
from datetime import date

import pytest

from fno.macro_calendar.fred import RELEASES, FredReleaseCalendar
from fno.macro_calendar.model import US_CPI, US_PAYROLLS, CalendarFailed
from fno.macro_calendar.unconfigured import UnconfiguredCalendar
from fno.macro_calendar.wiring import build_macro_calendar_job

KEY = "abcdef0123456789abcdef0123456789"
TODAY = date(2026, 10, 21)


def answer(release_id, days):
    rows = [{"release_id": release_id, "date": d} for d in days]
    return {"realtime_start": "2026-10-21", "order_by": "release_date", "sort_order": "desc", "release_dates": rows}


class Answer:
    def __init__(self, status, body):
        self.status_code, self.content = status, json.dumps(body).encode()

    def json(self):
        return json.loads(self.content)


class Session:
    def __init__(self, bodies, status=200):
        self.bodies, self.status, self.asked = bodies, status, []

    def get(self, url, params, timeout):
        self.asked.append(params)
        return Answer(self.status, self.bodies[params["release_id"]])


GOOD = {10: answer(10, ["2026-11-12", "2026-10-14", "2025-12-10"]), 50: answer(50, ["2026-11-06", "2026-10-02"])}


def test_cpi_and_payrolls_dates_from_the_run_s_year_on():
    calendar = FredReleaseCalendar(Session(GOOD), KEY).fetch(TODAY)
    days = {(d.kind, d.day) for d in calendar.dates}
    assert days == {(US_CPI, date(2026, 10, 14)), (US_CPI, date(2026, 11, 12)), (US_PAYROLLS, date(2026, 10, 2)),
                    (US_PAYROLLS, date(2026, 11, 6))}  # fmt: skip
    assert calendar.period == (date(2026, 1, 1), date(2026, 11, 12)) and RELEASES == {US_CPI: 10, US_PAYROLLS: 50}
    assert all("fred.stlouisfed.org/releases/" in d.source_url and KEY not in d.source_url for d in calendar.dates)


def test_the_key_is_asked_for_scheduled_dates_and_never_kept():
    echoing = {release: {**body, "url": f"?api_key={KEY}"} for release, body in GOOD.items()}  # an answer echoing it
    session = Session(echoing)
    calendar = FredReleaseCalendar(session, KEY).fetch(TODAY)
    assert session.asked[0]["include_release_dates_with_no_data"] == "true" and session.asked[0]["api_key"] == KEY
    assert KEY.encode() not in calendar.document


@pytest.mark.parametrize(
    "session",
    [Session(GOOD, status=400), Session({10: {"error_message": "Bad Request"}, 50: GOOD[50]}),
     Session({10: answer(10, ["2026-10-14"]), 50: GOOD[50]})],
    ids=["refused", "not the answer", "nothing scheduled after today"],
)  # fmt: skip
def test_a_bad_answer_fails_and_never_names_the_key(session):
    with pytest.raises(CalendarFailed) as failed:
        FredReleaseCalendar(session, KEY).fetch(TODAY)
    assert KEY not in str(failed.value) and "FRED release 10" in str(failed.value)


def test_no_key_means_not_configured_and_a_key_means_fred(monkeypatch):
    def calendars(env):
        return build_macro_calendar_job(env).capture.calendars

    monkeypatch.setattr("fno.macro_calendar.wiring.build_data_store", lambda *a, **k: None)
    assert isinstance(calendars({})[-1], UnconfiguredCalendar)
    assert isinstance(calendars({"FNO_FRED_API_KEY": KEY})[-1], FredReleaseCalendar)
