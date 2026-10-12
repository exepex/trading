from datetime import datetime, timedelta

from fno.config import load_config
from fno.constants import EVENT_IV_SNAPSHOT
from fno.live.learning.iv_history import IvHistory
from fno.live.results_store import JsonlResultsStore
from fno.live.signals.base import SymbolInputs
from fno.live.signals.guards import IvRankGuard
from fno.models import IST
from fno.providers.sample import SampleProvider

CLOSE = datetime(2026, 10, 13, 15, 45, tzinfo=IST)


def test_one_snapshot_per_underlying_per_day_and_rank_needs_history(tmp_path):
    store = JsonlResultsStore(tmp_path)
    history = IvHistory(store, min_days=3)
    chain = SampleProvider(load_config()).chain("NIFTY", CLOSE.date() + timedelta(days=14))
    first = history.observe("NIFTY", chain)
    assert first and history.observe("NIFTY", chain) == first  # latest value, kept once
    assert history.flush(CLOSE) == 1 and history.flush(CLOSE) == 0
    assert [s["symbol"] for s in store.payloads(EVENT_IV_SNAPSHOT, CLOSE.date())] == ["NIFTY"]
    assert history.rank("NIFTY", 20.0, CLOSE.date() + timedelta(days=1)) is None  # one day is not history


def test_rank_places_today_between_the_stored_low_and_high(tmp_path):
    store = JsonlResultsStore(tmp_path)
    for i, iv in enumerate([10.0, 20.0, 30.0]):
        day = CLOSE - timedelta(days=3 - i)
        store.record(EVENT_IV_SNAPSHOT, {"symbol": "NIFTY", "day": day.date().isoformat(), "atm_iv": iv}, day)
    history = IvHistory(store, min_days=3)
    assert history.rank("NIFTY", 25.0, CLOSE.date()) == 75.0
    assert history.rank("NIFTY", 40.0, CLOSE.date()) == 100.0
    assert history.rank("BANKNIFTY", 25.0, CLOSE.date()) is None


def test_iv_rank_guard_blocks_dear_options_and_abstains_without_history():
    guard = IvRankGuard({"max_iv_rank": 80})
    base = {"symbol": "NIFTY", "snapshot": None, "candles": [], "benchmark_change_pct": None, "research": None}
    assert guard.evaluate(SymbolInputs(**base, iv_rank=92.0)).blocked
    assert not guard.evaluate(SymbolInputs(**base, iv_rank=40.0)).blocked
    assert not guard.evaluate(SymbolInputs(**base)).blocked
