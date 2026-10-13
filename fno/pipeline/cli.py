"""`python -m fno pipeline <action>` (story O6). Research data only; nothing here trades.

- `fire <job>`: run by a GitHub Actions workflow after its download step: fires the job's routine once per new batch
  and version, saves the run summary in Drive and posts one line to #fno-desk (plus one per failure);
- `dry-run <pointer>`: run by the dry-run routine with the text it was fired with (untrusted: checked field by field
  before anything is read).
"""

from __future__ import annotations

from .pointer import PointerRefused, parse_pointer

DEFAULT_DAYS = 5
ROUTINE_FAILED = "Omenix F&O dry-run routine, batch {batch}: {line}"


def add_pipeline_parser(subparsers) -> None:
    from .wiring import JOBS

    pipeline = subparsers.add_parser("pipeline", help="fire routines on new data in Drive (story O6)")
    actions = pipeline.add_subparsers(dest="pipeline_cmd", required=True)
    fire = actions.add_parser("fire", help="fire the job's routine for each new batch and version")
    fire.add_argument("job", choices=sorted(JOBS))
    fire.add_argument("--days", type=int, default=DEFAULT_DAYS, help=f"window in days (default {DEFAULT_DAYS})")
    fire.add_argument("--download", required=True, help="the download step's outcome (success, failure, skipped)")
    fire.add_argument("--run-id", required=True, help="GitHub's run ID and attempt, e.g. 123456-1")
    fire.add_argument("--note", action="append", default=[], help="a result line of the download command")
    fire.set_defaults(func=cmd_pipeline_fire)
    dry_run = actions.add_parser("dry-run", help="the example routine: summarise one pointed-to file into Drive")
    dry_run.add_argument("pointer", help="the JSON text the routine was fired with")
    dry_run.set_defaults(func=cmd_pipeline_dry_run)


def cmd_pipeline_fire(args) -> int:
    from .wiring import build_pipeline_run

    notes = tuple(n.strip() for n in args.note if n.strip())
    return build_pipeline_run(args.job, args.days).run(args.run_id, args.download, notes)


def cmd_pipeline_dry_run(args) -> int:
    from .wiring import POINTER_DATASETS, build_dry_run_routine

    try:
        pointer = parse_pointer(args.pointer, POINTER_DATASETS)
    except PointerRefused as error:
        print(f"pointer refused: {error}")
        return 1
    try:
        ok, line = build_dry_run_routine().process(pointer)
    except Exception as error:  # noqa: BLE001 - a refused Drive read or write is alerted, never only a traceback
        ok, line = False, f"Drive refused ({type(error).__name__}: {error})"
    print(line)
    if not ok:
        from ..composition import build_alert_sender

        print(build_alert_sender().send(ROUTINE_FAILED.format(batch=pointer.batch, line=line)))
    return 0 if ok else 1
