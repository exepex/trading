"""checks.yml's scope (tools/ci_scope.sh): a push of lane-3 files only skips pytest, ruff and the import check and
scans just its changed files; anything else, or any doubt, runs every check."""

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "ci_scope.sh"
ZEROS = "0" * 40


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def commit(repo: Path, files: dict[str, str | None]) -> str:
    """Writes (or, for None, deletes) the files and commits them; returns the commit."""
    for name, text in files.items():
        path = repo / name
        if text is None:
            git(repo, "rm", "-q", name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        git(repo, "add", name)
    git(repo, "commit", "-q", "-m", "change")
    return git(repo, "rev-parse", "HEAD")


def scope(repo: Path, base: str, head: str) -> tuple[str, list[str]]:
    listed = repo.parent / "changed"
    out = subprocess.run(["sh", str(SCRIPT), base, head, str(listed)], cwd=repo, capture_output=True, text=True)
    files = [p for p in listed.read_text().split("\0") if p] if listed.exists() else []
    return out.stdout.strip(), files


def repository(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "test")
    first = commit(repo, {"fno/a.py": "x = 1\n", "reviews/judge/judge_1.md": "PASS\n"})
    return repo, first


def test_a_log_and_register_push_skips_the_code_checks_and_scans_its_files(tmp_path):
    repo, first = repository(tmp_path)
    head = commit(repo, {"conversations/2026-10-16.md": "log\n", "docs/WORK_REGISTER.md": "| row |\n"})
    assert scope(repo, first, head) == ("code=false", ["conversations/2026-10-16.md", "docs/WORK_REGISTER.md"])


def test_a_code_change_runs_every_check(tmp_path):
    repo, first = repository(tmp_path)
    head = commit(repo, {"conversations/2026-10-16.md": "log\n", "fno/a.py": "x = 2\n"})
    assert scope(repo, first, head)[0] == "code=true"
    assert scope(repo, first, commit(repo, {"docs/JUDGE.md": "rule\n"}))[0] == "code=true"  # a rule document


def test_a_deleted_code_file_counts_and_a_deleted_review_is_not_scanned(tmp_path):
    repo, first = repository(tmp_path)
    assert scope(repo, first, commit(repo, {"fno/a.py": None}))[0] == "code=true"
    repo2, first2 = repository(tmp_path / "second")
    head = commit(repo2, {"reviews/judge/judge_1.md": None, "reviews/judge/judge_2.md": "FAIL\n"})
    assert scope(repo2, first2, head) == ("code=false", ["reviews/judge/judge_2.md"])


def test_any_doubt_runs_every_check(tmp_path):
    repo, first = repository(tmp_path)
    assert scope(repo, ZEROS, first)[0] == "code=true"  # a new branch
    assert scope(repo, "1234567" * 5 + "12345", first)[0] == "code=true"  # a base missing (a force-push)
    assert scope(repo, first, first)[0] == "code=true"  # nothing changed


def test_a_number_claim_is_lane_3_and_the_number_check_runs_on_every_push(tmp_path):
    repo, first = repository(tmp_path)
    head = commit(repo, {"numbers/judge-report.csv": "number,name,session,claimed_at_utc\n"})
    assert scope(repo, first, head) == ("code=false", ["numbers/judge-report.csv"])
    steps = (SCRIPT.parent.parent / ".github" / "workflows" / "checks.yml").read_text()
    assert steps.rstrip().endswith(
        "      - if: always() # story O12: every push, last, so a reused number never stops "
        "the record scan above\n        run: python tools/check_numbers.py"
    )
