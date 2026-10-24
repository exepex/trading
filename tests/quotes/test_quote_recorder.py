"""3 pm quote recorder (story A4): immutable attempts, canonical snapshot, validity flags, never orders."""

from datetime import date, datetime, timedelta

from fno.models import IST, OptionChain, OptionQuote, QuoteBook
from fno.quotes.quote_validity import quote_validity
from fno.quotes.recorder import QuoteSnapshotRecorder, monthly_expiries
from fno.quotes.report import canonical_snapshots, spread_report
from fno.storage.raw_store import LocalFolderStore

DAY = date(2026, 10, 13)  # a Tuesday
TRADED = datetime(2026, 10, 13, 14, 58, tzinfo=IST)


class Clock:
    def __init__(self, start):
        self.t = start

    def now(self):
        self.t += timedelta(seconds=1)
        return self.t

    def sleep(self, seconds):
        self.t += timedelta(seconds=seconds)


class FakeProvider:
    name = "fake"

    def __init__(self, fail_first=0, traded=TRADED, book=None):
        self.fail_first, self.calls, self.traded, self.book = fail_first, 0, traded, book

    def expiries(self, underlying):
        return [date(2026, 10, 20), date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 24), date(2026, 12, 29)]

    def chain(self, underlying, expiry):
        quotes = {(k, t): OptionQuote(k, t, 10.0, symbol=f"N{k:g}{t}") for k in (21000.0, 22000.0, 23000.0, 25000.0)
                  for t in ("CE", "PE")}  # fmt: skip
        return OptionChain("NIFTY", 22000.0, expiry, TRADED, 65, quotes)

    def quote_book(self, chain, strike, kind):
        self.calls += 1
        if self.calls <= self.fail_first:
            raise ConnectionError("dropped")
        if self.book:
            return self.book
        return QuoteBook(f"N{strike:g}{kind}", 10.0, 11.0, 65, 130, 10.5, self.traded, "fields", "h")

    def place_order(self, *a, **k):  # the recorder must never call anything like this
        raise AssertionError("order call")


def recorder(tmp_path, provider, start):
    clock = Clock(start)
    return QuoteSnapshotRecorder(provider, LocalFolderStore(tmp_path), clock.now, clock.sleep), tmp_path


def files(folder):
    return sorted(p.name for p in folder.rglob("*") if p.is_file())


def test_monthly_expiries_are_the_last_of_each_month_from_today():
    listed = FakeProvider().expiries("NIFTY")
    assert monthly_expiries(listed, DAY) == [date(2026, 10, 27), date(2026, 11, 24)]


def test_a_complete_attempt_becomes_canonical_and_a_rerun_records_nothing(tmp_path):
    rec, folder = recorder(tmp_path, FakeProvider(), datetime(2026, 10, 13, 14, 55, tzinfo=IST))
    result = rec.record()
    assert result.status == "recorded" and result.complete and result.rows == 12  # 3 strikes x 2 types x 2 expiries
    assert rec.canonical(DAY) == result.snapshot_id
    before = files(folder)
    assert rec.record().status == "already recorded" and files(folder) == before


def test_an_incomplete_attempt_is_kept_and_retried_inside_the_window(tmp_path):
    rec, folder = recorder(tmp_path, FakeProvider(fail_first=1), datetime(2026, 10, 13, 14, 55, tzinfo=IST))
    result = rec.record()
    names = files(folder)
    assert result.complete and sum(n.endswith(".csv") for n in names) == 2  # the failed attempt stays
    assert rec.canonical(DAY) == result.snapshot_id


def test_after_the_window_without_a_complete_attempt_the_day_is_none(tmp_path):
    rec, _ = recorder(tmp_path, FakeProvider(fail_first=10_000), datetime(2026, 10, 13, 15, 9, 30, tzinfo=IST))
    result = rec.record()
    assert not result.complete and rec.canonical(DAY) == "none"


def test_weekends_holidays_and_early_starts(tmp_path):
    rec, folder = recorder(tmp_path, FakeProvider(), datetime(2026, 10, 17, 15, 0, tzinfo=IST))
    assert rec.record().status == "not a trading day" and files(folder) == []
    old_trade = datetime(2026, 10, 12, 15, 29, tzinfo=IST)  # nothing traded today: an exchange holiday
    rec, folder = recorder(tmp_path / "h", FakeProvider(traded=old_trade), datetime(2026, 10, 13, 15, 0, tzinfo=IST))
    assert rec.record().status == "not a trading day" and files(tmp_path / "h") == []
    rec, _ = recorder(tmp_path / "e", FakeProvider(), datetime(2026, 10, 13, 14, 40, tzinfo=IST))
    assert rec.record().status == "recorded"  # waited for 14:55
    rec, _ = recorder(tmp_path / "x", FakeProvider(), datetime(2026, 10, 13, 9, 30, tzinfo=IST))
    assert rec.record().status == "too early"


