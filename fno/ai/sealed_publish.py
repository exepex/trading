"""Publishing a sealed answer (stories F1 and G5's protocol, made generic for F1t's decisions and F2's role cards): the
commitment first, written once, then, from a given moment, the reveal (answer and salt) that must hash to it. Book-,
role- and kind-agnostic: a path, a transport, a clock. Standard library only (it runs in a routine before any
install)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from .seal import Commitment, reveal_text
from .transport import SubmissionTransport

ALREADY_SEALED = "{path} already exists: sealed once, never again"
DIFFERENT_REVEAL = "{path} already holds a different reveal (written once)"


class SealRefused(RuntimeError):
    """A step that must not run (a second seal, a different reveal); the message says what to do."""


class SealedPublisher:
    def __init__(self, transport: SubmissionTransport, clock: Callable[[], datetime], sleep: Callable[[float], None],
                 out: Callable[[str], None] = print):  # fmt: skip
        self.transport, self.clock, self.sleep, self.out = transport, clock, sleep, out

    def refuse_if_sealed(self, path: str) -> None:
        """Called before the salt is kept, so a second seal never replaces the first one's salt."""
        if self.transport.existing(path) is not None:
            raise SealRefused(ALREADY_SEALED.format(path=path))

    def commit(self, path: str, commitment: Commitment, message: str) -> str:
        """Publishes the commitment once; the commit that holds it."""
        self.refuse_if_sealed(path)
        return self.transport.publish(path, commitment.to_text(), message)

    def reveal(self, path: str, answer: dict, salt: str, reveal_from: datetime, message: str) -> str:
        """Waits until `reveal_from`, then publishes the reveal once; one line saying what happened."""
        wait = (reveal_from - self.clock()).total_seconds()
        if wait > 0:
            self.out(f"waiting {wait:.0f} s until {reveal_from:%H:%M:%S} before revealing")
            self.sleep(wait)
        text, existing = reveal_text(answer, salt), self.transport.existing(path)
        if existing is not None:
            if existing != text:
                raise SealRefused(DIFFERENT_REVEAL.format(path=path))
            return f"already revealed: {path}"
        return f"revealed in commit {self.transport.publish(path, text, message)[:10]}"
