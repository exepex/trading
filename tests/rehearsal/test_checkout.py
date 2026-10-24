"""REH1, acceptance 2 and 4b on real git repositories: the rehearsal's checkout has today's code and the data as of the
routine's start; every committer's `HEAD:main` push lands in the local bare origin; the one push to "GitHub" is the
rehearsal's own ref, and no other ref can be pushed. The record scan's hooks path is set and checked."""

import os
import subprocess
from datetime import date, datetime

import pytest

from fno.daily.full_log import FULL_LOGS
from fno.models import IST
from fno.rehearsal.checkout import RehearsalCheckout, RehearsalCheckoutError, refuse_unless_rehearsal_ref
from fno.rehearsal.mode import Rehearsal
from fno.rehearsal.rehearse import rehearse_daily

from .test_exercised_line import LINE, STEPS, Recording, full_log

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


def test_a_routine_s_receipts_commit_carries_the_replay_date(source, tmp_path):
    """Judge 564 F2: the receipts commit `rehearse` makes after the routine's commands goes through the rehearsal's
    git too, so it is dated at the routine's replayed time (19:53 IST on the day), never the wall clock's."""
    from fno.rehearsal.rehearse import rehearse
    from fno.rehearsal.routines import ROUTINES

    repo, github = source
    evening = ROUTINES["evening"]

    def commands(clone, routine, day, env, out):
        folder = clone / evening.receipts[0]
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "edition.sha256").write_text("x")
        return 0, "1 commands done"

    rehearse(evening, DAY, repo, [].append, tmp_path / "home", is_session=lambda d: True, run_child=commands,
             guard=lambda env, cwd: [])  # fmt: skip
    ref = [r for r in refs(github) if r.startswith("refs/heads/rehearsal/")][0]
    subject, when = git(github, "log", "-1", "--format=%s%n%cI", ref).splitlines()
    assert subject == "Rehearsal evening 2026-10-23: the routine's receipts"
    start = datetime.combine(DAY, evening.start, IST)
    assert abs((datetime.fromisoformat(when) - start).total_seconds()) < 120  # the replay time, not today's


def hook(repo, script, when="2026-10-24T10:05:00+05:30"):
    hooks = repo / ".githooks"
    hooks.mkdir(exist_ok=True)
    (hooks / "pre-commit").write_text(f"#!/bin/sh\n{script}\n")
    (hooks / "pre-commit").chmod(0o755)
    git(repo, "add", ".githooks")
    git(repo, "commit", "-q", "-m", "hooks", when=when)


def test_the_checkout_s_own_commit_and_its_hook_run_with_the_mode_so_its_alerts_are_labelled(source, tmp_path):
    """REH1e (DRY2's stop, 24 Oct): the record scan's hook on the checkout's data commit ran without the mode and
    posted an unlabelled alert to #fno-desk. The rehearsing parent now carries the mode, and every hook it runs sees
    it; the parent's environment is back as it was afterwards."""
    from fno.constants import ENV_FNO_REHEARSAL
    from fno.rehearsal.mode import Rehearsal as Mode

    repo, _ = source
    hook(repo, f'echo "${ENV_FNO_REHEARSAL}" > "$(git rev-parse --show-toplevel)/../hook-env"')
    rehearse_daily(DAY, repo, [].append, tmp_path / "home", is_session=lambda d: True,
                   run_child=lambda *a: (0, "day done"), guard=lambda env, cwd: [])  # fmt: skip
    seen = next((tmp_path / "home").glob("*/hook-env")).read_text().strip()
    assert seen and Mode.from_env(seen).day == DAY  # the hook's alert sender is the rehearsal's labelled one
    assert ENV_FNO_REHEARSAL not in os.environ


