"""In-memory history and registry for the counting rule's tests: commits are names, `parents` is the graph."""

from dataclasses import dataclass, field
from datetime import date

from fno.school.constants import RoadCode
from fno.school.registration.counting import CountCandidate, FirstCounted, RegisteredVersion

SESSION = date(2026, 11, 30)
CARD_SHA = "ab" * 32
COMPARISON_SHA = "ef" * 32  # the comparison card as the fake history holds it


@dataclass
class FakeHistory:
    parents: dict[str, tuple[str, ...]]  # commit -> its parents
    cards: tuple[str, ...] = ("card",)  # commits that changed the card, oldest first
    card_sha256: dict[str, str] = field(default_factory=dict)  # card commit -> the card's SHA-256 there
    first_counted: dict[str, FirstCounted] = field(default_factory=dict)  # decision commit -> value in its tree
    default: FirstCounted = FirstCounted(SESSION, "card")

    def card_commits(self) -> list[str]:
        return list(self.cards)

    def card_sha256_at(self, commit: str) -> str:
        return self.card_sha256.get(commit, COMPARISON_SHA)

    def first_counted_at(self, commit: str) -> FirstCounted:
        return self.first_counted.get(commit, self.default)

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
    registered: dict[str, RegisteredVersion] = field(
        default_factory=lambda: {"CS1@1": RegisteredVersion(CARD_SHA, COMPARISON_SHA)}
    )
    asked: list[tuple] = field(default_factory=list)

    def registered_before(self, driver_id: str, session: date, decision_commit: str) -> RegisteredVersion | None:
        self.asked.append((driver_id, session, decision_commit))
        return self.registered.get(driver_id)


def candidate(**changes) -> CountCandidate:
    base = dict(session=SESSION, road=RoadCode.BANKNIFTY_MONTHLY, driver_id="CS1@1", card_sha256=CARD_SHA,
                commit="decision")  # fmt: skip
    return CountCandidate(**{**base, **changes})
