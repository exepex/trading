"""LR1's forecasts section: every number copied from the committed G4 and G8 reports, never recomputed."""

from fno.forecast_scoring.score_report import weekly_summary
from fno.learning.forecast_section import NO_G4, NO_V4, ForecastSection
from fno.learning.readers import ReportFolder
from fno.learning.week import build_week

from .fakes import SATURDAY, Calendar, g4_document, g8_document, legacy_g8_document, write_report


def _section(tmp_path):
    return ForecastSection(ReportFolder(tmp_path / "v4", "v4"), ReportFolder(tmp_path / "g4", "g4"))


MISSES = "misses: 0 of 100 baseline days (0.0%), 0 of 5 2% days; input failures: 0"
BACKFILL = "  close-proxy cohort (back-fill, exploratory: does not count):"


def _v6_lines(lines, live):
    return lines[lines.index(f"- v6_abs_move_2pct_next_session: scored, live forecasts {live}") + 1 :]


def test_both_cohorts_show_labelled_each_with_its_own_new_this_week_and_exact_numbers(tmp_path):
    write_report(tmp_path / "v4", "2026-10-10", g8_document(1900, "2026-10-10", live=1))
    write_report(tmp_path / "v4", "2026-10-17", g8_document(1907))
    write_report(tmp_path / "v4", "2026-10-18", g8_document(9999))  # after the week: never read
    lines = _section(tmp_path).lines(build_week(Calendar(), SATURDAY))
    assert "Protocol v4 (G8 report v4/2026-10-17.json)" in lines
    assert "- v1_rv_next_session: not enough data yet, live forecasts 0" in lines
    assert "- v4_rv5_below_weekly_atm_iv: not started, live forecasts 0" in lines
    assert _v6_lines(lines, 3)[:7] == [
        BACKFILL, "    weather_vix_v1: n 1907, mean_brier 0.0391664", "    base_rate: no scored outcome yet",
        "    weather_vix_v1 vs base_rate: scored 1907 (new this week 7), D -0.0083, relative improvement 0.1756; "
        + MISSES,
        "  live cohort:", "    weather_vix_v1: n 3, mean_brier 0.02",
        "    weather_vix_v1 vs base_rate: scored 3 (new this week 2), D -0.0083, relative improvement 0.1756; "
        + MISSES,
    ]  # fmt: skip


def test_with_only_back_fill_rows_both_cohorts_show_and_live_has_no_rows_yet(tmp_path):
    write_report(tmp_path / "v4", "2026-10-17", g8_document(1907, live=0))
    lines = _v6_lines(_section(tmp_path).lines(build_week(Calendar(), SATURDAY)), 0)
    assert lines[0] == BACKFILL and lines[4] == "  live cohort: no rows yet"


def test_an_old_shape_previous_report_compares_like_for_like_with_the_back_fill_cohort(tmp_path):
    write_report(tmp_path / "v4", "2026-10-10", legacy_g8_document(1900, "2026-10-10"))  # before G10: no live rows
    write_report(tmp_path / "v4", "2026-10-17", g8_document(1907))
    lines = _v6_lines(_section(tmp_path).lines(build_week(Calendar(), SATURDAY)), 3)
    assert "scored 1907 (new this week 7)" in lines[3] and "scored 3 (new this week 3)" in lines[6]


def test_an_old_shape_latest_report_still_shows_as_back_fill(tmp_path):
    write_report(tmp_path / "v4", "2026-10-17", legacy_g8_document(1907, "2026-10-17"))
    lines = _v6_lines(_section(tmp_path).lines(build_week(Calendar(), SATURDAY)), 0)
    assert lines[:2] == [BACKFILL, "    weather_vix_v1: n 1907, mean_brier 0.04"]


def test_the_first_report_says_so(tmp_path):
    write_report(tmp_path / "v4", "2026-10-17", g8_document(1907))
    lines = _section(tmp_path).lines(build_week(Calendar(), SATURDAY))
    assert any("scored 1907 (first report)" in line for line in lines)


def test_g4_part_is_weekly_summary_line_for_line(tmp_path):
    write_report(tmp_path / "g4", "2026-10-16", g4_document())
    lines = _section(tmp_path).lines(build_week(Calendar(), SATURDAY))
    start = lines.index("Protocol v1-v3 (G4 report g4/2026-10-16.json)") + 1
    assert lines[start:] == weekly_summary(g4_document())


def test_no_reports_give_their_lines(tmp_path):
    lines = _section(tmp_path).lines(build_week(Calendar(), SATURDAY))
    assert lines == ["*Forecasts*", NO_V4, NO_G4]


def test_lr1_reads_the_cohort_report_g8_actually_writes(tmp_path):
    """The contract, end to end: G8's own report_json (a live and a back-fill row on one question) read by LR1."""
    from datetime import date

    from fno.constants import V6_BIG_MOVE_1S
    from fno.forecast_scoring.v4.days import DayCounts
    from fno.forecast_scoring.v4.inputs import ForecastValue, Outcome, V4ForecastSource, V4OutcomeSource
    from fno.forecast_scoring.v4.records import NoRegistrations
    from fno.forecast_scoring.v4.render import report_json
    from fno.forecast_scoring.v4.scoring import QUESTIONS, V4Scoring

    days = [date(2026, 10, 12), date(2026, 10, 13)]  # 12 Oct back-fill, 13 Oct live

    class Files(V4ForecastSource):
        def forecasters(self, question):
            return ["base_rate", "weather_vix_v1"] if question == V6_BIG_MOVE_1S else []

        def values(self, question, forecaster):
            return {d: ForecastValue(0.1 if forecaster == "base_rate" else 0.2, d == days[1]) for d in days}

    class Outcomes(V4OutcomeSource):
        def outcomes(self, question):
            return {d: Outcome(False, False, 14.0, 0.001) for d in days}

    scoring = V4Scoring(Files(), Outcomes(), NoRegistrations())
    document = report_json([scoring.question_report(q) for q in QUESTIONS], False, "2026-10-17", DayCounts(0, 0, 0, 0))
    write_report(tmp_path / "v4", "2026-10-17", document)
    lines = _section(tmp_path).lines(build_week(Calendar(), SATURDAY))
    v6 = lines[lines.index("- v6_abs_move_2pct_next_session: scored, live forecasts 2") + 1 :]
    assert v6[0] == BACKFILL and v6[1].startswith("    base_rate: n 1,")
    assert v6[3].startswith("    weather_vix_v1 vs base_rate: scored 1 (first report)")
    assert v6[4] == "  live cohort:" and v6[7].startswith("    weather_vix_v1 vs base_rate: scored 1 (first report)")
