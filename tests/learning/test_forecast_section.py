"""LR1's forecasts section: every number copied from the committed G4 and G8 reports, never recomputed."""

from fno.forecast_scoring.score_report import weekly_summary
from fno.learning.forecast_section import NO_G4, NO_V4, ForecastSection
from fno.learning.readers import ReportFolder
from fno.learning.week import build_week

from .fakes import SATURDAY, Calendar, g4_document, g8_document, write_report


def _section(tmp_path):
    return ForecastSection(ReportFolder(tmp_path / "v4", "v4"), ReportFolder(tmp_path / "g4", "g4"))


def test_v4_numbers_are_the_report_s_and_new_this_week_is_a_difference(tmp_path):
    write_report(tmp_path / "v4", "2026-10-10", g8_document(1900, "2026-10-10"))
    write_report(tmp_path / "v4", "2026-10-17", g8_document(1907))
    write_report(tmp_path / "v4", "2026-10-18", g8_document(9999))  # after the week: never read
    lines = _section(tmp_path).lines(build_week(Calendar(), SATURDAY))
    assert "Protocol v4 (G8 report v4/2026-10-17.json)" in lines
    assert "- v1_rv_next_session: not enough data yet, live forecasts 0" in lines
    assert "- v4_rv5_below_weekly_atm_iv: not started, live forecasts 0" in lines
    assert "  weather_vix_v1: n 1907, mean_brier 0.0391664" in lines
    assert "  base_rate: no scored outcome yet" in lines
    assert ("  weather_vix_v1 vs base_rate: scored 1907 (new this week 7), D -0.0083, relative improvement 0.1756; "
            "misses: 0 of 100 baseline days (0.0%), 0 of 5 2% days; input failures: 0") in lines  # fmt: skip


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
