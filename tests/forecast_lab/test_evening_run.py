"""Stories FL1-1 and FL1-1d, `lab close` (the evening edition; judge 422): the report written once and posted once, its
alerts sent once, every alert's outcome printed (an unsent one with its text, for the routine to post by hand), a
refused post the step's failure."""

from datetime import date

from fno.alerts.sender import NoAlertSender
from fno.forecast_lab.delivery import Delivery
from fno.forecast_lab.written import WrittenReport
from tests.desk.conftest import RecordingAlerts

from .builders import DAY, REPORT_DAY, Forecasts, Poster, Records, lab, on_time

MISSING = Forecasts(on_time(DAY))  # nothing aimed at 26 Oct: two alerts, N1 and N3
N1_MISSING = "NIFTY N1 for 2026-10-26 (issued 2026-10-23): no forecast was sealed; nothing to score"


def test_a_closed_day_and_a_muhurat_session_post_nothing():
    run, poster, alerts = lab(MISSING)
    for day in (date(2026, 10, 24), date(2026, 11, 8)):
        assert run.run(day).lines == [f"lab close {day}: not a regular session; nothing posted"]
    assert poster.posts == [] and alerts.sent == []


def test_a_session_posts_once_sends_each_alert_once_and_a_rerun_sends_nothing():
    records = Records()
    run, poster, alerts = lab(MISSING, records=records)
    assert run.run(REPORT_DAY).lines == ["lab close 2026-10-26: report to #fno-forecast: posted",
                                         "lab close 2026-10-26: 2 of 2 alert(s) sent to #fno-desk"]  # fmt: skip
    assert alerts.sent[0] == f"F&O forecast lab 2026-10-26: {N1_MISSING}"
    assert run.run(REPORT_DAY).lines == ["lab close 2026-10-26: already posted and alerted; nothing sent again"]
    assert len(poster.posts) == 1 and len(alerts.sent) == 2


def test_an_alert_not_sent_is_printed_with_its_text_and_counted_as_not_sent():
    records = Records()
    run, _, _ = lab(MISSING, records=records, alerts=NoAlertSender())
    result = run.run(REPORT_DAY)
    assert result.lines[1] == "lab close 2026-10-26: 0 of 2 alert(s) sent to #fno-desk" and not result.failed
    assert (
        result.lines[2] == f"alert NOT sent: FNO_SLACK_BOT_TOKEN is not set: F&O forecast lab 2026-10-26: {N1_MISSING}"
    )
    assert records.alert_marks[REPORT_DAY] == ["alert NOT sent: FNO_SLACK_BOT_TOKEN is not set"] * 2


def test_a_rerun_after_a_crash_before_the_post_posts_the_written_report_and_its_alerts():
    records = Records()
    records.write_report(REPORT_DAY, WrittenReport("the report as written\n", ("a stored finding",)))
    run, poster, alerts = lab(MISSING, records=records)
    run.run(REPORT_DAY)
    assert poster.posts == ["the report as written\n"]
    assert alerts.sent == ["F&O forecast lab 2026-10-26: a stored finding"]


def test_a_rerun_after_a_crash_between_the_post_and_the_alerts_sends_only_the_alerts():
    records = Records()
    records.write_report(REPORT_DAY, WrittenReport("posted\n", ("a stored finding",)))
    records.mark_posted(REPORT_DAY, "alert sent")
    run, poster, alerts = lab(MISSING, records=records)
    assert run.run(REPORT_DAY).lines[0] == "lab close 2026-10-26: report already posted to #fno-forecast"
    assert poster.posts == [] and alerts.sent == ["F&O forecast lab 2026-10-26: a stored finding"]


def test_a_refused_post_fails_the_run_alerts_it_once_with_the_day_s_alerts_and_the_rerun_retries_only_the_post():
    """The editions run outside O1's `Alerted` (FL1-1d): the run alerts its own failed post, once."""
    records, alerts = Records(), RecordingAlerts()
    run, poster, _ = lab(MISSING, records=records, alerts=alerts, poster=Poster(Delivery("alert NOT sent: x")))
    result = run.run(REPORT_DAY)
    failure = "the evening report was not posted to #fno-forecast (alert NOT sent: x)"
    assert result.failed and failure in result.lines
    assert not records.posted(REPORT_DAY) and len(alerts.sent) == 3
    assert alerts.sent[-1] == f"F&O forecast lab 2026-10-26: {failure}"
    again = run.run(REPORT_DAY)
    assert not again.failed and again.lines[-1] == "lab close 2026-10-26: alerts already sent; none sent again"
    assert len(poster.posts) == 2 and records.posted(REPORT_DAY) and len(alerts.sent) == 3


def test_a_maybe_posted_report_is_never_posted_again_and_says_which_channel_to_check():
    records = Records()
    maybe = Delivery("alert NOT sent: ReadTimeout; Slack may still have posted it", may_have_posted=True)
    run, poster, _ = lab(MISSING, records=records, poster=Poster(maybe))
    first = run.run(REPORT_DAY)
    assert first.failed and first.lines[1].endswith("; check #fno-forecast before any repost")
    assert run.run(REPORT_DAY).lines == ["lab close 2026-10-26: already posted and alerted; nothing sent again"]
    assert len(poster.posts) == 1 and records.posted(REPORT_DAY)


def test_the_stored_files_are_posted_with_the_text_and_a_rerun_posts_the_same_files():
    records = Records()
    run, poster, _ = lab(MISSING, records=records, poster=Poster(Delivery("alert NOT sent: x")))
    run.run(REPORT_DAY)
    run.run(REPORT_DAY)  # the stored report, never a rebuilt one
    assert poster.files == [["forecast-2026-10-26.html"]] * 2 and poster.posts[0] == poster.posts[1]
