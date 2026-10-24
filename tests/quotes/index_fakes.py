"""Fakes for story A4c's index recording: a provider with one chain per index and an NSE listing per index."""

from dataclasses import replace
from datetime import date, datetime

from fno.models import IST, OptionChain, OptionQuote, QuoteBook
from fno.quotes.indices import index_slot
from fno.quotes.indices_cli import record_indices
from fno.quotes.recorder import QuoteSnapshotRecorder
from tests.quotes.drive_fakes import FakeDrive, split_store
from tests.quotes.test_recorder_calendar import CALENDAR, Alerts

DAY = date(2026, 10, 13)  # a Tuesday session
MONTHLIES = [date(2026, 10, 27), date(2026, 11, 23), date(2026, 12, 29)]
SPOTS = {"BANKNIFTY": 55000.0, "FINNIFTY": 25000.0, "MIDCPNIFTY": 13800.0}
TOO_EARLY = "not started: too early (before 14:41); a rerun from 14:41 to 15:13 records it"  # A4c-2, word for word
FILE = {"source": "fake", "file": "nse/derivatives/fo-bhavcopy/2026/10/fake.zip", "file_date": "2026-10-12",
        "sha256": "a" * 64}  # fmt: skip


class Clock:
    def __init__(self, start: datetime, step: float = 1.0):
        self.t, self.step, self.slept = start, step, []

    def now(self):
        from datetime import timedelta

        self.t += timedelta(seconds=self.step)
        return self.t

    def sleep(self, seconds):
        from datetime import timedelta

        self.slept.append(seconds)
        self.t += timedelta(seconds=seconds)


class IndexProvider:
    name = "fake"

    def __init__(self, refuse=(), traded=True):
        self.refuse, self.traded, self.calls = set(refuse), traded, []

    def expiries(self, underlying):
        if underlying in self.refuse:
            raise ConnectionError(f"unknown symbol {underlying}")
        return MONTHLIES

    def chain(self, underlying, expiry):
        spot = SPOTS[underlying]
        quotes = {(k, t): OptionQuote(k, t, 10.0, symbol=f"{underlying}{k:g}{t}")
                  for k in (spot * 0.9, spot * 0.99, spot, spot * 1.01) for t in ("CE", "PE")}  # fmt: skip
        return OptionChain(underlying, spot, expiry, datetime(2026, 10, 13, 14, 58, tzinfo=IST), 30, quotes)

    def quote_book(self, chain, strike, kind):
        self.calls.append((chain.underlying, strike, kind))
        traded = datetime(2026, 10, 13, 14, 58, tzinfo=IST) if self.traded else datetime(2026, 10, 1, tzinfo=IST)
        return QuoteBook(f"{chain.underlying}{strike:g}{kind}", 10.0, 11.0, 30, 60, 10.5, traded, "depth", "h")


class Listing:
    """The previous session's NSE file: lists `listed` as index options (ListedExpiries and ExpiryHistory)."""

    def __init__(self, listed=tuple(SPOTS)):
        self.listed_names = set(listed)

    def listed(self, underlying, today):
        return (MONTHLIES if underlying in self.listed_names else []), dict(FILE)

    def listed_on(self, underlying, day):
        return day, (MONTHLIES if underlying in self.listed_names else []), dict(FILE)


def recorders(folder, clock, provider=None, listing=None, drive=None, **slot_changes):
    provider, listing = provider or IndexProvider(), listing or Listing()
    store = split_store(folder, drive if drive is not None else FakeDrive())
    slot_changes = {"workers": 1, "per_second": None} | slot_changes  # deterministic order; pace tested apart
    return {
        name: QuoteSnapshotRecorder(
            provider,
            store,
            clock.now,
            clock.sleep,
            fallback=listing,
            calendar=CALENDAR,
            history=listing,
            slot=replace(index_slot(name), **slot_changes),
        )  # fmt: skip
        for name in SPOTS
    }


def alerted(folder, start, capsys, **kwargs):
    """`quotes record-indices` on the fakes from `start`: (exit code, alerts sent, printed lines)."""
    clock, alerts = Clock(start), Alerts()
    code = record_indices(lambda: recorders(folder, clock, **kwargs), alerts, "cal.csv", clock.now, clock.sleep)
    return code, alerts.sent, capsys.readouterr().out.splitlines()
