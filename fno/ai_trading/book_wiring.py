"""Composition root of the AI books' decision routine side (story F1t): the only place that picks the routine's
concrete transport, clock and publisher. Standard library only (no `fno.config`, which needs PyYAML), so
`python -m fno.ai_trading` needs no install."""

from __future__ import annotations

import time
from pathlib import Path

from ..ai.sealed_publish import SealedPublisher
from ..ai.transport import GitMainTransport
from ..models import now_ist
from .session import DecisionSession
from .versions import REGISTRY

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def build_decision_session(root: Path = REPOSITORY_ROOT) -> DecisionSession:
    return DecisionSession(root, REGISTRY, SealedPublisher(GitMainTransport(root), now_ist, time.sleep))
