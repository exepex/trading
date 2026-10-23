"""FL1-1c and FL1-1d: the message's plain words (owner, 21 Oct 2026, DESK_DECISIONS 194aa8b3): "today" and
"tomorrow" only when true, ranges rounded outward, the 30-day light's thresholds, the edition's title, one line per
index and the fixed research line."""

from datetime import date

from fno.forecast_lab.page.model import Band
from fno.forecast_lab.page.plain import certain, light, likely, outward, slack_lines, when

from .page_builders import index, page

FRI, MON = date(2026, 10, 23), date(2026, 10, 26)


def test_tomorrow_is_said_only_when_the_next_session_is_the_next_calendar_day():
    assert when(1, date(2026, 10, 22), date(2026, 10, 21)) == "tomorrow"
    assert when(1, MON, FRI) == "next trading day, Mon 26 Oct"  # a weekend between
    assert when(3, date(2026, 10, 28), FRI) == "in 3 trading days, Wed 28 Oct"
    assert when(0, FRI, FRI) == "today"  # the morning edition's forecast for the session that opens today
    assert when(2, date(2026, 10, 27), FRI) == "in 2 trading days, Tue 27 Oct"  # the morning's N3, issued before


def test_ranges_in_words_are_rounded_outward_so_they_never_claim_a_narrower_range():
    assert outward(22745.32, 22999.51) == (22740, 23000)
    band = Band(22536.6, 22745.32, 22878.2, 22999.51, 23184.67)
    assert (likely(band), certain(band)) == ("22,740–23,000", "22,530–23,190")


def test_the_light_is_green_from_25_amber_at_24_red_at_23_or_fewer_and_grey_with_too_few_days():
    assert [light(index(right=r)) for r in (25, 24, 23)] == ["green", "amber", "red"]
    assert light(index(right=10, scored=12)) == "none"


def test_the_message_is_one_line_per_index_then_the_status_line():
    title, *lines = slack_lines(page())
    right = "Right = the close fell inside the “almost certainly” range."
    assert title == f"*Was today's forecast right?* (Fri 23 Oct, 20:05) {right}"
    assert lines[0].startswith("*NIFTY* · next trading day, Mon 26 Oct: most likely 990–1,010 (almost certainly")
    assert lines[0].endswith("🟢 past 30 days: inside “almost certainly” 26 of 30")
    assert lines[-1] == "✅ All systems normal. Research only. Not a trade tip."
    missing = slack_lines(page(system=("NIFTY: today's forecast is missing (none written by 15:47)",)))[-1]
    assert missing == "⚠️ NIFTY: today's forecast is missing (none written by 15:47). Research only. Not a trade tip."


def test_a_day_without_a_forecast_still_says_how_right_it_has_been():
    assert (
        slack_lines(page(indices=(index(today=()),)))[1]
        == "*NIFTY* · 🟢 past 30 days: inside “almost certainly” 26 of 30"
    )


def test_back_tested_days_are_said_in_the_record_until_the_window_is_all_live():
    from dataclasses import replace

    line = slack_lines(page(indices=(replace(index(today=()), backtested=26),)))[1]
    assert line == "*NIFTY* · 🟢 past 30 days (back-tested 26): inside “almost certainly” 26 of 30"


def test_the_morning_report_that_confirms_a_day_is_the_next_session_s_by_name():
    from fno.forecast_lab.page.plain import morning_report

    assert morning_report(date(2026, 10, 22), FRI) == "tomorrow's morning report"
    assert morning_report(FRI, MON) == "Monday's morning report"
    assert morning_report(FRI, None) == "the next morning report"
