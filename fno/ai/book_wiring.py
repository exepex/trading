"""Composition root of the book side (stories F1 and G5): the only place that picks the routine's concrete transport
and clock. Standard library only (no `fno.config`, which needs PyYAML), so `python -m fno.ai` needs no install."""

from __future__ import annotations

import time
from pathlib import Path

from ..models import now_ist
from .book import BookSession
from .transport import GitMainTransport

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def build_book_session(root: Path = REPOSITORY_ROOT) -> BookSession:
    return BookSession(root, GitMainTransport(root), now_ist, time.sleep)
