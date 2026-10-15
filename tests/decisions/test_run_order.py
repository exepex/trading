"""Story D3b criterion 4 and decision 61: one order for a day's runs. Ancestry first, then commit time, then the run
counter as a number; uncommitted runs last; a correction is known by its records."""

import json
from datetime import date

import pytest

from fno.playbook.decision_store import SUMS_FILE, DecisionStore
from fno.playbook.run_order import corrections, ordered_runs, run_counter

DAY = date(2026, 10, 14)
BOOK = "book1_rules"


class FakeCommits:
    """Which commit added each run's sums file, at what time, and which commits descend from which."""

    def __init__(self, added: dict[str, tuple[str, str]], ancestors: set[tuple[str, str]] = frozenset()):
        self.added, self.ancestors = added, set(ancestors)

    def added_in(self, path):
        return self.added.get(path.rsplit("/", 2)[-2])

    def is_ancestor(self, older, newer):
        return (older, newer) in self.ancestors


def runs(root, *counters):
    store = DecisionStore(root, BOOK)
    for n in counters:
        run = store.day_folder(DAY) / f"{DAY}-r{n}"
        run.mkdir(parents=True)
        (run / SUMS_FILE).write_text("")
    return store.runs(DAY)


def ids(ordered):
    return [r.run_id for r in ordered]


def at(minute):
    return f"2026-10-14T15:{minute:02d}:00+05:30"


def test_r10_comes_after_r2_by_its_counter_as_a_number_never_by_name(tmp_path):
    folders = runs(tmp_path, *range(1, 11))
    assert [p.name for p in folders][1] == f"{DAY}-r10"  # the folder-name order this replaces
    git = FakeCommits({f"{DAY}-r{n}": ("c", at(5)) for n in range(1, 11)})  # one commit holds all ten
    assert ids(ordered_runs(tmp_path, folders, git)) == [f"{DAY}-r{n}" for n in range(1, 11)]


def test_parallel_commits_are_ordered_by_commit_time_before_the_counter(tmp_path):
    git = FakeCommits({f"{DAY}-r1": ("c1", at(9)), f"{DAY}-r2": ("c2", at(4))})
    assert ids(ordered_runs(tmp_path, runs(tmp_path, 1, 2), git)) == [f"{DAY}-r2", f"{DAY}-r1"]


def test_ancestry_beats_a_fast_clock(tmp_path):
    """r2 was committed after pulling r1 (c1 is c2's ancestor), on a checkout whose clock runs fast: r1 is first."""
    git = FakeCommits({f"{DAY}-r1": ("c1", at(9)), f"{DAY}-r2": ("c2", at(4))}, {("c1", "c2")})
    assert ids(ordered_runs(tmp_path, runs(tmp_path, 1, 2), git)) == [f"{DAY}-r1", f"{DAY}-r2"]


def test_ancestry_holds_through_a_chain_with_a_parallel_run_between(tmp_path):
    """c1 -> c3 by ancestry; c2 is parallel and earliest by the clock: c2, then c1, then c3."""
    added = {f"{DAY}-r1": ("c1", at(6)), f"{DAY}-r2": ("c2", at(3)), f"{DAY}-r3": ("c3", at(1))}
    git = FakeCommits(added, {("c1", "c3")})
    assert ids(ordered_runs(tmp_path, runs(tmp_path, 1, 2, 3), git)) == [f"{DAY}-r2", f"{DAY}-r1", f"{DAY}-r3"]


def test_uncommitted_runs_come_last_by_counter_and_carry_no_commit(tmp_path):
    git = FakeCommits({f"{DAY}-r3": ("c3", at(8))})
    ordered = ordered_runs(tmp_path, runs(tmp_path, 1, 3, 10, 2), git)
    assert ids(ordered) == [f"{DAY}-r3", f"{DAY}-r1", f"{DAY}-r2", f"{DAY}-r10"]
    assert [r.commit for r in ordered] == ["c3", None, None, None]


def test_an_empty_day_and_a_bad_run_name(tmp_path):
    assert ordered_runs(tmp_path, [], FakeCommits({})) == []
    with pytest.raises(ValueError, match="not a decision run ID"):
        run_counter(tmp_path / "2026-10-14-x")


def test_a_correction_is_known_by_any_record_that_names_what_it_corrects(tmp_path):
    [original, fixed] = runs(tmp_path, 1, 2)
    (original / "inputs.json").write_text(json.dumps({"corrects": "inputs are never records"}))
    (original / "a.json").write_text(json.dumps({"corrects": None}))
    names = {"run_id": original.name, "opportunity_id": "sc-a-v1:2026-11-27"}
    (fixed / "a.json").write_text(json.dumps({"corrects": names, "reason": "corrected: wrong lot size recorded"}))
    assert corrections(original) == []
    assert corrections(fixed) == [{"corrects": names, "reason": "corrected: wrong lot size recorded"}]
