"""Protocol section 8, revision 5: legacy-file days take NSE's circular schedule (the derived lot only checks it),
UDiFF days take NSE's board lot, and a derived lot more than 5% off the schedule is listed."""

from datetime import date

from edge1study.day_files import DayRows
from edge1study.lots import circular_lot, disagreements, market_lots


def row(day, lots, source):
    return DayRows(day, (), (), lots, source)


def test_each_change_applies_from_its_first_expiry():
    assert circular_lot("NIFTY", date(2021, 6, 24)) == 75 and circular_lot("NIFTY", date(2021, 7, 29)) == 50
    assert circular_lot("BANKNIFTY", date(2020, 6, 25)) == 20 and circular_lot("BANKNIFTY", date(2020, 7, 30)) == 25
    assert circular_lot("BANKNIFTY", date(2023, 6, 29)) == 25 and circular_lot("BANKNIFTY", date(2023, 7, 27)) == 15


def test_legacy_days_use_the_schedule_and_udiff_days_the_board_lot():
    rows = [row(date(2020, 3, 13), {date(2020, 3, 26): 72}, "legacy"), row(date(2024, 5, 2), {date(2024, 5, 30): 25},
                                                                          "udiff")]  # fmt: skip
    assert market_lots("NIFTY", rows) == {date(2020, 3, 13): {date(2020, 3, 26): 75},
                                          date(2024, 5, 2): {date(2024, 5, 30): 25}}  # fmt: skip


def test_only_a_derived_lot_more_than_5_percent_off_is_listed():
    rows = [row(date(2020, 3, 13), {date(2020, 3, 26): 72, date(2020, 4, 30): 70}, "legacy"),
            row(date(2024, 5, 2), {date(2024, 5, 30): 25}, "udiff")]  # fmt: skip
    assert disagreements("NIFTY", rows) == [(date(2020, 3, 13), date(2020, 4, 30), 70, 75)]
