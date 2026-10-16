"""Judge 237's two boundaries. A fall of a single 0.05 step is still `held` (owner, 15 Oct 2026, da0f769d: every fall
waits for the owner). An incremental run counts a holding that exits in the very first session after the previous row's
`coverage_through`, so incremental still equals full. A held SF 100 at scale 11.7 needs 74,815 / 53,950 = 1.38675,
computed 1.40."""

from datetime import date

import pytest

from fno.nse_margins.stress_log import HELD, LastRow, decide

from .stress_days import planted
from .test_stress_run import SEED, SPIKE, THROUGH, run


@pytest.mark.parametrize(("in_force", "unrounded", "expected"), [
    (1.45, 1.38675, (1.45, 1.40, HELD)),  # one step below the seed
    (1.41, 1.38675, (1.41, 1.40, HELD)),  # a hand factor 0.01 above the computed one
    (1.45, 1.449, (1.45, 1.45, "applied")),  # rounds to the factor in force: not a fall
])  # fmt: skip
def test_a_one_step_fall_is_held(in_force, unrounded, expected):
    assert decide(LastRow(in_force, None, None), unrounded) == expected


@pytest.mark.parametrize("rows", [SEED, SEED + "2026-10-20,1.41,,,applied,owner hand value,,\n"], ids=["1.45", "1.41"])
def test_a_planted_run_one_step_below_the_factor_in_force_is_held(tmp_path, rows):
    code, row, sent = run(tmp_path, planted(THROUGH, {SPIKE: 11.7}), rows=rows)
    assert code == 0 and row[2:5] == ["1.4", "1.386747", "held"] and "waits for the owner" in sent[0]


def test_a_holding_exiting_in_the_first_session_after_the_last_coverage_is_counted(tmp_path):
    """Run 1 (7 Dec) covers to Fri 4 Dec; the 20 Nov peak's holdings exit Mon 7 Dec, the next session."""
    files = planted(date(2026, 12, 8), {date(2026, 11, 20): 20.0})
    _, first, _ = run(tmp_path / "steps", files, run_day=date(2026, 12, 7))
    assert first[6] == "2026-12-04"
    _, incremental, _ = run(tmp_path / "steps", files, run_day=date(2026, 12, 8))
    _, full, _ = run(tmp_path / "once", files, run_day=date(2026, 12, 8))
    assert incremental[1:5] == full[1:5] and incremental[3] == "1.686747"
