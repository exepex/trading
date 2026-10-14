"""Book 1's exit rules (story E5, E3's `ExitRules` seam): each open trade exits by its playbook version's time exit,
the trading day D2 computed for its expiry (`OpportunityFinder.exit_day`). E4 applies it; when C3 finds the prices
unverified, E4 records the due exit as pending until valid quotes.

They never stop the exit review (judge 84). The versions are read from the playbook files without D1's approval
checks (a refused playbook must not halt exits), and a version stating an exit code cannot enforce (D1 now refuses it
`paper`, so only an older file can) still gets its time exit, with an alert naming the exit nobody applies."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from ..alerts.sender import AlertSender
from ..desk.daily_ports import ExitRules
from ..desk.exit_rules import ExitOnDay, ExitRule
from ..desk.records import DeskRecords
from ..desk.status import open_positions
from ..desk.trade_counts import version_key
from ..playbook.exit_terms import unenforceable_exits
from ..playbook.loader import Playbook
from ..playbook.opportunities import OpportunityFinder

NOT_ENFORCED = (
    "F&O paper desk {book} {trade}: {version} states exits code cannot apply ({what}); only its time exit runs"
)


class PlaybookExitRules(ExitRules):
    def __init__(self, playbook: Callable[[], Playbook], finder: OpportunityFinder,
                 records: Callable[[str], DeskRecords], alerts: AlertSender):  # fmt: skip
        self.playbook, self.finder, self.records, self.alerts = playbook, finder, records, alerts

    def rules(self, book: str) -> Mapping[str, Sequence[ExitRule]]:
        playbook, rules = self.playbook(), {}
        for position in open_positions(self.records(book)):
            strategy = playbook.get(*version_key(position.strategy))
            unenforced = unenforceable_exits(strategy)
            if unenforced:
                what = "; ".join(unenforced)
                self.alerts.send(NOT_ENFORCED.format(book=book, trade=position.trade_id, version=position.strategy,
                                                     what=what))  # fmt: skip
            expiry = min(leg.expiry for leg, _ in position.holdings)
            exit_day = self.finder.exit_day(strategy, expiry)
            rules[position.trade_id] = [ExitOnDay(exit_day, f"{position.strategy} time exit for expiry {expiry}")]
        return rules
