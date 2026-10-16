"""Story F1t criteria 7 and 10: a decided run is committed only after F1t's check; a refusal, any decider exception or a
failed check puts every write path back to its state just before `decide()` (agreed with F6), including a shared
ledger row written earlier, and records the evidence."""

import pytest

from fno.ai_trading.promote import Promoter
from fno.ai_trading.write_snapshot import WriteSnapshot
from fno.constants import BOOK3_AI
from fno.playbook.decision_store import DecisionStore
from tests.ai.fakes import git

from .builders import DAY, FakeDecider, accepted, write_paths

LEDGER = "research/ledger.csv"


@pytest.fixture(autouse=True)
def checkout(tmp_path):
    """Each test's folder is a git checkout with one tracked playbook file, as the daily run's is."""
    (tmp_path / "playbook").mkdir()
    (tmp_path / "playbook/registry.csv").write_text("name,version\n", encoding="utf-8")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")


def promote(tmp_path, decider, book="book2_hybrid"):
    return Promoter(tmp_path, {book: decider}).promote(accepted(tmp_path, book), write_paths(book))


def test_a_good_run_is_promoted_with_its_files(tmp_path):
    decider = FakeDecider(tmp_path, extra={"journal/book2_hybrid/validity_failures.csv": "row\n"})
    promotion = promote(tmp_path, decider)
    assert promotion.promoted and promotion.run_id == f"{DAY.isoformat()}-r1"
    assert [p.name for p in promotion.paths] == [promotion.run_id, "validity_failures.csv"]


@pytest.mark.parametrize("changes, why", [
    ({"common_pack_sha256": "0" * 64}, "common_pack_sha256 is"),
    ({"private_pack_sha256": "0" * 64}, "private_pack_sha256 is"),
    ({"model_served": "claude-sonnet-5-5"}, "model_served is"),
    ({"session_id": "another"}, "session_id is"),
    ({"served": {"playbook": "p"}}, "served does not name the decision version"),
])  # fmt: skip
def test_a_run_that_fails_the_check_is_never_kept(tmp_path, changes, why):
    promotion = promote(tmp_path, FakeDecider(tmp_path, changes=changes))
    assert not promotion.promoted and why in promotion.reason and promotion.refused_run
    assert DecisionStore(tmp_path, "book2_hybrid").runs(DAY) == [] and promotion.paths == ()


def test_a_record_the_d3_schema_refuses_is_never_kept(tmp_path):
    promotion = promote(tmp_path, FakeDecider(tmp_path, changes={"reason": None, "chosen_action": None}))
    assert not promotion.promoted and "must fill" in promotion.reason


def test_a_second_run_of_the_day_is_refused(tmp_path):
    promotion = promote(tmp_path, FakeDecider(tmp_path, second_run=True))
    assert not promotion.promoted and "2 runs of book2_hybrid" in promotion.reason
    assert DecisionStore(tmp_path, "book2_hybrid").runs(DAY) == []


def test_a_returned_file_outside_the_write_paths_is_refused_and_put_back(tmp_path):
    promotion = promote(tmp_path, FakeDecider(tmp_path, extra={"playbook/registry.csv": "row\n"}))
    assert not promotion.promoted and "outside the version's write paths" in promotion.reason
    assert (tmp_path / "playbook/registry.csv").read_text() == "name,version\n"  # back to HEAD


class Sneaky(FakeDecider):
    """Writes a file it does not return: in a folder a later step commits, or inside its own write paths."""

    def __init__(self, root, path):
        super().__init__(root)
        self.path = path

    def decide(self, accepted):
        decided = super().decide(accepted)
        (self.root / self.path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / self.path).write_text("stray\n", encoding="utf-8")
        return decided


