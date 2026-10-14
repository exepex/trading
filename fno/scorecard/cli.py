"""`python -m fno desk scorecard` (story E6): every strategy version's paper scorecard against its plan, after the
automatic pause rules have run. Paper and research only: nothing here places an order."""

from __future__ import annotations

from datetime import date

EXIT_REFUSED = 2


def add_desk_parser(subparsers) -> None:
    desk = subparsers.add_parser("desk", help="the paper desk's strategy scorecards and pause rules (never orders)")
    actions = desk.add_subparsers(dest="desk_cmd", required=True)
    card = actions.add_parser("scorecard", help="scorecards per version and account; fires the automatic pauses")
    card.add_argument("--book", help="only this account (a book, or shadow:<name>-v<n>)")
    card.add_argument("--strategy", help="only this version, <name>-v<n>")
    card.add_argument("--on", type=date.fromisoformat, help="the day judged (default today, IST)")
    card.add_argument("--snapshot", help="marks for open positions: YYYY-MM-DD/<snapshot id> of a recorded capture")
    card.add_argument("--report-only", action="store_true", help="show the scorecards without firing any pause")
    desk.set_defaults(func=cmd_desk)


def cmd_desk(args) -> int:
    from ..config import load_app_config
    from ..desk.wiring import build_execution_snapshots
    from ..models import now_ist
    from ..playbook.fields import PlaybookError
    from .report import report
    from .scorecard import snapshot_marks
    from .wiring import build_scorecard_run

    on = args.on or now_ist().date()
    marks = {}
    if args.snapshot:
        day, snapshot_id = args.snapshot.split("/", 1)
        marks = snapshot_marks(build_execution_snapshots().snapshot(date.fromisoformat(day), snapshot_id))
    try:
        cards, actions = build_scorecard_run(load_app_config()).run(
            on, marks, args.book, args.strategy, pause=not args.report_only
        )
    except PlaybookError as refused:
        print(f"refused: {refused}")
        return EXIT_REFUSED
    print("\n".join(report(cards, actions)))
    return 0
