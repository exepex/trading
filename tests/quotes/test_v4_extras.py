"""Story G10 completion, criterion 3a: the `v4` window records V4's expiry by G7b's `first_v4_expiry` (imported, on
A7's real calendar) beside A4's monthlies, and one quote of the future of `e`; both only in the attempt's quote file,
never counted for its completeness; the sidecar names `v4_expiry`. A day the calendar cannot answer records
`v4_expiry: None` with its note (judge 581 m2); a failed chain or future quote is named, never hidden."""

import json
from datetime import date, datetime

from fno.forecast_v4_rules.v4_expiry import first_v4_expiry
from fno.models import IST, QuoteBook
from fno.quotes.book_fetch import BookFetcher, WindowEnded
from fno.quotes.future_quotes import FutureQuotes, NoFutureQuotes
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.quotes.snapshot_rows import COLUMNS
from fno.quotes.v4_extras import FUTURE_KIND, V4Extras
from fno.storage.raw_store import LocalFolderStore
from fno.storage.wiring import build_session_calendar
from tests.quotes.test_quote_recorder import FakeProvider

CALENDAR = build_session_calendar()
MONDAY = date(2026, 10, 26)
OCT, NOV3, NOV24 = date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 24)
NOW = datetime(2026, 10, 26, 14, 31, 5, tzinfo=IST)
BOOK = QuoteBook("NIFTY26OCTFUT", 25010.0, 25012.5, 75, 150, 25011.0, datetime(2026, 10, 26, 14, 30, 58, tzinfo=IST),
                 "fields", "f" * 64)  # fmt: skip


class Futures(FutureQuotes):
    def __init__(self, fails=False):
        self.fails, self.asked = fails, []

    def quote(self, expiry):
        self.asked.append(expiry)
        if self.fails:
            raise ConnectionError("dropped")
        return BOOK


class Provider(FakeProvider):
    def __init__(self, chain_fails=False):
        super().__init__()
        self.chain_fails, self.chains = chain_fails, []

    def chain(self, underlying, expiry):
        self.chains.append(expiry)
        if self.chain_fails:
            raise TimeoutError("slow")
        return super().chain(underlying, expiry)


def extras(provider=None, futures=None, sent=lambda: NOW, choose=None):
    provider = provider or Provider()
    rule = choose or (lambda day, listed: first_v4_expiry(day, listed, CALENDAR))
    return V4Extras(rule, provider, futures or Futures(), lambda: BookFetcher(provider, lambda: NOW),
                    QuoteSnapshotRecorder._contracts, sent, lambda: NOW, "NIFTY")  # fmt: skip


def test_a_monday_takes_the_next_weekly_when_tuesday_s_has_one_session():
    found = extras()
    rows = found.capture("nifty_20261026_143000", MONDAY, [OCT, NOV3, NOV24], [OCT, NOV24])
    assert found.meta()["v4_expiry"] == "2026-11-03" and found.meta()["v4_failures"] == []
    assert {r["expiry"] for r in rows if r["type"] != FUTURE_KIND} == {"2026-11-03"}
    future = [r for r in rows if r["type"] == FUTURE_KIND]
    assert len(future) == 1 and future[0]["expiry"] == "2026-10-27" and future[0]["bid"] == "25010"
    assert future[0]["last_trade_time"] == "2026-10-26T14:30:58+05:30" and set(future[0]) == set(COLUMNS)


def test_a_chosen_monthly_adds_no_chain_and_none_chosen_names_none():
    provider = Provider()
    monthly = extras(provider, choose=lambda day, listed: NOV24)
    monthly.capture("s", MONDAY, [OCT, NOV24], [OCT, NOV24])
    assert monthly.meta()["v4_expiry"] == "2026-11-24" and provider.chains == []
    nothing = extras(provider, choose=lambda day, listed: None)
    nothing.capture("s", MONDAY, [OCT], [OCT, NOV24])
    assert nothing.meta()["v4_expiry"] is None and "v4_expiry_note" not in nothing.meta() and provider.chains == []


