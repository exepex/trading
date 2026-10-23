"""FL1-1d, design part: the signed-off design (d8f0440 on story/fl1-report-design, DESK_DECISIONS 11ef1b23) drawn
from a PageView. Pins the key elements of both editions: the key, the three big numbers, chart 1 and chart 2, the
day table's columns, the percentages, the calendar, the trend, the phone drawings; no bands, no bars, no request."""

import re

from fno.forecast_lab.design.evening import render_evening
from fno.forecast_lab.design.morning import render_morning
from fno.forecast_lab.design.renderer import DesignRenderer

from .design_builders import nifty, page, unchecked

KEY_WORDS = ("✓ Correct = closed inside “most likely”", "⚠ Close call = outside “most likely”",
             "✗ Missed = outside “almost certainly”")  # fmt: skip
TABLE_COLUMNS = ("<th>Date</th>", "<th>Forecast middle</th>", "<th>Most likely</th>", "<th>Almost certainly</th>",
                 "<th>Actual close</th>", "<th>Gap pts</th>", "<th>Gap %</th>", "<th>Result</th>",
                 '<th class="reason">Reason</th>')  # fmt: skip


def test_the_evening_page_carries_the_key_the_three_numbers_both_charts_the_table_and_the_counts():
    html = render_evening(page("evening", checked=True))
    assert all(words in html for words in KEY_WORDS) and html.count("How to read the result") == 1
    assert "<small>Forecast middle</small>" in html and "<small>Actual close</small>" in html
    assert "<small>Gap</small>" in html and " pts</b>" in html
    assert html.count('<svg class="lines"') == 4 and html.count('<svg class="gap"') == 4  # desk + phone, 2 indices
    assert html.count('<svg class="trend"') == 4 and html.count('class="calgrid"') == 2
    assert all(column in html for column in TABLE_COLUMNS)
    assert re.search(r"✓ Correct \d+ \(\d+%\)", html) and "trading days, the last 30" in html
    assert 'class="phone"' in html and 'class="desk"' in html


def test_the_evening_result_card_says_the_result_and_how_far_outside_which_range():
    html = render_evening(page("evening", indices=(nifty(checked=True),)))
    assert "⚠ Close call" in html or "✓ Correct" in html or "✗ Missed" in html
    assert "Closed " in html and ("the forecast middle" in html or "“almost certainly”" in html)
    assert "Why it was correct" in html or "Why a close call" in html or "Why it missed" in html


def test_chart_2_writes_every_miss_with_its_signed_gap_and_chart_1_the_last_values():
    html = render_evening(page("evening", indices=(nifty(checked=True),)))
    assert html.count('class="gv red"') == 2 * 3  # three misses, desk and phone
    assert ">forecast " in html and ">close " in html and "<title>" in html


def test_the_morning_page_carries_the_big_numbers_chart_1_with_todays_forecast_and_the_chip():
    html = render_morning(page("morning", checked=True))
    assert all(words in html for words in KEY_WORDS)
    assert "<small>Most likely</small>" in html and "<small>Almost certainly</small>" in html
    assert "<small>Forecast middle</small>" in html and "1 day in 2" in html and "9 days in 10" in html
    assert html.count('<svg class="lines"') == 4 and html.count('class="pf"') == 4  # today's forecast point
    assert "almost certainly</tspan>" in html and 'class="gap"' not in html
    assert "Inside “almost certainly”" in html and ("· steady" in html or "· watch" in html)
    assert "Why this forecast" in html and "not available yet" in html  # no cue wired yet: plain words, no guess


def test_no_shaded_band_no_bar_no_request_and_one_definition_of_right():
    for html in (render_morning(page("morning", checked=True)), render_evening(page("evening", checked=True))):
        assert "<rect" not in html.replace('<rect class="zone"', "")  # the trend's warning zone is the only rect
        assert "polygon" not in html and "http://" not in html and "https://" not in html and "<link" not in html
        assert "Right " not in html  # the three words correct / close call / missed, never a bare "right"


def test_the_renderer_picks_the_edition_and_serves_the_same_page_as_picture_and_details():
    renderer = DesignRenderer()
    evening = page("evening", checked=True)
    assert renderer.picture(evening) == renderer.details(evening)
    morning = page("morning", checked=True)
    if getattr(morning, "edition", "evening") == "morning":  # the model after FL1-1d-1
        assert "Today’s forecast" in renderer.picture(morning) and "chart 2" not in renderer.picture(morning)
    assert "Was today’s forecast right?" in renderer.picture(evening)


def test_an_index_without_scored_sessions_renders_a_plain_line_instead_of_charts():
    from dataclasses import replace

    bare = replace(nifty(checked=True), horizons=(), scored=0, right=0, light="none", light_word="Too few days")
    html = render_evening(page("evening", indices=(bare,)))
    assert "no scored session yet" in html and "<svg" not in html
    assert "Too few days" in render_morning(page("morning", indices=(bare,)))


