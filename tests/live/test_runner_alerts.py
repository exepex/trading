"""One-time alerts and day bookkeeping across failures and midnight (judge, wave 0 round 4: N14, N15, N17)."""

import threading
from datetime import timedelta

from fno.live.runner import LiveRunner

from .fakes import at
from .test_risk_paths import desk_with_trades


def nse_down():
    raise ConnectionError("NSE down")


def dead_thread():
    thread = threading.Thread(target=lambda: None)
    thread.start()
    thread.join()
    return thread


def test_a_failing_reference_never_takes_the_dead_watcher_alert(tmp_path):
    svc, _, _, _ = desk_with_trades(tmp_path)
    svc.nse_feed.lot_sizes = nse_down
    runner = LiveRunner(svc)
    runner.state.day = at(9, 1).date()
    runner._report_problem(at(9, 1), "some other problem")  # the slot opens at 9:16, just as the reference retries
    runner._news_thread = dead_thread()
    for minute in range(1, 60):
        runner.tick(at(9, minute))
    assert sum("news watcher stopped" in m for m in svc.alerts.messages) == 1
    assert sum("reference data" in m for m in svc.alerts.messages) == 1  # it gets the next slot


def test_a_reference_outage_is_reported_once_and_never_overnight(tmp_path):
    svc, _, _, _ = desk_with_trades(tmp_path)
    svc.nse_feed.lot_sizes = nse_down
    runner = LiveRunner(svc)
    start, runner_now, sent_at = at(16, 0), [None], []  # from after Monday's close
    runner.services.alerts.problem = lambda message: sent_at.append((runner_now[0], message)) or True
    for step in range(0, 24 * 60, 5):
        runner_now[0] = start + timedelta(minutes=step)
        runner.tick(runner_now[0])
    reference_alerts = [when for when, m in sent_at if "reference data" in m]
    assert reference_alerts == [at(8, 45, start.date() + timedelta(days=1))]  # Tuesday 08:45 only


def test_a_new_day_never_sends_two_problem_alerts_at_once(tmp_path):
    svc, _, reference, _ = desk_with_trades(tmp_path)
    svc.nse_feed.lot_sizes = nse_down
    runner = LiveRunner(svc)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner._news_thread = dead_thread()
    tuesday = at(11, 0).date() + timedelta(days=1)
    runner.tick(at(8, 50, tuesday))  # the watcher alert goes out; the reference alert waits 15 minutes
    problems = [m for m in svc.alerts.messages if m.startswith("problem:")]
    assert len(problems) == 1 and "news watcher stopped" in problems[0]
    runner.tick(at(9, 5, tuesday))
    assert sum("reference data" in m for m in svc.alerts.messages) == 1


def test_a_kill_switch_day_alerts_once_across_midnight_and_still_sends_its_summary(tmp_path):
    svc, _, reference, _ = desk_with_trades(tmp_path)
    svc.kill_switch.engage("test", at(11, 5))
    runner = LiveRunner(svc)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner.tick(at(11, 6))
    assert not svc.desk.open_trades()
    runner.tick(at(15, 45))
    assert runner.state.summary_sent  # the kill-switch day still gets its summary
    closes = []
    svc.desk.close_all = lambda reason: closes.append(reason) or []
    runner.tick(at(23, 59))
    runner.tick(at(0, 1, at(11, 0).date() + timedelta(days=1)))
    assert svc.alerts.messages.count("kill switch") == 1 and closes == []  # nothing re-run at midnight
