"""REH1j, J5: the rehearsal's one line on what it exercised, in run order, printed and posted once to #fno-desk with
REH1's label first; nothing exercised, nothing printed or posted; a post Slack did not take prints "alert NOT sent"."""

import json
from datetime import date

from fno.alerts.sender import NOT_SENT, SENT
from fno.constants import ENV_FNO_REHEARSAL
from fno.daily.full_log import FULL_LOGS
from fno.rehearsal.exercised_line import exercised_line, report_exercised
from fno.rehearsal.mode import Rehearsal

DAY = date(2026, 10, 23)
STEPS = {
    "margin_check": {"result": {"status": "not_live", "reason": "n",
                                "exercised": {"status": "not_built", "reason": "no command 'margins x' in fno"}}},
    "weather": {"result": {"status": "ok"}},
    "quotes_done": {"result": {"status": "ok", "parts": {}, "exercised_parts": {
        "v4": {"status": "failed", "reason": "no v4 capture"}}}},
    "card": {"result": {"status": "not_live", "reason": "n", "exercised": {"status": "failed", "reason": "boom"}}},
    "premium_range_scores": {"result": {"status": "not_live", "reason": "n", "exercised": {"status": "ok"}}},
    "close_read": {"result": {"status": "not_live", "reason": "not live before 2026-10-26"}},  # the real day's own
}  # fmt: skip
LINE = ("not live in real runs (exercised): margin_check not built; quotes_done's v4 part failed: no v4 capture; "
        "card failed: boom; premium_range_scores ok")  # fmt: skip


class Recording:
    def __init__(self, outcome=SENT):
        self.sent, self.outcome = [], outcome

    def send(self, text):
        self.sent.append(text)
        return self.outcome


def full_log(root, steps):
    path = root / FULL_LOGS / f"{DAY}.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"day": str(DAY), "steps": steps}))


def test_the_line_names_each_exercised_step_and_part_in_run_order():
    assert exercised_line(STEPS) == LINE


def test_nothing_exercised_gives_no_line():
    assert exercised_line({"weather": {"result": {"status": "ok"}}}) is None
    assert exercised_line({}) is None


def test_the_line_is_printed_and_posted_once_labelled_through_the_real_alert_sender(tmp_path, monkeypatch):
    from fno.rehearsal.rehearse import _alerts

    sent = Recording()
    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(DAY, tmp_path, tmp_path).to_env())
    monkeypatch.setenv("FNO_SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setattr("fno.composition.SlackChannelAlerts", lambda *args: sent)
    full_log(tmp_path, STEPS)
    printed = []
    report_exercised(tmp_path, DAY, printed.append, _alerts(printed.append))
    assert printed == [LINE]
    assert sent.sent == [f"*DRY RUN, {DAY} replay, not a real trading day*\n{LINE}"]


def test_nothing_exercised_or_no_daily_log_prints_and_posts_nothing(tmp_path):
    printed, sent = [], Recording()
    report_exercised(tmp_path, DAY, printed.append, sent)  # a routine with no daily run log
    full_log(tmp_path, {"weather": {"result": {"status": "ok"}}})
    report_exercised(tmp_path, DAY, printed.append, sent)
    assert (printed, sent.sent) == ([], [])


def test_a_post_slack_did_not_take_prints_alert_not_sent(tmp_path):
    from fno.daily.alerts import ReportedAlerts

    full_log(tmp_path, STEPS)
    printed = []
    report_exercised(
        tmp_path, DAY, printed.append, ReportedAlerts(Recording(NOT_SENT.format(reason="down")), printed.append)
    )
    assert printed == [LINE, f"alert NOT sent: down | {LINE}"]
