"""A temporary git repository for story D6's tests: commit files, register versions, and make decision facts."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fno.books.version_registry import VersionRegistry, VersionRow
from fno.books.versions import VERSIONS_FILE, DecisionFacts, Versions
from fno.research_engine.ledger import Git
from tests.playbook.builders import commit_all, git

BOOK = "book2_hybrid"
MODEL_A, MODEL_B = {"model": "model-a", "prompt": "v1"}, {"model": "model-b", "prompt": "v1"}


class Repo:
    def __init__(self, root: Path):
        self.root, self.count = root, 0
        git(root, "init", "-q")
        (root / "prompt.md").write_text("v1")
        self.base = commit_all(root, "components")
        self.registry = VersionRegistry(root / VERSIONS_FILE)

    def register(self, version_id: str, starts_on: date, components=MODEL_A, book: str = BOOK) -> str:
        head = git(self.root, "rev-parse", "HEAD")
        self.registry.append(VersionRow(book, version_id, starts_on, head, components, "test"))
        return commit_all(self.root, f"register {version_id}")

    def decision(self, day: date, served=MODEL_A, book: str = BOOK) -> DecisionFacts:
        """A decision record committed now (its commit is the decision's commit)."""
        self.count += 1
        record = self.root / "journal" / book / "decisions" / f"{self.count}.json"
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(f"{self.count}")
        commit = commit_all(self.root, f"decision {self.count}")
        return DecisionFacts(book, day, f"d{self.count:03d}", commit, served)

    def versions(self) -> Versions:
        return Versions(self.registry.rows(), Git(self.root))
