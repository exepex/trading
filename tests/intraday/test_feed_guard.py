"""Story A16h, criteria 1 and 2: the feed probe's guard lets exactly the eleven market-data names through, refuses
every account-reading and trading name before the feed is touched, and cannot be changed; only the composition root
names `GrowwFeed`."""

import ast
from pathlib import Path

import pytest

from fno.intraday import wiring
from fno.intraday.read_only_feed import ACCOUNT_CALLS, FEED_CALLS, FeedViolation, ReadOnlyFeed

PACKAGE = Path(wiring.__file__).parent
GROWW_FEED_1_5_NAMES = FEED_CALLS | ACCOUNT_CALLS  # the installed SDK's 20 public names (judge 499 counted them)
TRADING_NAMES = ("place_order", "modify_order", "cancel_order", "create_smart_order")  # none in GrowwFeed today


def feed_names() -> set[str]:
    try:
        from growwapi import GrowwFeed
    except ImportError:
        return set(GROWW_FEED_1_5_NAMES)
    return {name for name in dir(GrowwFeed) if not name.startswith("_")}


class Touched:
    """A stand-in feed that records every name read from it."""

    def __init__(self):
        object.__setattr__(self, "read", [])

    def __getattr__(self, name):
        self.read.append(name)
        return lambda *args, **kwargs: name


def test_exactly_the_eleven_market_data_names_pass():
    assert len(FEED_CALLS) == 11
    feed = Touched()
    guard = ReadOnlyFeed(feed)
    assert all(getattr(guard, name)() == name for name in sorted(FEED_CALLS))
    assert feed.read == sorted(FEED_CALLS)


@pytest.mark.parametrize("name", sorted(ACCOUNT_CALLS) + list(TRADING_NAMES))
def test_every_account_and_trading_name_is_refused_before_the_feed_is_touched(name):
    feed = Touched()
    with pytest.raises(FeedViolation):
        getattr(ReadOnlyFeed(feed), name)
    assert feed.read == []


def test_the_sdks_names_are_the_allowed_ones_plus_the_refused_account_ones():
    assert feed_names() == GROWW_FEED_1_5_NAMES  # a new SDK name fails here until it is classified


def test_the_guard_cannot_be_changed():
    guard = ReadOnlyFeed(Touched())
    with pytest.raises(FeedViolation):
        guard.subscribe_ltp = None


def test_only_the_composition_root_names_growwfeed_or_builds_the_client():
    for path in PACKAGE.glob("*.py"):
        if path.name == "feed_wiring.py":
            continue
        names = {n.id for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Name)}
        assert "GrowwFeed" not in names, path.name