def test_a_day_past_the_calendar_s_end_records_none_with_its_note():
    """Judge 581 m2: the calendar ends on 31 Dec 2026, so from 22 Dec every choice raises CalendarError."""
    found = extras()
    rows = found.capture("s", date(2026, 12, 28), [date(2027, 1, 5), date(2027, 1, 26)], [date(2027, 1, 26)])
    assert found.meta()["v4_expiry"] is None and found.meta()["v4_expiry_note"].startswith("v4 expiry not chosen:")
    assert [r["type"] for r in rows] == [FUTURE_KIND]  # the future is still quoted


def test_a_failed_chain_or_future_is_named_and_never_raises():
    found = extras(Provider(chain_fails=True), Futures(fails=True))
    assert found.capture("s", MONDAY, [OCT, NOV3, NOV24], [OCT, NOV24]) == []
    assert found.meta()["v4_failures"] == ["chain 2026-11-03: TimeoutError (provider message withheld)"]
    assert found.meta()["future_quote"] == "future 2026-10-27: ConnectionError (provider message withheld)"
    late = extras(sent=lambda: (_ for _ in ()).throw(WindowEnded("window ended")))
    late.capture("s", MONDAY, [OCT, NOV3, NOV24], [OCT, NOV24])
    assert late.meta()["future_quote"].startswith("future 2026-10-27: WindowEnded")
    named = extras(futures=NoFutureQuotes("nse"))
    named.capture("s", MONDAY, [OCT, NOV3, NOV24], [OCT, NOV24])
    assert named.meta()["future_quote"].startswith("future 2026-10-27: RuntimeError")


def test_on_a_monthly_expiry_day_e_is_the_next_monthly():
    found = extras()
    rows = found.capture("s", OCT, [OCT, NOV3, NOV24], [OCT, NOV24])
    assert [r["expiry"] for r in rows if r["type"] == FUTURE_KIND] == ["2026-11-24"]


def test_the_recorder_keeps_the_extras_out_of_its_completeness_and_the_default_capture_has_none(tmp_path):
    from tests.quotes.test_quote_recorder import Clock

    clock = Clock(datetime(2026, 10, 13, 14, 59, tzinfo=IST))  # A4's fixture day: its quotes traded at 14:58
    plain = QuoteSnapshotRecorder(FakeProvider(), LocalFolderStore(tmp_path / "a"), clock.now, clock.sleep)
    result = plain.record(outside_window=True)
    meta = json.loads(next((tmp_path / "a").rglob("*.meta.json")).read_text())
    assert not {"v4_expiry", "v4_failures", "future_quote"} & set(meta)  # A4's default capture: unchanged keys
    assert FUTURE_KIND not in next((tmp_path / "a").rglob("*.csv")).read_text()
    with_extras = QuoteSnapshotRecorder(Provider(chain_fails=False), LocalFolderStore(tmp_path / "b"), clock.now,
                                        clock.sleep, extras=extras(futures=Futures(fails=True)))  # fmt: skip
    extra = with_extras.record(outside_window=True)
    assert (extra.complete, extra.rows) == (result.complete, result.rows)  # the extras never count
    meta = json.loads(next((tmp_path / "b").rglob("*.meta.json")).read_text())
    assert "v4_expiry" in meta and meta["future_quote"].startswith("future")


def test_the_v4_window_is_built_with_its_extras_on_the_window_s_own_provider():
    from fno.config import load_app_config
    from fno.quotes.capture_log import TimedProvider
    from fno.quotes.window_wiring import build_window_quote_recorder

    recorder = build_window_quote_recorder(load_app_config(), "v4")
    assert isinstance(recorder.extras, V4Extras) and isinstance(recorder.extras.provider, TimedProvider)
    assert recorder.extras.choose(MONDAY, [OCT, NOV3, NOV24]) == NOV3  # G7b's rule on A7's real calendar
