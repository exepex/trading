"""Story STR1 fixtures: a Book 1 trade of a one- or two-leg structure on C4's 14 Oct 2026 chain (spot 25,000), its
version allowing that width (0 included for LC and LP) and its claimed maximum loss from B2's cost model."""

from __future__ import annotations

from dataclasses import replace

from fno.checks.validity_proposal import ValidityProposal
from fno.constants import BOOK1_RULES
from fno.playbook.schema import parse_strategy
from tests.checks.validity_builders import CUTOFF, DAY, EXPIRY, LOT, legs_of, proposer_max_loss
from tests.playbook.builders import document


def one_side_strategy(code: str, width: float):
    doc = document(name=f"str1-{code.lower()}", status="paper")
    doc["structure"] = dict(doc["structure"], code=code, widths=[width])
    return parse_strategy(doc)


def one_side_proposal(code: str, spec, width: float, **changes) -> ValidityProposal:
    """A correct trade when `spec` is the code's own legs; the claimed loss is B2's unless a change replaces it."""
    version = one_side_strategy(code, width)
    claimed = changes.pop("claimed_max_loss", None)
    trade = ValidityProposal(
        BOOK1_RULES, f"{version.name}-v1:{EXPIRY}", DAY, CUTOFF, EXPIRY.isoformat(), code, width, 1, LOT,
        legs_of(spec), claimed if claimed is not None else proposer_max_loss(code, spec, width), True,
        version.parameters_sha256, version, frozenset({version.key}),
    )  # fmt: skip
    return replace(trade, **changes)
