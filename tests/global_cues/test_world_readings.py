"""Story A17e, criterion 3 and amendment 1: one reading per index prefers the official value and reads Yahoo's when the
official copy lacks the date (the Nasdaq-100 on 20-21 Oct 2026); the official/Yahoo comparison lists differences and
missing sessions by date and kind only. Every level here is made up."""

from datetime import date

from fno.global_cues.as_of import OPEN
from fno.global_cues.check_files import CueChecks
from fno.global_cues.cue_calendars import WeekdayCalendar
from fno.global_cues.index_reader import IndexPair, IndexReader
from fno.global_cues.markets import NEW_YORK
from fno.global_cues.pair_checks import DIFFERS, ONLY_OFFICIAL, ONLY_YAHOO, pair_rows
from fno.global_cues.reading import CURRENT, NONE, CueReader
from fno.global_cues.us_index_sources import NasdaqNdxSource
from fno.global_cues.yahoo_source import UNVERIFIED, YahooChartSource


class Table:
    def __init__(self, rows):
        self._rows = rows

    def rows(self):
        return self._rows


def row(day: str, value: float, seen: str) -> dict:
    return {"value_date": day, "value": str(value), "first_seen_at": seen}


SEEN_20, SEEN_21 = "2026-10-20T06:34:02+05:30", "2026-10-21T06:04:21+05:30"
# as observed: Nasdaq's 03:41 copies lacked the previous US close; Yahoo's had it (made-up levels)
NASDAQ = [row("2026-10-16", 100.0, SEEN_20), row("2026-10-19", 101.0, SEEN_21)]
YAHOO = [row("2026-10-16", 100.0, SEEN_20), row("2026-10-19", 101.0, SEEN_20), row("2026-10-20", 102.0, SEEN_21)]


def reader(official_rows, yahoo_rows, official="nasdaq100"):
    yahoo = YahooChartSource("nasdaq100_yahoo", "^NDX", NEW_YORK, 4, official is not None)
    sources = {"nasdaq100": NasdaqNdxSource(), "nasdaq100_yahoo": yahoo}
    tables = {"nasdaq100_yahoo": Table(yahoo_rows)} | ({official: Table(official_rows)} if official else {})
    cue_reader = CueReader(tables, sources, dict.fromkeys(sources, WeekdayCalendar()))
    return IndexReader(cue_reader, {"nasdaq100": IndexPair(official, "nasdaq100_yahoo")})


def test_at_the_open_a_late_official_close_reads_yahoos_and_the_official_wins_once_it_has_the_date():
    on_21 = reader(NASDAQ, YAHOO).read("nasdaq100", date(2026, 10, 21), OPEN, live_only=True)
    assert (on_21.cue, on_21.reading.row["value_date"], on_21.reading.status) == (
        "nasdaq100_yahoo",
        "2026-10-20",
        CURRENT,
    )
    on_20 = reader(NASDAQ, YAHOO).read("nasdaq100", date(2026, 10, 20), OPEN, live_only=True)
    assert (on_20.cue, on_20.reading.row["value_date"]) == (
        "nasdaq100_yahoo",
        "2026-10-19",
    )  # Nasdaq's 19th came the 21st
    later = NASDAQ + [row("2026-10-20", 102.0, "2026-10-22T05:30:00+05:30")]
    on_22 = reader(later, YAHOO).read("nasdaq100", date(2026, 10, 22), OPEN, live_only=False)
    assert on_22.cue == "nasdaq100" and on_22.reading.row["value_date"] == "2026-10-20"  # a tie goes to the official
    assert on_22.verified and on_22.label == ""


def test_no_value_anywhere_reads_none_and_a_yahoo_only_index_is_labelled_unverified():
    empty = reader([], []).read("nasdaq100", date(2026, 10, 21), OPEN, live_only=True)
    assert (empty.cue, empty.reading.status) == (None, NONE)
    lone = reader([], YAHOO, official=None).read("nasdaq100", date(2026, 10, 21), OPEN, live_only=True)
    assert lone.cue == "nasdaq100_yahoo" and not lone.verified and lone.label == UNVERIFIED


def test_pair_rows_list_differences_over_a_tenth_of_a_percent_and_sessions_only_one_has_inside_the_shared_span():
    official = [
        row(d, v, "")
        for d, v in (("2026-02-05", 17.0), ("2026-02-06", 17.76), ("2026-02-09", 18.0), ("2026-05-25", 15.0))
    ]
    yahoo = [
        row(d, v, "")
        for d, v in (("2026-02-04", 16.0), ("2026-02-05", 17.017), ("2026-02-06", 20.37), ("2026-02-09", 18.0))
    ]
    found = pair_rows("vix_us", official, yahoo)
    assert found == [("vix_us", "2026-02-06", DIFFERS)]  # 17.017 is 0.1% over 17.0: at the limit, not listed
    assert pair_rows("vix_us", official, yahoo + [row("2026-02-10", 18.0, "")]) == [
        ("vix_us", "2026-02-06", DIFFERS),
        ("vix_us", "2026-02-10", ONLY_YAHOO),
    ]
    holiday = official[:2] + [row("2026-02-08", 1.0, "")] + official[2:]
    assert ("vix_us", "2026-02-08", ONLY_OFFICIAL) in pair_rows("vix_us", holiday, yahoo)
    assert pair_rows("vix_us", [], yahoo) == [] and pair_rows("vix_us", official, []) == []


def test_the_checks_print_counts_only_write_dates_to_drive_and_name_the_unverified(tmp_path):
    written = {}

    class Snapshots:
        def write(self, fields, rows):
            written["rows"] = (fields, rows)

    official = [row("2026-02-06", 17.76, ""), row("2026-02-09", 18.0, "")]
    yahoo = [row("2026-02-06", 20.37, ""), row("2026-02-09", 18.0, "")]
    tables = {"vix_us": Table(official), "vix_us_yahoo": Table(yahoo), "hang_seng_yahoo": Table(yahoo)}
    pairs = {"vix_us": IndexPair("vix_us", "vix_us_yahoo"), "hang_seng": IndexPair(None, "hang_seng_yahoo")}
    private = {cue: Snapshots() for cue in tables}
    lines = CueChecks(tables, tmp_path, private, None, pairs, {"vix_us": Snapshots()}).write()
    assert "vix_us official against Yahoo: 2 dates compared, {'differs_over_0.1pct': 1}" in lines
    assert "unverified (Yahoo only): hang_seng" in lines
    assert written["rows"][1] == [("vix_us", "2026-02-06", DIFFERS)]
    assert not any("17.76" in line or "20.37" in line for line in lines)  # no level is ever printed


def test_official_holiday_rows_are_not_compared():
    official = [row(d, 1.0, "") for d in ("2026-05-22", "2026-05-25", "2026-05-26")]  # 25 May: Memorial Day
    yahoo = [row(d, 1.0, "") for d in ("2026-05-22", "2026-05-26", "2026-09-07")]  # 7 Sep: Labor Day, Yahoo's row
    assert pair_rows("vix_us", official, yahoo[:2]) == [("vix_us", "2026-05-25", ONLY_OFFICIAL)]
    us_sessions = lambda day: day != date(2026, 5, 25)  # noqa: E731
    assert pair_rows("vix_us", official, yahoo, us_sessions) == []
