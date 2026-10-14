"""Book 1's exit rules (story E5, E3's `ExitRules` seam): each open trade exits by its playbook version's time exit,
the trading day D2 computed for its expiry (`OpportunityFinder.exit_day`). E4 applies it; when C3 finds the prices
unverified, E4 records the due exit as pending until valid quotes. A version's other exits are free text today: one
that is not "none" cannot be applied by code, so it is refused, never silently ignored."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from ..desk.daily_ports import ExitRules
from ..desk.exit_rules import ExitOnDay, ExitRule
from ..desk.records import DeskRecords
from ..desk.status import open_positions
from ..desk.trade_counts import version_key
from ..playbook.loader import PlaybookLoader
from ..playbook.opportunities import OpportunityFinder
from ..playbook.schema import Strategy

TEXT_EXITS = ("profit", "loss", "event")
NO_EXIT = "none"


class ExitNotApplicable(ValueError):
    """A version's exit that code cannot apply (free text other than "none"): the owner must restate it."""


def time_exit_only(strategy: Strategy) -> None:
    written = {k: str(strategy.exits.get(k, "")) for k in TEXT_EXITS}
    other = [f"{k}: {text}" for k, text in written.items() if not text.strip().lower().startswith(NO_EXIT)]
    if other:
        raise ExitNotApplicable(f"{strategy.file_name}: exits code cannot apply ({'; '.join(other)})")


class PlaybookExitRules(ExitRules):
    def __init__(self, loader: PlaybookLoader, finder: OpportunityFinder, records: Callable[[str], DeskRecords]):
        self.loader, self.finder, self.records = loader, finder, records

    def rules(self, book: str) -> Mapping[str, Sequence[ExitRule]]:
        playbook, rules = self.loader.load(), {}
        for position in open_positions(self.records(book)):
            strategy = playbook.get(*version_key(position.strategy))
            time_exit_only(strategy)
            expiry = min(leg.expiry for leg, _ in position.holdings)
            exit_day = self.finder.exit_day(strategy, expiry)
            rules[position.trade_id] = [ExitOnDay(exit_day, f"{position.strategy} time exit for expiry {expiry}")]
        return rules
