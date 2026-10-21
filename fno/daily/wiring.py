"""Composition root of the daily run (story O1): E3's desk run (Book 1's orders and exit rules) with O1's steps
around it: A14c's margin check, the weather, the v4 forecasts and the card as their own commands, each from its
`daily.live_from` date; Book 1's decision (E5) right after the pack; and A4c's quote parts beside the desk, committed
through E3's committer in the run's one thread."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date
from pathlib import Path

from ..config import ROOT
from ..constants import CARD_DELIVERIES_FOLDER, OWNER_TIMING_STEP, PLAYBOOK_FOLDER, REVIEWS_STEP
from ..desk.daily_ports import DayStep
from .runner import DayRunner

V4_RECORDS = "research/forecasts/v4/"  # G7's rows and M1's weather records (`fno/forecast_v4_rules/wiring.py`)
WEATHER = ("weather", "capture")  # today only, before its cutoff
FORECASTS_V4 = ("forecast-v4", "capture")  # today only, before its cutoff
MARGIN_CHECK = ("margins", "stress-broker-check")  # A14c: idempotent, read-only Groww, done long before 14:55
MARGIN_CHECKS = "research/data/margins/stress_broker_check.csv"  # the one file it appends to (A14c builder, 15 Oct)
LIVE_STEPS = ("margin_check", "weather", "forecasts_v4", "card", OWNER_TIMING_STEP)


def live_dates(cfg: dict) -> dict[str, date | None]:
    """`daily.live_from`: each O1 step's first live date; a step without one is not live."""
    raw = cfg.get("daily", {}).get("live_from", {}) or {}
    return {name: date.fromisoformat(str(raw[name])) if raw.get(name) else None for name in LIVE_STEPS}


def build_day_runner(cfg: dict, root: Path = ROOT, sleep: Callable[[float], None] = time.sleep) -> DayRunner:
    """`sleep` is how the run waits (story O2: the end-to-end suite drives the whole day on a fake clock)."""
    from ..books.book1_wiring import build_book1_exit_rules, build_book1_orders
    from ..composition import build_alert_sender
    from ..desk.daily_wiring import build_daily_run
    from ..desk.git_limit import GitLocks
    from ..desk.git_sync import Git, GitCommitter
    from ..desk.owner_timing.wiring import build_owner_timing_desks, build_owner_timing_step
    from ..desk.wiring import build_entry_desk, build_execution_snapshots
    from ..intraday.backfill_daily import CATCH_UP_COMMAND, CATCH_UP_FROM, candle_folders
    from ..models import now_ist
    from ..scorecard.wiring import build_scorecard_run
    from .alerts import ReportedAlerts
    from .history import WholeHistory
    from .processes import ChildProcesses
    from .quote_parts import QUOTE_PARTS, QuoteParts
    from .quote_steps import FinishQuoteParts, ServicingWaiter, StartQuoteParts
    from .reviews import ReviewsStep, ScorecardReview
    from .steps import Alerted, CommandStep, LiveFrom, NotBefore

    git, alerts, processes, live = (
        Git(root),
        ReportedAlerts(build_alert_sender()),
        ChildProcesses(root),
        live_dates(cfg),
    )
    locks = GitLocks(root)  # story O2: a command stopped at its limit leaves no git lock behind
    parts = QuoteParts(QUOTE_PARTS, processes, GitCommitter(git), git.changed, alerts, now_ist)
    waiter = ServicingWaiter(parts, now_ist, sleep)

    def waiting(seconds: float) -> None:
        """A command's wait: a quote part due meanwhile starts (no git: the commits stay between the steps)."""
        sleep(seconds)
        parts.start_due()

    def command(arguments: Callable[[date], tuple[str, ...]], folder: str) -> DayStep:
        return CommandStep(processes, arguments, (folder,), git.changed, waiting, locks)

    card = command(lambda day: ("card", "daily", "--on", day.isoformat(), "--post"), CARD_DELIVERIES_FOLDER)
    steps = {
        "margin_check": Alerted(
            "margin_check", LiveFrom(command(lambda day: MARGIN_CHECK, MARGIN_CHECKS), live["margin_check"]), alerts
        ),  # A14c's command does not exist yet: live from the date its code lands
        "weather": Alerted("weather", LiveFrom(command(lambda day: WEATHER, V4_RECORDS), live["weather"]), alerts),
        "forecasts_v4": Alerted(
            "forecasts_v4", LiveFrom(command(lambda day: FORECASTS_V4, V4_RECORDS), live["forecasts_v4"]), alerts
        ),  # fmt: skip
        "quotes": Alerted("quotes", StartQuoteParts(parts), alerts),
        "book1": Alerted(
            "book1",
            CommandStep(
                processes, lambda day: ("desk", "book1", "--day", day.isoformat()), (), git.changed, waiting, locks
            ),
            alerts,
        ),  # E5: commits its own decision  # fmt: skip
        REVIEWS_STEP: Alerted(
            REVIEWS_STEP,
            ReviewsStep(
                (ScorecardReview(build_scorecard_run(cfg, root, alerts)),),
                build_execution_snapshots(),
                root,
                git.changed,
                (f"{PLAYBOOK_FOLDER}/",),
            ),
            alerts,
        ),  # E6's pauses  # fmt: skip
        "quotes_done": Alerted("quotes_done", FinishQuoteParts(parts, waiter), alerts, status_alerts=False),
        "card": Alerted("card", LiveFrom(card, live["card"]), alerts),
        "candles": Alerted(
            "candles",
            NotBefore(
                CommandStep(processes, lambda day: CATCH_UP_COMMAND, candle_folders(), git.changed, waiting, locks),
                CATCH_UP_FROM,
                waiter,
            ),
            alerts,
        ),  # A16b-d: yesterday's candles, after A16's last mark
    }
    cfg_orders, exit_rules = build_book1_orders(cfg, root), build_book1_exit_rules(root, alerts)
    entry_desk, exit_timing = build_owner_timing_desks(cfg, live[OWNER_TIMING_STEP], build_entry_desk(cfg))
    fills = build_owner_timing_step(cfg, alerts, exit_timing, live[OWNER_TIMING_STEP], root=root)
    steps[OWNER_TIMING_STEP] = Alerted(OWNER_TIMING_STEP, fills, alerts)  # E8: seals only before its live date
    daily_run = build_daily_run(cfg, cfg_orders, exit_rules, root=root, waiter=waiter, day_steps=steps, git=git,
                                alerts=alerts, entry_desk=entry_desk, exit_timing=exit_timing)  # fmt: skip
    return DayRunner(daily_run, parts, waiter, WholeHistory(git, alerts))
