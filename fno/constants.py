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

# News statuses from the market-brief verification pipeline that must never support a trade.
UNTRUSTED_NEWS_STATUSES = ("rumour", "promotional", "contradicted")
TRUSTED_NEWS_STATUSES = ("confirmed_primary", "corroborated")
