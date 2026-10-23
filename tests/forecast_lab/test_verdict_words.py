"""FL1-1f: the evening's top block per index (owner, 23 Oct 2026: readable in 30 seconds): the verdict against the
forecast's own edges, inside or outside by how many points; why, from measured facts only, each line labelled; a miss
without a measured cause says so and never guesses; context is never a cause. Made-up levels only."""

from dataclasses import replace
from datetime import date

from fno.forecast_lab.page.cues import Cue
from fno.forecast_lab.page.keypoints import QUIET, REASON
from fno.forecast_lab.page.model import Band, DayShape, Outcome, TrackRecord
from fno.forecast_lab.page.reasons import NO_REASON
from fno.forecast_lab.page.verdict_words import top_block

from .page_builders import index

DAY, MON = date(2026, 10, 23), date(2026, 10, 26)
BAND = Band(1000.4, 1050.0, 1100.0, 1150.0, 1199.6)


def checked(close, shape=None, why=()):
    result = Outcome(DAY, close, BAND, BAND.q25 <= close <= BAND.q75, BAND.q05 <= close <= BAND.q95, True, True)
    return replace(index(), result=result, shape=shape, why=why)


def test_the_verdict_uses_the_forecast_s_own_edges_so_a_close_just_outside_is_never_shown_inside():
    (line, *_) = top_block(checked(1000.0), DAY, MON)
    assert line.endswith("| almost certainly 1,000–1,200 → ❌ outside by 0.40 points (below) → ✗ wrong")


def test_a_hit_is_called_narrow_within_a_quarter_of_the_half_width_of_its_edge_else_comfortable():
    narrow = top_block(checked(1020.0, DayShape(1100.0, 1110.0, 1015.0, 1090.0)), DAY, MON)
    comfortable = top_block(checked(1100.0, DayShape(1100.0, 1110.0, 1090.0, 1090.0)), DAY, MON)
    assert "close 20 points inside the nearest “almost certainly” edge, narrow" in narrow[2]
    assert "close 100 points inside the nearest “almost certainly” edge, comfortable" in comfortable[2]
    assert narrow[2].startswith("Size (measured): swing 95 points = 0.9× the “most likely” width;")


def test_a_miss_names_only_measured_reasons_and_otherwise_says_there_is_no_measured_cause():
    said = top_block(checked(1250.0, why=(Cue(REASON, text="India VIX jumped from 14.0 to 16.1"),)), DAY, MON)
    assert "Missed because (measured): India VIX jumped from 14.0 to 16.1." in said
    unexplained = top_block(checked(1250.0, why=(Cue(REASON, text=NO_REASON),)), DAY, MON)
    assert "Missed (reasoning): no measured cause in our data, so likely noise." in unexplained


def test_context_is_labelled_never_a_cause_and_the_quiet_marker_is_not_a_cue():
    why = (Cue("Brent", 80.0, -0.85, "%"), Cue(QUIET, text=QUIET), Cue("USD/INR", None, None))
    lines = top_block(checked(1100.0, why=why), DAY, MON)
    assert "Context (measured, not a cause): Brent -0.85%." in lines
    assert not any(QUIET in line for line in lines)


def test_the_day_s_path_shows_only_the_levels_recorded():
    lines = top_block(checked(1100.0, DayShape(None, None, None, None)), DAY, MON)
    assert lines[1] == ("Day (measured): closed 1,100; the forecast's centre was 1,100 and its “most likely” width "
                        "100 points.")  # fmt: skip
    assert not lines[2].startswith("Size (measured): swing")


def test_the_record_counts_every_live_check_and_only_back_tested_sessions_in_its_window():
    from fno.forecast_lab.page.today_view import track_record

    def point(live, inside=True):
        return Outcome(DAY, 1100.0 if inside else 1300.0, BAND, inside, inside, live)

    points = [point(False)] * 29 + [point(True, False), point(False, False), point(True)]
    assert track_record(points) == TrackRecord(2, 1, 30, 29)
