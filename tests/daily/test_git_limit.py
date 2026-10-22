"""Story O2, row "Hung git call" (judge 204 addenda 2 and 3): a git call past its hard limit is stopped with its hooks,
its own new lock files are removed and the next call works; a lock that was there before is left, and the error names
it with the hand fix; a stopped push is "not confirmed" and counts as unpushed."""

import subprocess
import time
from pathlib import Path

import pytest

from fno.desk.daily_ports import CommitFailed
from fno.desk.git_limit import GIT_CALL_LIMIT_SECONDS, GitLocks, LimitedRun
from fno.desk.git_sync import Git, GitCallStopped, GitCommitter, GitError, PushNotConfirmed

from .fakes import QuietLocks

LIMIT = 1.0
HOOK_SLEEP = 600
HANGING_HOOK = '#!/bin/sh\necho $$ > "{pid_file}"\nsleep {sleep}\n'
HOOK_START_WAIT = 120.0  # how long a loaded machine may take to reach the hook; a test error past it, never a pass


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def _repo(tmp_path):
    origin, repo = tmp_path / "origin.git", tmp_path / "repo"
    _git(tmp_path, "init", "-q", "--bare", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(repo))
    for key, value in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        _git(repo, "config", key, value)
    (repo / "seed.txt").write_text("seed")
    _git(repo, "add", "seed.txt")
    _git(repo, "commit", "-q", "-m", "seed")
    _git(repo, "push", "-q", "-u", "origin", "HEAD")
    return repo


def _hang_hook(repo, name, tmp_path):
    hooks = tmp_path / f"hooks-{name}"
    hooks.mkdir()
    (hooks / name).write_text(HANGING_HOOK.format(pid_file=tmp_path / f"{name}.pid", sleep=HOOK_SLEEP))
    (hooks / name).chmod(0o755)
    _git(repo, "config", "core.hooksPath", str(hooks))


class HungCallRun(LimitedRun):
    """The test's short limit for the hung call only, counted from the moment its hook runs: it has written its pid,
    so git holds its lock (a commit takes `index.lock` before its hook). Every other call keeps the run's own limit, so
    neither a slow `git add` nor git's own start on a loaded machine can meet the short limit (judge E, 22 Oct: a flake
    in a full parallel run). `calls`: how many calls of `name` hang (None: every one)."""

    def __init__(self, name: str, pid_file: Path, calls: int | None = None):
        super().__init__(QuietLocks, started=self._wait_for_hook)
        self.name, self.pid_file, self.calls, self.hook_at, self.waiting = name, pid_file, calls, None, False

    def __call__(self, command, *, timeout, **options):
        hung = self.waiting = self.name in command and self.calls != 0
        if hung:
            self.pid_file.unlink(missing_ok=True)  # this call's hook writes it afresh
            self.calls = None if self.calls is None else self.calls - 1
        return super().__call__(command, timeout=timeout if hung else GIT_CALL_LIMIT_SECONDS, **options)

    def _wait_for_hook(self, command) -> None:
        if not self.waiting:
            return
        deadline = time.monotonic() + HOOK_START_WAIT
        while not (self.pid_file.is_file() and self.pid_file.read_text().strip()):
            assert time.monotonic() < deadline, f"the {self.name} hook never started"
            time.sleep(0.01)
        self.hook_at = time.monotonic()


def _hung(root, run):
    return Git(root, run=run, limit_seconds=LIMIT)


def _alive(pid):
    """Running, not a zombie waiting for its new parent to reap it."""
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except FileNotFoundError:
        return False
    return state != "Z"


def test_a_commit_hung_in_its_hook_is_stopped_with_the_hook_and_leaves_no_lock(tmp_path):
    repo = _repo(tmp_path)
    _hang_hook(repo, "pre-commit", tmp_path)
    (repo / "a.txt").write_text("a")
    run = HungCallRun("commit", tmp_path / "pre-commit.pid", calls=1)
    git = _hung(repo, run)
    stopped = r"ran past 1 s and was stopped with its hooks; its own lock files removed: .*\.git/index\.lock"
    with pytest.raises(GitCallStopped, match=stopped):
        git.commit_paths([repo / "a.txt"], "a")
    assert time.monotonic() - run.hook_at < HOOK_SLEEP / 20  # stopped by the limit, never the hook's own end
    assert not _alive(int((tmp_path / "pre-commit.pid").read_text()))  # the hook died with its group
    assert QuietLocks(repo).present() == set()
    _git(repo, "config", "--unset", "core.hooksPath")
    assert git.commit_paths([repo / "a.txt"], "a again") is True  # the next commit works


