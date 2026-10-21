"""The same-day announcements poll (story A21 part 2), a member behind A16's mark observer group: one poll of NSE's
day list at each A16 mark from 09:15 to 14:00 IST, each new `seq_id` recorded once with its first-seen time.

Every failure is one O10 row and one #fno-desk line: a failed poll once per episode (a "recovered" line ends it); a
stale gap, no poll by 10:00, a missed window and an unreadable seen set once a day. A16's group cuts this member off
at its time limit, so nothing here holds a lock."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, timedelta

from ..intraday.observer import MarkObserver
from .constants import FAILED, MISSED_WINDOW, NO_POLL_BY, OK, RAW_FOLDER, STALE_MINUTES, WINDOW_FIRST, WINDOW_LAST
from .day_state import DayState, DayStateSource
from .rows import ItemRefused, item_row, poll_row
from .source import AnnouncementSource, PollFailed

ALERT = "Omenix F&O same-day announcements (story A21): {line}"
LINES = {
    "poll": "poll failed at {mark} ({kind}); polls go on at each mark, one line per episode",
    "recovered": "polls recovered at {mark}",
    "stale": "stale: no successful poll since {last} ({minutes} min before the {mark} mark; limit 60)",
    "no_poll_by_1000": "no successful poll by the {mark} mark today",
    MISSED_WINDOW: "no successful poll in today's 09:15-14:00 window: F2 has no same-day announcements",
    "seen_set_unreadable": "today's earlier rows could not be read from Drive; this run polls nothing",
    "item_refused": "an NSE item lacked seq_id or exchdisstime at {mark}; the others were kept",
    "store_failed": "the {mark} poll could not be stored in Drive ({kind}); its items are recorded later, if at all",
}


class AnnouncementsPoller(MarkObserver):
    def __init__(self, source: AnnouncementSource, days: DayStateSource, store, items, polls, failures, alerts,
                 is_session: Callable[[date], bool], clock: Callable[[], datetime], run_id: str):  # fmt: skip
        self.source, self.days, self.store, self.items, self.polls = source, days, store, items, polls
        self.failures, self.alerts, self.is_session, self.clock, self.run_id = (
            failures,
            alerts,
            is_session,
            clock,
            run_id,
        )
        self._states: dict[date, DayState | None] = {}
        self.paths: tuple[str, ...] = ()  # what A16's mark commit carries for this member (set by the wiring)

    def after_mark(self, day: date, mark: datetime, document, status: str) -> None:
        if not self.is_session(day) or mark.time() < WINDOW_FIRST:
            return
        state = self._state(day)
        if state is None:
            return
        if mark.time() > WINDOW_LAST:
            self._after_window(day, mark, state)
            return
        self._poll(day, mark, state)
        self._checks(day, mark, state)

    def _state(self, day: date) -> DayState | None:
        if day not in self._states:
            try:
                self._states[day] = self.days.load(day)
            except Exception:  # any failure: never poll without the seen set
                self._states[day] = None
                self._once(day, "load", "seen_set_unreadable", {})
        return self._states[day]

    def _poll(self, day: date, mark: datetime, state: DayState) -> None:
        requested, before = self.clock(), state.last_status()
        try:
            found = self.source.day_list(day)
        except PollFailed as failed:
            self._log_poll(day, state, poll_row(mark, requested, FAILED, failed.kind, 0, 0, self.run_id))
            if before != FAILED:
                self._problem(day, "poll", failed.kind, {"mark": f"{mark:%H:%M}", "kind": failed.kind})
            return
        rows, refused = self._new_rows(found, state)
        try:
            self.store.put(f"{RAW_FOLDER}/{day:%Y/%m/%d}/{found.arrived_at:%H%M%S}_{mark:%H%M}.json", found.raw)
            if rows:
                self.items.write(day, mark, rows)
        except Exception as error:  # Drive down: named by class; its items are not claimed as seen
            self._problem(day, "store", "store_failed", {"mark": f"{mark:%H:%M}", "kind": type(error).__name__})
            return
        state.seen |= {row["seq_id"] for row in rows}
        state.items += rows
        kind = "item_refused" if refused else ""
        self._log_poll(day, state, poll_row(mark, requested, OK, kind, len(found.items), len(rows), self.run_id))
        if refused:
            self._once(day, "poll", "item_refused", {"mark": f"{mark:%H:%M}"})
        if before == FAILED:
            self.alerts.send(ALERT.format(line=LINES["recovered"].format(mark=f"{mark:%H:%M}")))

    def _new_rows(self, found, state: DayState) -> tuple[list[dict], int]:
        rows, refused, taken = [], 0, set(state.seen)
        for item in found.items:
            try:
                row = item_row(item, found.arrived_at, self.run_id)
            except ItemRefused:
                refused += 1
                continue
            if row["seq_id"] not in taken:
                rows.append(row)
                taken.add(row["seq_id"])
        return rows, refused

    def _log_poll(self, day: date, state: DayState, row: dict) -> None:
        state.polls.append(row)
        try:
            self.polls.write(day, datetime.fromisoformat(row["mark"]), [row])
        except Exception as error:  # a poll row that cannot be stored is named, never silent
            self._problem(day, "store", "store_failed", {"mark": row["mark"][11:16], "kind": type(error).__name__})

    def _checks(self, day: date, mark: datetime, state: DayState) -> None:
        last = state.last_ok()
        if last is None and mark.time() >= NO_POLL_BY:
            self._once(day, "checks", "no_poll_by_1000", {"mark": f"{mark:%H:%M}"})
        elif last is not None and mark - last > timedelta(minutes=STALE_MINUTES):
            minutes = int((mark - last).total_seconds() // 60)
            self._once(
                day, "checks", "stale", {"last": f"{last:%H:%M:%S}", "minutes": minutes, "mark": f"{mark:%H:%M}"}
            )

    def _after_window(self, day: date, mark: datetime, state: DayState) -> None:
        if state.last_ok() is None and not self.failures.has(day, MISSED_WINDOW):
            self._log_poll(day, state, poll_row(mark, self.clock(), MISSED_WINDOW, MISSED_WINDOW, 0, 0, self.run_id))
            self._problem(day, "window", MISSED_WINDOW, {})

    def _once(self, day: date, step: str, kind: str, values: dict) -> None:
        if not self.failures.has(day, kind):
            self._problem(day, step, kind, values)

    def _problem(self, day: date, step: str, kind: str, values: dict) -> None:
        line = LINES[kind if kind in LINES else "poll"].format(**values)
        self.failures.record(day, step, kind, line)
        self.alerts.send(ALERT.format(line=line))
