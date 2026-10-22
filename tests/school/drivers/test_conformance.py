"""Criteria 6 and 7 (story MS-P1e): every no-trade carries a reason from a's enum, and every driver passes the
shared `Driver` conformance check; the composition root builds the drivers from the repository's own config."""

import pytest
import yaml

from fno.school.constants import REASONS_BY_OUTCOME, NoTradeReason, Outcome, RoadCode
from fno.school.drivers.wiring import build_school_drivers
from tests.school.contracts import builders as cb
from tests.school.contracts import conformance as c
from tests.school.drivers import builders as b

SCENES = {
    RoadCode.NIFTY_MONTHLY: (25_000.0, 50.0, 75, (30, 60)),
    RoadCode.BANKNIFTY_MONTHLY: (50_000.0, 100.0, 30, (30, 60)),
    RoadCode.FINNIFTY_MONTHLY: (24_000.0, 50.0, 65, (30, 60)),
    RoadCode.MIDCPNIFTY_MONTHLY: (13_000.0, 25.0, 120, (30, 60)),
    RoadCode.NIFTY_WEEKLY: (25_000.0, 50.0, 75, (3, 10)),
}
DRIVERS = sorted(b.drivers())


@pytest.mark.parametrize("code", DRIVERS)
def test_the_driver_passes_the_conformance_check(code):
    driver = b.drivers()[code]
    for road in driver.card.roads:
        spot, step, lot, days = SCENES[road]
        road_day, snapshot = b.scene(road, spot, step, lot, days)
        c.check_driver(driver, road_day, snapshot, cb.position())


def test_every_no_trade_carries_a_reason_from_the_enum_and_every_outcome_its_own_kind():
    seen = set()
    for road, (spot, step, lot, days) in SCENES.items():
        road_day, snapshot = b.scene(road, spot, step, lot, days)
        for history in ((), b.history([spot] * 20), b.history([spot * 0.99] * 20)):
            for driver in b.drivers().values():
                if road not in driver.card.roads:
                    continue
                decision = driver.decide(road_day, snapshot, history, ())
                assert decision.outcome in (Outcome.TRADE, Outcome.NO_TRADE)
                assert decision.reason in REASONS_BY_OUTCOME[decision.outcome]
                if decision.outcome == Outcome.NO_TRADE:
                    assert decision.reason and decision.proposal is None
                    seen.add(decision.reason)
                else:
                    assert decision.proposal is not None
    assert seen >= {
        NoTradeReason.N0,
        NoTradeReason.NOT_ENOUGH_HISTORY,
        NoTradeReason.NO_EXPIRY_IN_WINDOW,
        NoTradeReason.RULE_NOT_FIRED,
    }


def test_the_composition_root_builds_every_driver_from_the_repository_config():
    cfg = yaml.safe_load((b.ROOT / "config.yaml").read_text(encoding="utf-8"))
    built = build_school_drivers(cfg, b.ROOT)
    assert sorted(d.card.code for d in built) == DRIVERS
    assert cfg["school"]["enabled"] is False  # building drivers does not switch the school on
    road_day, snapshot = b.scene()
    ps4 = next(d for d in built if d.card.code == "PS4").decide(road_day, snapshot, (), ())
    assert ps4.outcome == Outcome.TRADE and ps4.proposal.max_loss <= cfg["school"]["max_loss_rs"]
    assert ps4.proposal.costs > 240.0  # the real charges (brokerage, STT, ...) are inside the maximum loss
