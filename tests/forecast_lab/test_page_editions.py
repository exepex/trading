"""FL1-1d: the page in its two editions. The morning shows the forecasts sealed the session before for today and the
next sessions, against the last official close; the evening checks today's forecast against today's close as read,
labelled provisional, and says plainly when no close was read. The newest scored session expected differs: G13b
scores the previous session only in the 14:33 routine, so at 08:50 it is two sessions back."""

from datetime import date

from fno.forecast_lab.page.builder import PageBuilder
from fno.forecast_lab.page.plain import slack_lines
from fno.forecast_lab.ranges import STATUS_OK, Outcomes, RangeRow, TodayCloses

from .builders import QUANTILES, REPORT_DAY, SESSIONS, Forecasts, at, issue
from .test_page_builder import HISTORY_DAYS, History, NoFacts

FRI, MON, WED = date(2026, 10, 23), REPORT_DAY, date(2026, 10, 28)  # 26 Oct is a Monday; FRI its previous session


def implied(day):
    """The previous session's issue by the page's best method (implied): N1 for the next session, N3 three on."""
    n1, n3 = SESSIONS.next(day), SESSIONS.next(SESSIONS.next(SESSIONS.next(day)))
    return issue(day, rows=(RangeRow("implied", "N1", n1, QUANTILES, 0.5, STATUS_OK),
                            RangeRow("implied", "N3", n3, QUANTILES, 0.5, STATUS_OK)))  # fmt: skip


class Official(Outcomes):
    def __init__(self, closes):
        self.closes = closes

    def close(self, underlying, day):
        return self.closes.get(day)


class Read(TodayCloses):
    def __init__(self, value=None):
        self.value = value

    def close(self, underlying, day):
        return self.value

    def why_missing(self, day):
        return "NSE's index list did not answer"


def build(edition, issues, official=None, read=None, history=None, at_time=(8, 50)):
    pages = PageBuilder(Forecasts(issues), history or History(), NoFacts(), SESSIONS, underlyings=("NIFTY",),
                        official=Official(official or {}), today_closes=Read(read))  # fmt: skip
    return pages.build(MON, at(MON, *at_time), edition)


def test_the_morning_shows_the_forecasts_sealed_for_today_and_the_outlook_against_the_last_official_close():
    view = build("morning", (implied(FRI),), official={FRI: 25310.5})
    (index,) = view.indices
    assert [(r.horizon, r.target_day, r.when) for r in index.today] == [
        ("N1", MON, "today"), ("N3", WED, "in 2 trading days, Wed 28 Oct")]  # fmt: skip
    assert (index.price, index.price_at) == (25310.5, "close Fri 23 Oct") and view.edition == "morning"
    assert slack_lines(view)[0] == "*Today's forecast* (Mon 26 Oct, 08:50)"


def test_the_morning_without_the_official_close_marks_the_3_pm_price_and_says_so():
    (index,) = build("morning", (implied(FRI),)).indices
    assert (index.price, index.price_at) == (25250.0, "3 pm price Fri 23 Oct")


def test_a_morning_without_the_previous_session_s_issue_says_today_s_forecast_is_missing():
    view = build("morning", (implied(MON),))  # only today's own issue exists: not today's forecast
    assert view.indices[0].today == ()
    assert "NIFTY: today's forecast is missing (none sealed on Fri 23 Oct)" in view.system


def test_the_morning_expects_scores_up_to_two_sessions_back_and_the_evening_up_to_the_previous_one():
    class UpToThursday(History):  # G13b's scores at 08:50 on Monday: Friday's close is not scored yet
        def points(self, underlying):
            return [p for p in super().points(underlying) if p.target_day <= SESSIONS.back(MON, 2)]

    morning = build("morning", (implied(FRI),), history=UpToThursday())
    evening = build("evening", (implied(FRI), implied(MON)), history=UpToThursday(), at_time=(20, 5))
    assert not any("stale" in line for line in morning.system)
    assert any("expected 2026-10-23 (stale)" in line for line in evening.system)


def test_the_evening_checks_today_s_forecast_on_today_s_close_as_read_and_labels_it():
    view = build("evening", (implied(FRI), implied(MON)), read=25390.0, at_time=(20, 5))
    (index,) = view.indices
    last = index.horizons[0].timeline.points[-1]
    assert (last.day, last.close, last.inside_50, last.inside_90, last.provisional) == (MON, 25390.0, True, True, True)
    assert (index.price, index.price_at) == (25390.0, "close today") and index.scored == 30
    line = slack_lines(view)[1]
    assert line.startswith("*NIFTY* · today closed 25,390.00 (NSE's close; the official file confirms it tomorrow): "
                           "✓ Correct · tomorrow: most likely")  # fmt: skip


def test_a_close_call_and_a_miss_get_their_words():
    close_call = build("evening", (implied(FRI), implied(MON)), read=25500.0, at_time=(20, 5))
    missed = build("evening", (implied(FRI), implied(MON)), read=25700.0, at_time=(20, 5))
    assert "⚠ Close call" in slack_lines(close_call)[1] and "✗ Missed" in slack_lines(missed)[1]
    assert missed.indices[0].wrong_days[0] == MON


def test_an_evening_without_today_s_close_checks_nothing_and_says_why():
    view = build("evening", (implied(FRI), implied(MON)), at_time=(20, 5))
    points = view.indices[0].horizons[0].timeline.points
    assert points[-1].day == HISTORY_DAYS[-1] and not any(p.provisional for p in points)
    said = ("NIFTY: today's close was not read (NSE's index list did not answer); today is not checked here, and its "
            "result appears in tomorrow evening's report, once G13b scores NSE's official close")
    assert said in view.system


def test_an_evening_without_a_forecast_for_today_checks_nothing_and_reads_no_close():
    view = build("evening", (implied(MON),), read=25390.0, at_time=(20, 5))
    assert not any(p.provisional for p in view.indices[0].horizons[0].timeline.points)
    assert not any("close was not read" in line for line in view.system)


def test_the_morning_never_shows_a_row_aimed_before_today():
    """A same-day row of the previous session (A22's N0, issued at 09:15 for that day) is not today's forecast."""
    rows = (*implied(FRI).rows, RangeRow("implied", "N0", FRI, QUANTILES, 0.5, STATUS_OK))
    (index,) = build("morning", (issue(FRI, rows=rows),)).indices
    assert [r.horizon for r in index.today] == ["N1", "N3"]


def test_the_evening_checks_only_a_forecast_aimed_at_today():
    """A record whose next-session row names another day (a data error) is not checked against today's close."""
    wrong = issue(FRI, rows=(RangeRow("implied", "N1", WED, QUANTILES, 0.5, STATUS_OK),))
    view = build("evening", (wrong, implied(MON)), read=25390.0, at_time=(20, 5))
    assert not any(p.provisional for p in view.indices[0].horizons[0].timeline.points)


def test_every_outcome_carries_its_gap_to_the_middle_so_the_page_never_computes_it():
    view = build("evening", (implied(FRI), implied(MON)), read=25390.0, at_time=(20, 5))
    last = view.indices[0].horizons[0].timeline.points[-1]
    assert (last.gap_points, last.gap_pct) == (90.0, round(90 / 25300 * 100, 3))
