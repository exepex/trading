"""Story A15: NSE's month file and its archive path; a file that is not a whole, clean month is refused."""

from datetime import date

import pytest

from fno.vix_history.month_file import NSE_ROW_CAP, NseVixJsonReader, VixDay
from fno.vix_history.source import NseVixHistorySource, last_complete_month, month_end, months_between
from tests.vix_history.nse_vix import july_2010, month_file, nse_row

JULY = date(2010, 7, 1)
READER = NseVixJsonReader()


def test_a_month_has_one_path_and_nses_url_for_the_whole_month():
    path = NseVixHistorySource.path_for(date(2010, 7, 19))
    assert path == "nse/indices/india-vix-history/2010/07/india-vix_201007.json"
    assert NseVixHistorySource.day_for_path(path) == JULY
    assert NseVixHistorySource.url_for(path) == (
        "https://www.nseindia.com/api/historicalOR/vixhistory?from=01-07-2010&to=31-07-2010"
    )


def test_months_run_from_the_first_month_and_a_running_month_is_never_complete():
    assert months_between(date(2010, 11, 5), date(2011, 2, 1)) == [
        date(2010, 11, 1),
        date(2010, 12, 1),
        date(2011, 1, 1),
        date(2011, 2, 1),
    ]
    assert last_complete_month(date(2026, 10, 15)) == date(2026, 9, 1)
    assert last_complete_month(date(2026, 1, 1)) == date(2025, 12, 1)
    assert month_end(date(2024, 2, 1)) == date(2024, 2, 29)
    assert NseVixHistorySource.first_day == JULY  # NSE serves nothing before 19 Jul 2010 (probed back to Nov 2007)


def test_the_values_are_nses_own_in_date_order():
    assert READER.read(july_2010(), JULY) == [
        VixDay(date(2010, 7, 19), 19.7, 20.87, 19.36, 20.71),
        VixDay(date(2010, 7, 20), 20.71, 20.71, 19.61, 20.38),
    ]


def test_a_zero_level_is_kept_as_published_not_refused():
    data = month_file([nse_row(date(2021, 2, 12), 0, 0, 0, 23.045)])
    assert READER.read(data, date(2021, 2, 1)) == [VixDay(date(2021, 2, 12), 0.0, 0.0, 0.0, 23.045)]


BAD_FILES = {
    "html page": (b"<!DOCTYPE html><title>NSE India</title>Service Temporarily Unavailable", "not NSE's JSON"),
    "no data list": (b'{"rows": []}', 'no "data" list'),
    "empty": (month_file([]), "no rows"),
    "other index": (month_file([nse_row(date(2010, 7, 19), 1, 2, 1, 2, name="NIFTY 50")]), "not INDIA VIX"),
    "outside month": (month_file([nse_row(date(2010, 8, 2), 1, 2, 1, 2)]), "outside the month 2010-07"),
    "day twice": (month_file([nse_row(date(2010, 7, 19), 1, 2, 1, 2)] * 2), "days given twice"),
    "text level": (month_file([nse_row(date(2010, 7, 19), "1", 2, 1, 2)]), "not a number"),
    "missing level": (month_file([nse_row(date(2010, 7, 19), None, 2, 1, 2)]), "not a number"),
    "at the cap": (month_file([nse_row(date(2010, 7, 19), 1, 2, 1, 2)] * NSE_ROW_CAP), "may have been cut"),
}


@pytest.mark.parametrize("name", BAD_FILES)
def test_a_file_that_is_not_a_whole_clean_month_is_refused(name):
    data, reason = BAD_FILES[name]
    with pytest.raises(ValueError, match=reason):
        READER.read(data, JULY)
