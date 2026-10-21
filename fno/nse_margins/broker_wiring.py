"""Composition root of story A14c part 2, the daily broker margin check: A14's rows and archived SPAN files, Groww's
read-only calculator behind this caller's allow-list, O9's data store and verified Drive cache, A7's calendar and
#fno-desk. Apart from `wiring.py` so the root of the jobs GitHub Actions runs (A14, A14c part 1) builds no broker
client: Actions holds no Groww key, and this check runs only in O1's routine."""

from __future__ import annotations

import os
import time

from ..composition import build_alert_sender
from ..config import ROOT
from ..constants import NIFTY_SYMBOL
from ..intraday.read_only import ReadOnlyGroww
from ..models import now_ist
from ..providers.groww import GrowwProvider
from ..storage.data_wiring import build_data_store, build_drive_cache
from .broker_basket import BasketBuilder
from .broker_check import BrokerCheckParts, BrokerMarginCheck
from .broker_port import BROKER_CHECK_CALLS, GrowwBrokerMargins
from .broker_record import BrokerRecord
from .calculator import NseIndexOptionExposure
from .wiring import build_drive_span_files, build_margin_log, build_row_builder, build_trading_days

WRITER = "margins stress-broker-check"  # the receipts' writer
PACE_SECONDS = 2.0  # one broker request every 2 seconds (part 2 text: about 35 s for 15 baskets)


def build_broker_check(cfg: dict, env=os.environ) -> BrokerMarginCheck:
    provider = GrowwProvider(cfg)
    broker = GrowwBrokerMargins(ReadOnlyGroww(lambda: provider.api, BROKER_CHECK_CALLS))
    log = build_margin_log(cfg, ROOT)
    parts = BrokerCheckParts(
        log.existing, build_drive_span_files(env), BasketBuilder(build_row_builder(cfg)), broker,
        NseIndexOptionExposure(), cfg["lot_sizes"][NIFTY_SYMBOL],
        BrokerRecord(build_data_store(WRITER, env=env), build_drive_cache(env)),
    )  # fmt: skip
    return BrokerMarginCheck(parts, build_trading_days(), now_ist, time.sleep, build_alert_sender(), PACE_SECONDS)
