"""Story E5 fixtures: Book 1 over D2's and D3's test builders (a fixed market, features and book), a committer that
remembers when each path was committed, and a git view built from it, so E3's real D3 reader sees the commits."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from fno.books.book1 import PENDING_MARKER, Book1, Book1Day, Book1Inputs
from fno.books.decided_runs import ON_DISK, ON_ORIGIN, DecidedRuns, FoundRun
from fno.composition import build_session_calendar, build_structures
from fno.constants import BOOK1_RULES
from fno.desk.daily_ports import Committer
from fno.desk.pending_commit import PendingCommitter
from fno.playbook.allocation import Allocator
from fno.playbook.candidates import CandidateBuilder
from fno.playbook.decision_run import DecisionRun
from fno.playbook.decision_store import INPUTS_FILE, DecisionStore
from fno.playbook.evaluate import RuleEvaluator
from fno.playbook.opportunities import OpportunityFinder
from fno.research_engine.cycles import TradingDays
from fno.risk.manager import RiskManager
from fno.risk.rules import MaxLossPerTrade, MaxOpenTrades
from tests.checks.builders import CALENDAR
from tests.decisions.builders import CONTEXT
from tests.playbook.evaluation_builders import COSTS, LOT, REAL, Counts, FixedValues, OwnShadowBooks, chain_market
from tests.risk.builders import book

DAYS = (date(2026, 10, 13), date(2026, 10, 14), date(2026, 10, 15))  # three fixture session days


def priced_evaluator() -> RuleEvaluator:
    """D2's test evaluator with C2 pricing the approved entry, as the app's wiring does (E4's entry limit needs it)."""
    risk = RiskManager((MaxLossPerTrade(COSTS, 10_000), MaxOpenTrades(3)), {}, COSTS)
    builder = CandidateBuilder({s.code: s for s in build_structures()}, COSTS, 10_000, LOT)
    return RuleEvaluator(
        OpportunityFinder(TradingDays(build_session_calendar())), builder, Allocator(risk, COSTS), REAL
    )


class FixedInputs(Book1Inputs):
    """The same market every day (D2's fixture chain, its expiry 45 days after 13 Oct)."""

    def day(self, day: date) -> Book1Day:
        return Book1Day(chain_market(day=day), FixedValues(), book(), Counts(), OwnShadowBooks(), CONTEXT)


class Commits(Committer):
    def __init__(self, clock):
        self.clock, self.made = clock, []

    def commit(self, paths, message, own_unpushed=None):
        commit = f"{len(self.made) + 1:040x}"
        self.made.append((commit, self.clock(), tuple(paths), message))
        return commit

    def added_in(self, path: str):
        """(commit, committer time) of the first commit holding `path` (a run's records.sha256)."""
        for commit, moment, paths, _ in self.made:
            if path.startswith(f"journal/{BOOK1_RULES}/decisions/") and any(str(p).endswith(path) for p in paths):
                return commit, moment.isoformat()
        return None

    def observed(self):
        return f"origin-{len(self.made)}"


class DiskRuns(DecidedRuns):
    """Book 1's runs on disk, each "on origin" once `commits` has committed it (no git in these fixtures)."""

    def __init__(self, root, commits: Commits):
        self.store, self.commits = DecisionStore(root, BOOK1_RULES), commits

    def find(self, day):
        committed = {Path(p).parent.name for _, _, paths, _ in self.commits.made for p in paths}
        return [FoundRun(run.name, ON_ORIGIN if run.name in committed else ON_DISK, (run / INPUTS_FILE).read_bytes())
                for run in self.store.runs(day)]  # fmt: skip


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "sent"


def book1(root, playbook, clock, inputs=None, validator=None, alerts=None) -> tuple[Book1, Commits]:
    commits = Commits(clock)
    run = DecisionRun(priced_evaluator(), DecisionStore(root, BOOK1_RULES), validator)
    committer = PendingCommitter(commits, root, PENDING_MARKER)
    decider = Book1(root, CALENDAR, lambda: playbook, inputs or FixedInputs(), run, committer, DiskRuns(root, commits),
                    alerts or Alerts())  # fmt: skip
    return decider, commits


def git_book1(root, playbook, run, alerts=None, inputs=None) -> Book1:
    """Book 1 as the app wires it, on a real git checkout: E2b's committer with Book 1's marker, origin checked."""
    from fno.books.book1_wiring import build_book1_commits

    committer, decided = build_book1_commits(root)
    return Book1(root, CALENDAR, lambda: playbook, inputs or FixedInputs(), run, committer, decided,
                 alerts or Alerts())  # fmt: skip


def clock_at(moment: datetime):
    now = {"t": moment}

    def clock():
        return now["t"]

    clock.set = lambda t: now.update(t=t)  # type: ignore[attr-defined]
    return clock


EXITS = {"time": "21 days to expiry", "profit": "none", "loss": "none", "event": "none"}


def book1_doc(name: str = "sc-a", **changes) -> dict:
    """A paper version whose exits code can apply: the time exit only (the others "none")."""
    from tests.decisions.builders import doc

    return doc(name, **{"exits": EXITS, **changes})
