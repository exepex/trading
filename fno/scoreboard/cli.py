"""`python -m fno scoreboard b [--on YYYY-MM-DD]` (story S2): scoreboard B from the paper records, written to
`research/scoreboards/B/<date>.json` and kept in Drive, never committed (story E2c: it holds marked results). Research
only: it reads records and places nothing."""

from __future__ import annotations

from datetime import date

LINE = "{book}: {state}"


def add_scoreboard_parser(subparsers) -> None:
    board = subparsers.add_parser("scoreboard", help="the books' scoreboards (epic S)")
    which = board.add_subparsers(dest="scoreboard_cmd", required=True)
    whole = which.add_parser("b", help="scoreboard B, whole systems: each book's paper account (story S2)")
    whole.add_argument("--on", type=date.fromisoformat, help="the last day counted (default today, IST)")
    board.set_defaults(func=cmd_scoreboard)


def summary(board: dict) -> list[str]:
    lines = [
        f"scoreboard B {board['date']} ({board['protocol']}); common start {board['common_start'] or 'not reached'}"
    ]
    for book, entry in board["books"].items():
        if "overall" not in entry:
            lines.append(LINE.format(book=book, state=entry["account"]))
            continue
        overall, ok = entry["overall"], entry["reconciliation"]["ok"]
        money = f"raw account net Rs {overall['raw_account_net_rs']:,.2f}, {overall['trades']['positions']} positions"
        state = f"{money}, {'reconciles' if ok else 'DOES NOT RECONCILE'} with C1"
        lines.append(LINE.format(book=book, state=state))
    return lines


def cmd_scoreboard(args) -> int:
    from ..config import ROOT, load_app_config
    from ..desk.wiring import download_private_records
    from ..models import now_ist
    from .whole_system import write_board
    from .wiring import build_whole_system_board

    files = download_private_records()
    board = build_whole_system_board(load_app_config()).build(args.on or now_ist().date())
    path = write_board(ROOT, board)
    files.push([path])
    print("\n".join([*summary(board), f"written {path.relative_to(ROOT)} and kept in Drive (never committed)"]))
    return 0
