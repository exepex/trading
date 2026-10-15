"""Story A14c criterion 2: the largest held rise of the whole margin C2 counts, by hand on planted files. A held SF
100 entered on 1 Oct at scale 1 (margin 53,950) peaks on 7 Oct at scale 10 (71,500): rise 1.32530; a smaller bump the
day before and after must not win, and every day of the holding is read."""

from datetime import date

import pytest

from fno.nse_margins.span_file import read_span_file

from .span_builder import EXPIRY
from .stress_days import BASE_MARGIN, EXPIRY2, FIRST, day_bytes, margin, planted, sf_tracker

EXIT = date(2026, 11, 2)  # the last weekday 21+ days before 23 Nov


def fed(scales):
    tracker = sf_tracker()
    for day, data in sorted(planted(EXIT, scales).items()):
        tracker.feed(day, read_span_file(data, f"nsccl.{day:%Y%m%d}.i1.zip"), open_new=day == FIRST)
    return tracker


def test_the_largest_rise_over_the_holding_by_hand():
    tracker = fed({date(2026, 10, 6): 2.0, date(2026, 10, 7): 10.0, date(2026, 10, 8): 5.0})
    (held,) = tracker.found.completed
    assert (held.entry, held.exit, held.peak_day) == (FIRST, EXIT, date(2026, 10, 7))
    assert held.entry_margin == pytest.approx(BASE_MARGIN) and held.peak_margin == pytest.approx(margin(10))
    assert held.rise == pytest.approx(71_500 / 53_950)  # 1.32530


def test_a_rise_on_the_exit_day_counts():
    (held,) = fed({EXIT: 4.0}).found.completed
    assert held.peak_day == EXIT and held.rise == pytest.approx(margin(4) / BASE_MARGIN)


def test_a_position_whose_margin_only_falls_has_a_rise_of_one():
    (held,) = fed({date(2026, 10, 7): 0.1}).found.completed
    assert held.rise == pytest.approx(1.0) and held.peak_day == FIRST


def test_a_leg_missing_on_a_held_day_drops_the_position_by_name():
    tracker = sf_tracker()
    files = planted(EXIT)
    for day, data in sorted(files.items()):
        span = read_span_file(data, f"nsccl.{day:%Y%m%d}.i1.zip")
        if day == date(2026, 10, 9):
            span.series[EXPIRY].pop((20100.0, "CE"))
        tracker.feed(day, span, open_new=day == FIRST)
    assert tracker.found.completed == [] and "SF 100 entered 2026-10-01" in tracker.found.dropped[0]


def test_every_day_opens_its_own_entry_and_only_finished_holdings_complete():
    tracker = sf_tracker()
    for day, data in sorted(planted(date(2026, 10, 30)).items()):
        tracker.feed(day, read_span_file(data, f"nsccl.{day:%Y%m%d}.i1.zip"))
    assert tracker.found.completed == []  # the first exit is 2 Nov
    by_expiry = {(h.entry, h.expiry) for h in tracker.open}
    assert by_expiry == {(d, EXPIRY if d <= date(2026, 10, 23) else EXPIRY2) for d in planted(date(2026, 10, 30))}


def test_a_planted_day_reads_as_its_hand_figure():
    data = day_bytes(FIRST, 3.0)
    span = read_span_file(data, "nsccl.20261001.i1.zip")
    tracker = sf_tracker()
    tracker.feed(FIRST, span)
    assert tracker.open[0].entry_margin == pytest.approx(margin(3))
