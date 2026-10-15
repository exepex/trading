"""Story O1, criteria 4 and 4a with real git (judge 169 addendum 1, note 2): each quote part's commit holds exactly its
own files (A4c's paths), never a Groww raw quote file, and never a file another writer staged; and a real child
command's exit code and lines."""

import shutil
import subprocess
import time

from fno.config import ROOT
from fno.daily.processes import ChildProcesses
from fno.daily.quote_parts import QUOTE_PARTS
from fno.daily.steps import wait
from fno.desk.git_sync import Git

GROWW = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10"
NSE = "research/data/quotes/nse/derivatives/quote-snapshots/2026/10"
OWN = {
    "nifty": [f"{GROWW}/nifty_20261016.canonical", f"{GROWW}/nifty_20261016_145500.meta.json"],
    "nse": [f"{NSE}/nifty_20261016{suffix}" for suffix in (".canonical", "_145501.csv", "_145501.meta.json")],
    "indices": [f"{GROWW}/{name}_20261016{suffix}" for name in ("banknifty", "finnifty", "midcpnifty")
                for suffix in (".canonical", "_150100.meta.json")],
}  # fmt: skip
RAW = [f"{GROWW}/{name}_20261016_145500.csv" for name in ("nifty", "banknifty")]
OTHER = "research/notes/another_writer.md"  # a tracked file another writer staged


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def test_each_part_commits_only_its_own_files_with_another_file_staged(tmp_path):
    git(tmp_path, "init", "-q")
    for key, value in (("user.email", "t@example.org"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
        git(tmp_path, "config", key, value)
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")
    for path in [*sum(OWN.values(), []), *RAW, OTHER]:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("x")
    git(tmp_path, "add", ".gitignore", OTHER)  # another writer's staged file
    repo = Git(tmp_path)
    for part in QUOTE_PARTS:
        files = repo.changed(part.pathspecs)
        assert sorted(repo.relative(f) for f in files) == sorted(OWN[part.name])  # no raw file, no other part's
        assert repo.commit_paths(files, f"3 pm quotes {part.name}")
        assert sorted(git(tmp_path, "show", "--name-only", "--format=", "HEAD").split()) == sorted(OWN[part.name])
    assert git(tmp_path, "diff", "--cached", "--name-only").split() == [".gitignore", OTHER]  # still staged, untouched
    assert repo.changed(QUOTE_PARTS[0].pathspecs) == []  # committed: nothing left for NIFTY


def test_a_real_child_command_gives_its_exit_code_and_last_lines():
    process = ChildProcesses(ROOT).start(["daily", "--help"])
    assert wait(process, sleep=lambda seconds: time.sleep(0.05)) == 0
    assert any("daily" in line for line in process.lines())
