"""Story G11 round 1 (criteria 2, 3, 6 and 8, the rows' part): every settled AI book-day is one G7-schema row per
started question, read by G8's own reader; every failure is a non-ok row G8 counts as no forecast; a pending day has
no row; a label is never back-fill."""

from datetime import date

import pytest

from fno.ai.scoring_gate import PENDING, SCORED, UNSCORED, ScoringStatus
from fno.ai.stop_rule import STOPPED as STOP_RULE_REASON
from fno.ai.v4_rows import BookDay, v4_rows, v4_status, write_book_day
from fno.constants import BOOK2_HYBRID, BOOK3_AI, V6_BIG_MOVE_1S, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.inputs import ForecastFiles
from fno.forecast_v4_rules import records

DAY = date(2026, 10, 26)
QUESTIONS = (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S)  # the rules slot's started set at the freeze (V6a, V6b)
NOT_FIRED_BY_STOP_RULE = "the routine was not fired: " + STOP_RULE_REASON.format(count=2, window=20, days="x")
VERSION = "book3_ai/v2/sha256:" + "a" * 64 + "/isolation:sealed_same_day"


def book_day(status=SCORED, reason="on time; transcript clean or not drawn", notes=(), values=None, book=BOOK3_AI):
    values = {V6_BIG_MOVE_1S: 0.07, V6_BIG_MOVE_5S: 0.21} if values is None else values
    return BookDay(book, DAY, ScoringStatus(status, reason, "sealed_same_day"), list(notes), values, VERSION,
                   "b" * 64, "c" * 64, "2026-10-26T09:36:00+00:00")  # fmt: skip


def test_an_on_time_day_writes_one_ok_row_per_question_that_g8_reads(tmp_path):
    assert write_book_day(tmp_path, book_day(), QUESTIONS) == 2
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
    ("reason", "notes", "status"),
    [("late", (), "late"), ("not_fired", ("the routine was not fired: trigger refused",), "not_fired"),
     ("no_submission", (), "no_submission"), ("not_revealed", (), "not_revealed"), ("invalid", (), "invalid"),
     ("model_mismatch", (), "model_mismatch"), ("exposed", (), "exposed"),
     ("transcript breach: shell, network", (), "breach"),
     ("not_fired", (NOT_FIRED_BY_STOP_RULE,), "stopped")],
)  # fmt: skip
def test_every_failure_is_a_non_ok_row_g8_counts_as_no_forecast(tmp_path, reason, notes, status):
    assert write_book_day(tmp_path, book_day(UNSCORED, reason, notes), QUESTIONS) == 2
    for question in QUESTIONS:
        assert ForecastFiles(tmp_path).values(question, BOOK3_AI)[DAY].value is None  # a miss, never a gap
        assert records.read(records.path(tmp_path, BOOK3_AI, question))[DAY.isoformat()].status == status


@pytest.mark.parametrize("reason", ["transcript audit due", "not collected", "weekly audit draw not made yet"])
def test_a_pending_day_has_no_row_yet(tmp_path, reason):
    assert v4_status(book_day(PENDING, reason)) is None and v4_rows(book_day(PENDING, reason), QUESTIONS) == []
    assert write_book_day(tmp_path, book_day(PENDING, reason), QUESTIONS) == 0 and not list(tmp_path.rglob("*.csv"))


def test_an_unknown_outcome_is_refused_never_guessed():
    with pytest.raises(ValueError, match="has no v4 status"):
        v4_status(book_day(UNSCORED, "a new outcome"))


def test_a_scored_day_missing_one_answer_is_that_questions_invalid_row():
    rows = v4_rows(book_day(values={V6_BIG_MOVE_1S: 0.07}), QUESTIONS)
    assert [(r.status, r.value) for r in rows] == [("ok", "0.07"), ("invalid", "")]


def test_book2_writes_its_hybrid_slot_and_never_a_back_fill_label(tmp_path):
    write_book_day(tmp_path, book_day(book=BOOK2_HYBRID), QUESTIONS)
    rows = [records.read(records.path(tmp_path, BOOK2_HYBRID, q))[DAY.isoformat()] for q in QUESTIONS]
    assert {(r.slot, r.label) for r in rows} == {("hybrid", "live")}


def test_a_day_once_written_never_changes(tmp_path):
    write_book_day(tmp_path, book_day(), QUESTIONS)
    assert write_book_day(tmp_path, book_day(), QUESTIONS) == 0  # the same rows again: nothing added
    with pytest.raises(records.RecordConflict):
        write_book_day(tmp_path, book_day(UNSCORED, "late"), QUESTIONS)


def test_a_value_out_of_range_is_refused_before_anything_is_written(tmp_path):
    with pytest.raises(records.InvalidRecord):
        write_book_day(tmp_path, book_day(values={V6_BIG_MOVE_1S: 1.4, V6_BIG_MOVE_5S: 0.2}), QUESTIONS)
    assert not list(tmp_path.rglob("*.csv"))
