"""Story A16 criterion 10 (the read-only allow-list, the grep over the whole import closure) and Definitions "Index
source time" (the 1-minute candle fallback: level and time from one candle; IST text without an offset)."""

import ast
from datetime import date, timedelta
from pathlib import Path

import pytest

from fno.intraday import wiring
from fno.intraday.expiry_plan import ExpiryPlan
from fno.intraday.groww_source import GrowwIntradaySource
from fno.intraday.index_reading import CANDLE_BASIS, QUOTE_BASIS, candle_start
from fno.intraday.pacing import RatePacer
from fno.intraday.read_only import ALLOWED, ReadOnlyGroww, ReadOnlyViolation
from fno.intraday.status import verdict
from fno.models import IST
from tests.intraday.fakes import DAY, FakeClock, ist
from tests.intraday.groww_fakes import FORBIDDEN, FakeGrowwApi

ROOT = Path(__file__).resolve().parents[2]
SDK_1_5_0_NAMES = (
    "cancel_order", "cancel_smart_order", "create_smart_order", "generate_socket_token", "get_access_token",
    "get_all_instruments", "get_available_margin_details", "get_contracts", "get_expiries", "get_greeks",
    "get_historical_candle_data", "get_historical_candles", "get_holdings_for_user",
    "get_instrument_by_exchange_and_trading_symbol", "get_instrument_by_exchange_token",
    "get_instrument_by_groww_symbol",
    "get_ltp", "get_ohlc", "get_option_chain", "get_order_detail", "get_order_list", "get_order_margin_details",
    "get_order_status", "get_order_status_by_reference",
    "get_position_for_trading_symbol", "get_positions_for_user", "get_quote", "get_smart_order", "get_smart_order_list",
    "get_trade_list_for_order", "get_user_profile", "modify_order", "modify_smart_order", "place_order",
    "ORDER_TYPE_MARKET", "PRODUCT_NRML", "TRANSACTION_TYPE_BUY", "EXCHANGE_NSE", "SEGMENT_CASH", "SEGMENT_FNO",
)  # fmt: skip


def sdk_names() -> set[str]:
    """The real SDK class's public names when `growwapi` is installed, else its 1.5.0 names (step 0's listing)."""
    try:
        from growwapi import GrowwAPI
    except ImportError:
        return set(SDK_1_5_0_NAMES)
    return {name for name in dir(GrowwAPI) if not name.startswith("_")}


def test_the_wrapper_refuses_every_sdk_name_outside_the_allow_list_before_the_sdk_is_touched():
    touched = []
    wrapper = ReadOnlyGroww(lambda: touched.append("client") or FakeGrowwApi())
    refused = sdk_names() - ALLOWED
    assert {"place_order", "modify_order", "cancel_order", "get_positions_for_user"} <= refused
    for name in refused:
        with pytest.raises(ReadOnlyViolation):
            getattr(wrapper, name)
    assert touched == []  # refused before the client was even built (no sign-in)


def test_the_allowed_names_pass_through_and_the_wrapper_cannot_be_changed():
    wrapper = ReadOnlyGroww(FakeGrowwApi)
    assert wrapper.EXCHANGE_NSE == "NSE" and wrapper.get_quote(trading_symbol="NIFTY", exchange="NSE", segment="CASH")
    with pytest.raises(ReadOnlyViolation):
        wrapper.place_order = lambda: None


def _closure(module: str, seen: set[str]) -> set[str]:
    """Every `fno` module `module` imports, directly or not (by AST, as tools/check_imports.py reads them)."""
    if module in seen:
        return seen
    path = ROOT.joinpath(*module.split("."))
    file = path.with_suffix(".py") if path.with_suffix(".py").is_file() else path / "__init__.py"
    if not file.is_file():
        return seen
    seen.add(module)
    package = module.split(".")[:-1] if file.name != "__init__.py" else module.split(".")
    for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - node.level + 1] if node.level else []
            target = ".".join(base + ([node.module] if node.module else []))
            names = [target] + [f"{target}.{alias.name}" for alias in node.names]
        for name in names:
            if name.startswith("fno"):
                _closure(name, seen)
    return seen


def test_no_module_in_the_whole_import_closure_names_an_order_position_holdings_or_margin_call():
    modules = set()
    for file in sorted((ROOT / "fno" / "intraday").glob("*.py")):
        _closure(f"fno.intraday.{file.stem}", modules)
    assert "fno.providers.groww" in modules and "fno.composition" in modules and len(modules) > 30
    found = {}
    for module in modules:
        path = ROOT.joinpath(*module.split("."))
        file = path.with_suffix(".py") if path.with_suffix(".py").is_file() else path / "__init__.py"
        text = file.read_text(encoding="utf-8")
        if hits := [name for name in FORBIDDEN if name in text]:
            found[module] = hits
    assert found == {}


