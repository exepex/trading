"""`python -m fno live <command>`: run the desk, scan once, check status, or use the kill switch."""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from datetime import datetime, timedelta

from .. import journal
from ..config import load_config
from ..constants import SessionPhase
from ..models import IST
from .learning.signal_report import format_report, rule_accuracy, suggested_weights
from .learning.view_outcomes import VIEW_OUTCOME_KIND
from .runner import LiveRunner
from .scanner import LiveScanner
from .services import build_live_services
from .universe import ReferenceData

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class SilentSink:
    """Stands in for alerts and storage during a diagnostic scan."""

    def send(self, *_args) -> bool:
        return False

    def record(self, *_args, **_kwargs) -> None:
        return None


def add_live_parser(subparsers) -> None:
    live = subparsers.add_parser("live", help="live F&O scanner and paper desk")
    actions = live.add_subparsers(dest="live_cmd", required=True)
    actions.add_parser("run", help="run during market hours (long-lived service)")
    once = actions.add_parser("scan-once", help="one scan now and print what it found (ignores the session clock)")
    once.add_argument("--json", action="store_true", help="print the full report as JSON")
    actions.add_parser("status", help="open trades, today's results, kill switch")
    kill = actions.add_parser("kill", help="close all paper trades and stop new ones")
    kill.add_argument("reason", nargs="?", default="manual stop")
    actions.add_parser("resume", help="release the kill switch")
    report = actions.add_parser("signal-report", help="how well each signal predicted the later price move")
    report.add_argument("--days", type=int, default=20, help="look back this many days")
    report.add_argument("--horizon", type=int, default=30, help="minutes after the view (30 or 90)")
    live.set_defaults(func=run_live_command)


def run_live_command(args) -> int:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    services = build_live_services(load_config(args.config))
    now = datetime.now(IST)
    if args.live_cmd == "run":
        LiveRunner(services).run_forever()
    elif args.live_cmd == "scan-once":
        return _scan_once(services, now, args.json)
    elif args.live_cmd == "status":
        _print_status(services, now)
    elif args.live_cmd == "kill":
        services.kill_switch.engage(args.reason, now)
        print(f"Kill switch engaged ({args.reason}). The running desk closes all paper trades within a minute.")
    elif args.live_cmd == "resume":
        services.kill_switch.release()
        print("Kill switch released. New trades are allowed again.")
    elif args.live_cmd == "signal-report":
        _print_signal_report(services, now, args.days, args.horizon)
    return 0


def _scan_once(services, now: datetime, as_json: bool) -> int:
    reference = ReferenceData.load(services.nse_feed, now.date())
    research = services.research_loader.load(now, services.clock.previous_session_close(now))
    # Diagnostic run: report what would be traded, but never open a trade outside the real session.
    report = LiveScanner(replace(services, alerts=SilentSink(), store=SilentSink())).run_cycle(
        now, SessionPhase.CLOSED, reference, research
    )
    if as_json:
        print(json.dumps(report.summary(), indent=1))
        return 0
    print(f"Universe {report.universe_size} · shortlisted {len(report.shortlisted)}: {', '.join(report.shortlisted)}")
    print(
        f"Research: regime {research.regime}, news on {len(research.news)} companies, "
        f"earnings dates {len(research.next_earnings)}"
    )
    for view in report.views:
        flag = f" BLOCKED: {'; '.join(view.block_reasons)}" if view.blocked else ""
        print(f"  {view.symbol:12s} {view.direction.value:8s} score {view.score:+.2f} agree {view.agreement:.0%}{flag}")
    for idea in report.ideas:
        print(
            f"IDEA {idea.contract_name}: {idea.lots} lot(s) @ {idea.entry_price:.2f} = Rs {idea.capital_used:,.0f}"
            f" · stop {idea.stop_price:.2f} · target {idea.target_price:.2f}"
            f" · would open: {report.rejected.get(idea.id, 'yes')}"
        )
    for key, reason in report.rejected.items():
        if key not in {i.id for i in report.ideas}:
            print(f"  skipped {key}: {reason}")
    for error in report.errors:
        print(f"  error: {error}")
    return 0


def _print_signal_report(services, now: datetime, days: int, horizon: int) -> None:
    learning = services.live_cfg.get("learning", {})
    outcomes = services.store.payloads(VIEW_OUTCOME_KIND, now.date() - timedelta(days=days))
    results = rule_accuracy(outcomes, horizon, learning.get("min_abs_score", 0.2))
    min_votes = learning.get("min_votes_for_verdict", 50)
    print(format_report(results, horizon, min_votes))
    print("\nSuggested weights (copy to config.yaml live.signals once rules have enough votes):")
    for rule, weight in suggested_weights(results, min_votes).items():
        print(f"  {rule}: {weight}")


def _print_status(services, now: datetime) -> None:
    trades = services.desk.trades()
    stats = journal.stats(trades)
    print(f"Kill switch: {'ENGAGED ' + services.kill_switch.reason if services.kill_switch.engaged else 'off'}")
    print(f"Session phase now: {services.clock.phase(now).value}")
    print(f"Open trades: {stats['open']} · money in open trades Rs {journal.deployed(trades):,.0f}")
    for t in services.desk.open_trades():
        mark = t.get("last_mark") or {}
        print(
            f"  {t['id']} {t.get('contract_name', t['candidate'])} x{t['lots']} unrealised Rs {mark.get('pnl', 0):,.0f}"
        )
    today = services.desk.closed_on(now.date())
    print(f"Closed today: {len(today)} · net Rs {sum(t['pnl_net'] for t in today):,.0f}")
    print(f"All closed: {stats['closed']} ({stats['win_rate']:.0f}% wins) · net Rs {stats['net']:,.0f}")
    print(f"Results stored at: {services.store.location}")
