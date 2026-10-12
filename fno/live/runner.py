"""The market-hours loop: refresh data, scan for entries, manage exits, and report. Runs as a long-lived service."""

from __future__ import annotations

import logging
import threading
import time as wall_clock
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from ..constants import EVENT_SHADOW_CLOSED, ExitReason, SessionPhase
from ..models import IST
from .alerts import day_summary_message, exit_message
from .learning.performance import performance_stop_reason
from .learning.view_outcomes import ViewOutcomeTracker
from .research.research_context import ResearchSnapshot
from .scanner import LiveScanner
from .services import LiveServices, build_news_watcher
from .universe import ReferenceData

log = logging.getLogger(__name__)
NEWS_WATCHER_DOWN = "news watcher stopped: news guard and news exit are off until the desk restarts"

ACTIVE_PHASES = (SessionPhase.OPENING_RANGE, SessionPhase.TRADING, SessionPhase.NO_NEW_ENTRIES, SessionPhase.SQUARE_OFF)


@dataclass(frozen=True)
class LoopTimings:
    scan_every_seconds: int = 180
    review_every_seconds: int = 60
    research_every_minutes: int = 30
    idle_sleep_seconds: int = 60
    problem_alert_every_minutes: int = 15

    @classmethod
    def from_config(cls, cfg: dict) -> LoopTimings:
        return cls(**{k: v for k, v in (cfg or {}).items() if k in cls.__dataclass_fields__})


@dataclass
class DayState:
    """Per-day bookkeeping, reset each trading day."""

    day: date
    scans: int = 0
    ideas: int = 0
    summary_sent: bool = False
    kill_reported: bool = False
    last_scan: datetime | None = None
    last_review: datetime | None = None
    last_problem_alert: datetime | None = None
    seen_ideas: set[str] = field(default_factory=set)