def candle(start: str, close: float) -> list:
    return [start, close - 1, close + 2, close - 3, close, None, None]


def source(api, clock):
    plan = ExpiryPlan(lambda: [date(2026, 10, 19), date(2026, 10, 27)])
    pacer = RatePacer(1000, clock=lambda: 0.0, sleep=lambda s: None)
    return GrowwIntradaySource(ReadOnlyGroww(lambda: api), plan, 75, clock.now, pacer)


def test_without_an_index_time_the_level_and_time_come_from_the_latest_finished_candle():
    clock = FakeClock(ist(DAY, 9, 30, 0.4))  # the response arrives 0.4 s after the mark
    rows = [candle("2026-10-15T09:28:00", 25010.0), candle("2026-10-15T09:29:00", 25020.0),
            candle("2026-10-15T09:30:00", 25030.0)]  # the last one is still forming  # fmt: skip
    api = FakeGrowwApi(index_level=24000.0, index_time=None, candles=rows)  # a frozen quote beside live candles
    found = source(api, clock).take(DAY, ist(DAY, 9, 30))
    assert (found.index_level, found.index_basis) == (25020.0, CANDLE_BASIS)  # the candle's close, never 24000
    assert found.index_source_time == ist(DAY, 9, 30)  # the 09:29 candle's end
    assert api.calls[1].startswith("candles NSE-NIFTY 1minute 2026-10-15 09:25:00..2026-10-15 09:30:00")
    assert verdict(found, None).status == "good"


def test_the_quote_time_wins_when_groww_gives_one_and_no_candle_is_asked_for():
    api = FakeGrowwApi(index_level=25000.0)
    found = source(api, FakeClock(ist(DAY, 10, 0))).take(DAY, ist(DAY, 10, 0))
    assert found.index_basis == QUOTE_BASIS and found.index_candle is None
    assert not [call for call in api.calls if call.startswith("candles")]


def test_no_finished_candle_leaves_no_source_time_and_the_mark_is_stale():
    clock = FakeClock(ist(DAY, 9, 30, 0.4))
    api = FakeGrowwApi(index_time=None, candles=[candle("2026-10-15T09:30:00", 25030.0)])
    found = source(api, clock).take(DAY, ist(DAY, 9, 30))
    assert found.index_source_time is None and found.index_basis == ""
    assert verdict(found, None).status == "stale" and "index_time_missing" in verdict(found, None).failures


def test_an_old_finished_candle_is_stale_at_121_seconds_and_fresh_at_120():
    clock = FakeClock(ist(DAY, 9, 30, 0))
    old = FakeGrowwApi(index_time=None, candles=[candle("2026-10-15T09:26:59", 25000.0)])  # ended 09:27:59, 121 s
    fresh = FakeGrowwApi(index_time=None, candles=[candle("2026-10-15T09:27:00", 25000.0)])  # ended 09:28:00, 120 s
    assert verdict(source(old, clock).take(DAY, ist(DAY, 9, 30)), None).status == "stale"
    clock.moment = ist(DAY, 9, 30, 0)
    assert verdict(source(fresh, clock).take(DAY, ist(DAY, 9, 30)), None).status == "good"


@pytest.mark.parametrize("text", ["2026-10-15T09:29:00+05:30", "2026-10-15T09:29:00Z", "garbage"])
def test_a_candle_time_with_an_offset_or_bad_text_is_a_named_failure(text):
    api = FakeGrowwApi(index_time=None, candles=[candle(text, 25020.0)])
    found = source(api, FakeClock(ist(DAY, 9, 30, 0.4))).take(DAY, ist(DAY, 9, 30))
    assert found.index_level is None and found.failures[0].startswith("index_parse: ")


def test_candle_times_are_read_as_ist_whatever_the_host_time_zone(monkeypatch):
    monkeypatch.setenv("TZ", "America/New_York")
    assert candle_start("2026-10-15T09:29:00") == ist(DAY, 9, 29) and candle_start(
        "2026-10-15T09:29:00"
    ).utcoffset() == timedelta(hours=5, minutes=30)
    assert candle_start("2026-10-15T09:29:00").tzinfo is IST


def test_the_composition_root_gives_the_source_only_the_wrapper(monkeypatch):
    from tests.intraday.groww_fakes import FakeGrowwProvider

    monkeypatch.setattr(wiring, "GrowwProvider", lambda cfg: FakeGrowwProvider())
    held = vars(wiring.build_intraday_recorder({}, Path("/tmp/a16-dry")).source)
    assert [type(v).__name__ for v in held.values() if "Groww" in type(v).__name__] == ["ReadOnlyGroww"]
