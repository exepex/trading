from datetime import date

from fno.constants import Direction, OiBuildup
from fno.live.market_view import MarketViewBuilder, ViewThresholds, combine
from fno.live.models import SignalVote, UnderlyingSnapshot, oi_buildup
from fno.live.research.research_context import NewsSignal, ResearchSnapshot, summarise_news
from fno.live.signals.base import SymbolInputs
from fno.live.signals.guards import BanListGuard, EarningsGuard, MarketStressGuard
from fno.live.signals.positioning import FuturesOiBuildup
from fno.live.signals.price_action import IntradayTrend, OpeningRangeBreakout, RelativeStrength, VwapPosition
from fno.live.signals.registry import build_guard_rules, build_signal_rules
from fno.live.signals.research_signals import ModelScore, NewsSentiment

from .fakes import at, trending_candles


def inputs(step_pct=0.15, change_pct=2.0, oi_pct=8.0, research=None, banned=()):
    snap = UnderlyingSnapshot(
        "RELIANCE", last_price=100 * (1 + change_pct / 100), previous_close=100.0, oi_change_pct=oi_pct
    )
    return SymbolInputs(
        "RELIANCE",
        snap,
        trending_candles(100, step_pct, 30),
        0.3,
        research or ResearchSnapshot(),
        set(banned),
        at(11, 45),
    )


def test_price_action_rules_agree_on_a_steady_rally():
    rally = inputs(step_pct=0.15)
    for rule in (OpeningRangeBreakout(1.0), VwapPosition(1.0), IntradayTrend(1.0), RelativeStrength(1.0)):
        assert rule.evaluate(rally).score > 0, rule.name


def test_price_action_rules_agree_on_a_steady_fall():
    fall = inputs(step_pct=-0.15, change_pct=-2.0)
    for rule in (OpeningRangeBreakout(1.0), VwapPosition(1.0), IntradayTrend(1.0), RelativeStrength(1.0)):
        assert rule.evaluate(fall).score < 0, rule.name


def test_opening_range_abstains_before_the_window_closes():
    early = inputs()
    early.candles = early.candles[:2]
    assert OpeningRangeBreakout(1.0, {"minutes": 15}).evaluate(early) is None


def test_oi_buildup_reading():
    assert oi_buildup(1.5, 6.0) is OiBuildup.LONG_BUILDUP
    assert oi_buildup(-1.5, 6.0) is OiBuildup.SHORT_BUILDUP
    assert oi_buildup(1.5, -6.0) is OiBuildup.SHORT_COVERING
    assert oi_buildup(-1.5, -6.0) is OiBuildup.LONG_UNWINDING
    assert oi_buildup(0.01, 6.0) is OiBuildup.UNCLEAR
    assert FuturesOiBuildup(1.0).evaluate(inputs(change_pct=-2.0, oi_pct=9.0)).score == -1.0


def test_research_votes_and_trust():
    research = ResearchSnapshot(news={"RELIANCE": NewsSignal(0.4, 2, 0, "Order win")}, model_prob_up={"RELIANCE": 0.58})
    news_vote = NewsSentiment(1.0, {"full_scale": 0.4, "unverified_factor": 0.5}).evaluate(inputs(research=research))
    assert news_vote.score == 0.5  # full positive, halved for unverified
    assert ModelScore(1.0, {"full_scale": 0.1}).evaluate(inputs(research=research)).score == 0.8


def test_summarise_news_drops_rumours():
    rows = [
        {"ticker": "TCS", "sentiment": 0.5, "status": "rumour", "title": "x"},
        {"ticker": "TCS", "sentiment": -0.2, "status": "corroborated", "title": "y"},
    ]
    news = summarise_news(rows)["TCS"]
    assert news.items == 1 and news.trusted_items == 1 and news.mean_sentiment == -0.2


def test_guards_block():
    research = ResearchSnapshot(next_earnings={"RELIANCE": date(2026, 10, 13)}, stress=True)
    case = inputs(research=research, banned=("RELIANCE",))
    assert BanListGuard().evaluate(case).blocked
    assert EarningsGuard({"min_days_before_results": 2}).evaluate(case).blocked
    assert MarketStressGuard().evaluate(case).blocked


def test_combine_and_view_thresholds():
    votes = [SignalVote("a", 1.0, 1.0, ""), SignalVote("b", 0.5, 1.0, ""), SignalVote("c", -0.5, 1.0, "")]
    score, agreement = combine(votes)
    assert round(score, 3) == 0.333 and round(agreement, 3) == 0.667
    rules = build_signal_rules({"vwap": {"weight": 1}, "intraday_trend": {"weight": 1}, "opening_range": {"weight": 1}})
    view = MarketViewBuilder(rules, build_guard_rules({"ban_list": {}}), ViewThresholds()).build(inputs())
    assert view.direction is Direction.BULLISH and not view.blocked


def test_registry_rejects_unknown_rules():
    try:
        build_signal_rules({"astrology": {"weight": 1}})
    except ValueError as exc:
        assert "astrology" in str(exc)
        return
    raise AssertionError("unknown rule must be rejected")
