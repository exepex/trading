"""Book 3's strategy proposals of a day (story F6 expected design 4): each one is checked by Book 3's own guards, then
registered by D5's `register()` (constitution, `proposed_on` from the clock, the trial ledger). A refused proposal
never stops the day: every proposal, registered or refused, is returned with its reason for the day log, whatever its
text holds (unparseable YAML, an impossible date, a field D1 refuses).

Guards: `status: research` with every `evidence` field empty (Book 3's registry is not an owner approval); no expected
net, since no Book 3 strategy was tested; `catastrophic_loss_rs` at most the owner's per-trade cap, so a spec cannot
loosen E6's pause; only exits code enforces (the time exit; text exits "none"), since orders refuse any other. The rule
key (`rule_sha256`, from the parsed rule) refuses a rule Book 3 already registered under another name or wording, and
marks a copy of a playbook version's rule, or a named `supersedes`, as `reused`."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import fields as dataclass_fields
from datetime import date

from ..playbook.documents import strategy_from_text
from ..playbook.exit_terms import unenforceable_exits
from ..playbook.schema import Evidence, Strategy, rule_sha256
from ..playbook.transitions import RESEARCH
from .constitution import Constitution
from .registry import Provenance, RegistrationRefused, StrategyRegistry, spec_path

REGISTERED, REFUSED = "registered", "refused"
SAME_RULE = "same rule as {strategy_id}: trade that one"
NO_CONSTITUTION = "no constitution in force (none matches the registered D6 component)"
UNREADABLE = "the spec cannot be read: {problem}"


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
        book3, missing = self._registered_rules()
        entries = []
        for proposal in proposals:
            entry = {"reason": proposal["reason"], "supersedes": proposal["supersedes"], "strategy_id": None,
                     "new_or_reused": None}  # fmt: skip
            strategy, refusal = (None, missing) if missing else self._guards(proposal["spec"], constitution, book3)
            if not refusal:
                key = rule_sha256(strategy)
                reused = "reused" if proposal["supersedes"] or key in playbook else "new"
                provenance = Provenance(model, prompt_version, role_set_version, reused, proposal["supersedes"])
                try:
                    row = self.registry.register(proposal["spec"], provenance, constitution)
                except RegistrationRefused as refused:
                    refusal = str(refused)
            if refusal:
                entries.append({**entry, "status": REFUSED, "why": refusal})
                continue
            book3[key] = row["strategy_id"]
            entries.append({**entry, "status": REGISTERED, "why": "", "strategy_id": row["strategy_id"],
                            "new_or_reused": row["new_or_reused"]})  # fmt: skip
        return entries

    def _guards(self, text: str, constitution: Constitution | None, book3: Mapping[str, str]) -> tuple:
        """(the parsed strategy, why Book 3 refuses it; '' when it may go to D5)."""
        if constitution is None:
            return None, NO_CONSTITUTION
        try:
            strategy = strategy_from_text(text, "the proposed spec")
        except Exception as bad:  # noqa: BLE001 - any unreadable text is that proposal's refusal, never the day's end
            return None, UNREADABLE.format(problem=f"{type(bad).__name__}: {bad}")
        same = book3.get(rule_sha256(strategy))
        if same:
            return strategy, SAME_RULE.format(strategy_id=same)
        return strategy, "; ".join(self._problems(strategy))

    def _problems(self, strategy: Strategy) -> list[str]:
        problems = []
        if strategy.status != RESEARCH:
            problems.append(f"status must be {RESEARCH} (Book 3's registry is not an approval)")
        if any(getattr(strategy.evidence, f.name) is not None for f in dataclass_fields(Evidence)):
            problems.append("every evidence field must be null")
        if strategy.evaluation_plan["expected_net_per_opportunity"] is not None:
            problems.append("expected_net_per_opportunity must be none (no Book 3 strategy was tested)")
        if strategy.evaluation_plan["catastrophic_loss_rs"] > self.cap:
            problems.append(f"catastrophic_loss_rs must be at most the per-trade cap {self.cap:g}")
        unenforced = unenforceable_exits(strategy)
        if unenforced:
            problems.append(f"exits code cannot enforce ({'; '.join(unenforced)}): only the time exit; the rest none")
        return problems

    def _registered_rules(self) -> tuple[dict[str, str], str]:
        """(each registered Book 3 spec's rule key -> its strategy ID, why none can be compared). Each spec is read as
        committed (or as written earlier today), so a deleted file never frees its rule for a second registration; a
        registered spec missing everywhere refuses the day's proposals (the decision itself still runs)."""
        found, git = {}, self.registry.git
        for row in self.registry.rows():
            path = spec_path(row["strategy_id"])
            text = git.committed_text(path) if git.commit_exists("HEAD") else None
            on_disk = self.registry.root / path
            text = text or (on_disk.read_text(encoding="utf-8") if on_disk.is_file() else None)
            if text is None:
                return {}, f"{row['strategy_id']}: its registered spec is missing, so no rule can be compared"
            found[rule_sha256(strategy_from_text(text, path))] = row["strategy_id"]
        return found, ""
