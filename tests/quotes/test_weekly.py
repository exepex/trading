"""Story A4f: NIFTY's two nearest weeklies recorded after the other indices, in A4c's window and pace, in their own
dataset (stem `niftyweekly`); a day with no weekly ends "none" at once; the 5% band and the 15:13 stop at their
edges."""

import csv
import io
import json
from dataclasses import replace
from datetime import date, datetime

from fno.models import IST, OptionChain, OptionQuote, QuoteBook
from fno.quotes import index_wiring
from fno.quotes.book_fetch import BookFetcher
from fno.quotes.drive_only_store import DriveOnlyQuoteStore
from fno.quotes.indices import TOO_EARLY_REASON, IndexRecording, weekly_slot
from fno.quotes.indices_cli import INDEX_ALERT, record_indices
from fno.quotes.recorder import DATASET, QuoteSnapshotRecorder
from fno.quotes.weekly import NO_WEEKLY, WEEKLY_DATASET, WEEKLY_NAME, nearest_weeklies
from fno.storage import quote_wiring
from fno.storage.raw_store import LocalFolderStore
from tests.quotes.drive_fakes import SETTINGS, FakeDrive
from tests.quotes.index_fakes import FILE, Clock
from tests.quotes.test_recorder_calendar import CALENDAR, Alerts

DAY = date(2026, 10, 13)  # a Tuesday: a NIFTY weekly expires today
LISTED = [date(2026, 10, 13), date(2026, 10, 20), date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 10),
          date(2026, 11, 24), date(2026, 12, 29)]  # fmt: skip
MONTHLIES = [date(2026, 10, 27), date(2026, 11, 24)]
SPOT = 22000.0


def at(hour, minute, second):
    return datetime(2026, 10, 13, hour, minute, second, tzinfo=IST)


def test_the_two_nearest_non_monthly_expiries_after_today_are_taken():
    assert nearest_weeklies(LISTED, MONTHLIES, DAY) == [date(2026, 10, 20), date(2026, 11, 3)]


def test_today_s_own_weekly_is_not_taken_on_its_expiry_day():
    """Judge 433 minor 1: at about 15:05 it has minutes left; the next-session range (piece 2) cannot score it."""
    assert date(2026, 10, 13) not in nearest_weeklies(LISTED, MONTHLIES, DAY)


def test_in_a_monthly_expiry_week_the_two_weeklies_after_it_are_taken():
    listed = [date(2026, 10, 27), date(2026, 11, 3), date(2026, 11, 10), date(2026, 11, 17), date(2026, 11, 24)]
    assert nearest_weeklies(listed, MONTHLIES, date(2026, 10, 21)) == [date(2026, 11, 3), date(2026, 11, 10)]


def test_one_weekly_listed_gives_one_and_none_gives_none():
    assert nearest_weeklies([*MONTHLIES, date(2026, 11, 3)], MONTHLIES, DAY) == [date(2026, 11, 3)]
    assert nearest_weeklies(MONTHLIES, MONTHLIES, DAY) == []


def test_the_weekly_dataset_sits_beside_a4_s():
    assert f"{DATASET}-weekly" == WEEKLY_DATASET


class NiftyProvider:
    name = "fake"

    def __init__(self, listed=LISTED):
        self.listed, self.chains = listed, []

    def expiries(self, underlying):
        return self.listed

    def chain(self, underlying, expiry):
        self.chains.append(expiry)
        quotes = {(k, t): OptionQuote(k, t, 10.0, oi=1000.0, symbol=f"N{k:g}{t}")
                  for k in (SPOT * 0.9, SPOT * 0.99, SPOT, SPOT * 1.01) for t in ("CE", "PE")}  # fmt: skip
        return OptionChain("NIFTY", SPOT, expiry, datetime(2026, 10, 13, 15, 4, tzinfo=IST), 65, quotes)

    def quote_book(self, chain, strike, kind):
        return QuoteBook(f"N{strike:g}{kind}", 10.0, 11.0, 65, 130, 10.5,
                         datetime(2026, 10, 13, 15, 4, tzinfo=IST), "fields", "h")  # fmt: skip


class NiftyListing:
    def listed(self, underlying, today):
        return LISTED, dict(FILE)


class ShortListing(NiftyListing):
    def __init__(self, listed):
        self.short = listed

    def listed(self, underlying, today):
        return self.short, dict(FILE)


def _weekly(folder, provider, clock, drive):
    store = DriveOnlyQuoteStore(LocalFolderStore(folder), lambda: drive, WEEKLY_DATASET, SETTINGS)
    slot = replace(weekly_slot(), workers=1, per_second=None)  # deterministic order; the pace is A4c's, tested there
    return QuoteSnapshotRecorder(provider, store, clock.now, clock.sleep, fallback=NiftyListing(), calendar=CALENDAR,
                                 dataset=WEEKLY_DATASET, slot=slot)  # fmt: skip


def test_the_weekly_slot_records_two_weeklies_in_its_own_dataset_with_quotes_in_drive_only(tmp_path):
    clock, drive, provider = Clock(datetime(2026, 10, 13, 15, 5, tzinfo=IST)), FakeDrive(), NiftyProvider()
    result = IndexRecording({WEEKLY_NAME: _weekly(tmp_path, provider, clock, drive)}, clock.now, clock.sleep).run()
    weekly = result[WEEKLY_NAME]
    assert weekly.complete and weekly.snapshot_id.startswith("niftyweekly_20261013_150")
    assert provider.chains == [date(2026, 10, 20), date(2026, 11, 3)]
    [csv_path] = drive.files
    assert csv_path.startswith(f"{WEEKLY_DATASET}/2026/10/niftyweekly_")
    rows = list(csv.DictReader(io.StringIO(drive.files[csv_path].decode())))
    assert {r["expiry"] for r in rows} == {"2026-10-20", "2026-11-03"} and all(
        r["open_interest"] == "1000" for r in rows
    )
    marker = tmp_path / WEEKLY_DATASET / "2026/10/niftyweekly_20261013.canonical"
    assert marker.read_text() == weekly.snapshot_id and not list(tmp_path.rglob("*.csv"))
    assert not (tmp_path / DATASET).exists()  # nothing in A4's monthly dataset


