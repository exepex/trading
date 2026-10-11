"""One scan cycle: universe → shortlist → signals → contract → risk gate → paper trade."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from ..constants import BENCHMARK_UNDERLYING, Direction, SessionPhase
from .alerts import entry_message
from .models import MarketView, ScanReport, TradeIdea, UnderlyingSnapshot, as_record
from .research.research_context import ResearchSnapshot
from .services import LiveServices
from .shortlist import build_shortlist
from .signals.base import SymbolInputs
from .universe import ReferenceData, build_snapshots, choose_expiry

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CycleContext:
    """What stays fixed during one scan cycle."""

    now: datetime
    phase: SessionPhase
    reference: ReferenceData
    research: ResearchSnapshot
    benchmark_change_pct: float | None


class LiveScanner:
    def __init__(self, services: LiveServices):
        self.services = services
        self._expiries: dict[tuple[str, date], list[date]] = {}  # (symbol, day) -> expiries, fetched once a day

    def run_cycle(
        self, now: datetime, phase: SessionPhase, reference: ReferenceData, research: ResearchSnapshot
    ) -> ScanReport:
        s = self.services
        report = ScanReport(started_at=now, universe_size=len(reference.symbols))
        snapshots = self._snapshots(reference, report)
        if not snapshots:
            return report
        benchmark = snapshots.get(BENCHMARK_UNDERLYING)
        context = CycleContext(now, phase, reference, research, benchmark.day_change_pct if benchmark else None)
        held = {t["underlying"] for t in s.desk.open_trades()}
        report.shortlisted = build_shortlist(
            snapshots,
            s.shortlist_rules,
            excluded=reference.banned | held,
            always_include=tuple(s.live_cfg.get("always_scan", ())),
        )
        for symbol in report.shortlisted:
            try:
                self._examine(snapshots[symbol], context, report)
            except Exception as exc:  # one symbol's bad data must not end the cycle
                log.warning("examining %s failed: %s", symbol, exc)
                report.errors.append(f"{symbol}: {exc}")
        s.store.record("scan", report.summary(), now)
        return report

    def _snapshots(self, reference: ReferenceData, report: ScanReport) -> dict[str, UnderlyingSnapshot]:
        s = self.services
        try:
            quotes = s.price_feed.day_quotes(reference.symbols)
            oi_moves = s.nse_feed.open_interest_moves()
        except Exception as exc:
            report.errors.append(f"market snapshot failed: {exc}")
            return {}
        return build_snapshots(reference.symbols, quotes, oi_moves)

    def _examine(self, snapshot: UnderlyingSnapshot, context: CycleContext, report: ScanReport) -> None:
        s, symbol, now = self.services, snapshot.symbol, context.now
        inputs = SymbolInputs(
            symbol=symbol,
            snapshot=snapshot,
            candles=s.price_feed.candles(symbol),
            benchmark_change_pct=context.benchmark_change_pct,
            research=context.research,
            banned=context.reference.banned,
            now=now,
        )
        view = s.view_builder.build(inputs)
        report.views.append(view)
        if view.blocked or view.direction is Direction.NEUTRAL:
            return
        idea = self._idea(view, context.reference, now.date(), report)
        if idea is None:
            return
        report.ideas.append(idea)
        s.store.record("idea", as_record(idea), now, symbol)
        refusal = s.gate.refusal(idea, s.desk.trades(), context.phase, now)
        if refusal:
            report.rejected[idea.id] = refusal
            s.store.record("rejected", {"idea": idea.id, "reason": refusal}, now, symbol)
            return
        trade = s.desk.open(idea, note=f"live scan {now:%H:%M}")
        report.opened.append(trade["id"])
        s.store.record("opened", trade, now, symbol)
        s.alerts.send(entry_message(idea, trade["id"]))

    def _idea(self, view: MarketView, reference: ReferenceData, today: date, report: ScanReport) -> TradeIdea | None:
        s = self.services
        expiry = choose_expiry(self._expiries_for(view.symbol, today), today, s.live_cfg.get("min_days_to_expiry", 4))
        if expiry is None:
            report.rejected[view.symbol] = "no expiry far enough away"
            return None
        chain = s.chain_source.chain(view.symbol, expiry)
        chain.lot_size = reference.lot_sizes.get(view.symbol, chain.lot_size)
        idea, reason = s.picker.pick(view, chain, today)
        if idea is None:
            report.rejected[view.symbol] = reason
        return idea

    def _expiries_for(self, symbol: str, today: date) -> list[date]:
        key = (symbol, today)
        if key not in self._expiries:
            self._expiries[key] = self.services.chain_source.expiries(symbol)
        return self._expiries[key]
