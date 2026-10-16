"""Composition root of story A20b: NSE's and SEBI's feeds through a polite session, the O9 data store (the owner's
Drive, receipts), the verified Drive cache for the circulars already listed, the receipts committer and the #fno-desk
alert sender."""

from __future__ import annotations

import os

from ..alerts.run_location import run_location
from ..alerts.step_output import StepOutputAlerts
from ..composition import build_alert_sender
from ..constants import RESEARCH_USER_AGENT
from ..http_pacing import PacedSession
from ..storage.data_store import new_run_id
from ..storage.data_wiring import DATA_AREA, build_data_store, build_drive_cache, build_receipt_committer
from ..storage.part_table import read_parts
from .capture import LIST_TABLE, CircularCapture
from .feeds import NseCircularApi, SebiCircularList
from .job import CircularsJob
from .model import COLUMNS, NSE, SEBI
from .relevance import FnoRelevance

WRITER = "circulars"


def seen_circulars(env=os.environ) -> dict[str, str]:
    """Link -> source of every circular already listed, from the receipted parts (verified byte for byte)."""
    cache, prefix = build_drive_cache(env), f"{DATA_AREA}/{LIST_TABLE}"
    report = cache.sync(prefix)
    if not report.complete:
        raise RuntimeError("; ".join(report.problems))
    return {row["link"]: row["source"] for row in read_parts(cache.local(prefix), COLUMNS)}


def build_circulars_job(env=os.environ) -> CircularsJob:
    session = PacedSession()
    session.headers["User-Agent"] = RESEARCH_USER_AGENT
    feeds = {NSE: NseCircularApi(session), SEBI: SebiCircularList(session)}
    capture = CircularCapture(feeds, FnoRelevance(), build_data_store(WRITER, new_run_id(), env))
    alerts = StepOutputAlerts(build_alert_sender(), env)  # the workflow's own line speaks only if this did not
    return CircularsJob(lambda: seen_circulars(env), capture, build_receipt_committer(), alerts, run_location(env))
