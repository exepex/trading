"""The only Groww object a read-only caller holds (story A16, criterion 10; A14c part 2): an allow-list over the SDK
client, one list per caller (the recorder's is the default).

The client `growwapi.GrowwAPI` can place, modify and cancel orders (design 6.6: "a key that can trade"). The recorder
needs five read calls and a few constants, so this wrapper lets exactly those through and refuses every other name
before it reaches the SDK. The client itself is built (and signed in, after 06:00 IST each day) by `GrowwProvider`;
the wrapper is made around it in the composition root only. A guard, not a sandbox: it makes a trading call
impossible by mistake and visible in review."""

from __future__ import annotations

import re
from collections.abc import Callable

READ_CALLS = frozenset({"get_quote", "get_option_chain", "get_expiries", "get_contracts", "get_historical_candles"})
CONSTANTS = frozenset(
    {"EXCHANGE_NSE", "SEGMENT_CASH", "SEGMENT_FNO", "CANDLE_INTERVAL_MIN_1", "CANDLE_INTERVAL_MIN_15"}  # 15: A16b
)
ALLOWED = READ_CALLS | CONSTANTS
# Every growwapi.GrowwAPI name that creates, changes or cancels an order starts with one of these verbs (dir() of the
# SDK 1.5, 16 Oct 2026: six names, none of them a read). No caller's list may hold one, so an allow-list can never be
# widened into a trading client by mistake; matched by prefix, so the trading names themselves never appear here.
TRADING_VERBS = re.compile(r"^(place|modify|cancel|create)_")
# The positive rule every caller's list must meet first (judge 356): only public reads named get_<lower_snake> and
# UPPER_CASE constants; never a private name, and never a sign-in, token or session call, whatever its prefix.
PUBLIC_READ, CONSTANT = re.compile(r"get_[a-z0-9_]+"), re.compile(r"[A-Z][A-Z0-9_]*")
CREDENTIAL_WORDS = re.compile(r"token|session|secret|password|login|auth")


class ReadOnlyViolation(AttributeError):
    """A name outside the allow-list was asked for; nothing reached the SDK."""


class ReadOnlyGroww:
    __slots__ = ("__client", "__allowed")

    def __init__(self, client: Callable[[], object], allowed: frozenset[str] = ALLOWED):
        refused = sorted(name for name in allowed if not _allowed_name(name))
        if refused:
            raise ReadOnlyViolation(
                f"an allow-list may hold only public reads and constants, not: {', '.join(refused)}"
            )
        trading = sorted(
            name for name in allowed if TRADING_VERBS.match(name)
        )  # the second line, should the first ever change
        if trading:
            raise ReadOnlyViolation(f"an allow-list may not hold an order call: {', '.join(trading)}")
        object.__setattr__(self, "_ReadOnlyGroww__client", client)  # called on each use: Groww's token renews daily
        object.__setattr__(self, "_ReadOnlyGroww__allowed", frozenset(allowed))

    def __getattr__(self, name: str):
        if name not in self.__allowed:
            raise ReadOnlyViolation(f"{name} is not a read call this client may use")
        return getattr(self.__client(), name)

    def __setattr__(self, name: str, value) -> None:
        raise ReadOnlyViolation("the read-only client cannot be changed")


def _allowed_name(name: str) -> bool:
    readable = PUBLIC_READ.fullmatch(name) or CONSTANT.fullmatch(name)
    return bool(readable) and not CREDENTIAL_WORDS.search(name.lower())
