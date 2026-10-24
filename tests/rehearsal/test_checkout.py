"""REH1, acceptance 2 and 4b on real git repositories: the rehearsal's checkout has today's code and the data as of the
routine's start; every committer's `HEAD:main` push lands in the local bare origin; the one push to "GitHub" is the
rehearsal's own ref, and no other ref can be pushed. The record scan's hooks path is set and checked."""

import os
import subprocess
from datetime import date, datetime

import pytest

from fno.models import IST
from fno.rehearsal.checkout import RehearsalCheckout, RehearsalCheckoutError, refuse_unless_rehearsal_ref
from fno.rehearsal.mode import Rehearsal
from fno.rehearsal.rehearse import rehearse_daily

DAY = date(2026, 10, 23)
START = datetime(2026, 10, 23, 14, 5, tzinfo=IST)


def git(cwd, *args, when=None):
    env = {**os.environ, **({"GIT_COMMITTER_DATE": when, "GIT_AUTHOR_DATE": when} if when else {})}
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout


def refs(repo):
    return git(repo, "for-each-ref", "--format=%(refname)").split()


@pytest.fixture
def source(tmp_path):
    """A checkout of a "GitHub" origin: data recorded in the morning, the day's run at 15:15, a code change since."""
    github, repo = tmp_path / "github.git", tmp_path / "source"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(github))
    git(tmp_path, "clone", "-q", str(github), str(repo))
    for key, value in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(repo, "config", key, value)
    git(repo, "checkout", "-q", "-b", "main")
    steps = [("receipts/data/a.sha256", "morning", "2026-10-23T09:00:00+05:30"),
             ("journal/runs/2026-10-23.json", "the real run", "2026-10-23T15:15:00+05:30"),
             ("fno/code.py", "today's code", "2026-10-24T10:00:00+05:30")]  # fmt: skip
    for path, text, when in steps:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text)
        git(repo, "add", path)
        git(repo, "commit", "-q", "-m", text, when=when)
    git(repo, "push", "-q", "origin", "main")
    return repo, github


def test_the_checkout_has_today_s_code_the_morning_s_data_and_a_local_origin(source, tmp_path):
    repo, github = source
    checkout = RehearsalCheckout(repo, Rehearsal.new(DAY, tmp_path / "home", repo), tmp_path / "home")
    checkout.create(START)
    clone = checkout.clone
    assert (clone / "fno/code.py").read_text() == "today's code" and (clone / "receipts/data/a.sha256").is_file()
    assert not (clone / "journal/runs/2026-10-23.json").exists()  # the day's real run is not there
    assert git(clone, "remote", "get-url", "origin").strip() == str(checkout.bare)
    assert git(clone, "config", "core.hooksPath").strip() == ".githooks"
    (clone / "journal/runs").mkdir(parents=True)
    (clone / "journal/runs/2026-10-23.json").write_text("rehearsed")
    git(clone, "add", "journal")
    git(clone, "commit", "-q", "-m", "Desk run 2026-10-23 step quotes")
    git(clone, "push", "-q", "origin", "HEAD:main")  # as every committer of every step does
    assert "Desk run 2026-10-23 step quotes" in git(checkout.bare, "log", "--format=%s", "main")
    assert "Desk run" not in git(github, "log", "--format=%s", "main") and refs(github) == ["refs/heads/main"]


def test_publish_pushes_only_the_rehearsal_s_ref_and_every_other_ref_is_refused(source, tmp_path):
    repo, github = source
    lines = []
    ran = lambda clone, routine, day, env, out: (0, "day done")  # noqa: E731
    code = rehearse_daily(DAY, repo, lines.append, tmp_path / "home", is_session=lambda d: True, run_child=ran,
                          guard=lambda env, cwd: [])  # fmt: skip
    pushed = refs(github)
    assert code == 0 and pushed[0] == "refs/heads/main" and len(pushed) == 2
    assert pushed[1].startswith("refs/heads/rehearsal/2026-10-23-")
    assert git(github, "log", "-1", "--format=%s", "main").strip() == "today's code"  # main unchanged
    run_id = pushed[1].removeprefix("refs/heads/rehearsal/2026-10-23-")
    assert lines[0].startswith(f"rehearsal daily 2026-10-23 {run_id}: ") and lines[-1].endswith(
        f"Drive dryrun/{run_id}/"
    )
    for ref in ("refs/heads/main", "refs/heads/story/x", "refs/tags/v1", "refs/heads/rehearsal/../main", "main"):
        with pytest.raises(RehearsalCheckoutError, match="only refs/heads/rehearsal/"):
            refuse_unless_rehearsal_ref(ref)


