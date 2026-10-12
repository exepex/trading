"""The capacity-screen downloader: monthly expiries decided as-of from each complete file, and no data loss on
resume (ChatGPT review 5, sections 2-4)."""

import csv
import importlib.util
import io
import sys
import zipfile
from datetime import date
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "2026-10-12-capacity-screen"
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("capacity_fetch", HERE / "fetch.py")
fetch = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = fetch
spec.loader.exec_module(fetch)

from expiries import eligible_monthly, monthly_expiries  # noqa: E402

COLUMNS = ["TckrSymb", "FinInstrmTp", *fetch.OPTION_FIELDS]


def nse_zip(day: date, expiries: list[date], spot: float = 21665.8) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for e in expiries:
        writer.writerow({"TckrSymb": "NIFTY", "FinInstrmTp": "IDO", "TradDt": day.isoformat(), "XpryDt": e.isoformat(),
                         "StrkPric": "21650", "OptnTp": "CE", "ClsPric": "100", "UndrlygPric": str(spot),
                         "TtlTradgVol": "5", "NewBrdLotQty": "50"})  # fmt: skip
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("f.csv", buf.getvalue())
    return out.getvalue()


JAN_2 = date(2024, 1, 2)
JAN_2_LISTED = [date(2024, 1, 4), date(2024, 1, 11), date(2024, 1, 18), date(2024, 1, 25), date(2024, 2, 1),
                date(2024, 2, 29), date(2024, 3, 28)]  # fmt: skip


def test_2_january_2024_has_no_eligible_monthly_and_never_takes_the_weekly():
    expiries, kept = fetch.extract(nse_zip(JAN_2, JAN_2_LISTED), JAN_2)
    monthly = {date.fromisoformat(r["expiry"]) for r in expiries if r["monthly"]}
    assert monthly == {date(2024, 1, 25), date(2024, 2, 29), date(2024, 3, 28)}
    assert eligible_monthly(JAN_2, monthly) is None  # 1 Feb (30 days) is a weekly; 29 Feb is 58 days away
    assert {r["XpryDt"] for r in kept} == {"2024-01-25", "2024-02-01"}  # kept prices never decide monthly identity


def test_a_real_monthly_a_holiday_moved_monthly_and_an_expiry_change_are_decided_as_of_the_day():
    assert eligible_monthly(date(2024, 1, 15), monthly_expiries(set(JAN_2_LISTED))) == date(2024, 2, 29)  # 45 days
    moved = {date(2024, 3, 20), date(2024, 3, 27)}  # the month's last Thursday was a holiday: Wednesday expiry
    assert monthly_expiries(moved) == {date(2024, 3, 27)}
    before_change, after_change = {date(2025, 4, 24)}, {date(2025, 4, 24), date(2025, 4, 29)}
    assert monthly_expiries(before_change) == {date(2025, 4, 24)}  # each day uses only what it lists
    assert monthly_expiries(after_change) == {date(2025, 4, 29)}


class Library:
    def __init__(self, files):
        self.files, self.asked = files, []

    def get(self, path):
        self.asked.append(path)
        return type("Raw", (), {"data": self.files.get(path)})()


def library_for(days):
    return Library({fetch.NseDailyFoSource.path_for(d): nse_zip(d, JAN_2_LISTED) for d in days})


def test_resuming_from_the_committed_files_keeps_every_row(tmp_path):
    first = library_for([JAN_2, date(2024, 1, 3)])
    fetch.update(tmp_path, first, JAN_2, date(2024, 1, 3))
    before = {f: (tmp_path / f).read_bytes() for f in fetch.FILES.values()}
    again = library_for([])
    fetch.update(tmp_path, again, JAN_2, date(2024, 1, 3))
    assert again.asked == [] and {f: (tmp_path / f).read_bytes() for f in fetch.FILES.values()} == before


