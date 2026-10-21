"""Story D4 fixtures: playbook versions with a chosen width set and lot count, and trade envelopes in memory."""

from __future__ import annotations

from fno.playbook.envelope import ActionStatus, EnvelopeAction, TradeEnvelope
from fno.playbook.schema import parse_strategy
from tests.playbook.builders import document

ALLOWED, SHADOW, FORBIDDEN = ActionStatus.ALLOWED, ActionStatus.SHADOW_ONLY, ActionStatus.FORBIDDEN
V1_DEFAULTS = {action: ALLOWED for action in EnvelopeAction}  # envelope v1's default statuses (design 12.2)


def version(name: str = "sc-a", lots: int = 2, widths=(300, 200, 100), code: str = "SC"):
    doc = document(name=name, status="paper")
    doc["structure"] = dict(doc["structure"], code=code, widths=list(widths), lots=lots)
    return parse_strategy(doc)


def envelope(key, **statuses) -> TradeEnvelope:
    """An envelope for `key`; keyword statuses override the defaults (pass `None` to leave an action unlisted)."""
    table = dict(V1_DEFAULTS)
    for action, status in statuses.items():
        if status is None:
            table.pop(EnvelopeAction(action))
        else:
            table[EnvelopeAction(action)] = status
    return TradeEnvelope(key, table, f"sha-{key[0]}")
