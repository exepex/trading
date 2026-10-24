"""Story O12e, criteria 1, 2, 4 and 5: ledger trial ids sit in blocks claimed for their experiment; the check finds
each way they do not, the seed turns history into blocks, and `Ledger.register` and the freezes refuse an unclaimed id.
"""

from pathlib import Path

import pytest

from fno.config import ROOT
from fno.numbering.blocks import LEDGER, LEDGER_TRIAL, TrialClaims, ledger_trials, seed_blocks
from fno.numbering.check import check_numbers
from fno.numbering.registry import read_rows
from fno.numbering.seed import seed_registries
from fno.numbering.seed_pin import read_pins, seeded_digest, write_pins
from fno.research_engine.ledger import COLUMNS, LEDGER_FILE, Ledger, TrialNotClaimed
from tests.numbering.helpers import HEADER, write

STAMP = "2026-10-25T00:00:00Z"
CLAIMS = HEADER + f"1-2,old,existing,\n3-6,edge2-f6,session_x,{STAMP}\n"


def trial(n: int, experiment: str) -> str:
    return f"{n},{experiment},trial {n},prospective,no,2026-10-25,,,,\n"


def checkout(tmp_path: Path, claims: str = CLAIMS, trials: str = "") -> Path:
    """Two history trials and their pinned block, then `claims` as the registry and `trials` appended."""
    ledger = ",".join(COLUMNS) + "\n" + trial(1, "old") + trial(2, "old") + trials
    write(tmp_path, {LEDGER: ledger, LEDGER_TRIAL.registry: HEADER + "1-2,old,existing,\n"})
    write_pins(tmp_path, {LEDGER_TRIAL.name: seeded_digest(read_rows(tmp_path / LEDGER_TRIAL.registry))})
    return write(tmp_path, {LEDGER_TRIAL.registry: claims})


def test_the_checks_ledger_is_b4s_ledger():
    assert LEDGER == LEDGER_FILE


def test_trials_in_their_experiments_block_pass_and_a_block_not_used_yet_is_a_claim_being_written(tmp_path):
    assert check_numbers(checkout(tmp_path, trials=trial(3, "edge2-f6") + trial(4, "edge2-f6-weekly"))) == []


def test_a_trial_in_no_block_fails(tmp_path):
    found = check_numbers(checkout(tmp_path, trials=trial(7, "edge2-f6")))
    assert found == [
        f"{LEDGER}: trial 7 (edge2-f6) is in no block of {LEDGER_TRIAL.registry}; claim one first: python "
        "tools/claim_number.py ledger-trial <experiment-prefix> --session <id> --count <k>"
    ]


@pytest.mark.parametrize("experiment", ["edge1-rules", "edge2-f60", "edge2"])
def test_a_trial_in_another_experiments_block_fails(tmp_path, experiment):
    found = check_numbers(checkout(tmp_path, trials=trial(3, experiment)))
    assert found == [f"{LEDGER}: trial 3's experiment {experiment} does not start with its block's name edge2-f6 "
                     "(block 3-6)"]  # fmt: skip


def test_overlapping_blocks_fail(tmp_path):
    found = check_numbers(checkout(tmp_path, CLAIMS + f"6-9,edge2-f7,session_y,{STAMP}\n"))
    assert found == [f"{LEDGER_TRIAL.registry}: blocks 3-6 (edge2-f6) and 6-9 (edge2-f7) overlap"]


@pytest.mark.parametrize("block", ["5-3", "x", "3-", "0-2", "07"])
def test_a_malformed_block_fails(tmp_path, block):
    found = check_numbers(checkout(tmp_path, CLAIMS + f"{block},edge2-f7,session_y,{STAMP}\n"))
    assert found == [f"{LEDGER_TRIAL.registry}: row {block},edge2-f7: number is not of this category's form"]


def test_a_history_block_added_after_the_pin_fails(tmp_path):
    found = check_numbers(checkout(tmp_path, CLAIMS + "7,late,existing,\n", trial(7, "late")))
    assert found == [f"{LEDGER_TRIAL.registry}: the seeded rows differ from their pin in fno/numbering/seed_pins.json; "
                     "the seed is history only"]  # fmt: skip


def test_the_seed_makes_one_history_block_per_run_of_one_experiment_and_pins_it(tmp_path):
    trials = trial(3, "a") + trial(4, "a") + trial(5, "b") + trial(7, "b") + trial(8, "b")
    root = checkout(tmp_path, HEADER, trials)
    assert [b.text for b in seed_blocks(ledger_trials(root), [])] == ["1-2", "3-4", "5", "7-8"]
    assert seed_registries(root) == 4 and seed_registries(root) == 0
    rows = read_rows(root / LEDGER_TRIAL.registry)
    assert [(r.number, r.name, r.session) for r in rows] == [
        ("1-2", "old", "existing"), ("3-4", "a", "existing"), ("5", "b", "existing"), ("7-8", "b", "existing"),
    ]  # fmt: skip
    assert read_pins(root)[LEDGER_TRIAL.name] == seeded_digest(rows) and check_numbers(root) == []


def test_main_holds_the_history_and_both_reservations():
    rows = {r.number: (r.name, r.session) for r in read_rows(ROOT / LEDGER_TRIAL.registry)}
    assert rows["101-108"] == ("forecasts-v4", "existing")
    assert rows["109-114"] == ("edge2-f1-weekly-vrp-gate", "session_01VhppcYHXq3yTJBV2UnsWSs")
    assert rows["115-120"] == ("edge2-f6", "session_01Mt6dcBU5kp2htdPN2KmiZH")
    assert [line for line in check_numbers(ROOT) if LEDGER_TRIAL.registry in line or LEDGER in line] == []


def register(root: Path, trial_id: str, experiment: str) -> None:
    Ledger(root).register(trial_id, experiment, "planted", "prospective", False)


def test_register_refuses_an_unclaimed_id_and_another_experiments_block(tmp_path):
    root = checkout(tmp_path)
    with pytest.raises(TrialNotClaimed, match=r"trial 7 is in no block of numbers/ledger-trial.csv: claim one first"):
        register(root, "7", "edge2-f6")
    with pytest.raises(TrialNotClaimed, match=r"trial 4 sits in block 3-6, claimed for experiment 'edge2-f6', not "):
        register(root, "4", "edge1-rules")
    assert [t.id for t in ledger_trials(root)] == [1, 2]  # nothing written


def test_register_takes_a_claimed_id_and_book_3s_named_ids(tmp_path):
    root = checkout(tmp_path)
    register(root, "4", "edge2-f6-weekly")
    register(root, "book3:SC2-a", "book3-strategies")
    assert [r["trial_id"] for r in Ledger(root).rows()] == ["1", "2", "4", "book3:SC2-a"]


def test_the_next_free_id_is_the_lowest_in_the_experiments_block_and_never_another_blocks(tmp_path):
    root = checkout(tmp_path, CLAIMS + f"7-9,edge2-f7,session_y,{STAMP}\n")
    claims = TrialClaims(root)
    assert claims.next_free("edge2-f6-x", {"1", "2", "3"}) == "4"
    with pytest.raises(ValueError, match=r"no free id in a block claimed for experiment 'edge2-f6-x'"):
        claims.next_free("edge2-f6-x", {"3", "4", "5", "6"})  # full, though 7-9 is free
    with pytest.raises(ValueError, match=r"no free id in a block claimed for experiment 'edge3'"):
        claims.next_free("edge3", set())
