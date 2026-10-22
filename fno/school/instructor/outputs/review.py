"""The 30-session descriptive review's input (story MS-INS, part e; 325 section 6.3b, 327 P2): per driver version, its
decisions' outcome codes (every denominator, refusals included), its account trades' rupees (net, maximum drawdown,
worst day, worst trade; tickets never summed in), its attribution sums and its causes; the paired rows; and every
session it could not read. Descriptive only: no claim, no licence."""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date

from ....models import IST
from ..contracts import Attribution, Classification, ClosedRead, PairedRow
from ..ports import InstructorKind, InstructorStore
from .comparison import SealedDecisions

ATTRIBUTION_PARTS = ("delta", "gamma", "vega", "theta", "residual", "charges", "spread", "net")


@dataclass(frozen=True)
class DriverSummary:
    driver_id: str
    outcomes: dict[str, int]  # decision outcome code -> count
    trades: int
    tickets: int
    net_rs: float  # account trades only
    max_drawdown_rs: float
    worst_day_rs: float | None
    worst_trade_rs: float | None
    attribution: dict[str, float]
    primary: dict[str, int]
    secondary: dict[str, int]
    not_testable: dict[str, int]
    modifiers: dict[str, int]
    poor_fit: int
    unclassified: int


@dataclass(frozen=True)
class Review:
    first: date
    last: date
    drivers: tuple[DriverSummary, ...]
    paired: tuple[PairedRow, ...]
    unreadable: tuple[date, ...]  # outcomes files that could not be read
    unsealed: tuple[date, ...]  # sessions without a readable decisions file
    orphans: int  # corrections naming no outcome
    sessions: list[date] = field(default_factory=list)


def latest_records(store: InstructorStore, sessions, kind: InstructorKind) -> dict[str, object]:
    """The latest record of each position over the sessions' files (a later correction replaces an earlier one)."""
    latest = {}
    for session in sessions:
        for record in store.read(session, kind) or ():
            latest[record.position_id] = record
    return latest


def driver_summary(driver_id: str, read: ClosedRead, outcomes: Counter, attributions: list[Attribution],
                   causes: list[Classification]) -> DriverSummary:  # fmt: skip
    mine = [p.outcome for p in read.paths if p.outcome.driver_id == driver_id]
    trades = [o for o in mine if not o.is_ticket]
    by_day: dict[date, float] = defaultdict(float)
    for o in trades:
        by_day[o.exit.filled_at.astimezone(IST).date()] += o.net
    return DriverSummary(
        driver_id=driver_id,
        outcomes=dict(sorted(outcomes.items())),
        trades=len(trades),
        tickets=len(mine) - len(trades),
        net_rs=round(sum(o.net for o in trades), 2),
        max_drawdown_rs=_drawdown([by_day[d] for d in sorted(by_day)]),
        worst_day_rs=min(by_day.values(), default=None),
        worst_trade_rs=min((o.net for o in trades), default=None),
        attribution={part: round(sum(getattr(a, part) for a in attributions), 2) for part in ATTRIBUTION_PARTS},
        primary=_tally(c.primary for c in causes if c.primary),
        secondary=_tally(cause for c in causes for cause in c.secondary),
        not_testable=_tally(cause for c in causes for cause in c.not_testable),
        modifiers=_tally(c.modifier for c in causes),
        poor_fit=sum(a.poor_fit for a in attributions),
        unclassified=sum(c.primary is None for c in causes),
    )


def build_review(first: date, last: date, sessions: list[date], read: ClosedRead, decisions: SealedDecisions,
                 store: InstructorStore, paired: tuple[PairedRow, ...], orphans: int) -> Review:  # fmt: skip
    attributions = latest_records(store, sessions, InstructorKind.ATTRIBUTION).values()
    causes = latest_records(store, sessions, InstructorKind.CAUSES).values()
    counts = decisions.outcome_counts()
    drivers = sorted(set(counts) | {p.outcome.driver_id for p in read.paths})
    summaries = tuple(driver_summary(d, read, counts.get(d, Counter()),
                                     [a for a in attributions if a.driver_id == d],
                                     [c for c in causes if c.driver_id == d]) for d in drivers)  # fmt: skip
    return Review(first, last, summaries, paired, read.unreadable, decisions.unsealed, orphans, sessions)


def _drawdown(daily: list[float]) -> float:
    peak = equity = worst = 0.0
    for change in daily:
        equity += change
        peak = max(peak, equity)
        worst = min(worst, equity - peak)
    return round(worst, 2)


def _tally(values) -> dict[str, int]:
    return dict(sorted(Counter(str(v) for v in values).items()))
