from datetime import date

import pytest

from fno.config import load_config
from fno.http_pacing import RequestPacer, SourceCoolingOff
from fno.providers.cached import CachedProvider
from fno.providers.sample import SampleProvider


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def pacer(clock):
    p = RequestPacer({"nse": 1.0}, cool_off_seconds=900, clock=clock)
    p.sleep = lambda seconds: setattr(clock, "now", clock.now + seconds)
    return p


def test_requests_to_one_host_are_spaced():
    clock = FakeClock()
    p = pacer(clock)
    for _ in range(3):
        p.wait_turn("nse")
    assert clock.now == 2.0  # three requests, one second apart
    p.wait_turn("other-host")
    assert clock.now == 2.0  # other hosts are not held up


def test_two_refusals_in_a_row_pause_the_host():
    clock = FakeClock()
    p = pacer(clock)
    p.observe("nse", 403)
    p.observe("nse", 200)  # a success resets: NSE may refuse once before its cookies are set
    p.observe("nse", 403)
    p.wait_turn("nse")
    p.observe("nse", 429)
    with pytest.raises(SourceCoolingOff):
        p.wait_turn("nse")
    clock.now += 901
    p.wait_turn("nse")


class CountingSample(SampleProvider):
    calls = 0

    def chain(self, underlying, expiry):
        self.calls += 1
        return super().chain(underlying, expiry)


def test_one_chain_fetch_serves_every_reader_until_it_is_stale():
    clock = FakeClock()
    inner = CountingSample(load_config())
    cached = CachedProvider(inner, chain_max_age_seconds=50, clock=clock)
    expiry = date(2026, 10, 27)
    for _ in range(4):
        cached.chain("NIFTY", expiry)
    assert inner.calls == 1
    clock.now = 51
    cached.chain("NIFTY", expiry)
    assert inner.calls == 2
