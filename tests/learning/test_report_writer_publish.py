"""LR1's report records (written once), the routine fire (pointer only, budget stop, not configured) and the one post
(summary checked, objections in their own section, the lines in every case)."""

import json
from datetime import datetime

import pytest

from fno.advocate.port import Advocate, AdvocateResult
from fno.forecast_scoring.v4.records import EXPLORATORY
from fno.learning.publish import OBJECTIONS_HEAD, PROSE_SUFFIX, SUMMARY_HEAD, Publisher
from fno.learning.report import PostMortemBuilder, PostMortemConflict, PostMortemRecords, PostMortemSection, Report
from fno.learning.week import build_week
from fno.learning.writer import BUDGET_STOP, BudgetSignal, PostMortemRoutine, SignalFile, WriterPointer
from fno.models import IST
from fno.pipeline.trigger import FireFailed, UnconfiguredTrigger

from .fakes import SATURDAY, Calendar

NOT_CONFIGURED = "routine weekly post-mortem not configured"
OBJECTED = AdvocateResult(("[L2] 40% is back-fill.",))
LINES = "Omenix F&O weekly post-mortem, week ending 2026-10-17\nweather_vix_v1: scored 40%\n"


class Section(PostMortemSection):
    name = "fake"

    def lines(self, week):
        return ["*Fake*", f"sessions {len(week.sessions)}"]

    def data(self, week):
        return {"n": len(week.sessions)}


def test_the_builder_puts_exploratory_first_until_the_freeze():
    week = build_week(Calendar(), SATURDAY)
    before = PostMortemBuilder([Section()], lambda: False).build(week)
    after = PostMortemBuilder([Section()], lambda: True).build(week)
    assert before.text.splitlines()[0] == EXPLORATORY and before.data["exploratory"] is True
    assert after.text.splitlines()[0].startswith("Omenix F&O weekly post-mortem, week ending 2026-10-17")
    assert after.data["fake"] == {"n": 5} and "sessions 5" in after.text


def test_a_week_is_written_once(tmp_path):
    records = PostMortemRecords(tmp_path)
    assert records.write(SATURDAY, Report(LINES, {"a": 1})) == "written"
    assert records.write(SATURDAY, Report(LINES, {"a": 1})) == "already written"
    with pytest.raises(PostMortemConflict):
        records.write(SATURDAY, Report(LINES + "late\n", {"a": 1}))
    assert records.path(SATURDAY).read_text() == LINES


class Trigger:
    name = "postmortem"

    def __init__(self, failure=None):
        self.fired, self.failure = [], failure

    def fire(self, pointer):
        if self.failure:
            raise FireFailed(self.failure)
        self.fired.append(pointer.to_text())
        return "https://claude.ai/code/session_x"


class Budget(BudgetSignal):
    def __init__(self, stopped):
        self.stopped = stopped

    def ai_roles_stopped(self, day):
        return self.stopped


def _routine(tmp_path, trigger, stopped=False):
    records = PostMortemRecords(tmp_path)
    records.write(SATURDAY, Report(LINES, {}))
    return records, PostMortemRoutine(
        trigger, records, Budget(stopped), lambda: datetime(2026, 10, 17, 10, 42, tzinfo=IST)
    )


def test_the_routine_gets_only_the_pointer_and_is_fired_once(tmp_path):
    trigger = Trigger()
    records, routine = _routine(tmp_path, trigger)
    assert routine.fire(SATURDAY).endswith("routine fired")
    assert routine.fire(SATURDAY).endswith("already fired (once per week)")
    sha = __import__("hashlib").sha256(LINES.encode()).hexdigest()
    assert trigger.fired == [WriterPointer(SATURDAY, sha).to_text()]
    assert json.loads(trigger.fired[0]) == {
        "job": "weekly_postmortem",
        "lines_sha256": sha,
        "week_ending": "2026-10-17",
    }
    assert records.read_json(SATURDAY, "_fired.json")["session_link"].endswith("session_x")


