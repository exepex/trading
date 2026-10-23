"""Git before writes (orchestrator, 22 Oct 2026, after git-fails-loud's caller audit): `factory register`, `factory
freeze`, `research run` and a playbook status change read git before their first write, so a failed git call leaves
nothing half written; a register or freeze that stopped between its two writes is completed by its rerun."""

from datetime import date
from pathlib import Path

import pytest

from fno.factory.constants import IDEA_KIND, Gate
from fno.factory.gate_order import GateStepError
from fno.factory.registration import RegistrationError
from fno.factory.wiring import build_registration, read_idea
from fno.research_engine.ledger import Ledger, write_ledger
from fno.research_engine.research_cli import record_run
from tests.factory.helpers import commit, git, init_repo, write_card
from tests.factory.shadow_helpers import DAY, freezer, parts, planned_repo
from tests.playbook.builders import changer, commit_all, document, filled_evidence, repository, write
from tests.research_engine.git_failures import require_nothing_written_on_any_git_failure

RUN_DAY = date(2026, 10, 21)
RESULTS = {"experiment": "exp", "period": {"name": "challenge", "start": "2026-01-01", "end": "2026-06-30"},
           "note": "a planted run", "opportunities": [], "decisive": False, "policies": {}}  # fmt: skip


def folder(path: Path) -> Path:
    path.mkdir()
    return path


def unregistered(path: Path) -> Path:
    root = init_repo(folder(path))
    write_card(root)
    return root


def register(root: Path):
    return build_registration(root).register(read_idea("X1", root), DAY)


def planned(path: Path) -> Path:
    return planned_repo(folder(path))


def freeze(root: Path):
    return freezer(root).freeze(read_idea("X1", root), DAY)


def with_trial(path: Path) -> Path:
    root = folder(path)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@example.invalid")
    git(root, "config", "user.name", "test")
    (root / "research" / "exp").mkdir(parents=True)
    Ledger(root).register("P1", "exp", "policy one", "prospective", True, today=RUN_DAY)
    commit(root, "ledger")
    return root


def run(root: Path):
    return record_run(Ledger(root), root / "research" / "exp", RESULTS, ("P1",), decisive=True)


def candidate(path: Path) -> Path:
    root = folder(path)
    write(root / "playbook", document(evidence=filled_evidence(repository(root))))
    commit_all(root, "candidate")
    return root


def to_paper(root: Path):
    return changer(root).change("sc-test", 1, "paper", "owner", RUN_DAY)


ACTIONS = {"factory register": (unregistered, register), "factory freeze": (planned, freeze),
           "research run": (with_trial, run), "playbook status change": (candidate, to_paper)}  # fmt: skip


@pytest.mark.parametrize(("build", "act"), ACTIONS.values(), ids=ACTIONS.keys())
def test_any_failed_git_call_leaves_nothing_written(monkeypatch, tmp_path, build, act):
    require_nothing_written_on_any_git_failure(monkeypatch, tmp_path, build, act)
    root = build(tmp_path / "clean")
    act(root)  # and without a failure, the action writes


def test_a_register_stopped_before_its_gate_row_is_completed_by_its_rerun(tmp_path):
    root = unregistered(tmp_path / "repo")
    card = read_idea("X1", root)
    Ledger(root).register("3", card.experiment, card.description, IDEA_KIND, card.hypothesis, protocol_path=card.path,
                          today=DAY)  # fmt: skip  # the first write done, then the stop
    register(root)
    (row,) = [r for r in parts(root)[0].gates.rows() if r.trial_id == "3"]
    assert (row.gate, row.on, row.commit) == (Gate.IDEA_CARD, DAY.isoformat(), git(root, "rev-parse", "HEAD"))
    assert [r["trial_id"] for r in Ledger(root).rows()] == ["1", "2", "3"]  # never registered twice


