"""Shared names and fixed strings. Change a value here, not where it is used."""

from __future__ import annotations

from enum import StrEnum


class Direction(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class OptionKind(StrEnum):
    CALL = "CE"
    PUT = "PE"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class TradeStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class ExitReason(StrEnum):
    STOP_LOSS = "stop loss"
    TRAILING_STOP = "trailing stop"
    TARGET = "target"
    INTRADAY_SQUARE_OFF = "intraday square-off"
    MAX_HOLDING_DAYS = "maximum holding days"
    BEFORE_EXPIRY = "time exit before expiry"
    OVERNIGHT_LIMIT = "overnight exposure limit"
    PERFORMANCE_STOP = "performance kill switch"
    KILL_SWITCH = "kill switch"
    MANUAL = "manual"


class OiBuildup(StrEnum):
    """Futures price move combined with open-interest change."""

    LONG_BUILDUP = "long build-up"  # price up, OI up: fresh buying
    SHORT_BUILDUP = "short build-up"  # price down, OI up: fresh selling
    SHORT_COVERING = "short covering"  # price up, OI down: sellers exiting
    LONG_UNWINDING = "long unwinding"  # price down, OI down: buyers exiting
    UNCLEAR = "unclear"


class SessionPhase(StrEnum):
    CLOSED = "closed"
    PRE_OPEN = "pre-open"
    OPENING_RANGE = "opening range"  # first minutes: watch, do not enter
    TRADING = "trading"  # entries allowed
    NO_NEW_ENTRIES = "no new entries"  # manage open trades only
    SQUARE_OFF = "square-off"  # close intraday trades


STRATEGY_LONG_CALL = "long_call"
STRATEGY_LONG_PUT = "long_put"

OPTION_DISPLAY_NAME = {OptionKind.CALL.value: "Call", OptionKind.PUT.value: "Put"}

# Index underlyings and their names on NSE / Yahoo.
INDEX_UNDERLYINGS = ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50")
BENCHMARK_UNDERLYING = "NIFTY"

# Environment variable names (values are never stored in files).
ENV_FNO_SLACK_BOT_TOKEN = "FNO_SLACK_BOT_TOKEN"
ENV_FNO_SLACK_CHANNEL_ID = "FNO_SLACK_CHANNEL_ID"
ENV_FNO_SLACK_WEBHOOK_URL = "FNO_SLACK_WEBHOOK_URL"
# Shared with the market-brief tool for now (owner's decision); only used when a MotherDuck option is chosen.
ENV_MOTHERDUCK_TOKEN = "MOTHERDUCK_TOKEN"
# Groww Trade API (market data only; the desk never places orders)
ENV_GROWW_ACCESS_TOKEN = "GROWW_ACCESS_TOKEN"
ENV_GROWW_API_KEY = "GROWW_API_KEY"
ENV_GROWW_API_SECRET = "GROWW_API_SECRET"
ENV_GROWW_TOTP_SECRET = "GROWW_TOTP_SECRET"

# News statuses from the market-brief verification pipeline that must never support a trade.
UNTRUSTED_NEWS_STATUSES = ("rumour", "promotional", "contradicted")
TRUSTED_NEWS_STATUSES = ("confirmed_primary", "corroborated")

# Shadow book (one paper lot of every idea, for grading) event names in the results store
EVENT_SHADOW_OPENED = "shadow_opened"
EVENT_SHADOW_CLOSED = "shadow_closed"

# Fast news watcher (fno/live/news): API keys live only in ~/.trading.env or the environment
ENV_FINNHUB_API_KEY = "FINNHUB_API_KEY"
ENV_MARKETAUX_API_TOKEN = "MARKETAUX_API_TOKEN"
ENV_ASKNEWS_API_KEY = "ASKNEWS_API_KEY"
EVENT_NEWS_STORY = "news_story"  # a story seen for the first time, by the source that had it first
EVENT_NEWS_SIGHTING = "news_sighting"  # the same story from another source later, with the delay
NEWS_THEME_WORLD = "WORLD"  # world-risk news (war, oil, central banks, tariffs) that moves indices


class NewsCredibility(StrEnum):
    """How far a story can be trusted, from who carried it."""

    EXCHANGE_FILING = "exchange filing"  # the company's own filing with NSE/BSE: the primary source
    WIDELY_REPORTED = "widely reported"  # three or more independent outlets
    CORROBORATED = "corroborated"  # two independent outlets
    SINGLE_SOURCE = "single source"  # one outlet only: treat with care
