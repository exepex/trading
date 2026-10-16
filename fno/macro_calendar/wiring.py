"""Composition root of story A20c: MOSPI's and the Fed's calendars through a polite session, US CPI and payrolls with
no source yet (open question 1), the O9 data store (the owner's Drive, receipts), the receipts committer and the
#fno-desk alert sender."""

from __future__ import annotations

import os

from ..alerts.run_location import run_location
from ..alerts.step_output import StepOutputAlerts
from ..composition import build_alert_sender
from ..constants import RESEARCH_USER_AGENT
from ..http_pacing import PacedSession
from ..storage.data_store import new_run_id
from ..storage.data_wiring import build_data_store, build_receipt_committer
from .capture import CalendarCapture
from .fed import FedFomcCalendar
from .job import MacroCalendarJob
from .model import BLS, US_CPI, US_PAYROLLS
from .mospi import MospiArcCalendar
from .unconfigured import UnconfiguredCalendar

WRITER = "macro-calendar"


def build_macro_calendar_job(env=os.environ) -> MacroCalendarJob:
    session = PacedSession()
    session.headers["User-Agent"] = RESEARCH_USER_AGENT
    calendars = (MospiArcCalendar(session), FedFomcCalendar(session), UnconfiguredCalendar(BLS, (US_CPI, US_PAYROLLS)))
    capture = CalendarCapture(calendars, build_data_store(WRITER, new_run_id(), env))
    alerts = StepOutputAlerts(build_alert_sender(), env)  # the workflow's own line speaks only if this did not
    return MacroCalendarJob(capture, build_receipt_committer(), alerts, run_location(env))
