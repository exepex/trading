"""Story DR1, first dataset: A4h's closes certified from A4h's own raw answers (the shadow phase), by quality only:
integrity, A4h's stamp and index rules, sanity and, for the certified record, NSE's official file."""

import hashlib

import pytest

from fno.close_read.constants import READ, RECHECK
from fno.record_store.constants import CERTIFIED, PROVISIONAL
from tests.record_store.helpers import LEVELS, SESSION, Official, World, answer


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def test_two_agreeing_reads_make_one_provisional_record_and_a_rerun_changes_nothing(world):
    world.a4h_saves(READ, answer())
    world.a4h_saves(RECHECK, answer("23-Oct-2026 15:31"))
    outcome = world.certifier().certify(SESSION, PROVISIONAL)
    assert outcome.recorded, outcome.line
    assert "2 of 2 version(s) passed; 2 passing version(s) agree on NIFTY 50, NIFTY BANK" in outcome.line
    assert outcome.record.chosen.path.endswith(".first.raw.json")
    text = world.records.file_for("closes", SESSION, PROVISIONAL).read_text()
    assert "22741" not in text and "54965" not in text  # a record holds pointers and checks, never a level
    again = world.certifier().certify(SESSION, PROVISIONAL)
    assert again.recorded and "already recorded" in again.line


def test_a_later_read_that_differs_supersedes_the_earlier_and_the_change_is_named(world):
    """Both reads carry NSE's 15:30 stamp (23 Oct's real files): a change after the close is NSE's correction."""
    world.a4h_saves(READ, answer())
    world.a4h_saves(RECHECK, answer(levels={**LEVELS, "NIFTY 50": (22745.0, 22700.0)}))
    outcome = world.certifier().certify(SESSION, PROVISIONAL)
    assert outcome.recorded and outcome.record.chosen.path.endswith(".recheck.raw.json")
    assert "; the later read supersedes the earlier (NIFTY 50 differs by 3.75); A4h wrote no record" in outcome.line


def test_india_vix_may_move_more_than_20_percent_but_must_be_positive(world):
    world.a4h_saves(READ, answer(levels={**LEVELS, "INDIA VIX": (18.0, 13.5)}))  # +33%, a shock day
    assert world.certifier().certify(SESSION, PROVISIONAL).recorded


def test_when_both_reads_agree_with_the_official_file_the_closest_is_certified(world):
    world.a4h_saves(READ, answer())  # equal to the official closes
    world.a4h_saves(RECHECK, answer(levels={**LEVELS, "NIFTY 50": (22741.26, 22700.0)}))  # 0.01 off: still passes
    outcome = world.certifier().certify(SESSION, CERTIFIED)
    assert outcome.recorded and "2 of 2 version(s) passed" in outcome.line
    assert outcome.record.chosen.path.endswith(".first.raw.json")


def test_the_certified_record_chooses_the_read_that_agrees_with_the_official_file(world):
    world.a4h_saves(READ, answer(levels={**LEVELS, "NIFTY 50": (22745.0, 22700.0)}))
    world.a4h_saves(RECHECK, answer("23-Oct-2026 15:31"))
    outcome = world.certifier().certify(SESSION, CERTIFIED)
    assert outcome.recorded and outcome.record.chosen.path.endswith(".recheck.raw.json")
    assert "1 of 2 version(s) passed; closest to NSE's official file ind_close_all_23102026.csv" in outcome.line
    failed = [v for v in outcome.record.verdicts if not v.passed][0]
    assert failed.failure() == "official file: NIFTY 50 differs by 3.75"


def test_no_official_file_yet_means_no_certified_record(tmp_path):
    world = World(tmp_path, Official(None))
    world.a4h_saves(READ, answer())
    outcome = world.certifier().certify(SESSION, CERTIFIED)
    assert not outcome.recorded and "no official index-close file in Drive yet" in outcome.line


@pytest.mark.parametrize(
    "data, words",
    [
        (answer("23-Oct-2026 15:20"), "stamp and indices: NSE stamp 23-Oct-2026 15:20 is before 15:30"),
        (answer("22-Oct-2026 15:30"), "is not today's session"),
        (answer(levels={k: v for k, v in LEVELS.items() if k != "NIFTY BANK"}), "NIFTY BANK missing"),
        (answer(levels={**LEVELS, "NIFTY 50": (0.0, 22700.0)}), "sanity: NIFTY 50 is not positive"),
        (answer(levels={**LEVELS, "NIFTY BANK": (70000.0, 54900.0)}), "closed more than 20% from its open"),
        (answer(levels={**LEVELS, "INDIA VIX": (-1.0, 13.5)}), "sanity: INDIA VIX is not positive"),
        (b"<html>busy</html>", "layout: not JSON"),
    ],
)
def test_a_bad_answer_never_becomes_the_record_and_the_reason_is_named(world, data, words):
    world.a4h_saves(READ, data)
    outcome = world.certifier().certify(SESSION, PROVISIONAL)
    assert not outcome.recorded and words in outcome.line


def test_bytes_that_differ_from_their_receipt_fail_integrity(world, tmp_path):
    world.a4h_saves(READ, answer())
    (tmp_path / "drive/data/closes/2026/10/2026-10-23.first.raw.json").write_bytes(answer("23-Oct-2026 15:35"))
    outcome = world.certifier().certify(SESSION, PROVISIONAL)
    assert not outcome.recorded and "integrity: bytes differ from their receipt" in outcome.line


def test_no_version_at_all_is_named(world):
    outcome = world.certifier().certify(SESSION, PROVISIONAL)
    assert not outcome.recorded and outcome.line.endswith("NOT recorded: no staged version")


def test_the_shadow_line_says_whether_a4hs_record_cites_the_chosen_read(world):
    world.a4h_saves(READ, answer())
    world.a4h_records({"read": "first", "raw_sha256": hashlib.sha256(answer()).hexdigest()})
    assert world.certifier().certify(SESSION, PROVISIONAL).line.endswith("; matches A4h's record")


def test_a_record_published_first_by_another_certifier_is_a_conflict_not_an_overwrite(world):
    world.a4h_saves(READ, answer())
    certifier = world.certifier()

    class OtherWins:
        def commit(self, what):  # the pull brings another certifier's record for the same session and level
            file = world.records.file_for("closes", SESSION, PROVISIONAL)
            file.write_text(file.read_text().replace(certifier_sha, "0" * 64))

    certifier_sha = hashlib.sha256(answer()).hexdigest()
    world.records.committer = OtherWins()
    outcome = certifier.certify(SESSION, PROVISIONAL)
    assert not outcome.recorded and "conflict: the record names 000000000000" in outcome.line
