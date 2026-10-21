"""Composition root of story A20c: MOSPI's and the Fed's calendars through a polite session, US CPI and payrolls from
FRED (the owner's key; "not configured" while the secret is missing), the O9 data store (the owner's Drive,
receipts), the receipts committer and the #fno-desk alert sender."""

from __future__ import annotations

import os

from ..alerts.run_location import run_location
from ..alerts.step_output import StepOutputAlerts
from ..composition import build_alert_sender
from ..constants import ENV_FRED_API_KEY, RESEARCH_USER_AGENT
from ..http_pacing import PacedSession
from ..storage.data_store import new_run_id
from ..storage.data_wiring import build_data_store, build_receipt_committer
from .capture import CalendarCapture
from .fed import FedFomcCalendar
from .fred import FredReleaseCalendar
from .job import MacroCalendarJob
from .model import BLS, US_CPI, US_PAYROLLS
from .mospi import MospiArcCalendar
from .unconfigured import UnconfiguredCalendar

WRITER = "macro-calendar"


def build_macro_calendar_job(env=os.environ) -> MacroCalendarJob:
    session = PacedSession()
    session.headers["User-Agent"] = RESEARCH_USER_AGENT
    key = env.get(ENV_FRED_API_KEY)
    us = FredReleaseCalendar(session, key) if key else UnconfiguredCalendar(BLS, (US_CPI, US_PAYROLLS))
    calendars = (MospiArcCalendar(session), FedFomcCalendar(session), us)
    capture = CalendarCapture(calendars, build_data_store(WRITER, new_run_id(), env))
    alerts = StepOutputAlerts(build_alert_sender(), env)  # the workflow's own line speaks only if this did not
    return MacroCalendarJob(capture, build_receipt_committer(), alerts, run_location(env))
