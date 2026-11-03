"""Judge 661.1 S1: Book 2's research-loss stops are in the real daily run. With `daily.live_from.book2_hybrid` set,
the run's reviews step holds Book 2's pauses review and commits `research_pauses.csv`; with Book 2 off, neither (nothing
of Book 2 is read)."""

import copy
from datetime import date

from fno.book2.pauses import PAUSES_FILE, Book2ResearchPauses
from fno.config import load_app_config
from fno.constants import BOOK2_HYBRID, REVIEWS_STEP
from fno.daily import wiring

DAY = date(2026, 10, 27)


def reviews_step(live_from):
    cfg = copy.deepcopy(load_app_config())
    cfg["daily"]["live_from"][BOOK2_HYBRID] = live_from
    runner = wiring.build_day_runner(cfg, sleep=lambda seconds: None, day=DAY)
    return runner.daily_run.day_steps[REVIEWS_STEP].step


def test_a_book2_live_day_runs_its_research_pauses_and_commits_their_file():
    step = reviews_step(DAY)
    assert any(isinstance(review, Book2ResearchPauses) for review in step.reviews)
    assert PAUSES_FILE in step.pathspecs


def test_with_book2_off_the_reviews_step_holds_neither():
    step = reviews_step(None)
    assert not any(isinstance(review, Book2ResearchPauses) for review in step.reviews)
    assert PAUSES_FILE not in step.pathspecs
