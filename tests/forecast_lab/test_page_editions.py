"""FL1-1d: the page in its two editions. The morning shows the forecasts sealed the session before for today and the
next sessions, against the last official close; the evening checks today's forecast against today's close as read,
labelled provisional, and says plainly when no close was read. The newest scored session expected differs: G13b
scores the previous session only in the 14:33 routine, so at 08:50 it is two sessions back."""

from datetime import date

from fno.forecast_lab.page.builder import PageBuilder
from fno.forecast_lab.page.message import slack_lines
from fno.forecast_lab.page.model import CLOSE_NOT_READ, NO_FORECAST_TODAY, DayShape, TrackRecord
from fno.forecast_lab.ranges import STATUS_OK, Outcomes, RangeRow, TodayCloses

from .builders import QUANTILES, REPORT_DAY, SESSIONS, Forecasts, at, issue
from .test_page_builder import HISTORY_DAYS, History, NoFacts

FRI, MON, WED = date(2026, 10, 23), REPORT_DAY, date(2026, 10, 28)  # 26 Oct is a Monday; FRI its previous session
THU = date(2026, 10, 22)
RIGHT = "Right = the close fell inside the “almost certainly” range."


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
    def __init__(self, value=None, levels=None):
        self.value, self.found = value, levels or {}

    def levels(self, underlying, day):
        return self.found

    def close(self, underlying, day):
        return self.value

    def why_missing(self, day):
        return "NSE's index list did not answer"


def build(edition, issues, official=None, read=None, history=None, at_time=(8, 50), levels=None):
    pages = PageBuilder(Forecasts(issues), history or History(), NoFacts(), SESSIONS, underlyings=("NIFTY",),
                        official=Official(official or {}), today_closes=Read(read, levels))  # fmt: skip
    return pages.build(MON, at(MON, *at_time), edition)


def test_the_morning_shows_the_forecasts_sealed_for_today_and_the_outlook_against_the_last_official_close():
    view = build("morning", (implied(FRI),), official={FRI: 25310.5})
    (index,) = view.indices
    assert [(r.horizon, r.target_day, r.when) for r in index.today] == [
        ("N1", MON, "today"), ("N3", WED, "in 2 trading days, Wed 28 Oct")]  # fmt: skip
    assert (index.price, index.price_at) == (25310.5, "close Fri 23 Oct") and view.edition == "morning"
    assert slack_lines(view)[0] == f"*Today's forecast* (Mon 26 Oct, 08:50) {RIGHT}"


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
    evening = build("evening", (implied(THU), implied(FRI), implied(MON)), history=UpToThursday(), at_time=(20, 5))
    assert not any("stale" in line for line in morning.system)
    assert any("expected 2026-10-23 (stale)" in line for line in evening.system)
    unissued = build("evening", (implied(FRI), implied(MON)), history=UpToThursday(), at_time=(20, 5))
    assert any("no forecast was issued for 2026-10-23" in line for line in unissued.system)


def test_the_evening_checks_today_s_forecast_on_today_s_close_as_read_and_labels_it():
    view = build("evening", (implied(FRI), implied(MON)), read=25390.0, at_time=(20, 5))
    (index,) = view.indices
    last = index.horizons[0].timeline.points[-1]
    assert (last.day, last.close, last.inside_50, last.inside_90, last.provisional) == (MON, 25390.0, True, True, True)
    assert (index.price, index.price_at) == (25390.0, "close today") and index.scored == 30
    assert slack_lines(view)[1] == ("*NIFTY* today: closed 25,390.00 (NSE's close; the official file confirms it in "
                                    "tomorrow's morning report) | most likely 25,200–25,400 → ✅ inside | almost "
                                    "certainly 25,000–25,600 → ✅ inside → ✓ right")  # fmt: skip


def test_a_friday_evening_names_monday_s_morning_report_never_tomorrow():
    """FL1-1e: the 23 Oct evening said "tomorrow morning's report" on a Friday; Saturday has no session."""
    fri = PageBuilder(Forecasts((implied(THU),)), History(), NoFacts(), SESSIONS, underlyings=("NIFTY",),
                      today_closes=Read()).build(FRI, at(FRI, 20, 5), "evening")  # fmt: skip
    assert fri.next_session == MON and fri.indices[0].unchecked == CLOSE_NOT_READ
    assert slack_lines(fri)[1] == ("⚠️ *NIFTY* today: no verdict. Today's close could not be read (NSE's index list "
                                   "did not answer). The result comes in Monday's morning report.")  # fmt: skip
    assert any("today's result appears in Monday's morning report" in line for line in fri.system)


def test_a_close_call_and_a_miss_get_their_words():
    close_call = build("evening", (implied(FRI), implied(MON)), read=25500.0, at_time=(20, 5))
    missed = build("evening", (implied(FRI), implied(MON)), read=25700.0, at_time=(20, 5))
    assert slack_lines(close_call)[1].endswith("most likely 25,200–25,400 → ❌ outside by 100.00 points (above) | "
                                               "almost certainly 25,000–25,600 → ✅ inside → ✓ right")  # fmt: skip
    assert slack_lines(missed)[1].endswith("→ ❌ outside by 300.00 points (above) | almost certainly 25,000–25,600 → "
                                           "❌ outside by 100.00 points (above) → ✗ wrong")  # fmt: skip
    assert missed.indices[0].wrong_days[0] == MON


