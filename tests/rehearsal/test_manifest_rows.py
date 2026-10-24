"""REH1g (DRY2's gap G2): a Drive file whose record is a manifest row, not an O9 receipt (A9's librarian datasets,
the global cues), is visible once the commit that added its row is at or before the replay clock: never before (no
look-ahead), and a row not committed yet never counts."""

import os
import subprocess
from datetime import UTC, datetime

from fno.rehearsal.manifest_rows import MANIFESTS, ManifestRows
from fno.rehearsal.visibility import Visibility
from fno.storage.receipts import ReceiptFolder

INDEX_CLOSE = "raw/nse/indices/index-close/2026/10/ind_close_all_16102026.csv"
SP500 = "raw/cboe/indices/spx-history/2026/10/23/060620_spx-history.json"


def git(repo, *args, when=None):
    env = {"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when} if when else {}
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env={**os.environ, **env})


def record(tmp_path):
    repo = tmp_path / "record"
    (repo / MANIFESTS / "global-cues").mkdir(parents=True)
    git(repo, "init", "-q")
    for key, value in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(repo, "config", key, value)
    index = repo / MANIFESTS / "index-close.csv"
    index.write_text("date,url,status,sha256,size_bytes\n")
    cues = repo / MANIFESTS / "global-cues" / "sp500.csv"
    cues.write_text("fetched_at,path,url,form,sha256,size_bytes\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "headers", when="2026-10-01T00:00:00+00:00")
    with index.open("a") as rows:
        rows.write("2026-10-16,https://nsearchives.nseindia.com/content/indices/ind_close_all_16102026.csv,200,ab,1\n")
    git(repo, "commit", "-q", "-am", "16 Oct close", when="2026-10-16T19:01:48+00:00")
    with cues.open("a") as rows:
        rows.write("2026-10-23T06:06:20+05:30,cboe/indices/spx-history/2026/10/23/060620_spx-history.json,u,,cd,1\n")
    git(repo, "commit", "-q", "-am", "S&P", when="2026-10-23T00:42:24+00:00")
    return repo, index


def visibility(repo, at):
    return Visibility(ReceiptFolder(repo / "receipts"), lambda: at, ManifestRows(repo))


def test_the_16_oct_index_close_and_the_s_p_cue_are_visible_from_their_row_s_commit(tmp_path):
    repo, _ = record(tmp_path)
    rows = ManifestRows(repo)
    assert rows.seen_at(INDEX_CLOSE) == datetime(2026, 10, 16, 19, 1, 48, tzinfo=UTC)
    assert rows.seen_at(SP500) == datetime(2026, 10, 23, 0, 42, 24, tzinfo=UTC)
    assert visibility(repo, datetime(2026, 10, 23, 3, 8, tzinfo=UTC))(INDEX_CLOSE)  # 08:38 IST on 23 Oct
    assert visibility(repo, datetime(2026, 10, 23, 3, 8, tzinfo=UTC))(SP500)


def test_a_row_committed_after_the_replay_time_stays_invisible(tmp_path):
    repo, _ = record(tmp_path)
    assert not visibility(repo, datetime(2026, 10, 16, 19, 1, 47, tzinfo=UTC))(INDEX_CLOSE)
    assert not visibility(repo, datetime(2026, 10, 23, 0, 42, 23, tzinfo=UTC))(SP500)


def test_an_uncommitted_row_and_a_file_with_no_row_never_count(tmp_path):
    repo, index = record(tmp_path)
    with index.open("a") as rows:
        rows.write("2026-10-19,https://nsearchives.nseindia.com/content/indices/ind_close_all_19102026.csv,200,ef,1\n")
    later = visibility(repo, datetime(2026, 12, 1, tzinfo=UTC))
    assert not later("raw/nse/indices/index-close/2026/10/ind_close_all_19102026.csv")
    assert not later("raw/nse/indices/index-close/2026/10/ind_close_all_20102026.csv")
    assert not later("raw/elsewhere/ind_close_all_16102026.csv")  # the file's name in another dataset's folder


def test_the_rehearsal_s_drive_reads_the_record_s_manifest_rows(tmp_path):
    from datetime import date

    from fno.constants import ENV_FNO_REHEARSAL
    from fno.rehearsal.drive_wiring import rehearsed_drive
    from fno.rehearsal.mode import Rehearsal

    from .fakes import RecordingDrive

    repo, _ = record(tmp_path)
    env = {ENV_FNO_REHEARSAL: Rehearsal(date(2026, 10, 23), "r", tmp_path / "state", repo).to_env()}
    drive = rehearsed_drive(RecordingDrive({INDEX_CLOSE: b"close"}), env)
    assert drive.get(INDEX_CLOSE) == b"close"  # the replay clock (now) is past the row's commit
