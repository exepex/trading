"""Commands for the daily forecasts (stories G2 and G3):

python -m fno forecast capture [--day YYYY-MM-DD] [--run-id ID]   # Book 1's daily record (the Actions job)
python -m fno forecast backfill [--check]                          # the history back-fill for evaluation
"""

from __future__ import annotations

from datetime import date


def add_forecast_parser(subparsers) -> None:
    forecast = subparsers.add_parser("forecast", help="daily forecasts: Book 1's capture and the history back-fill")
    actions = forecast.add_subparsers(dest="forecast_cmd", required=True)
    capture = actions.add_parser("capture", help="record Book 1's forecasts for a trading day (default: today, IST)")
    capture.add_argument("--day", type=date.fromisoformat, help="YYYY-MM-DD (default: today in IST)")
    capture.add_argument("--run-id", help="the GitHub Actions run, to save the run summary in Drive's pipeline area")
    backfill = actions.add_parser("backfill", help="write (or --check) the baselines' and Book 1's history records")
    backfill.add_argument("--check", action="store_true", help="recompute and compare with the committed file")
    forecast.set_defaults(func=cmd_forecast)


def cmd_forecast(args) -> int:
    return _capture(args) if args.forecast_cmd == "capture" else _backfill(args)


def _capture(args) -> int:
    from ..config import ROOT
    from ..models import now_ist
    from ..storage.wiring import build_session_calendar
    from .baseline_wiring import save_capture_summary
    from .capture import capture_book1

    started = now_ist()
    line = capture_book1(ROOT, args.day or started.date(), build_session_calendar())
    print(line)
    if args.run_id:
        print(save_capture_summary(args.run_id, started, line))
    return 0


def _backfill(args) -> int:
    from ..config import ROOT, load_app_config
    from .backfill import BACKFILL_FILE, backfill_records
    from .baseline_wiring import build_baselines, build_forecast_history, panel_pack_sha256
    from .record_files import records_gzip

    history = build_forecast_history(load_app_config())
    data = records_gzip(backfill_records(history, build_baselines(history), panel_pack_sha256()))
    path = ROOT / BACKFILL_FILE
    if args.check:
        same = path.exists() and path.read_bytes() == data
        print(f"back-fill {'unchanged' if same else 'DIFFERS from the committed file'}: {BACKFILL_FILE}")
        return 0 if same else 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"wrote {BACKFILL_FILE} ({len(data):,} bytes)")
    return 0
