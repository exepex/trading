"""Composition root of the Actions side of the AI books' forecasts (stories F1 and G5): the only place that picks the
concrete routine triggers, alert sender, repository history and GitHub receipt source. Another trigger or receipt
source is one new class and one line here. The book side has its own root (`book_wiring.py`, standard library only)."""

from __future__ import annotations

import os
from datetime import date

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
from ..forecast_scoring.v4.inputs import ForecastFiles
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
from .v4_book_inputs import V4BookInputs
from .v4_collect import V4BookCollector
from .v4_fire import V4BookFirer
from .v4_settle import V4RowSettler

AI_V4_KEY = "ai_books_v4"  # config.yaml daily.live_from: the AI books' v4 go-live
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


def v4_live_from(cfg: dict | None = None) -> date | None:
    """The AI books' own v4 go-live date (`daily.live_from.ai_books_v4`): the v4 AI fire runs from it and the v2 AI
    fire stops (owner's choice A). Its own key, never O1's `forecasts_v4` (orchestrator, 21 Oct): null until the
    books' v4 steps exist, so nothing here turns on with the rule forecasts."""
    from ..config import load_app_config

    raw = ((cfg if cfg is not None else load_app_config()).get("daily", {}).get("live_from", {}) or {}).get(AI_V4_KEY)
    return date.fromisoformat(str(raw)) if raw else None


def build_v4_firer(env=os.environ) -> V4BookFirer:
    from ..forecast_scoring.v4.wiring import FORECASTS_FOLDER, build_slot_registry
    from ..v4_pack.wiring import build_released_packs

    triggers = {book: build_book_trigger(book, env) for book in ROUTINES}
    inputs = V4BookInputs(ROOT, build_slot_registry(), ForecastFiles(FORECASTS_FOLDER))
    return V4BookFirer(ROOT, triggers, lambda: build_released_packs(env), inputs, build_alert_sender(), now_ist,
                       v4_live_from())  # fmt: skip


def build_v4_collector(env=os.environ) -> V4BookCollector:
    from ..forecast_scoring.v4.wiring import FORECASTS_FOLDER, build_slot_registry
    from ..v4_pack.wiring import build_released_packs

    history = RepoHistory(ROOT)
    receipts = GitHubActivityReceipts(env.get(GITHUB_REPOSITORY_VARIABLE, ""), env.get(ENV_GITHUB_TOKEN, ""), history)
    inputs = V4BookInputs(ROOT, build_slot_registry(), ForecastFiles(FORECASTS_FOLDER))
    return V4BookCollector(ROOT, history, receipts, inputs, lambda: build_released_packs(env), now_ist,
                           v4_live_from())  # fmt: skip


def build_v4_settler(env=os.environ) -> V4RowSettler:
    from ..forecast_scoring.v4.wiring import FORECASTS_FOLDER

    return V4RowSettler(ROOT, FORECASTS_FOLDER, lambda: build_audit_seeds(ROOT, env)[0])


def build_ai_firer(env=os.environ) -> AiBookFirer:
    triggers = {book: build_book_trigger(book, env) for book in ROUTINES}
    return AiBookFirer(ROOT, triggers, build_alert_sender(), now_ist, v4_live_from())


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
