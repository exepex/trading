"""Story G11 criterion C13: the AI books' 10 slot registrations, in the protocol's order. Good: written on the
freeze's day after the rules rows, read clean by G8's SlotFile. Bad: before the freeze, or without the rules rows,
nothing is written. Boundary: 09:14:59 of the first session still registers, 09:15:00 is refused; a result SlotFile
refuses is rolled back. Empty: `--print` writes nothing. Idempotent: a second run says "already registered"."""

from datetime import date, datetime, time, timedelta

import pytest

from fno.ai.v4_register import DECISION, SlotRegistrar
from fno.constants import V4_SLOT_AI, V4_SLOT_HYBRID, V4_SLOT_RULES
from fno.forecast_scoring.v4.records import LookRecords
from fno.forecast_scoring.v4.slot_file import SlotFile
from fno.forecast_v4.terms import FAMILY_QUESTIONS
from fno.models import IST

FROZEN = date(2026, 10, 23)  # a Friday: the first session after it is Monday 26 Oct
FIRST = date(2026, 10, 26)
HEADER = "question,slot,forecaster,effective_start,registered_on,decision\n"


def at(day, hh, mm, ss=0):
    return datetime.combine(day, time(hh, mm, ss), IST)


def sessions(first, last):
    return [
        first + timedelta(days=n) for n in range((last - first).days + 1) if (first + timedelta(days=n)).weekday() < 5
    ]


def desk(tmp_path, frozen=True, rules=True, eligible=lambda question: None):
    folder, slots = tmp_path / "v4_scores", tmp_path / "v4_slots.csv"
    freeze = tmp_path / "FREEZE_v4.md"
    if frozen:
        freeze.write_text(f"# Freeze\n\nFrozen on: {FROZEN}\n")
    if rules:
        rows = "".join(f"{q},{V4_SLOT_RULES},rule_{q},{FIRST},{FROZEN},freeze\n" for q in FAMILY_QUESTIONS)
        slots.write_text(HEADER + rows)
    looks = LookRecords(folder, freeze)
    frozen_on = lambda: looks.frozen_on() if looks.frozen() else None  # noqa: E731
    return slots, lambda now: SlotRegistrar(slots, looks, lambda: SlotFile(slots, eligible, frozen_on), sessions,
                                            lambda: now)  # fmt: skip


def test_ten_rows_land_after_the_rules_rows_and_g8_reads_all_fifteen(tmp_path):
    slots, registrar = desk(tmp_path)
    assert registrar(at(FROZEN, 18, 0)).register(write=True) == [
        "Omenix F&O AI v4 slots: 10 rows registered, effective 2026-10-26: v4_slots.csv"
    ]
    found = SlotFile(slots, lambda q: None).registered()
    assert len(found) == 15 and {r.effective_start for r in found.values()} == {FIRST}
    assert found[(FAMILY_QUESTIONS[0], V4_SLOT_HYBRID)].forecaster == "book2_hybrid_v2"
    assert found[(FAMILY_QUESTIONS[-1], V4_SLOT_AI)].forecaster == "book3_ai_v2"
    assert DECISION in slots.read_text() and f",{FIRST},{FROZEN}," in slots.read_text()
    again = registrar(at(FROZEN, 18, 5)).register(write=True)
    assert again == ["Omenix F&O AI v4 slots: already registered (10 rows)"]


REFUSALS = [(False, True, "FREEZE_v4.md does not exist"), (True, False, "no rules row for v1_rv_next_session")]


@pytest.mark.parametrize(("frozen", "rules", "why"), REFUSALS)
def test_before_the_freeze_or_without_the_rules_rows_nothing_is_written(tmp_path, frozen, rules, why):
    slots, registrar = desk(tmp_path, frozen, rules)
    before = slots.read_text() if slots.exists() else None
    [line] = registrar(at(FROZEN, 18, 0)).register(write=True)
    assert line.startswith("Omenix F&O AI v4 slots: refused, nothing written") and why in line
    assert (slots.read_text() if slots.exists() else None) == before


@pytest.mark.parametrize(("now", "written"), [(at(FIRST, 9, 14, 59), True), (at(FIRST, 9, 15), False)])
def test_a_row_must_be_written_before_the_first_session_opens(tmp_path, now, written):
    slots, registrar = desk(tmp_path)
    [line] = registrar(now).register(write=True)
    assert ("10 rows registered" in line) is written and (V4_SLOT_AI in slots.read_text()) is written


def test_a_result_slotfile_refuses_is_rolled_back(tmp_path):
    """G8's SlotFile reads the file once more after the append; a refusal there restores the file as it was."""
    slots, registrar = desk(tmp_path)
    looks = LookRecords(tmp_path / "v4_scores", tmp_path / "FREEZE_v4.md")
    readings = iter([lambda q: None, lambda q: None, lambda q: FROZEN])  # rows(), the append's check, then the result

    def g8():
        return SlotFile(slots, next(readings), looks.frozen_on)

    before = slots.read_text()
    [line] = SlotRegistrar(slots, looks, g8, sessions, lambda: at(FROZEN, 18, 0)).register(write=True)
    assert "refused, nothing written" in line and "after the first eligible session" in line
    assert slots.read_text() == before


def test_print_gives_the_rows_and_writes_nothing(tmp_path):
    slots, registrar = desk(tmp_path)
    before = slots.read_text()
    [text] = registrar(at(FROZEN, 18, 0)).register(write=False)
    assert len(text.splitlines()) == 10 and text.splitlines()[0].startswith("v1_rv_next_session,hybrid,book2_hybrid_v2")
    assert slots.read_text() == before
