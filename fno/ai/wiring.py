"""Composition root of the Actions side of the AI books' forecasts (stories F1 and G5): the only place that picks the
concrete routine triggers, alert sender, repository history and GitHub receipt source. Another trigger or receipt
source is one new class and one line here. The book side has its own root (`book_wiring.py`, standard library only)."""

from __future__ import annotations

import os

from ..budget.wiring import build_usage_ledger
from ..composition import build_alert_sender
from ..config import ROOT
from ..constants import (
    BOOK2_HYBRID,
    BOOK3_AI,
    ENV_GITHUB_TOKEN,
    ENV_ROUTINE_BOOK2_TOKEN,
    ENV_ROUTINE_BOOK2_TRIGGER_ID,
    ENV_ROUTINE_BOOK3_TOKEN,
    ENV_ROUTINE_BOOK3_TRIGGER_ID,
    GITHUB_REPOSITORY_VARIABLE,
)
from ..models import now_ist
from ..pipeline.trigger import RoutineFireTrigger, RoutineTrigger, UnconfiguredTrigger
from ..storage import wiring as storage
from ..storage.raw_store import AreaStore
from .audit_plan import fired_sessions, weeks_to_draw
from .close_archive import DriveIndexCloseArchive, NoCloseArchive
from .collect import AiForecastCollector
from .draw_seed import verified_seeds
from .fire import AiBookFirer
from .history import RepoHistory
from .paths import CLOSES_FILE
from .receipts import GitHubActivityReceipts
from .record_writer import AiRecordWriter
from .usage_gaps import alert_usage_gaps
from .usage_record import BookUsageRecorder

ROUTINES = {
    BOOK2_HYBRID: (ENV_ROUTINE_BOOK2_TRIGGER_ID, ENV_ROUTINE_BOOK2_TOKEN),
    BOOK3_AI: (ENV_ROUTINE_BOOK3_TRIGGER_ID, ENV_ROUTINE_BOOK3_TOKEN),
}  # book -> its routine's two repository secrets


def build_book_trigger(book: str, env=os.environ) -> RoutineTrigger:
    names = ROUTINES[book]
    trigger_id, token = (env.get(name) for name in names)
    if not (trigger_id and token):
        return UnconfiguredTrigger(book, tuple(n for n in names if not env.get(n)))
    return RoutineFireTrigger(book, trigger_id, token)


def build_ai_firer(env=os.environ) -> AiBookFirer:
    triggers = {book: build_book_trigger(book, env) for book in ROUTINES}
    return AiBookFirer(ROOT, triggers, build_alert_sender(), now_ist)


def build_ai_collector(env=os.environ) -> AiForecastCollector:
    history = RepoHistory(ROOT)
    receipts = GitHubActivityReceipts(env.get(GITHUB_REPOSITORY_VARIABLE, ""), env.get(ENV_GITHUB_TOKEN, ""), history)
    return AiForecastCollector(ROOT, history, receipts, AiRecordWriter(ROOT), now_ist)


def record_book_usage(day) -> list[str]:
    """Story F8c: every timing file into BG1's usage ledger, then one alert per run of `day` still not captured."""
    ledger = build_usage_ledger(ROOT)
    recorded = BookUsageRecorder(ROOT, ledger).record(now_ist().date())
    return recorded + alert_usage_gaps(ROOT, ledger, day, build_alert_sender())


def build_audit_seeds(root=ROOT, env=os.environ) -> tuple[dict, list[str]]:
    """The weekly audit draws' seeds, each close confirmed in the Drive archive, and one line per refused week."""
    drive = storage.build_owner_drive(env)
    archive = DriveIndexCloseArchive(AreaStore(drive, storage.RAW_AREA)) if drive else NoCloseArchive()
    return verified_seeds(root / CLOSES_FILE, archive, weeks_to_draw(fired_sessions(root)))
