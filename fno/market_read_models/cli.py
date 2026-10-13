"""`python -m fno market ...` (story P6): the NSE market read models for the dashboard's Screener and Markets.

market daily [--day D]          the routine: archive the session's NSE files to Drive, then publish (default: the
                                last session before today, IST; run after NSE's late-evening rewrites)
market publish --day D [--local FOLDER]   build, validate and publish one session from the archived files
market compare --day D          compare the built blocks with the pinned W11 examples, field by field
market contract-check           compare the pinned W11 contract with the dashboard's published one
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

DAILY_DATASETS = ("fo-bhavcopy", "index-close", "cm-bhavcopy", "security-delivery")
DAILY_SNAPSHOTS = ("equity-list", "nifty500-list")
FETCH_FAILED = "Omenix F&O market read models for {day}: NSE files not archived ({reason}); nothing published."


def add_market_parser(subparsers) -> None:
    market = subparsers.add_parser("market", help="NSE market read models for the dashboard (story P6)")
    actions = market.add_subparsers(dest="market_cmd", required=True)
    daily = actions.add_parser("daily", help="archive the session's NSE files, then build, validate and publish")
    daily.add_argument("--day", type=date.fromisoformat, help="YYYY-MM-DD (default: the last session before today)")
    publish = actions.add_parser("publish", help="build, validate and publish one session from the archived files")
    publish.add_argument("--day", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    publish.add_argument("--local", type=Path, help="publish to this folder instead of Azure")
    compare = actions.add_parser("compare", help="compare the built blocks with the pinned W11 examples")
    compare.add_argument("--day", type=date.fromisoformat, default=date(2026, 10, 12), help="YYYY-MM-DD")
    actions.add_parser("contract-check", help="compare the pinned W11 contract with the dashboard's")
    market.set_defaults(func=cmd_market)


def cmd_market(args) -> int:
    handlers = {"daily": _daily, "publish": _publish, "compare": _compare, "contract-check": _contract_check}
    return handlers[args.market_cmd](args)


def _publish(args) -> int:
    from ..composition import build_market_run, build_read_model_publisher
    from ..config import load_app_config

    code, lines = build_market_run(load_app_config(), build_read_model_publisher(args.local)).run(args.day)
    print("\n".join(lines))
    return code


def _daily(args) -> int:
    from ..composition import build_alert_sender
    from ..models import now_ist
    from ..storage.wiring import build_session_calendar

    day = args.day or build_session_calendar().previous_session(now_ist().date())
    problem = _archive_session(day)
    if problem:
        message = FETCH_FAILED.format(day=day, reason=problem)
        print(message)
        print(build_alert_sender().send(message))
        return 1
    args.day, args.local = day, None
    return _publish(args)


def _archive_session(day: date) -> str | None:
    """Archives the session's files (with their manifest rows, committed); the first problem, or None."""
    from ..storage.wiring import build_librarian, build_manifest_recorder, build_snapshot_taker

    recorder = build_manifest_recorder()
    try:
        for name in DAILY_DATASETS:
            report = build_librarian(name, log=print).fill(day, day)
            if not report.complete:
                gaps = len(report.not_published), len(report.damaged), len(report.rejected)
                return f"{name}: {gaps[0]} not published yet, {gaps[1]} damaged, {gaps[2]} rejected"
        for name in DAILY_SNAPSHOTS:
            print(build_snapshot_taker(name).take(day))
        return None
    except (RuntimeError, ValueError) as exc:
        return f"{type(exc).__name__}: {exc}"
    finally:
        print(recorder.commit(f"market daily {day}"))


def _compare(args) -> int:
    from ..composition import build_market_blocks, build_pinned_contract, build_session_rows_builder
    from ..config import load_app_config
    from .contract_examples import compare

    rows = build_session_rows_builder(load_app_config()).build(args.day)
    blocks = {b.page_key: b.build(rows) for b in build_market_blocks()}
    total = 0
    for name, found in compare(blocks, build_pinned_contract().examples()).items():
        total += len(found)
        print(f"{name}: {len(found)} difference(s)")
        for path, ours, theirs in found:
            print(f"    {path}: ours {ours!r}, example {theirs!r}")
    return 0 if total == 0 else 1


def _contract_check(args) -> int:
    from ..composition import build_pinned_contract, build_published_contract
    from .contract import drift

    contract = build_pinned_contract()
    changed = contract.changed_files()
    if changed:
        print(f"the pinned copy differs from its pin: {', '.join(changed)}")
        return 1
    drifted = drift(contract, build_published_contract())
    print(f"pinned W11 contract {contract.version} (commit {contract.pin['commit'][:12]}): "
          + (f"the dashboard has changed {', '.join(drifted)}" if drifted else "same as the dashboard's"))  # fmt: skip
    return 1 if drifted else 0
