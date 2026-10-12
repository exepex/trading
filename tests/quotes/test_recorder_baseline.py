"""Clean-slate criterion 9: the moved recorder writes byte-for-byte what the pre-cleanup recorder wrote."""

from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from fno.models import IST, OptionChain, OptionQuote, QuoteBook
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.storage.raw_store import LocalFolderStore

BASELINE = Path(__file__).resolve().parent.parent / "fixtures" / "quote_recorder_golden"
TRADED = datetime(2026, 10, 13, 14, 58, tzinfo=IST)


class Clock:
    def __init__(self, start):
        self.t = start

    def now(self):
        self.t += timedelta(seconds=1)
        return self.t

    def sleep(self, seconds):
        self.t += timedelta(seconds=seconds)


class Fake:
    name = "fake"

    def __init__(self, fail_first=0, traded=TRADED, listed=None):
        self.fail_first, self.calls, self.traded, self.listed = fail_first, 0, traded, listed

    def expiries(self, underlying):
        return self.listed or [date(2026, 10, 20), date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 24),
                               date(2026, 12, 29)]  # fmt: skip

    def chain(self, underlying, expiry):
        quotes = {(k, t): OptionQuote(k, t, 10.0, symbol=f"N{k:g}{t}") for k in (21000.0, 22000.0, 23000.0, 25000.0)
                  for t in ("CE", "PE")}  # fmt: skip
        return OptionChain("NIFTY", 22000.0, expiry, TRADED, 65, quotes)

    def quote_book(self, chain, strike, kind):
        self.calls += 1
        if self.calls <= self.fail_first:
            raise ConnectionError("dropped")
        return QuoteBook(f"N{strike:g}{kind}", 10.0, 11.0, 65, 130, 10.5, self.traded, "fields", "h")


class Listing:
    def listed(self, underlying, today):
        return [date(2026, 12, 29), date(2027, 1, 26)], {"source": "nse-file", "file": "f.zip", "sha256": "abc"}


DECEMBER = datetime(2026, 12, 23, 14, 58, tzinfo=IST)
SCENARIOS = {  # name: (fresh provider, start time, expiry fallback)
    "normal": (lambda: Fake(), datetime(2026, 10, 13, 14, 55, tzinfo=IST), None),
    "retry": (lambda: Fake(fail_first=1), datetime(2026, 10, 13, 14, 55, tzinfo=IST), None),
    "none": (lambda: Fake(fail_first=10**6), datetime(2026, 10, 13, 15, 9, 30, tzinfo=IST), None),
    "december": (
        lambda: Fake(traded=DECEMBER, listed=[date(2026, 12, 22), date(2026, 12, 29)]),
        datetime(2026, 12, 23, 14, 55, tzinfo=IST),
        Listing(),
    ),  # fmt: skip
}


def _files(folder: Path) -> dict[str, bytes]:
    return {str(p.relative_to(folder)): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_output_equals_the_pre_cleanup_baseline(tmp_path, name):
    make_provider, start, fallback = SCENARIOS[name]
    clock = Clock(start)
    QuoteSnapshotRecorder(
        make_provider(), LocalFolderStore(tmp_path), clock.now, clock.sleep, fallback=fallback
    ).record()
    expected = _files(BASELINE / name)
    assert expected, f"baseline {name} is missing"
    assert _files(tmp_path) == expected
