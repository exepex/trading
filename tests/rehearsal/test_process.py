"""REH1a, judge 557 SF1: a process started through the package's real entry point with the mode set runs on the
replay clock and refuses a live call; the rehearsal's own `rehearse check` proves both in a child. Removing either of
`install_process`'s two installs fails this test."""

import os
import subprocess
import sys
from datetime import UTC, date, datetime
from pathlib import Path

from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.clock import ReplayClock
from fno.rehearsal.mode import Rehearsal
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS

REPOSITORY = Path(__file__).resolve().parents[2]


def check(env):
    command = [sys.executable, "-m", "fno", "rehearse", "check"]
    return subprocess.run(command, cwd=REPOSITORY, env=env, capture_output=True, text=True, timeout=120, check=False)


def child_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in OWNER_UPLOAD_SETTINGS}  # never a real Drive sign-in
    return {**env, "FNO_SLACK_BOT_TOKEN": "xoxb-test", **extra}


def test_a_rehearsing_process_runs_on_the_replay_clock_and_refuses_a_live_call(tmp_path):
    mode = Rehearsal.new(date(2026, 10, 23), tmp_path, tmp_path)
    ReplayClock(mode.state).start(datetime(2026, 10, 23, 8, 35, tzinfo=UTC))  # 14:05 IST, a day ago
    done = check(child_env(**{ENV_FNO_REHEARSAL: mode.to_env()}))
    assert (done.returncode, done.stdout) == (0, ""), done.stdout + done.stderr


def test_without_the_mode_the_check_says_there_is_nothing_to_check():
    done = check({k: v for k, v in child_env().items() if k != ENV_FNO_REHEARSAL})
    assert done.returncode == 1 and "FNO_REHEARSAL is not set" in done.stdout
