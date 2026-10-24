"""Story DR1, first dataset: A4h's closes certified from A4h's own raw answers (the shadow phase), by quality only:
integrity, A4h's stamp and index rules, sanity and, for the certified record, NSE's official file."""

import hashlib

import pytest

from fno.close_read.constants import READ, RECHECK
from fno.record_store.constants import CERTIFIED, PROVISIONAL
from fno.storage.raw_library import NoReadableStore
from tests.record_store.helpers import (
    LEVELS,
    OFFICIAL,
    PREVIOUS_OFFICIAL,
    SESSION,
    Official,
    World,
    answer,
    official_values,
)


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
    assert "; the later read supersedes the earlier (NIFTY 50 last differs by 3.75); A4h wrote no" in outcome.line


def test_a_change_of_the_open_alone_is_named_as_such(world):
    world.a4h_saves(READ, answer())
    world.a4h_saves(RECHECK, answer(levels={**LEVELS, "NIFTY BANK": (54965.75, 54901.5)}))
    outcome = world.certifier().certify(SESSION, PROVISIONAL)
    assert "(NIFTY BANK open differs by 1.50)" in outcome.line


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
    assert failed.failure() == "official file: NIFTY 50 last differs by 3.75"


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
        (
            answer(levels={**LEVELS, "NIFTY 50": (0.0, 22700.0)}, ranges={"NIFTY 50": (22760.0, 0.0)}),
            "sanity: NIFTY 50 is not positive",
        ),
        (
            answer(levels={**LEVELS, "NIFTY BANK": (70000.0, 54900.0)}, ranges={"NIFTY BANK": (70010.0, 54880.0)}),
            "closed more than 20% from its open",
        ),
        (answer(levels={**LEVELS, "NIFTY BANK": (55100.0, 54900.0)}), "NIFTY BANK: last outside the day's high-low"),
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


def test_the_certified_record_names_the_recheck_when_it_is_the_closer_read(world):
    """Judge 543 SF2: both reads pass (within 0.01), and the closer one is the record, whichever read it is."""
    world.a4h_saves(READ, answer(levels={**LEVELS, "NIFTY 50": (22741.26, 22700.0)}))  # 0.01 off the official file
    world.a4h_saves(RECHECK, answer())  # equal to the official file
    outcome = world.certifier().certify(SESSION, CERTIFIED)
    assert outcome.recorded and "2 of 2 version(s) passed" in outcome.line
    assert outcome.record.chosen.path.endswith(".recheck.raw.json")


@pytest.mark.parametrize(
    "failure",
    [NoReadableStore("no store to read raw/x.csv from: set the owner's Drive settings"), OSError("sign-in refused")],
)
def test_an_unreadable_official_source_fails_loudly_never_as_not_out_yet(tmp_path, failure):
    """Orchestrator, 24 Oct: "no store can be read" must never look like "the file isn't in Drive yet"."""

    class Unreadable(Official):
        def values(self, day):
            raise failure

    world = World(tmp_path, Unreadable())
    world.a4h_saves(READ, answer())
    outcome = world.certifier().certify(SESSION, CERTIFIED)
    assert not outcome.recorded and outcome.alert
    kind = type(failure).__name__
    assert f"NOT recorded: a source could not be read: NSE's official index-close files could not be read ({kind})" in (
        outcome.line
    )
    assert "in Drive yet" not in outcome.line


def test_a_file_not_archived_yet_stays_an_ordinary_not_recorded_line(tmp_path):
    world = World(tmp_path, Official(None))
    world.a4h_saves(READ, answer())
    outcome = world.certifier().certify(SESSION, CERTIFIED)
    assert not outcome.recorded and not outcome.alert and "no official index-close file in Drive yet" in outcome.line


def test_the_certifier_reads_official_files_through_o9s_one_reader_builder(monkeypatch):
    """One reader builder (judge 558 note 2): the certifier never builds its own store list."""
    import fno.record_store.wiring as wiring

    sentinel = object()
    monkeypatch.setattr(wiring, "build_stored_index_close_files", lambda: sentinel)
    monkeypatch.setattr(wiring, "_drive", lambda env=None: object())
    certifier = wiring.build_certifier("closes", commit=False)
    assert certifier.rules.official.files is sentinel


@pytest.mark.parametrize(
    "official, words",
    [
        (Official(official_values(ranges={"NIFTY 50": (22762.5, 22690.0)})), "NIFTY 50 high differs by 2.50"),
        (Official(official_values(ranges={"NIFTY BANK": (55010.0, 54875.0)})), "NIFTY BANK low differs by 5.00"),
        (
            Official(OFFICIAL, {**PREVIOUS_OFFICIAL, "Nifty 50": {"close": 22700.0}}),
            "NIFTY 50 previous_close differs by 12.40",
        ),
        (Official(OFFICIAL, None), "no official index-close file in Drive for the previous session"),
    ],
)
def test_the_certified_record_checks_the_day_range_and_previous_close_too(tmp_path, official, words):
    """Rules version 2 (A4h-2): FL1-1f's evening reads the high, low and previous close, so they are certified."""
    world = World(tmp_path, official)
    world.a4h_saves(READ, answer())
    outcome = world.certifier().certify(SESSION, CERTIFIED)
    assert not outcome.recorded and words in outcome.line


def test_india_vixs_range_is_recorded_never_certified(tmp_path):
    world = World(tmp_path, Official(official_values(ranges={"INDIA VIX": (15.0, 12.0)})))
    world.a4h_saves(READ, answer())
    assert world.certifier().certify(SESSION, CERTIFIED).recorded


def test_a_previous_file_lacking_an_index_is_named_by_its_own_file(tmp_path):
    """Judge 554's note: the previous close's source is the previous session's file, not today's."""
    previous = {k: v for k, v in PREVIOUS_OFFICIAL.items() if k != "Nifty 50"}
    world = World(tmp_path, Official(OFFICIAL, previous))
    world.a4h_saves(READ, answer())
    assert (
        "NIFTY 50 previous_close not in ind_close_all_22102026.csv"
        in world.certifier().certify(SESSION, CERTIFIED).line
    )
