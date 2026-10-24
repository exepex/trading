"""Story T1f: the facts a posted card still records when its full facts cannot be built. Plain values only (text,
booleans, null and the clock checks already made), so they always turn into JSON, and they keep every key the next
card's `misses()` and the dashboard's card read (`slack`, `clock`, `missing`, `previous_misses`, `records_used`)."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from ..server_clock import SkewCheck, utc_text
from .card import TradeCard
from .posting import PostReceipt

FACTS_FAILED = "facts not built ({error})"


def minimal_facts(card: TradeCard, text: str, receipt: PostReceipt, checks: Sequence[SkewCheck], code_commit: str,
                  test: bool, error: Exception) -> dict:  # fmt: skip
    return {
        "day": card.day.isoformat(), "status": str(card.status), "reason_code": _text(card.reason_code),
        "card_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "code_commit": _text(code_commit),
        "test": bool(test), "records_used": [], "missing": [], "previous_misses": [],
        "slack": {"sent": receipt.sent, "ts": _text(receipt.ts), "channel": _text(receipt.channel),
                  "outcome": _text(receipt.outcome), "server_time_utc": _server_time(receipt)},
        "clock": _stored(checks), "failure": FACTS_FAILED.format(error=type(error).__name__),
    }  # fmt: skip


def _text(value) -> str | None:
    return value if isinstance(value, str) else None


def _server_time(receipt: PostReceipt) -> str | None:
    try:
        moment = receipt.server_time
    except (TypeError, ValueError):  # a `ts` that is not seconds: the post is named, its time is not
        return None
    return utc_text(moment) if moment else None


def _stored(checks: Sequence[SkewCheck]) -> list[dict]:
    """The clock checks already made (judge 592 addendum 1), or none if even they cannot be stored."""
    try:
        return [check.stored() for check in checks]
    except Exception:  # noqa: BLE001 - the fallback itself must never raise
        return []
