"""G0 registration end to end in a temporary repository (story R1a, criterion 1; judge 259 notes 2 and 4)."""

from datetime import date

import pytest

from fno.factory.card import CardError
from fno.factory.registration import RegistrationError
from fno.factory.wiring import build_gate_log, build_registration, read_idea
from fno.research_engine.ledger import LEDGER_FILE, Ledger

from .helpers import BLOCK, CARD, commit, git, init_repo, write_card

DAY = date(2026, 10, 17)
TRIAL_2 = BLOCK.replace("trial: 3", "trial: 2").replace("x1-test", "old").replace("X1: a planted idea", "trial 2")


@pytest.fixture
def repo(tmp_path):
    return init_repo(tmp_path)


def snapshot(root):
    return git(root, "status", "--porcelain", "--untracked-files=all"), (root / LEDGER_FILE).read_text()


@pytest.mark.parametrize(("flag", "written"), [("yes", "yes"), ("no", "no")])
def test_register_writes_the_ledger_row_and_the_idea_row(repo, flag, written):
    write_card(repo, BLOCK.replace("hypothesis: yes", f"hypothesis: {flag}"))
    head = git(repo, "rev-parse", "HEAD")
    files = build_registration(repo).register(read_idea("X1", repo), DAY)
    assert files == (CARD, LEDGER_FILE, "research/factory/gates.csv")
    row = Ledger(repo).rows()[-1]
    assert (row["trial_id"], row["experiment"], row["description"]) == ("3", "x1-test", "X1: a planted idea")
    assert (row["kind"], row["hypothesis"], row["registered_on"], row["protocol_path"]) == (
        "prospective", written, "2026-10-17", CARD,
    )  # fmt: skip
    gate = build_gate_log(repo).last("3")
    assert (gate.gate, gate.outcome, gate.on, gate.commit, gate.numbers) == ("G0", "idea", "2026-10-17", head, "")
    commit(repo, "register X1")
    Ledger(repo).require_committed("3")  # B4's guard accepts the committed registration


def test_a_card_with_a_missing_field_writes_nothing(repo):
    write_card(repo, BLOCK.replace("question: planted-question\n", ""))
    before = snapshot(repo)
    with pytest.raises(CardError, match="field 'question' is missing"):
        build_registration(repo).register(read_idea("X1", repo), DAY)
    assert snapshot(repo) == before


@pytest.mark.parametrize("trial", ["2", "4"])
def test_the_trial_must_be_the_next_ledger_number(repo, trial):
    write_card(repo, BLOCK.replace("trial: 3", f"trial: {trial}"))
    before = snapshot(repo)
    with pytest.raises(RegistrationError, match="trial"):
        build_registration(repo).register(read_idea("X1", repo), DAY)
    assert snapshot(repo) == before


def test_other_staged_files_are_refused_before_writing(repo):
    write_card(repo)
    (repo / "notes.md").write_text("unrelated\n")
    git(repo, "add", "notes.md")
    before = snapshot(repo)
    with pytest.raises(RegistrationError, match=r"other files are staged \(notes.md\)"):
        build_registration(repo).register(read_idea("X1", repo), DAY)
    assert snapshot(repo) == before


def test_the_same_card_is_never_registered_twice(repo):
    write_card(repo)
    build_registration(repo).register(read_idea("X1", repo), DAY)
    commit(repo, "register X1")
    write_card(repo, BLOCK.replace("trial: 3", "trial: 4"))
    with pytest.raises(RegistrationError, match="already registered"):
        build_registration(repo).register(read_idea("X1", repo), DAY)


def test_backfill_dates_the_idea_row_by_its_ledger_row(repo):
    write_card(repo, TRIAL_2)
    registered_in = git(repo, "log", "--format=%H", "-1")
    commit(repo, "a later commit, so the row must name the ledger's commit, not HEAD")  # judge 261 note 1
    build_registration(repo).backfill(read_idea("X1", repo))
    rows = build_gate_log(repo).rows()
    ledger_day = Ledger(repo).rows()[1]["registered_on"]
    assert len(rows) == 1 and (rows[0].trial_id, rows[0].gate, rows[0].outcome) == ("2", "G0", "idea")  # idea only
    assert (rows[0].on, rows[0].commit, rows[0].numbers) == (ledger_day, registered_in, "backfilled=yes")
    with pytest.raises(RegistrationError, match="already has a gate-log row"):
        build_registration(repo).backfill(read_idea("X1", repo))


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [("experiment: old", "experiment: other", "experiment"), ('"trial 2"', '"trial 9"', "description"),
     ("hypothesis: yes", "hypothesis: no", "hypothesis")],
)  # fmt: skip
def test_backfill_refuses_a_card_that_differs_from_its_ledger_row(repo, old, new, field):
    write_card(repo, TRIAL_2.replace(old, new))
    with pytest.raises(RegistrationError, match=f"field '{field}' differs"):
        build_registration(repo).backfill(read_idea("X1", repo))
    assert not build_gate_log(repo).file.exists()


def test_backfill_needs_a_registered_trial(repo):
    write_card(repo)
    with pytest.raises(RegistrationError, match="not in research/ledger.csv"):
        build_registration(repo).backfill(read_idea("X1", repo))


def test_a_book3_row_in_the_ledger_never_stops_the_next_numbered_trial(repo):
    """D5 registers `book3:<strategy_id>` rows in the same ledger (fno/book3/registry.py); the next factory trial
    counts numbered rows only, as S1's freeze does (FL1 builder's finding, 21 Oct 2026)."""
    Ledger(repo).register("book3:x-v1", "book3", "Book 3 strategy x-v1", "prospective", True, "s.yaml", DAY)
    commit(repo, "book3 row")
    write_card(repo)
    build_registration(repo).register(read_idea("X1", repo), DAY)
    assert Ledger(repo).rows()[-1]["trial_id"] == "3"
