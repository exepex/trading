"""The monitor's thresholds (story LM1), read from `config.yaml` `monitor` and checked once at start. Every value is
the owner's (DESK_DECISIONS, 16 Oct 2026; response 248); `version` names the set, so an alert record says which set
fired it."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from ..intraday.status import GOOD, INCOMPLETE

KEYS = (
    "version", "loss_used_warning", "loss_used_danger", "short_strike_near_pct", "big_move_pct",
    "big_move_step_pct", "stale_after_minutes", "check_incomplete_marks", "expiry_warn_sessions", "expiry_warn_from",
    "danger_summary_after", "summary_every_minutes",
)  # fmt: skip
BAD_SETTING = "monitor setting {key}: {problem}"


class MonitorSettingsError(ValueError):
    pass


@dataclass(frozen=True)
class MonitorSettings:
    version: str
    loss_used_warning: float  # share of the maximum loss
    loss_used_danger: float
    short_strike_near_pct: float
    big_move_pct: float
    big_move_step_pct: float | None  # alert again each further step; None: once an hour while it lasts
    stale_after_minutes: int
    check_incomplete_marks: bool  # an incomplete mark is checked for positions whose legs are all on it
    expiry_warn_sessions: int  # sessions before the nearest expiry from which it warns (0: expiry day only)
    expiry_warn_from: str  # IST time of the first mark that may warn (HH:MM)
    danger_summary_after: int
    summary_every_minutes: int
    execution_snapshot: time  # the desk timetable's, read, never typed

    @property
    def usable_statuses(self) -> tuple[str, ...]:
        return (GOOD, INCOMPLETE) if self.check_incomplete_marks else (GOOD,)

    @classmethod
    def from_config(cls, section: dict, execution_snapshot: time) -> MonitorSettings:
        missing = [k for k in KEYS if k not in section]
        unknown = sorted(set(section) - set(KEYS))
        if missing or unknown:
            raise MonitorSettingsError(f"monitor settings: missing {missing}, unknown {unknown}")
        settings = cls(**{k: section[k] for k in KEYS}, execution_snapshot=execution_snapshot)
        settings._validate()
        return settings

    def _validate(self) -> None:
        shares = (self.loss_used_warning, self.loss_used_danger)
        _require(0 < shares[0] < shares[1] <= 1, "loss_used", "need 0 < warning < danger <= 1")
        for key in ("short_strike_near_pct", "big_move_pct"):
            _require(_positive(getattr(self, key)), key, "must be a positive number")
        step = self.big_move_step_pct
        _require(step is None or _positive(step), "big_move_step_pct", "must be positive or null")
        for key in ("stale_after_minutes", "danger_summary_after", "summary_every_minutes"):
            _require(_whole(getattr(self, key)) and getattr(self, key) > 0, key, "must be a positive whole number")
        _require(_whole(self.expiry_warn_sessions) and self.expiry_warn_sessions >= 0, "expiry_warn_sessions",
                 "must be a whole number, 0 or more")  # fmt: skip
        _require(_clock(self.expiry_warn_from), "expiry_warn_from", "must be a time HH:MM")
        _require(isinstance(self.check_incomplete_marks, bool), "check_incomplete_marks", "must be true or false")
        _require(isinstance(self.version, str) and bool(self.version), "version", "must be a non-empty text")


def _positive(value) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value > 0


def _clock(value) -> bool:
    try:
        return isinstance(value, str) and time.fromisoformat(value) is not None
    except ValueError:
        return False


def _whole(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require(ok: bool, key: str, problem: str) -> None:
    if not ok:
        raise MonitorSettingsError(BAD_SETTING.format(key=key, problem=problem))
