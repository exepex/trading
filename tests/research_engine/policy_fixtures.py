"""Synthetic opportunities with known P&L for the policy runner tests (story B3)."""

from __future__ import annotations

from datetime import date, timedelta

from fno.constants import CycleStatus
from fno.research_engine.cycles import Cycle
from fno.research_engine.opportunities import Opportunity
from fno.research_engine.simulator import CycleResult

F1, F2, F3 = "F1_atm_iv_minus_rv20", "F2_vix_above_250d_median", "F3_scheduled_event_in_window"
STRUCTURES = ("BF", "SC", "SF")


def cycle(i: int, start: date = date(2019, 1, 1)) -> Cycle:
    decision = start + timedelta(days=30 * i)
    return Cycle(decision + timedelta(days=40), decision, decision + timedelta(days=1), decision + timedelta(days=19))


def result(c: Cycle, code: str, net: float, status: CycleStatus = CycleStatus.TRADED, max_loss: float = 9000.0):
    traded = status == CycleStatus.TRADED
    return CycleResult(c, code, status, width=300.0, net=net if traded else 0.0, max_loss=max_loss)


def opportunity(i: int, features: dict, nets: dict, statuses: dict | None = None, start=date(2019, 1, 1)):
    c, statuses = cycle(i, start), statuses or {}
    return Opportunity(
        c,
        features,
        {code: result(c, code, nets.get(code, 0.0), statuses.get(code, CycleStatus.TRADED)) for code in STRUCTURES},
    )