def test_a_guard_problem_stops_before_any_step_and_a_closed_day_is_refused(source, tmp_path):
    repo, github = source
    lines = []
    ran = []
    assert rehearse_daily(DAY, repo, lines.append, tmp_path / "home", is_session=lambda d: True,
                          run_child=lambda *a: ran.append(1), guard=lambda env, cwd: ["planted"]) == 1  # fmt: skip
    assert ran == [] and lines[-1] == "rehearsal STOPPED before any step: planted"
    assert refs(github) == ["refs/heads/main"]  # nothing published
    assert rehearse_daily(date(2026, 10, 24), repo, lines.append, tmp_path / "h2", is_session=lambda d: False) == 1
    assert lines[-1] == "rehearsal refused: 2026-10-24 is not a session day (NSE's calendar)"


def test_a_push_to_the_rehearsal_s_origin_has_a_receipt_at_the_replay_time(source, tmp_path):
    """REH1b: G13b's seals ask when a commit was pushed; a rehearsal answers from its origin's push log."""
    from fno.ai.history import RepoHistory
    from fno.rehearsal.clock import ReplayClock
    from fno.rehearsal.push_receipts import PUSH_LOG, LocalPushReceipts

    repo, _ = source
    mode = Rehearsal.new(DAY, tmp_path / "home", repo)
    ReplayClock(mode.state).start(datetime(2026, 10, 23, 15, 29, tzinfo=IST))
    checkout = RehearsalCheckout(repo, mode, tmp_path / "home")
    checkout.create(START)
    (checkout.clone / "seal.json").write_text("{}")
    git(checkout.clone, "add", "seal.json")
    git(checkout.clone, "commit", "-q", "-m", "seal")
    git(checkout.clone, "push", "-q", "origin", "HEAD:main")
    commit = git(checkout.clone, "rev-parse", "HEAD").strip()
    received = LocalPushReceipts(mode.state / PUSH_LOG, RepoHistory(checkout.clone)).received_at(commit)
    assert abs((received - datetime(2026, 10, 23, 15, 29, tzinfo=IST)).total_seconds()) < 30


def test_the_clone_s_data_commit_runs_the_record_scan_hook(source, tmp_path):
    """Judge 560 F2: the hooks path being set is not enough; the clone's own data commit runs the repository's hook
    (never --no-verify). The source's hook leaves a mark when it runs."""
    repo, _ = source
    hooks = repo / ".githooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text('#!/bin/sh\ntouch "$(git rev-parse --show-toplevel)/../hook-ran"\n')
    (hooks / "pre-commit").chmod(0o755)
    git(repo, "add", ".githooks")
    git(repo, "commit", "-q", "-m", "hooks", when="2026-10-24T10:05:00+05:30")
    checkout = RehearsalCheckout(repo, Rehearsal.new(DAY, tmp_path / "home", repo), tmp_path / "home")
    checkout.create(START)
    assert (checkout.root / "hook-ran").is_file()


def test_a_guard_that_crashes_or_exits_non_zero_stops_the_rehearsal_whatever_it_printed(tmp_path):
    """Judge 560 F3: only a clean exit with nothing printed is safe."""
    import sys

    from fno.rehearsal.rehearse import _guard

    crash = (sys.executable, "-c", "raise RuntimeError('guard broke')")
    quiet_fail = (sys.executable, "-c", "raise SystemExit(3)")
    clean = (sys.executable, "-c", "pass")
    assert _guard(dict(os.environ), tmp_path, crash)[-1].startswith("the guard did not finish cleanly (exit 1)")
    assert _guard(dict(os.environ), tmp_path, quiet_fail) == [
        "the guard did not finish cleanly (exit 3): no error output"
    ]
    assert _guard(dict(os.environ), tmp_path, clean) == []


def test_a_step_s_commit_through_the_rehearsal_s_env_carries_the_replay_date(source, tmp_path):
    """Judge 562 F2: the child's PATH puts the rehearsal's git first, so a step's commit is dated by the replay clock
    (14:05 IST on the day), never the wall clock's day after."""
    repo, _ = source
    dates = []

    def step(clone, routine, day, env, out):
        (clone / "decision.json").write_text("{}")
        subprocess.run(["git", "add", "decision.json"], cwd=clone, env=env, check=True)
        bare = {k: v for k, v in env.items() if k not in ("GIT_COMMITTER_DATE", "GIT_AUTHOR_DATE")}
        subprocess.run(["git", "commit", "-q", "-m", "Desk run step decisions"], cwd=clone, env=bare, check=True)
        dates.append(subprocess.run(["git", "log", "-1", "--format=%cI"], cwd=clone, env=bare, check=True,
                                    capture_output=True, text=True).stdout.strip())  # fmt: skip
        return 0, "day done"

    rehearse_daily(DAY, repo, [].append, tmp_path / "home", is_session=lambda d: True, run_child=step,
                   guard=lambda env, cwd: [])  # fmt: skip
    committed = datetime.fromisoformat(dates[0])
    assert abs((committed - START).total_seconds()) < 120  # the replay time, not today's