@pytest.mark.parametrize("path", ["playbook/new-v1.yaml", "playbook/registry.csv", "journal/book2_hybrid/stray.txt"])
def test_a_file_written_but_not_returned_is_refused_and_put_back(tmp_path, path):
    promotion = promote(tmp_path, Sneaky(tmp_path, path))
    assert not promotion.promoted and f"wrote files it did not return (never committed, put back): {path}" in (
        promotion.reason
    )
    assert (
        not (tmp_path / "playbook/new-v1.yaml").exists() and not (tmp_path / "journal/book2_hybrid/stray.txt").exists()
    )
    assert (tmp_path / "playbook/registry.csv").read_text() == "name,version\n"


def test_a_change_made_before_decide_outside_the_paths_is_kept(tmp_path):
    (tmp_path / "playbook/registry.csv").write_text("name,version\nb0,1\n", encoding="utf-8")  # an earlier step's
    assert promote(tmp_path, FakeDecider(tmp_path)).promoted
    assert (tmp_path / "playbook/registry.csv").read_text() == "name,version\nb0,1\n"


def test_a_refusal_or_any_exception_restores_every_write_path_to_its_snapshot(tmp_path):
    (tmp_path / LEDGER).parent.mkdir(parents=True)
    (tmp_path / LEDGER).write_text("header\nfactory row written before decide\n", encoding="utf-8")
    before = WriteSnapshot.take(tmp_path, write_paths(BOOK3_AI))
    extra = {LEDGER: "book3 trial row\n", "journal/book3_ai/proposals/2026-10-19.json": "{}"}
    for decider in (FakeDecider(tmp_path, extra=extra, refuse="private pack does not rebuild"),
                    FakeDecider(tmp_path, extra=extra, fail=KeyError("width"))):  # fmt: skip
        promotion = promote(tmp_path, decider, BOOK3_AI)
        assert not promotion.promoted and LEDGER in promotion.restored
        assert before.changed() == [] and DecisionStore(tmp_path, BOOK3_AI).runs(DAY) == []
    assert (tmp_path / LEDGER).read_text() == "header\nfactory row written before decide\n"
    assert promotion.reason == "the decider failed: KeyError: 'width'"


def test_a_book_with_no_decider_is_refused_and_nothing_written(tmp_path):
    promotion = Promoter(tmp_path, {}).promote(accepted(tmp_path), write_paths("book2_hybrid"))
    assert not promotion.promoted and "no decider is wired" in promotion.reason


def test_the_snapshot_of_empty_paths_restores_to_empty(tmp_path):
    snapshot = WriteSnapshot.take(tmp_path, ("journal/book2_hybrid/",))
    (tmp_path / "journal/book2_hybrid/new/deep").mkdir(parents=True)
    (tmp_path / "journal/book2_hybrid/new/deep/f.txt").write_text("x")
    assert snapshot.restore() == ["journal/book2_hybrid/new/deep/f.txt"]
    assert not (tmp_path / "journal/book2_hybrid/new").exists()


class Malformed(FakeDecider):
    """Writes a valid run plus a record file that is not JSON: the check itself cannot read it."""

    def decide(self, accepted):
        decided = super().decide(accepted)
        (decided.run / "broken.json").write_text("{not json", encoding="utf-8")
        return decided


def test_a_run_the_check_cannot_read_is_refused_and_put_back(tmp_path):
    promotion = promote(tmp_path, Malformed(tmp_path))
    assert not promotion.promoted and "unreadable" in promotion.reason
    assert DecisionStore(tmp_path, "book2_hybrid").runs(DAY) == []


def test_git_status_renames_in_either_column_and_spaces_are_parsed(tmp_path):
    from fno.ai_trading.write_snapshot import GitWorktree

    (tmp_path / "c d.txt").write_text("x")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "add", "c d.txt")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "c d")
    git(tmp_path, "mv", "c d.txt", "e f.txt")
    (tmp_path / "new file.txt").write_text("y")
    assert GitWorktree(tmp_path).changed() == {"e f.txt", "new file.txt"}
