"""Story G11 round 1 (criteria 2, 3, 6 and 8, the rows' part): every settled AI book-day is one G7-schema row per
started question, read by G8's own reader; every failure is a non-ok row G8 counts as no forecast; a pending day has
no row; a label is never back-fill."""

from datetime import date, timedelta

import pytest

from fno.ai.scoring_gate import PENDING, SCORED, UNSCORED, ScoringStatus
from fno.ai.v4_rows import BookDay, v4_rows, v4_status, write_book_day
from fno.ai.versions import current_version
from fno.constants import BOOK2_HYBRID, BOOK3_AI, FORECAST_PROTOCOL_V4, V4_SLOT_AI, V6_BIG_MOVE_1S, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.inputs import ForecastFiles
from fno.forecast_scoring.v4.reconcile import AiSlotDays
from fno.forecast_scoring.v4.records import Registration, SlotRegistry
from fno.forecast_v4_rules import records
from fno.v4_pack.guard import PackBindingRefused

DAY = date(2026, 10, 26)
QUESTIONS = (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S)  # the rules slot's started set at the freeze (V6a, V6b)
BOOK3_V2 = BOOK3_AI + "_v2"  # the registered forecaster: G8 finds it by its folder
PACK = "d" * 64  # the released pack, given to the book in its pointer
V4 = {book: current_version(book, FORECAST_PROTOCOL_V4) for book in (BOOK2_HYBRID, BOOK3_AI)}  # prompt v2


def book_day(status=SCORED, reason="on time; transcript clean or not drawn", stop_rule=False, values=None,
             book=BOOK3_AI, pack=PACK):  # fmt: skip
    values = {V6_BIG_MOVE_1S: 0.07, V6_BIG_MOVE_5S: 0.21} if values is None else values
    gate = ScoringStatus(status, reason, "sealed_same_day")
    return BookDay(V4[book], DAY, gate, stop_rule, values, "c" * 64, "2026-10-26T09:36:00+00:00", pack)


def write(folder, day, released=PACK):
    return write_book_day(folder, day, QUESTIONS, released)


def test_an_on_time_day_writes_one_ok_row_per_question_that_g8_reads(tmp_path):
    assert write(tmp_path, book_day()) == 2
    files = ForecastFiles(tmp_path)
    assert files.forecasters(V6_BIG_MOVE_1S) == [BOOK3_V2]
    assert files.values(V6_BIG_MOVE_1S, BOOK3_V2)[DAY].value == 0.07
    assert (
        files.values(V6_BIG_MOVE_5S, BOOK3_V2)[DAY].value == 0.21 and files.values(V6_BIG_MOVE_5S, BOOK3_V2)[DAY].live
    )
    row = records.read(records.path(tmp_path, BOOK3_V2, V6_BIG_MOVE_1S))[DAY.isoformat()]
    assert (row.status, row.label, row.kind, row.slot, row.forecaster_version) == (
        "ok",
        "live",
        "ai",
        "ai_team",
        V4[BOOK3_AI].label,
    )
    assert (row.method_sha256, row.inputs_sha256) == (V4[BOOK3_AI].prompt_sha256, "c" * 64)


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
        assert ForecastFiles(tmp_path).values(question, BOOK3_V2)[DAY].value is None  # a miss, never a gap
        assert records.read(records.path(tmp_path, BOOK3_V2, question))[DAY.isoformat()].status == status


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
    rows = [records.read(records.path(tmp_path, BOOK2_HYBRID + "_v2", q))[DAY.isoformat()] for q in QUESTIONS]
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


class RegisteredBook3(SlotRegistry):
    """The ledger row round 3 appends: the ai_team slot of V6a, registered as book3_ai_v2 from DAY."""

    def registered(self):
        return {(V6_BIG_MOVE_1S, V4_SLOT_AI): Registration(BOOK3_V2, DAY)}


def test_a_written_day_settles_g8s_reconciliation_and_a_missing_one_blocks_it(tmp_path):
    """The rows' folder is the registered forecaster's, so G8's look finds them (reconcile.py, read as it stands)."""
    slot_days = AiSlotDays(ForecastFiles(tmp_path), RegisteredBook3(), lambda first, last: [DAY])
    assert [s.day for s in slot_days.unsettled(DAY - timedelta(days=1), DAY)] == [DAY]  # no row yet: blocks the look
    write(tmp_path, book_day(UNSCORED, "no_submission"))
    assert slot_days.unsettled(DAY - timedelta(days=1), DAY) == []  # a miss row settles the day


def test_the_guard_checks_the_book_of_the_version_that_names_the_folder(tmp_path, monkeypatch):
    """Judge 274 add. 1 with the G10 builder (16 Oct): a book2_hybrid_v2 row is checked as book2_hybrid, both read
    from the one registered version."""
    checked = []
    monkeypatch.setattr("fno.ai.v4_rows.check_pack_binding", lambda *args: checked.append(args))
    write(tmp_path, book_day(book=BOOK2_HYBRID))
    assert checked == [(BOOK2_HYBRID, DAY.isoformat(), PACK, PACK)]
    assert (tmp_path / "book2_hybrid_v2").is_dir() and not (tmp_path / BOOK2_HYBRID).exists()


def test_every_row_carries_the_release_records_pack_sha256(tmp_path):
    """G11 C9: the released pack's SHA in G7's pack_sha256 column, on ok rows and misses alike."""
    write(tmp_path, book_day())
    write(tmp_path, book_day(UNSCORED, "late", book=BOOK2_HYBRID))
    for folder in (BOOK3_V2, BOOK2_HYBRID + "_v2"):
        for question in QUESTIONS:
            assert records.read(records.path(tmp_path, folder, question))[DAY.isoformat()].pack_sha256 == PACK
