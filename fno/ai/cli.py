"""`python -m fno ai <action>`: the GitHub Actions side of the AI books' forecasts (stories F1 and G5). Research only.

- `fire`: after the day's v2 pack is committed, fires each AI book's routine once (one #fno-desk line per failure);
- `reveals-ready`: exit 0 once every fired book's reveal is in the checkout (or nothing was fired);
- `collect`: after 15:15 IST, turns the books' sealed submissions into records and audit files (written once);
- `coverage`: per book, the pack days with a counted forecast (story G5 criterion 3).
The routine side is `python -m fno.ai` (standard library only).
"""

from __future__ import annotations

import json
from datetime import date


def add_ai_parser(subparsers) -> None:
    ai = subparsers.add_parser("ai", help="the AI books' daily forecasts: fire, collect, coverage (F1, G5)")
    actions = ai.add_subparsers(dest="ai_cmd", required=True)
    for name, text in (("fire", "fire each AI book's routine once for the day"),
                       ("reveals-ready", "exit 0 once every fired book's reveal is in"),
                       ("collect", "record the AI books' forecasts for the day (after 15:15 IST)")):  # fmt: skip
        action = actions.add_parser(name, help=text)
        action.add_argument("--day", type=date.fromisoformat, help="YYYY-MM-DD (default: today in IST)")
    actions.add_parser("coverage", help="pack days with a counted forecast, per AI book")
    ai.set_defaults(func=cmd_ai)


def cmd_ai(args) -> int:
    from ..models import now_ist

    day = getattr(args, "day", None) or now_ist().date()
    commands = {"fire": _fire, "reveals-ready": _reveals_ready, "collect": _collect, "coverage": _coverage}
    return commands[args.ai_cmd](day)


def _fire(day: date) -> int:
    from .wiring import build_ai_firer

    print("\n".join(build_ai_firer().fire(day)))
    return 0


def _reveals_ready(day: date) -> int:
    from ..config import ROOT
    from .paths import fired_path, reveal_path

    log = ROOT / fired_path(day)
    fired = [b for b, e in json.loads(log.read_text(encoding="utf-8")).items() if e["fired"]] if log.is_file() else []
    return 0 if all((ROOT / reveal_path(day, book)).is_file() for book in fired) else 1


def _collect(day: date) -> int:
    from .wiring import build_ai_collector

    print("\n".join(build_ai_collector().collect(day)))
    return 0


def _coverage(day: date) -> int:
    from ..config import ROOT
    from .coverage import coverage_lines

    print("\n".join(coverage_lines(ROOT)))
    return 0
