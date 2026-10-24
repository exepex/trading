"""`python -m fno daily run --rehearse --day D` (story REH1): the recorded day through the unchanged daily run. The
rehearsal's own checkout is made, the replay clock starts at the routine's time (14:05 IST) on the day, the guard
checks every outside service, and the daily run runs in the checkout as a child with the mode set; at the end its
branch is the one push to GitHub. The run's own last line is kept; the rehearsal adds its first and last lines."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from datetime import date, datetime, time
from pathlib import Path

from ..constants import ENV_FNO_REHEARSAL
from ..models import IST
from .checkout import RehearsalCheckout, RehearsalCheckoutError, run_git
from .clock import ReplayClock
from .git_dates import install_git_shim
from .mode import Rehearsal

ROUTINE_START = time(14, 5)  # CLAUDE.md: the daily routine's scheduled start
HOME = Path("~/.fno/rehearsals").expanduser()
STARTED = "rehearsal {day} {run_id}: data as of {at}, checkout {checkout}"
NOT_A_SESSION = "rehearsal refused: {day} is not a session day (NSE's calendar)"
GUARD_STOPPED = "rehearsal STOPPED before any step: {problem}"
ENDED = "rehearsal {day} {run_id} ended: {line}; branch {ref}; Drive dryrun/{run_id}/"


def rehearse_daily(day: date, source: Path, out: Callable[[str], None] = print, home: Path = HOME,
                   is_session: Callable[[date], bool] | None = None, run_child=None, guard=None) -> int:  # fmt: skip
    if not (is_session or _is_session)(day):
        out(NOT_A_SESSION.format(day=day))
        return 1
    mode = Rehearsal.new(day, home, source)
    start = datetime.combine(day, ROUTINE_START, IST)
    checkout = RehearsalCheckout(source, mode, home)
    ReplayClock(mode.state).start(start)  # first: the origin's push log reads it from the first push on
    try:
        checkout.create(start)
    except RehearsalCheckoutError as failed:
        out(str(failed))
        return 1
    out(STARTED.format(day=day, run_id=mode.run_id, at=start.isoformat(), checkout=checkout.clone))
    path = install_git_shim(checkout.root / "bin", mode.state)  # every commit dated by the replay clock
    env = {**os.environ, ENV_FNO_REHEARSAL: mode.to_env(), "PATH": path}
    for problem in (guard or _guard)(env, checkout.clone):
        out(GUARD_STOPPED.format(problem=problem))
        return 1
    code, line = (run_child or _run_child)(checkout.clone, day, env, out)
    ref = checkout.publish(run_git(source, "remote", "get-url", "origin").strip())
    out(ENDED.format(day=day, run_id=mode.run_id, line=line, ref=ref))
    return code


def _is_session(day: date) -> bool:
    from ..storage.trading_days import is_trading_day
    from ..storage.wiring import build_session_calendar

    return is_trading_day(build_session_calendar(), day)


def _guard(env: dict, cwd: Path) -> list[str]:
    """`rehearse check` in a child started as every step is (`python -m fno`, the mode set, in the checkout): its own
    clock and HTTP guard, and every builder's rehearsal form."""
    command = [sys.executable, "-m", "fno", "rehearse", "check"]
    done = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, check=False)
    found = [line for line in done.stdout.splitlines() if line]
    if done.returncode != 0 and not found:
        return [f"the guard could not run: {(done.stderr or '').strip().splitlines()[-1:]}"]
    return found


def _run_child(checkout: Path, day: date, env: dict, out: Callable[[str], None]) -> tuple[int, str]:
    """The unchanged `daily run` in the rehearsal's checkout, its lines relayed as they come; its last line kept."""
    command = [sys.executable, "-m", "fno", "daily", "run", "--day", day.isoformat()]
    child = subprocess.Popen(command, cwd=checkout, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)  # fmt: skip
    last = ""
    for line in child.stdout:
        out(line.rstrip("\n"))
        last = line.strip() or last
    return child.wait(), last
