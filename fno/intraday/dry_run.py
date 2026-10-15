"""What a dry run uses instead of the repository commit (story A16): nothing is committed or pushed."""

from __future__ import annotations

from ..storage.manifest_commit import ManifestRecorder

NOT_PUBLISHED = "dry run: nothing committed or pushed"


class NoPublish(ManifestRecorder):
    def pending(self) -> list[str]:
        return []

    def commit(self, what: str) -> str:
        return NOT_PUBLISHED
