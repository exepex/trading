"""Composition root of story O13: the owner's Drive `logs/routines` area, this machine's open-run state, IST time, NSE's
session calendar and the #fno-desk alert sender."""

from __future__ import annotations

import os

from ..composition import build_alert_sender
from ..config import ROOT
from ..models import now_ist
from ..storage.raw_store import AreaStore, RawFileStore
from ..storage.trading_days import is_trading_day
from ..storage.wiring import OWNER_UPLOAD_SETTINGS, build_owner_drive, build_session_calendar
from .layout import LOGS_AREA
from .run_log import RoutineRunLog
from .run_state import RunStateFolder
from .schedule import ROUTINES
from .watch import RoutineWatcher

STATE_FOLDER = ROOT / "work" / "routine-logs"
NO_DRIVE = "Drive settings missing ({names})"


class NoDriveStore(RawFileStore):
    """Stands in when the Drive settings are absent: every write fails with the reason, so the run still goes on."""

    name = "no Drive"

    def get(self, path: str) -> bytes | None:
        raise RuntimeError(NO_DRIVE.format(names=", ".join(OWNER_UPLOAD_SETTINGS)))

    def put(self, path: str, data: bytes) -> None:
        raise RuntimeError(NO_DRIVE.format(names=", ".join(OWNER_UPLOAD_SETTINGS)))


def build_logs_store(env=os.environ) -> RawFileStore:
    drive = build_owner_drive(env)
    return AreaStore(drive, LOGS_AREA) if drive is not None else NoDriveStore()


def build_run_log(env=os.environ) -> RoutineRunLog:
    return RoutineRunLog(build_logs_store(env), RunStateFolder(STATE_FOLDER), now_ist)


def build_watcher(env=os.environ) -> RoutineWatcher:
    calendar = build_session_calendar()
    return RoutineWatcher(build_logs_store(env), ROUTINES, lambda day: is_trading_day(calendar, day), now_ist)


def build_sender():
    return build_alert_sender()
