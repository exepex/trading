"""Composition root of story A4h: NSE's public index list (no Groww), O9's Drive data store and the checkout's
receipts, the archived index-close files, A7's calendar, the #fno-desk sender and the IST clock."""

from __future__ import annotations

import os
import time

from ..composition import build_alert_sender
from ..daily.alerts import ReportedAlerts
from ..models import now_ist
from ..providers.public import PublicData
from ..storage.data_wiring import build_data_store, receipt_folder
from ..storage.wiring import build_index_close_files, build_owner_drive, build_session_calendar
from .confirm import Confirmer
from .constants import DATA_AREA, ROOT, WRITER
from .official import ArchivedIndexCloses
from .reader import CloseReader
from .source import NseIndexList
from .store import DriveClosesStore

NO_DRIVE = "set the four FNO_GDRIVE_* owner settings to use A4h's Drive data store"


def receipt_pathspecs() -> tuple[str, ...]:
    """The receipts of A4h's Drive files only, never the shared `receipts/` root (O1's step commits these)."""
    return (f"receipts/{DATA_AREA}/{ROOT}/",)


def build_close_reader(env=os.environ) -> CloseReader:
    drive = build_owner_drive(env)
    if drive is None:
        raise RuntimeError(NO_DRIVE)
    store = DriveClosesStore(drive, build_data_store(WRITER, env=env), receipt_folder())
    calendar = build_session_calendar()
    alerts = ReportedAlerts(build_alert_sender())  # an unsent alert is printed with its text (O2)
    confirmer = Confirmer(store, ArchivedIndexCloses(build_index_close_files()), calendar, alerts)
    return CloseReader(NseIndexList(PublicData().nse_json), store, confirmer, calendar, now_ist, time.sleep)
