"""Book 3's strategy proposals of a day (story F6 expected design 4): each one is checked by Book 3's own guards, then
registered by D5's `register()` (constitution, `proposed_on` from the clock, the trial ledger). A refused proposal
never stops the day; every proposal, registered or refused, is returned with its reason for the day log.

Guards: `status: research` with every `evidence` field empty (Book 3's registry is not an owner approval); no expected
net, since no Book 3 strategy was tested; `catastrophic_loss_rs` at most the owner's per-trade cap, so a spec cannot
loosen E6's pause. The rule key (`rule_sha256`: structure, entry conditions, exits) refuses a rule Book 3 already
registered under another name, and marks a copy of a playbook version's rule, or a named `supersedes`, as `reused`."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import fields as dataclass_fields
from datetime import date

import yaml

from ..playbook.fields import PlaybookError
from ..playbook.schema import Evidence, parse_strategy, rule_sha256
from ..playbook.transitions import RESEARCH
from .constitution import Constitution
from .registry import Provenance, RegistrationRefused, StrategyRegistry, spec_path

REGISTERED, REFUSED = "registered", "refused"
SAME_RULE = "same rule as {strategy_id}: trade that one"
NO_CONSTITUTION = "no constitution in force (none matches the registered D6 component)"


class Book3Proposer:
    def __init__(self, registry: StrategyRegistry, constitution: Callable[[date], Constitution | None],
                 max_loss_cap: float, playbook_rules: Callable[[], Mapping[str, str]]):  # fmt: skip
        """`playbook_rules()`: each playbook version's rule key -> its version ID (D1's own files)."""
        self.registry, self.constitution, self.cap, self.playbook_rules = (
            registry, constitution, max_loss_cap, playbook_rules,
        )  # fmt: skip

    def register_all(self, day: date, proposals: Sequence[Mapping], model: str, prompt_version: str,
                     role_set_version: str) -> list[dict]:  # fmt: skip
        constitution, playbook = self.constitution(day), self.playbook_rules()
        book3 = self._registered_rules()
        entries = []
        for proposal in proposals:
            entry = {"reason": proposal["reason"], "supersedes": proposal["supersedes"], "strategy_id": None,
                     "new_or_reused": None}  # fmt: skip
            try:
                document, refusal = self._guards(proposal["spec"], constitution, book3)
                if refusal:
                    raise RegistrationRefused(refusal)
                reused = bool(proposal["supersedes"]) or rule_sha256(document) in playbook
                provenance = Provenance(model, prompt_version, role_set_version, "reused" if reused else "new",
                                        proposal["supersedes"])  # fmt: skip
                row = self.registry.register(proposal["spec"], provenance, constitution)
            except (RegistrationRefused, PlaybookError) as refused:
                entries.append({**entry, "status": REFUSED, "why": str(refused)})
                continue
            book3[rule_sha256(document)] = row["strategy_id"]
            entries.append({**entry, "status": REGISTERED, "why": "", "strategy_id": row["strategy_id"],
                            "new_or_reused": row["new_or_reused"]})  # fmt: skip
        return entries

    def _guards(self, text: str, constitution: Constitution | None, book3: Mapping[str, str]) -> tuple[dict, str]:
        """The parsed document and why Book 3 refuses it ('' when it may go to D5)."""
        if constitution is None:
            return {}, NO_CONSTITUTION
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as bad:
            return {}, f"not valid YAML: {bad}"
        if not isinstance(document, dict):
            return {}, "the spec must be a YAML mapping in the playbook format"
        strategy = parse_strategy(document)  # PlaybookError names the field
        same = book3.get(rule_sha256(document))
        if same:
            return document, SAME_RULE.format(strategy_id=same)
        return document, "; ".join(self._problems(strategy))

    def _problems(self, strategy) -> list[str]:
        problems = []
        if strategy.status != RESEARCH:
            problems.append(f"status must be {RESEARCH} (Book 3's registry is not an approval)")
        if any(getattr(strategy.evidence, f.name) is not None for f in dataclass_fields(Evidence)):
            problems.append("every evidence field must be null")
        if strategy.evaluation_plan["expected_net_per_opportunity"] is not None:
            problems.append("expected_net_per_opportunity must be none (no Book 3 strategy was tested)")
        if strategy.evaluation_plan["catastrophic_loss_rs"] > self.cap:
            problems.append(f"catastrophic_loss_rs must be at most the per-trade cap {self.cap:g}")
        return problems

    def _registered_rules(self) -> dict[str, str]:
        """Each registered Book 3 spec's rule key -> its strategy ID."""
        found = {}
        for row in self.registry.rows():
            path = self.registry.root / spec_path(row["strategy_id"])
            if path.is_file():
                found[rule_sha256(yaml.safe_load(path.read_text(encoding="utf-8")))] = row["strategy_id"]
        return found
