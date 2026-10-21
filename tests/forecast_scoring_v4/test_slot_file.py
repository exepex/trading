"""The v4 slot registrations (the freeze plan, response 287; judge 184's note; ChatGPT review 119): one row per slot,
refused when it would change who is a member or hide misses."""

from datetime import date

import pytest

from fno.constants import V1_RV_1S, V2_RV_5S, V3_RV_20S, V4_SLOT_AI, V4_SLOT_RULES, V6_BIG_MOVE_1S
from fno.forecast_scoring.v4 import wiring
from fno.forecast_scoring.v4.records import Registration
from fno.forecast_scoring.v4.slot_file import COLUMNS, RegistrationRefused, SlotFile

FREEZE_NEXT = date(2026, 10, 28)  # the first session after a freeze on 27 Oct


def slot_file(tmp_path, *rows, first_eligible=lambda q: FREEZE_NEXT):
    file = tmp_path / "v4_slots.csv"
    file.write_text(",".join(COLUMNS) + "\n" + "".join(",".join(r) + "\n" for r in rows))
    return SlotFile(file, first_eligible)


def row(question=V6_BIG_MOVE_1S, slot=V4_SLOT_RULES, name="weather_vix_v1", start="2026-10-28", on="2026-10-27"):
    return (question, slot, name, start, on, "DESK_DECISIONS 15 Oct decision 70")


def test_rows_become_registrations_and_no_file_means_none(tmp_path):
    found = slot_file(tmp_path, row(), row(V2_RV_5S, name="v2_close_blend")).registered()
    assert found == {
        (V6_BIG_MOVE_1S, V4_SLOT_RULES): Registration("weather_vix_v1", FREEZE_NEXT),
        (V2_RV_5S, V4_SLOT_RULES): Registration("v2_close_blend", FREEZE_NEXT),
    }
    assert SlotFile(tmp_path / "absent.csv", lambda q: None).registered() == {}


@pytest.mark.parametrize(
    "bad",
    [
        row(V3_RV_20S),  # V3 is reported only, never a member
        row(slot="hybrid_v2"),  # not a slot
        row(start="2026-10-28", on="2026-10-29"),  # declared after its misses start
        row(start="2026-10-29"),  # starts after the first eligible session: one day's miss hidden
    ],
)
def test_a_registration_that_changes_membership_or_hides_misses_is_refused(tmp_path, bad):
    with pytest.raises(RegistrationRefused):
        slot_file(tmp_path, bad).registered()


def test_a_second_row_for_a_slot_is_refused_even_with_another_forecaster(tmp_path):
    with pytest.raises(RegistrationRefused, match="second registration"):
        slot_file(tmp_path, row(), row(name="v6_ewma_t4")).registered()


def test_a_start_on_the_first_eligible_session_or_before_any_eligible_value_is_accepted(tmp_path):
    assert slot_file(tmp_path, row(start="2026-10-28")).registered()  # on the first eligible session
    later_v1 = row(V1_RV_1S, name="v1_close_blend", start="2026-11-20", on="2026-11-19")
    assert slot_file(tmp_path, later_v1, first_eligible=lambda q: None).registered()  # V1 not eligible yet
    ai = row(slot=V4_SLOT_AI, name="book3_ai_v2", start="2026-10-28")
    assert slot_file(tmp_path, ai).registered()[(V6_BIG_MOVE_1S, V4_SLOT_AI)].forecaster == "book3_ai_v2"


def test_before_the_freeze_the_repository_registers_no_slot():
    assert not wiring.FREEZE_FILE.exists() and wiring._first_eligible(V6_BIG_MOVE_1S) is None
    assert wiring._registry().registered() == {}
