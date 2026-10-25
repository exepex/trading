"""`python -m fno recommend decide [--on YYYY-MM-DD]` (story REC1b): the day's one recommendation, recorded
write-once with its receipt pushed, then posted to #fno-desk. A day that is not an NSE trading session records
nothing. Exit 1 when the record was not made or posted, or an input could not be read (the daily run then names
the step)."""

from __future__ import annotations

from datetime import date

from ..models import now_ist

NOT_A_SESSION = "recommend {day}: not a trading day, nothing recorded"


def add_recommend_parser(sub) -> None:
    recommend = sub.add_parser("recommend", help="the recommender's daily answer (paper only; story REC1)")
    commands = recommend.add_subparsers(dest="recommend_cmd", required=True)
    decide = commands.add_parser("decide", help="record and post the day's recommendation (after the school step)")
    decide.add_argument("--on", type=date.fromisoformat, default=None, help="YYYY-MM-DD (default: today, IST)")
    decide.set_defaults(func=cmd_decide)


def cmd_decide(args, out=print) -> int:
    from ..config import load_app_config
    from .wiring import build_recommend_run, is_session

    day = args.on or now_ist().date()
    if not is_session(day):
        out(NOT_A_SESSION.format(day=day))
        return 0
    result = build_recommend_run(load_app_config()).run(day)
    for line in result.lines:
        out(line)
    return 0 if result.ok else 1
