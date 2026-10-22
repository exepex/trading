"""GR1 protocol section 12 (c)-(d) on a temporary repository: a study file off its FREEZE.md hash, an uncommitted
change, an unfrozen file, a selection.json not committed or changed, and a final.json now or in any earlier commit
each refuse the run."""

import hashlib
import subprocess

import pytest
from gr1study.guard import Refused, check_code, check_final_allowed, frozen_hashes


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@t")
    git(tmp_path, "config", "user.name", "t")
    git(tmp_path, "config", "core.hooksPath", "/dev/null")
    study = tmp_path / "research" / "gr1"
    (study / "gr1study").mkdir(parents=True)
    (study / "study.py").write_text("print('run')\n")
    (study / "gr1study" / "a.py").write_text("A = 1\n")
    freeze(tmp_path)
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "freeze")
    return tmp_path


def freeze(root):
    study = root / "research" / "gr1"
    rows = [f"| `{p.relative_to(study).as_posix()}` | `{hashlib.sha256(p.read_bytes()).hexdigest()}` |"
            for p in sorted(study.rglob("*.py"))]  # fmt: skip
    (study / "FREEZE.md").write_text("# Freeze\n\n| `PROTOCOL.md` | `" + "0" * 64 + "` |\n\n## Analysis code\n\n"
                                     + "\n".join(rows) + "\n")  # fmt: skip


def test_frozen_code_passes_and_the_protocol_row_is_not_read_as_code(repo):
    check_code(repo)
    assert set(frozen_hashes((repo / "research/gr1/FREEZE.md").read_text())) == {"study.py", "gr1study/a.py"}
    with pytest.raises(Refused, match="no frozen analysis code"):
        frozen_hashes("# Freeze\n| `PROTOCOL.md` | `" + "0" * 64 + "` |\n")


def test_a_changed_file_an_unfrozen_one_or_an_uncommitted_change_refuses(repo):
    (repo / "research/gr1/gr1study/a.py").write_text("A = 2\n")
    with pytest.raises(Refused, match="differs from its FREEZE.md hash"):
        check_code(repo)
    git(repo, "checkout", "-q", "--", ".")
    (repo / "research/gr1/gr1study/b.py").write_text("B = 1\n")
    with pytest.raises(Refused, match="without a frozen hash"):
        check_code(repo)
    (repo / "research/gr1/gr1study/b.py").unlink()
    (repo / "research/gr1/notes.txt").write_text("x\n")
    with pytest.raises(Refused, match="uncommitted changes"):
        check_code(repo)


def test_run_2_needs_a_committed_unchanged_selection_and_no_final_ever(repo):
    selection = repo / "research/gr1/selection.json"
    with pytest.raises(Refused, match="not committed"):
        check_final_allowed(repo)
    selection.write_text("{}\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "selection")
    check_final_allowed(repo)
    selection.write_text('{"changed": 1}\n')
    with pytest.raises(Refused, match="differs from its commit"):
        check_final_allowed(repo)
    git(repo, "checkout", "-q", "--", ".")
    final = repo / "research/gr1/final.json"
    final.write_text("{}\n")
    with pytest.raises(Refused, match="read once"):
        check_final_allowed(repo)
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "final")
    git(repo, "rm", "-q", str(final))
    git(repo, "commit", "-q", "-m", "remove the final")
    with pytest.raises(Refused, match="read once"):  # deleted later: still in an earlier commit
        check_final_allowed(repo)
