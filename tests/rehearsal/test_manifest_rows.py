"""REH1g (DRY2's gap G2): a Drive file whose record is a manifest row, not an O9 receipt (A9's librarian datasets,
the global cues), is visible once the commit that added its row is at or before the replay clock: never before (no
look-ahead); a row not on the record's main (only in the working tree, or on a branch) never counts; a row merged into
main counts from its merge; the same URL archived on two days is two files; a path outside the raw area never
matches."""

import os
import subprocess
from datetime import UTC, datetime, timedelta

from fno.rehearsal.manifest_rows import MANIFESTS, ManifestRows
from fno.rehearsal.visibility import Visibility
from fno.storage.receipts import ReceiptFolder

INDEX_CLOSE = "raw/nse/indices/index-close/2026/10/ind_close_all_16102026.csv"
SP500 = "raw/cboe/indices/spx-history/2026/10/23/060620_spx-history.json"
BAN = "raw/nse/derivatives/fo-ban-list/2026/10/{day}/fo_secban.csv"
BAN_URL = "https://nsearchives.nseindia.com/content/fo/fo_secban.csv"


def git(repo, *args, when=None, authored=None):
    """`authored`: an author date other than `when` (a rebased or cherry-picked commit keeps its older one)."""
    env = {"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": authored or when} if when else {}
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
    ban = repo / MANIFESTS / "fo-ban-list.csv"
    ban.write_text(f"date,url,status,sha256,size_bytes\n2026-10-22,{BAN_URL},200,a1,74\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "ban 22", when="2026-10-21T13:00:00+00:00")
    with ban.open("a") as rows:
        rows.write(f"2026-10-23,{BAN_URL},200,c2,74\n")
    git(repo, "commit", "-q", "-am", "ban 23", when="2026-10-22T13:00:00+00:00")
    publish(repo)
    return repo, index


def publish(repo):
    """The record checkout's view of main is its `origin/main`."""
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")


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


def test_a_row_committed_only_on_a_branch_never_counts(tmp_path):
    repo, index = record(tmp_path)
    git(repo, "checkout", "-q", "-b", "story")
    with index.open("a") as rows:
        rows.write("2026-10-19,https://nsearchives.nseindia.com/content/indices/ind_close_all_19102026.csv,200,ef,1\n")
    git(repo, "commit", "-q", "-am", "on a branch", when="2026-10-19T19:00:00+00:00")
    branch_only = ManifestRows(repo).seen_at("raw/nse/indices/index-close/2026/10/ind_close_all_19102026.csv")
    assert branch_only is None  # HEAD has the row; the record's main does not


def test_a_merged_row_counts_from_its_merge_into_main(tmp_path):
    repo, index = record(tmp_path)
    git(repo, "checkout", "-q", "-b", "story")
    with index.open("a") as rows:
        rows.write("2026-10-19,https://nsearchives.nseindia.com/content/indices/ind_close_all_19102026.csv,200,ef,1\n")
    git(repo, "commit", "-q", "-am", "on a branch", when="2026-10-19T19:00:00+00:00")
    git(repo, "checkout", "-q", "-")
    git(repo, "merge", "-q", "--no-ff", "-m", "merge", "story", when="2026-10-20T08:00:00+00:00")
    publish(repo)
    seen = ManifestRows(repo).seen_at("raw/nse/indices/index-close/2026/10/ind_close_all_19102026.csv")
    assert seen == datetime(2026, 10, 20, 8, tzinfo=UTC)  # when main held it, not when the branch wrote it


def test_the_same_url_archived_on_two_days_is_two_files(tmp_path):
    """The review's look-ahead: fo_secban.csv is the same URL every day; the 23 Oct copy waits for its own row."""
    repo, _ = record(tmp_path)
    rows = ManifestRows(repo)
    assert rows.seen_at(BAN.format(day=22)) == datetime(2026, 10, 21, 13, tzinfo=UTC)
    assert rows.seen_at(BAN.format(day=23)) == datetime(2026, 10, 22, 13, tzinfo=UTC)
    assert not visibility(repo, datetime(2026, 10, 22, 12, tzinfo=UTC))(BAN.format(day=23))
    assert rows.seen_at(BAN.format(day=26)) is None


def test_a_path_outside_the_raw_area_never_matches_a_row(tmp_path):
    repo, _ = record(tmp_path)
    rows = ManifestRows(repo)
    for elsewhere in ("processed/" + SP500.removeprefix("raw/"), "dryrun/r/" + SP500, SP500.removeprefix("raw/")):
        assert rows.seen_at(elsewhere) is None


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


def test_a_row_is_visible_at_its_commit_s_exact_second_and_not_a_microsecond_before(tmp_path):
    repo, _ = record(tmp_path)
    committed = datetime(2026, 10, 16, 19, 1, 48, tzinfo=UTC)
    assert visibility(repo, committed)(INDEX_CLOSE)
    assert not visibility(repo, committed.replace(microsecond=0) - timedelta(microseconds=1))(INDEX_CLOSE)


def test_a_record_with_no_manifests_shows_nothing(tmp_path):
    assert ManifestRows(tmp_path).seen_at(INDEX_CLOSE) is None
    assert not visibility(tmp_path, datetime(2026, 12, 1, tzinfo=UTC))(INDEX_CLOSE)
