"""C4's two modes (story C4, design 12.4). `PlaybookMode` (books 1 and 2) checks the trade against the version it
claims: the version's fingerprint, that the version may trade on the day, its structure code, wing widths and lots,
and that the legs have that structure's shape. Book 2's authority envelope (D4) and Book 3's constitution (D5) are not
built: until they are, their checks fail closed (`WaitsFor`), so no Book 2 or Book 3 trade can pass hard validity."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .validity_proposal import CheckResult, ValidityProposal

BODY_SOLD = {"SF": True, "SC": True, "BF": False}  # whether the body (inner strikes) is sold when opening


class ValidityMode(ABC):
    name: str

    @abstractmethod
    def checks(self, proposal: ValidityProposal) -> list[CheckResult]:
        """The mode's own checks, each with its result."""


class PlaybookMode(ValidityMode):
    name = "playbook"

    def checks(self, proposal: ValidityProposal) -> list[CheckResult]:
        strategy = proposal.strategy
        if strategy is None:
            return [CheckResult("version", False, "no playbook version named for the trade")]
        spec, key = strategy.structure, (strategy.name, strategy.version)
        fingerprint = strategy.parameters_sha256 == proposal.rule_sha256
        shape = shape_problem(proposal)
        version = f"rule {proposal.rule_sha256[:12]} vs the version's {strategy.parameters_sha256[:12]}"
        return [
            CheckResult("version", fingerprint, version),
            CheckResult(
                "permitted", key in proposal.approved, f"{strategy.name} v{strategy.version} on {proposal.day}"
            ),
            CheckResult("structure", proposal.structure == spec.code, f"{proposal.structure} vs {spec.code}"),
            CheckResult("width", proposal.width in spec.widths, f"{proposal.width:g} in {list(spec.widths)}"),
            CheckResult("lots", proposal.lots == spec.lots, f"{proposal.lots} vs the version's {spec.lots}"),
            CheckResult("shape", not shape, shape or "legs have the structure's shape"),
        ]


def shape_problem(proposal: ValidityProposal) -> str:
    """Why the four legs are not the structure's: a body call and put on the body side, wings one width further out on
    the other side (SF and BF: one body strike; SC: the call body above the put body)."""
    if proposal.structure not in BODY_SOLD or len(proposal.legs) != 4:
        return f"{proposal.structure} needs four legs of a known structure, not {len(proposal.legs)}"
    body_side = -1 if BODY_SOLD[proposal.structure] else 1
    legs = {(leg.leg.kind, leg.leg.side): leg.leg.strike for leg in proposal.legs}
    try:
        call, put = legs[("CE", body_side)], legs[("PE", body_side)]
        call_wing, put_wing = legs[("CE", -body_side)], legs[("PE", -body_side)]
    except KeyError:
        return "the legs are not a body call and put with a wing on each side"
    if call_wing - call != proposal.width or put - put_wing != proposal.width:
        return f"wings are not {proposal.width:g} points beyond the body"
    same_body = call == put
    if (proposal.structure == "SC") == same_body or call < put:
        return "the body strikes do not fit the structure"
    return ""


class WaitsFor(ValidityMode):
    """A mode whose story is not built: every trade fails it, so nothing passes unchecked."""

    def __init__(self, name: str, story: str):
        self.name, self.story = name, story

    def checks(self, proposal: ValidityProposal) -> list[CheckResult]:
        return [CheckResult(self.name, False, f"waits for story {self.story}: not checkable yet, so the trade fails")]
