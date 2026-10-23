"""The practice clock and a session's dated configuration (MS-SIM-d2)."""

from datetime import date, datetime

from fno.models import IST
from fno.school.simulator.practice.clock import PRACTICE_TIME, practice_clock
from fno.school.simulator.practice.dated import cfg_on
from tests.school.simulator.source import builders as sb

CFG = {"charges": dict(sb.CHARGES), "other": {"kept": 1}}


def test_the_practice_clock_is_after_the_close_the_snapshot_is_stamped_with():
    now = practice_clock(date(2022, 3, 7)).now()
    assert now == datetime(2022, 3, 7, 15, 31, tzinfo=IST) and PRACTICE_TIME.minute == 31
    assert now > datetime(2022, 3, 7, 15, 30, tzinfo=IST)  # a snapshot's finished_at


def test_a_sessions_config_carries_that_dates_stt_and_changes_nothing_else():
    old, new = cfg_on(CFG, sb.TERMS, date(2023, 3, 31)), cfg_on(CFG, sb.TERMS, date(2023, 4, 3))
    assert (old["charges"]["stt_sell_pct"], new["charges"]["stt_sell_pct"]) == (0.05, 0.0625)
    assert old["other"] == CFG["other"] and CFG["charges"]["stt_sell_pct"] == 0.15  # the original is untouched
