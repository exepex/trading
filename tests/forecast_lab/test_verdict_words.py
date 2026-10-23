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
    assert track_record(points) == TrackRecord(2, 1, 28, 27, 30, 1)  # the window: the last 30 sessions


def test_missing_context_says_not_available_with_each_reason_and_a_quiet_day_says_so():
    """Orchestrator, 23 Oct: the real build prints measured values, never a placeholder."""
    quiet = (Cue(QUIET, text=QUIET),)
    why = ("Nasdaq-100: no reading yet (the last one is too old to use)", "USD/INR (RBI): the read failed (OSError)")
    lines = top_block(checked(1100.0, why=quiet), DAY, MON, why)
    assert ("Context: not available (Nasdaq-100: no reading yet (the last one is too old to use); USD/INR (RBI): the "
            "read failed (OSError)).") in lines  # fmt: skip
    assert "Context (measured): no notable moves in our data." in top_block(checked(1100.0, why=quiet), DAY, MON)


def test_the_message_passes_the_evening_s_missing_sources_and_never_the_morning_only_ones():
    from fno.forecast_lab.page.cues import FAILED, NOT_AVAILABLE, NOT_OUT_YET, SectionView
    from fno.forecast_lab.page.message import slack_lines
    from fno.forecast_lab.page.model import PageView

    cues = (SectionView("Brent", NOT_OUT_YET, why="Brent: no reading yet (nothing recorded)"),
            SectionView("GIFT Nifty", NOT_AVAILABLE, why="GIFT Nifty is a pre-open cue: the morning edition only"),
            SectionView("Flags", FAILED, why="Flags: the read failed (OSError)"))  # fmt: skip
    view = PageView(DAY, "Live, sealed", (checked(1100.0),), (), cues=cues, next_session=MON)
    assert ("Context: not available (Brent: no reading yet (nothing recorded); Flags: the read failed (OSError)).") in (
        slack_lines(view)
    )


def test_the_page_gets_each_piece_as_plain_words_without_slack_s_bold():
    """The designer's page lays each piece out as its own row (FL1-1f): no "*NIFTY*" markup in any piece."""
    from fno.forecast_lab.page import verdict_words as words
    from fno.forecast_lab.page.model import NO_FORECAST_TODAY

    assert (words.edge_words(1000.0, 1000.4, 1199.6), words.range_words(1000.4, 1199.6)) == (
        "❌ outside by 0.40 points (below)", "1,000–1,200")  # fmt: skip
    hit = checked(1100.0, DayShape(1100.0, 1110.0, 1090.0, 1090.0), why=(Cue("Brent", 80.0, 1.5, "%"),))
    assert words.day_line(hit).startswith("Day (measured): opened 1,100 (+10 on the previous close)")
    assert words.size_line(hit).startswith("Size (measured): swing 20 points")
    assert words.cause_lines(hit) == ["Context (measured, not a cause): Brent +1.50%."]
    none = replace(index(), unchecked=NO_FORECAST_TODAY, unchecked_why="no issue")
    said = "❌ today: no verdict. No forecast was issued for today (no issue), so there is nothing to check."
    assert words.no_verdict_words(none, DAY, MON) == said
    assert words.no_verdict_line(none, DAY, MON).startswith("❌ *NIFTY* today: no verdict.")
    assert not any(
        "*" in piece for piece in (words.day_line(hit), words.size_line(hit), words.no_verdict_words(none, DAY, MON))
    )


def test_judge_547_f1_thirty_back_filled_then_ten_live_counts_only_the_last_30_sessions():
    """Judge 547 F1's probe: the back-test counts among the last 30 sessions, never the 30 before the live ones."""
    from fno.forecast_lab.page.plain import record_words
    from fno.forecast_lab.page.today_view import track_record

    points = [Outcome(DAY, 1100.0, BAND, True, True, False)] * 30 + [Outcome(DAY, 1100.0, BAND, True, True, True)] * 10
    track = track_record(points)
    assert track == TrackRecord(10, 10, 20, 20, 30, 10)
    assert record_words(replace(index(), track=track)).endswith("| Back-test (20 of the last 30 days): 20 of 20")


def test_judge_547_f2_one_live_day_never_shows_a_colour_before_the_live_count():
    """Judge 547 F2: a green light from mostly back-tested days never stands before "Live so far"."""
    one_live = replace(checked(1100.0), right=29, scored=30, track=TrackRecord(1, 1, 29, 28, 30, 1))
    record = "Live so far: 1 day, inside “almost certainly” 1 of 1 | Back-test (29 of the last 30 days): 28 of 29"
    assert top_block(one_live, DAY, MON)[-1] == f"⚪ too few live days to rate | {record}"
