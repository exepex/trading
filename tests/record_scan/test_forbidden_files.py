"""Story A4b: the public-record scan refuses a raw Groww quote file by its path, whatever it holds, even when it is
added past `.gitignore` with `git add -f`; sidecars, markers and NSE's public chain still commit."""

from fno.record_scan.forbidden_files import MOVED_VIX_FILES, RAW_GROWW_QUOTES
from tests.record_scan.test_routine_gate import git, repo  # noqa: F401 - the routine checkout fixture

GROWW = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10/"


def _stage(repo, path, text="snapshot_id,bid\n1,10\n"):  # noqa: F811
    (repo / path).parent.mkdir(parents=True, exist_ok=True)
    (repo / path).write_text(text)
    assert git(repo, "add", "-f", path).returncode == 0


def test_a_force_added_groww_quote_file_is_refused(repo):  # noqa: F811
    _stage(repo, f"{GROWW}nifty_20261015_145500.csv")
    commit = git(repo, "commit", "-q", "-m", "routine records")
    assert commit.returncode != 0
    assert f"{GROWW}nifty_20261015_145500.csv:0: raw Groww quote file" in commit.stderr
    assert git(repo, "rev-parse", "HEAD").returncode != 0


def test_sidecars_markers_and_nse_files_commit(repo):  # noqa: F811
    _stage(repo, f"{GROWW}nifty_20261015_145500.meta.json", "{}\n")
    _stage(repo, f"{GROWW}nifty_20261015.canonical", "nifty_20261015_145500\n")
    _stage(repo, "research/data/quotes/nse/derivatives/quote-snapshots/2026/10/nifty_20261015_145500.csv")
    _stage(repo, "tests/fixtures/x/groww/derivatives/quote-snapshots/2026/10/a.csv")  # synthetic fixtures elsewhere
    assert git(repo, "commit", "-q", "-m", "routine records").returncode == 0


def test_the_path_rule_boundaries():
    assert RAW_GROWW_QUOTES.matches(f"{GROWW}a.csv") and RAW_GROWW_QUOTES.matches(f"{GROWW}A.CSV")
    assert not RAW_GROWW_QUOTES.matches(f"{GROWW}a.meta.json")
    assert not RAW_GROWW_QUOTES.matches(f"x/{GROWW}a.csv")
    assert not RAW_GROWW_QUOTES.matches("research/data/quotes/groww.csv")


def test_a_force_added_vix_file_moved_to_drive_is_refused_and_its_readme_commits(repo):  # noqa: F811
    """O9b: the VIX table and checks live in Drive; a copy added back past `.gitignore` is refused by path."""
    _stage(repo, "research/data/vix/checks/gaps.csv", "date,kind\n")
    commit = git(repo, "commit", "-q", "-m", "data")
    assert (
        commit.returncode != 0 and "research/data/vix/checks/gaps.csv:0: India VIX data moved to Drive" in commit.stderr
    )
    git(repo, "rm", "-q", "--cached", "research/data/vix/checks/gaps.csv")
    _stage(repo, "research/data/vix/README.md", "# India VIX\n")
    assert git(repo, "commit", "-q", "-m", "docs").returncode == 0
    assert MOVED_VIX_FILES.matches("research/data/vix/india_vix_daily.csv")
    assert not MOVED_VIX_FILES.matches("receipts/data/vix/india_vix_daily/x.csv.sha256")
