"""Story FL1-1's report text (judge 422): the seal check of each target day runs on its own day, whatever the close's
state; the match comes once the close is archived, in a later report; a missed day or a late archive is taken up by a
later report, never skipped and never alerted twice; FL1 counts regular sessions only, as G13b does."""

from dataclasses import replace
from datetime import date

from fno.forecast_lab.ranges import RangeRow
from fno.forecast_lab.scoreboard import scoreboard_lines, trust_line

from .builders import (
    CALENDAR,
    DAY,
    N1_ISSUE,
    N3_ISSUE,
    QUANTILES,
    REPORT_DAY,
    SESSIONS,
    Closes,
    Forecasts,
    Records,
    at,
    issue,
    lab,
    on_time,
    score,
    scored,
)

SCORES = (score(N1_ISSUE, "N1", qs=12.5), score(N3_ISSUE, "N3", qs=30.25, inside=(False, True)))
MATCH_23 = (
    "NIFTY match: the forecasts for 2026-10-23 against its official close; the latest days are matched in a later "
    "report (NSE archives the close in the evening)"
)
MATCHED_N1 = "close 25350.00: 25-75 in, 5-95 in, median direction right, quantile score 12.50"
NOT_READY_23 = (
    "NIFTY: the official close of 2026-10-23 is archived but G13b has not scored all its forecasts yet; its match "
    "comes in a later report"
)
LATE_N1 = (
    "NIFTY N1 for 2026-10-23 (issued 2026-10-22): sealed late (2026-10-23 09:16:00+05:30); not shown as a forecast"
)


def test_forecasts_sealed_in_time_are_matched_with_g13bs_own_scores_and_the_trust_line():
    today = issue(REPORT_DAY, at(REPORT_DAY, 15, 46))  # pushed before the report's 15:47
    forecasts = Forecasts((*on_time(DAY, REPORT_DAY), today), SCORES, days={"NIFTY": [N1_ISSUE, DAY]})
    run, poster, alerts = lab(forecasts)
    run.run(REPORT_DAY)
    (text,) = poster.posts
    assert MATCH_23 in text and " N1, issued 2026-10-22 15:45 at 25250.00:" in text
    assert MATCHED_N1 in text
    assert "close 25350.00: 25-75 out, 5-95 in, median direction right, quantile score 30.25" in text  # G13b's numbers
    assert "NIFTY forecasts for 2026-10-26: every one sealed in time" in text
    assert "  N1 (2026-10-27) rv20: 5/25/50/75/95 25000/25200/25300/25400/25600, P(up) 0.55" in text
    assert "Trust: 2 scored trading day(s) of about 60 needed to judge calibration" in text
    assert alerts.sent == []


def test_a_late_seal_is_alerted_on_its_day_before_the_close_exists_and_matched_once_in_the_next_report():
    """Judge 422's two-day probe: closes archived only the next day; the late N1 is alerted once, on day d."""
    forecasts = Forecasts((issue(N1_ISSUE, at(DAY, 9, 16)), *on_time(REPORT_DAY), issue(N3_ISSUE)), SCORES)
    records = Records()
    first, poster, alerts = lab(forecasts, records=records, closes=Closes(archived=()), today=DAY)
    first.run(DAY)
    assert alerts.sent == [f"F&O forecast lab 2026-10-23: {LATE_N1}"] and LATE_N1 in poster.posts[0]
    second, poster, alerts = lab(forecasts, records=records, closes=Closes(archived=(DAY,)))
    second.run(REPORT_DAY)
    (text,) = poster.posts
    assert alerts.sent == [] and LATE_N1 not in text and MATCH_23 in text
    assert " N1, issued 2026-10-22: no forecast sealed in time (its seal check said why)" in text
    assert "quantile score 30.25" in text and records.reports[REPORT_DAY].matched == ("NIFTY 2026-10-23",)
    third_day = SESSIONS.next(REPORT_DAY)
    later = Forecasts((*forecasts.issues.values(), *on_time(third_day)), (*SCORES, *scored(REPORT_DAY)))
    third, poster, alerts = lab(later, records=records,
                                closes=Closes((DAY, REPORT_DAY)), today=third_day)  # fmt: skip
    third.run(third_day)
    assert records.reports[third_day].matched == ("NIFTY 2026-10-26",) and MATCH_23 not in poster.posts[0]


