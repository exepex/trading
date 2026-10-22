"""Composition root of `fno/school/registration/` (story MS-P1h): git for the card's history and D6's version registry
for the driver versions, wired into the counting rule with the first counted session from the `school` settings.

A driver version is a D6 row of the book `school:<driver id>` (e.g. `school:CS1@1`), its component `card_sha256` the
frozen driver card's SHA-256."""

import subprocess
from datetime import date
from pathlib import Path

from ...books.versions import Versions
from ..settings import SchoolSettings
from .counting import CountingRule

SCHOOL_BOOK = "school:{driver_id}"
CARD_COMPONENT = "card_sha256"


class GitCardHistory:
    def __init__(self, repository: Path, run=subprocess.run):
        self.repository, self.run = Path(repository), run

    def last_commit(self, path: str) -> str | None:
        done = self._git("log", "-1", "--format=%H", "--", path)
        return done.stdout.strip() or None if done.returncode == 0 else None

    def is_ancestor(self, older: str, newer: str) -> bool:
        return self._git("merge-base", "--is-ancestor", older, newer).returncode == 0

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        return self.run(["git", *args], cwd=self.repository, capture_output=True, text=True)


class D6VersionLookup:
    def __init__(self, versions: Versions):
        self.versions = versions

    def card_sha256_registered_before(self, driver_id: str, session: date, decision_commit: str) -> str | None:
        row = self.versions.active_version(SCHOOL_BOOK.format(driver_id=driver_id), session, decision_commit)
        return None if row is None else row.components.get(CARD_COMPONENT)


def build_counting_rule(settings: SchoolSettings, history: GitCardHistory, versions: Versions) -> CountingRule:
    return CountingRule(settings.first_counted, history, D6VersionLookup(versions))