def test_a_partial_resume_adds_only_the_new_days(tmp_path):
    fetch.update(tmp_path, library_for([JAN_2]), JAN_2, JAN_2)
    later = library_for([date(2024, 1, 3)])
    fetch.update(tmp_path, later, JAN_2, date(2024, 1, 4))
    manifest = fetch.read_csv(tmp_path / "manifest.csv")
    assert [r["date"] for r in manifest] == ["2024-01-02", "2024-01-03", "2024-01-04"]
    assert [r["status"] for r in manifest] == ["200", "200", "404"]
    assert len(later.asked) == 2 and {r["date"] for r in fetch.read_csv(tmp_path / "nifty_expiries.csv.gz")} == {
        "2024-01-02",
        "2024-01-03",
    }


def test_a_manifest_without_its_extracts_stops_without_writing(tmp_path):
    fetch.update(tmp_path, library_for([JAN_2]), JAN_2, JAN_2)
    (tmp_path / "nifty_options.csv.gz").unlink()
    manifest = (tmp_path / "manifest.csv").read_bytes()
    with pytest.raises(fetch.InconsistentData):
        fetch.update(tmp_path, library_for([]), JAN_2, date(2024, 1, 3))
    assert (tmp_path / "manifest.csv").read_bytes() == manifest and not (tmp_path / "nifty_options.csv.gz").exists()


class Unreachable:
    def get(self, path):
        raise fetch.RawSourceUnavailable("NSE: connection refused")


def test_a_rebuild_that_fetches_nothing_leaves_the_files_untouched(tmp_path):
    fetch.update(tmp_path, library_for([JAN_2]), JAN_2, JAN_2)
    before = {f: (tmp_path / f).read_bytes() for f in fetch.FILES.values()}
    added = fetch.update(tmp_path, Unreachable(), JAN_2, date(2024, 1, 3), rebuild=True)
    assert added["days"] == 0 and {f: (tmp_path / f).read_bytes() for f in fetch.FILES.values()} == before


def test_a_holiday_moved_weekly_is_not_mistaken_for_the_monthly():
    from expiries import monthly_as_of

    listings = {
        date(2025, 2, 20): {date(2025, 4, 24): 63},  # the April monthly is listed two months ahead
        date(2025, 3, 27): {date(2025, 4, 24): 28, date(2025, 4, 30): 34},  # the 30 Apr weekly appears in April
    }
    assert monthly_as_of(listings)[date(2025, 3, 27)] == {date(2025, 4, 24)}


def test_option_rows_that_disagree_with_the_manifest_are_rejected(tmp_path):
    fetch.update(tmp_path, library_for([JAN_2, date(2024, 1, 3)]), JAN_2, date(2024, 1, 3))
    rows = fetch.read_csv(tmp_path / "nifty_options.csv.gz")
    for broken in ([], rows[1:]):  # header only; one row missing
        fetch.write_csv(tmp_path / "nifty_options.csv.gz", fetch.OPTION_FIELDS, broken)
        with pytest.raises(fetch.InconsistentData):
            fetch.update(tmp_path, library_for([]), JAN_2, date(2024, 1, 4))
    fetch.write_csv(tmp_path / "nifty_options.csv.gz", fetch.OPTION_FIELDS, rows)
    assert fetch.update(tmp_path, library_for([]), JAN_2, date(2024, 1, 3)) == {"days": 0, "files": 0}


def test_a_re_dated_monthly_keeps_only_its_new_date():
    from expiries import eligible_monthly, monthly_as_of

    listings = {
        date(2025, 7, 1): {date(2025, 9, 25): 86},  # listed for Thursday 25 Sep
        date(2025, 8, 1): {date(2025, 9, 30): 60},  # NSE moved it to Tuesday 30 Sep; the old date is gone
        date(2025, 8, 18): {date(2025, 9, 30): 43, date(2025, 8, 26): 8},
    }
    monthly = monthly_as_of(listings)
    assert monthly[date(2025, 8, 18)] == {date(2025, 9, 30)}
    assert eligible_monthly(date(2025, 8, 18), monthly[date(2025, 8, 18)]) == date(2025, 9, 30)
