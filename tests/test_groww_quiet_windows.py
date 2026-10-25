"""Story GW1, part 5: no Groww call through `get_provider` starts inside an A16 mark's quiet window, and A16's own
provider is never held."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from fno.models import IST
from tests.groww_sdk_fake import fake_sdk

MORNING = datetime(2026, 10, 26, 8, 22, tzinfo=IST)


class SleepClock:
    def __init__(self, at):
        self.at, self.slept = at, []

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.at += timedelta(seconds=seconds)


QUIET_CASES = [
    ((14, 30, 10), [110.0]),  # inside A16's 14:30 mark: waits to 14:32:00
    ((15, 0, 0), [120.0]),  # boundary: the mark itself
    ((15, 1, 59), [1.0]),  # A4c at 15:01:59 starts at 15:02:00
    ((15, 2, 0), []),  # boundary: the window's end
    ((15, 15, 0), [120.0]),  # E3's execution capture starts at 15:17:00
    ((14, 32, 0), []),  # the v4 capture at 14:32: no wait (the window's end)
    ((9, 14, 59), []),  # before the first mark
    ((15, 32, 0), []),  # after the last mark's window
]


@pytest.mark.parametrize(("at", "slept"), QUIET_CASES)
def test_an_attempt_never_starts_inside_an_a16_mark(at, slept):
    from fno.providers.groww_quiet_windows import MarkQuietWindows

    clock = SleepClock(datetime(2026, 10, 26, *at, tzinfo=IST))
    MarkQuietWindows(clock, clock.sleep).wait()
    assert clock.slept == slept


@pytest.mark.parametrize(("at", "slept"), QUIET_CASES)
def test_a_call_inside_an_a16_mark_is_refused_and_never_delayed(at, slept):
    from fno.providers.groww_quiet_windows import GrowwQuietWindow, MarkQuietWindows

    clock = SleepClock(datetime(2026, 10, 26, *at, tzinfo=IST))
    quiet = MarkQuietWindows(clock, clock.sleep)
    if slept:
        with pytest.raises(GrowwQuietWindow, match="until"):
            quiet.check()
    else:
        quiet.check()
    assert clock.slept == []


def test_get_providers_groww_starts_its_attempt_after_the_mark_and_a16s_own_never_waits(monkeypatch):
    import fno.providers.groww as groww
    import fno.providers.groww_quiet_windows as quiet
    from fno.providers import get_provider
    from fno.providers.groww import GrowwProvider
    from fno.providers.groww_quiet_windows import GrowwQuietWindow

    sdk, clock = fake_sdk(monkeypatch), SleepClock(datetime(2026, 10, 26, 15, 0, 30, tzinfo=IST))
    sdk.answers["get_expiries"] = {"expiries": ["2026-10-27"]}
    quiet_seconds = timedelta(seconds=quiet.QUIET_SECONDS)
    monkeypatch.setattr(quiet.MarkQuietWindows.__init__, "__defaults__", (clock, clock.sleep, quiet_seconds))
    monkeypatch.setattr(groww, "now_ist", clock)
    provider = get_provider("groww", {})
    provider._token = lambda: "t"
    with pytest.raises(GrowwQuietWindow):
        provider.api.get_quote(trading_symbol="X")  # a call inside the mark: refused, unsent
    assert sdk.calls == [] and clock.slept == []
    provider.expiries("NIFTY")  # an attempt's first call: waits for 15:02:00, then asks
    assert clock.slept == [90.0] and sdk.calls == ["get_expiries"] * 2  # this year and next
    clock.at = datetime(2026, 10, 26, 15, 15, 5, tzinfo=IST)
    own = GrowwProvider({})
    own._token = lambda: "t"
    own.expiries("NIFTY")
    own.api.get_quote(trading_symbol="X")
    assert clock.slept == [90.0] and sdk.calls[2:] == [
        "get_expiries",
        "get_expiries",
        "get_quote",
    ]  # A16's: no wait, no refusal


def test_the_v4_captures_configured_start_is_outside_every_a16_quiet_window():
    """The v4 capture (14:32 by config, protocol v4's freeze) must never be moved into A16's 14:30 quiet window: its
    first call would wait and its others be refused (orchestrator, 25 Oct)."""
    from fno.config import load_config
    from fno.providers.groww_quiet_windows import MarkQuietWindows

    start = datetime.strptime(load_config()["quotes"]["windows"]["v4"]["start"], "%H:%M").time()
    clock = SleepClock(datetime.combine(MORNING.date(), start, IST))
    MarkQuietWindows(clock, clock.sleep).wait()
    assert clock.slept == [], f"quotes.windows.v4.start {start} is inside an A16 mark's quiet window"
