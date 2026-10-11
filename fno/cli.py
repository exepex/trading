"""Command-line entry point: python -m fno <command>."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import journal
from .config import ROOT, load_config
from .providers import get_provider


def _cfg(args) -> dict:
    overrides = {}
    if args.provider:
        overrides["provider"] = args.provider
    if getattr(args, "underlyings", None):
        overrides["underlyings"] = [u.upper() for u in args.underlyings]
    return load_config(args.config, overrides)


def cmd_brief(args) -> int:
    from .brief import run_brief

    cfg = _cfg(args)
    provider = get_provider(cfg["provider"], cfg)
    md, js, _ = run_brief(provider, cfg, args.out)
    print(md.read_text(encoding="utf-8"))
    print(f"\nSaved {md} and {js}", file=sys.stderr)
    return 0


def cmd_daily(args) -> int:
    """Morning routine: re-price paper trades, then write the brief (Markdown, HTML, Slack text)."""
    from .brief import run_brief

    cfg = _cfg(args)
    provider = get_provider(cfg["provider"], cfg)
    path = Path(args.journal)
    trades = journal.load(path)
    log = journal.mark(trades, provider, cfg) if trades else []
    journal.save(trades, path)
    st = journal.stats(trades)
    md, _, _ = run_brief(provider, cfg, args.out, journal_stats=st, journal_log=log)
    for line in log:
        print(line)
    stem = md.name.replace("-brief.md", "")
    for suffix in ("-brief.html", "-brief.png", "-page.html", "-slack.md"):
        f = md.parent / f"{stem}{suffix}"
        print(f"Wrote {f}" if f.exists() else f"Missing {f}")
    return 0


def cmd_notify(args) -> int:
    from .models import now_ist
    from .notify import post_brief

    cfg = _cfg(args)
    stamp = args.date or now_ist().strftime("%Y-%m-%d")
    print(post_brief(Path(args.out), stamp, cfg, args.web_url))
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
    print(f"PCR {an.put_call_ratio(chain) or 0:.2f}  max pain {an.max_pain(chain):,.0f}  "
          f"straddle move +/-{an.straddle_expected_move(chain) or 0:,.0f}")
    print(f"{'CE OI':>10} {'CE IV':>6} {'CE bid/ask':>16} | {'strike':^8} | {'PE bid/ask':<16} {'PE IV':>6} {'PE OI':>10}")
    for k in chain.strikes():
        if abs(k - atm) > step * args.width:
            continue
        ce, pe = chain.get(k, "CE"), chain.get(k, "PE")
        def ba(q):
            return f"{q.bid or 0:.2f}/{q.ask or 0:.2f}" if q else ""
        print(f"{(ce.oi if ce else 0):>10,.0f} {(ce.iv or 0) if ce else 0:>6.1f} {ba(ce):>16} | {k:^8,.0f} | "
              f"{ba(pe):<16} {(pe.iv or 0) if pe else 0:>6.1f} {(pe.oi if pe else 0):>10,.0f}")
    return 0


def cmd_paper(args) -> int:
    cfg = _cfg(args)
    path = Path(args.journal)
    trades = journal.load(path)
    if args.action == "open":
        cand = journal.find_candidate(args.target, Path(args.reports))
        t = journal.open_trade(trades, cand, cfg, lots=args.lots, note=args.note or "")
        journal.save(trades, path)
        print(f"Opened {t['id']}: {t['candidate']} x {t['lots']} lot(s), entry value {t['entry_value']:.2f}/unit")
    elif args.action == "mark":
        provider = get_provider(cfg["provider"], cfg)
        for line in journal.mark(trades, provider, cfg):
            print(line)
        journal.save(trades, path)
    elif args.action == "close":
        provider = get_provider(cfg["provider"], cfg)
        t = journal.close(trades, args.target, provider, cfg)
        journal.save(trades, path)
        print(f"Closed {t['id']}: net P&L Rs {t['pnl_net']:,.0f}")
    elif args.action == "report":
        print(journal.report(trades, cfg.get("account", {}).get("capital", 1)))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="fno", description="Indian F&O options research assistant (paper trading).")
    p.add_argument("--config", default=str(ROOT / "config.yaml"))
    p.add_argument("--provider", choices=["nse", "groww", "sample"], help="override config provider")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("brief", help="scan underlyings and write today's research brief")
    b.add_argument("underlyings", nargs="*")
    b.add_argument("--out", default=str(ROOT / "reports"))
    b.set_defaults(func=cmd_brief)

    d = sub.add_parser("daily", help="morning routine: mark paper trades + write brief, HTML and Slack text")
    d.add_argument("--out", default=str(ROOT / "reports"))
    d.add_argument("--journal", default=str(journal.DEFAULT_PATH))
    d.set_defaults(func=cmd_daily)

    n = sub.add_parser("notify", help="post the day's brief (text + page images) to the F&O Slack channel")
    n.add_argument("--date", help="YYYY-MM-DD (default: today IST)")
    n.add_argument("--out", default=str(ROOT / "reports"))
    n.add_argument("--web-url", default="https://claude.ai/artifact/8tokXxQfSPnB3DxMpkYpXX")
    n.set_defaults(func=cmd_notify)

    c = sub.add_parser("chain", help="print an option chain around the money")
    c.add_argument("underlying")
    c.add_argument("--expiry", help="YYYY-MM-DD (default: nearest)")
    c.add_argument("--width", type=int, default=8, help="strikes either side of ATM")
    c.set_defaults(func=cmd_chain)

    j = sub.add_parser("paper", help="paper-trading journal")
    j.add_argument("action", choices=["open", "mark", "close", "report"])
    j.add_argument("target", nargs="?", help="candidate id (open) or trade id (close)")
    j.add_argument("--lots", type=int)
    j.add_argument("--note")
    j.add_argument("--journal", default=str(journal.DEFAULT_PATH))
    j.add_argument("--reports", default=str(ROOT / "reports"))
    j.set_defaults(func=cmd_paper)

    args = p.parse_args(argv)
    if args.cmd == "paper" and args.action in ("open", "close") and not args.target:
        p.error(f"paper {args.action} needs an id")
    return args.func(args)
