"""Judge 80: every part criterion 2 names is held by the replay (risk, validity, alternatives; alternatives are all the
other outcomes, shadow included), and a replay under different code is refused, never passed as a reproduction."""

import json

import pytest

from fno.playbook.code_tree import GitCodeTree
from fno.playbook.decision_run import ReplayRefused, replay
from fno.playbook.history import PlaybookGit
from tests.playbook.builders import commit_all, git
from tests.playbook.evaluation_builders import book_with_open, evaluator

from .builders import SAME_CODE, doc, run_day, snapshot

LOSER = "sc-a-v1_2026-11-27.json"


def contested_run(tmp_path):
    """sc-b wins the last slot; sc-a is "not chosen: slot" with its C2 verdicts; sc-new runs in shadow."""
    playbook = snapshot(doc("sc-a"), doc("sc-b", expected=300.0), doc("sc-new", status="research"),
                        registered_research=("sc-new",))  # fmt: skip
    return run_day(tmp_path, playbook, the_book=book_with_open(2))


def edit(run, name, change):
    path = run / name
    record = json.loads(path.read_text())
    change(record)
    path.write_text(json.dumps(record))


@pytest.mark.parametrize(
    ("field", "change"),
    [
        ("risk", lambda r: r["risk"]["verdicts"][1].update(reason="edited")),
        ("validity", lambda r: r["validity"].update(candidate="edited")),
        ("alternatives", lambda r: r["alternatives"].pop()),
        ("decision", lambda r: r["decision"].update(outcome="chosen")),
    ],
)
def test_an_edit_to_any_part_of_a_record_is_found_by_the_replay(tmp_path, field, change):
    run = contested_run(tmp_path)
    assert replay(run, evaluator(), SAME_CODE) == []
    edit(run, LOSER, change)
    assert replay(run, evaluator(), SAME_CODE) == [f"{LOSER}: {field} differs"]


def test_alternatives_are_all_the_other_outcomes_shadow_included(tmp_path):
    run = contested_run(tmp_path)
    stored = {p.name: json.loads(p.read_text()) for p in run.glob("*.json") if p.name != "inputs.json"}
    outcomes = {r["opportunity_id"] for name, r in stored.items() if name != "no_trade.json"}
    assert outcomes == {"sc-a-v1:2026-11-27", "sc-b-v1:2026-11-27", "sc-new-v1:2026-11-27"}
    for name, record in stored.items():
        others = {a["opportunity_id"] for a in record["alternatives"]}
        assert others == (outcomes if name == "no_trade.json" else outcomes - {record["opportunity_id"]})
    assert {a["mode"] for a in stored[LOSER]["alternatives"]} == {"book", "shadow"}


def test_the_code_tree_matches_only_the_same_committed_code(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "fno").mkdir()
    (tmp_path / "fno" / "rule.py").write_text("LIMIT = 1\n")
    (tmp_path / "config.yaml").write_text("risk: 1\n")
    commit = commit_all(tmp_path)
    tree = GitCodeTree(PlaybookGit(tmp_path))
    assert tree.matches(commit) and not tree.matches("0" * 40)
    (tmp_path / "fno" / "rule.py").write_text("LIMIT = 2\n")
    assert not tree.matches(commit)  # an uncommitted change
    (tmp_path / "fno" / "rule.py").write_text("LIMIT = 1\n")
    (tmp_path / "fno" / "extra.py").write_text("")
    assert not tree.matches(commit)  # an untracked file
    (tmp_path / "fno" / "extra.py").unlink()
    (tmp_path / "notes.md").write_text("not decision code")
    assert tree.matches(commit)


class OtherCode:
    def matches(self, commit):
        return False


def test_a_replay_under_other_code_is_refused_and_a_todays_code_comparison_says_so(tmp_path):
    run = contested_run(tmp_path)
    with pytest.raises(ReplayRefused, match="c{40}.*git worktree add <dir> c{40}"):
        replay(run, evaluator(), OtherCode())
    result = replay(run, evaluator(), OtherCode(), todays_code=True)
    assert result[0].startswith("NOTE: compared with today's code, not the recorded commit") and len(result) == 1
