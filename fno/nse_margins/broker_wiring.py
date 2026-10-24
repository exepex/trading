"""Composition root of story A14c part 2, the daily broker margin check: A14's rows and archived SPAN files, Groww's
read-only calculator behind this caller's allow-list, A20a's dated lots (the market school's reader), O9's data store
and verified Drive cache, A7's calendar and #fno-desk. Apart from `wiring.py` so the root of the jobs GitHub Actions
runs (A14, A14c part 1) builds no broker client: Actions holds no Groww key, and this check runs only in O1's
routine."""

from __future__ import annotations

import os
import time
from functools import cache

from ..composition import build_alert_sender
from ..config import ROOT
from ..intraday.read_only import ReadOnlyGroww
from ..models import now_ist
from ..providers.groww import GrowwProvider
from ..school.roads.lots import ArchivedLots
from ..school.roads.stored_files import StoredFilesOnly
from ..school.roads.wiring import build_archive_stores
from ..storage.data_wiring import build_data_store, build_drive_cache
from ..storage.raw_library import RawFileLibrary
from .broker_basket import BasketBuilder
from .broker_check import BrokerCheckParts, BrokerMarginCheck
from .broker_lot import NseDatedLot
from .broker_port import BROKER_CHECK_CALLS, GrowwBrokerMargins
from .broker_record import BrokerRecord
from .calculator import NseIndexOptionExposure
from .wiring import build_drive_span_files, build_margin_log, build_row_builder, build_trading_days

WRITER = "margins stress-broker-check"  # the receipts' writer
PACE_SECONDS = 2.0  # one broker request every 2 seconds (measured: 15 baskets and two quotes in about a minute)


def build_broker_check(cfg: dict, env=os.environ) -> BrokerMarginCheck:
    """Groww and Drive are built on first use, so a closed day or an early start needs neither the SDK nor settings
    (judge 630 finding 1). The lot is the row builder's own (one source); A20a's dated lot checks it."""
    provider = cache(lambda: GrowwProvider(cfg))
    broker = GrowwBrokerMargins(ReadOnlyGroww(lambda: provider().api, BROKER_CHECK_CALLS))
    lots = cache(lambda: ArchivedLots(RawFileLibrary(build_archive_stores(), StoredFilesOnly())))
    log = build_margin_log(cfg, ROOT)
    parts = BrokerCheckParts(
        log.existing, lambda day: build_drive_span_files(env)(day), BasketBuilder(build_row_builder(cfg)), broker,
        NseIndexOptionExposure(), NseDatedLot(lots),
        BrokerRecord(lambda: build_data_store(WRITER, env=env), lambda: build_drive_cache(env)),
    )  # fmt: skip
    return BrokerMarginCheck(parts, build_trading_days(), now_ist, time.sleep, build_alert_sender(), PACE_SECONDS)
