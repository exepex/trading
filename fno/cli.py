"""Command-line entry point: python -m fno <command>."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

from .books.cli import add_account_parser
from .config import ROOT, load_app_config
from .providers import get_provider
from .quotes.cli import add_quotes_parser
from .research_data.participant_oi_cli import add_participant_oi_parser
from .storage.fingerprints_cli import add_fingerprints_parser
from .storage.librarian_cli import add_librarian_parser


def _cfg(args) -> dict:
    """The settings, with `--provider` overriding the root `provider` (used by `chain` and `groww-check` only; the
    quote recorder has its own `quotes.provider`)."""
    return load_app_config(args.config, {"provider": args.provider} if args.provider else None)


def cmd_drive_check(args) -> int:
    from .storage.drive_check import drive_check_lines

    lines = drive_check_lines()
    print("\n".join(lines))
    return 0 if lines[-1].startswith("inside it") else 1


def cmd_data_coverage(args) -> int:
    from .storage.coverage import report_lines
    from .storage.wiring import COVERAGE_DATASETS, build_coverage_check

    check = build_coverage_check()
    results = []
    for dataset in COVERAGE_DATASETS:  # one progress line per dataset, so a long run shows where it is
        results.append(check.run(dataset, args.start, args.end))
        print(f"checked {results[-1].dataset}: {results[-1].expected} sessions", flush=True)
    print("\n".join(report_lines(results)))
    print(f"calendar sha256 {check.calendar.calendar_sha256()}")
    return 0 if all(r.ok for r in results) else 1


def cmd_nifty_panel(args) -> int:
    from .research_data.nifty_panel import PanelBuildError, build_nifty_panel, summary_lines
    from .storage import wiring

    fo_files, index_files = wiring.build_nifty_panel_files(args.raw_folder)
    rules = {"calendar": wiring.build_session_calendar(), "exceptions": wiring.build_file_exceptions()}
    try:
        panel = build_nifty_panel(fo_files, index_files, args.start, args.end, sink=wiring.build_panel_sink(), **rules)
    except PanelBuildError as exc:
        print(f"NOT research-ready, nothing written: {exc}")
        return 1
    print("\n".join(summary_lines(panel)))
    return 0


def cmd_groww_check(args) -> int:
    from .providers.groww_check import groww_check_lines

    for line in groww_check_lines(_cfg(args)):
        print(line)
    return 0


def cmd_chain(args) -> int:
    from . import analytics as an

    cfg = _cfg(args)
    provider = get_provider(cfg["provider"], cfg)
    u = args.underlying.upper()
    expiry = date.fromisoformat(args.expiry) if args.expiry else provider.expiries(u)[0]
    chain = provider.chain(u, expiry)
    atm, step = chain.atm_strike(), chain.strike_step()
    print(f"{u} {expiry}  spot {chain.spot:,.2f}  lot {chain.lot_size}  as of {chain.timestamp:%d %b %H:%M}")
    print(
        f"PCR {an.put_call_ratio(chain) or 0:.2f}  max pain {an.max_pain(chain):,.0f}  "
        f"straddle move +/-{an.straddle_expected_move(chain) or 0:,.0f}"
    )
    print(
        f"{'CE OI':>10} {'CE IV':>6} {'CE bid/ask':>16} | {'strike':^8} | {'PE bid/ask':<16} {'PE IV':>6} {'PE OI':>10}"
    )
    for k in chain.strikes():
        if abs(k - atm) > step * args.width:
            continue
        ce, pe = chain.get(k, "CE"), chain.get(k, "PE")

        def ba(q):
            return f"{q.bid or 0:.2f}/{q.ask or 0:.2f}" if q else ""

        print(
            f"{(ce.oi if ce else 0):>10,.0f} {(ce.iv or 0) if ce else 0:>6.1f} {ba(ce):>16} | {k:^8,.0f} | "
            f"{ba(pe):<16} {(pe.iv or 0) if pe else 0:>6.1f} {(pe.oi if pe else 0):>10,.0f}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fno", description="Omenix F&O: Indian F&O options research (paper trading).")
    p.add_argument("--config", default=str(ROOT / "config.yaml"))
    p.add_argument("--provider", choices=["nse", "groww", "sample"], help="override the root provider (chain only)")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("drive-check", help="check the Google Drive project folder can be read (prints no secrets)")
    d.set_defaults(func=cmd_drive_check)
    v = sub.add_parser("data-coverage", help="list raw NSE files missing or damaged in Drive (read-only)")
    v.add_argument("--from", dest="start", type=date.fromisoformat, default=date(2019, 1, 1), help="YYYY-MM-DD")
    v.add_argument(
        "--to",
        dest="end",
        type=date.fromisoformat,
        default=date.today() - timedelta(days=1),
        help="YYYY-MM-DD (default: yesterday)",
    )
    v.set_defaults(func=cmd_data_coverage)
    n = sub.add_parser("nifty-panel", help="build the NIFTY option-chain panel from the raw NSE files (story A3)")
    n.add_argument("--from", dest="start", type=date.fromisoformat, default=date(2019, 1, 1), help="YYYY-MM-DD")
    n.add_argument("--to", dest="end", type=date.fromisoformat, required=True, help="YYYY-MM-DD: last day to include")
    n.add_argument("--raw-folder", type=Path, help="local project folder searched before Drive (its raw area)")
    n.set_defaults(func=cmd_nifty_panel)
    g = sub.add_parser("groww-check", help="check the Groww data connection (prints no secrets)")
    g.set_defaults(func=cmd_groww_check)

    c = sub.add_parser("chain", help="print an option chain around the money")
    c.add_argument("underlying")
    c.add_argument("--expiry", help="YYYY-MM-DD (default: nearest)")
    c.add_argument("--width", type=int, default=8, help="strikes either side of ATM")
    c.set_defaults(func=cmd_chain)

    add_quotes_parser(sub)
    add_account_parser(sub)
    add_participant_oi_parser(sub)
    add_librarian_parser(sub)
    add_fingerprints_parser(sub)

    args = p.parse_args(argv)
    return args.func(args)