def test_bad_quotes_are_kept_but_never_valid():
    one_sided = QuoteBook("x", None, 11.0, None, 65, 10.0, TRADED, "fields", "h")
    crossed = QuoteBook("x", 12.0, 11.0, 65, 65, 10.0, TRADED, "fields", "h")
    no_size = QuoteBook("x", 10.0, 11.0, 0, 65, 10.0, TRADED, "fields", "h")
    stale_depth = QuoteBook("x", 10.0, 11.0, 65, 65, 10.0, TRADED - timedelta(days=1), "depth", "h")
    stale_fields = QuoteBook("x", 10.0, 11.0, 65, 65, 10.0, TRADED - timedelta(days=1), "fields", "h")
    never_traded = QuoteBook("x", 10.0, 11.0, 65, 65, None, None, "fields", "h")
    good = QuoteBook("x", 10.0, 11.0, 65, 65, 10.0, TRADED, "fields", "h")
    assert quote_validity(None, DAY) == "no quote"
    assert quote_validity(one_sided, DAY) and quote_validity(crossed, DAY).startswith("crossed")
    assert quote_validity(no_size, DAY) == "no size" and "stale" in quote_validity(stale_depth, DAY)
    assert "no trade today" in quote_validity(stale_fields, DAY)  # best bid/offer fields are not proof of freshness
    assert "no trade today" in quote_validity(never_traded, DAY)
    assert quote_validity(good, DAY) == ""


def test_an_outside_window_attempt_is_never_canonical(tmp_path):
    rec, folder = recorder(tmp_path, FakeProvider(), datetime(2026, 10, 13, 20, 0, tzinfo=IST))
    result = rec.record(outside_window=True)
    assert result.status == "recorded" and rec.canonical(DAY) is None


def test_the_report_uses_canonical_valid_quotes_by_distance(tmp_path):
    rec, folder = recorder(tmp_path, FakeProvider(), datetime(2026, 10, 13, 14, 55, tzinfo=IST))
    rec.record()
    report = spread_report(canonical_snapshots(folder, LocalFolderStore(folder)))
    assert report["days"] == 1
    assert report["bands"]["0-1%"]["median_half_spread"] == 0.5 and report["bands"]["0-1%"]["valid_quotes"] == 4
    assert report["bands"]["3-5%"]["valid_quotes"] == 8  # 21000 and 23000 are 4.5% from 22000


def test_fewer_than_two_monthly_expiries_is_recorded_but_incomplete(tmp_path):
    class December(FakeProvider):
        def expiries(self, underlying):
            return [date(2026, 12, 22), date(2026, 12, 29)]  # Groww lists no 2027 expiries in December

    december_trade = datetime(2026, 12, 23, 14, 58, tzinfo=IST)
    rec, _ = recorder(tmp_path, December(traded=december_trade), datetime(2026, 12, 23, 15, 9, 30, tzinfo=IST))
    result = rec.record()
    assert result.rows == 6 and not result.complete and rec.canonical(date(2026, 12, 23)) == "none"


class FakeListing:
    def __init__(self, dates=None, fail=False):
        self.dates, self.fail = dates or [], fail

    def listed(self, underlying, today):
        if self.fail:
            raise RuntimeError("no recent NSE file")
        return self.dates, {"source": "nse-file", "file": "f.zip", "sha256": "abc"}


def test_december_takes_january_from_the_nse_listing_and_records_where_it_came_from(tmp_path):
    class December(FakeProvider):
        def expiries(self, underlying):
            return [date(2026, 12, 22), date(2026, 12, 29)]

    trade = datetime(2026, 12, 23, 14, 58, tzinfo=IST)
    nse = FakeListing([date(2026, 12, 29), date(2027, 1, 5), date(2027, 1, 12), date(2027, 1, 26), date(2027, 3, 30)])
    clock = Clock(datetime(2026, 12, 23, 14, 55, tzinfo=IST))
    rec = QuoteSnapshotRecorder(
        December(traded=trade), LocalFolderStore(tmp_path), clock.now, clock.sleep, fallback=nse
    )
    result = rec.record()
    assert result.complete and result.rows == 12
    meta = next(tmp_path.rglob("*.meta.json")).read_text()
    assert '"2027-01-26"' in meta and '"nse-file"' in meta and '"abc"' in meta


def test_an_unavailable_listing_keeps_december_incomplete(tmp_path):
    class December(FakeProvider):
        def expiries(self, underlying):
            return [date(2026, 12, 29)]

    trade = datetime(2026, 12, 23, 14, 58, tzinfo=IST)
    clock = Clock(datetime(2026, 12, 23, 15, 9, 30, tzinfo=IST))
    rec = QuoteSnapshotRecorder(
        December(traded=trade), LocalFolderStore(tmp_path), clock.now, clock.sleep, fallback=FakeListing(fail=True)
    )
    result = rec.record()
    assert not result.complete and rec.canonical(date(2026, 12, 23)) == "none"
    assert "expiry fallback" in next(tmp_path.rglob("*.meta.json")).read_text()


class OnlyMarketData:
    """A provider that fails the test on any call other than the three market-data calls the recorder may make."""

    ALLOWED = {"name", "expiries", "chain", "quote_book"}

    def __init__(self):
        self.inner = FakeProvider()

    def __getattr__(self, attr):
        if attr not in self.ALLOWED:
            raise AssertionError(f"the recorder called {attr}: only market data is allowed")
        return getattr(self.inner, attr)


def test_the_recorder_makes_only_market_data_calls(tmp_path):
    rec, _ = recorder(tmp_path, OnlyMarketData(), datetime(2026, 10, 13, 14, 55, tzinfo=IST))
    assert rec.record().complete
