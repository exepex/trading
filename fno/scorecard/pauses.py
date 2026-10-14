"""Automatic pauses (story E6, criterion 1; design 12.8): the only switch-offs allowed before a review date.

- **Catastrophic loss:** a completed or unwound trade of an approved version, in any **book**, closed on or after the
  version's latest change to paper, whose C1 net loss reaches the plan's `catastrophic_loss_rs` (judge 73: a loss
  before an owner's re-approval, or in the version's earlier shadow test, never pauses it).
- **Live-feature drift (judge 67):** an approved version whose live feature no longer passes its use rule.

Either pauses that version at once (`paper -> paused`, approved by `hard_loss_rule`, through D1's status change, so no
book can trade it) and sends one #fno-desk line. A shadow version (status research) is only alerted: research cannot be
paused, and its result is evidence for the owner, who decides. Commit the registry and playbook file the change writes.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date

from ..alerts.sender import AlertSender
from ..constants import APPROVER_HARD_LOSS_RULE, SHADOW_PREFIX, PlaybookStatus
from ..desk.trade_counts import version_key
from ..playbook.lifecycle import StatusChanger
from ..playbook.loader import Playbook
from .strategy_record import StrategyRecord

ALERT = "F&O paper desk: {version} {action} ({reason})"
PAUSED_NOW, SHADOW_ONLY = "paused in every book", "shadow test, not paused: the owner decides"


@dataclass(frozen=True)
class PauseTrigger:
    name: str
    version: int
    reason: str

    @property
    def label(self) -> str:
        return f"{self.name}-v{self.version}"


def _counts(
    record: StrategyRecord, status: PlaybookStatus, approved_on: date | None, closed_on: date, on: date
) -> bool:
    """Whether a trade closed on `closed_on` in this record can trigger: an approved version only on its book trades
    since its latest approval; a research version (shadow) only on the day the trade closed (it is never paused, so an
    older loss would alert again on every run)."""
    shadow_account = record.account.startswith(SHADOW_PREFIX)
    if status == PlaybookStatus.PAPER:
        return not shadow_account and approved_on is not None and closed_on >= approved_on
    return status == PlaybookStatus.RESEARCH and closed_on == on


def catastrophic_losses(
    records: Iterable[StrategyRecord], playbook: Playbook, on: date, approved_on: Mapping[tuple[str, int], date]
) -> list[PauseTrigger]:
    """Every counting loss at or beyond its version's cap. `approved_on`: each version's latest change to paper."""
    triggers = []
    for record in records:
        name, version = version_key(record.strategy)
        found = [s for s in playbook.strategies if s.key == (name, version)]
        if not found:
            continue
        cap, status = found[0].evaluation_plan["catastrophic_loss_rs"], found[0].status
        for trade in record.closed:
            counts = _counts(record, status, approved_on.get((name, version)), trade.line.closed_on, on)
            if trade.line.net <= -cap and counts:
                reason = f"trade {trade.trade_id} in {record.account} lost Rs {-trade.line.net:,.2f}, cap Rs {cap:,.2f}"
                triggers.append(PauseTrigger(name, version, f"catastrophic loss: {reason}"))
    return triggers


def drifts(playbook: Playbook) -> list[PauseTrigger]:
    return [PauseTrigger(*d.strategy.key, f"live feature drift: {d.reason}") for d in playbook.drifted]


class AutoPauser:
    def __init__(self, changer: StatusChanger, alerts: AlertSender):
        self.changer, self.alerts = changer, alerts

    def apply(self, triggers: Iterable[PauseTrigger], playbook: Playbook, on: date) -> list[str]:
        """Pause each approved version once, alert each shadow once; returns one line per action taken."""
        status = {s.key: s.status for s in playbook.strategies}
        lines, done = [], set()
        for trigger in triggers:
            key = (trigger.name, trigger.version)
            if key in done or status.get(key) not in (PlaybookStatus.PAPER, PlaybookStatus.RESEARCH):
                continue
            done.add(key)
            action = SHADOW_ONLY
            if status[key] == PlaybookStatus.PAPER:
                self.changer.change(trigger.name, trigger.version, PlaybookStatus.PAUSED, APPROVER_HARD_LOSS_RULE, on)
                action = PAUSED_NOW
            text = ALERT.format(version=trigger.label, action=action, reason=trigger.reason)
            lines.append(f"{text} [{self.alerts.send(text)}]")
        return lines
