"""Composition root of the daily packs (story E2): the common pack's inputs (A4 snapshot, session calendar, official
closes, events), D2's opportunity code with the playbook, and the private pack's folders. Apart from `wiring.py`
(story E4's fills), so each story's parts are wired in one place."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from ..config import ROOT
from ..constants import BOOK1_RULES, BOOK3_AI
from .book_sheet import BookSheet, LazySheet
from .common_pack import CommonPackBuilder
from .packs import WrittenPacks
from .private_pack import PrivatePackBuilder

PACKED_BOOKS = (BOOK1_RULES,)  # the daily run also packs each live AI book (story F1t)


def _book3_sheet(cfg: dict, root: Path) -> BookSheet:
    from ..book3.decision_wiring import build_book3_sheet

    return build_book3_sheet(cfg, root)


SheetBuilder = Callable[[dict, Path], BookSheet]
SHEETS: dict[str, SheetBuilder] = {BOOK3_AI: _book3_sheet}  # story E2e: book -> its sheet's builder (F5 adds Book 2)


def build_common_pack_builder(root: Path = ROOT) -> CommonPackBuilder:
    from ..composition import build_session_calendar
    from ..forecast.closes_source import CommittedClosesFile
    from ..playbook.opportunities import OpportunityFinder
    from ..playbook.wiring import build_playbook_loader
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
    return CommonPackBuilder(
        inputs, OpportunitySet(OpportunityFinder(TradingDays(calendar))), build_playbook_loader(root)
    )


def build_private_pack_builder(root: Path = ROOT) -> PrivatePackBuilder:
    return PrivatePackBuilder(root)


def build_packs(root: Path = ROOT, refresh: Callable[[], None] = lambda: None, files=None, alerts=None,
                books: Sequence[str] = PACKED_BOOKS, cfg: dict | None = None) -> WrittenPacks:  # fmt: skip
    """The day's common pack and each packed book's private pack, written once under `journal/`; the private packs are
    kept in Drive (story E2c), with only their `.sha256` committed. `alerts`: the caller's one sender (the daily run's
    reported sender, story O1); a command run alone gets the app's. `books`: the run's books (story F1t). Each packed
    book's sheet is built on first use (`cfg`: the run's settings, else the app's), so it refuses that book alone."""
    from ..composition import DESK_DECISION_TIME, build_alert_sender
    from .pack_store import PackStore
    from .wiring import build_private_files

    keep, alerts = (files or build_private_files(root)).push, alerts or build_alert_sender()
    return WrittenPacks(build_common_pack_builder(root), build_private_pack_builder(root), PackStore(root),
                        DESK_DECISION_TIME, tuple(books), refresh, keep, book_sheets(books, root, cfg), alerts,
                        tuple(b for b in books if b != BOOK1_RULES))  # fmt: skip  # F1t: AI books refused alone


def book_sheets(books: Sequence[str], root: Path, cfg: dict | None = None) -> dict[str, BookSheet]:
    from ..config import load_app_config

    def builder(book: str) -> Callable[[], BookSheet]:
        return lambda: SHEETS[book](cfg if cfg is not None else load_app_config(), root)

    return {book: LazySheet(builder(book)) for book in books if book in SHEETS}
