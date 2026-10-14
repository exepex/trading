"""Composition root of the daily packs (story E2): the common pack's inputs (A4 snapshot, session calendar, official
closes, events), D2's opportunity code with the playbook, and the private pack's folders. Apart from `wiring.py`
(story E4's fills), so each story's parts are wired in one place."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from ..config import ROOT
from ..playbook.loader import Playbook
from ..playbook.registry import RegistryRow
from .common_pack import CommonPackBuilder
from .private_pack import PrivatePackBuilder


class LoadedPlaybook:
    """The playbook as D1's loader reads it (every check), and its registry rows (approval dates)."""

    def __init__(self, root: Path):
        from ..playbook.wiring import build_playbook_loader

        self.loader = build_playbook_loader(root)

    def load(self) -> Playbook:
        return self.loader.load()

    def registry_rows(self) -> Sequence[RegistryRow]:
        return self.loader.registry.rows()


def build_common_pack_builder(root: Path = ROOT) -> CommonPackBuilder:
    from ..composition import build_session_calendar
    from ..forecast.closes_source import CommittedClosesFile
    from ..playbook.opportunities import OpportunityFinder
    from ..quotes.recorder import DATASET
    from ..research_data.events import read_events
    from ..research_engine.cycles import TradingDays
    from ..storage.wiring import EVENTS_FILE, PANEL_FOLDER, build_quote_store
    from .opportunity_set import OpportunitySet
    from .reference_inputs import ClosesInput, EventsInput, SessionInput
    from .snapshot_inputs import SnapshotInput

    calendar = build_session_calendar()
    events = tuple(read_events(EVENTS_FILE.read_text(encoding="utf-8")))
    inputs = (
        SnapshotInput(build_quote_store(), DATASET),  # the same snapshot dataset E4 fills from
        SessionInput(calendar),
        ClosesInput(CommittedClosesFile(PANEL_FOLDER / "warmup_closes.csv")),
        EventsInput(events, EVENTS_FILE.relative_to(ROOT).as_posix()),
    )
    return CommonPackBuilder(inputs, OpportunitySet(OpportunityFinder(TradingDays(calendar))), LoadedPlaybook(root))


def build_private_pack_builder(root: Path = ROOT) -> PrivatePackBuilder:
    return PrivatePackBuilder(root)
