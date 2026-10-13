"""Commands for story G4 (forecast scoring), apart from the frozen `fno/forecast/cli.py`:

python -m fno forecast-scores run [--as-of YYYY-MM-DD]           # write research/forecasts/scores/<as-of>.json
python -m fno forecast-scores summary [--as-of YYYY-MM-DD] [--send]  # plain-words summary (--send: to #fno-desk)
"""

from __future__ import annotations

import json
from datetime import date


def add_forecast_scores_parser(subparsers) -> None:
    scores = subparsers.add_parser("forecast-scores", help="score the forecasts and write or summarise the report")
    actions = scores.add_subparsers(dest="scores_cmd", required=True)
    run = actions.add_parser("run", help="score every resolvable forecast as of a day and write the report")
    run.add_argument("--as-of", type=date.fromisoformat, help="YYYY-MM-DD (default: today in IST)")
    summary = actions.add_parser("summary", help="the plain-words summary of the latest report up to a day")
    summary.add_argument("--as-of", type=date.fromisoformat, help="YYYY-MM-DD (default: today in IST)")
    summary.add_argument("--send", action="store_true", help="also post it to #fno-desk")
    scores.set_defaults(func=cmd_forecast_scores)


def cmd_forecast_scores(args) -> int:
    from ..models import now_ist

    as_of = args.as_of or now_ist().date()
    return (_run if args.scores_cmd == "run" else _summary)(as_of, args)


def _run(as_of: date, args) -> int:
    from ..config import ROOT, load_app_config
    from ..forecast.freeze import NotFrozen
    from .score_report import report_json
    from .wiring import SCORES_FOLDER, build_receipts, score_forecasts

    try:
        document = score_forecasts(load_app_config(), as_of, build_receipts())
    except NotFrozen as problem:
        print(f"Omenix F&O forecast scores: not scored: protocol freeze check failed: {problem}")
        return 1
    path = ROOT / SCORES_FOLDER / f"{as_of.isoformat()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_json(document), encoding="utf-8")
    scored = sum(s["counts"]["resolved"] for m in document["modes"] for s in m["scores"])
    print(f"Omenix F&O forecast scores {as_of}: wrote {path.relative_to(ROOT)}; {scored} forecasts scored")
    return 0


def _summary(as_of: date, args) -> int:
    from ..composition import build_alert_sender
    from ..config import ROOT
    from .score_report import weekly_summary
    from .wiring import SCORES_FOLDER

    reports = sorted(p for p in (ROOT / SCORES_FOLDER).glob("*.json") if p.stem <= as_of.isoformat())
    if not reports:
        print(f"Omenix F&O forecast scores: no report up to {as_of}")
        return 1
    text = "\n".join(weekly_summary(json.loads(reports[-1].read_text(encoding="utf-8"))))
    print(text)
    if args.send:
        print(build_alert_sender().send(text))
    return 0
