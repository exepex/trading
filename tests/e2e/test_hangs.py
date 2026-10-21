"""Story O2, rows "Hung git call" and "Hung command": a push that never returns, through a hanging `pre-push` hook
in the fixture checkout (git's own hook, a real git and a real hang), and a child command that never ends. The git
limit is the one knob the suite turns (`fno.desk.git_sync.GIT_CALL_LIMIT_SECONDS`, read when `Git` is built), so a
120 s limit takes 2 s here; nothing else is replaced."""

from datetime import datetime, time

import pytest

from fno.desk.git_limit import GitLocks
from fno.models import IST

from .children import Foreground
from .harness import fixture_day
from .test_kill_rerun import RERUN_LOSES_THE_DAY

LIMIT = 2.0
HANG = '#!/bin/sh\n[ -f "$(git rev-parse --git-dir)/hang-push" ] && sleep 600\nexit 0\n'


def hanging_pushes(day, monkeypatch):
    """Every push hangs while `.git/hang-push` exists; `hang()` and `release()` switch it."""
    monkeypatch.setattr("fno.desk.git_sync.GIT_CALL_LIMIT_SECONDS", LIMIT)
    hook = day.root / ".git/hooks/pre-push"
    hook.write_text(HANG)
    hook.chmod(0o755)
    flag = day.root / ".git/hang-push"
    return lambda: flag.write_text(""), lambda: flag.unlink(missing_ok=True)


def no_lock_left(day) -> bool:
    return GitLocks(day.root).present() == set()


def test_a_desk_push_that_hangs_is_stopped_alerted_once_and_the_rerun_recovers(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    hang, release = hanging_pushes(day, monkeypatch)
    day.clock.on_condition = [(lambda: day.committed(f"Desk run {day.day} step snapshot"), hang)]  # fills' push
    code, line = day.run()
    assert (
        code == 1 and "run STOPPED at step fills" in line and "push not confirmed" in line and "no card today" in line
    )
    assert len(day.slack.sent) == 1 and no_lock_left(day)
    release()
    day.slack.sent.clear()
    code, line = day.run()
    assert f"Desk run {day.day} step fills" in day.origin_subjects()  # the stuck commit, pushed by the recovery
    assert day.step("exits")["book1_rules"]["reviewed"] is True and "card" in day.log()["steps"]
    assert line == "day done with problems: quotes_done"  # the named F1 limit: see the strict xfail below


@pytest.mark.xfail(strict=True, reason=RERUN_LOSES_THE_DAY + "; and a rerun after a stop calls parts the stopped run "
                   "committed 'not in this run' (failed, alerted)")  # fmt: skip
def test_the_rerun_after_a_stopped_push_ends_day_done(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    hang, release = hanging_pushes(day, monkeypatch)
    day.clock.on_condition = [(lambda: day.committed(f"Desk run {day.day} step snapshot"), hang)]
    day.run()
    release()
    assert day.run() == (0, "day done")


def test_a_quote_part_s_push_that_hangs_is_alerted_not_pushed_the_next_push_carries_it_and_the_desk_goes_on(
    tmp_path, monkeypatch
):
    """Gap G4 (O1, judge 420): the run's one committer remembers the part's own unpushed commit, so the desk's next
    commit accepts it, checked by content, and pushes it; never refused as a stray (decision 51)."""
    day = fixture_day(tmp_path, monkeypatch)
    hang, release = hanging_pushes(day, monkeypatch)
    after_parts = datetime.combine(day.day, time(14, 57, 30), IST)  # the parts' push hangs, the desk's do not
    day.clock.on_condition = [(lambda: day.committed(f"Desk run {day.day} step forecasts_v4"), hang),
                              (lambda: day.clock.now >= after_parts, release)]  # fmt: skip
    code, line = day.run()
    assert code == 1 and line.startswith("day done with problems:") and "quotes_done" in line
    assert any("quote part nifty committed, NOT pushed (the next push carries it)" in text and "push not confirmed"
               in text for text in day.slack.sent)  # fmt: skip
    assert f"3 pm quotes {day.day} nifty" in day.origin_subjects()  # carried by the desk's next push
    assert day.step("exits")["book1_rules"]["reviewed"] is True and no_lock_left(day)


def test_a_command_that_never_ends_is_stopped_at_its_limit_and_the_day_goes_on(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    day.children.script[("desk", "book1")] = Foreground(24 * 60, lambda: (0, []))  # Book 1's decision never returns
    code, line = day.run()
    assert (code, line) == (1, "day done with problems: book1")
    assert day.step("book1")["reason"].startswith("stopped after 10 minutes without ending")
    assert day.step("decisions")["book1_rules"]["decision"] == "no decision (late)"
    assert day.step("exits")["book1_rules"]["reviewed"] is True
    assert [text for text in day.slack.sent if "step book1 failed" in text] and no_lock_left(day)
