"""Composition root of the AI usage ledger and the budget meter (stories F8 and BG1): the only place that picks the
concrete usage reader, files, session calendar and alert sender. The alert sender is a dry run in this story; a later
routine swaps in the Slack sender here (one line)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ..accounting.ledgers import read_operating_costs
from ..alerts.dry_run import DryRunAlertSender
from ..alerts.sender import AlertSender
from ..config import ROOT, load_app_config
from ..storage.wiring import build_session_calendar
from .allocation import allocate
from .cap import CapSettings, cap_reading
from .capture_coverage import not_captured
from .items import month_items, plan_cost, unapproved_costs, unknown_items
from .report import MonthMeter
from .stop_rule_tracker import ReviewDate, review_date
from .usage_export import ExportFileUsageReader, SessionUsageReader
from .usage_ledger import UsageLedger

COSTS_FILE = "accounting/operating_costs.csv"


def build_usage_reader(export: Path) -> SessionUsageReader:
    return ExportFileUsageReader(export)


def build_usage_ledger(root: Path = ROOT) -> UsageLedger:
    return UsageLedger(root)


def build_budget_alert_sender() -> AlertSender:
    return DryRunAlertSender()


def build_month_meter(month: str, today: date, root: Path = ROOT, config: dict | None = None) -> MonthMeter:
    budget = (config or load_app_config())["budget"]
    costs_file = root / COSTS_FILE
    costs = read_operating_costs(costs_file.read_text(encoding="utf-8")) if costs_file.is_file() else []
    usage = [row for row in UsageLedger(root).rows() if row["date"].startswith(month)]
    missing = not_captured(root, month, usage, today.isoformat())
    return MonthMeter(
        month=month,
        items=month_items(costs, month),
        allocation=allocate(month, plan_cost(costs, month), usage),
        cap=cap_reading(usage, CapSettings.from_config(budget), len(missing)),
        usage_rows=usage,
        missing_captures=missing,
        needs_owner_yes=unapproved_costs(costs, month),
        unknown_items=unknown_items(costs, month),
    )


def build_review_date(config: dict | None = None) -> ReviewDate:
    rule = (config or load_app_config())["budget"]["stop_rule"]
    freeze = date.fromisoformat(rule["v4_freeze_date"]) if rule.get("v4_freeze_date") else None
    return review_date(freeze, rule["projected_v4_freeze_month"], build_session_calendar())
