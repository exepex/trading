"""REH1h, H6: through the real composition (`build_librarian`, `build_snapshot_taker`) with the mode set, a file the
evening routine archived is served from the record at its row's commit and archived again only under
`dryrun/<run_id>/`, its manifest row in the rehearsal's checkout; the real Drive is only read; the guard lists the new
session; outside the mode `build_nse_source` is unchanged. The A9 index the session reads carries each row's dataset
and SHA-256 (judges' minor)."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from fno.constants import ENV_FNO_REHEARSAL
from fno.models import IST
from fno.rehearsal.guard import builders
from fno.rehearsal.manifest_rows import MANIFESTS, A9Row, ManifestRows
from fno.rehearsal.mode import Rehearsal
from fno.rehearsal.recorded_archive import RecordedArchiveSession
from fno.storage.manifest_folder import ManifestFolder
from fno.storage.raw_source import NseDailyFoSource, ParticipantOiSource
from fno.storage.snapshot_source import FiiDiiCashBySessionSource
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS

from .fakes import RecordingDrive
from .test_manifest_rows import git, publish

FIXTURES = Path(__file__).parents[1] / "fixtures"
OI_DAY, FLOWS_DAY = date(2026, 10, 9), date(2026, 10, 13)  # the fixtures are the real files of these sessions
OI = (FIXTURES / "nse" / "fao_participant_oi_09102026.csv").read_bytes()
FLOWS = (FIXTURES / "flows" / "fii-dii-cash_13102026.json").read_bytes()
OI_SHA = "d95f403185bbfbe70a487fa427aaa5a05d564d44539c0363e369efc7abbe2e0a"
FLOWS_SHA = "216a4b935610d28536e143de357ac6f4162298b7043ffa16de4bf3b667ee96e7"
OI_PATH, FLOWS_PATH = ParticipantOiSource.path_for(OI_DAY), FiiDiiCashBySessionSource.path_for(FLOWS_DAY)
OI_URL, FLOWS_URL = ParticipantOiSource.url_for(OI_PATH), FiiDiiCashBySessionSource.url_for(FLOWS_PATH)


def ist(day, hour, minute, second):
    return datetime(day.year, day.month, day.day, hour, minute, second, tzinfo=IST)


def record(tmp_path):
    """The record's main: the day's two rows, each committed by the evening routine at its own time."""
    repo = tmp_path / "record"
    (repo / MANIFESTS).mkdir(parents=True)
    git(repo, "init", "-q")
    for key, value in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(repo, "config", key, value)
    header = "date,url,status,sha256,size_bytes\n"
    for name, row, when in (
        ("participant-oi", f"{OI_DAY},{OI_URL},200,{OI_SHA},{len(OI)}\n", ist(OI_DAY, 19, 55, 29)),
        ("fii-dii-cash-by-session", f"{FLOWS_DAY},{FLOWS_URL},200,{FLOWS_SHA},{len(FLOWS)}\n",
         ist(FLOWS_DAY, 19, 55, 39)),
    ):  # fmt: skip
        (repo / MANIFESTS / f"{name}.csv").write_text(header + row)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", name, when=when.isoformat())
    publish(repo)
    return repo


class Clock:
    def __init__(self, at):
        self.at = at

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.at += timedelta(seconds=seconds)


@pytest.fixture
def rehearsing(monkeypatch, tmp_path):
    """The mode for a replay day, the real Drive a recording fake holding the record's raw files, the writer's
    manifests the rehearsal checkout's own folder, and the replay clock at 19:53:30 that day."""

    def start(day):
        repo = record(tmp_path)
        monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal(day, "r1", tmp_path / "state", repo).to_env())
        for name in OWNER_UPLOAD_SETTINGS:
            monkeypatch.setenv(name, "planted")
        real = RecordingDrive({f"raw/{OI_PATH}": OI, f"raw/{FLOWS_PATH}": FLOWS})
        monkeypatch.setattr("fno.storage.wiring.GoogleDriveUploadStore", lambda *a, **k: real)
        checkout = tmp_path / "checkout" / "manifests"
        checkout.mkdir(parents=True)
        # the writers' builder, not the constant: a module first imported now would keep a patched constant for the
        # rest of the worker (`backfill_daily` did, failing `test_rehearsed_day` by test order, 24 Oct)
        monkeypatch.setattr("fno.storage.wiring.build_manifest_folder", lambda: ManifestFolder(checkout))
        clock = Clock(ist(day, 19, 53, 30))
        monkeypatch.setattr("fno.models._clock", clock)
        monkeypatch.setattr("time.sleep", clock.sleep)
        return real, checkout, clock

    return start


def test_the_librarian_archives_the_evening_s_participant_oi_only_under_dryrun(rehearsing):
    from fno.storage.librarian import fill_report_lines
    from fno.storage.wiring import build_librarian

    real, checkout, clock = rehearsing(OI_DAY)
    report = build_librarian("participant-oi", log=lambda line: None).fill(OI_DAY, OI_DAY)
    assert report.uploaded == [OI_DAY], fill_report_lines(report)
    assert clock() == ist(OI_DAY, 19, 55, 29)  # served at the row's commit, not before
    assert real.writes == [f"dryrun/r1/raw/{OI_PATH}"]
    assert real.files[f"raw/{OI_PATH}"] == OI  # the real record only read
    assert OI_SHA in (checkout / "participant-oi.csv").read_text()  # the row in the rehearsal's checkout


def test_the_by_session_taker_after_the_commit_is_served_the_day_s_copy_only_under_dryrun(rehearsing):
    from fno.storage.snapshot_taker import ALREADY
    from fno.storage.wiring import build_snapshot_taker

    real, checkout, clock = rehearsing(FLOWS_DAY)
    clock.at = ist(FLOWS_DAY, 19, 56, 40)  # commit + 61 s: a fetch-first read
    taker = build_snapshot_taker("fii-dii-cash-by-session")
    assert taker.source.session.get(FLOWS_URL).content == FLOWS  # the session serves the day's copy, no wait
    assert clock() == ist(FLOWS_DAY, 19, 56, 40)
    # the record already shows the file at this time (REH1g), so the taker keeps it: the accepted "already" line
    assert taker.take(FLOWS_DAY) == ALREADY.format(path=FLOWS_PATH)
    assert real.writes == [f"dryrun/r1/raw/{FLOWS_PATH}"]
    assert real.files[f"dryrun/r1/raw/{FLOWS_PATH}"] == FLOWS
    assert FLOWS_SHA in (checkout / "fii-dii-cash-by-session.csv").read_text()


def test_the_guard_lists_the_recorded_archive_session(rehearsing):
    rehearsing(OI_DAY)
    build, forms = builders()["NSE's archive session"]
    assert forms == (RecordedArchiveSession,)
    assert isinstance(build(), RecordedArchiveSession)


def test_outside_the_mode_the_nse_source_s_session_is_the_paced_one(monkeypatch):
    from fno.storage.wiring import build_nse_source

    monkeypatch.delenv(ENV_FNO_REHEARSAL, raising=False)
    assert type(build_nse_source(NseDailyFoSource).session).__name__ == "PacedSession"


def test_the_a9_index_carries_each_row_s_dataset_day_and_sha256(tmp_path):
    rows = ManifestRows(record(tmp_path)).archived(FLOWS_URL)
    committed = ist(FLOWS_DAY, 19, 55, 39).astimezone(UTC)
    assert rows == [A9Row(committed, "fii-dii-cash-by-session", FLOWS_DAY, FLOWS_URL, FLOWS_SHA)]
    assert ManifestRows(tmp_path / "record").archived("https://www.nseindia.com/") == []
