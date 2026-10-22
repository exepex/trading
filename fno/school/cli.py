"""`python -m fno school ...` (story MS-P1j): the session's run, its replay, and b's capture-gate report.

- `run [--session D]`: the paper record of the 15:00 slot, only when `school.enabled` is true; otherwise it prints the
  school-off line and touches nothing (no store is even built).
- `run --replay FOLDER [--session D]`: a recorded session again, every write under FOLDER (no Drive write, no push,
  no commit, a fixed clock). A replay writes no paper record, so it runs whatever the switch says; it is how the
  end-to-end dry run is made.
- `capture-gate [...]`: b's read-only report (unchanged)."""

from collections import Counter
from datetime import date
from pathlib import Path

from ..config import load_app_config
from ..models import now_ist
from .constants import FLEET_STOPPED, SCHOOL_OFF_LINE, SETTINGS_KEY
from .settings import school_settings

NOT_A_SESSION = "not a trading day: nothing scheduled"


def add_school_parser(sub) -> None:
    school = sub.add_parser("school", help="the market school pilot (paper only; story MS-P1)")
    commands = school.add_subparsers(dest="school_cmd", required=True)
    run = commands.add_parser("run", help="the 15:00 slot of one session: decide, seal, fill (paper only)")
    run.add_argument("--session", type=date.fromisoformat, default=None, help="YYYY-MM-DD (default: today, IST)")
    run.add_argument("--replay", type=Path, default=None, help="replay into this folder: no record, no push")
    run.set_defaults(func=cmd_run)
    gate = commands.add_parser("capture-gate", help="b's read-only capture-gate report")
    gate.add_argument("rest", nargs="*")
    gate.set_defaults(func=cmd_capture_gate)


def cmd_run(args, out=print) -> int:
    cfg = load_app_config(args.config) if getattr(args, "config", None) else load_app_config()
    session = args.session or now_ist().date()
    if args.replay is None and not school_settings(cfg).enabled:
        out(SCHOOL_OFF_LINE)
        return 0
    from .contracts.fleet import RunMode
    from .fleet.quote_share import share_lines
    from .wiring import build_fleet

    mode = RunMode.REPLAY if args.replay else RunMode.RECORD
    if mode is RunMode.REPLAY:
        cfg = {**cfg, SETTINGS_KEY: {**cfg[SETTINGS_KEY], "enabled": True}}
    run = build_fleet(cfg, mode, session, replay_folder=args.replay).run(session, mode)
    for line in run_lines(run, share_lines):
        out(line)
    return 1 if run.status.startswith(FLEET_STOPPED) else 0  # a stop fails the daily run's step, which alerts #fno-desk


def run_lines(run, share_lines) -> list[str]:
    if run.status:
        return [run.status]
    if not run.decisions:
        return [NOT_A_SESSION]
    tally = Counter((r.decision.outcome.value, r.decision.reason) for r in run.decisions)
    lines = [f"school {run.session} ({run.mode}): {len(run.decisions)} decisions sealed, {len(run.fills)} fills"]
    lines += [f"  {outcome}{': ' + reason if reason else ''} x{n}" for (outcome, reason), n in sorted(tally.items())]
    return lines + [f"  {line}" for line in share_lines(run.decisions)]


def cmd_capture_gate(args) -> int:
    from .quality.command import main

    return main(args.rest)
