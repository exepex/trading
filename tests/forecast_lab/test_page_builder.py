"""FL1-1c: the page's numbers from live sources: the method with the lowest next-session error, the light over the
last 30 sessions, today's ranges from the written issue (its seal is judged elsewhere), and a missing issue or stale
scores as a system problem."""

from datetime import date

from fno.forecast_lab.page.builder import PageBuilder
from fno.forecast_lab.page.facts import FactsSource
from fno.forecast_lab.page.history import HistorySource
from fno.forecast_lab.page.reasons import Facts
from fno.forecast_lab.ranges import STATUS_OK, RangeRow

from .builders import QUANTILES, REPORT_DAY, SESSIONS, Forecasts, at, issue
from .page_builders import point

HISTORY_DAYS = [d for d in (date(2026, 9, 1).fromordinal(date(2026, 9, 1).toordinal() + i) for i in range(60))
                if SESSIONS.is_regular(d) and d < REPORT_DAY][-35:]  # fmt: skip


class History(HistorySource):
    def __init__(self, misses=0, live_last=0):
        self.misses, self.live_last = misses, live_last

    def points(self, underlying):
        out = []
        for i, day in enumerate(HISTORY_DAYS):
            inside = i < len(HISTORY_DAYS) - self.misses
            out.append(point("rv20", day, 1000.0, error=6.0, inside=(inside, inside)))
            live = i >= len(HISTORY_DAYS) - self.live_last
            out.append(point("implied", day, 1000.0, error=4.0, inside=(inside, inside), live=live))
        return out


class NoFacts(FactsSource):
    def facts(self, day):
        return Facts()


def build(forecasts, misses=0, live_last=0):
    builder = PageBuilder(forecasts, History(misses, live_last), NoFacts(), SESSIONS, underlyings=("NIFTY",))
    return builder.build(REPORT_DAY, at(REPORT_DAY, 15, 47))


def test_the_lowest_error_method_is_shown_with_today_s_written_ranges_and_the_30_day_light():
    rows = tuple(RangeRow(m, h, date(2026, 10, 27), QUANTILES, 0.5, STATUS_OK) for m in ("implied", "rv20")
                 for h in ("N1", "N3"))  # fmt: skip
    view = build(Forecasts((issue(REPORT_DAY, at(REPORT_DAY, 15, 46), rows=rows),)), misses=5)
    (index,) = view.indices
    assert index.method == "implied" and (index.right, index.scored) == (25, 30)
    assert [(r.horizon, r.band.q50) for r in index.today] == [("N1", 25300.0), ("N3", 25300.0)]
    assert index.price == 25250.0 and len(index.horizons[0].timeline.points) == len(HISTORY_DAYS)
    assert view.system == () and (index.light, index.light_word) == ("green", "Good")
    assert index.wrong_days == tuple(reversed(HISTORY_DAYS[-5:]))  # newest first
    assert [r.when for r in index.today] == ["tomorrow", "tomorrow"]  # the words follow each row's own target day


def test_a_missing_issue_is_a_system_problem_and_the_page_still_shows_the_history():
    view = build(Forecasts(()))
    assert view.system == ("NIFTY: today's forecast is missing (none written by 15:47)",)
    assert view.indices[0].today == () and view.indices[0].scored == 30


def test_scores_older_than_the_previous_session_are_stale_data():
    class Old(History):
        def points(self, underlying):
            return [p for p in super().points(underlying) if p.target_day < HISTORY_DAYS[-2]]

    builder = PageBuilder(Forecasts(()), Old(), NoFacts(), SESSIONS, underlyings=("NIFTY",))
    system = builder.build(REPORT_DAY, at(REPORT_DAY, 15, 47)).system
    assert any(line.startswith("NIFTY: newest scored close is") and line.endswith("(stale)") for line in system)


def test_the_record_counts_the_back_tested_days_in_its_window():
    (index,) = build(Forecasts(()), live_last=4).indices
    assert (index.scored, index.backtested, index.live_days) == (30, 26, 4)


def test_a_score_for_the_report_day_itself_is_never_in_the_history():
    class WithToday(History):
        def points(self, underlying):
            return super().points(underlying) + [point("implied", REPORT_DAY, 1000.0, error=1.0, inside=(False, False))]

    builder = PageBuilder(Forecasts(()), WithToday(), NoFacts(), SESSIONS, underlyings=("NIFTY",))
    (index,) = builder.build(REPORT_DAY, at(REPORT_DAY, 15, 47)).indices
    assert index.horizons[0].timeline.points[-1].day == HISTORY_DAYS[-1] and index.right == 30  # judge 434 Q10
