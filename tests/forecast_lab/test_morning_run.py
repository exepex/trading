"""FL1-1d: the editions' run rules. An edition posts only from its own live date. The morning is today's forecast
only before the open: at or after 09:15 it is not posted, one alert says so, and a rerun sends no second alert; a
report written before 09:15 but not posted is never posted late."""

from datetime import date
from functools import partial

from fno.forecast_lab.constants import MORNING_BY
from fno.forecast_lab.delivery import Delivery
from fno.forecast_lab.edition_run import Composer, Edition, EditionRun
from fno.forecast_lab.written import WrittenReport
from tests.desk.conftest import RecordingAlerts

from .builders import SESSIONS, Poster, Records, at

MON = date(2026, 10, 26)


class Fixed(Composer):
    def __init__(self):
        self.calls = 0

    def compose(self, day, now):
        self.calls += 1
        return WrittenReport("today's forecast\n", ())


def morning(hour, minute, live_from=MON, records=None, poster=None):
    alerts, composer = RecordingAlerts(), Fixed()
    run = EditionRun(Edition("morning", live_from, MORNING_BY), composer, records or Records(), poster or Poster(),
                     alerts, SESSIONS.is_regular, partial(at, MON, hour, minute))  # fmt: skip
    return run, alerts, composer


def test_before_9_15_the_morning_posts_once():
    run, alerts, _ = morning(8, 50)
    assert run.run(MON).lines == ["lab open 2026-10-26: report to #fno-forecast: posted",
                                  "lab open 2026-10-26: 0 of 0 alert(s) sent to #fno-desk"]  # fmt: skip


def test_at_9_15_the_morning_posts_nothing_alerts_once_and_a_rerun_alerts_no_more():
    records, poster = Records(), Poster()
    run, alerts, composer = morning(9, 15, records=records, poster=poster)
    first = run.run(MON)
    assert first.failed and first.lines[0] == (
        "lab open 2026-10-26: not posted: it is 09:15, and the morning edition is only posted before 09:15"
    )
    assert alerts.sent == ["F&O forecast lab 2026-10-26: the morning edition was not posted before 09:15 (run at "
                           "09:15); nothing was sent"]  # fmt: skip
    again = run.run(MON)
    assert again.failed and again.lines[-1] == "lab open 2026-10-26: alerts already sent; none sent again"
    assert poster.posts == [] and len(alerts.sent) == 1 and composer.calls == 0


def test_a_morning_report_written_but_not_posted_in_time_is_never_posted_late():
    records = Records()
    early, early_alerts, _ = morning(8, 50, records=records, poster=Poster(Delivery("alert NOT sent: x")))
    assert early.run(MON).failed and records.report(MON) is not None
    assert early_alerts.sent == ["F&O forecast lab 2026-10-26: the morning report was not posted to #fno-forecast "
                                 "(alert NOT sent: x)"]  # fmt: skip
    late, alerts, _ = morning(9, 20, records=records)
    result = late.run(MON)
    assert result.failed and "not posted: it is 09:20" in result.lines[0]
    assert alerts.sent == [] and not records.posted(MON)  # the 08:50 run alerted its failed post already


def test_an_edition_before_its_live_date_or_with_none_posts_nothing():
    for live_from in (None, date(2026, 10, 27)):
        run, alerts, composer = morning(8, 50, live_from=live_from)
        (line,) = run.run(MON).lines
        not_live = f"not live (config forecast_lab.live_from.morning: {live_from}); nothing posted"
        assert line == f"lab open 2026-10-26: {not_live}"
        assert alerts.sent == [] and composer.calls == 0


def test_a_morning_posted_in_time_still_sends_its_stored_alerts_on_a_late_rerun():
    records = Records()
    records.write_report(MON, WrittenReport("today's forecast\n", ("a stored finding",)))
    records.mark_posted(MON, "posted")
    run, alerts, _ = morning(9, 20, records=records)
    assert not run.run(MON).failed and alerts.sent == ["F&O forecast lab 2026-10-26: a stored finding"]


class Raising(Composer):
    def compose(self, day, now):
        raise ValueError("a damaged record")


def test_a_failure_before_the_post_is_alerted_once_and_fails_the_run():
    from fno.forecast_lab.edition_run import guarded

    alerts = RecordingAlerts()
    run = EditionRun(Edition("evening", MON), Raising(), Records(), Poster(), alerts, SESSIONS.is_regular,
                     partial(at, MON, 20, 5))  # fmt: skip
    result = guarded("evening", MON, lambda: run, alerts)
    assert result.failed and result.lines == ["lab close 2026-10-26: the evening report was not made (ValueError); "
                                              "nothing was posted"]  # fmt: skip
    assert alerts.sent == ["F&O forecast lab 2026-10-26: the evening report was not made (ValueError); nothing was "
                           "posted"]  # fmt: skip


def test_a_build_that_fails_is_alerted_and_an_unsent_alert_is_printed_with_its_text():
    from fno.alerts.sender import NoAlertSender
    from fno.forecast_lab.edition_run import guarded

    def build():
        raise RuntimeError("G13b's records could not be read verified from Drive")

    result = guarded("morning", MON, build, NoAlertSender())
    assert result.failed and result.lines[1] == (
        "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set: F&O forecast lab 2026-10-26: the morning report was not made "
        "(RuntimeError); nothing was posted")  # fmt: skip


def test_a_morning_whose_making_ran_past_9_15_is_not_posted():
    class Slow(Composer):
        def compose(self, day, now):
            clock.now = at(MON, 9, 16)
            return WrittenReport("today's forecast\\n", ("NIFTY Fri 23 Oct: CORRECTION: ...",))

    class Clock:
        now = at(MON, 9, 14)

        def __call__(self):
            return self.now

    clock, poster, alerts = Clock(), Poster(), RecordingAlerts()
    run = EditionRun(Edition("morning", MON, MORNING_BY), Slow(), Records(), poster, alerts, SESSIONS.is_regular,
                     clock)  # fmt: skip
    result = run.run(MON)
    assert result.failed and "not posted: it is 09:16" in result.lines[0] and poster.posts == []
    assert len(alerts.sent) == 2 and alerts.sent[0].endswith("CORRECTION: ...")  # judge 444.1: never dropped
