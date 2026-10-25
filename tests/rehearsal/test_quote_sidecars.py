"""REH1p (the school's 23 Oct morning rehearsal saw every road `capture_missing`): a Groww raw quote file, vouched for
by its committed sidecar (A4b) and by no receipt or manifest row, is visible to a rehearsal once the replay clock has
reached both its attempt's `finished_at` and its sidecar's first-parent commit on main, the later of the two (P1, P2);
a failed save, a sidecar not on main, and any other file never count (P3); through the rehearsed Drive the previous
day's file is read and a same-day one before its time is not (P4); a real run is unchanged (P5)."""

import json
import os
import subprocess
from datetime import UTC, datetime, timedelta

from fno.rehearsal.drive import DryrunDrive
from fno.rehearsal.quote_sidecars import QUOTES, QuoteSidecars
from fno.rehearsal.visibility import Visibility
from fno.storage.receipts import ReceiptFolder

from .fakes import RecordingDrive

MONTH = "groww/derivatives/quote-snapshots/2026/10"
B22, B23 = f"{MONTH}/banknifty_20261022_150146", f"{MONTH}/banknifty_20261023_150121"
FINISHED_22 = datetime(2026, 10, 22, 9, 33, 36, tzinfo=UTC)  # 15:03:36 IST
COMMITTED_22 = datetime(2026, 10, 22, 9, 44, 16, tzinfo=UTC)  # the real record's commit of that sidecar


def git(repo, *args, when=None):
    env = {"GIT_COMMITTER_DATE": when.isoformat(), "GIT_AUTHOR_DATE": when.isoformat()} if when else {}
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env={**os.environ, **env})


def sidecar(repo, stem, finished, saved=True):
    path = repo / QUOTES / f"{stem}.meta.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {"finished_at": finished.isoformat(), "csv_sha256": "ab"} | ({} if saved else {"raw_file_saved": False})
    path.write_text(json.dumps(meta))


def commit(repo, message, when):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message, when=when)
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")  # the record checkout's view of main


def record(tmp_path):
    repo = tmp_path / "record"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for key, value in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(repo, "config", key, value)
    sidecar(repo, B22, FINISHED_22)
    commit(repo, "22 Oct banknifty", COMMITTED_22)
    return repo


def raw(stem):
    return f"raw/{stem}.csv"


def seen(repo, stem, at):
    return Visibility(ReceiptFolder(repo / "receipts"), lambda: at, None, QuoteSidecars(repo))(raw(stem))


# P1 and P2: the later of the finish and the commit


def test_the_previous_day_s_file_is_visible_the_next_morning(tmp_path):
    repo = record(tmp_path)
    assert QuoteSidecars(repo).seen_at(raw(B22)) == COMMITTED_22
    assert seen(repo, B22, datetime(2026, 10, 23, 3, 8, tzinfo=UTC))  # 08:38 IST on 23 Oct


def test_between_its_finish_and_its_commit_a_file_is_not_yet_visible(tmp_path):
    """The orchestrator's ask: a sidecar committed later than its `finished_at` never shows the file early."""
    repo = record(tmp_path)
    assert not seen(repo, B22, FINISHED_22 + timedelta(minutes=5))
    assert not seen(repo, B22, COMMITTED_22 - timedelta(seconds=1))
    assert seen(repo, B22, COMMITTED_22)  # the boundary: at the later time itself


def test_a_sidecar_committed_before_its_finish_waits_for_the_finish(tmp_path):
    repo = record(tmp_path)
    finished = datetime(2026, 10, 23, 9, 40, tzinfo=UTC)
    sidecar(repo, B23, finished)
    commit(repo, "23 Oct, dated early", datetime(2026, 10, 23, 9, 35, tzinfo=UTC))
    assert not seen(repo, B23, finished - timedelta(seconds=1)) and seen(repo, B23, finished)


# P3: what never counts


def test_a_failed_save_a_sidecar_off_main_and_a_file_with_no_sidecar_never_count(tmp_path):
    repo = record(tmp_path)
    late = datetime(2026, 10, 25, tzinfo=UTC)
    sidecar(repo, B23, datetime(2026, 10, 23, 9, 33, tzinfo=UTC), saved=False)
    commit(repo, "failed save", datetime(2026, 10, 23, 9, 44, tzinfo=UTC))
    assert not seen(repo, B23, late)
    assert not seen(repo, f"{MONTH}/midcpnifty_20261023_150400", late)  # no sidecar at all
    assert QuoteSidecars(repo).seen_at(f"data/{B22}.csv") is None  # outside the raw area
    assert QuoteSidecars(repo).seen_at(f"raw/{B22}.meta.json") is None  # not a quote file


