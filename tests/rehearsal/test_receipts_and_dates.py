"""REH1b round 2 (judge 562): with the mode set, the push receipts the seals and packs read are the rehearsal origin's
push log, never GitHub's; and the rehearsal's commits are dated by the replay clock through the child's PATH."""

import re
import subprocess
from datetime import date, datetime
from pathlib import Path

import pytest

from fno.ai.receipts import ReceiptNotFound
from fno.constants import ENV_FNO_REHEARSAL
from fno.models import IST
from fno.rehearsal.mode import Rehearsal
from fno.rehearsal.push_receipts import PUSH_LOG, LocalPushReceipts

PACKAGE = Path(__file__).resolve().parents[2] / "fno"
DAY = date(2026, 10, 23)


def test_with_the_mode_set_a_real_builder_reads_the_rehearsal_s_push_log(monkeypatch, tmp_path):
    from fno.v4_pack.wiring import build_commitment_times

    mode = Rehearsal.new(DAY, tmp_path, tmp_path)
    monkeypatch.setenv(ENV_FNO_REHEARSAL, mode.to_env())
    times = build_commitment_times(tmp_path)
    receipts = times.evidence.receipts
    assert isinstance(receipts, LocalPushReceipts) and receipts.log == mode.state / PUSH_LOG


def test_every_builder_of_github_s_receipts_hands_them_to_the_rehearsal_s_choice():
    builders = [
        p for p in PACKAGE.rglob("*.py") if "GitHubActivityReceipts(" in p.read_text() and p.name != "receipts.py"
    ]
    assert len(builders) == 5
    for path in builders:
        text = path.read_text()
        assert re.search(r"rehearsed_receipts\(\s*GitHubActivityReceipts\(", text), path  # built, then handed over


class History:
    """Ancestry by a planted table: which commits each pushed commit holds."""

    def __init__(self, holds):
        self.holds = holds

    def is_ancestor(self, older, newer):
        return older in self.holds.get(newer, set())


def test_a_commit_already_held_before_a_push_is_not_received_by_it(tmp_path):
    """Judge 562 minor B2: `_held` decides; a push whose old tip already holds the commit did not bring it."""
    log = tmp_path / PUSH_LOG
    log.write_text("1761210000 aaa bbb\n")  # one push, from aaa to bbb; the commit c1 was in aaa already
    receipts = LocalPushReceipts(log, History({"aaa": {"c1"}, "bbb": {"c1"}}))
    with pytest.raises(ReceiptNotFound):
        receipts.received_at("c1")


def git(cwd, *args, env=None):
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout


def test_the_hook_logs_pushes_to_main_only(tmp_path):
    """Judge 562 minor B6: a push of any other ref is not a receipt of main."""
    from fno.rehearsal.clock import ReplayClock
    from fno.rehearsal.push_receipts import post_receive_hook

    ReplayClock(tmp_path / "state").start(datetime(2026, 10, 23, 15, 29, tzinfo=IST))
    bare, clone = tmp_path / "origin.git", tmp_path / "clone"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(bare))
    hook = bare / "hooks" / "post-receive"
    hook.write_text(post_receive_hook(tmp_path / "state"))
    hook.chmod(0o755)
    git(tmp_path, "clone", "-q", str(bare), str(clone))
    git(clone, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x")
    git(clone, "push", "-q", "origin", "HEAD:refs/heads/other")
    assert not (tmp_path / "state" / PUSH_LOG).exists()
    git(clone, "push", "-q", "origin", "HEAD:main")
    assert len((tmp_path / "state" / PUSH_LOG).read_text().splitlines()) == 1