def test_a_day_whose_scores_are_not_ready_is_not_matched_and_a_later_report_matches_it_with_them():
    """Judge 422.1's probe: 23 Oct's close is archived by the 26 Oct report but G13b's score step has not run (or ran
    late, or only partly); the day waits, and the 27 Oct report shows it with its scores."""
    records, issues = Records(), on_time(DAY, REPORT_DAY, SESSIONS.next(REPORT_DAY))
    partly = Forecasts(issues, SCORES[:1])  # the N1 row scored, the N3 row not yet
    run, poster, _ = lab(partly, records=records)
    run.run(REPORT_DAY)
    assert NOT_READY_23 in poster.posts[0] and MATCHED_N1 not in poster.posts[0]
    assert records.reports[REPORT_DAY].matched == ()
    later = SESSIONS.next(REPORT_DAY)
    run, poster, _ = lab(Forecasts(issues, (*SCORES, *scored(REPORT_DAY))), records=records,
                         closes=Closes((DAY, REPORT_DAY)), today=later)  # fmt: skip
    run.run(later)
    assert MATCH_23 in poster.posts[0] and MATCHED_N1 in poster.posts[0] and "quantile score 30.25" in poster.posts[0]
    assert records.reports[later].matched == ("NIFTY 2026-10-23", "NIFTY 2026-10-26")


def test_a_forecast_with_one_of_its_rows_unscored_is_not_ready():
    rows = (RangeRow("rv20", "N1", DAY, QUANTILES, 0.55, "ok"), RangeRow("implied", "N1", DAY, QUANTILES, 0.5, "ok"))
    forecasts = Forecasts((issue(N1_ISSUE, rows=rows), issue(N3_ISSUE), *on_time(REPORT_DAY)), SCORES)  # rv20 only
    run, poster, _ = lab(forecasts)
    run.run(REPORT_DAY)
    assert NOT_READY_23 in poster.posts[0]


def test_a_missed_report_day_is_checked_and_matched_by_the_next_report():
    forecasts = Forecasts(on_time(N1_ISSUE, DAY, REPORT_DAY), scored(N1_ISSUE, DAY))
    records = Records()
    run, poster, alerts = lab(forecasts, records=records, closes=Closes((N1_ISSUE, DAY)), first_day=N1_ISSUE)
    run.run(REPORT_DAY)  # no report on 22 or 23 Oct
    written = records.reports[REPORT_DAY]
    assert written.checked == ("NIFTY 2026-10-22", "NIFTY 2026-10-23", "NIFTY 2026-10-26")
    assert written.matched == ("NIFTY 2026-10-22", "NIFTY 2026-10-23") and alerts.sent == []


def test_a_close_archived_late_is_matched_by_a_later_report():
    forecasts = Forecasts(on_time(DAY, REPORT_DAY, SESSIONS.next(REPORT_DAY)), scored(DAY, REPORT_DAY))
    records = Records()
    run, poster, _ = lab(forecasts, records=records, closes=Closes(archived=()))
    run.run(REPORT_DAY)
    expected = "NIFTY: the official close of 2026-10-23 is not archived yet; its match comes in a later report"
    assert expected in poster.posts[0] and records.reports[REPORT_DAY].matched == ()
    later = SESSIONS.next(REPORT_DAY)
    run, poster, _ = lab(forecasts, records=records, closes=Closes((DAY, REPORT_DAY)), today=later)
    run.run(later)
    assert records.reports[later].matched == ("NIFTY 2026-10-23", "NIFTY 2026-10-26") and MATCH_23 in poster.posts[0]


def test_the_seal_deadline_is_the_next_regular_session_s_open_after_the_issue_day_not_the_target_s():
    """The story's rule and G13b's deadline: an N3 issued 19 Oct is late after 21 Oct's 09:15 (20 Oct is a holiday),
    though still before its target's (23 Oct's) open; a seal on the holiday itself is in time."""
    late_n3 = issue(N3_ISSUE, at(date(2026, 10, 21), 9, 16))
    run, poster, alerts = lab(Forecasts((issue(N1_ISSUE), late_n3, *on_time(REPORT_DAY)), SCORES))
    run.run(REPORT_DAY)
    assert alerts.sent == ["F&O forecast lab 2026-10-26: NIFTY N3 for 2026-10-23 (issued 2026-10-19): sealed late "
                           "(2026-10-21 09:16:00+05:30); not shown as a forecast"]  # fmt: skip
    on_holiday = issue(N3_ISSUE, at(date(2026, 10, 20), 10, 0))
    run, _, alerts = lab(Forecasts((issue(N1_ISSUE), on_holiday, *on_time(REPORT_DAY)), SCORES))
    run.run(REPORT_DAY)
    assert alerts.sent == []


