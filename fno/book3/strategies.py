"""Book 3's tradable strategies on a day (story F6 expected design 5), as the playbook snapshot D2 and D3 read: every
registered spec (listed from the registry as committed) proposed before the day whose registration D5 accepts at the
decision's base commit (committed, unchanged, the registry never edited); a spec D5 refuses or cannot read is listed
as excluded with its reason and never stops the others. Each opens on its `proposed_on` and trades from the next
session. The spec texts are the committed ones, keyed by D1's file name, so D3's records, its replay and the exits read
exactly what was registered; the registry's committed text is kept with them as a record."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..playbook.decision_inputs import PlaybookSnapshot
from ..playbook.fields import PlaybookError
from ..playbook.schema import file_name
from .registry import REGISTRY_FILE, NotRegistered, StrategyRegistry, parse_registry, spec_path


@dataclass(frozen=True)
class Tradable:
    snapshot: PlaybookSnapshot
    excluded: dict[str, str]  # strategy ID -> why D5 refused it today (shown in the day log, never traded)


class Book3Strategies:
    def __init__(self, registry: StrategyRegistry):
        self.registry = registry

    def on(self, day: date, commit: str) -> Tradable:
        git = self.registry.git
        registry_text = git.committed_text(REGISTRY_FILE, commit) or ""
        files, opens, excluded = {}, {}, {}
        for row in parse_registry(registry_text):  # the registry as committed, never the working tree
            strategy_id, proposed = row["strategy_id"], date.fromisoformat(row["proposed_on"])
            if proposed >= day:
                continue  # proposed today (or later): it trades from the next session
            try:
                spec = self.registry.require_registered(strategy_id, day, commit)
            except (NotRegistered, PlaybookError) as refused:  # one damaged spec never stops the others (judge 400)
                excluded[strategy_id] = str(refused)
                continue
            files[file_name(spec.name, spec.version)] = git.committed_text(spec_path(strategy_id), commit)
            opens[strategy_id] = proposed.isoformat()
        return Tradable(PlaybookSnapshot(files, registry_text, commit, opens), excluded)
