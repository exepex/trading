import pytest

from fno.http_pacing import RequestPacer, SourceCoolingOff


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
