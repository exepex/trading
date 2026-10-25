"""Story GB1: the deleting step re-checks every branch, defaults to a dry run and never touches main."""

import csv
import sys

import pytest

from fno.config import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import branch_cleanup  # noqa: E402
from branch_rules import Evidence  # noqa: E402

SHA = "1" * 40
OTHER = "2" * 40
NONE = Evidence({}, frozenset(), frozenset())


def go(plan, held=NONE, apply=True, table=None, delete=None):
    deleted = []
    code = branch_cleanup.run(
        plan, held, apply, delete or deleted.append, table if table is not None else {n: s for n, s, *_ in plan}
    )
    return code, deleted


def test_dry_run_deletes_nothing_and_says_what_would_go(capsys):
    code, deleted = go([("story/a", SHA, "merged", True)], apply=False)
    assert (code, deleted) == (0, []) and "WOULD DELETE story/a" in capsys.readouterr().out


def test_apply_deletes_a_matching_branch():
    assert go([("story/a", SHA, "merged", True)]) == (0, ["story/a"])


def test_a_moved_head_is_skipped(capsys):
    code, deleted = go([("story/a", SHA, "merged", True)], table={"story/a": OTHER})
    assert (code, deleted) == (0, []) and "head moved" in capsys.readouterr().out


def test_a_branch_already_gone_is_skipped():
    assert go([("story/a", SHA, "merged", True)], table={}) == (0, [])


def test_main_is_never_deleted_even_when_the_plan_lists_it():
    assert go([("main", SHA, "oops", True)]) == (0, [])


@pytest.mark.parametrize(
    "held",
    [
        Evidence({"story/a": "in flight"}, frozenset(), frozenset()),
        Evidence({}, frozenset(), frozenset({"story/a"})),
    ],
)
def test_keep_list_and_open_pr_stop_a_listed_branch(held):
    assert go([("story/a", SHA, "merged", True)], held=held) == (0, [])


def test_a_stale_register_row_does_not_stop_a_merged_branch_but_stops_an_unmerged_one():
    held = Evidence({}, frozenset({"story/a"}), frozenset())
    assert go([("story/a", SHA, "merged", True)], held=held) == (0, ["story/a"])
    assert go([("story/a", SHA, "idle", False)], held=held) == (0, [])


def test_a_failed_delete_is_counted_and_the_rest_still_run():
    def delete(name):
        if name == "story/a":
            raise RuntimeError("boom")
        deleted.append(name)

    deleted = []
    code, _ = go([("story/a", SHA, "x", True), ("story/b", SHA, "x", True)], delete=delete)
    assert code == 1 and deleted == ["story/b"]


def write_inventory(path, rows):
    with path.open("w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["branch", "sha", "last_commit_utc", "merged", "commits_not_on_main", "decision", "reason"])
        writer.writerows(rows)


def test_inventory_plan_takes_only_delete_rows(tmp_path):
    path = tmp_path / "inventory.csv"
    write_inventory(path, [["a", SHA, "t", "yes", "0", "delete", "r"], ["b", SHA, "t", "no", "2", "keep-unsure", "r"]])
    assert branch_cleanup.inventory_plan(path) == [("a", SHA, "r", True)]


def test_inventory_with_a_repeated_branch_is_refused(tmp_path):
    path = tmp_path / "inventory.csv"
    write_inventory(path, [["a", SHA, "t", "yes", "0", "delete", "r"]] * 2)
    with pytest.raises(SystemExit, match="listed twice"):
        branch_cleanup.inventory_plan(path)
