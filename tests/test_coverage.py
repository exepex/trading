"""Story A1: the coverage check lists exactly the missing and damaged raw files, against the session calendar, and
never writes."""

import hashlib
import zipfile
from datetime import date
from io import BytesIO
from pathlib import Path

import pytest

from fno.fo_bhavcopy import read_fo_file
from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.content_checks import validate_index_close
from fno.storage.coverage import CoverageCheck, CoverageDataset, read_exceptions, report_lines
from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource
from fno.storage.raw_store import RawFileStore
from fno.storage.wiring import coverage_datasets

NSE = Path(__file__).parent / "fixtures" / "nse"
SOURCE = "https://nsearchives.nseindia.com/content/circulars/example.pdf"
CALENDAR = CsvSessionCalendar(
    "date,kind,description,source_url\n"
    f"2019-01-02,holiday,Test holiday,{SOURCE}\n"
    f"2019-01-05,special,Test Saturday session,{SOURCE}\n"
)


class ReadOnlyFakeDrive(RawFileStore):
    """Files by path; any write fails the test."""

    def __init__(self, files: dict[str, bytes]):
        self.files = files

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        raise AssertionError("the coverage check must never write")


def legacy_zip(day: date) -> bytes:
    """A small, valid old-format F&O file for one day."""
    stamp = f"{day:%d}-{day:%b}-{day:%Y}".upper()
    csv_text = (
        "INSTRUMENT,SYMBOL,EXPIRY_DT,STRIKE_PR,OPTION_TYP,OPEN,HIGH,LOW,CLOSE,SETTLE_PR,CONTRACTS,VAL_INLAKH,"
        "OPEN_INT,CHG_IN_OI,TIMESTAMP\n"
        f"FUTIDX,NIFTY,31-JAN-2019,0,XX,1,1,1,1,1,1,1,1,0,{stamp}\n"
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(NseLegacyFoSource.filename_for(day).removesuffix(".zip"), csv_text)
    return buffer.getvalue()


def flip_byte(data: bytes) -> bytes:
    middle = len(data) // 2
    return data[:middle] + bytes([data[middle] ^ 0xFF]) + data[middle + 1 :]


def drive(days: list[date], damaged: date | None = None) -> ReadOnlyFakeDrive:
    files = {NseLegacyFoSource.path_for(d): legacy_zip(d) for d in days}
    if damaged:
        files[NseLegacyFoSource.path_for(damaged)] = flip_byte(legacy_zip(damaged))
    return ReadOnlyFakeDrive(files)


# 1-7 Jan 2019: sessions are 1 (Tue), 3, 4, 5 (special Saturday), 7; the 2nd is a holiday, the 6th a Sunday.
SESSIONS = [date(2019, 1, d) for d in (1, 3, 4, 5, 7)]


def fingerprinted(store: ReadOnlyFakeDrive) -> CoverageDataset:
    """The old-format dataset with a manifest row for every file the store holds."""
    rows = {path.rsplit("/", 1)[1]: hashlib.sha256(data).hexdigest() for path, data in store.files.items()}
    return CoverageDataset(NseLegacyFoSource, read_fo_file, rows)


def run(store, exceptions=None, start=date(2019, 1, 1), end=date(2019, 1, 7), dataset=None):
    return CoverageCheck(store, CALENDAR, exceptions or {}).run(dataset or fingerprinted(store), start, end)


def test_complete_set_passes():
    result = run(drive(SESSIONS))
    assert (result.expected, result.present, result.missing, result.damaged) == (5, 5, [], [])
    assert result.ok and report_lines([result])[-1] == "result: complete"


def test_lists_exactly_the_missing_day_and_the_damaged_file():
    result = run(drive([date(2019, 1, d) for d in (1, 3, 7)], damaged=date(2019, 1, 4)))
    assert result.missing == [date(2019, 1, 5)]  # the special Saturday session is expected too
    assert [day for day, _ in result.damaged] == [date(2019, 1, 4)]
    assert not result.ok and report_lines([result])[-1].startswith("result: INCOMPLETE")


def test_a_sourced_exception_explains_a_gap():
    exceptions = {(NseLegacyFoSource.dataset, date(2019, 1, 5)): "NSE published no file"}
    result = run(drive([date(2019, 1, d) for d in (1, 3, 4, 7)]), exceptions)
    assert result.ok and result.excepted == [(date(2019, 1, 5), "NSE published no file")]


def test_file_on_a_closed_day_is_reported_for_review():
    result = run(drive([*SESSIONS, date(2019, 1, 2)]))
    assert result.unexpected == [date(2019, 1, 2)] and result.ok
    assert any(line.startswith("unexpected file") for line in report_lines([result]))


def test_range_is_clipped_to_the_days_the_dataset_exists():
    result = CoverageCheck(ReadOnlyFakeDrive({}), CALENDAR, {}).run(
        coverage_datasets()[1], date(2019, 1, 1), date(2019, 1, 7)
    )
    assert result.expected == 0 and result.start == NseDailyFoSource.first_day  # UDiFF starts on 1 Jan 2024


def test_real_nse_files_pass_their_validators():
    day = date(2024, 1, 2)
    for source in (NseDailyFoSource, NseLegacyFoSource, NseIndexCloseSource):
        dataset = next(d for d in coverage_datasets() if d.source is source)
        filename = source.filename_for(day)
        # The fixtures are trimmed copies of NSE's files, so they pass the content check, not the manifest's SHA-256.
        dataset.validate(filename, (NSE / filename).read_bytes())


def test_index_close_without_india_vix_is_damaged():
    text = "Index Name,Closing Index Value\nNifty 50,21665.80\n"
    with pytest.raises(ValueError, match="India VIX"):
        validate_index_close("ind_close_all_02012024.csv", text.encode())


def test_exceptions_need_a_source(tmp_path):
    path = tmp_path / "exceptions.csv"
    path.write_text("dataset,date,reason,source_url\nnse/x,2019-01-05,no file,\n")
    with pytest.raises(ValueError, match="source"):
        read_exceptions(path)
    assert read_exceptions(tmp_path / "absent.csv") == {}


def test_a_file_without_a_manifest_row_is_reported_and_the_result_is_not_complete():
    store = drive(SESSIONS)
    rows = dict(fingerprinted(store).fingerprints)
    del rows[NseLegacyFoSource.filename_for(date(2019, 1, 4))]  # planted: archived, but no manifest row
    result = run(store, dataset=CoverageDataset(NseLegacyFoSource, read_fo_file, rows))
    assert result.present == 5 and result.unfingerprinted == [date(2019, 1, 4)] and not result.ok
    lines = report_lines([result])
    assert lines[1].split()[-2] == "1"  # the "no sha" column (the last is "revised", A11)
    assert f"no fingerprint (content checked only) {NseLegacyFoSource.dataset} 2019-01-04" in lines
    assert lines[-1].startswith("result: INCOMPLETE")
