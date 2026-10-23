"""Tests' git never calls the machine's signing program (orchestrator, 23 Oct 2026): a test repository's commit is
unsigned, and keeps the machine's identity settings."""

import subprocess


def test_a_test_repositorys_commit_is_not_signed(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True).stdout

    git("init", "-q")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "test")
    (tmp_path / "a.txt").write_text("a\n")
    git("add", "a.txt")
    git("commit", "-qm", "one")
    assert "gpgsig" not in git("cat-file", "-p", "HEAD")
    assert git("config", "--get", "commit.gpgsign").strip() == "false"
