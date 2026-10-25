"""Story F1t criterion 13: the owner's checklist names commands that exist and the daily routine's settings by the
names the code reads, and holds no value of any setting."""

import re

from fno import constants
from fno.ai_trading.__main__ import main
from fno.ai_trading.wiring import ROUTINES
from fno.config import ROOT

CHECKLIST = (ROOT / "docs/stories/F1t-owner-checklist.md").read_text(encoding="utf-8")


def test_every_routine_step_names_a_real_command(capsys):
    for step in re.findall(r"python -m fno\.ai_trading (\w+)", CHECKLIST):
        try:
            main([step, "--help"])
        except SystemExit as ended:
            assert ended.code == 0, step
    assert set(re.findall(r"python -m fno\.ai_trading (\w+)", CHECKLIST)) == {"brief", "seal", "reveal"}


def test_the_settings_are_the_names_the_wiring_reads_and_no_value_is_written():
    names = {name for pair in ROUTINES.values() for name in pair}
    assert names == set(re.findall(r"`(FNO_ROUTINE_BOOK\d_DECISION_\w+)`", CHECKLIST))
    assert names <= {getattr(constants, n) for n in dir(constants) if n.startswith("ENV_")}
    assert "trig_" not in CHECKLIST.replace("`trig_...`", "")


def test_the_switch_keys_in_the_checklist_are_the_ones_the_run_reads():
    from fno.daily.wiring import LIVE_BOOKS

    assert LIVE_BOOKS == ("book2_hybrid", "book3_ai")
    assert "`daily.live_from.book2_hybrid` (or `book3_ai`)" in CHECKLIST