def test_an_evening_without_today_s_close_checks_nothing_and_says_why():
    view = build("evening", (implied(FRI), implied(MON)), at_time=(20, 5))
    points = view.indices[0].horizons[0].timeline.points
    assert points[-1].day == HISTORY_DAYS[-1] and not any(p.provisional for p in points)
    said = (
        "NIFTY: today's close was not read (NSE's index list did not answer); today's result appears in tomorrow's "
        "morning report once NSE's official close is archived"
    )
    assert said in view.system and view.indices[0].unchecked == CLOSE_NOT_READ


def test_an_evening_without_a_forecast_for_today_checks_nothing_and_reads_no_close():
    view = build("evening", (implied(MON),), read=25390.0, at_time=(20, 5))
    assert not any(p.provisional for p in view.indices[0].horizons[0].timeline.points)
    assert not any("close was not read" in line for line in view.system)
    assert view.indices[0].unchecked == NO_FORECAST_TODAY
    assert slack_lines(view)[1] == ("❌ *NIFTY* today: no verdict. No forecast was issued for today (the Fri 23 Oct "
                                    "15:45 issue holds no next-session forecast for Mon 26 Oct), so there is nothing "
                                    "to check.")  # fmt: skip


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


class UpToThursday(History):
    """G13b's scores at 08:50 on Monday: Friday's close is not scored yet."""

    def points(self, underlying):
        return [p for p in super().points(underlying) if p.target_day <= THU]


def test_the_morning_checks_the_previous_session_on_its_official_close_when_not_scored_yet():
    view = build("morning", (implied(THU), implied(FRI)), official={FRI: 25390.0}, history=UpToThursday())
    (index,) = view.indices
    assert (index.result.day, index.result.close, index.result.provisional) == (FRI, 25390.0, False)
    assert index.horizons[0].timeline.points[-1] == index.result and index.scored == 30
    assert slack_lines(view)[1].startswith("*NIFTY* · Fri 23 Oct: closed 25,390.00 (NSE's official close; G13b's "
                                           "score follows) · inside “most likely”: yes · inside “almost certainly”: "
                                           "yes → ✓ right · today: most likely")  # fmt: skip
    assert view.indices[0].unchecked == ""  # the morning never says "not checked yet" of today


def test_the_morning_does_not_check_a_session_already_scored_or_without_its_official_close():
    scored = build("morning", (implied(THU), implied(FRI)), official={FRI: 25390.0})  # History scores Friday
    assert scored.indices[0].result is None
    unarchived = build("morning", (implied(THU), implied(FRI)), history=UpToThursday())
    assert unarchived.indices[0].result is None


def test_the_evening_carries_the_day_s_path_and_the_record_live_and_back_tested_apart():
    """FL1-1f: the day's levels from the close reader, the previous session's official close, and the record."""
    levels = {"open": 25350.0, "high": 25420.0, "low": 25280.0}
    view = build("evening", (implied(FRI), implied(MON)), {FRI: 25310.5}, 25390.0, at_time=(20, 5), levels=levels)
    (index,) = view.indices
    assert index.shape == DayShape(25350.0, 25420.0, 25280.0, 25310.5)
    assert index.track == TrackRecord(1, 1, 29, 29, 30, 1)  # the last 30 sessions: 29 back-tested and today, live
    lines = slack_lines(view)
    assert lines[2] == ("Day (measured): opened 25,350 (+40 on the previous close), ranged 25,280–25,420, closed "
                        "25,390; the forecast's centre was 25,300 and its “most likely” width 200 points.")  # fmt: skip
    assert lines[3].startswith("Size (measured): swing 140 points = 0.7× the “most likely” width; close 210 points "
                               "inside the nearest “almost certainly” edge, comfortable")  # fmt: skip
    assert lines[4] == "Context (measured): no notable moves in our data."  # no Sections in this build
    assert lines[5] == ("⚪ too few live days to rate | Live so far: 1 day, inside “almost certainly” 1 of 1 | "
                        "Back-test (29 of the last 30 days): 29 of 29")  # fmt: skip
    assert lines[6].startswith("Next: tomorrow: most likely")


def test_the_morning_and_a_day_without_a_check_carry_no_day_path():
    assert build("morning", (implied(FRI),), {FRI: 25310.5}, levels={"open": 1.0}).indices[0].shape is None
    checked = build(
        "morning", (implied(THU), implied(FRI)), {FRI: 25390.0}, history=UpToThursday(), levels={"open": 1.0}
    )
    assert checked.indices[0].result is not None and checked.indices[0].shape is None  # the morning's check: no path
    unread = build("evening", (implied(FRI), implied(MON)), at_time=(20, 5), levels={"open": 1.0}).indices[0]
    assert unread.shape is None and unread.unchecked_why == "NSE's index list did not answer"
