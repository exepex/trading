"""Composition root of the daily run (story O1): E3's desk run (Book 1's orders and exit rules) with O1's steps
around it: A14c's margin check, the weather, the v4 forecasts and the card as their own commands, each from its
`daily.live_from` date; the AI books' fire right after the pack and their collection after Book 1's decision (E5),
each AI book from its own `daily.live_from` date with its own orders and exit rules (story F1t); and A4c's quote
parts beside the desk, committed through E3's committer in the run's one thread."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

from ..config import ROOT
from ..constants import BOOK1_RULES, BOOK2_HYBRID, BOOK3_AI, CARD_DELIVERIES_FOLDER, PLAYBOOK_FOLDER, REVIEWS_STEP
from ..desk.daily_ports import DayStep
from .runner import DayRunner

V4_RECORDS = "research/forecasts/v4/"  # G7's rows and M1's weather records (`fno/forecast_v4_rules/wiring.py`)
WEATHER = ("weather", "capture")  # today only, before its cutoff
FORECASTS_V4 = ("forecast-v4", "capture")  # today only, before its cutoff
MARGIN_CHECK = ("margins", "stress-broker-check")  # A14c: idempotent, read-only Groww, done long before 14:55
MARGIN_CHECKS = "research/data/margins/stress_broker_check.csv"  # the one file it appends to (A14c builder, 15 Oct)
LIVE_STEPS = ("margin_check", "weather", "forecasts_v4", "card")
LIVE_BOOKS = (BOOK2_HYBRID, BOOK3_AI)  # story F1t: each AI book's first trading day; null: not in the desk at all


def live_dates(cfg: dict) -> dict[str, date | None]:
    """`daily.live_from`: each O1 step's first live date; a step without one is not live."""
    raw = cfg.get("daily", {}).get("live_from", {}) or {}
    return {name: date.fromisoformat(str(raw[name])) if raw.get(name) else None for name in LIVE_STEPS}


def live_ai_books(cfg: dict, day: date) -> tuple[str, ...]:
    """The AI books live on `day` (`daily.live_from.<book>` on or before it); a key `daily.live_from` does not know is
    refused, so a typo can never leave a book silently off (O1 builder, 16 Oct)."""
    raw = cfg.get("daily", {}).get("live_from", {}) or {}
    unknown = sorted(set(raw) - set(LIVE_STEPS) - set(LIVE_BOOKS))
    if unknown:
        raise ValueError(f"config.yaml daily.live_from: unknown {', '.join(unknown)}; known: {LIVE_STEPS + LIVE_BOOKS}")
    return tuple(b for b in LIVE_BOOKS if raw.get(b) and date.fromisoformat(str(raw[b])) <= day)


def build_day_runner(cfg: dict, root: Path = ROOT, day: date | None = None) -> DayRunner:
    """`day`: the session the run is for (its AI books are those live that day; none when not given)."""
    from ..ai_trading.book_dispatch import ExitRulesByBook, OrdersByBook
    from ..ai_trading.wiring import build_ai_steps, build_book_parts
    from ..books.book1_wiring import build_book1_exit_rules, build_book1_orders
    from ..composition import build_alert_sender
    from ..desk.daily_wiring import build_daily_run
    from ..desk.git_sync import Git, GitCommitter
    from ..desk.wiring import build_execution_snapshots
    from ..models import now_ist
    from ..scorecard.wiring import build_scorecard_run
    from .alerts import ReportedAlerts
    from .history import WholeHistory
    from .processes import ChildProcesses
    from .quote_parts import QUOTE_PARTS, QuoteParts
    from .quote_steps import FinishQuoteParts, ServicingWaiter, StartQuoteParts
    from .reviews import ReviewsStep, ScorecardReview
    from .steps import Alerted, CommandStep, LiveFrom

    git, alerts, processes, live = (
        Git(root),
        ReportedAlerts(build_alert_sender()),
        ChildProcesses(root),
        live_dates(cfg),
    )
    parts = QuoteParts(QUOTE_PARTS, processes, GitCommitter(git), git.changed, alerts, now_ist)
    waiter = ServicingWaiter(parts, now_ist)

    def command(arguments: Callable[[date], tuple[str, ...]], folder: str) -> DayStep:
        return CommandStep(processes, arguments, (folder,), git.changed)

    card = command(lambda day: ("card", "daily", "--on", day.isoformat(), "--post"), CARD_DELIVERIES_FOLDER)
    ai_books = live_ai_books(cfg, day) if day else ()
    book_parts = build_book_parts(cfg, root, alerts, ai_books)
    live_on = lambda run_day: ai_books if run_day == day else ()  # noqa: E731 - the books live on the built day
    ai_steps = build_ai_steps(cfg, root, live_on, book_parts, processes, waiter, git, now_ist)
    steps = {
        "margin_check": Alerted(
            "margin_check", LiveFrom(command(lambda day: MARGIN_CHECK, MARGIN_CHECKS), live["margin_check"]), alerts
        ),  # A14c's command does not exist yet: live from the date its code lands
        "weather": Alerted("weather", LiveFrom(command(lambda day: WEATHER, V4_RECORDS), live["weather"]), alerts),
        "forecasts_v4": Alerted(
            "forecasts_v4", LiveFrom(command(lambda day: FORECASTS_V4, V4_RECORDS), live["forecasts_v4"]), alerts
        ),  # fmt: skip
        "quotes": Alerted("quotes", StartQuoteParts(parts), alerts),
        **{name: Alerted(name, step, alerts) for name, step in ai_steps.items()},  # story F1t
        "book1": Alerted(
            "book1",
            CommandStep(processes, lambda day: ("desk", "book1", "--day", day.isoformat()), (), git.changed),
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
    }
    orders = OrdersByBook({BOOK1_RULES: build_book1_orders(cfg), **{b: p.orders for b, p in book_parts.items()}})
    exits = ExitRulesByBook(
        {BOOK1_RULES: build_book1_exit_rules(root, alerts), **{b: p.exits for b, p in book_parts.items()}}
    )
    daily_run = build_daily_run(cfg, orders, exits, books=(BOOK1_RULES, *ai_books), root=root, waiter=waiter,
                                day_steps=steps, git=git, alerts=alerts)  # fmt: skip
    return DayRunner(daily_run, parts, waiter, WholeHistory(git, alerts))
