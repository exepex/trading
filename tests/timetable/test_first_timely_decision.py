"""Story D3b criteria 1-3, with real git: E3's collector takes each book's FIRST original run committed
before the deadline (commit-time order), never a correction; the decisions step lists every other run
of the day in the run log, a correction with what it corrects and why."""

import hashlib
import json
import os
import subprocess
from datetime import date

from fno.constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI
from fno.desk.committed_decisions import D3CommittedDecisions
from fno.playbook.decision_store import SUMS_FILE, DecisionStore
from fno.playbook.history import PlaybookGit

from .fakes import C4, Decisions, Rules, daily_run
from .test_daily_run import NORMAL, at

BOOKS = (BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI)
DEADLINE = at(15, 12, day=NORMAL)
FIXED = {"run_id": f"{NORMAL}-r1", "opportunity_id": "sc-a-v1:2026-11-27"}


def git(root, *args, when=None):
    env = {**os.environ, **({"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when} if when else {})}
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True, env=env).stdout


def repository(root):
    git(root, "init", "-q", "-b", "main")
    for key, value in (("user.email", "t@example.org"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
        git(root, "config", key, value)


def commit_run(root, book, n, minute, corrects=None):
    """Writes run r<n> of `book` and commits it with the committer clock at 15:<minute> IST."""
    run = DecisionStore(root, book).day_folder(NORMAL) / f"{NORMAL}-r{n}"
    run.mkdir(parents=True)
    record = {"corrects": corrects, "reason": "corrected: wrong lot size recorded" if corrects else ""}
    (run / "a.json").write_text(json.dumps(record))
    (run / SUMS_FILE).write_text("sums\n")
    git(root, "add", "--", str(run.relative_to(root)))
    git(root, "commit", "-q", "-m", f"{book} r{n}", when=f"{NORMAL}T15:{minute:02d}:00+05:30")


def collector(root):
    return D3CommittedDecisions(root, PlaybookGit(root))


def test_the_first_of_two_timely_original_runs_is_collected_for_every_book(tmp_path):
    repository(tmp_path)
    for book in BOOKS:
        commit_run(tmp_path, book, 1, 3)
        commit_run(tmp_path, book, 2, 7)  # also before the deadline: the latest, which E3 used to take
    for book in BOOKS:
        assert collector(tmp_path).committed(book, NORMAL, DEADLINE).run_id == f"{NORMAL}-r1"


def test_a_timely_correction_is_never_collected_and_is_listed_with_what_it_corrects(tmp_path):
    repository(tmp_path)
    commit_run(tmp_path, BOOK1_RULES, 1, 3)
    commit_run(tmp_path, BOOK1_RULES, 2, 5, corrects=FIXED)
    source = collector(tmp_path)
    taken = source.committed(BOOK1_RULES, NORMAL, DEADLINE)
    assert taken.run_id == f"{NORMAL}-r1"
    [other] = source.others(BOOK1_RULES, NORMAL, taken.run_id)
    assert other["run_id"] == f"{NORMAL}-r2" and other["commit"] and other["committed_at"].startswith(f"{NORMAL}T15:05")
    assert other["corrections"] == [{"corrects": FIXED, "reason": "corrected: wrong lot size recorded"}]


def test_a_day_with_only_a_timely_correction_has_no_timely_decision(tmp_path):
    repository(tmp_path)
    commit_run(tmp_path, BOOK1_RULES, 1, 14)  # the original, after the 15:12 deadline
    commit_run(tmp_path, BOOK1_RULES, 2, 6, corrects=FIXED)  # a correction whose commit time is before it
    assert collector(tmp_path).committed(BOOK1_RULES, NORMAL, DEADLINE) is None


def test_the_decisions_step_lists_the_other_runs_in_the_run_log(root, tmp_path, alerts):
    repository(root)
    commit_run(root, BOOK1_RULES, 1, 3)
    commit_run(root, BOOK1_RULES, 2, 5, corrects=FIXED)
    run, clock, *_ = daily_run(root, tmp_path, alerts, (BOOK1_RULES,), Decisions(), C4(), Rules())
    run.steps.decisions = collector(root)
    run.steps.decisions.observe = lambda: "origin-head"  # no origin here; the pull is not what this tests
    clock.now = DEADLINE
    result = run.steps.collect_decisions(NORMAL).result[BOOK1_RULES]
    assert result["run_id"] == f"{NORMAL}-r1"
    assert [o["run_id"] for o in result["others"]] == [f"{NORMAL}-r2"] and result["others"][0]["corrections"]


def test_no_other_run_adds_no_others_key(tmp_path):
    repository(tmp_path)
    commit_run(tmp_path, BOOK1_RULES, 1, 3)
    assert collector(tmp_path).others(BOOK1_RULES, NORMAL, f"{NORMAL}-r1") == []
    assert collector(tmp_path).others(BOOK1_RULES, date(2026, 10, 15), None) == []


def test_a_ten_run_day_is_ordered_by_commit_time_then_counter_never_by_name(tmp_path):
    """r10 was committed first; the name order would put r10 second and the old latest rule would take r9."""
    repository(tmp_path)
    commit_run(tmp_path, BOOK1_RULES, 10, 1)
    for n in range(1, 10):
        commit_run(tmp_path, BOOK1_RULES, n, 2 + n)
    source = collector(tmp_path)
    assert source.committed(BOOK1_RULES, NORMAL, DEADLINE).run_id == f"{NORMAL}-r10"
    listed = [o["run_id"] for o in source.others(BOOK1_RULES, NORMAL, f"{NORMAL}-r10")]
    assert listed == [f"{NORMAL}-r{n}" for n in range(1, 10)]


def test_an_unreadable_record_makes_only_its_own_run_uncollectable(tmp_path):
    repository(tmp_path)
    commit_run(tmp_path, BOOK1_RULES, 1, 3)
    (DecisionStore(tmp_path, BOOK1_RULES).day_folder(NORMAL) / f"{NORMAL}-r1" / "a.json").write_text("{ broken")
    commit_run(tmp_path, BOOK1_RULES, 2, 5)
    commit_run(tmp_path, BOOK2_HYBRID, 1, 4)
    source = collector(tmp_path)
    assert source.committed(BOOK1_RULES, NORMAL, DEADLINE).run_id == f"{NORMAL}-r2"
    [listed] = source.others(BOOK1_RULES, NORMAL, f"{NORMAL}-r2")
    assert listed["corrections"][0]["unreadable"] == "a.json"
    assert source.committed(BOOK2_HYBRID, NORMAL, DEADLINE).run_id == f"{NORMAL}-r1"


def test_the_collected_run_carries_the_hash_of_its_committed_sums_file(tmp_path):
    repository(tmp_path)
    commit_run(tmp_path, BOOK1_RULES, 1, 3)
    taken = collector(tmp_path).committed(BOOK1_RULES, NORMAL, DEADLINE)
    assert taken.sums_sha256 == hashlib.sha256(b"sums\n").hexdigest()
