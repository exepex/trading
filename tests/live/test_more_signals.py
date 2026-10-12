from datetime import date, timedelta

from fno.config import load_config
from fno.live.exit_policy import TrailingStop
from fno.live.market_backdrop import MarketBackdrop, market_breadth
from fno.live.models import UnderlyingSnapshot
from fno.live.research.research_context import ResearchSnapshot
from fno.live.research.research_source import Announcement
from fno.live.signals.base import SymbolInputs
from fno.live.signals.guards import ExpensiveOptionsGuard, realised_volatility
from fno.live.signals.market_signals import GlobalCues, MarketBreadth, SectorStrength, VixDirection
from fno.live.signals.option_signals import OptionWritingPressure
from fno.live.signals.research_signals import AnnouncementCatalyst, BlockDealFlow, ForeignFlow
from fno.live.signals.session_levels import PreviousDayLevels, VolumeConfirmation
from fno.providers.sample import SampleProvider

from .fakes import SESSION_DAY, at, trending_candles

YESTERDAY = SESSION_DAY - timedelta(days=3)  # the Friday before


def inputs(
    change_pct=2.0, research=None, backdrop=None, chain=None, today_volume=1000, industry="Information Technology"
):
    today = [c.__class__(c.start, c.open, c.high, c.low, c.close, today_volume) for c in trending_candles(102, 0.1, 20)]
    history = trending_candles(100, 0.0, 75, day=YESTERDAY)  # flat around 100: high ~100.05, low ~99.95
    snap = UnderlyingSnapshot("TCS", last_price=100 * (1 + change_pct / 100), previous_close=100.0)
    return SymbolInputs(
        "TCS",
        snap,
        today,
        0.5,
        research or ResearchSnapshot(),
        set(),
        at(11, 0),
        history=history,
        chain=chain,
        backdrop=backdrop or MarketBackdrop(),
        industry=industry,
    )


def test_market_backdrop_rules():
    backdrop = MarketBackdrop(
        {"^CNXIT": 1.8}, global_change_pct=-0.6, vix_change_pct=6.0, breadth=0.5, advancers=150, decliners=50
    )
    case = inputs(backdrop=backdrop)
    assert SectorStrength(1.0).evaluate(case).score > 0  # IT +1.8% vs NIFTY +0.5%
    assert MarketBreadth(1.0).evaluate(case).score > 0
    assert GlobalCues(1.0).evaluate(case).score < 0
    assert VixDirection(1.0).evaluate(case).score < 0  # rising fear
    assert SectorStrength(1.0).evaluate(inputs(industry="Chemicals")) is None  # no sector index for it


def test_breadth_ignores_indices():
    snaps = {s: UnderlyingSnapshot(s, 101, 100) for s in ("A", "B", "NIFTY")} | {"C": UnderlyingSnapshot("C", 99, 100)}
    assert market_breadth(snaps) == (1 / 3, 2, 1)


def test_previous_day_breakout_and_volume():
    case = inputs()
    assert PreviousDayLevels(1.0).evaluate(case).score == 1.0  # today ~102+ vs yesterday's high ~100
    assert VolumeConfirmation(1.0).evaluate(inputs(today_volume=1000)) is None  # normal volume says nothing
    heavy = VolumeConfirmation(1.0).evaluate(inputs(today_volume=3000))
    assert heavy.score > 0.9  # 3x normal, backing an up move


def test_option_writing_pressure():
    chain = SampleProvider(load_config()).chain("NIFTY", date(2026, 10, 27))
    for (_strike, kind), quote in chain.quotes.items():
        quote.oi_change = 5000.0 if kind == "PE" else 1000.0  # heavy put writing
    assert OptionWritingPressure(1.0).evaluate(inputs(chain=chain)).score > 0.5
    for quote in chain.quotes.values():
        quote.oi_change = None  # a source without OI change (Groww)
    assert OptionWritingPressure(1.0).evaluate(inputs(chain=chain)) is None


def test_research_rules():
    filing = Announcement("TCS", "Outcome of Board Meeting", "Results", at(9, 0))
    routine = Announcement("TCS", "Copy of Newspaper Publication", "", at(9, 0))
    research = ResearchSnapshot(
        announcements={"TCS": [filing]}, block_deal_net={"TCS": 250e7}, foreign_flows_cr=[-3000, -4000, -6000]
    )
    settings = {"ignored_categories": ["Copy of Newspaper Publication"], "min_move_pct": 1.0}
    assert AnnouncementCatalyst(1.0, settings).evaluate(inputs(research=research)).score > 0
    only_routine = ResearchSnapshot(announcements={"TCS": [routine]})
    assert AnnouncementCatalyst(1.0, settings).evaluate(inputs(research=only_routine)) is None
    assert BlockDealFlow(1.0).evaluate(inputs(research=research)).score == 1.0  # Rs 250 crore bought
    assert ForeignFlow(1.0).evaluate(inputs(research=research)).score == -1.0  # Rs 13,000 crore sold


def test_expensive_options_guard():
    chain = SampleProvider(load_config()).chain("NIFTY", date(2026, 10, 27))  # ~13% implied vol
    calm = inputs(chain=chain)  # the candles barely move: realised vol far below 13%
    assert ExpensiveOptionsGuard({"max_iv_to_realised": 1.6}).evaluate(calm).blocked
    assert realised_volatility(trending_candles(100, 0.1, 10)) is None  # too few bars


def test_trailing_stop():
    trail = TrailingStop(activate_gain_pct=30, lock_pct=50)
    assert not trail.triggered(100, 120, 105)  # never reached +30%
    assert not trail.triggered(100, 140, 125)  # floor is 120
    assert trail.triggered(100, 140, 119)
