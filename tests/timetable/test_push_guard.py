"""Judge 118 addendum 6, should-fix 1, and decision 51, with real `Git` and a bare origin: (a) before every push the
raw-quote guard checks every file the push would change, whoever made the commit; (b) an unpushed commit the run did
not make is refused before anything is pulled or pushed. The run's own stuck commit, named by its pending marker,
still pushes, also when origin moved on and the recovery merges."""

import subprocess

import pytest

from fno.desk.daily_run import RunStopped
from fno.desk.git_sync import GitCommitter

from .fakes import RAW_QUOTE, Decisions
from .test_commit_failure_run import git
from .test_daily_run import NORMAL, run_day
from .test_rerun_after_stop import REJECT_LAST, FilePacks, origin_messages, real_run


def stray_commit(root, name, text="stray\n", message="a commit the run did not make"):
    (root / name).parent.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(text, encoding="utf-8")
    git(root, "add", "-f", "--", name)
    git(root, "commit", "-q", "-m", message)


def reject_last(root):
    hook = root / "origin.git" / "hooks" / "pre-receive"
    hook.write_text(REJECT_LAST, encoding="utf-8")
    hook.chmod(0o755)
    return hook


def stopped(root, tmp_path, alerts):
    run, clock, _ = real_run(root, tmp_path, alerts, Decisions(), FilePacks(root))
    return run, clock


def test_a_stray_local_raw_quote_commit_is_refused_before_any_push(root, tmp_path, alerts):
    run, clock = stopped(root, tmp_path, alerts)
    stray_commit(root, RAW_QUOTE, "contract_id,bid,ask\n")
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    (sent,) = alerts.sent
    assert "unpushed commit(s) the run did not make" in sent and RAW_QUOTE in sent
    assert origin_messages(root) == []  # origin unchanged


def test_the_pre_push_guard_alone_refuses_a_raw_quote_file_in_any_unpushed_commit(root, tmp_path, alerts, monkeypatch):
    """Layer (a) holds by itself: with the stray refusal switched off, the push is still refused, naming the file."""
    monkeypatch.setattr(GitCommitter, "_refuse_stray", lambda self, own: None)
    run, clock = stopped(root, tmp_path, alerts)
    stray_commit(root, RAW_QUOTE, "contract_id,bid,ask\n")
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    (sent,) = alerts.sent
    assert "would publish raw Groww quotes" in sent and "nifty_20261014_151500.csv" in sent
    assert origin_messages(root) == []


def test_a_stray_commit_without_quotes_is_refused_too(root, tmp_path, alerts):
    run, clock = stopped(root, tmp_path, alerts)
    stray_commit(root, "notes/hand_edit.md")
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    assert "notes/hand_edit.md" in alerts.sent[0] and origin_messages(root) == []


def test_the_run_s_own_stuck_commit_still_pushes_after_origin_moved_on(root, tmp_path, alerts):
    """The recovery's commit is the run's own (the marker's message, only the marker's files), so (b) lets it through;
    origin moved meanwhile, so a rerun's pull left a merge unpushed, and that merge is not a stray."""
    run, clock = stopped(root, tmp_path, alerts)
    hook = reject_last(root)
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(root / "origin.git"), str(other)], check=True, capture_output=True)
    for key, value in (("user.email", "t@example.org"), ("user.name", "t"), ("core.hooksPath", "/dev/null")):
        git(other, "config", key, value)
    (other / "elsewhere.md").write_text("another writer\n", encoding="utf-8")
    git(other, "add", "elsewhere.md")
    git(other, "commit", "-q", "-m", "another writer's commit")
    git(other, "push", "-q", "origin", "HEAD:main")
    with pytest.raises(RunStopped):  # a rerun while pushes are still rejected: its pull leaves a merge unpushed
        run.run(NORMAL)
    assert len(git(root, "rev-list", "--merges", "origin/main..HEAD").split()) == 1
    hook.unlink()
    run.run(NORMAL)
    assert f"Desk run {NORMAL} step trade_marks" in origin_messages(root)
    assert git(root, "rev-list", "origin/main..HEAD") == ""


def test_a_stray_commit_copying_the_run_s_message_but_touching_other_files_is_refused(root, tmp_path, alerts):
    run, clock = stopped(root, tmp_path, alerts)
    hook = reject_last(root)
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    stray_commit(root, "notes/hand_edit.md", message=f"Desk run {NORMAL} step trade_marks")
    hook.unlink()
    with pytest.raises(RunStopped):
        run.run(NORMAL)
    assert "the run did not make" in alerts.sent[-1] and "notes/hand_edit.md" in alerts.sent[-1]
    assert f"Desk run {NORMAL} step trade_marks" not in origin_messages(root)


def reworded(root):
    """The stuck commit itself under another message: the marker's files with the recorded content."""
    git(root, "reset", "-q", "--soft", "HEAD~1")
    git(root, "commit", "-q", "-m", "another message")


def changed_content(root):
    """A commit with the run's own message touching only one of the marker's files, with other content; the file on
    disk is then put back as recorded, so the rerun's own hash check passes and only the stray rule can refuse it."""
    log = root / "journal" / "runs" / f"{NORMAL}.json"
    recorded = log.read_bytes()
    log.write_text("{}\n", encoding="utf-8")
    git(root, "add", "--", str(log.relative_to(root)))
    git(root, "commit", "-q", "-m", f"Desk run {NORMAL} step trade_marks")
    log.write_bytes(recorded)


@pytest.mark.parametrize("stray", [reworded, changed_content])
def test_a_stray_on_only_the_marker_s_files_is_refused_by_message_and_by_content(root, tmp_path, alerts, stray):
    """Judge 118 addendum 7 minors 1-2: the recorded content under another message is refused (plant S4); the run's
    own message with content other than the marker recorded is refused too (own is exact by content)."""
    run, clock = stopped(root, tmp_path, alerts)
    hook = reject_last(root)
    with pytest.raises(RunStopped):
        run_day(run, clock, NORMAL)
    stray(root)
    hook.unlink()
    before = git(root / "origin.git", "rev-parse", "main")
    with pytest.raises(RunStopped):
        run.run(NORMAL)
    assert "the run did not make" in alerts.sent[-1] and f"journal/runs/{NORMAL}.json" in alerts.sent[-1]
    assert git(root / "origin.git", "rev-parse", "main") == before  # nothing pushed
