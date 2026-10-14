"""Book 1's exit rules (story E5, E3's `ExitRules` seam): each open trade exits by the time exit fixed at its decision
(the day D2 computed from the version file the run read, `book1_records.decided_exit_days`). E4 applies it; when C3
finds the prices unverified, E4 records the due exit as pending until valid quotes.

Nothing read now can stop or move that exit (judge 84). Today's version file is read only to alert: when it can no
longer be read, or states an exit code cannot enforce (D1 now refuses that for `paper`), the trade keeps its decided
time exit and #fno-desk is told. A trade with no committed decision record is held by E4, with its alert."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import date

from ..alerts.sender import AlertSender
from ..desk.daily_ports import ExitRules
from ..desk.exit_rules import ExitOnDay, ExitRule
from ..desk.records import DeskRecords
from ..desk.status import OpenPosition, open_positions
from ..playbook.documents import strategy_from_text
from ..playbook.exit_terms import unenforceable_exits

ALERT = "F&O paper desk {book} {trade} ({version}): {what}; its time exit {day} still runs"
UNREADABLE = "its playbook version file cannot be read now ({problem})"
NOT_ENFORCED = "its version states exits code cannot apply ({what})"
NO_RECORD = "F&O paper desk {book} {trade}: no committed decision record names its time exit; E4 holds it"

DecidedExits = Callable[[str], Mapping[str, tuple[date, str]]]  # book -> {trade ID: (exit day, version)}


class PlaybookExitRules(ExitRules):
    def __init__(self, decided: DecidedExits, version_text: Callable[[str], str | None],
                 records: Callable[[str], DeskRecords], alerts: AlertSender):  # fmt: skip
        self.decided, self.version_text, self.records, self.alerts = decided, version_text, records, alerts

    def rules(self, book: str) -> Mapping[str, Sequence[ExitRule]]:
        decided, rules = self.decided(book), {}
        for position in open_positions(self.records(book)):
            if position.trade_id not in decided:
                self.alerts.send(NO_RECORD.format(book=book, trade=position.trade_id))
                continue
            exit_day, version = decided[position.trade_id]
            rules[position.trade_id] = [ExitOnDay(exit_day, f"{version} time exit fixed at the decision")]
            self._warn(book, position, version, exit_day)
        return rules

    def _warn(self, book: str, position: OpenPosition, version: str, exit_day: date) -> None:
        """Alerts only: today's file never changes the exit above."""
        try:
            strategy = strategy_from_text(self.version_text(version) or "", f"{version}.yaml")
        except Exception as problem:  # noqa: BLE001 - any unreadable file is only reported, never fatal to the exits
            what = UNREADABLE.format(problem=f"{type(problem).__name__}: {problem}")
        else:
            unenforced = unenforceable_exits(strategy)
            what = NOT_ENFORCED.format(what="; ".join(unenforced)) if unenforced else ""
        if what:
            self.alerts.send(ALERT.format(book=book, trade=position.trade_id, version=version, what=what, day=exit_day))
