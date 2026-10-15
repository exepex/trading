"""Story A17: each source reads its publisher's real layout, refuses anything else, and asks for the right files."""

from datetime import date

import pytest

from fno.global_cues.other_sources import RBI_ARCHIVE, EiaBrentSource, FbilUsdInrSource, RbiUsdInrSource
from fno.global_cues.source import CueRequest, CueValue
from fno.global_cues.treasury_source import TreasuryTenYearSource
from tests.global_cues.fakes import EIA, RBI, TREASURY, fbil

ERROR_PAGE = b"<html><title>Service Temporarily Unavailable</title></html>"


def values(*pairs):
    return [CueValue(date.fromisoformat(d), v) for d, v in pairs]


def test_treasury_gives_the_10_year_and_leaves_a_blank_day_out():
    assert TreasuryTenYearSource().parse(TREASURY) == values(("2026-10-09", 5.25), ("2026-10-14", 5.19))
    assert [r.name for r in TreasuryTenYearSource().requests(date(2025, 12, 1), date(2026, 1, 5))] == [
        "daily-treasury-rates_2025.csv",
        "daily-treasury-rates_2026.csv",
    ]


def test_eia_gives_brent_by_weekday_across_a_year_end_and_leaves_blanks_out():
    year_end = (("2025-12-29", 61.1), ("2025-12-30", 62.0), ("2026-01-02", 60.75))
    assert EiaBrentSource().parse(EIA) == values(*year_end, ("2026-10-05", 125.51), ("2026-10-06", 125.44))


def test_rbi_gives_the_reference_rate():
    assert RbiUsdInrSource().parse(RBI) == values(("2026-10-13", 95.2477), ("2026-10-14", 95.0317))


def test_fbil_gives_only_the_usd_rate():
    assert FbilUsdInrSource().parse(fbil(("2026-10-07", 96.623))) == values(("2026-10-07", 96.623))


class FormSession:
    """Answers RBI's form page, then records the post."""

    def __init__(self):
        self.posted = None

    def get(self, url, timeout):
        return Answer(RBI)

    def post(self, url, data, timeout):
        self.posted = (url, data)
        return Answer(RBI)


class Answer:
    def __init__(self, content):
        self.content, self.text = content, content.decode()

    def raise_for_status(self):
        return None


def test_rbi_posts_its_form_with_the_hidden_fields_and_the_dates():
    (request,) = RbiUsdInrSource().requests(date(2007, 1, 1), date(2026, 10, 14))
    session = FormSession()
    assert RbiUsdInrSource().download(session, request) == RBI
    url, form = session.posted
    assert url == RBI_ARCHIVE and form["__VIEWSTATE"] == "abc"
    assert (form["txtFromDate"], form["txtToDate"], form["chkUSD"]) == ("01/01/2007", "14/10/2026", "on")


@pytest.mark.parametrize("source", [TreasuryTenYearSource(), EiaBrentSource(), RbiUsdInrSource()])
def test_an_error_page_is_refused(source):
    with pytest.raises(ValueError):
        source.parse(ERROR_PAGE)


def test_fbil_refuses_an_error_answer_and_a_zero_rate():
    with pytest.raises(ValueError):
        FbilUsdInrSource().parse(b'{"cause": null, "stackTrace": []}')
    with pytest.raises(ValueError, match="not a positive number"):
        FbilUsdInrSource().parse(fbil(("2026-10-07", 0)))


def test_every_request_names_a_file_and_an_https_url():
    for source in (TreasuryTenYearSource(), EiaBrentSource(), FbilUsdInrSource()):
        for request in source.requests(date(2026, 9, 1), date(2026, 10, 14)):
            assert isinstance(request, CueRequest) and request.url.startswith("https://") and request.name