def test_a_day_with_no_weekly_listed_is_one_attempt_no_chain_and_none_at_once(tmp_path):
    clock, drive = Clock(datetime(2026, 10, 13, 15, 5, tzinfo=IST)), FakeDrive()
    provider = NiftyProvider(listed=[date(2026, 10, 13), *MONTHLIES])
    result = IndexRecording({WEEKLY_NAME: _weekly(tmp_path, provider, clock, drive)}, clock.now, clock.sleep).run()
    assert result[WEEKLY_NAME].reason == NO_WEEKLY and provider.chains == []
    assert (tmp_path / WEEKLY_DATASET / "2026/10/niftyweekly_20261013.canonical").read_text() == "none"
    sidecars = [json.loads(p.read_text()) for p in tmp_path.rglob("*.meta.json")]
    assert len(sidecars) == 1 and NO_WEEKLY in sidecars[0]["failures"]


def test_the_5_percent_band_at_just_inside_and_just_outside():
    """Judge 433 minor 2: strikes at exactly 5% from spot are in; a paisa beyond is out."""
    quotes = {(k, "CE"): OptionQuote(k, "CE", 1.0) for k in (18999.99, 19000.0, 19000.01, 20999.99, 21000.0, 21000.01)}
    chain = OptionChain("NIFTY", 20000.0, date(2026, 10, 20), datetime(2026, 10, 13, 15, 4, tzinfo=IST), 65, quotes)
    strikes = [k for k, _ in QuoteSnapshotRecorder._contracts(chain)]
    assert strikes == [19000.0, 19000.01, 20999.99, 21000.0]


def test_a_quote_request_at_15_12_59_and_at_15_13_00_starts_and_one_at_15_13_01_does_not():
    """Judge 433 minor 2: the weekly slot's last request edge (A4c's stop, inclusive at 15:13:00)."""
    stop = datetime.combine(DAY, weekly_slot().stop_requests_at, IST)
    chain = NiftyProvider().chain("NIFTY", date(2026, 10, 20))
    for moment, starts in ((at(15, 12, 59), True), (at(15, 13, 0), True), (at(15, 13, 1), False)):
        [got] = BookFetcher(NiftyProvider(), lambda m=moment: m, 1, None, stop).fetch(chain, [(SPOT, "CE")])
        assert (got.error is None) is starts, moment


def test_a_weekly_attempt_with_a_monthly_missing_records_nothing_and_says_why(tmp_path):
    """Judge 441 minor 2: a listing of one month only gives one monthly (A5 takes each month's last expiry); the weekly
    slot then records nothing and says so, as the monthly slot does, never a weekly beside an unknown monthly."""
    clock, drive = Clock(datetime(2026, 10, 13, 15, 5, tzinfo=IST)), FakeDrive()
    short = [date(2026, 10, 13), date(2026, 10, 20), date(2026, 10, 27)]
    provider = NiftyProvider(listed=short)
    recorder = _weekly(tmp_path, provider, clock, drive)
    recorder.fallback = ShortListing(short)  # the fallback lists no more
    result = recorder.attempt_now()
    assert not result.complete and result.rows == 0 and provider.chains == []
    sidecars = [json.loads(p.read_text()) for p in tmp_path.rglob("*.meta.json")]
    assert "only 1 monthly expiries found" in sidecars[0]["failures"]


def test_the_wiring_sends_weekly_quote_files_to_drive_only(tmp_path, monkeypatch):
    """Judge 441 minor 1: wired to A4's store instead, a weekly quote file would stay local and never reach Drive."""
    drive = FakeDrive()
    monkeypatch.setattr(quote_wiring, "build_owner_drive", lambda env: drive)
    monkeypatch.setattr(index_wiring, "QUOTES_FOLDER", tmp_path)
    monkeypatch.setattr(index_wiring, "get_provider", lambda name, cfg: NiftyProvider())
    monkeypatch.setattr(index_wiring, "build_nse_fo_library", lambda: None)
    monkeypatch.setattr(index_wiring, "build_session_calendar", lambda: CALENDAR)
    store = index_wiring.build_index_quote_recorders({})[WEEKLY_NAME].store
    path = f"{WEEKLY_DATASET}/2026/10/niftyweekly_20261013_150501.csv"
    store.put(path, b"snapshot_id\nx\n")
    assert drive.files == {f"raw/{path}": b"snapshot_id\nx\n"} and not list(tmp_path.rglob("*.csv"))


def test_the_weekly_slot_run_too_early_says_not_started_like_the_other_indices(tmp_path, capsys):
    """A4c-2 criterion 7: one IndexRecording, so A4f's weekly slot gets the same wording and no marker."""
    clock, alerts = Clock(datetime(2026, 10, 13, 14, 38, tzinfo=IST)), Alerts()

    def build():
        return {WEEKLY_NAME: _weekly(tmp_path, NiftyProvider(), clock, FakeDrive())}

    assert record_indices(build, alerts, "cal.csv", clock.now, clock.sleep) == 1
    assert alerts.sent == [INDEX_ALERT.format(names=f"{WEEKLY_NAME} ({TOO_EARLY_REASON})")]
    assert capsys.readouterr().out.splitlines()[0].endswith(f"- {TOO_EARLY_REASON}")
    assert not list(tmp_path.rglob("*.canonical"))
