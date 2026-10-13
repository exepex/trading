"""The registered version of each AI book's forecast (stories F1 and G5, design D6): its prompt file, the prompt's
SHA-256, the model the routine must run on and Hybrid's envelope width. A prompt changes only as a new version (a new
file and a new entry here); `brief` refuses a prompt whose bytes differ from the registered hash, so a quiet edit can
never reach a counted forecast."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..constants import BOOK2_HYBRID, BOOK3_AI


class VersionRefused(ValueError):
    """The book, version or prompt is not the registered one."""


@dataclass(frozen=True)
class BookVersion:
    book: str
    number: int
    prompt_file: str  # repository path of the versioned prompt
    prompt_sha256: str
    registered_model: str  # the routine's model; a different served model leaves the day unscored (D6)
    envelope_width: float | None  # Hybrid: how far outside the baselines' range it may go; None: no envelope

    @property
    def label(self) -> str:
        """`method_or_version` of every record (like Book 1's `book1/v1/sha256:<method hash>`)."""
        return f"{self.book}/v{self.number}/sha256:{self.prompt_sha256}"

    def prompt_text(self, root: Path) -> str:
        data = (Path(root) / self.prompt_file).read_bytes()
        if hashlib.sha256(data).hexdigest() != self.prompt_sha256:
            raise VersionRefused(f"{self.prompt_file} differs from version {self.number}: a change needs a new version")
        return data.decode("utf-8")


VERSIONS = (
    BookVersion(BOOK2_HYBRID, 1, "agents/forecast/book2_hybrid_v1.md",
                "8f860d90e2d623763198f4764b1e6ff04fdd7ec7c2fd374c66892542c65505af", "claude-opus-5-5", 0.10),
    BookVersion(BOOK3_AI, 1, "agents/forecast/book3_ai_v1.md",
                "6917786dac7430c951a7f80027b8d7c5ba40701d21288aebe7cfadccad77259a", "claude-opus-5-5", None),
)  # fmt: skip


def current_version(book: str) -> BookVersion:
    """The newest registered version of the book's forecast."""
    found = [v for v in VERSIONS if v.book == book]
    if not found:
        raise VersionRefused(f"{book!r} is not an AI book")
    return max(found, key=lambda v: v.number)


def version_by_label(label: str) -> BookVersion:
    for version in VERSIONS:
        if version.label == label:
            return version
    raise VersionRefused(f"{label!r} is not a registered version")
