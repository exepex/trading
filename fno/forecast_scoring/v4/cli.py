"""Commands of story G8 (protocol v4 scoring):

python -m fno forecast-v4-scores report [--as-of YYYY-MM-DD]    # write research/forecasts/v4_scores/<as-of>.{md,json}
python -m fno forecast-v4-scores look --look stop_rule_review   # the family decision and Test A (recorded once)

Before `research/forecasts/FREEZE_v4.md` exists every output starts with the EXPLORATORY line and `look` writes nothing.
"""

from __future__ import annotations

import json
from datetime import date

from ...forecast_v4.terms import LOOK_ERROR_RATE


def add_forecast_v4_scores_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "forecast-v4-scores", help="protocol v4 scores, comparisons and the two looks (story G8)"
    )
    actions = parser.add_subparsers(dest="v4_cmd", required=True)
    report = actions.add_parser("report", help="score every v4 forecast and write the descriptive report")
    report.add_argument("--as-of", type=date.fromisoformat, help="YYYY-MM-DD (default: today in IST)")
    look = actions.add_parser("look", help="run a confirmatory look (minutes: thresholds are computed at the look)")
    look.add_argument("--look", choices=sorted(LOOK_ERROR_RATE), required=True)
    parser.set_defaults(func=cmd_forecast_v4)


def cmd_forecast_v4(args) -> int:
    from ...models import now_ist
    from .wiring import build_look_records, build_scoring, build_thresholds

    scoring, records = build_scoring(), build_look_records()
    if args.v4_cmd == "report":
        return _report(scoring, records, (args.as_of or now_ist().date()).isoformat())
    return _look(scoring, records, build_thresholds(), args.look, now_ist())


def _report(scoring, records, as_of: str) -> int:
    from .render import report_json, report_lines
    from .scoring import QUESTIONS

    reports = [scoring.question_report(q) for q in QUESTIONS]
    lines = report_lines(reports, records.frozen(), as_of)
    records.folder.mkdir(parents=True, exist_ok=True)
    (records.folder / f"{as_of}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = report_json(reports, records.frozen(), as_of)
    (records.folder / f"{as_of}.json").write_text(json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


def _look(scoring, records, thresholds, look: str, decided_at) -> int:
    from dataclasses import asdict

    from .look import run_look
    from .records import EXPLORATORY

    counted_after = records.frozen_on() if records.frozen() else None
    result = run_look(look, decided_at, scoring.member_comparisons(counted_after), thresholds, records.closed(look))
    if counted_after is None:
        print("\n".join([EXPLORATORY, *result.lines()]))
        return 0
    payload = {"lines": result.lines(), "test_a": result.test_a, "regimes": [list(k) + [v] for k, v in
               result.regimes.items()], "misses": [list(k) + [v] for k, v in result.misses.items()],
               "members": [asdict(m) for m in result.decision.members]}  # fmt: skip
    print("\n".join([*result.lines(), f"recorded: {records.write(look, payload)}"]))
    return 0