def test_a_file_moved_out_of_the_repository_after_the_start_stays_out_and_the_scan_still_runs(source, tmp_path):
    """REH1e (the 23 Oct VIX case): a file the day had at the routine's start, moved to Drive later that day, is not
    restored as a repository file; today's scan, which refuses it, still runs on the checkout's commit and passes."""
    repo, github = source
    vix, calendar = "research/data/vix/india_vix_daily.csv", "research/data/calendar/nse_sessions.csv"
    for path in (vix, calendar):  # the folder stays tracked today, as on main
        (repo / path).parent.mkdir(parents=True)
        (repo / path).write_text("data")
        git(repo, "add", path)
    git(repo, "commit", "-q", "-m", "A15 VIX table", when="2026-10-23T08:00:00+05:30")
    git(repo, "rm", "-q", vix)
    git(repo, "commit", "-q", "-m", "O9b: VIX data out of the repository", when="2026-10-23T13:40:00+05:30")
    hook(repo, f'git diff --cached --name-only | grep -q "^{vix}$" && exit 1; touch "$(git rev-parse '
               '--show-toplevel)/../hook-ran"; exit 0')  # fmt: skip
    git(repo, "push", "-q", "origin", "main")
    checkout = RehearsalCheckout(repo, Rehearsal.new(DAY, tmp_path / "home", repo), tmp_path / "home")
    checkout.create(datetime(2026, 10, 23, 8, 36, tzinfo=IST))
    assert not (checkout.clone / vix).exists() and (checkout.clone / calendar).is_file()
    assert (checkout.root / "hook-ran").is_file()
    assert vix not in git(checkout.clone, "ls-files")


# REH1j, J5: the exercised line through `rehearse` itself, on the real checkout (helpers: test_exercised_line)


def test_rehearse_prints_the_line_after_the_day_s_last_line_and_posts_it_once(source, tmp_path):
    repo, _ = source
    lines, sent = [], Recording()

    def day_run(clone, routine, day, env, out):
        full_log(clone, STEPS)
        out("day done")
        return 0, "day done"

    rehearse_daily(DAY, repo, lines.append, tmp_path / "home", is_session=lambda d: True, run_child=day_run,
                   guard=lambda env, cwd: [], alerts=sent)  # fmt: skip
    at = lines.index("day done")
    assert lines[at + 1] == LINE and lines[at + 2].startswith("rehearsal daily 2026-10-23 ")  # then the end line
    assert sent.sent == [LINE]


def test_an_unreadable_full_log_never_stops_the_publish(source, tmp_path):
    repo, github = source
    lines = []

    def day_run(clone, routine, day, env, out):
        path = clone / FULL_LOGS / f"{DAY}.json"
        path.parent.mkdir(parents=True)
        path.write_text("{not json")
        return 0, "day done"

    code = rehearse_daily(DAY, repo, lines.append, tmp_path / "home", is_session=lambda d: True, run_child=day_run,
                          guard=lambda env, cwd: [], alerts=Recording())  # fmt: skip
    assert code == 0 and any(line.startswith("rehearsal: the exercised steps could not be read") for line in lines)
    assert lines[-1].startswith("rehearsal daily 2026-10-23 ")  # published


# REH1k, K4: a routine's not-live command reaches the same line, through `rehearse` itself


def test_a_routine_s_not_live_command_is_printed_after_its_last_line_and_posted_once(source, tmp_path, monkeypatch):
    from fno.rehearsal import rehearse as module
    from fno.rehearsal.exercised_line import not_live_result
    from fno.rehearsal.routines import ROUTINES

    repo, _ = source
    lines, sent = [], Recording()

    def routine_run(clone, routine, day, env, out, not_live, exercised):
        assert not_live == {"evening"}  # what the rehearsal found not live on the day, handed to the routine
        exercised["lab close"] = {"result": not_live_result(1, "lab close said no")}
        out("7 commands done")
        return 0, "7 commands done"

    monkeypatch.setattr(module, "run_routine", routine_run)
    monkeypatch.setattr(module, "_not_live_editions", lambda day: frozenset({"evening"}))
    code = module.rehearse(ROUTINES["evening"], DAY, repo, lines.append, tmp_path / "home",
                           is_session=lambda d: True, guard=lambda env, cwd: [], alerts=sent)  # fmt: skip
    line = "not live in real runs (exercised): lab close failed: lab close said no"
    at = lines.index("7 commands done")
    assert code == 0 and lines[at + 1] == line and sent.sent == [line]


def test_which_editions_are_not_live_comes_from_the_config():
    from fno.rehearsal.rehearse import _not_live_editions

    assert _not_live_editions(date(2026, 10, 22)) == {"morning", "evening"}  # both live from 23 Oct
    assert _not_live_editions(DAY) == frozenset()
