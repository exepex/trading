"""Commits what one news run owns (story A19): its receipts under `receipts/data/news/` and O10's capture-error log
(`git add` by name; the log is union-merged). Pushed to main through O9's committer rules: the record scan runs,
nothing is bypassed, and a checkout carrying other changes is refused."""

from __future__ import annotations

from ..storage.manifest_commit import GitManifestRecorder

MESSAGE = "News capture: receipts and capture-error rows ({what})"
LABEL = "news receipts"


class NewsCommitter(GitManifestRecorder):
    def __init__(self, repository, receipts_folder, error_log: str, **options):
        super().__init__(repository, receipts_folder, message=MESSAGE, label=LABEL, **options)
        self.error_log = error_log

    def _paths(self) -> list[str]:
        """Only paths that exist or are tracked: Git refuses a whole `add` when one pathspec matches nothing."""
        listed = self._git("ls-files", "-z", "--cached", "--others", "--exclude-standard", "--",
                           self.folder, self.error_log).stdout.split("\0")  # fmt: skip
        present = [path for path in listed if path]
        return [p for p in (self.folder, self.error_log) if any(x == p or x.startswith(p + "/") for x in present)]

    def owns(self, path: str) -> bool:
        return path == self.error_log or path.startswith(f"{self.folder}/")
