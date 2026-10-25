"""Story F1t criteria 1, 3e, 8, 9 and 10, end to end on E3's real daily run (see `end_to_end.py`): an on-time AI
answer becomes a committed D3 run that E3 collects at its deadline and fills like Book 1's; a C4 failure never fills;
every miss leaves E3's no-decision record and no fill; a slow Book 1 cannot make an AI book late; a dead observer
makes every fired book late; Book 1's records are the same with or without the AI book."""

import json

import pytest

from fno.ai_trading.paths import outcome_path
from fno.books.account import PaperAccount
from fno.constants import BOOK1_RULES, BOOK2_HYBRID, DAILY_RUN_STEPS
from fno.desk.no_decision import FILE as NO_DECISION
from fno.desk.records import DeskRecords
from fno.playbook.decision_store import DecisionStore
from tests.desk.conftest import alerts  # noqa: F401
from tests.timetable.test_daily_run import NORMAL

from .builders import FakeDecider, accepted, draft, record
from .end_to_end import C4_FAILED, build_day

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def outcome(root):
    return json.loads((root / outcome_path(NORMAL, BOOK2_HYBRID)).read_text())


def filled(root, book=BOOK2_HYBRID):
    return [row["trade_id"] for row in DeskRecords(PaperAccount(root, book)).fill_rows()]


def no_decision(root, book=BOOK2_HYBRID):
    return (DecisionStore(root, book).day_folder(NORMAL) / NO_DECISION).is_file()


def test_an_on_time_answer_is_promoted_collected_at_e3_s_deadline_and_filled(tmp_path, alerts):  # noqa: F811
    root = tmp_path / "repo"
    root.mkdir()
    run, clock, routine, decider, observer, _ = build_day(root, tmp_path, alerts, NORMAL, draft())
    log = run.run(NORMAL)
    assert [name for name in DAILY_RUN_STEPS if name in log.steps][:4] == ["versions", "pack", "ai_fire", "ai_collect"]
    assert log.result("ai_fire")["status"] == "ok" and log.result("ai_collect")["status"] == "ok"
    assert outcome(root)["status"] == "promoted" and len(decider.calls) == 1 and len(observer.started) == 1
    assert log.result("decisions")[BOOK2_HYBRID]["run_id"] == f"{NORMAL}-r1"
    assert filled(root) and not no_decision(root)


def test_a_c4_failure_is_promoted_as_a_record_but_never_filled(tmp_path, alerts):  # noqa: F811
    root = tmp_path / "repo"
    root.mkdir()
    run, *_ = build_day(root, tmp_path, alerts, NORMAL, draft(), c4=C4_FAILED)
    log = run.run(NORMAL)
    assert outcome(root)["status"] == "promoted" and filled(root) == []
    assert "C4 failed: envelope" in json.dumps(log.result("fills"))


@pytest.mark.parametrize("kwargs, status", [
    ({"seal_at": (15, 10, 5)}, "late"),
    ({"seal_at": None}, "no_submission"),
    ({"reveal": False}, "not_revealed"),
    ({"observer_killed": True}, "late"),
    ({"routine_draft": draft(model="unknown")}, "model_unverified"),
    ({"routine_draft": draft(model="claude-sonnet-5-5")}, "model_mismatch"),
])  # fmt: skip
def test_every_miss_is_recorded_alerted_once_and_never_filled(tmp_path, alerts, kwargs, status):  # noqa: F811
    root = tmp_path / "repo"
    root.mkdir()
    routine_draft = kwargs.pop("routine_draft", draft())
    run, *_ = build_day(root, tmp_path, alerts, NORMAL, routine_draft, **kwargs)
    log = run.run(NORMAL)
    assert outcome(root)["status"] == status and log.result("ai_collect")["status"] == "refused"
    assert no_decision(root) and filled(root) == []
    lines = [text for text in alerts.sent if "ai_collect" in text]
    assert len(lines) == 1 and f"{BOOK2_HYBRID} {status}" in lines[0]
    if kwargs.get("observer_killed"):
        assert "the remote observer ended with exit code 1 (Traceback: git ls-remote failed)" in lines[0]


