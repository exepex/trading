"""Story A8 criteria 1 and 4: the coverage check covers participant OI (missing and damaged files fail, a file whose
SHA-256 differs from the manifest fails), and the committed real files match NSE's fingerprints in the manifest."""

import hashlib
from datetime import date
from pathlib import Path

from fno.research_data.calendar import CsvSessionCalendar
from fno.storage.coverage import CoverageCheck, CoverageDataset, report_lines
from fno.storage.raw_source import ParticipantOiSource
from fno.storage.raw_store import RawFileStore
from fno.storage.wiring import build_manifest_folder, coverage_datasets, validate_participant_oi

NSE = Path(__file__).parent / "fixtures" / "nse"
SOURCE = "https://nsearchives.nseindia.com/content/circulars/FAOP71777.pdf"
CALENDAR = CsvSessionCalendar(f"date,kind,description,source_url\n2026-10-02,holiday,Gandhi Jayanti,{SOURCE}\n")
REAL_DAY = date(2026, 10, 9)
REAL = (NSE / ParticipantOiSource.filename_for(REAL_DAY)).read_bytes()


class ReadOnlyFakeDrive(RawFileStore):
    def __init__(self, files: dict[str, bytes]):
        self.files = files

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        raise AssertionError("the coverage check must never write")


def file_for(day: date) -> bytes:
    """The real 9 Oct file, re-dated (its numbers stay valid) to stand in for another day."""
    return REAL.replace(b"Oct 09, 2026", f"{day:%b %d, %Y}".encode())


def fingerprints_of(files: dict[date, bytes]) -> dict[str, str]:
    return {ParticipantOiSource.filename_for(d): hashlib.sha256(data).hexdigest() for d, data in files.items()}


def run(files: dict[date, bytes], fingerprints=None):
    """Coverage of 5-9 Oct 2026; every given file is fingerprinted unless `fingerprints` says otherwise."""
    store = ReadOnlyFakeDrive({ParticipantOiSource.path_for(d): data for d, data in files.items()})
    known = fingerprints_of(files) if fingerprints is None else fingerprints
    dataset = CoverageDataset(ParticipantOiSource, validate_participant_oi, known)
    return CoverageCheck(store, CALENDAR, {}).run(dataset, date(2026, 10, 5), date(2026, 10, 9))


def test_participant_oi_is_one_of_the_coverage_datasets():
    assert ParticipantOiSource in [d.source for d in coverage_datasets()]


def test_a_complete_week_passes_and_a_missing_day_fails():
    week = {date(2026, 10, d): file_for(date(2026, 10, d)) for d in range(5, 10)}
    assert run(week).ok and run(week).present == 5
    del week[date(2026, 10, 7)]
    result = run(week)
    assert result.missing == [date(2026, 10, 7)] and not result.ok


def test_a_flipped_byte_or_a_file_for_another_day_is_damaged():
    week = {date(2026, 10, d): file_for(date(2026, 10, d)) for d in range(5, 10)}
    middle = len(REAL) // 2
    week[REAL_DAY] = REAL[:middle] + bytes([REAL[middle] ^ 0xFF]) + REAL[middle + 1 :]
    week[date(2026, 10, 8)] = file_for(date(2026, 10, 7))  # right bytes, wrong day
    result = run(week, fingerprints={})  # content checks only: the flipped byte and the wrong day are both caught
    assert [day for day, _ in result.damaged] == [date(2026, 10, 8), REAL_DAY]
    assert "INCOMPLETE" in report_lines([result])[-1]


def test_a_file_that_differs_from_its_fingerprint_is_damaged_even_when_it_parses():
    name = ParticipantOiSource.filename_for(REAL_DAY)
    week = {date(2026, 10, d): file_for(date(2026, 10, d)) for d in range(5, 10)}
    week[REAL_DAY] = REAL.replace(b"\r\n", b"\n")  # still a valid file, but not NSE's bytes
    result = run(week, {name: hashlib.sha256(REAL).hexdigest()})
    assert result.damaged == [(REAL_DAY, f"{name}: SHA-256 differs from the manifest")]


def test_the_committed_real_files_match_nses_fingerprints_in_the_manifest():
    fingerprints = build_manifest_folder().fingerprints(ParticipantOiSource)
    for day in (date(2019, 6, 3), date(2022, 1, 3), REAL_DAY):
        name = ParticipantOiSource.filename_for(day)
        assert hashlib.sha256((NSE / name).read_bytes()).hexdigest() == fingerprints[name]
