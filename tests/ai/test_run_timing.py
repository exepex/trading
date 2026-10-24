"""Story F8c: each AI book run's minutes are captured inside the steps today's (hash-frozen) prompts already run:
`brief` notes the start and the routine's session id, `reveal` publishes the run's timing in its own publish after the
reveal's, each book its own file; `ai collect` records every file in BG1's ledger once, and a fired run still missing
is one alert. The recorder and its tests were written by the G11 builder (013xqaNT, fa758dcc) and moved here."""

import json
from datetime import timedelta

import pytest

from fno.ai.paths import fired_path, reveal_path, timing_path
from fno.ai.run_timing import NO_SESSION, routine_session_id
from fno.ai.transport import PublishFailed
from fno.ai.usage_gaps import NOT_CAPTURED, alert_usage_gaps
from fno.ai.usage_record import BookUsageRecorder
from fno.budget.self_timed import SelfTimedUsageReader
from fno.budget.usage_ledger import UsageLedger
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from tests.ai.fakes import DAY, Clock, FakeRoutine, at, make_desk_repo
from tests.ai.test_book_session import draft
from tests.ai.test_inputs import pointer

SESSION = "session_01AbCdEf"


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent to #fno-desk"


@pytest.fixture
def desk(tmp_path):
    return make_desk_repo(tmp_path)


def full_run(desk, book=BOOK3_AI, session_id=SESSION):
    clock = Clock(at(15, 11))
    routine = FakeRoutine(desk, clock)
    session = routine.session(session_id)
    session.brief(pointer(desk, book).to_text())
    clock.now = at(15, 13)
    answer = desk / ".ai_book" / "answer.json"
    answer.write_text(json.dumps(draft()), encoding="utf-8")
    session.seal(answer)
    session.reveal()  # sleeps to 15:15:10, reveals, then publishes the run's timing
    return routine


def test_the_reveal_publishes_the_run_from_brief_to_reveal_in_bg1s_shape(desk):
    routine = full_run(desk)
    path = desk / timing_path(DAY, BOOK3_AI)
    assert json.loads(path.read_text(encoding="utf-8")) == {"session_id": SESSION, "model": "",
        "started_at": at(15, 11).isoformat(), "ended_at": at(15, 15, 10).isoformat(),
        "sealed_at": at(15, 13).isoformat(), "reveal_calls": 1}  # fmt: skip  # G11 C17: work and wait apart
    [usage] = SelfTimedUsageReader(path).days()
    assert (usage.day, usage.minutes, usage.turns) == (DAY, 4.17, 1)
    assert routine.printed[-1].startswith(f"timed: {BOOK3_AI} {DAY} from ")
    revealed = next(i for i, line in enumerate(routine.printed) if line.startswith("revealed:"))
    assert revealed == len(routine.printed) - 2 and len(routine.transport.commits) == 3  # its own publish, after


def test_the_session_id_is_the_environments_remote_id_as_the_session_tools_name_it():
    assert routine_session_id("cse_0134MoC6f7aAJVcHRBiyATo6") == "session_0134MoC6f7aAJVcHRBiyATo6"
    assert routine_session_id("  ") == ""


def test_a_timing_failure_never_costs_the_reveal(desk):
    routine = full_run(desk, session_id="")  # no session id: the timing is refused, the reveal is out
    assert (desk / reveal_path(DAY, BOOK3_AI)).is_file() and not (desk / timing_path(DAY, BOOK3_AI)).exists()
    assert routine.printed[-1].startswith(f"timing NOT published ({NO_SESSION})")


def test_a_failed_timing_publish_is_said_and_the_reveal_stands(desk):
    clock = Clock(at(15, 11))
    routine = FakeRoutine(desk, clock)
    session = routine.session()
    session.brief(pointer(desk, BOOK3_AI).to_text())
    answer = desk / ".ai_book" / "answer.json"
    answer.write_text(json.dumps(draft()), encoding="utf-8")
    session.seal(answer)
    publish = routine.transport.publish

    def refuse_timing(path, text, message):
        if path == timing_path(DAY, BOOK3_AI):
            raise PublishFailed("push rejected 3 times")
        return publish(path, text, message)

    routine.transport.publish = refuse_timing
    session.reveal()
    assert (desk / reveal_path(DAY, BOOK3_AI)).is_file()
    assert routine.printed[-1].startswith("timing NOT published (push rejected 3 times)")


def test_a_rerun_reveal_keeps_the_first_start_and_publishes_the_timing_once(desk):
    routine = full_run(desk)
    commits = len(routine.transport.commits)
    routine.session().reveal()  # the routine retried its last step
    assert len(routine.transport.commits) == commits
    assert routine.printed[-1] == f"timing already published: {timing_path(DAY, BOOK3_AI)}"


