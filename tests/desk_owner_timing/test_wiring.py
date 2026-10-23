"""E8's composition root: the owner's entry rule (`ApprovedLimit`, DESK_DECISIONS "E8 entry rule: price cap only"), the
verdict view at R = 60 minutes, C2's fill-day check, and the daily run's switch on E8's live date."""

from __future__ import annotations

from datetime import date

from fno.config import load_app_config
from fno.constants import VERDICT_REACTION_MINUTES, VIEW_VERDICT
from fno.desk.exit_timing import ImmediateExits
from fno.desk.owner_timing.entry_range import ApprovedLimit
from fno.desk.owner_timing.exit_alerts import AlertThenWait
from fno.desk.owner_timing.fill_risk import FillDayRisk
from fno.desk.owner_timing.live_switch import LiveFromEntries, LiveFromExits, LiveFromStep
from fno.desk.owner_timing.pending_entries import PendingEntries
from fno.desk.owner_timing.wiring import build_owner_timing_desks, build_owner_timing_step
from fno.desk.wiring import build_entry_desk


def test_the_step_fills_by_the_owners_price_cap_in_the_verdict_view():
    switch = build_owner_timing_step(load_app_config(), None, ImmediateExits(), date(2026, 11, 2))
    assert isinstance(switch, LiveFromStep) and switch.live_from == date(2026, 11, 2)
    step = switch.step
    entries = step.entries
    assert isinstance(entries.due_fill.entry_range, ApprovedLimit) and isinstance(entries.risk, FillDayRisk)
    assert (entries.view, entries.reaction, step.exits.view, step.exits.reaction) == (
        VIEW_VERDICT, VERDICT_REACTION_MINUTES, VIEW_VERDICT, VERDICT_REACTION_MINUTES)  # fmt: skip
    assert VERDICT_REACTION_MINUTES == 60


def test_the_daily_runs_desks_switch_on_the_live_date():
    cfg = load_app_config()
    entries, exits = build_owner_timing_desks(cfg, date(2026, 11, 2), build_entry_desk(cfg))
    assert isinstance(entries, LiveFromEntries) and isinstance(entries.after, PendingEntries)
    assert isinstance(exits, LiveFromExits) and isinstance(exits.after, AlertThenWait)
    assert entries.live_from == exits.live_from == date(2026, 11, 2)
