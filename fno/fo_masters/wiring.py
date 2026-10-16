"""Composition root of story A20a's job: NSE's sources and the owner's Drive through the raw-data wiring, the session
calendar, the manifest committer and the #fno-desk alert sender."""

from __future__ import annotations

import os

from ..alerts.run_location import run_location
from ..alerts.step_output import StepOutputAlerts
from ..composition import build_alert_sender
from ..storage.snapshot_source import FoBanListSource, FoLotSizeSource
from ..storage.source_lists import dataset_name
from ..storage.wiring import build_manifest_recorder, build_session_calendar, build_snapshot_taker
from .job import FoMastersJob, Step, taken


def build_fo_masters_job(env=os.environ) -> FoMastersJob:
    calendar = build_session_calendar()
    ban, lots = (dataset_name(s) for s in (FoBanListSource, FoLotSizeSource))
    steps = (
        Step("ban list", lambda day: taken(build_snapshot_taker(ban).take(day))),
        Step("lot sizes", lambda day: taken(build_snapshot_taker(lots).take(day))),
    )
    alerts = StepOutputAlerts(build_alert_sender(), env)  # the workflow's own line speaks only if this did not
    return FoMastersJob(calendar, steps, build_manifest_recorder(), alerts, run_location(env))