def test_a_sidecar_committed_only_on_a_branch_never_counts(tmp_path):
    repo = record(tmp_path)
    git(repo, "checkout", "-q", "-b", "side")
    sidecar(repo, B23, datetime(2026, 10, 23, 9, 33, tzinfo=UTC))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "on a branch", when=datetime(2026, 10, 23, 9, 50, tzinfo=UTC))
    assert not seen(repo, B23, datetime(2026, 10, 25, tzinfo=UTC))  # committed and on disk, but not on main


def test_a_sidecar_merged_into_main_counts_from_the_merge(tmp_path):
    repo = record(tmp_path)
    git(repo, "checkout", "-q", "-b", "side")
    sidecar(repo, B23, datetime(2026, 10, 23, 9, 33, tzinfo=UTC))
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "on a branch", when=datetime(2026, 10, 23, 9, 40, tzinfo=UTC))
    git(repo, "checkout", "-q", "main")
    merged = datetime(2026, 10, 23, 10, 0, tzinfo=UTC)
    git(repo, "merge", "-q", "--no-ff", "-m", "merge", "side", when=merged)
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    assert QuoteSidecars(repo).seen_at(raw(B23)) == merged


# P4: through the rehearsed Drive


def test_the_rehearsed_drive_reads_the_previous_day_s_file_and_not_a_same_day_one_before_its_time(tmp_path):
    repo = record(tmp_path)
    sidecar(repo, B23, datetime(2026, 10, 23, 9, 33, 21, tzinfo=UTC))
    commit(repo, "23 Oct banknifty", datetime(2026, 10, 23, 9, 44, tzinfo=UTC))
    real = RecordingDrive({raw(B22): b"22 Oct rows", raw(B23): b"23 Oct rows"})
    at = {"now": datetime(2026, 10, 23, 3, 10, tzinfo=UTC)}  # 08:40 IST on 23 Oct
    visible = Visibility(ReceiptFolder(repo / "receipts"), lambda: at["now"], None, QuoteSidecars(repo))
    store = DryrunDrive(real, "dryrun/r1", visible)
    assert store.get(raw(B22)) == b"22 Oct rows" and store.get(raw(B23)) is None
    at["now"] = datetime(2026, 10, 23, 9, 44, tzinfo=UTC)
    assert store.get(raw(B23)) == b"23 Oct rows"


# P5: a real run is unchanged


def test_with_no_mode_the_owner_drive_is_returned_as_it_is():
    from fno.rehearsal.drive_wiring import rehearsed_drive

    real = RecordingDrive({})
    assert rehearsed_drive(real, {}) is real


def test_under_the_mode_the_owner_drive_sees_the_record_s_quote_sidecars(monkeypatch, tmp_path):
    from datetime import date

    from fno.constants import ENV_FNO_REHEARSAL
    from fno.rehearsal.drive_wiring import rehearsed_drive
    from fno.rehearsal.mode import Rehearsal

    repo = record(tmp_path)
    env = {ENV_FNO_REHEARSAL: Rehearsal.new(date(2026, 10, 23), tmp_path / "home", repo).to_env()}
    monkeypatch.setattr("fno.rehearsal.drive_wiring.now_utc", lambda: datetime(2026, 10, 23, 3, 10, tzinfo=UTC))
    store = rehearsed_drive(RecordingDrive({raw(B22): b"22 Oct rows"}), env)
    assert store.get(raw(B22)) == b"22 Oct rows"


def test_the_sidecar_is_read_as_main_holds_it_never_from_the_working_tree(tmp_path):
    """Self-review: the record checkout may be on any branch; a sidecar gone from its working tree, or edited there,
    neither crashes the read nor changes what main recorded."""
    repo = record(tmp_path)
    path = repo / QUOTES / f"{B22}.meta.json"
    path.write_text(json.dumps({"finished_at": "2026-10-25T00:00:00+00:00", "raw_file_saved": False}))
    assert QuoteSidecars(repo).seen_at(raw(B22)) == COMMITTED_22  # the edit is ignored
    path.unlink()
    assert seen(repo, B22, datetime(2026, 10, 23, 3, 8, tzinfo=UTC))  # and so is its absence


def test_a_weekly_file_counts_and_a_non_groww_file_with_a_matching_sidecar_does_not(tmp_path):
    repo = tmp_path / "record"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    for key, value in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(repo, "config", key, value)
    weekly = "groww/derivatives/quote-snapshots-weekly/2026/10/niftyweekly_20261022_150613"
    nse = "nse/derivatives/quote-snapshots/2026/10/nifty_20261022_145500"
    for stem in (weekly, nse):
        sidecar(repo, stem, FINISHED_22)
    commit(repo, "both", COMMITTED_22)
    assert QuoteSidecars(repo).seen_at(raw(weekly)) == COMMITTED_22
    assert QuoteSidecars(repo).seen_at(raw(nse)) is None  # NSE's chain is in the repository, never a Drive quote


def test_a_record_with_no_main_shows_nothing(tmp_path):
    repo = tmp_path / "record"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    assert QuoteSidecars(repo).seen_at(raw(B22)) is None