class LiveRunner:
    def __init__(self, services: LiveServices):
        self.services = services
        self.scanner = LiveScanner(services)
        self.timings = LoopTimings.from_config(services.live_cfg.get("timings"))
        self.outcomes = ViewOutcomeTracker(
            services.store, tuple(services.live_cfg.get("learning", {}).get("horizons_minutes", (30, 90)))
        )
        self.reference: ReferenceData | None = None
        self.research = ResearchSnapshot()
        self.state = DayState(day=date.min)
        self.news_watcher = None
        self._stop_news = threading.Event()
        self._news_thread: threading.Thread | None = None
        self._news_down_reported = False

    def run_forever(self) -> None:
        log.info("live desk started; results stored at %s", self.services.store.location)
        try:
            self._start_day_if_needed(datetime.now(IST))  # holidays known before the news watcher starts
        except Exception:  # noqa: BLE001 - the first tick retries; the watcher then falls back to weekdays
            log.exception("could not load today's reference data before starting the news watcher")
        self._start_news_watcher()
        while True:
            self.tick(datetime.now(IST))
            wall_clock.sleep(self.timings.idle_sleep_seconds // 4 or 1)

    def _start_news_watcher(self) -> None:
        """The news watcher runs beside the desk in its own thread, one request at a time."""
        watcher = build_news_watcher(self.services)
        if watcher is None:
            return
        self.news_watcher = watcher
        self._news_thread = threading.Thread(
            target=watcher.run_forever, args=(self._stop_news,), name="news-watcher", daemon=True
        )
        self._news_thread.start()
        log.info("news watcher started with %d sources", len(watcher.schedule.plans))

    def tick(self, now: datetime) -> None:
        """One pass of the loop. Safe to call as often as you like: each job runs only when it is due."""
        try:
            self._start_day_if_needed(now)
            self._check_news_watcher(now)
            phase = self.services.clock.phase(now)
            if self.services.kill_switch.engaged:
                self._handle_kill_switch(now)
                return
            if phase in ACTIVE_PHASES:
                self._review_if_due(now, phase)
                self._scan_if_due(now, phase)
            elif phase is SessionPhase.CLOSED and now.time() > self.services.clock.times.market_close:
                self._send_day_summary_once(now)
        except Exception as exc:
            log.exception("tick failed")
            self._report_problem(now, f"{type(exc).__name__}: {exc}")

    def _check_news_watcher(self, now: datetime) -> None:
        """A dead watcher silently switches off the news guard and exit: say so once."""
        if self._news_thread is None or self._news_thread.is_alive() or self._news_down_reported:
            return
        self._news_down_reported = True
        self._report_problem(now, NEWS_WATCHER_DOWN)

    def _start_day_if_needed(self, now: datetime) -> None:
        today = now.date()
        if self.state.day == today:
            return
        self.state = DayState(day=today)
        self.outcomes.end_of_day()
        if self.services.iv_history is not None:
            self.services.iv_history.flush(now)  # readings of a day that ended early, under their own day
        self.reference = ReferenceData.load(self.services.nse_feed, today)
        self.services.clock.holidays = self.reference.holidays
        self.services.gate.industries = self.reference.industries
        log.info(
            "new day %s: %d F&O underlyings, %d banned", today, len(self.reference.symbols), len(self.reference.banned)
        )

    def _research(self, now: datetime) -> ResearchSnapshot:
        loaded = self.research.loaded_at
        if loaded is None or now - loaded >= timedelta(minutes=self.timings.research_every_minutes):
            news_since = self.services.clock.previous_session_close(now)
            self.research = self.services.research_loader.load(now, news_since)
        return self.research

    def _scan_if_due(self, now: datetime, phase: SessionPhase) -> None:
        if phase is not SessionPhase.TRADING or not self._due(
            self.state.last_scan, now, self.timings.scan_every_seconds
        ):
            return
        self.state.last_scan = now
        report = self.scanner.run_cycle(now, phase, self.reference, self._research(now))
        self.outcomes.observe(report)
        self.state.scans += 1
        new_ideas = {i.id for i in report.ideas} - self.state.seen_ideas
        self.state.ideas += len(new_ideas)
        self.state.seen_ideas |= new_ideas
        if report.errors and not report.shortlisted:
            self._report_problem(now, "; ".join(report.errors[:3]))
        log.info(
            "scan %s: shortlisted %d, ideas %d, opened %s",
            now.strftime("%H:%M"),
            len(report.shortlisted),
            len(report.ideas),
            report.opened,
        )

    def _review_if_due(self, now: datetime, phase: SessionPhase) -> None:
        if not self._due(self.state.last_review, now, self.timings.review_every_seconds):
            return
        self.state.last_review = now
        closed, errors = self.services.desk.review_open_trades(now, phase)
        try:
            if self.services.news_exit is not None:
                news_closed, news_errors = self.services.news_exit.close_hit(self.services.desk, now)
                closed, errors = closed + news_closed, errors + news_errors
        finally:  # closes already made are always recorded, alerted and checked against the kill switch
            for trade in closed:
                self.services.store.record("closed", trade, now, trade["underlying"])
                self.services.alerts.send(exit_message(trade))
            if errors:
                self._report_problem(now, "could not re-price or close: " + "; ".join(errors[:3]))
            if closed:
                self._stop_if_performance_breaks(now)
        self._review_shadow_book(now, phase)

    def _review_shadow_book(self, now: datetime, phase: SessionPhase) -> None:
        """Same exit rules for the shadow book (news exit included), recorded quietly: no alerts, no kill switch."""
        shadow_desk = self.services.shadow_desk
        if shadow_desk is None:
            return
        closed, _ = shadow_desk.review_open_trades(now, phase)
        if self.services.news_exit is not None:
            closed += self.services.news_exit.close_hit(shadow_desk, now)[0]
        for trade in closed:
            self.services.store.record(EVENT_SHADOW_CLOSED, trade, now, trade["underlying"])

    def _stop_if_performance_breaks(self, now: datetime) -> None:
        """A losing run or deep drawdown stops everything until a person reviews it (kill switch)."""
        reason = performance_stop_reason(
            self.services.desk.trades(), self.services.cfg, since=self.services.kill_switch.released_at
        )
        if reason and not self.services.kill_switch.engaged:
            self.services.kill_switch.engage(f"automatic: {reason}", now)

    def _handle_kill_switch(self, now: datetime) -> None:
        if self.state.kill_reported:
            return
        closed = self.services.desk.close_all(ExitReason.KILL_SWITCH)
        for trade in closed:
            self.services.store.record("closed", trade, now, trade["underlying"])
        self.services.store.record(
            "kill_switch", {"reason": self.services.kill_switch.reason, "closed": len(closed)}, now
        )
        self.services.alerts.kill_switch()
        self.state.kill_reported = True

    def _send_day_summary_once(self, now: datetime) -> None:
        if self.state.summary_sent or not self.services.clock.is_trading_day(now.date()):
            return
        if self.services.iv_history is not None:
            self.services.iv_history.flush(now)
        desk = self.services.desk
        message = day_summary_message(
            now.date(), desk.closed_on(now.date()), desk.open_trades(), self.state.scans, self.state.ideas
        )
        self.services.alerts.send(message)
        self.state.summary_sent = True

    def _report_problem(self, now: datetime, message: str) -> None:
        if self._due(self.state.last_problem_alert, now, self.timings.problem_alert_every_minutes * 60):
            self.state.last_problem_alert = now
            self.services.alerts.problem(message)

    @staticmethod
    def _due(last: datetime | None, now: datetime, every_seconds: int) -> bool:
        return last is None or (now - last).total_seconds() >= every_seconds