def test_a_lock_that_was_there_before_is_left_and_named_with_the_hand_fix(tmp_path):
    repo = _repo(tmp_path)
    (repo / ".git" / "index.lock").write_text("")
    (repo / "a.txt").write_text("a")
    with pytest.raises(GitError, match=r"index\.lock by hand, then rerun"):
        Git(repo, run=LimitedRun(locks=QuietLocks)).commit_paths([repo / "a.txt"], "a")  # the run's own limit
    assert (repo / ".git" / "index.lock").exists()


def test_a_lock_is_never_removed_while_another_git_process_runs(tmp_path):
    proc = tmp_path / "proc"
    (proc / "4242").mkdir(parents=True)
    (proc / "4242" / "comm").write_text("git\n")
    repo = _repo(tmp_path)
    locks = GitLocks(repo, proc=proc)
    before = locks.present()
    (repo / ".git" / "index.lock").write_text("")
    assert locks.remove_new(before) == [] and (repo / ".git" / "index.lock").exists()
    assert GitLocks(repo, proc=tmp_path / "absent").remove_new(before) == []  # cannot see processes: nothing removed


def test_a_hung_push_is_not_confirmed_and_the_commit_counts_as_unpushed(tmp_path):
    repo = _repo(tmp_path)
    _hang_hook(repo, "pre-push", tmp_path)
    (repo / "a.txt").write_text("a")
    with pytest.raises(CommitFailed, match="push not confirmed: git push -q ran past 1 s") as failed:
        GitCommitter(_hung(repo, HungCallRun("push", tmp_path / "pre-push.pid"))).commit([repo / "a.txt"], "a")
    assert failed.value.unpushed is True
    with pytest.raises(PushNotConfirmed):
        _hung(repo, HungCallRun("push", tmp_path / "pre-push.pid")).push()


def test_every_call_has_the_limit_by_default(tmp_path):
    repo = _repo(tmp_path)
    git = Git(repo)
    assert isinstance(git.run, LimitedRun) and git.limit_seconds == 120.0


def _fake_proc(tmp_path, members: dict[int, tuple[str, int]]) -> Path:
    """A /proc with one `stat` per pid: (state, process group)."""
    proc = tmp_path / "proc"
    for pid, (state, group) in members.items():
        (proc / str(pid)).mkdir(parents=True)
        (proc / str(pid) / "stat").write_text(f"{pid} (sh) {state} 1 {group} {group} 0 -1\n")
    return proc


def test_a_stopped_group_counts_as_running_while_a_live_member_is_left_never_a_zombie(tmp_path):
    """A4 builder, 22 Oct: SIGKILL ends each member when the kernel reaches it; a hook is git's grandchild, which
    `communicate` does not wait for, so the call waits until no live member of its group is left."""
    from fno.desk.git_limit import running_in_group

    assert running_in_group(7, _fake_proc(tmp_path / "a", {8: ("S", 7), 9: ("R", 3)})) is True
    assert (
        running_in_group(7, _fake_proc(tmp_path / "b", {8: ("Z", 7), 9: ("R", 3)})) is False
    )  # a zombie holds nothing
    assert running_in_group(7, tmp_path / "absent") is False  # cannot tell: never wait forever


def test_the_wait_for_a_stopped_group_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr("fno.desk.git_limit.GROUP_GONE_SECONDS", 0.2)
    run = LimitedRun(proc=_fake_proc(tmp_path, {8: ("S", 7)}))  # a member that never ends
    started = time.monotonic()
    run._until_gone(7)
    assert 0.2 <= time.monotonic() - started < 5
