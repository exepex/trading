"""Where a session's blocks are published (story P6): behind one interface, all blocks or none. A failed publish
leaves the previous publication current and unchanged; publishing the same publication again changes nothing."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .publication import Publication


class PublishFailed(RuntimeError):
    """Nothing of the publication became visible; the previous one is still current."""


class ReadModelPublisher(ABC):
    name: str = "publisher"

    @abstractmethod
    def publish(self, publication: Publication) -> None:
        """Makes every record of the publication current at once (PublishFailed: none of them)."""

    @abstractmethod
    def current(self) -> dict[str, dict]:
        """The current publication's records by page key (empty before the first publication)."""
