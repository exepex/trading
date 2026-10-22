"""In-memory history and registry for the counting rule's tests: commits are names, `parents` is the graph."""

from dataclasses import dataclass, field
from datetime import date

from fno.school.constants import RoadCode
from fno.school.registration.counting import CountCandidate

SESSION = date(2026, 11, 30)
CARD_SHA = "ab" * 32


@dataclass
class FakeHistory:
    parents: dict[str, tuple[str, ...]]  # commit -> its parents
    card_commit: str | None = "card"

    def last_commit(self, path: str) -> str | None:
        return self.card_commit

    def is_ancestor(self, older: str, newer: str) -> bool:
        seen, todo = set(), [newer]
        while todo:
            commit = todo.pop()
            if commit == older:
                return True
            if commit not in seen:
                seen.add(commit)
                todo.extend(self.parents.get(commit, ()))
        return False


CHAIN = FakeHistory({"card": (), "row": ("card",), "decision": ("row",)})


@dataclass
class FakeLookup:
    registered: dict[str, str] = field(default_factory=lambda: {"CS1@1": CARD_SHA})
    asked: list[tuple] = field(default_factory=list)

    def card_sha256_registered_before(self, driver_id: str, session: date, decision_commit: str) -> str | None:
        self.asked.append((driver_id, session, decision_commit))
        return self.registered.get(driver_id)


def candidate(**changes) -> CountCandidate:
    base = dict(session=SESSION, road=RoadCode.BANKNIFTY_MONTHLY, driver_id="CS1@1", card_sha256=CARD_SHA,
                commit="decision")  # fmt: skip
    return CountCandidate(**{**base, **changes})
