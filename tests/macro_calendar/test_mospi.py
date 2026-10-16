"""A20c criterion 10: MOSPI's Advance Release Calendar for FY 2026-27 (text extracted by pinned pypdf 5.4.0 from
ARC_2026_27_Sept_2026.pdf, 16 Oct 2026) gives 12 CPI, 12 IIP and 5 GDP planned dates; a "Released on" note is not a
planned date; 11 or 13 CPI dates, no title, a PDF without text and a non-PDF are refused."""

import json
from datetime import date
from pathlib import Path

import pytest

from fno.macro_calendar.model import INDIA_CPI, INDIA_GDP, INDIA_IIP, CalendarFailed
from fno.macro_calendar.mospi import FILE_BASE, LATEST_URL, MospiArcCalendar, pdf_text, read_arc
from tests.macro_calendar.pdf_fixture import text_pdf

FIXTURES = Path(__file__).parents[1] / "fixtures" / "macro_calendar"
ARC = (FIXTURES / "ARC_2026_27_Sept_2026.txt").read_text()
LATEST = (FIXTURES / "mospi_latest_16102026.json").read_bytes()


def days(dates, kind):
    return [d.day for d in dates if d.kind == kind]


def test_the_real_calendar_gives_12_cpi_12_iip_and_5_gdp_dates():
    dates = read_arc(ARC, "u")
    cpi, iip, gdp = days(dates, INDIA_CPI), days(dates, INDIA_IIP), days(dates, INDIA_GDP)
    assert len(cpi) == 12 and cpi[0] == date(2026, 4, 12) and cpi[-1] == date(2027, 3, 12)
    assert len(iip) == 12 and date(2026, 6, 1) in iip and iip[-1] == date(2027, 3, 28)
    assert gdp == [date(2026, 6, 5), date(2026, 8, 31), date(2026, 11, 30), date(2027, 1, 7), date(2027, 2, 26)]


def test_a_released_on_note_is_not_a_planned_date():
    assert date(2026, 4, 13) not in days(read_arc(ARC, "u"), INDIA_CPI)  # "Released on 13th April, 2026"


def test_eleven_or_thirteen_cpi_dates_are_a_layout_change():
    with pytest.raises(CalendarFailed, match="india_cpi 11"):
        read_arc(ARC.replace("12th May All India Consumer Price Index", "12th May All India Something", 1), "u")
    with pytest.raises(CalendarFailed, match="india_cpi 13"):
        read_arc(ARC + "\n12th March All India Consumer Price Index (CPI)\n", "u")


def test_a_text_without_the_calendar_title_is_refused():
    with pytest.raises(CalendarFailed, match="no 'ADVANCE RELEASE CALENDAR"):
        read_arc(ARC.replace("ADVANCE RELEASE CALENDAR (2026-27)", "CALENDAR"), "u")


def test_pdf_text_reads_a_pdf_and_refuses_a_non_pdf_and_an_empty_one():
    assert "Consumer Price Index" in pdf_text(text_pdf(["12th April All India Consumer Price Index"]), "u")
    with pytest.raises(CalendarFailed, match="not a readable PDF"):
        pdf_text(b"<html>not a pdf</html>", "u")
    with pytest.raises(CalendarFailed, match="no text"):
        pdf_text(text_pdf([]), "u")


class Answer:
    def __init__(self, status, content):
        self.status_code, self.content = status, content

    def json(self):
        return json.loads(self.content)


class Session:
    def __init__(self, answers):
        self.answers, self.asked = answers, []

    def get(self, url, timeout):
        self.asked.append(url)
        return self.answers[url]


def test_the_adapter_follows_mospi_s_latest_calendar_and_refuses_a_bad_answer():
    pdf_url = FILE_BASE + json.loads(LATEST)["data"]["url"]
    lines = ["ADVANCE RELEASE CALENDAR (2026-27)"] + [
        f"12th {m} All India Consumer Price Index 28th {m} All India Index of Industrial Production"
        for m in ("April", "May", "June", "July", "August", "September", "October", "November", "December",
                  "January", "February", "March")
    ]  # fmt: skip
    lines += [f"{d} Quarterly Estimates of GDP" for d in ("5th June", "31st August", "30th November", "26th February")]
    session = Session({LATEST_URL: Answer(200, LATEST), pdf_url: Answer(200, text_pdf(lines))})
    calendar = MospiArcCalendar(session).fetch(date(2026, 10, 16))
    assert len(calendar.dates) == 28 and calendar.extension == "pdf" and session.asked == [LATEST_URL, pdf_url]
    with pytest.raises(CalendarFailed, match="HTTP 403"):
        MospiArcCalendar(Session({LATEST_URL: Answer(403, b"")})).fetch(date(2026, 10, 16))
    not_pdf = json.dumps({"data": {"url": "uploads/x.docx"}}).encode()
    with pytest.raises(CalendarFailed, match="not a PDF"):
        MospiArcCalendar(Session({LATEST_URL: Answer(200, not_pdf)})).fetch(date(2026, 10, 16))