def test_a_decider_exception_refuses_the_book_and_the_day_goes_on_to_the_exits(tmp_path, alerts):  # noqa: F811
    from .builders import FakeDecider

    root = tmp_path / "repo"
    root.mkdir()
    run, _, _, decider, _, _ = build_day(root, tmp_path, alerts, NORMAL, draft(), decider=None)
    run.day_steps["ai_collect"].step.collector.promoter.deciders[BOOK2_HYBRID] = FakeDecider(root, fail=ValueError("x"))
    log = run.run(NORMAL)
    assert outcome(root)["status"] == "refused" and "ValueError: x" in outcome(root)["reason"]
    assert "exits" in log.steps and filled(root) == []


def test_a_slow_book1_cannot_make_an_ai_book_late(tmp_path, alerts):  # noqa: F811
    from fno.desk.daily_steps import StepOutcome

    root = tmp_path / "repo"
    root.mkdir()
    run, clock, *_ = build_day(root, tmp_path, alerts, NORMAL, draft())

    class SlowBook1:
        def run(self, day):
            clock.until(clock.now.replace(hour=15, minute=11, second=30))  # E5's command running past 15:10:30
            return StepOutcome({}, {"status": "ok", "reason": "decided"})

    run.day_steps["book1"] = SlowBook1()
    log = run.run(NORMAL)
    assert log.steps["book1"]["result"]["status"] == "ok" and outcome(root)["status"] == "promoted"
    assert filled(root)


def test_book1_s_records_are_the_same_with_or_without_the_live_ai_book(tmp_path, alerts):  # noqa: F811
    roots = []
    for name, live in (("with", (BOOK2_HYBRID,)), ("without", ())):
        root = tmp_path / name
        root.mkdir()
        run, *_ = build_day(root, tmp_path / f"{name}-quotes", alerts, NORMAL, draft(), live=live)
        run.run(NORMAL)
        roots.append(root)
    with_ai, without = roots
    assert (DeskRecords(PaperAccount(with_ai, BOOK1_RULES)).fill_rows() ==
            DeskRecords(PaperAccount(without, BOOK1_RULES)).fill_rows())  # fmt: skip
    assert not (without / outcome_path(NORMAL, BOOK2_HYBRID)).exists()


def test_a_slow_ai_decider_is_stopped_late_and_book1_is_still_collected_on_time(tmp_path, alerts):  # noqa: F811
    """Judge 651 should-fix 1: a decider that would run 95 s past 15:11:47 is stopped by its time limit (real
    seconds: what is left before 15:12:00, less the 10 s reserve), its run is put back, and E3 collects on time."""
    import time

    from fno.desk.daily_steps import StepOutcome

    root = tmp_path / "repo"
    root.mkdir()
    run, clock, *_ = build_day(root, tmp_path, alerts, NORMAL, draft())

    class SlowBook1:
        def run(self, day):
            clock.until(clock.now.replace(hour=15, minute=11, second=40))
            store = DecisionStore(root, BOOK1_RULES)  # Book 1's run; the daily run commits and pushes it after the step
            book1 = store.write(day, store.next_run_id(day), None, [book1_record(store.next_run_id(day))])
            clock.until(clock.now.replace(hour=15, minute=11, second=48))  # ai_collect reaches Book 2 at 15:11:48
            return StepOutcome({}, {"status": "ok", "reason": "decided"}, [book1])

    def book1_record(run_id):
        return record(BOOK1_RULES, run_id, accepted(root), model_served=None, session_id=None, served={"playbook": "p"},
                      judge=None)  # fmt: skip

    class SlowDecider(FakeDecider):
        def decide(self, accepted):
            decided = super().decide(accepted)  # its run is on disk: the stop must put it back
            time.sleep(30)  # never reached in full: the limit is about 2 real seconds
            clock.advance(95)
            return decided

    run.day_steps["book1"] = SlowBook1()
    run.day_steps["ai_collect"].step.collector.promoter.deciders[BOOK2_HYBRID] = SlowDecider(root)
    started = time.monotonic()
    log = run.run(NORMAL)
    assert time.monotonic() - started < 15
    assert outcome(root)["status"] == "late" and "did not finish within" in outcome(root)["reason"]
    assert not any(DecisionStore(root, BOOK2_HYBRID).day_folder(NORMAL).glob("*-r*"))  # put back, never committed
    collected = log.result("decisions")
    assert collected[BOOK1_RULES]["run_id"] == f"{NORMAL}-r1"  # Book 1's committed run is collected on time
    assert no_decision(root) and filled(root) == []
