"""One scan cycle: universe → backdrop → shortlist → signals → contract → risk gate → paper trade."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from ..constants import BENCHMARK_UNDERLYING, Direction, SessionPhase
from ..models import OptionChain
from .alerts import entry_message
from .market_backdrop import MarketBackdrop, build_market_backdrop
from .models import Candle, MarketView, ScanReport, UnderlyingSnapshot, as_record
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
    backdrop: MarketBackdrop


def split_sessions(candles: list[Candle]) -> tuple[list[Candle], list[Candle]]:
    """(latest session's candles, earlier sessions' candles)."""
    if not candles:
        return [], []
    latest_day = candles[-1].start.date()
    return [c for c in candles if c.start.date() == latest_day], [c for c in candles if c.start.date() != latest_day]


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
        report.prices = {sym: snap.last_price for sym, snap in snapshots.items()}
        benchmark = snapshots.get(BENCHMARK_UNDERLYING)
        context = CycleContext(
            now,
            phase,
            reference,
            research,
            benchmark.day_change_pct if benchmark else None,
            self._backdrop(snapshots, report),
        )
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

    def _backdrop(self, snapshots: dict[str, UnderlyingSnapshot], report: ScanReport) -> MarketBackdrop:
        try:
            return build_market_backdrop(self.services.price_feed, snapshots)
        except Exception as exc:  # sector and global context is helpful, not essential
            report.errors.append(f"market backdrop failed: {exc}")
            return MarketBackdrop()

    def _examine(self, snapshot: UnderlyingSnapshot, context: CycleContext, report: ScanReport) -> None:
        s, symbol, now = self.services, snapshot.symbol, context.now
        today, history = split_sessions(s.price_feed.candles(symbol))
        chain = self._chain(symbol, context.reference, now.date(), report)
        inputs = SymbolInputs(
            symbol=symbol,
            snapshot=snapshot,
            candles=today,
            benchmark_change_pct=context.benchmark_change_pct,
            research=context.research,
            banned=context.reference.banned,
            now=now,
            history=history,
            chain=chain,
            backdrop=context.backdrop,
            industry=context.reference.industries.get(symbol),
        )
        view = s.view_builder.build(inputs)
        report.views.append(view)
        if view.blocked or view.direction is Direction.NEUTRAL or chain is None:
            return
        self._trade_if_allowed(view, chain, context, report)

    def _trade_if_allowed(
        self, view: MarketView, chain: OptionChain, context: CycleContext, report: ScanReport
    ) -> None:
        s, now, symbol = self.services, context.now, view.symbol
        idea, reason = s.picker.pick(view, chain, now.date())
        if idea is None:
            report.rejected[symbol] = reason
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

    def _chain(self, symbol: str, reference: ReferenceData, today: date, report: ScanReport) -> OptionChain | None:
        """The chain of the expiry a trade would use, fetched before the view so option signals can read it."""
        s = self.services
        expiry = choose_expiry(self._expiries_for(symbol, today), today, s.live_cfg.get("min_days_to_expiry", 4))
        if expiry is None:
            report.rejected[symbol] = "no expiry far enough away"
            return None
        chain = s.chain_source.chain(symbol, expiry)
        chain.lot_size = reference.lot_sizes.get(symbol, chain.lot_size)
        return chain

    def _expiries_for(self, symbol: str, today: date) -> list[date]:
        key = (symbol, today)
        if key not in self._expiries:
            self._expiries[key] = self.services.chain_source.expiries(symbol)
        return self._expiries[key]
