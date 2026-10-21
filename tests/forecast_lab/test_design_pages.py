"""FL1-1d, design part: the signed-off design (d8f0440 on story/fl1-report-design, DESK_DECISIONS 11ef1b23) drawn
from a PageView. Pins the key elements of both editions: the key, the three big numbers, chart 1 and chart 2, the
day table's columns, the percentages, the calendar, the trend, the phone drawings; no bands, no bars, no request."""

import re

from fno.forecast_lab.design.evening import render_evening
from fno.forecast_lab.design.morning import render_morning
from fno.forecast_lab.design.renderer import DesignRenderer

from .design_builders import nifty, page

KEY_WORDS = ("✓ Correct = closed inside “most likely”", "⚠ Close call = outside “most likely”",
             "✗ Missed = outside “almost certainly”")  # fmt: skip
TABLE_COLUMNS = ("<th>Date</th>", "<th>Forecast middle</th>", "<th>Most likely</th>", "<th>Almost certainly</th>",
                 "<th>Actual close</th>", "<th>Gap pts</th>", "<th>Gap %</th>", "<th>Result</th>",
                 '<th class="reason">Reason</th>')  # fmt: skip


def test_the_evening_page_carries_the_key_the_three_numbers_both_charts_the_table_and_the_counts():
    html = render_evening(page("evening"))
    assert all(words in html for words in KEY_WORDS) and html.count("How to read the result") == 1
    assert "<small>Forecast middle</small>" in html and "<small>Actual close</small>" in html
    assert "<small>Gap</small>" in html and " pts</b>" in html
    assert html.count('<svg class="lines"') == 4 and html.count('<svg class="gap"') == 4  # desk + phone, 2 indices
    assert html.count('<svg class="trend"') == 4 and html.count('class="calgrid"') == 2
    assert all(column in html for column in TABLE_COLUMNS)
    assert re.search(r"✓ Correct \d+ \(\d+%\)", html) and "trading days, the last 30" in html
    assert 'class="phone"' in html and 'class="desk"' in html


def test_the_evening_result_card_says_the_result_and_how_far_outside_which_range():
    html = render_evening(page("evening", indices=(nifty(),)))
    assert "⚠ Close call" in html or "✓ Correct" in html or "✗ Missed" in html
    assert "Closed " in html and ("the forecast middle" in html or "“almost certainly”" in html)
    assert "Why it was correct" in html or "Why a close call" in html or "Why it missed" in html


def test_chart_2_writes_every_miss_with_its_signed_gap_and_chart_1_the_last_values():
    html = render_evening(page("evening", indices=(nifty(),)))
    assert html.count('class="gv red"') == 2 * 3  # three misses, desk and phone
    assert ">forecast " in html and ">close " in html and "<title>" in html


def test_the_morning_page_carries_the_big_numbers_chart_1_with_todays_forecast_and_the_chip():
    html = render_morning(page("morning"))
    assert all(words in html for words in KEY_WORDS)
    assert "<small>Most likely</small>" in html and "<small>Almost certainly</small>" in html
    assert "<small>Forecast middle</small>" in html and "1 day in 2" in html and "9 days in 10" in html
    assert html.count('<svg class="lines"') == 4 and html.count('class="pf"') == 4  # today's forecast point
    assert "almost certainly</tspan>" in html and 'class="gap"' not in html
    assert "Inside “almost certainly”" in html and ("· steady" in html or "· watch" in html)
    assert "Why this forecast" in html and "not available yet" in html  # no cue wired yet: plain words, no guess


def test_no_shaded_band_no_bar_no_request_and_one_definition_of_right():
    for html in (render_morning(page("morning")), render_evening(page("evening"))):
        assert "<rect" not in html.replace('<rect class="zone"', "")  # the trend's warning zone is the only rect
        assert "polygon" not in html and "http://" not in html and "https://" not in html and "<link" not in html
        assert "Right " not in html  # the three words correct / close call / missed, never a bare "right"


def test_the_renderer_picks_the_edition_and_serves_the_same_page_as_picture_and_details():
    renderer = DesignRenderer()
    evening = page("evening")
    assert renderer.picture(evening) == renderer.details(evening)
    morning = page("morning")
    if getattr(morning, "edition", "evening") == "morning":  # the model after FL1-1d-1
        assert "Today’s forecast" in renderer.picture(morning) and "chart 2" not in renderer.picture(morning)
    assert "Was today’s forecast right?" in renderer.picture(evening)


def test_an_index_without_scored_sessions_renders_a_plain_line_instead_of_charts():
    from dataclasses import replace

    bare = replace(nifty(), horizons=(), scored=0, right=0, light="none", light_word="Too few days")
    html = render_evening(page("evening", indices=(bare,)))
    assert "no scored session yet" in html and "<svg" not in html
    assert "Too few days" in render_morning(page("morning", indices=(bare,)))


def test_the_result_card_reads_the_editions_own_check_when_the_model_carries_it():
    from types import SimpleNamespace

    from fno.forecast_lab.design.values import days_of, result_of

    index = nifty()
    days = days_of(index, 30)
    assert result_of(index, days).day == days[-1].day  # main's model: the newest scored session
    own = index.horizons[0].timeline.points[-5]
    with_result = SimpleNamespace(result=own, horizons=index.horizons)
    assert result_of(with_result, days).day == own.day  # FL1-1d-2's model: IndexView.result
    assert result_of(SimpleNamespace(result=None, horizons=()), []) is None
