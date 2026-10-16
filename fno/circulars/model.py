"""One circular as its publisher lists it, and the row A20b keeps for it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

NSE, SEBI = "nse", "sebi"
COLUMNS = (
    "source",
    "number",
    "issued_on",
    "department",
    "category",
    "subject",
    "link",
    "fno_relevant",
    "first_seen_at",
)
YES, NO = "yes", "no"
DEPARTMENT_SEPARATOR = "; "  # a circular NSE lists under several departments keeps them all


class FeedFailed(RuntimeError):
    """The publisher's list could not be read whole (refused, unreachable, not in its layout): never "no new
    circulars"."""


@dataclass(frozen=True)
class Circular:
    source: str
    number: str
    issued_on: date
    department: str  # NSE's departments ("; " between several); SEBI lists none
    category: str
    subject: str
    link: str  # the circular's own file or page: its identity

    def row(self, relevant: bool, first_seen_at: str) -> dict:
        return {
            "source": self.source, "number": self.number, "issued_on": self.issued_on.isoformat(),
            "department": self.department, "category": self.category, "subject": self.subject, "link": self.link,
            "fno_relevant": YES if relevant else NO, "first_seen_at": first_seen_at,
        }  # fmt: skip

    @property
    def departments(self) -> tuple[str, ...]:
        return tuple(self.department.split(DEPARTMENT_SEPARATOR)) if self.department else ()

    @property
    def filename(self) -> str:
        return self.link.rstrip("/").rsplit("/", 1)[-1]