def test_the_result_card_reads_only_the_editions_own_check_never_an_older_day():
    """Owner, 23 Oct: with no check of today, the page said 21 Oct's result under "Was today's forecast right?"."""
    from dataclasses import replace
    from types import SimpleNamespace

    from fno.forecast_lab.design.values import days_of, result_of

    index = nifty(checked=True)
    own = index.horizons[0].timeline.points[-5]
    assert result_of(SimpleNamespace(result=own)).day == own.day  # IndexView.result (FL1-1d-2)
    assert result_of(replace(index, result=None)) is None and days_of(index, 30)  # never days[-1] instead


def test_the_honesty_labels_are_printed_and_never_dropped():
    """Judge 446: a mutation that drops any of these must fail here."""
    from dataclasses import replace
    from types import SimpleNamespace

    from fno.forecast_lab.design.blocks import result_card
    from fno.forecast_lab.design.values import day_of
    from fno.forecast_lab.page.model import Miss

    index = nifty(checked=True)
    # 1. a reason from the data is escaped, never injected as markup
    # the hostile reason sits on the newest miss, a red row of the shown day table AND of the misses table (446.1)
    hostile = replace(index, misses=(Miss(index.misses[-1].day, "above", 60.0, ("<b>bold</b> & co",)),))
    html = render_evening(page("evening", indices=(hostile,)))
    assert html.count("&lt;b&gt;bold&lt;/b&gt; &amp; co") == 2 and "<b>bold</b>" not in html
    # 2. a provisional close says so instead of the date
    point = index.horizons[0].timeline.points[-1]
    provisional = SimpleNamespace(day=point.day, close=point.close, band=point.band, inside_50=point.inside_50,
                                  inside_90=point.inside_90, live=False, provisional=True)  # fmt: skip
    assert "the official file confirms it in the next morning report" in result_card(day_of(provisional))
    assert "the official file confirms it" not in result_card(day_of(point))
    # 3. the back-tested count is on both pages: the evening's note and the morning's chip, and the method line
    tested = replace(index, backtested=7)
    evening = render_evening(page("evening", indices=(tested,)))
    morning = render_morning(page("morning", indices=(tested,)))
    assert "7 of the last 30 were scored on a back-fill, not live" in evening
    assert "· 7 back-tested ·" in morning and "back-tested 7 of the last 30 days" in morning
    assert "Method: implied, lowest error on its own history" in evening and "0 of 60 live days scored" in morning
    assert "back-tested" not in render_morning(page("morning", indices=(index,)))  # none when there is none
    # 4. system problems are printed on both pages, and "all normal" only when there is none
    from fno.forecast_lab.page.model import PageView

    broken = PageView(page(checked=True).day, "Live, sealed", (index,), (), ("a forecast is missing: data late",))
    for html in (render_morning(broken), render_evening(broken)):
        assert "⚠ a forecast is missing: data late" in html and "All systems normal" not in html
    assert "All systems normal" in render_evening(page("evening", checked=True))


def test_the_result_words_come_from_one_source_shared_with_the_text_lines():
    from fno.forecast_lab.design.formats import AMBER, GLYPH, GREEN, RED, WORD
    from fno.forecast_lab.page.plain import RESULTS

    assert f"{GLYPH[GREEN]} {WORD[GREEN]}" == RESULTS[(True, True)] == "✓ Correct"
    assert f"{GLYPH[AMBER]} {WORD[AMBER]}" == RESULTS[(False, True)] == "⚠ Close call"
    assert f"{GLYPH[RED]} {WORD[RED]}" == RESULTS[(False, False)] == "✗ Missed"


def test_the_evening_verdict_comes_first_in_the_owners_words_then_why_record_and_the_next_forecast():
    """Owner, 23 Oct: per index, the verdict (close against both ranges, glyph plus word), why, the record with
    back-tested apart, then the next session's forecast; the words are the FL1 builder's text lines' (FL1-1e)."""
    from dataclasses import replace

    from fno.forecast_lab.design.verdict import VERDICTS, YES_NO

    index = nifty(checked=True)
    html = render_evening(page("evening", indices=(index,)))
    card = html[html.index("<h2>NIFTY") : html.index("chart 1")]
    assert "today: closed <b>" in card and "(NSE&#x27;s official close)" in card
    assert "inside “most likely”: <b>yes</b>" in card and "inside “almost certainly”: <b>yes</b>" in card
    assert 'verdict: <b class="green">✓ right</b>' in card and VERDICTS == {True: "✓ right", False: "✗ wrong"}
    order = ("verdict:", "<small>Forecast middle</small>", "Why it was correct", "Inside “almost certainly”",
             "Method: implied", "Next session’s forecast · close")  # fmt: skip
    assert [card.index(words) for words in order] == sorted(card.index(words) for words in order)
    assert YES_NO == {True: "yes", False: "no"}
    # a close outside "almost certainly" is wrong, in red, with "no" on both ranges
    point = index.horizons[0].timeline.points[-1]
    missed = replace(index, result=replace(point, close=point.band.q95 + 60, inside_50=False, inside_90=False))
    wrong = render_evening(page("evening", indices=(missed,)))
    assert 'verdict: <b class="red">✗ wrong</b>' in wrong and wrong.count("<b>no</b>") == 2
    # a close call (judge 538 F3): outside "most likely", inside "almost certainly": right, green, over the amber chip
    amber = replace(index, result=replace(point, close=point.band.q75 + 80, inside_50=False, inside_90=True))
    call = render_evening(page("evening", indices=(amber,)))
    card = call[call.index("<h2>NIFTY") : call.index("chart 1")]
    assert "inside “most likely”: <b>no</b>" in card and "inside “almost certainly”: <b>yes</b>" in card
    assert card.index('verdict: <b class="green">✓ right</b>') < card.index('<span class="chip amber">⚠ Close call')