def test_g13bs_own_late_verdict_makes_an_issue_late_even_with_a_push_time_in_time():
    flagged = replace(issue(N1_ISSUE), late=True)
    run, poster, alerts = lab(Forecasts((flagged, issue(N3_ISSUE), *on_time(REPORT_DAY)), SCORES))
    run.run(REPORT_DAY)
    assert "NIFTY N1 for 2026-10-23 (issued 2026-10-22): sealed late (2026-10-22 15:50:00+05:30)" in poster.posts[0]
    assert len(alerts.sent) == 1  # pushed in time, but G13b's own verdict says late


def test_an_issue_with_no_push_evidence_is_late():
    no_evidence = replace(issue(N1_ISSUE), sealed_at=None)
    run, poster, _ = lab(Forecasts((no_evidence, issue(N3_ISSUE), *on_time(REPORT_DAY)), SCORES))
    run.run(REPORT_DAY)
    assert "sealed late (no push evidence)" in poster.posts[0]


def test_today_s_issue_is_shown_only_once_pushed_by_the_report_s_time():
    for sealed, shown in ((at(REPORT_DAY, 20, 4), True), (at(REPORT_DAY, 20, 6), False)):
        run, poster, _ = lab(Forecasts((*on_time(DAY, REPORT_DAY), issue(REPORT_DAY, sealed)), SCORES))
        run.run(REPORT_DAY)  # the evening report is built at 20:05
        assert ("NIFTY next sessions: today's 15:45 issue is not sealed yet; not shown" in poster.posts[0]) is not shown


def test_only_an_ok_row_of_the_same_issue_day_is_matched():
    failed = RangeRow("rv20", "N1", DAY, QUANTILES, 0.55, "failed", "no chain")
    rows = (failed,)
    forecasts = Forecasts((issue(N1_ISSUE, rows=rows), issue(N3_ISSUE), *on_time(REPORT_DAY)), SCORES)
    run, poster, _ = lab(forecasts)
    run.run(REPORT_DAY)
    assert MATCHED_N1 not in poster.posts[0]  # a non-ok row is never matched
    other_day = Forecasts((*on_time(DAY, REPORT_DAY),), (score(N3_ISSUE, "N1"), SCORES[1]))
    run, poster, _ = lab(other_day)
    run.run(REPORT_DAY)
    assert NOT_READY_23 in poster.posts[0]  # a score of another issue day never stands in for the N1 row's


def test_no_forecast_issued_before_g13b_s_first_live_day_is_expected_so_go_live_raises_no_false_alert():
    """G13b live from 23 Oct: 23 Oct's N1 (issued 22 Oct) and N3 (19 Oct) cannot exist, nor 26 Oct's N3 (21 Oct)."""
    run, poster, alerts = lab(Forecasts((issue(DAY),)), issues_from=DAY)
    run.run(REPORT_DAY)
    none = "NIFTY forecasts for 2026-10-23: none expected (issued before G13b's first live day)"
    assert alerts.sent == [] and none in poster.posts[0]
    assert "NIFTY forecasts for 2026-10-26: every one sealed in time" in poster.posts[0]
    run, _, alerts = lab(Forecasts(()), issues_from=DAY)
    run.run(REPORT_DAY)
    assert alerts.sent == ["F&O forecast lab 2026-10-26: NIFTY N1 for 2026-10-26 (issued 2026-10-23): no forecast was "
                           "sealed; nothing to score"]  # fmt: skip


def test_the_trust_line_counts_a_day_scored_for_either_underlying():
    forecasts = Forecasts(days={"BANKNIFTY": [DAY]})
    assert trust_line(forecasts, ("NIFTY", "BANKNIFTY"), REPORT_DAY).startswith("Trust: 1 scored trading day(s)")


def test_two_method_versions_of_one_forecaster_are_never_pooled():
    old, new = replace(SCORES[0], method="a" * 64, quantile_score=10.0), replace(SCORES[0], method="b" * 64)
    lines = scoreboard_lines([old, new])
    for line in ("  N1 rv20 [method aaaaaaaa]: 1 day(s), mean quantile score 10.00",
                 "  N1 rv20 [method bbbbbbbb]: 1 day(s), mean quantile score 12.50"):  # fmt: skip
        assert any(shown.startswith(line) for shown in lines)


def test_fl1_steps_over_regular_sessions_only_as_g13b_does():
    muhurat_monday = date(2026, 11, 9)  # NSE's calendar: 8 Nov 2026 is the Diwali muhurat session
    assert CALENDAR.previous_session(muhurat_monday) == date(2026, 11, 8)
    assert SESSIONS.previous(muhurat_monday) == date(2026, 11, 6) and not SESSIONS.is_regular(date(2026, 11, 8))
    assert SESSIONS.window(REPORT_DAY, 3) == [N1_ISSUE, DAY, REPORT_DAY]
