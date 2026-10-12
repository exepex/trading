"""Scans records for values that must never be public (story O5). A finding names the file, line and kind of value,
never the value itself, so that the report can be posted to Slack and logged safely."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from .patterns import RecordPattern
from .record_files import RecordText

UNSCANNABLE = "binary content that cannot be scanned"


@dataclass(frozen=True)
class Finding:
    path: str
    line: int  # 1-based; 0 for a whole-file finding
    kind: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.kind}"


class RecordScanner:
    def __init__(self, patterns: list[RecordPattern], allowed_values: Iterable[str] = ()):
        self._patterns = patterns
        self._allowed = frozenset(allowed_values)

    def scan_text(self, path: str, text: str) -> list[Finding]:
        if "\x00" in text:
            return [Finding(path, 0, UNSCANNABLE)]
        found = {
            (text.count("\n", 0, start) + 1, pattern.name)
            for pattern in self._patterns
            for start, value in pattern.values_in(text)
            if value not in self._allowed
        }
        return [Finding(path, line, kind) for line, kind in sorted(found)]

    def scan(self, records: Iterable[RecordText]) -> list[Finding]:
        return [finding for record in records for finding in self.scan_text(record.path, record.text)]
