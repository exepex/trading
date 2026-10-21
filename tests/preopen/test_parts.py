"""The adapters' wiring: Groww's index symbols through A16b's read-only candle source (default NIFTY unchanged)."""

from __future__ import annotations

import sys
from datetime import datetime

import pytest

from fno.config import load_app_config
from fno.intraday.candle_source import GrowwCandleSource
from fno.intraday.index_reading import CANDLE_SYMBOL
from fno.preopen import wiring
from fno.preopen.parts import PartFailed

from .fixtures import DAY, ist


class Api:
    EXCHANGE_NSE, SEGMENT_CASH, CANDLE_INTERVAL_MIN_1 = "NSE", "CASH", "1m"

    def __init__(self):
        self.symbols = []

    def get_historical_candles(self, **request):
        self.symbols.append(request["groww_symbol"])
        return {"candles": []}


def _now() -> datetime:
    return ist(9, 10)


def test_the_candle_source_asks_for_its_symbol_and_defaults_to_nifty():
    api = Api()
    GrowwCandleSource(api, _now, symbol="NSE-BANKNIFTY").minute_candles(DAY)
    GrowwCandleSource(api, _now).minute_candles(DAY)
    assert api.symbols == ["NSE-BANKNIFTY", CANDLE_SYMBOL]


def test_the_capture_reads_gift_the_fo_list_then_nifty_and_banknifty_from_groww(monkeypatch):
    monkeypatch.setitem(sys.modules, "growwapi", None)  # as in CI: requirements.txt only, no Groww SDK
    parts = wiring._parts(load_app_config())  # builds only: Groww's provider is made at the first read
    assert [part.name for part in parts] == ["gift", "fo_list", "nifty", "banknifty"]
    assert [part.source.symbol for part in parts[2:]] == ["NSE-NIFTY", "NSE-BANKNIFTY"]


def test_without_the_groww_sdk_a_read_is_a_named_part_failure(monkeypatch):
    monkeypatch.setitem(sys.modules, "growwapi", None)
    nifty = wiring._parts(load_app_config())[2]
    with pytest.raises(PartFailed, match="RuntimeError"):  # GrowwProvider's "Install the Groww SDK first"
        nifty.answer(DAY)


def test_two_reads_build_one_groww_provider(monkeypatch):
    """Judge 432 add. 1: one sign-in per run, not one per 30 s retry."""
    built = []

    class Provider:
        def __init__(self, cfg):
            built.append(cfg)
            self.api = Api()

    monkeypatch.setattr(wiring, "GrowwProvider", Provider)
    nifty, banknifty = wiring._parts(load_app_config())[2:]
    nifty.answer(DAY), nifty.answer(DAY), banknifty.answer(DAY)
    assert len(built) == 1
