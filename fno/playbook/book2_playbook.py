"""Book 2's view of the playbook (story F5, the owner's Q11 of 25 Oct 2026): the versions D2 approves for paper on the
day (`approved_on`: paper at the day's start and through it, never paused, retired or drifted) **plus** the research
candidates D2 forward-tests that day (`shadow_on`, registered before it) that are still `research` through the day,
**minus** every version Book 2's own research pause has stopped by then (`fno/book2/pauses.py`). It evaluates no
shadow: the research versions it trades are Book 2 candidates in Book 2's own book, never written into D2's shadow
books. Passed to D2's `RuleEvaluator` and to C4's proposal builder through the run's `PlaybookSnapshot`, so neither
changes and Book 1 keeps the plain `Playbook`."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .loader import Playbook
from .schema import Strategy
from .transitions import RESEARCH


@dataclass(frozen=True)
class Book2Playbook(Playbook):
    paused: frozenset[tuple[str, int]] = field(default_factory=frozenset)  # Book 2's research pauses by the day

    def approved_on(self, day: date) -> tuple[Strategy, ...]:
        through = self.status_through(day)
        research = [s for s in Playbook.shadow_on(self, day) if through.get(s.key) == RESEARCH]
        return tuple(s for s in (*Playbook.approved_on(self, day), *research) if s.key not in self.paused)

    def shadow_on(self, day: date) -> tuple[Strategy, ...]:
        return ()
