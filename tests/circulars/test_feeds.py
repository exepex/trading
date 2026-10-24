"""A20b: NSE's circulars API and SEBI's circulars page are read whole from today's real answers (fixtures of
15-16 Oct 2026); a refused, unreadable or re-laid-out answer is FeedFailed, never an empty list."""

from datetime import date
from pathlib import Path

import pytest
import requests

from fno.circulars.feeds import NseCircularApi, SebiCircularList
from fno.circulars.model import NSE, SEBI, FeedFailed
from fno.circulars.relevance import FnoRelevance

FIXTURES = Path(__file__).parents[1] / "fixtures" / "circulars"
NSE_JSON = (FIXTURES / "nse_circulars_15-16102026.json").read_bytes()
SEBI_HTML = (FIXTURES / "sebi_circulars_16102026.html").read_bytes()
D15, D16 = date(2026, 10, 15), date(2026, 10, 16)


class Answer:
    def __init__(self, status, body):
        self.status_code, self.content, self.text = status, body, body.decode("utf-8", "replace")

    def json(self):
        import json

        return json.loads(self.content)


class Session:
    def __init__(self, status=200, body=b"", error=None):
        self.status, self.body, self.error, self.asked = status, body, error, []

    def get(self, url, timeout):
        self.asked.append(url)
        if self.error:
            raise self.error
        return Answer(self.status, self.body)


def test_nse_lists_every_circular_of_the_dates_with_its_department():
    feed_session = Session(body=NSE_JSON)
    circulars = NseCircularApi(feed_session).fetch(D15, D16)
    assert feed_session.asked == ["https://www.nseindia.com/api/circulars?fromDate=15-10-2026&toDate=16-10-2026"]
    assert len(circulars) == 63 and {c.source for c in circulars} == {NSE}  # 70 items: 7 listed under 2 departments
    closing = next(c for c in circulars if c.number == "NSE/CMTR/76963")
    assert closing.departments == ("Futures & Options", "Capital Market (Equities) Trade")
    margin = next(c for c in circulars if c.number == "NCL/CMPT/76975")
    assert (margin.issued_on, margin.department, margin.subject) == (
        D16, "Futures & Options", "Additional Exposure Margin on Securities under MWPL",
    )  # fmt: skip
    assert margin.link == "https://nsearchives.nseindia.com/content/circulars/CMPT76975.zip"
    assert margin.filename == "CMPT76975.zip"


@pytest.mark.parametrize(
    "session",
    [Session(403, b"denied"), Session(503, b'{"data": []}'), Session(body=b"<html>blocked</html>"),
     Session(body=b'{"data": [{"sub": "x"}]}'), Session(body=b'{"data": {"a": 1}}'),
     Session(body=b'{"rows": []}'), Session(error=requests.ConnectionError("down"))],
    ids=["refused", "503 with a JSON body", "html", "item without fields", "data a dict", "no data list",
         "unreachable"],
)  # fmt: skip
def test_an_unreadable_nse_answer_fails_loudly(session):
    with pytest.raises(FeedFailed):
        NseCircularApi(session).fetch(D15, D16)


def test_sebi_lists_its_latest_circulars_with_number_date_and_title():
    circulars = SebiCircularList(Session(body=SEBI_HTML)).fetch(D15, D16)
    assert len(circulars) == 25 and {c.source for c in circulars} == {SEBI}
    first = circulars[0]
    assert (first.issued_on, first.number) == (D15, "105293")
    assert first.subject.startswith("Review of certain aspects of the Closing Auction Session")


@pytest.mark.parametrize("session", [Session(body=b"<html>no table</html>"), Session(500, b"")], ids=["layout", "500"])
def test_an_unreadable_sebi_page_fails_loudly(session):
    with pytest.raises(FeedFailed):
        SebiCircularList(session).fetch(D15, D16)


def test_relevance_keeps_fno_department_and_fno_subjects_only():
    nse = NseCircularApi(Session(body=NSE_JSON)).fetch(D15, D16)
    relevant = {c.number for c in nse if FnoRelevance()(c)}
    assert relevant == {"NCL/CMPT/76975", "NSE/CMTR/76963", "NCL/CMPT/76951", "NSE/FAOP/76921"}  # the 4 F&O ones
    sebi = SebiCircularList(Session(body=SEBI_HTML)).fetch(D15, D16)
    assert FnoRelevance()(sebi[0])  # "... settlement methodology for derivatives contracts"


def test_a_file_the_publisher_does_not_serve_is_feedfailed():
    circular = NseCircularApi(Session(body=NSE_JSON)).fetch(D15, D16)[0]
    with pytest.raises(FeedFailed, match="HTTP 404"):
        NseCircularApi(Session(404, b"")).download(circular)


def test_a_sebi_page_with_one_row_in_another_layout_fails_whole():
    broken = SEBI_HTML.replace(b"<td>Oct 15, 2026</td>", b"<td>15-10-2026</td>", 1)
    with pytest.raises(FeedFailed, match="24 of 25 rows readable"):
        SebiCircularList(Session(body=broken)).fetch(D15, D16)
