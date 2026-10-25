"""The packs an AI book's decider reads must be the ones its session was fired with (story F1t, shared by F5's and
F6's deciders), or the records would claim data the decision did not use."""

from __future__ import annotations

from collections.abc import Mapping

from .ports import AcceptedDecision, DecisionRefused

PACK_DIFFERS = "{pack} pack read now ({now}) is not the one the session was fired with ({fired})"


def require_fired_packs(context: Mapping, accepted: AcceptedDecision) -> None:
    """`context`: the decider's input reader's run context, which names the packs' SHA-256 as read now."""
    for pack, fired in (("common", accepted.common_pack.sha256), ("private", accepted.private_pack.sha256)):
        now = context.get(f"{pack}_pack_sha256")
        if now != fired:
            raise DecisionRefused(PACK_DIFFERS.format(pack=pack, now=now, fired=fired))
