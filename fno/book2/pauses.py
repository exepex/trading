"""Book 2's research pauses (story F5 criterion 14; judge 632 B2, the owner's E6 risk rules applied to the research
versions Q11 lets Book 2 trade). E6 counts a research version only on its shadow account and pauses only `paper`
versions (`fno/scorecard/pauses.py`), so Book 2 keeps its own stop: on Book 2's own closed trades of a research
version, from its first one, a single loss of at least the version's `catastrophic_loss_rs`, or a realised net at or
below `CUMULATIVE_CAPS` times that cap (E6's own constant), appends one row to `research_pauses.csv` and sends one
alert. `Book2Playbook` drops the version from that day: new Book 2 entries stop, open trades keep their exits. The
registry, D2's shadow and Book 1 are untouched; only a new version number trades again.

The file is append-only (judge 632.1): no row is ever edited or removed, and a row is dated its trigger's day, never a
past one. Every read checks the file against its committed text and refuses a change or a back-dated row."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..alerts.sender import AlertSender
from ..constants import BOOK2_HYBRID
from ..daily.reviews import Review, ReviewResult
from ..desk.trade_counts import version_key
from ..playbook.loader import Playbook
from ..playbook.schema import version_id
from ..playbook.transitions import RESEARCH
from ..scorecard.pauses import CUMULATIVE_CAPS
from ..scorecard.strategy_record import StrategyRecord

PAUSES_FILE = "journal/book2_hybrid/research_pauses.csv"
COLUMNS = ("version", "day", "reason")
CATASTROPHIC = "catastrophic loss: Book 2 trade {trade} lost Rs {loss:,.2f}, cap Rs {cap:,.2f}"
CUMULATIVE = "cumulative loss: Book 2 realised Rs {loss:,.2f}, {times} x cap Rs {cap:,.2f}"
ALERT = ("F&O Book 2 {day}: research version {version} paused for Book 2 ({reason}); no new Book 2 entry, its open "
         "trades keep their exits; Book 1 and the registry untouched")  # fmt: skip


class PausesRefused(ValueError):
    """The pause file was edited, shortened or back-dated: Book 2 trades no research version until it is fixed."""


@dataclass(frozen=True)
class PauseTrigger:
    version: str  # "<name>-v<n>"
    reason: str


class ResearchPauses:
    def __init__(self, root: Path, committed_text: Callable[[], str | None]):
        """`committed_text()`: the file as last committed (None when never committed)."""
        self.path, self.committed_text = Path(root) / PAUSES_FILE, committed_text

    def rows(self) -> list[dict]:
        text = self.path.read_text(encoding="utf-8") if self.path.is_file() else ""
        committed = self.committed_text() or ""
        if not text.startswith(committed):
            raise PausesRefused(f"{PAUSES_FILE} differs from its committed text: rows are never edited or removed")
        rows = list(csv.DictReader(io.StringIO(text))) if text else []
        days = [date.fromisoformat(r["day"]) for r in rows]
        if any(later < earlier for earlier, later in zip(days, days[1:])):
            raise PausesRefused(f"{PAUSES_FILE} holds a back-dated row: each row is dated its trigger's day")
        return rows

    def paused_on(self, day: date) -> tuple[str, ...]:
        """The versions Book 2 may not enter on `day` (a row dated that day or before)."""
        return tuple(sorted({r["version"] for r in self.rows() if date.fromisoformat(r["day"]) <= day}))

    def append(self, trigger: PauseTrigger, day: date) -> bool:
        """Adds the version's one row, dated `day` (today); False when it is already paused."""
        rows = self.rows()
        if any(r["version"] == trigger.version for r in rows):
            return False
        if rows and date.fromisoformat(rows[-1]["day"]) > day:
            raise PausesRefused(f"a pause dated {day} would be back-dated behind {rows[-1]['day']}")
        out = io.StringIO()
        writer = csv.DictWriter(out, COLUMNS, lineterminator="\n")
        if not rows:
            writer.writeheader()
        writer.writerow({"version": trigger.version, "day": day.isoformat(), "reason": trigger.reason})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="") as file:
            file.write(out.getvalue())
        return True


def research_triggers(records: Iterable[StrategyRecord], playbook: Playbook, day: date) -> list[PauseTrigger]:
    """Each research version (still `research` through the day) whose Book 2 closed trades break a cap."""
    through = playbook.status_through(day)
    caps = {s.key: float(s.evaluation_plan["catastrophic_loss_rs"]) for s in playbook.strategies
            if through.get(s.key) == RESEARCH}  # fmt: skip
    triggers = []
    for record in records:
        key = version_key(record.strategy)
        if record.account != BOOK2_HYBRID or key not in caps:
            continue
        cap, lines = caps[key], [(t.trade_id, t.line.net) for t in record.closed]
        worst = min(lines, key=lambda line: line[1], default=None)
        total = sum(net for _, net in lines)
        if worst is not None and worst[1] <= -cap:
            reason = CATASTROPHIC.format(trade=worst[0], loss=-worst[1], cap=cap)
            triggers.append(PauseTrigger(version_id(*key), reason))
        elif total <= -CUMULATIVE_CAPS * cap:
            triggers.append(PauseTrigger(version_id(*key), CUMULATIVE.format(loss=-total, times=CUMULATIVE_CAPS,
                                                                             cap=cap)))  # fmt: skip
    return triggers


class Book2ResearchPauses(Review):
    """One more review in E6's `reviews` step (fno/daily/reviews.py)."""

    def __init__(self, records: Callable[[], list[StrategyRecord]], playbook: Callable[[], Playbook],
                 pauses: ResearchPauses, alerts: AlertSender):  # fmt: skip
        self.records, self.playbook, self.pauses, self.alerts = records, playbook, pauses, alerts

    def review(self, day: date, marks: Mapping) -> ReviewResult:
        lines = []
        for trigger in research_triggers(self.records(), self.playbook(), day):
            if self.pauses.append(trigger, day):
                text = ALERT.format(day=day, version=trigger.version, reason=trigger.reason)
                lines.append(f"{text} [{self.alerts.send(text)}]")
        return ReviewResult(lines)
