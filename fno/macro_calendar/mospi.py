"""MOSPI's Advance Release Calendar (story A20c): the latest PDF, found through MOSPI's API, read with `pypdf`. Each
release row gives its planned date (e.g. "12th April") and then its title; a date is classed by the titles that follow
it up to the next date. A financial year's calendar must hold 12 CPI and 12 IIP dates (a "Released on" note's date has
no title after it); another count is a layout change."""

from __future__ import annotations

import io
import re
from datetime import date

import requests
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .http import get_ok
from .model import INDIA_CPI, INDIA_GDP, INDIA_IIP, MOSPI, Calendar, CalendarFailed, ReleaseDate

LATEST_URL = "https://www.mospi.gov.in/api/documents/get-latest-release-calender"
FILE_BASE = "https://www.mospi.gov.in/"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
PLANNED = re.compile(r"(?<![A-Za-z])(\d{1,2})\s*(?:st|nd|rd|th)\s*(" + "|".join(MONTHS) + r")[a-z]*")
FINANCIAL_YEAR = re.compile(r"ADVANCE RELEASE CALENDAR \((\d{4})-(\d{2})\)")
TITLES = {
    INDIA_CPI: re.compile(r"Consumer\s+Price\s+Index"),
    INDIA_IIP: re.compile(r"Index\s+of\s+Industrial\s+Production"),
    INDIA_GDP: re.compile(r"Gross\s+Domestic\s+Product|Estimates\s+of\s+GDP"),
}
EXPECTED = {INDIA_CPI: 12, INDIA_IIP: 12}  # monthly releases: one a month over the financial year
MIN_GDP = 4  # at least the four quarterly estimates


def read_arc(text: str, source_url: str) -> tuple[ReleaseDate, ...]:
    """Every CPI, IIP and GDP planned date of one financial year's calendar text; CalendarFailed on a layout change."""
    year = FINANCIAL_YEAR.search(text)
    if year is None:
        raise CalendarFailed(f"{source_url}: no 'ADVANCE RELEASE CALENDAR (YYYY-YY)' title")
    first_year = int(year.group(1))
    planned = list(PLANNED.finditer(text))
    dates = []
    for i, match in enumerate(planned):
        end = planned[i + 1].start() if i + 1 < len(planned) else len(text)
        title = text[match.end() : end]
        month = MONTHS.index(match.group(2)) + 1
        day = date(first_year if month >= 4 else first_year + 1, month, int(match.group(1)))
        dates += [ReleaseDate(kind, day, source_url) for kind, pattern in TITLES.items() if pattern.search(title)]
    _check_counts(dates, source_url)
    return tuple(sorted(set(dates), key=lambda d: (d.day, d.kind)))


def _check_counts(dates: list[ReleaseDate], source_url: str) -> None:
    counts = {kind: sum(d.kind == kind for d in dates) for kind in TITLES}
    wrong = [f"{kind} {counts[kind]} (expected {n})" for kind, n in EXPECTED.items() if counts[kind] != n]
    if counts[INDIA_GDP] < MIN_GDP:
        wrong.append(f"{INDIA_GDP} {counts[INDIA_GDP]} (expected at least {MIN_GDP})")
    if wrong:
        raise CalendarFailed(f"{source_url}: layout changed? {', '.join(wrong)}")


def pdf_text(data: bytes, source_url: str) -> str:
    try:
        text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    except (PdfReadError, ValueError, OSError) as exc:
        raise CalendarFailed(f"{source_url}: not a readable PDF ({type(exc).__name__})") from exc
    if not text.strip():
        raise CalendarFailed(f"{source_url}: the PDF holds no text")
    return text


class MospiArcCalendar:
    source = MOSPI

    def __init__(self, session: requests.Session):
        self.session = session

    def fetch(self, today: date) -> Calendar:
        url = FILE_BASE + self._latest_path()
        data = get_ok(self.session, url).content
        return Calendar(read_arc(pdf_text(data, url), url), data, "pdf")

    def _latest_path(self) -> str:
        try:
            path = get_ok(self.session, LATEST_URL).json()["data"]["url"]
        except (ValueError, KeyError, TypeError) as exc:
            raise CalendarFailed(f"{LATEST_URL}: not MOSPI's latest-calendar answer ({type(exc).__name__})") from exc
        if not isinstance(path, str) or not path.endswith(".pdf"):
            raise CalendarFailed(f"{LATEST_URL}: the latest calendar is not a PDF ({path!r})")
        return path
