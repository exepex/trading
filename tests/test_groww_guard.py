"""Story GW1: Groww's rate limits are never exceeded. Sign-in back-off and daily cap, one alert, the read-only client
for every caller, a 429 named, and a minute's stop after it."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from fno.intraday.read_only import ReadOnlyViolation
from fno.models import IST
from fno.providers.groww_rate_guard import (
    PAUSE_SECONDS,
    GrowwRateLimited,
    GrowwRateLimitPaused,
    RateGuardedGroww,
    RateLimitPause,
)
from fno.providers.groww_sign_in import FIRST_WAIT, LONGEST_WAIT, TRIES_A_DAY, GrowwSignIn, GrowwSignInPaused
from tests.groww_sdk_fake import fake_sdk

MORNING = datetime(2026, 10, 26, 8, 22, tzinfo=IST)


class Clock:
    def __init__(self, at=MORNING):
        self.at = at

    def __call__(self):
        return self.at


class SignInStub:
    def __init__(self, fail: bool = True):
        self.tries, self.fail = 0, fail

    def __call__(self):
        self.tries += 1
        if self.fail:
            raise ConnectionError("token=SECRET-VALUE refused")
        return f"client{self.tries}"


def test_a_failed_sign_in_is_not_tried_again_within_its_back_off():
    clock, stub = Clock(), SignInStub()
    guard = GrowwSignIn(stub, clock)
    with pytest.raises(ConnectionError):
        guard.client()
    for seconds in (0, 1, 299):  # boundary: one second before the back-off ends
        clock.at = MORNING + timedelta(seconds=seconds)
        with pytest.raises(GrowwSignInPaused, match="next try at 08:27:00 IST"):
            guard.client()
    assert stub.tries == 1
    clock.at = MORNING + FIRST_WAIT  # exactly at its end: tried again
    with pytest.raises(ConnectionError):
        guard.client()
    assert stub.tries == 2


def test_the_back_off_doubles_to_thirty_minutes_and_stops_at_the_day_cap():
    clock, stub = Clock(), SignInStub()
    guard, waits = GrowwSignIn(stub, clock), []
    for _ in range(TRIES_A_DAY):
        with pytest.raises(ConnectionError):
            guard.client()
        waits.append(guard._next_try - clock.at)
        clock.at = guard._next_try
    assert waits[:4] == [FIRST_WAIT, 2 * FIRST_WAIT, 4 * FIRST_WAIT, LONGEST_WAIT] and waits[-1] == LONGEST_WAIT
    clock.at += timedelta(hours=10)  # still the same token day (before 06:00 tomorrow)
    with pytest.raises(GrowwSignInPaused, match="no more tries until 06:00 IST"):
        guard.client()
    assert stub.tries == TRIES_A_DAY
    clock.at = datetime(2026, 10, 27, 6, 0, tzinfo=IST)  # a new token day starts afresh
    stub.fail = False
    assert guard.client() == f"client{TRIES_A_DAY + 1}"


def test_a_success_is_kept_for_the_token_day_and_resets_the_failures():
    clock, stub = Clock(), SignInStub(fail=False)
    guard = GrowwSignIn(stub, clock)
    assert guard.client() == guard.client() == "client1"
    clock.at = datetime(2026, 10, 27, 5, 59, tzinfo=IST)
    assert guard.client() == "client1" and stub.tries == 1
    clock.at = datetime(2026, 10, 27, 6, 0, tzinfo=IST)
    assert guard.client() == "client2"


def test_the_first_failure_of_a_day_alerts_once_with_the_class_name_only():
    clock, stub, lines = Clock(), SignInStub(), []
    guard = GrowwSignIn(stub, clock, lines.append)
    for _ in range(3):
        with pytest.raises((ConnectionError, GrowwSignInPaused)):
            guard.client()
        clock.at += FIRST_WAIT * 4
    assert len(lines) == 1 and "ConnectionError" in lines[0] and "SECRET" not in lines[0]
    clock.at = datetime(2026, 10, 27, 6, 0, tzinfo=IST)
    with pytest.raises(ConnectionError):
        guard.client()
    assert len(lines) == 2  # one a token day


def test_missing_credentials_are_a_failure_like_any_other(monkeypatch):
    from fno.constants import ENV_GROWW_ACCESS_TOKEN, ENV_GROWW_API_KEY

    sdk = fake_sdk(monkeypatch)
    for name in (ENV_GROWW_ACCESS_TOKEN, ENV_GROWW_API_KEY):
        monkeypatch.delenv(name, raising=False)
    from fno.providers.groww import GrowwProvider

    provider = GrowwProvider({})
    with pytest.raises(RuntimeError, match="credentials missing"):
        provider.api.get_quote(trading_symbol="X")
    with pytest.raises(GrowwSignInPaused):
        provider.api.get_quote(trading_symbol="X")
    assert sdk.tokens == [] and sdk.calls == []


def test_every_caller_gets_the_read_only_client_and_no_order_call_reaches_the_sdk(monkeypatch):
    from fno.providers.groww import GrowwProvider
    from fno.quotes.future_quotes import GrowwFutureQuotes

    sdk = fake_sdk(monkeypatch)
    provider = GrowwProvider({})
    provider._token = lambda: "t"
    for name in ("place_order", "modify_order", "cancel_order", "get_positions_for_user"):
        with pytest.raises(ReadOnlyViolation):
            getattr(provider.api, name)
    assert sdk.calls == [] and sdk.tokens == []  # refused before the sign-in, never at the SDK
    sdk.answers["get_quote"] = {"bid_price": 99.5, "offer_price": 100.5, "last_price": 100.0}
    book = GrowwFutureQuotes(provider).quote(MORNING.date())
    assert (book.bid, book.ask) == (99.5, 100.5) and sdk.calls == ["get_quote"]


def test_the_feed_probe_alone_gets_the_signed_in_sdk_client(monkeypatch):
    from fno.providers.groww import GrowwProvider

    sdk = fake_sdk(monkeypatch)
    provider = GrowwProvider({})
    provider._token = lambda: "t"
    assert type(provider.feed_client()).__name__ == "GrowwAPI" and sdk.tokens == ["t"]
    assert provider.api.EXCHANGE_NSE == "NSE"
    assert sdk.tokens == ["t"]  # one sign-in shared by both


class CodedError(Exception):
    def __init__(self, code):
        super().__init__("https://api.groww.in/... private text")
        self.code = code


class Ticker:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def guarded_client(error_at: dict, ticker: Ticker):
    calls = []

    class Client:
        EXCHANGE_NSE = "NSE"

        def get_quote(self, n):
            calls.append(n)
            if n in error_at:
                raise error_at[n]
            return {"n": n}

    client = Client()
    return RateGuardedGroww(lambda: client, RateLimitPause(clock=ticker)), calls


@pytest.mark.parametrize("error", [CodedError("429"), CodedError(429)])
def test_a_429_is_named_and_carries_no_groww_text(error):
    guarded, _ = guarded_client({1: error}, Ticker())
    with pytest.raises(GrowwRateLimited) as caught:
        guarded.get_quote(1)
    assert caught.value.code == "429" and "groww.in" not in str(caught.value) and caught.value.__cause__ is None


def test_another_error_passes_unchanged_and_starts_no_pause():
    other = CodedError("GA001")
    guarded, calls = guarded_client({1: other}, Ticker())
    with pytest.raises(CodedError) as caught:
        guarded.get_quote(1)
    assert caught.value is other and guarded.get_quote(2) == {"n": 2} and calls == [1, 2]
    assert guarded.EXCHANGE_NSE == "NSE"


def test_after_a_429_nothing_is_sent_for_a_minute():
    ticker = Ticker()
    guarded, calls = guarded_client({3: CodedError("429")}, ticker)
    outcomes = []
    for n in range(1, 21):  # an A4 attempt of 20 contracts, sequential
        try:
            guarded.get_quote(n)
            outcomes.append("ok")
        except (GrowwRateLimited, GrowwRateLimitPaused) as exc:
            outcomes.append(type(exc).__name__)
    assert calls == [1, 2, 3]  # Groww asked 3 times, not 20
    assert outcomes[2] == "GrowwRateLimited" and set(outcomes[3:]) == {"GrowwRateLimitPaused"}
    ticker.now += PAUSE_SECONDS - 0.5
    with pytest.raises(GrowwRateLimitPaused):
        guarded.get_quote(4)
    ticker.now += 0.5  # the minute is over: sent again
    assert guarded.get_quote(4) == {"n": 4} and calls == [1, 2, 3, 4]


def test_a4s_public_failure_entry_now_names_the_rate_limit():
    from fno.intraday.groww_source import failure_name
    from fno.quotes.recorder import withheld

    error = GrowwRateLimited("x")
    assert withheld("chain", error) == "chain: GrowwRateLimited (provider message withheld)"
    assert failure_name(error) == "GrowwRateLimited:429"


def test_get_provider_wires_the_desk_alert_for_a_failed_sign_in(monkeypatch, capsys):
    import fno.composition as composition
    from fno.constants import ENV_GROWW_ACCESS_TOKEN
    from fno.providers import get_provider

    sdk, sent = fake_sdk(monkeypatch), []
    sdk.sign_in_error = ConnectionError("down")
    monkeypatch.setenv(ENV_GROWW_ACCESS_TOKEN, "ready")

    class Sender:
        def send(self, text):
            sent.append(text)
            return "alert NOT sent: test"

    monkeypatch.setattr(composition, "build_alert_sender", Sender)
    for name in ("groww", "auto"):
        provider = get_provider(name, {})
        with pytest.raises(ConnectionError):
            provider.api.get_quote(trading_symbol="X")
    assert len(sent) == 2 and all("ConnectionError" in line for line in sent)
    assert capsys.readouterr().out.count("alert NOT sent: test") == 2


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


def test_a_429_on_next_years_expiries_is_named_not_swallowed():
    from fno.providers.groww import listed_expiries

    class Api:
        EXCHANGE_NSE = "NSE"

        def get_expiries(self, exchange, underlying_symbol, year):
            if year > 2026:
                raise GrowwRateLimited("x")
            return {"expiries": ["2026-10-27"]}

    with pytest.raises(GrowwRateLimited):
        listed_expiries(Api(), "NIFTY", MORNING.date())


def test_the_alert_is_sent_outside_the_sign_in_lock():
    clock, held = Clock(), []
    guard = GrowwSignIn(SignInStub(), clock, lambda line: held.append(guard._lock.locked()))
    with pytest.raises(ConnectionError) as caught:
        guard.client()
    assert held == [False] and caught.value.__suppress_context__  # the original error, as before
