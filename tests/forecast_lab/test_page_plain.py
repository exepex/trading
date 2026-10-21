"""FL1-1c: the message's plain words (owner, 21 Oct 2026, DESK_DECISIONS 194aa8b3): "tomorrow" only when true, ranges
rounded outward, the 30-day light's thresholds, the 3 lines with the fixed research line."""

from datetime import date

from fno.forecast_lab.page.model import Band
from fno.forecast_lab.page.plain import certain, light, likely, outward, slack_lines, when

from .page_builders import index, page

FRI, MON = date(2026, 10, 23), date(2026, 10, 26)


def test_tomorrow_is_said_only_when_the_next_session_is_the_next_calendar_day():
    assert when("N1", date(2026, 10, 22), date(2026, 10, 21)) == "tomorrow"
    assert when("N1", MON, FRI) == "next trading day, Mon 26 Oct"  # a weekend between
    assert when("N3", date(2026, 10, 28), FRI) == "in 3 trading days, Wed 28 Oct"


def test_ranges_in_words_are_rounded_outward_so_they_never_claim_a_narrower_range():
    assert outward(22745.32, 22999.51) == (22740, 23000)
    band = Band(22536.6, 22745.32, 22878.2, 22999.51, 23184.67)
    assert (likely(band), certain(band)) == ("22,740–23,000", "22,530–23,190")


def test_the_light_is_green_from_25_amber_at_24_red_at_23_or_fewer_and_grey_with_too_few_days():
    assert [light(index(right=r)) for r in (25, 24, 23)] == ["green", "amber", "red"]
    assert light(index(right=10, scored=12)) == "none"


def test_the_message_is_one_line_per_index_then_the_status_line():
    lines = slack_lines(page())
    assert lines[0].startswith("*NIFTY* · next trading day, Mon 26 Oct: most likely 990–1,010 (almost certainly")
    assert lines[0].endswith("🟢 right 26 of the last 30 days")
    assert lines[-1] == "✅ All systems normal. Research only. Not a trade tip."
    missing = slack_lines(page(system=("NIFTY: today's forecast is missing (none written by 15:47)",)))[-1]
    assert missing == "⚠️ NIFTY: today's forecast is missing (none written by 15:47). Research only. Not a trade tip."


def test_a_day_without_a_forecast_still_says_how_right_it_has_been():
    assert slack_lines(page(indices=(index(today=()),)))[0] == "*NIFTY* · 🟢 right 26 of the last 30 days"


def test_back_tested_days_are_said_in_the_record_until_the_window_is_all_live():
    from dataclasses import replace

    line = slack_lines(page(indices=(replace(index(today=()), backtested=26),)))[0]
    assert line == "*NIFTY* · 🟢 right 26 of the last 30 days (26 back-tested)"
