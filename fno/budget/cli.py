"""`python -m fno budget <action>` (stories F8 and BG1). Research and bookkeeping only; posts nothing.

- `meter`: the month's costs by item (design v2 section 8.1), the allocated plan cost apart from cash spend, the AI cap;
- `signal`: writes the month's signal file (`accounting/budget/<YYYY-MM>_signal.json`) and dry-runs its alert;
- `stop-rule`: the stop-rule review date, days left, and which inputs of Test A and Test B exist yet;
- `record-usage`: adds one session's complete days to `accounting/ai_usage.csv` from a session export (F8).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ..constants import AI_BOOKS, USAGE_PURPOSES


def add_budget_parser(subparsers) -> None:
    budget = subparsers.add_parser("budget", help="AI usage, the budget meter and the stop-rule tracker (F8, BG1)")
    actions = budget.add_subparsers(dest="budget_cmd", required=True)
    for name, text in (("meter", "print the month's budget meter"),
                       ("signal", "write the month's budget signal and dry-run its alert")):  # fmt: skip
        actions.add_parser(name, help=text).add_argument("--month", help="YYYY-MM (default: this month in IST)")
    actions.add_parser("stop-rule", help="the stop-rule review date and its inputs")
    record = actions.add_parser("record-usage", help="record one session's usage from its export (written once)")
    record.add_argument("--export", type=Path, required=True, help="the JSON a Claude session saved (outside git)")
    record.add_argument("--purpose", required=True, choices=USAGE_PURPOSES)
    record.add_argument("--book", default="", choices=("", *AI_BOOKS))
    record.add_argument("--role", default="", help="the role or bundle the session worked for")
    budget.set_defaults(func=cmd_budget)


def cmd_budget(args) -> int:
    from ..models import now_ist

    today = now_ist().date()
    commands = {"meter": _meter, "signal": _signal, "stop-rule": _stop_rule, "record-usage": _record_usage}
    return commands[args.budget_cmd](args, today)


def _month(args, today: date) -> str:
    month = getattr(args, "month", None) or f"{today:%Y-%m}"
    date.fromisoformat(month + "-01")  # refuses a malformed month
    return month


def _meter(args, today: date) -> int:
    from .report import meter_lines
    from .wiring import build_month_meter

    print("\n".join(meter_lines(build_month_meter(_month(args, today), today))))
    return 0


def _signal(args, today: date) -> int:
    from ..config import ROOT
    from ..models import now_ist
    from .signal import send_alert, signal_data, write_signal
    from .wiring import build_budget_alert_sender, build_month_meter

    meter = build_month_meter(_month(args, today), today)
    data = signal_data(meter.month, meter.cap, len(meter.missing_captures), now_ist())
    print(f"signal {data['level']} written: {write_signal(ROOT, data).relative_to(ROOT)}")
    print(send_alert(build_budget_alert_sender(), data))
    return 0


def _stop_rule(args, today: date) -> int:
    from ..config import ROOT
    from .report import stop_rule_lines
    from .wiring import build_review_date

    print("\n".join(stop_rule_lines(ROOT, build_review_date(), today)))
    return 0


def _record_usage(args, today: date) -> int:
    from .usage_export import ExportRefused
    from .usage_ledger import Attribution, UsageRefused
    from .wiring import build_usage_ledger, build_usage_reader

    try:
        reader = build_usage_reader(args.export)
        before = min(today, reader.captured_on())  # a day still running when the export was taken is not complete
        lines = build_usage_ledger().record(reader.days(), Attribution(args.purpose, args.book, args.role), before)
    except (ExportRefused, UsageRefused) as refused:
        print(f"refused: {refused}")
        return 1
    print("\n".join(lines))
    return 0
