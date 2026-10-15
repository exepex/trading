"""C4's two modes (story C4, design 12.4). `PlaybookMode` (books 1 and 2) checks the trade against the version it
claims: the version's fingerprint, that the version may trade on the day, its structure code, wing widths and lots,
and that the legs have that structure's shape (`validity_shapes.py`). Book 2's authority envelope (D4) and Book 3's
constitution (D5) are not built: until they are, their checks fail closed (`WaitsFor`), so no Book 2 or Book 3 trade
can pass hard validity."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

from .validity_proposal import CheckResult, ValidityProposal
from .validity_shapes import Shape, shape_problem


class ValidityMode(ABC):
    name: str

    @abstractmethod
    def checks(self, proposal: ValidityProposal) -> list[CheckResult]:
        """The mode's own checks, each with its result."""


class PlaybookMode(ValidityMode):
    name = "playbook"

    def __init__(self, shapes: Mapping[str, Shape]):
        self.shapes = dict(shapes)  # structure code -> its shape rule (validity_shapes.py)

    def checks(self, proposal: ValidityProposal) -> list[CheckResult]:
        strategy = proposal.strategy
        if strategy is None:
            return [CheckResult("version", False, "no playbook version named for the trade")]
        spec, key = strategy.structure, (strategy.name, strategy.version)
        fingerprint = strategy.parameters_sha256 == proposal.rule_sha256
        shape = shape_problem(self.shapes, proposal.structure, [leg.leg for leg in proposal.legs], proposal.width)
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


class WaitsFor(ValidityMode):
    """A mode whose story is not built: every trade fails it, so nothing passes unchecked."""

    def __init__(self, name: str, story: str):
        self.name, self.story = name, story

    def checks(self, proposal: ValidityProposal) -> list[CheckResult]:
        return [CheckResult(self.name, False, f"waits for story {self.story}: not checkable yet, so the trade fails")]
