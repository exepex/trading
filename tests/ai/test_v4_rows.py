"""Story G11 round 1 (criteria 2, 3, 6 and 8, the rows' part): every settled AI book-day is one G7-schema row per
started question, read by G8's own reader; every failure is a non-ok row G8 counts as no forecast; a pending day has
no row; a label is never back-fill."""

from datetime import date

import pytest

from fno.ai.scoring_gate import PENDING, SCORED, UNSCORED, ScoringStatus
from fno.ai.v4_rows import BookDay, v4_rows, v4_status, write_book_day
from fno.constants import BOOK2_HYBRID, BOOK3_AI, V6_BIG_MOVE_1S, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.inputs import ForecastFiles
from fno.forecast_v4_rules import records
from fno.v4_pack.guard import PackBindingRefused

DAY = date(2026, 10, 26)
QUESTIONS = (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S)  # the rules slot's started set at the freeze (V6a, V6b)
PACK = "d" * 64  # the released pack, given to the book in its pointer
VERSION = "book3_ai/v2/sha256:" + "a" * 64 + "/isolation:sealed_same_day"


def book_day(status=SCORED, reason="on time; transcript clean or not drawn", stop_rule=False, values=None,
             book=BOOK3_AI, pack=PACK):  # fmt: skip
    values = {V6_BIG_MOVE_1S: 0.07, V6_BIG_MOVE_5S: 0.21} if values is None else values
    return BookDay(book, DAY, ScoringStatus(status, reason, "sealed_same_day"), stop_rule, values, VERSION,
                   "b" * 64, "c" * 64, "2026-10-26T09:36:00+00:00", pack)  # fmt: skip


def write(folder, day, released=PACK):
    return write_book_day(folder, day, QUESTIONS, released)


def test_an_on_time_day_writes_one_ok_row_per_question_that_g8_reads(tmp_path):
    assert write(tmp_path, book_day()) == 2
    files = ForecastFiles(tmp_path)
    assert files.forecasters(V6_BIG_MOVE_1S) == [BOOK3_AI]
    assert files.values(V6_BIG_MOVE_1S, BOOK3_AI)[DAY].value == 0.07
    assert (
        files.values(V6_BIG_MOVE_5S, BOOK3_AI)[DAY].value == 0.21 and files.values(V6_BIG_MOVE_5S, BOOK3_AI)[DAY].live
    )
    row = records.read(records.path(tmp_path, BOOK3_AI, V6_BIG_MOVE_1S))[DAY.isoformat()]
    assert (row.status, row.label, row.kind, row.slot, row.forecaster_version) == (
        "ok",
        "live",
        "ai",
        "ai_team",
        VERSION,
    )
    assert (row.method_sha256, row.inputs_sha256) == ("b" * 64, "c" * 64)


@pytest.mark.parametrize(
    ("reason", "stop_rule", "status"),
    [("late", False, "late"), ("not_fired", False, "not_fired"), ("no_submission", False, "no_submission"),
     ("not_revealed", False, "not_revealed"), ("invalid", False, "invalid"),
     ("model_mismatch", False, "model_mismatch"), ("exposed", False, "exposed"),
     ("transcript breach: shell, network", False, "breach"),
     ("not_fired", True, "stopped")],
)  # fmt: skip
def test_every_failure_is_a_non_ok_row_g8_counts_as_no_forecast(tmp_path, reason, stop_rule, status):
    assert write(tmp_path, book_day(UNSCORED, reason, stop_rule)) == 2
    for question in QUESTIONS:
        assert ForecastFiles(tmp_path).values(question, BOOK3_AI)[DAY].value is None  # a miss, never a gap
        assert records.read(records.path(tmp_path, BOOK3_AI, question))[DAY.isoformat()].status == status


@pytest.mark.parametrize("reason", ["transcript audit due", "not collected", "weekly audit draw not made yet"])
def test_a_pending_day_has_no_row_yet(tmp_path, reason):
    assert v4_status(book_day(PENDING, reason)) is None and v4_rows(book_day(PENDING, reason), QUESTIONS) == []
    assert write(tmp_path, book_day(PENDING, reason)) == 0 and not list(tmp_path.rglob("*.csv"))


def test_an_unknown_outcome_is_refused_never_guessed():
    with pytest.raises(ValueError, match="has no v4 status"):
        v4_status(book_day(UNSCORED, "a new outcome"))


def test_a_scored_day_missing_one_answer_is_that_questions_invalid_row():
    rows = v4_rows(book_day(values={V6_BIG_MOVE_1S: 0.07}), QUESTIONS)
    assert [(r.status, r.value) for r in rows] == [("ok", "0.07"), ("invalid", "")]


def test_book2_writes_its_hybrid_slot_and_never_a_back_fill_label(tmp_path):
    write(tmp_path, book_day(book=BOOK2_HYBRID))
    rows = [records.read(records.path(tmp_path, BOOK2_HYBRID, q))[DAY.isoformat()] for q in QUESTIONS]
    assert {(r.slot, r.label) for r in rows} == {("hybrid", "live")}


def test_a_day_once_written_never_changes(tmp_path):
    write(tmp_path, book_day())
    assert write(tmp_path, book_day()) == 0  # the same rows again: nothing added
    with pytest.raises(records.RecordConflict):
        write(tmp_path, book_day(UNSCORED, "late"))


def test_a_value_out_of_range_is_refused_before_anything_is_written(tmp_path):
    with pytest.raises(records.InvalidRecord):
        write(tmp_path, book_day(values={V6_BIG_MOVE_1S: 1.4, V6_BIG_MOVE_5S: 0.2}))
    assert not list(tmp_path.rglob("*.csv"))


def test_only_the_fire_logs_flag_makes_a_day_stopped():
    """The flag decides, never a reason's wording (R2/G7, 16 Oct); the flag on another outcome changes nothing."""
    assert v4_status(book_day(UNSCORED, "not_fired")) == "not_fired"
    assert v4_status(book_day(UNSCORED, "late", stop_rule=True)) == "late"


@pytest.mark.parametrize("named", ["e" * 64, ""])
def test_a_pack_other_than_the_released_one_writes_nothing(tmp_path, named):
    with pytest.raises(PackBindingRefused):
        write(tmp_path, book_day(pack=named))
    assert not list(tmp_path.rglob("*.csv"))


def test_a_system_late_day_gives_the_books_no_row_even_when_they_missed(tmp_path):
    with pytest.raises(PackBindingRefused, match="system_late"):
        write(tmp_path, book_day(UNSCORED, "not_fired"), released="")
    assert not list(tmp_path.rglob("*.csv"))
