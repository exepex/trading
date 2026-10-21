"""Story FL1-1's 15:45 report: forecasts counted only when sealed before their target's open, G13b's scores shown as
they are, written once and posted once; every missing, late or unposted report alerted to #fno-desk."""

from datetime import date

from fno.cards.posting import UNKNOWN, PostReceipt
from fno.forecast_lab.constants import MAY_HAVE_POSTED
from fno.forecast_lab.lab_close import CloseReport, LabClose
from fno.forecast_lab.match import MatchSection
from tests.checks.builders import CALENDAR
from tests.desk.conftest import RecordingAlerts

from .builders import DAY, N1_ISSUE, N3_ISSUE, Closes, Forecasts, Poster, Records, at, issue, score

ON_TIME = (issue(N1_ISSUE, at(N1_ISSUE, 15, 50)), issue(N3_ISSUE, at(N3_ISSUE, 15, 50)), issue(DAY, at(DAY, 15, 46)))
SCORES = (score(N1_ISSUE, "N1", qs=12.5), score(N3_ISSUE, "N3", qs=30.25, inside=(False, True)))


def lab(forecasts, records=None, poster=None, alerts=None, archived=True, underlyings=("NIFTY",)):
    report = CloseReport(forecasts, MatchSection(forecasts, Closes(archived), CALENDAR.previous_session),
                         underlyings=underlyings)  # fmt: skip
    records, poster, alerts = records or Records(), poster or Poster(), alerts or RecordingAlerts()
    return LabClose(report, records, poster, alerts, CALENDAR.session_kind, lambda: at(DAY, 15, 47)), poster, alerts


def test_a_closed_day_posts_nothing():
    run, poster, alerts = lab(Forecasts(ON_TIME, SCORES))
    assert run.run(date(2026, 10, 24)) == ["lab close 2026-10-24: not a trading day; nothing posted"]
    assert poster.posts == [] and alerts.sent == []


def test_forecasts_sealed_in_time_are_shown_with_g13bs_own_scores_and_the_trust_line():
    run, poster, alerts = lab(Forecasts(ON_TIME, SCORES, days=[N1_ISSUE, DAY]))
    assert run.run(DAY) == ["lab close 2026-10-23: #fno-forecast: alert sent; 0 alert(s) to #fno-desk"]
    (text,) = poster.posts
    assert " N1, issued 2026-10-22 15:45 at 25250.00:" in text and " N3, issued 2026-10-19 15:45 at 25250.00:" in text
    assert "close 25350.00: 25-75 in, 5-95 in, median direction right, quantile score 12.50" in text
    assert "close 25350.00: 25-75 out, 5-95 in, median direction right, quantile score 30.25" in text  # G13b's numbers
    assert "  N1 (2026-10-26) rv20: 5/25/50/75/95 25000/25200/25300/25400/25600, P(up) 0.55" in text
    assert "Trust: 2 scored trading day(s) of about 60 needed to judge calibration" in text
    assert alerts.sent == []


def test_a_missing_and_a_late_forecast_are_said_alerted_and_never_shown():
    late = issue(N1_ISSUE, at(DAY, 9, 16))  # pushed after the target day's open
    run, poster, alerts = lab(Forecasts((late, issue(DAY, at(DAY, 15, 46))), SCORES))
    run.run(DAY)
    text = poster.posts[0]
    assert "NIFTY N1 (issued 2026-10-22): sealed late (2026-10-23 09:16:00+05:30); not shown as a forecast" in text
    assert "NIFTY N3 (issued 2026-10-19): no forecast was sealed; nothing to score" in text
    assert "5-95 in, median direction right, quantile score 12.50" not in text  # no match line for a late seal
    assert [a.split(": ", 1)[1] for a in alerts.sent] == [
        "NIFTY N1 (issued 2026-10-22): sealed late (2026-10-23 09:16:00+05:30); not shown as a forecast",
        "NIFTY N3 (issued 2026-10-19): no forecast was sealed; nothing to score",
    ]


def test_no_push_evidence_is_late_and_todays_unsealed_issue_is_not_shown():
    run, poster, alerts = lab(Forecasts((issue(N1_ISSUE, None), issue(N3_ISSUE, at(N3_ISSUE, 15, 50)))))
    run.run(DAY)
    assert "sealed late (no push evidence)" in poster.posts[0]
    assert "NIFTY next sessions: today's 15:45 issue is not sealed yet; not shown" in poster.posts[0]


def test_an_unarchived_close_defers_todays_match():
    run, poster, _ = lab(Forecasts(ON_TIME, SCORES), archived=False)
    run.run(DAY)
    assert (
        "NIFTY: today's official close is not archived yet; today's match comes in the next report" in poster.posts[0]
    )


def test_a_rerun_after_the_post_posts_nothing():
    records = Records()
    run, poster, _ = lab(Forecasts(ON_TIME, SCORES), records=records)
    run.run(DAY)
    assert run.run(DAY) == ["lab close 2026-10-23: already posted; nothing posted again"] and len(poster.posts) == 1


def test_a_rerun_after_a_crash_before_the_post_posts_the_written_report_and_its_alerts():
    records = Records()
    records.write_report(DAY, "the report as written\n", ["NIFTY N3 (issued 2026-10-19): no forecast was sealed"])
    run, poster, alerts = lab(Forecasts(ON_TIME, SCORES), records=records)
    run.run(DAY)
    assert poster.posts == ["the report as written\n"]
    assert alerts.sent == ["F&O forecast lab 2026-10-23: NIFTY N3 (issued 2026-10-19): no forecast was sealed"]


def test_a_refused_post_is_alerted_and_retried_by_the_rerun_but_a_maybe_posted_one_never_is():
    records = Records()
    refused = PostReceipt("alert NOT sent: channel_not_found")
    run, poster, alerts = lab(Forecasts(ON_TIME, SCORES), records=records, poster=Poster(refused))
    run.run(DAY)
    assert not records.posted(DAY) and alerts.sent[-1].endswith("(alert NOT sent: channel_not_found)")
    run.run(DAY)
    assert len(poster.posts) == 2 and records.posted(DAY)
    maybe = PostReceipt("alert NOT sent: " + UNKNOWN.format(failure="ReadTimeout"))
    records, alerts = Records(), RecordingAlerts()
    run, poster, alerts = lab(Forecasts(ON_TIME, SCORES), records=records, poster=Poster(maybe), alerts=alerts)
    run.run(DAY)
    run.run(DAY)
    assert len(poster.posts) == 1 and records.posted(DAY) and "Slack may still have posted it" in alerts.sent[-1]
    assert MAY_HAVE_POSTED in UNKNOWN  # T1's wording: the guard against a double post follows it