def test_the_evening_without_a_check_says_so_in_red_first_and_names_the_last_checked_day():
    why = "today: not checked yet (NSE close not read); result in Monday's morning report"
    html = render_evening(page("evening", indices=(unchecked(nifty(), why),)))
    card = html[html.index("<h2>NIFTY") : html.index("chart 1")]
    red = card.index('<p class="nocheck">⚠ today: not checked yet (NSE close not read)')
    assert red < card.index("last checked:") < card.index("Method:")  # judge 538 F2: the red line first
    assert "<small>today: not checked</small>" in card and "verdict:" not in card and "Why " not in card
    assert "last checked: Thu 22 Oct, ✓ Correct" in card and "Next session’s forecast" in card
    # the model before FL1-1e carries no reason: the plain line, never a guess
    bare = unchecked(nifty(), "")
    assert "⚠ today: not checked (no verdict)" in render_evening(page("evening", indices=(bare,)))


def test_the_close_label_names_the_morning_report_that_confirms_it_never_tomorrow_on_a_friday():
    from dataclasses import replace
    from datetime import date

    from fno.forecast_lab.design.verdict import morning_report

    friday, monday = date(2026, 10, 23), date(2026, 10, 26)
    assert morning_report(friday, monday) == "Monday's morning report"
    assert morning_report(date(2026, 10, 22), friday) == "tomorrow morning's report"
    assert morning_report(friday, None) == "the next morning report"
    index = nifty(checked=True)
    provisional = replace(index, result=replace(index.result, provisional=True))
    view = page("evening", indices=(provisional,))
    try:
        view = replace(view, next_session=monday)  # FL1-1e's PageView.next_session
    except TypeError:
        view.__dict__["next_session"] = monday
    html = render_evening(view)
    assert "(NSE&#x27;s close; the official file confirms it in Monday&#x27;s morning report)" in html
    assert "close as read after 15:30; the official file confirms it in Monday&#x27;s morning report" in html
    assert "next morning" not in html  # the small note under the close names the same report as the verdict line


def test_the_morning_shows_the_previous_sessions_check_in_the_same_words_with_its_day():
    html = render_morning(page("morning", indices=(nifty(checked=True),)))
    assert "Last session’s check" in html and "Fri 23 Oct: closed <b>" in html
    assert "inside “almost certainly”: <b>yes</b>" in html and 'verdict: <b class="green">✓ right</b>' in html
    from dataclasses import replace

    assert "Last session’s check" not in render_morning(
        page("morning", indices=(replace(nifty(checked=True), result=None),))
    )


def test_a_past_days_check_is_never_called_today():
    """Orchestrator, 23 Oct: a past day under "today" without its date label is the fault of the 23 Oct page."""
    from dataclasses import replace

    index = nifty(checked=True)
    past = replace(index, result=index.horizons[0].timeline.points[-3])  # Wed 21 Oct on the Fri 23 Oct page
    html = render_evening(page("evening", indices=(past,)))
    assert "Wed 21 Oct: closed <b>" in html and "<small>Wed 21 Oct · closed" in html
    assert "today: closed" not in html and "today · closed" not in html
    own = render_evening(page("evening", indices=(index,)))
    assert "today: closed <b>" in own and "<small>today · closed" in own


def test_the_chip_counts_over_its_own_window_and_a_cues_unit_goes_on_the_change_only():
    """Seen on the 23 Oct dry run: the morning chip said "25 of 30 (✓ correct 2 · ⚠ close call 5)", counted over the
    10 days the morning chart shows; and a level printed as "7,663.43%" because the change's unit was appended."""
    import re
    from datetime import date

    from fno.forecast_lab.design.page import _cue_words, reliability_chip
    from fno.forecast_lab.design.values import days_of
    from fno.forecast_lab.page.cues import Cue

    index = nifty(checked=True)
    chip = reliability_chip(index, days_of(index, 10))
    correct, close = map(int, re.search(r"✓ correct (\d+) · ⚠ close call (\d+)", chip).groups())
    assert correct + close == index.right == 27 and f"{index.right} of {index.scored}" in chip
    assert chip == reliability_chip(index, days_of(index, 30))
    assert _cue_words(Cue("S&P 500", 7000.5, -1.21, "%", date(2026, 10, 22))) == "7,000.5 −1.21%"
    assert _cue_words(Cue("US 10-year yield", 4.96, -0.17, "pts", date(2026, 10, 22))) == "4.96 −0.17pts"
    assert _cue_words(Cue("India VIX", 15.76, 0.51, "%", date(2026, 10, 22))) == "15.76 +0.51%"