def test_a_second_brief_keeps_the_runs_first_start(desk):
    clock = Clock(at(15, 11))
    routine = FakeRoutine(desk, clock)
    routine.session().brief(pointer(desk, BOOK3_AI).to_text())
    clock.now = at(15, 12)
    routine.session().brief(pointer(desk, BOOK3_AI).to_text())  # the model ran brief again: the same run
    answer = desk / ".ai_book" / "answer.json"
    answer.write_text(json.dumps(draft()), encoding="utf-8")
    routine.session().seal(answer)
    routine.session().reveal()
    assert json.loads((desk / timing_path(DAY, BOOK3_AI)).read_text())["started_at"] == at(15, 11).isoformat()


def test_a_reused_container_never_lends_another_days_start(desk):
    stale = desk / ".ai_book" / f"started_{(DAY - timedelta(days=1)).isoformat()}_{BOOK3_AI}.json"
    stale.parent.mkdir(exist_ok=True)
    stale.write_text(json.dumps({"started_at": at(9, 0).isoformat()}), encoding="utf-8")
    full_run(desk)
    assert json.loads((desk / timing_path(DAY, BOOK3_AI)).read_text())["started_at"] == at(15, 11).isoformat()


def test_two_books_in_one_container_each_keep_their_own_start(desk):
    """Judge 276 addendum 1's note: the start is keyed by day and book, so one shared file would fail this."""
    FakeRoutine(desk, Clock(at(15, 5))).session().brief(pointer(desk, BOOK2_HYBRID).to_text())
    full_run(desk, BOOK3_AI)  # the same container's working folder
    started = json.loads((desk / timing_path(DAY, BOOK3_AI)).read_text())["started_at"]
    assert started == at(15, 11).isoformat()  # full_run's own brief at 15:11, not Book 2's earlier start file


def test_the_ledger_gets_each_books_minutes_once(desk):
    full_run(desk, BOOK3_AI)
    recorder = BookUsageRecorder(desk, UsageLedger(desk))
    [line] = recorder.record(DAY + timedelta(days=1))
    assert "recorded 4.17 minutes" in line
    [row] = UsageLedger(desk).rows()
    assert (row["purpose"], row["book"], row["session_id"], row["minutes"]) == (
        "books_and_roles", BOOK3_AI, SESSION, "4.17")  # fmt: skip
    assert recorder.record(DAY + timedelta(days=2)) == []  # already recorded: nothing printed, nothing added
    assert len(UsageLedger(desk).rows()) == 1


def test_a_bad_timing_file_is_a_refused_line_and_the_others_still_count(desk):
    full_run(desk, BOOK3_AI)
    bad = desk / timing_path(DAY, BOOK2_HYBRID)
    bad.write_text(json.dumps({"session_id": SESSION, "started_at": "15:11", "ended_at": "15:15"}), encoding="utf-8")
    stray = desk / timing_path(DAY, "book9")
    stray.write_text("{}", encoding="utf-8")
    lines = BookUsageRecorder(desk, UsageLedger(desk)).record(DAY + timedelta(days=1))
    assert sum("refused:" in line for line in lines) == 2 and sum("recorded" in line for line in lines) == 1
    assert [row["book"] for row in UsageLedger(desk).rows()] == [BOOK3_AI]


def fired(desk, **sessions):
    path = desk / fired_path(DAY)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({b: {"fired": True, "version": "v", "session": s} for b, s in sessions.items()}))


def test_a_fired_run_not_captured_is_one_alert_and_a_captured_one_none(desk):
    full_run(desk, BOOK3_AI)
    fired(desk, **{BOOK3_AI: "https://claude.ai/code/cse_01AbCdEf", BOOK2_HYBRID: "https://claude.ai/code/cse_02Zz"})
    ledger, alerts = UsageLedger(desk), Alerts()
    BookUsageRecorder(desk, ledger).record(DAY + timedelta(days=1))
    printed = alert_usage_gaps(desk, ledger, DAY, alerts)
    assert alerts.sent == [NOT_CAPTURED.format(day=DAY.isoformat(), book=BOOK2_HYBRID)]
    assert printed == [f"usage not captured: {BOOK2_HYBRID} {DAY}: alert sent to #fno-desk"]
    assert not any(line.startswith("Omenix F&O AI") for line in printed)  # the job posts those lines again


def test_a_day_with_nothing_fired_alerts_nothing(desk):
    alerts = Alerts()
    assert alert_usage_gaps(desk, UsageLedger(desk), DAY, alerts) == [] and alerts.sent == []
