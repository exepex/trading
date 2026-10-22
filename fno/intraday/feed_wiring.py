"""Composition root of the A16h feed probe (story A16h): the full Groww client is built here and wrapped at once,
the feed in `ReadOnlyFeed`, the REST client in A16's `ReadOnlyGroww` (one index quote per index for ATM); the
instrument tokens come from Groww's public instrument list (the SDK's own `INSTRUMENT_CSV_URL`). Nothing else holds
`GrowwFeed` or `GrowwAPI`."""

from __future__ import annotations

import csv
import io
import json
import time as clock_module
import urllib.request

from ..config import ROOT
from ..models import now_ist
from ..providers.groww import GrowwProvider
from .feed_gate import alongside_gate, catch_up_gate
from .feed_probe import FeedProbe
from .feed_universe import INDICES, universe
from .index_reading import quote_reading
from .ledger import SlotLedger
from .read_only import ReadOnlyGroww
from .read_only_feed import ReadOnlyFeed
from .wiring import INTRADAY_FOLDER

INSTRUMENTS_TIMEOUT_SECONDS = 60
RUN_LOGS = ROOT / "journal" / "runs"  # O1's daily run log, one file per day


def build_feed_probe(cfg: dict) -> tuple[FeedProbe, ReadOnlyGroww]:
    from growwapi import GrowwFeed

    provider = GrowwProvider(cfg)
    feed = ReadOnlyFeed(GrowwFeed(provider.api))  # signs in once, before the plan's window check
    return FeedProbe(feed, now_ist, clock_module.sleep), ReadOnlyGroww(lambda: provider.api)


def build_universe(client: ReadOnlyGroww, side: int, every_expiry: bool = False):
    from growwapi import GrowwAPI

    with urllib.request.urlopen(GrowwAPI.INSTRUMENT_CSV_URL, timeout=INSTRUMENTS_TIMEOUT_SECONDS) as answer:
        rows = list(csv.DictReader(io.StringIO(answer.read().decode("utf-8"))))
    spots = {}
    for name in INDICES:
        quote = client.get_quote(trading_symbol=name, exchange=client.EXCHANGE_NSE, segment=client.SEGMENT_CASH)
        level, _ = quote_reading(quote)
        if level:
            spots[name] = float(level)
    return universe(rows, spots, now_ist().date(), side, every_expiry)


def build_gate():
    ledger = SlotLedger(INTRADAY_FOLDER)
    return lambda day: alongside_gate(ledger.rows, day)


def build_catch_up_gate():
    """Reads the checkout's run log: pull `main` first (the routine commits it)."""

    def gate(day):
        path = RUN_LOGS / f"{day.isoformat()}.json"
        return catch_up_gate(json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None, day)

    return gate
