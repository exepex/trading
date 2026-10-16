"""Story G11 (response 272): what the v4 firer gives each book, read from the committed records and the slot ledger.

- **The day's questions** are the ones the book's own slot (hybrid or ai_team) is registered for, from its
  `effective_start`: exactly the rows the look's reconciliation expects. One list, never an AI list; a registered
  question the book's prompt does not define is refused loudly (a misregistration), never silently dropped.
- **Hybrid's rules values:** the rules slot's registered forecaster and the primary baseline, each its live row of the
  day (committed before 14:30); a missing row is `None` (no value), never a default."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..constants import BOOK2_HYBRID, V4_SLOT_RULES
from ..forecast_scoring.v4.inputs import V4ForecastSource
from ..forecast_scoring.v4.records import SlotRegistry
from ..forecast_v4.terms import PRIMARY_BASELINE
from ..v4_pack.model import Pack
from .export import recent_closes
from .paths import CLOSES_FILE
from .v4_input import V4InputFor, build_v4_input
from .v4_rows import SLOTS
from .versions import BookVersion

NOT_DEFINED = "{label} is registered for {questions}, which its prompt does not define: register a new version first"


class QuestionsRefused(ValueError):
    """The ledger asks a book a question its registered prompt does not define."""


@dataclass
class V4BookInputs:
    root: Path
    registry: SlotRegistry
    forecasts: V4ForecastSource

    def questions(self, version: BookVersion, day: date) -> list[str]:
        slot = SLOTS[version.book]
        asked = sorted(q for (q, s), r in self.registry.registered().items() if s == slot and r.effective_start <= day)
        if undefined := [q for q in asked if q not in version.questions]:
            raise QuestionsRefused(NOT_DEFINED.format(label=version.label, questions=undefined))
        return asked

    def build(self, version: BookVersion, day: date, questions: Sequence[str], pack: Pack, pack_sha256: str) -> dict:
        who = V4InputFor(version.book, version.label, day, questions, pack_sha256)
        closes = recent_closes(self.root / CLOSES_FILE, day)
        hybrid = version.book == BOOK2_HYBRID
        rules = self._rules(day, questions) if hybrid else None
        return build_v4_input(who, pack, closes, rules, version.envelope_width if hybrid else None)

    def _rules(self, day: date, questions: Sequence[str]) -> dict[str, dict[str, float | None]]:
        registered = self.registry.registered()
        out = {}
        for question in questions:
            rule = registered.get((question, V4_SLOT_RULES))
            names = [n for n in (rule.forecaster if rule else None, PRIMARY_BASELINE[question]) if n]
            out[question] = {name: self._live_value(question, name, day) for name in names}
        return out

    def _live_value(self, question: str, forecaster: str, day: date) -> float | None:
        found = self.forecasts.values(question, forecaster).get(day)
        return found.value if found is not None and found.live else None