@pytest.mark.parametrize(
    ("trigger", "stopped", "reason"),
    [
        (Trigger(), True, BUDGET_STOP),
        (UnconfiguredTrigger("weekly post-mortem", ("FNO_ROUTINE_POSTMORTEM_TOKEN",)), False, NOT_CONFIGURED),
        (Trigger("HTTP 503 from the routine API"), False, "HTTP 503"),
    ],
)  # fmt: skip
def test_not_fired_is_logged_with_its_reason(tmp_path, trigger, stopped, reason):
    records, routine = _routine(tmp_path, trigger, stopped)
    assert "not fired: " + reason in routine.fire(SATURDAY)
    assert records.read_json(SATURDAY, "_fired.json")["reason"].startswith(reason)


def test_the_budget_signal_file_is_bg1_s(tmp_path):
    folder = tmp_path / "accounting" / "budget"
    folder.mkdir(parents=True)
    (folder / "2026-10_signal.json").write_text(json.dumps({"stop_ai_roles": True}))
    assert SignalFile(tmp_path).ai_roles_stopped(SATURDAY) is True
    assert SignalFile(tmp_path).ai_roles_stopped(SATURDAY.replace(month=11, day=7)) is False


class Alerts:
    def __init__(self, outcome="alert sent to #fno-desk"):
        self.sent, self.outcome = [], outcome

    def send(self, text):
        self.sent.append(text)
        return self.outcome


class FakeAdvocate(Advocate):
    def __init__(self, result):
        self.result, self.subjects = result, []

    def objections(self, subject):
        self.subjects.append(subject)
        return self.result


def _publisher(tmp_path, prose=None, result=OBJECTED, outcome=None, fired=True):
    records, routine = _routine(tmp_path, Trigger() if fired else Trigger("HTTP 503 from the routine API"))
    routine.fire(SATURDAY)
    if prose is not None:
        sha = __import__("hashlib").sha256(LINES.encode()).hexdigest()
        records.path(SATURDAY, PROSE_SUFFIX).write_text(f"{sha}\n{prose}\n")
    alerts = Alerts(*(() if outcome is None else (outcome,)))
    return records, Publisher(records, FakeAdvocate(result), alerts), alerts


def test_all_three_sections_are_posted_once(tmp_path):
    records, publisher, alerts = _publisher(tmp_path, prose="The weather model scored 40% this week.")
    assert publisher.publish(SATURDAY)[0].endswith("posted (alert sent to #fno-desk)")
    assert publisher.publish(SATURDAY)[0].endswith("already posted (once per week)")
    (message,) = alerts.sent
    assert message.index(SUMMARY_HEAD) < message.index(OBJECTIONS_HEAD) < message.index(LINES)
    assert "[L2] 40% is back-fill." in message
    assert records.read_json(SATURDAY, "_posted.json")["summary"] == "posted"


def test_a_number_mismatch_drops_the_summary_with_one_alert(tmp_path):
    records, publisher, alerts = _publisher(tmp_path, prose="The model scored 4 sessions well.")
    publisher.publish(SATURDAY)
    message, alert = alerts.sent
    assert (
        SUMMARY_HEAD not in message and "summary: AI summary dropped: rule 3: number 4 is not in the lines" in message
    )
    assert OBJECTIONS_HEAD in message and LINES in message
    assert "AI summary dropped: rule 3" in alert


def test_advocate_not_run_changes_nothing_else(tmp_path):
    _, publisher, alerts = _publisher(
        tmp_path, prose="It scored 40%.", result=AdvocateResult(not_run="no objections received")
    )
    publisher.publish(SATURDAY)
    (message,) = alerts.sent
    assert "advocate not run: no objections received" in message and SUMMARY_HEAD in message and LINES in message


def test_no_prose_and_a_routine_not_fired(tmp_path):
    _, publisher, alerts = _publisher(tmp_path)
    publisher.publish(SATURDAY)
    assert "summary: no summary received" in alerts.sent[0]
    _, publisher, alerts = _publisher(tmp_path / "b", fired=False)
    publisher.publish(SATURDAY)
    assert "summary: HTTP 503 from the routine API" in alerts.sent[0]
    assert "advocate not run: HTTP 503 from the routine API" in alerts.sent[0]


def test_a_slack_failure_still_writes_the_publish_record(tmp_path):
    records, publisher, _ = _publisher(tmp_path, prose="It scored 40%.", outcome="alert NOT sent: channel_not_found")
    assert "alert NOT sent" in publisher.publish(SATURDAY)[0]
    assert records.read_json(SATURDAY, "_posted.json")["slack"].startswith("alert NOT sent")
