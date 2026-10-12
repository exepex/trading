from datetime import date, datetime, timedelta

from fno.analytics import Greeks, bs_greeks
from fno.config import load_config
from fno.constants import Direction
from fno.live.contract_picker import ContractPicker, ExitLevels, PickerRules
from fno.live.feeds.participant_oi import FiiDay, FiiPositioning, load_fii_positioning, parse_participant_oi
from fno.live.models import Candle, MarketView
from fno.live.move_check import MoveCheck, move_needed
from fno.live.signals.base import SymbolInputs
from fno.live.signals.day_type import SidewaysDayGuard, path_efficiency
from fno.live.signals.participant_signals import FiiPositioningSignal
from fno.models import IST
from fno.providers.sample import SampleProvider

from .fakes import SESSION_DAY

START = datetime(2026, 10, 13, 9, 15, tzinfo=IST)
CFG = load_config()
PARTICIPANT_FILE = "\n".join(
    [
        '""Participant wise Open Interest (no. of contracts) in Equity Derivatives as on Oct 09, 2026"",,,',
        "Client Type,Future Index Long,Future Index Short,Option Index Call Long,Option Index Put Long,"
        "Option Index Call Short,Option Index Put Short",
        "Client,291627,62104,3396080,3418874,3337345,4049875",
        "FII,34943,328931,600034,1245164,946852,704672",
        "TOTAL,438669,438669,5404257,6021463,5404257,6021463",
    ]
)


def candles(closes):
    out, previous = [], closes[0]
    for i, close in enumerate(closes):
        out.append(
            Candle(START + timedelta(minutes=5 * i), previous, max(previous, close), min(previous, close), close, 1)
        )
        previous = close
    return out


def inputs(**kw):
    base = {"symbol": "NIFTY", "snapshot": None, "candles": [], "benchmark_change_pct": None, "research": None}
    return SymbolInputs(**{**base, **kw})


def test_trend_is_judged_on_the_last_hour_and_waits_until_known():
    guard = SidewaysDayGuard({"min_candles": 6, "window_candles": 12, "min_efficiency": 0.3})
    straight = candles([100 + i for i in range(14)])
    zigzag = candles([100 + (i % 2) for i in range(14)])
    assert path_efficiency(straight) == 1.0 and path_efficiency(zigzag) < 0.1
    assert not guard.evaluate(inputs(candles=straight)).blocked
    assert guard.evaluate(inputs(candles=zigzag)).blocked
    assert "not known yet" in guard.evaluate(inputs(candles=straight[:4])).reason
    choppy_morning_trending_hour = candles([100 + (i % 2) for i in range(20)] + [101 + i for i in range(12)])
    assert not guard.evaluate(inputs(candles=choppy_morning_trending_hour)).blocked


def test_move_needed_solves_delta_and_gamma():
    assert move_needed(10.0, Greeks(delta=0.5, gamma=0.0, theta=0.0, vega=0.0)) == 20.0
    with_gamma = move_needed(10.0, Greeks(delta=0.5, gamma=0.01, theta=0.0, vega=0.0))
    assert 0.5 * with_gamma + 0.005 * with_gamma**2 == __import__("pytest").approx(10.0)


def test_move_check_refuses_unrealistic_targets_and_notes_the_ratio():
    chain = SampleProvider(CFG).chain("NIFTY", date(2026, 10, 27))
    quote = chain.get(chain.atm_strike(), "CE")
    greeks = bs_greeks(chain.spot, quote.strike, chain.years_to_expiry(), 0.065, quote.iv / 100, "CE")
    assert MoveCheck(max_needed_to_likely=0.1).problem(chain, quote.ltp, greeks).startswith("needs more than 0.1x")
    assert MoveCheck(max_needed_to_likely=50).problem(chain, quote.ltp, greeks) is None
    strict = ContractPicker(
        PickerRules(min_open_interest=0),
        ExitLevels(),
        CFG["position_rules"],
        10_000,
        None,
        MoveCheck(max_needed_to_likely=0.1),
    )
    view = MarketView("NIFTY", Direction.BULLISH, 0.6, 0.8, strong_evidence=True)
    idea, reason = strict.pick(view, chain, SESSION_DAY)
    assert idea is None and "needs more than 0.1x the move the market expects" in reason
    relaxed = ContractPicker(
        PickerRules(min_open_interest=0),
        ExitLevels(),
        CFG["position_rules"],
        10_000,
        None,
        MoveCheck(max_needed_to_likely=50),
    )
    idea, _ = relaxed.pick(view, chain, SESSION_DAY)
    assert any("the market expects" in note for note in idea.notes)


def test_participant_file_parsing_and_fii_shift():
    rows = parse_participant_oi(PARTICIPANT_FILE)
    fii = FiiDay.from_row(date(2026, 10, 9), rows["FII"])
    assert round(fii.futures_long_share, 3) == 0.096
    asked = []

    def fetch(url):
        asked.append(url)
        return PARTICIPANT_FILE if "09102026" in url or "08102026" in url or "07102026" in url else None

    positioning = load_fii_positioning(fetch, date(2026, 10, 12), sessions=3)
    assert [d.day.isoformat() for d in positioning.days] == ["2026-10-07", "2026-10-08", "2026-10-09"]
    assert not any("10102026" in u or "11102026" in u for u in asked)  # weekends are never requested
    assert positioning.futures_shift() == 0.0


def test_fii_signal_votes_on_change_for_indices_only():
    day = date(2026, 10, 1)
    days = tuple(
        FiiDay(day + timedelta(days=i), share, tilt)
        for i, (share, tilt) in enumerate([(0.08, -0.40), (0.08, -0.40), (0.10, -0.30)])
    )
    signal = FiiPositioningSignal(0.6)
    vote = signal.evaluate(inputs(symbol="NIFTY", fii=FiiPositioning(days)))
    assert vote.score > 0.9 and "added" in vote.reason
    assert signal.evaluate(inputs(symbol="RELIANCE", fii=FiiPositioning(days))) is None
    assert signal.evaluate(inputs(symbol="NIFTY", fii=FiiPositioning(days[:2]))) is None
