"""Story E2b criteria 4 and 5: E3's 15:15 capture commits its record and the sidecar, never the quote file, and every
commit of the desk's committer passes the raw-quote guard first (before git runs)."""

import json
import subprocess
from datetime import datetime

import pytest

from fno.desk.commit_guard import RawQuoteCommitRefused, RawQuoteGuard
from fno.desk.daily_ports import Committer
from fno.desk.execution_capture import RecorderExecutionCapture
from fno.desk.git_sync import QUOTES_FOLDER_IN_REPOSITORY, Git, GitCommitter
from fno.models import IST
from fno.quotes.recorder import DATASET
from fno.storage.raw_store import LocalFolderStore
from fno.storage.wiring import QUOTES_FOLDER
from tests.timetable.fakes import Capture, Clock

DAY_TIME = datetime(2026, 10, 14, 15, 15, tzinfo=IST)


class Recording(Committer):
    def __init__(self):
        self.paths = []

    def commit(self, paths, message):
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
    body = json.loads(paths[0].read_text(encoding="utf-8")) if paths[0].suffix == ".json" else {}
    assert {"csv_sha256", "meta_sha256"} <= set(body) and captured.csv_sha256 == body["csv_sha256"]


def guard(tmp_path):
    (tmp_path / "research/data/quotes" / DATASET / "2026/10").mkdir(parents=True)
    return RawQuoteGuard(tmp_path, tmp_path / "research/data/quotes")


QUOTE = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261014_151500.csv"


DOTTED = "journal/../research/data/quotes/groww/derivatives/quote-snapshots/2026/10/x.csv"
CANONICAL = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10/nifty_20261014.canonical"
NSE_CSV = "research/data/quotes/nse/derivatives/quote-snapshots/2026/10/x.csv"


@pytest.mark.parametrize("path", [QUOTE, QUOTE.replace(".csv", ".CSV"), DOTTED])
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

    with pytest.raises(RawQuoteCommitRefused):
        GitCommitter(SpyGit(tmp_path)).commit([tmp_path / QUOTE], "Execution capture")
    assert calls == []  # not even the pull


def test_the_committers_quote_folder_is_the_app_s():
    assert QUOTES_FOLDER.relative_to(QUOTES_FOLDER.parents[2]) == QUOTES_FOLDER_IN_REPOSITORY