def test_a_committed_ledger_row_without_its_gate_row_is_sent_to_backfill(tmp_path):
    root = unregistered(tmp_path / "repo")
    card = read_idea("X1", root)
    Ledger(root).register("3", card.experiment, card.description, IDEA_KIND, card.hypothesis, protocol_path=card.path,
                          today=DAY)  # fmt: skip
    commit(root, "a half registration, committed")
    with pytest.raises(RegistrationError, match="committed without its gate row: run `factory backfill`"):
        register(root)


def test_a_freeze_stopped_before_its_gate_row_is_completed_at_its_frozen_commit(tmp_path):
    root = planned(tmp_path / "repo")
    head = git(root, "rev-parse", "HEAD")
    ledger = parts(root)[1]
    ledger.file.write_text(write_ledger([r | {"protocol_commit": head} if r["trial_id"] == "3" else r
                                         for r in ledger.rows()]))  # fmt: skip
    commit(root, "the half freeze, committed")
    row = freeze(root)
    assert (row.gate, row.commit) == (Gate.REGISTRATION, head)
    assert ledger.rows()[-1]["protocol_commit"] == head  # never refrozen
    ledger.require_registered("3")


def test_a_half_frozen_card_changed_since_its_commit_is_refused(tmp_path):
    root = planned(tmp_path / "repo")
    head = git(root, "rev-parse", "HEAD")
    ledger = parts(root)[1]
    ledger.file.write_text(write_ledger([r | {"protocol_commit": head} if r["trial_id"] == "3" else r
                                         for r in ledger.rows()]))  # fmt: skip
    card = root / "research/ideas/X1.md"
    card.write_text(card.read_text() + "\nA later edit.\n")
    commit(root, "the card changed after the half freeze")
    with pytest.raises(GateStepError, match="already frozen at .*, which is not research/ideas/X1.md as it is now"):
        freeze(root)


def test_a_half_registration_of_another_kind_is_refused_never_adopted(tmp_path):
    root = unregistered(tmp_path / "repo")
    card = read_idea("X1", root)
    Ledger(root).register("3", card.experiment, card.description, "retrospective", card.hypothesis,
                          protocol_path=card.path, today=DAY)  # fmt: skip
    with pytest.raises(RegistrationError, match="kind 'retrospective', not a factory idea"):
        register(root)
    assert parts(root)[0].gates.rows() == []


def test_a_half_freeze_at_a_commit_outside_the_history_is_refused(tmp_path):
    root = planned(tmp_path / "repo")
    git(root, "checkout", "-q", "-b", "elsewhere")
    (root / "other.txt").write_text("x\n")
    elsewhere = commit(root, "a commit on another branch")
    git(root, "checkout", "-q", "-")
    ledger = parts(root)[1]
    ledger.file.write_text(write_ledger([r | {"protocol_commit": elsewhere} if r["trial_id"] == "3" else r
                                         for r in ledger.rows()]))  # fmt: skip
    commit(root, "the half freeze names a commit outside the history")
    with pytest.raises(GateStepError, match="already frozen at"):
        freeze(root)


@pytest.mark.parametrize("field", ["description", "hypothesis"])
def test_a_half_registration_that_no_longer_matches_its_card_is_refused_naming_the_field(tmp_path, field):
    root = unregistered(tmp_path / "repo")
    card = read_idea("X1", root)
    Ledger(root).register("3", card.experiment, card.description, IDEA_KIND, card.hypothesis, protocol_path=card.path,
                          today=DAY)  # fmt: skip
    changed = {"description": ('"X1: a planted idea"', '"X1: changed after the stop"'),
               "hypothesis": ("hypothesis: yes", "hypothesis: no")}[field]  # fmt: skip
    path = root / card.path
    path.write_text(path.read_text().replace(*changed))
    with pytest.raises(RegistrationError, match=f"field '{field}' differs from trial 3's ledger row"):
        register(root)
    assert parts(root)[0].gates.rows() == []
