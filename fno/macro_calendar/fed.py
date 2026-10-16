"""The Fed's FOMC calendar page (story A20c): one panel per year, each scheduled meeting a month and a day range
("27-28", "17-18*" with projections, "30-1" across "Apr/May"); the decision day is the range's last day. Entries
that are not a day range (a notation vote, a call) are not scheduled decisions. A year from the run's year on must
hold 8 decision days; any other count is a layout change. Dates are US dates: the statement comes at 2 pm New York
time, about 23:30-00:30 IST, so NSE first trades on it the next IST session."""

from __future__ import annotations

import re
from datetime import date

import requests

from .http import get_ok
from .model import FED, US_FOMC, Calendar, CalendarFailed, ReleaseDate

URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
YEAR_PANEL = re.compile(r'<h4><a id="\d+">(\d{4}) FOMC Meetings</a></h4>')
MEETING = re.compile(
    r'fomc-meeting__month[^>]*><strong>([^<]*)</strong></div>\s*<div class="fomc-meeting__date[^>]*>([^<]*)</div>'
)
DAY_RANGE = re.compile(r"^\d{1,2}-(\d{1,2})\*?$")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December")  # fmt: skip
MEETINGS_A_YEAR = 8


def read_fomc(page: str, today: date) -> tuple[ReleaseDate, ...]:
    """The decision days of every year from `today`'s year on; CalendarFailed on a layout change."""
    panels = list(YEAR_PANEL.finditer(page))
    years = [int(p.group(1)) for p in panels]
    if today.year not in years:
        raise CalendarFailed(f"{URL}: no panel for {today.year}")
    dates = []
    for i, panel in enumerate(panels):
        year = int(panel.group(1))
        if year < today.year:
            continue
        body = page[panel.end() : panels[i + 1].start() if i + 1 < len(panels) else len(page)]
        days = [_decision_day(year, month, span) for month, span in MEETING.findall(body) if DAY_RANGE.match(span)]
        if len(days) != MEETINGS_A_YEAR:
            raise CalendarFailed(f"{URL}: {year} has {len(days)} scheduled meetings (expected {MEETINGS_A_YEAR})")
        dates += [ReleaseDate(US_FOMC, day, URL) for day in days]
    return tuple(sorted(dates, key=lambda d: d.day))


def _decision_day(year: int, month: str, span: str) -> date:
    last_month = month.split("/")[-1]
    names = [m for m in MONTHS if m.startswith(last_month)]
    if len(names) != 1:
        raise CalendarFailed(f"{URL}: unknown month {month!r}")
    return date(year, MONTHS.index(names[0]) + 1, int(DAY_RANGE.match(span).group(1)))


class FedFomcCalendar:
    source = FED

    def __init__(self, session: requests.Session):
        self.session = session

    def fetch(self, today: date) -> Calendar:
        data = get_ok(self.session, URL).content
        dates = read_fomc(data.decode("utf-8", "replace"), today)
        return Calendar(dates, data, "html", (date(today.year, 1, 1), date(dates[-1].day.year, 12, 31)))
