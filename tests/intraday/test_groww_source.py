"""Story A16 criteria 4 and 10: what the Groww adapter asks and keeps (read-only calls, two chains, contracts within
6% of the index level, the index first, failures by class name only), and that no credential reaches any output."""

import gzip
import os
from datetime import date, time

import pytest

from fno.constants import ENV_GROWW_API_KEY, ENV_GROWW_TOTP_SECRET
from fno.intraday.cli import report
from fno.intraday.expiry_plan import ExpiryPlan
from fno.intraday.groww_source import GrowwIntradaySource, epoch_time
from fno.intraday.pacing import RatePacer
from tests.intraday.fakes import DAY, FakeClock, build, ist
from tests.intraday.groww_fakes import FakeGrowwApi, FakeGrowwProvider

LISTED = [date(2026, 10, 19), date(2026, 10, 27), date(2026, 11, 3)]
PLANTED = "PLANTED-SECRET-7f3a"


def source(api=None, provider=None, listed=LISTED, clock=None):
    clock = clock or FakeClock(ist(DAY, 10, 0))
    plan = ExpiryPlan(lambda: listed)
    pacer = RatePacer(1000, clock=lambda: 0.0, sleep=lambda s: None)
    return GrowwIntradaySource(provider or FakeGrowwProvider(api), plan, clock.now, pacer)


def test_a_snapshot_holds_the_index_the_future_two_chains_and_every_contract_within_6_percent():
    api = FakeGrowwApi(index_level=25000.0)
    found = source(api).take(DAY, ist(DAY, 10, 0))
    assert api.calls[0] == "quote NIFTY"  # the index first, right at the mark
    assert found.index_level == 25000.0 and found.index_source_time == epoch_time(1792036800000)
    assert found.future.meta == {"symbol": "NIFTY26OCTFUT"} and not found.future.failure
    assert [c.meta["expiry"] for c in found.chains] == ["2026-10-19", "2026-10-27"]
    strikes = sorted({q.meta["strike"] for q in found.quotes})
    assert strikes[0] == 23500 and strikes[-1] == 26500  # 25000 * (1 -/+ 0.06), both ends included
    assert found.expected_contracts == found.recorded_contracts == found.two_sided_contracts == 2 * 61 * 2
    assert found.expiries["monthly"] == "2026-10-27" and found.failures == []


def test_on_the_monthly_expiry_day_the_second_chain_is_the_next_listed_expiry():
    expiry_day = date(2026, 10, 27)
    found = source(listed=[expiry_day, date(2026, 11, 3)]).take(expiry_day, ist(expiry_day, 10, 0))
    assert [c.meta["expiry"] for c in found.chains] == ["2026-10-27", "2026-11-03"]


def test_a_failed_contract_quote_is_kept_by_its_class_name_and_counted():
    symbol = "NIFTY26101925000CE"
    found = source(FakeGrowwApi(fail=(symbol,))).take(DAY, ist(DAY, 10, 0))
    failed = [q for q in found.quotes if q.failure]
    assert [(q.meta["symbol"], q.failure, q.payload) for q in failed] == [(symbol, "RuntimeError", None)]
    assert found.recorded_contracts == found.expected_contracts - 1 and f"quote {symbol}" in found.failures


def test_a_failed_chain_leaves_its_contracts_out_and_says_so():
    found = source(FakeGrowwApi(fail=("chain 2026-10-19",))).take(DAY, ist(DAY, 10, 0))
    assert found.chains[0].failure == "RuntimeError" and found.expected_contracts == 122
    assert "chain 2026-10-19" in found.failures


def test_no_listed_expiry_is_a_named_failure_and_the_index_is_still_kept():
    found = source(listed=[]).take(DAY, ist(DAY, 10, 0))
    assert found.index_level == 25000.0 and found.chains == [] and found.failures == ["expiry_plan: ExpiryPlanError"]


