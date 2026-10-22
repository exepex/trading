"""Composition root of `fno/school/registration/` (story MS-P1h): the repository's git history (the research engine's
`Git`, one adapter) and D6's version registry, wired into the counting rule.

A driver version is a D6 row of the book `school:<driver id>` (e.g. `school:CS1@1`; D6's `SCHOOL_BOOK_PREFIX`), its
component `CARD_COMPONENT` (`card_sha256`) the frozen driver card's SHA-256. The first counted session is read from
`config.yaml` as committed at each decision's own commit, so it can never be set or moved after the decisions it
would count."""

from datetime import date

import yaml

from ...books.version_registry import SCHOOL_BOOK_PREFIX
from ...books.versions import Versions
from ...research_engine.ledger import Git
from ..constants import SETTINGS_KEY
from .counting import CARD_PATH, CONFIG_PATH, CountingRule, FirstCounted

CARD_COMPONENT = "card_sha256"
FIRST_COUNTED_KEY = "first_counted"


class GitCountingHistory:
    def __init__(self, git: Git):
        self.git = git

    def is_ancestor(self, older: str, newer: str) -> bool:
        return self.git.is_ancestor(older, newer)

    def card_commits(self) -> list[str]:
        return self.git.commits_touching(CARD_PATH)

    def first_counted_at(self, commit: str) -> FirstCounted:
        text = self.git.committed_text(CONFIG_PATH, commit)
        block = (yaml.safe_load(text) or {}).get(SETTINGS_KEY) if text else None
        value = block.get(FIRST_COUNTED_KEY) if isinstance(block, dict) else None
        if not isinstance(value, date):
            return FirstCounted(None, None)
        written = self.git.first_commit_containing(f"{FIRST_COUNTED_KEY}: {value.isoformat()}", CONFIG_PATH)
        return FirstCounted(value, written)


class D6VersionLookup:
    def __init__(self, versions: Versions):
        self.versions = versions

    def card_sha256_registered_before(self, driver_id: str, session: date, decision_commit: str) -> str | None:
        row = self.versions.active_version(f"{SCHOOL_BOOK_PREFIX}{driver_id}", session, decision_commit)
        return None if row is None else row.components.get(CARD_COMPONENT)


def build_counting_rule(git: Git, versions: Versions) -> CountingRule:
    return CountingRule(GitCountingHistory(git), D6VersionLookup(versions))
