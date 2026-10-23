"""Protocol section 13 on a temporary repository: a study file off its FREEZE.md hash, an unfrozen file or an
uncommitted change refuses both runs; run 2 also needs a committed, unchanged selection.json and no final.json now or
in any earlier commit."""

import hashlib
import subprocess

import pytest
from edge1study.guard import STUDY, Refused, check_code, check_final_allowed


def git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    for args in (("init", "-q"), ("config", "user.email", "t@t"), ("config", "user.name", "t"),
                 ("config", "core.hooksPath", "/dev/null")):  # fmt: skip
        git(tmp_path, *args)
    study = tmp_path / STUDY
    (study / "edge1study").mkdir(parents=True)
    (study / "study.py").write_text("print('run')\n")
    (study / "edge1study" / "a.py").write_text("A = 1\n")
    rows = [f"| `{p.relative_to(study).as_posix()}` | `{hashlib.sha256(p.read_bytes()).hexdigest()}` |"
            for p in sorted(study.rglob("*.py"))]  # fmt: skip
    (study / "FREEZE.md").write_text("# Freeze\n\n## Analysis code\n\n" + "\n".join(rows) + "\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "freeze")
    return tmp_path


def test_frozen_code_passes_and_any_change_refuses(repo):
    check_code(repo)
    (repo / STUDY / "edge1study/a.py").write_text("A = 2\n")
    with pytest.raises(Refused, match="differs from its FREEZE.md hash"):
        check_code(repo)
    git(repo, "checkout", "-q", "--", ".")
    (repo / STUDY / "edge1study/b.py").write_text("B = 1\n")
    with pytest.raises(Refused, match="without a frozen hash"):
        check_code(repo)
    (repo / STUDY / "edge1study/b.py").unlink()
    (repo / STUDY / "notes.txt").write_text("x\n")
    with pytest.raises(Refused, match="uncommitted changes"):
        check_code(repo)


def test_run_two_needs_a_committed_selection_and_is_read_once(repo):
    with pytest.raises(Refused, match="not committed"):
        check_final_allowed(repo)
    (repo / STUDY / "selection.json").write_text("{}\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "run 1")
    check_final_allowed(repo)
    (repo / STUDY / "selection.json").write_text('{"x": 1}\n')
    with pytest.raises(Refused, match="differs from its commit"):
        check_final_allowed(repo)
    git(repo, "checkout", "-q", "--", ".")
    (repo / STUDY / "final.json").write_text("{}\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "run 2")
    git(repo, "rm", "-q", f"{STUDY}/final.json")
    git(repo, "commit", "-q", "-m", "deleted")
    with pytest.raises(Refused, match="read once"):
        check_final_allowed(repo)
