"""Story E2b criteria 4 and 5: E3's 15:15 capture commits its record and the sidecar, never the quote file, and every
commit of the desk's committer passes the raw-quote guard first (before git runs)."""

import json
import subprocess
from datetime import datetime

import pytest

from fno.desk.commit_guard import RawQuoteCommitRefused, RawQuoteGuard
from fno.desk.daily_ports import CommitFailed, Committer
from fno.desk.execution_capture import RecorderExecutionCapture
from fno.desk.git_sync import Git, GitCommitter
from fno.models import IST
from fno.quotes.recorder import DATASET
from fno.storage.raw_store import LocalFolderStore
from tests.timetable.fakes import Capture, Clock

DAY_TIME = datetime(2026, 10, 14, 15, 15, tzinfo=IST)


class Recording(Committer):
    def __init__(self):
        self.paths = []

    def commit(self, paths, message, own_unpushed=None):
        self.paths.append(list(paths))
        return "c1"


def test_the_capture_commits_its_record_and_sidecar_never_the_quote_file(tmp_path):
    clock, quotes, committer = Clock(), LocalFolderStore(tmp_path / "quotes"), Recording()
    clock.until(DAY_TIME)
    record = RecorderExecutionCapture(Capture(clock, quotes), quotes, tmp_path / "quotes", tmp_path, committer)
    captured = record.capture(DAY_TIME.date())
    [paths] = committer.paths
    names = sorted(p.name for p in paths)
    assert names == [f"{captured.snapshot_id}.json", f"{captured.snapshot_id}.meta.json"]
    assert not any(p.suffix == ".csv" for p in paths)
    [record_path] = [p for p in paths if p.name == f"{captured.snapshot_id}.json"]
    body = json.loads(record_path.read_text(encoding="utf-8"))
    assert {"csv_sha256", "meta_sha256"} <= set(body) and captured.csv_sha256 == body["csv_sha256"]


def guard(tmp_path):
    (tmp_path / "research/data/quotes" / DATASET / "2026/10").mkdir(parents=True)
    return RawQuoteGuard(tmp_path, tmp_path / "research/data/quotes")


QUOTE = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261014_151500.csv"


DOTTED = "journal/../research/data/quotes/groww/derivatives/quote-snapshots/2026/10/x.csv"
CANONICAL = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261014.canonical"
NSE_CSV = "research/data/quotes/nse/derivatives/quote-snapshots/2026/10/x.csv"


V4_QUOTE = QUOTE.replace("quote-snapshots/", "quote-snapshots-v4/")  # A4e: a named window's own dataset


@pytest.mark.parametrize("path", [QUOTE, QUOTE.replace(".csv", ".CSV"), DOTTED, V4_QUOTE])
def test_a_raw_quote_path_is_refused_naming_it(tmp_path, path):
    with pytest.raises(RawQuoteCommitRefused, match="would publish raw Groww quotes"):
        guard(tmp_path).check([tmp_path / "journal/runs/2026-10-14.json", tmp_path / path])


def test_a_symlink_pointing_into_the_quote_folder_is_refused(tmp_path):
    check = guard(tmp_path)
    target = tmp_path / QUOTE
    target.write_text("contract_id,bid,ask\n", encoding="utf-8")
    (tmp_path / "journal").mkdir()
    link = tmp_path / "journal" / "innocent.csv"
    link.symlink_to(target)
    with pytest.raises(RawQuoteCommitRefused, match="innocent.csv"):
        check.check([link])


@pytest.mark.parametrize(
    "paths", [[], [QUOTE.replace(".csv", ".meta.json")], [CANONICAL], ["journal/x/account/desk_fills.csv"], [NSE_CSV]]
)
def test_sidecars_markers_other_csvs_and_an_empty_list_pass(tmp_path, paths):
    guard(tmp_path).check([tmp_path / p for p in paths])


def test_the_committer_refuses_before_git_runs(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    calls = []

    class SpyGit(Git):
        def __call__(self, *args, **kwargs):
            calls.append(args)
            return super().__call__(*args, **kwargs)

    with pytest.raises(CommitFailed, match="would publish raw Groww quotes"):
        GitCommitter(SpyGit(tmp_path)).commit([tmp_path / QUOTE], "Execution capture")
    assert calls == []  # not even the pull


def git_repo(tmp_path):
    origin, work = tmp_path / "origin.git", tmp_path / "work"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True, capture_output=True)
    for key, value in (("user.email", "t@example.org"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
        subprocess.run(["git", "-C", str(work), "config", key, value], check=True)
    (work / QUOTE).parent.mkdir(parents=True)
    (work / QUOTE).write_text("contract_id,bid,ask\n", encoding="utf-8")
    (work / QUOTE.replace(".csv", ".meta.json")).write_text("{}\n", encoding="utf-8")
    return Git(work)


def committed(git):
    """The files in the last commit (none before the first commit)."""
    return git("ls-tree", "-r", "--name-only", "HEAD", check=False).stdout.split()


@pytest.mark.parametrize("given", ["research/data/quotes", "research/data/quotes/", "research"])
def test_a_folder_or_pathspec_holding_a_quote_file_is_refused_after_the_add(tmp_path, given):
    """Review B1: the guard checks what the add staged, not only the given names."""
    git = git_repo(tmp_path)
    with pytest.raises(RawQuoteCommitRefused):
        git.commit_paths([git.root / given], "a folder holding a quote file")
    assert committed(git) == [] and git("diff", "--cached", "--name-only").stdout == ""


def test_a_quote_file_staged_earlier_is_never_swept_into_a_desk_commit(tmp_path):
    """Review B2: `git commit` takes the whole index, so an earlier staged quote file is caught too."""
    git = git_repo(tmp_path)
    git("add", "--", QUOTE)
    with pytest.raises(RawQuoteCommitRefused, match="nifty_20261014_151500.csv"):
        git.commit_paths([git.root / QUOTE.replace(".csv", ".meta.json")], "sidecar only")
    assert committed(git) == []  # nothing committed; the earlier staged file stays staged, so it refuses again
    assert git("diff", "--cached", "--name-only").stdout.split() == [QUOTE]


def test_a_sidecar_alone_is_committed(tmp_path):
    git = git_repo(tmp_path)
    assert git.commit_paths([git.root / QUOTE.replace(".csv", ".meta.json")], "sidecar only")
    assert committed(git) == [QUOTE.replace(".csv", ".meta.json")]


def test_a_staged_deletion_of_a_quote_file_is_refused(tmp_path):
    """Judge 118 addendum 3 minor 1 (plant N4): removing a committed quote file is a change to the public record too."""
    git = git_repo(tmp_path)
    git("add", "--", QUOTE)
    git("commit", "-q", "-m", "a quote file committed before the guard")
    git("rm", "-q", "--cached", "--", QUOTE)
    with pytest.raises(RawQuoteCommitRefused, match="nifty_20261014_151500.csv"):
        git.commit_paths([git.root / QUOTE.replace(".csv", ".meta.json")], "sidecar only")
    assert committed(git) == [QUOTE]  # the deletion was not committed
