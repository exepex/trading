from datetime import timedelta

from fno.config import load_config
from fno.constants import EVENT_PRICE_SHOCK, SessionPhase
from fno.live.feeds.live_prices import parse_groww_ltp
from fno.live.research.research_context import ResearchSnapshot
from fno.live.runner import LiveRunner
from fno.live.scanner import LiveScanner
from fno.live.shock_detector import ShockDetector, ShockRules
from fno.live.universe import ReferenceData

from .fakes import at
from .test_desk_end_to_end import LOTS, ShiftableSample, services


def test_a_sudden_move_is_a_shock_once_per_cooldown():
    detector = ShockDetector(ShockRules(window_seconds=120, index_move_pct=0.4, stock_move_pct=1.5))
    t = at(11, 0)
    assert detector.observe("NIFTY", 22500, t) is None
    assert detector.observe("NIFTY", 22540, t + timedelta(seconds=20)) is None  # +0.18%
    shock = detector.observe("NIFTY", 22400, t + timedelta(seconds=40))  # -0.62% from the high
    assert shock and shock.direction == -1 and shock.move_pct < -0.4
    assert detector.observe("NIFTY", 22300, t + timedelta(seconds=60)) is None  # cooling down
    assert detector.observe("TCS", 3000, t) is None and detector.observe("TCS", 3030, t + timedelta(seconds=20)) is None
    slow = ShockDetector()
    slow.observe("NIFTY", 22500, t)
    assert slow.observe("NIFTY", 22400, t + timedelta(minutes=5)) is None  # outside the 2-minute window


def test_groww_ltp_parsing():
    assert parse_groww_ltp({"NSE_RELIANCE": 2500.5, "NSE_TCS": {"ltp": 3000.0}, "NSE_X": 0}) == {
        "RELIANCE": 2500.5,
        "TCS": 3000.0,
    }


class FakePrices:
    def __init__(self, path):
        self.path = list(path)

    def prices(self, symbols):
        return {"NIFTY": self.path.pop(0)} if self.path else {}


def test_a_shock_on_a_held_name_re_checks_open_trades_at_once(tmp_path):
    market = ShiftableSample(load_config(), as_of=at(11, 0))
    svc = services(tmp_path, market)
    reference = ReferenceData(loaded_on=at(11, 0).date(), lot_sizes=LOTS)
    LiveScanner(svc).run_cycle(at(11, 0), SessionPhase.TRADING, reference, ResearchSnapshot())
    assert svc.desk.open_trades()[0]["underlying"] == "NIFTY"
    svc.live_prices = FakePrices([22900, 22500])
    runner = LiveRunner(svc)
    runner.reference, runner.state.day = reference, at(11, 0).date()
    runner.tick(at(11, 1))
    reviewed_at = runner.state.last_review
    runner.tick(
        at(
            11,
            1,
        )
        + timedelta(seconds=25)
    )  # NIFTY -1.7% in 25 seconds
    shocks = svc.store.payloads(EVENT_PRICE_SHOCK, at(11, 0).date())
    assert shocks and shocks[0]["symbol"] == "NIFTY" and shocks[0]["held"] is True
    assert runner.state.last_review > reviewed_at  # reviewed again straight away, not 2 minutes later
