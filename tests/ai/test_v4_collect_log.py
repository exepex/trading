"""Story G11 (round 2b step 4; completion C11, C13, C19; judge 586 F1 and F2), split from `test_v4_collect.py` for the
size limit: collect reads the fire log as first committed and waits for a lost one; sessions from the AI slots' start
before go-live are not_fired; exposures are marked; the pack guard reads two sources."""

import json
from datetime import datetime, time, timedelta

import pytest

from fno.ai.run_terms import V4_TERMS
from fno.ai.v4_book_inputs import V4BookInputs
from fno.constants import BOOK2_HYBRID, BOOK3_AI, V6_BIG_MOVE_1S
from fno.forecast_scoring.v4.inputs import ForecastFiles
from fno.models import IST
from tests.ai.fakes import git
from tests.ai.test_v4_collect import V4Desk
from tests.ai.test_v4_fire import DAY, Ledger, NoBudgetStop, Released, Series, at


@pytest.fixture
def desk(tmp_path):
    return V4Desk(tmp_path)


def commit_fire_log(desk):
    path = V4_TERMS.fired_path(DAY)
    git(desk.root, "add", path)
    git(desk.root, "commit", "-q", "-m", "G10/G11 Actions: v4 AI fire log")
    return desk.root / path


def edit_log(path, edit):
    log = json.loads(path.read_text())
    edit(log)
    path.write_text(json.dumps(log))


def test_the_fire_log_is_read_as_first_committed_so_a_later_edit_changes_no_verdict(desk):
    """Review of 99a916f2: the log is the record of what each book was given; an edit after its commit is ignored."""
    desk.fire()
    desk.answer(BOOK3_AI)
    log = commit_fire_log(desk)
    edit_log(log, lambda f: f["books"][BOOK3_AI]["labels"].update(export_sha256="0" * 64))
    desk.collect()
    assert desk.audit(BOOK3_AI)["status"] == "on_time"


def test_a_hybrid_entry_without_its_envelope_is_invalid_never_unchecked(desk):
    desk.fire()
    desk.answer(BOOK2_HYBRID, values=(0.95, None))  # outside any envelope
    edit_log(desk.root / V4_TERMS.fired_path(DAY), lambda f: f["books"][BOOK2_HYBRID].update(envelope=None))
    desk.collect()
    assert desk.audit(BOOK2_HYBRID)["status"] == "invalid"


@pytest.mark.parametrize(("sessions_later", "waits"), [(2, True), (3, False)])
def test_a_lost_fire_log_waits_three_sessions_then_the_committed_book_is_invalid(desk, sessions_later, waits):
    desk.sessions = [DAY + timedelta(days=n) for n in range(sessions_later + 1)]
    desk.fire()
    desk.answer(BOOK3_AI)
    (desk.root / V4_TERMS.fired_path(DAY)).unlink()
    last = desk.sessions[-1]
    lines = desk.collect(day=last, now=datetime.combine(last, time(15, 31), IST))
    first = [line for line in lines if f": {DAY}: " in line]
    if waits:
        assert len(first) == 1 and "awaiting the fire log" in first[0]
    else:
        assert desk.audit(BOOK3_AI)["status"] == "invalid" and "lost" in " ".join(desk.audit(BOOK3_AI)["notes"])
        assert desk.audit(BOOK2_HYBRID)["status"] == "not_fired"


def test_sessions_between_the_slots_start_and_a_later_go_live_are_not_fired_and_the_look_is_reconciled(tmp_path):
    """Judge 586 F1, its probe: the AI slots start one session before the go-live date (DAY)."""
    from fno.forecast_scoring.v4.reconcile import AiSlotDays

    early = DAY - timedelta(days=3)  # Friday 23 Oct, the session before Monday's go-live
    desk = V4Desk(tmp_path, Ledger(start=early))
    desk.sessions = [early, DAY]
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.answer(BOOK2_HYBRID, values=(0.05, None))
    desk.collect(live_from=DAY)
    assert desk.audit_of(early, BOOK3_AI)["status"] == "not_fired"
    assert "before the AI books' v4 go-live (2026-10-26)" in desk.audit_of(early, BOOK3_AI)["fire"]["reason"]
    desk.settle()
    slot_days = AiSlotDays(ForecastFiles(desk.v4), Ledger(start=early), lambda first, last: desk.sessions)
    assert slot_days.unsettled(early - timedelta(days=1), DAY) == []  # G8's look is not refused


def test_the_fire_says_each_day_how_many_sessions_fell_before_go_live(tmp_path):
    from fno.ai.v4_fire import V4BookFirer

    early = DAY - timedelta(days=3)
    desk = V4Desk(tmp_path, Ledger(start=early))
    firer = V4BookFirer(desk.root, desk.triggers, Released, desk.inputs, desk.alerts, lambda: at(14, 33), DAY,
                        lambda day: [], NoBudgetStop(), lambda first, last: [early, DAY])  # fmt: skip
    lines = firer.fire(DAY)
    assert lines[0].endswith("1 AI session(s) from the slots' start 2026-10-23 fell before the go-live date "
                             "2026-10-26: each with a released pack is a not_fired miss "
                             "(a system_late day is excused)")  # fmt: skip
    on_time = V4BookFirer(desk.root, desk.triggers, Released, V4BookInputs(tmp_path, Ledger(), ForecastFiles(desk.v4),
                          Series()), desk.alerts, lambda: at(14, 33), DAY, lambda day: [], NoBudgetStop(),
                          lambda first, last: [DAY])  # fmt: skip
    assert "fell before" not in on_time.fire(DAY)[0]


def test_a_book_that_commits_after_the_other_books_answer_was_public_is_exposed(desk):
    """Judge 586 F2 (P18): the v4 collect marks exposures, as F1/G5's collect does."""
    desk.fire()
    desk.answer(BOOK3_AI, sealed=at(15, 0), revealed=at(15, 4))  # Book 3's answer readable at 15:04
    desk.answer(BOOK2_HYBRID, values=(0.05, None), sealed=at(15, 6))  # Hybrid commits after it
    desk.collect()
    assert desk.audit(BOOK2_HYBRID)["status"] == "exposed"


def test_the_pack_guard_compares_the_fire_logs_pack_with_the_release_records(desk):
    """Judge 586 F2 (P23): two sources. A fire log naming another pack than the release record never makes rows."""
    desk.fire()
    desk.answer(BOOK3_AI)
    edit_log(desk.root / V4_TERMS.fired_path(DAY), lambda f: f["books"][BOOK3_AI].update(pack_sha256="e" * 64))
    desk.collect()
    assert desk.audit(BOOK3_AI)["released_sha256"] == "d" * 64  # the release record's, read by collect itself
    lines = desk.settle()
    assert desk.row(BOOK3_AI, V6_BIG_MOVE_1S) is None
    assert any("NOT settled" in line and "PackBindingRefused" in line for line in lines)
