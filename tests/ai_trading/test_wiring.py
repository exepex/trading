"""Story F1t criteria 1 and 8: the live switches (null keeps every AI book out of the desk; a date includes it from that
day; a misspelled key is refused), the built daily run with the two steps, and E3's commit-time rule at the deadline
(a run committed at 15:11:59 counts, one committed at 15:12:00 is late)."""

from dataclasses import replace
from datetime import date, datetime, time

import pytest

from fno.config import load_app_config
from fno.constants import AI_COLLECT_STEP, AI_FIRE_STEP, BOOK1_RULES, BOOK2_HYBRID, STEP_NOT_LIVE
from fno.daily.wiring import build_day_runner, live_ai_books
from fno.desk.committed_decisions import D3CommittedDecisions
from fno.models import IST
from fno.playbook.history import PlaybookGit
from tests.timetable.test_daily_run import NORMAL

from .builders import FakeDecider, accepted
from .end_to_end import git, start_repository

CFG = load_app_config()


def with_live(**books):
    return CFG | {"daily": {"live_from": CFG["daily"]["live_from"] | books}}


def test_the_switches_are_null_in_config_yaml():
    assert live_ai_books(CFG, date(2030, 1, 1)) == ()


@pytest.mark.parametrize("live_from, day, live", [("2026-10-19", date(2026, 10, 19), True),
                                                  ("2026-10-19", date(2026, 10, 18), False),
                                                  ("2026-10-19", date(2026, 10, 20), True)])  # fmt: skip
def test_a_book_is_live_from_its_date(live_from, day, live):
    assert (BOOK2_HYBRID in live_ai_books(with_live(book2_hybrid=live_from), day)) is live


def test_a_misspelled_key_is_refused():
    with pytest.raises(ValueError, match="unknown book2_hybird"):
        live_ai_books(with_live(book2_hybird="2026-10-19"), NORMAL)


def test_with_no_live_book_the_run_holds_book1_only_and_both_steps_are_not_live():
    runner = build_day_runner(CFG, day=NORMAL)
    assert runner.daily_run.steps.books == (BOOK1_RULES,) and runner.daily_run.steps.packs.books == (BOOK1_RULES,)
    for name in (AI_FIRE_STEP, AI_COLLECT_STEP):
        assert runner.daily_run.day_steps[name].run(NORMAL).result["status"] == STEP_NOT_LIVE


def test_a_live_book_joins_the_desk_and_its_packs():
    runner = build_day_runner(with_live(book2_hybrid=NORMAL.isoformat()), day=NORMAL)
    assert runner.daily_run.steps.books == (BOOK1_RULES, BOOK2_HYBRID)
    assert runner.daily_run.steps.packs.books == (BOOK1_RULES, BOOK2_HYBRID)


@pytest.mark.parametrize("moment, on_time", [((15, 11, 59), True), ((15, 12, 0), False)])
def test_e3_counts_a_run_committed_before_its_deadline_only(tmp_path, moment, on_time):
    root = tmp_path / "repo"
    root.mkdir()
    start_repository(root, NORMAL)
    decided = FakeDecider(root).decide(replace(accepted(root), day=NORMAL))
    git(root, "add", "-f", str(decided.run))
    git(root, "commit", "-q", "-m", "ai_collect", when=datetime.combine(NORMAL, time(*moment), IST))
    deadline = datetime.combine(NORMAL, time(15, 12), IST)
    found = D3CommittedDecisions(root, PlaybookGit(root)).committed(BOOK2_HYBRID, NORMAL, deadline)
    assert (found is not None) is on_time
