"""Story A5 (judge 7, finding 1): the quote recorder chooses monthly contracts by A5's point-in-time rule."""

import json
from datetime import date, datetime, timedelta

import pytest

from fno.models import IST
from fno.quotes import expiry_listing
from fno.quotes.expiry_listing import ExpiryHistory, ExpiryListUnavailable, NseDailyFileExpiries
from fno.quotes.monthly_contracts import PointInTimeMonthlies
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.research_data.expiries import monthly_expiries as last_expiry_of_each_month
from fno.storage.raw_library import RawFile
from fno.storage.raw_store import LocalFolderStore

from .test_quote_recorder import Clock, FakeProvider
from .test_recorder_baseline import BASELINE, SCENARIOS, _files

APRIL_2 = date(2025, 4, 2)
# NSE's NIFTY expiries on 2 Apr 2025 (UDiFF file of that day, up to June): 30 Apr is a weekly moved for a holiday
LISTED_APRIL_2 = [date(2025, 4, 3), date(2025, 4, 9), date(2025, 4, 17), date(2025, 4, 24), date(2025, 4, 30),
                  date(2025, 5, 29), date(2025, 6, 26)]  # fmt: skip
MONTHLIES = {date(2025, 4, 24), date(2025, 5, 29), date(2025, 6, 26)}


class History(ExpiryHistory):
    """NSE's listings over time: monthlies listed from 90 days ahead, weeklies from 42 days ahead."""

    def __init__(self, monthlies, weeklies, fail=False):
        self.monthlies, self.weeklies, self.fail, self.reads = monthlies, weeklies, fail, []

    def listed_on(self, underlying, day):
        if self.fail:
            raise ExpiryListUnavailable("no NSE F&O file")
        self.reads.append(day)
        listed = [m for m in self.monthlies if 0 <= (m - day).days <= 90]
        listed += [w for w in self.weeklies if 0 <= (w - day).days <= 42]
        return day, sorted(listed), {"source": "fake", "file_date": day.isoformat()}


def april_history(fail=False):
    return History(MONTHLIES, set(LISTED_APRIL_2) - MONTHLIES, fail)


def test_the_holiday_moved_weekly_of_30_april_2025_is_not_taken_for_the_monthly():
    monthly, used = PointInTimeMonthlies(april_history()).monthlies("NIFTY", LISTED_APRIL_2, APRIL_2)
    assert sorted(monthly)[:2] == [date(2025, 4, 24), date(2025, 5, 29)]  # last-of-month would give 30 Apr
    assert date(2025, 4, 30) not in monthly and used  # the answer names the files it relied on


class April(FakeProvider):
    def expiries(self, underlying):
        return LISTED_APRIL_2


def april_recorder(folder, history, start=datetime(2025, 4, 2, 14, 55, tzinfo=IST)):
    clock = Clock(start)
    provider = April(traded=datetime(2025, 4, 2, 14, 58, tzinfo=IST))
    return QuoteSnapshotRecorder(provider, LocalFolderStore(folder), clock.now, clock.sleep, history=history)


def test_the_recorder_records_the_24_april_monthly_and_the_files_that_proved_it(tmp_path):
    history = april_history()
    result = april_recorder(tmp_path, history).record()
    meta = json.loads(next(tmp_path.rglob("*.meta.json")).read_text())
    assert result.complete and meta["expiries"] == ["2025-04-24", "2025-05-29"]
    assert meta["monthly_check"] and all(source["source"] == "fake" for source in meta["monthly_check"])


def test_earlier_files_are_read_once_across_retries():
    history = april_history()
    check = PointInTimeMonthlies(history)
    first = check.monthlies("NIFTY", LISTED_APRIL_2, APRIL_2)
    reads = list(history.reads)
    assert check.monthlies("NIFTY", LISTED_APRIL_2, APRIL_2) == first and history.reads == reads


def test_an_unreadable_history_is_a_recorded_failure_never_a_guess(tmp_path):
    rec = april_recorder(tmp_path, april_history(fail=True), datetime(2025, 4, 2, 15, 9, 30, tzinfo=IST))
    result = rec.record()
    metas = [json.loads(p.read_text()) for p in tmp_path.rglob("*.meta.json")]
    assert not result.complete and result.rows == 0 and rec.canonical(APRIL_2) == "none"
    assert all(m["expiries"] == [] and any(f.startswith("monthly check") for f in m["failures"]) for m in metas)


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_with_a_consistent_history_the_baseline_records_the_same_contracts(tmp_path, name):
    make_provider, start, fallback = SCENARIOS[name]
    listed = set(make_provider().expiries("NIFTY")) | (
        set(fallback.listed("NIFTY", start.date())[0]) if fallback else set()
    )
    monthlies = last_expiry_of_each_month(listed)  # true here: no weekly in these lists was moved for a holiday
    clock = Clock(start)
    QuoteSnapshotRecorder(
        make_provider(), LocalFolderStore(tmp_path), clock.now, clock.sleep, fallback=fallback,
        history=History(monthlies, listed - monthlies),
    ).record()  # fmt: skip
    got, expected = _files(tmp_path), _files(BASELINE / name)
    assert got.keys() == expected.keys()
    for path, data in expected.items():
        if path.endswith(".meta.json"):
            meta = json.loads(got[path])
            assert "monthly_check" in meta
            del meta["monthly_check"]
            assert meta == json.loads(data)
        else:
            assert got[path] == data


class Library:
    def __init__(self, days):
        self.days, self.asked = days, []

    def get(self, path):
        self.asked.append(path)
        day = next((d for d in self.days if d.strftime("%Y%m%d") in path), None)
        return RawFile(day.isoformat().encode() if day else None, "fake store")


def test_nse_files_answer_on_or_before_the_day_and_listed_keeps_looking_only_before_today(monkeypatch):
    def rows(name, data):
        return [{"XpryDt": "2025-04-24", "FinInstrmTp": "IDO", "TckrSymb": "NIFTY"}]

    monkeypatch.setattr(expiry_listing, "read_fo_file", rows)
    friday, saturday = date(2025, 3, 7), date(2025, 3, 8)
    nse = NseDailyFileExpiries(Library([friday, saturday + timedelta(days=2)]))
    file_day, expiries, provenance = nse.listed_on("NIFTY", saturday + timedelta(days=1))  # Sunday: Friday's file
    assert (file_day, expiries, provenance["file_date"]) == (friday, [date(2025, 4, 24)], "2025-03-07")
    assert nse.listed_on("NIFTY", saturday + timedelta(days=2))[0] == date(2025, 3, 10)  # that day's own file
    assert nse.listed("NIFTY", date(2025, 3, 10))[1]["file_date"] == "2025-03-07"  # listed(): before today only
    with pytest.raises(ExpiryListUnavailable):
        nse.listed_on("NIFTY", date(2025, 2, 20))