def test_a_refused_sign_in_fails_every_call_by_name_and_never_raises():
    adapter = source(provider=FakeGrowwProvider(sign_in_error=RuntimeError("Groww credentials missing")))
    adapter.prepare(DAY)
    found = adapter.take(DAY, ist(DAY, 10, 0))
    assert found.index.failure == "RuntimeError" and found.index_level is None
    assert found.notes == ["prepare sign_in: RuntimeError"] and found.expected_contracts == 0
    assert found.failures[0] == "index" and "chain 2026-10-19" in found.failures


def test_no_order_position_margin_or_funds_call_is_made_in_a_whole_session(tmp_path):
    api = FakeGrowwApi()  # fails the test on any forbidden call
    adapter = source(api)
    for minute in (0, 15, 30):
        adapter.take(DAY, ist(DAY, 10, minute))
    assert {call.split()[0] for call in api.calls} == {"quote", "chain"}


@pytest.mark.parametrize("value, expected", [(1792036790, 1792036790), (1792036790123, 1792036790.123)])
def test_groww_epoch_times_in_seconds_or_milliseconds(value, expected):
    assert epoch_time(value).timestamp() == pytest.approx(expected)
    assert epoch_time(None) is None and epoch_time(0) is None


def test_no_credential_reaches_a_document_the_ledger_an_alert_or_the_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(ENV_GROWW_API_KEY, PLANTED)
    monkeypatch.setenv(ENV_GROWW_TOTP_SECRET, PLANTED + "-totp")
    leak = RuntimeError(f"refused key {os.environ[ENV_GROWW_API_KEY]}")
    clock = FakeClock(ist(DAY, 9, 10))
    recorder, _, alerts, *_ = build(tmp_path, clock)
    recorder.source = source(provider=FakeGrowwProvider(sign_in_error=leak), clock=clock)
    recorder.settlement.source = recorder.source.name = "fakegroww"
    report(recorder.run(time(10, 5)))
    written = b"".join(p.read_bytes() for p in tmp_path.rglob("*") if p.is_file())
    texts = [gzip.decompress(p.read_bytes()) for p in tmp_path.rglob("*.gz")]
    assert alerts.sent and PLANTED.encode() not in written and all(PLANTED.encode() not in t for t in texts)
    assert PLANTED not in capsys.readouterr().out and all(PLANTED not in a for a in alerts.sent)


@pytest.mark.parametrize("bad_time", ["2026-10-15T09:15:00", "not a time", [1]])
def test_an_unexpected_index_time_is_a_named_failure_never_a_crash(bad_time):
    api = FakeGrowwApi()
    api.get_quote = lambda trading_symbol, exchange, segment, timeout=None: (
        {"payload": {"last_price": 25000.0, "last_trade_time": bad_time}} if segment == "CASH" else
        {"payload": {"bid_price": 1, "offer_price": 2, "last_trade_time": 10**13}})  # fmt: skip
    found = source(api).take(DAY, ist(DAY, 10, 0))
    assert found.index_level is None and found.failures[0].startswith("index_parse: ")
    assert found.two_sided_contracts == 0 and found.recorded_contracts == found.expected_contracts  # unreadable books


def test_an_unreadable_chain_is_a_named_failure():
    api = FakeGrowwApi()
    api.get_option_chain = lambda **kwargs: {"payload": {"strikes": {"not a strike": {"CE": {"ltp": 1}}}}}
    found = source(api).take(DAY, ist(DAY, 10, 0))
    assert "chain_parse 2026-10-19: ValueError" in found.failures and found.expected_contracts == 0


def test_every_call_carries_a_timeout():
    seen = []
    api = FakeGrowwApi()
    quote, chain = api.get_quote, api.get_option_chain
    api.get_quote = lambda **kw: seen.append(kw["timeout"]) or quote(**kw)
    api.get_option_chain = lambda **kw: seen.append(kw["timeout"]) or chain(**kw)
    source(api).take(DAY, ist(DAY, 10, 0))
    assert set(seen) == {10} and len(seen) == 2 + 2 + 244
