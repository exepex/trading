"""Reading and writing a recommendation (story REC1a): the school's canonical JSON (equal records, equal bytes),
read strictly. A missing field (the candidate set and `evidence_cutoff` above all, judge 620.1), an unknown field,
an unknown code or a broken rule refuses the bytes; nothing is ever filled in."""

from __future__ import annotations

import json
from dataclasses import fields

from .contracts import Recommendation, RecordRefused

FIELDS = frozenset(f.name for f in fields(Recommendation))
MISSING = "recommendation record lacks {names}"
UNKNOWN = "recommendation record has unknown fields {names}"
UNREADABLE = "recommendation record does not read: {kind}"


def encode(record: Recommendation) -> bytes:
    return record.to_bytes()


def decode(data: bytes) -> Recommendation:
    try:
        plain = json.loads(data)
    except (UnicodeDecodeError, ValueError) as bad:
        raise RecordRefused(UNREADABLE.format(kind=type(bad).__name__)) from None
    if not isinstance(plain, dict):
        raise RecordRefused(UNREADABLE.format(kind=type(plain).__name__))
    _same_fields(set(plain))
    try:
        return Recommendation.from_bytes(data)
    except RecordRefused:
        raise
    except (TypeError, ValueError, KeyError) as bad:
        raise RecordRefused(UNREADABLE.format(kind=type(bad).__name__)) from None


def _same_fields(names: set[str]) -> None:
    if missing := FIELDS - names:
        raise RecordRefused(MISSING.format(names=", ".join(sorted(missing))))
    if unknown := names - FIELDS:
        raise RecordRefused(UNKNOWN.format(names=", ".join(sorted(unknown))))
