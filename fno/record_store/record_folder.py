"""The records, kept in git (story DR1): `receipts/records/<dataset>/<yyyy>/<mm>/<session>.<level>.json`, a small
pointer to the chosen version (path and SHA-256) with every check's result; never a data value. Publishing is a push
to main, the one atomic step there is (first push wins), so two certifiers can never both make a record."""

from __future__ import annotations

import json
from pathlib import Path

from ..storage.manifest_commit import ManifestRecorder
from .models import Record, StagedVersion


def encode(document: dict) -> bytes:
    return (json.dumps(document, indent=1, sort_keys=True) + "\n").encode()


class RecordFolder:
    def __init__(self, folder: Path, committer: ManifestRecorder | None = None):
        """`committer`: commits and pushes only this folder (None: records stay local, e.g. a dry run)."""
        self.folder, self.committer = Path(folder), committer

    def file_for(self, dataset: str, session: str, level: str) -> Path:
        year, month, _ = session.split("-")
        return self.folder / dataset / year / month / f"{session}.{level}.json"

    def chosen(self, dataset: str, session: str, level: str) -> StagedVersion | None:
        file = self.file_for(dataset, session, level)
        if not file.is_file():
            return None
        return StagedVersion(**json.loads(file.read_text(encoding="utf-8"))["chosen"])

    def write(self, record: Record) -> StagedVersion:
        """Writes once and returns the version the record names: this one, or the one an earlier record holds."""
        held = self.chosen(record.dataset, record.session, record.level)
        if held is None:
            file = self.file_for(record.dataset, record.session, record.level)
            file.parent.mkdir(parents=True, exist_ok=True)
            temporary = file.with_name(f".{file.name}.part")
            temporary.write_bytes(encode(record.to_document()))
            temporary.replace(file)
        if self.committer is not None:
            self.committer.commit(f"{record.dataset} {record.session} {record.level}")
        return self.chosen(record.dataset, record.session, record.level)
