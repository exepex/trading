"""The evening check run (story REC1c): every recorded day of the last 60 sessions whose latest check is not final is
checked again, each into its own write-once file `<day>.check.<check day>.json` with its receipt pushed; a day that
becomes final (complete, or incomplete because a source was unavailable) gets one #fno-desk line. A day that cannot
be read is alerted and fails the step, never the other days; the evening edition was already posted before it."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from ..alerts.sender import AlertSender
from ..school.contracts.seal import StaleSeal
from ..storage.receipts import RECEIPT_SUFFIX
from .check import OutcomeLookup, check, unreadable
from .check_record import FINAL, CheckRecord
from .check_text import answer_text, trades_text
from .codec import decode
from .constants import WINDOW_SESSIONS
from .contracts import RecordRefused
from .ports import DataDisagrees, InputFailed
from .run import DayResult
from .store import AREA_FOLDER, record_path
from .write_once import NotOurs, NotSaved, WriteOnce

CHECK_NAME = "{day}.check.{on}.json"
RECEIPT_MESSAGE = "Receipt: the recommender's check of {day} on {on}"
NOT_CHECKED = "recommender check NOT made for {day}: {why}"
NOTHING = "recommender check {on}: no recorded day waits for a check"
LINE = "PAPER ONLY. Recommender check for {day:%d %b %Y}: {verdict}. {answer} {trades} Record {path}, SHA-256 {short}."


@dataclass(frozen=True)
class CheckPorts:
    receipts: Path  # the repository's receipts folder of the data area (`receipts/data`)
    read: Callable[[str], bytes]  # a data-area file, verified against its receipt
    sessions: Callable[[date, date], list[date]]  # NSE sessions from a to b, both included
    lookup: Callable[[], OutcomeLookup]  # a fresh lookup per run (its cache is per run)


class CheckRun:
    def __init__(self, ports: CheckPorts, keeper: WriteOnce, alerts: AlertSender, clock: Callable[[], datetime]):
        self.ports, self.keeper, self.alerts, self.clock = ports, keeper, alerts, clock

    def run(self, on: date) -> DayResult:
        lookup, lines, ok = self.ports.lookup(), [], True
        for day in self._recorded_days(on):
            last = len(self.ports.sessions(day, on)) >= WINDOW_SESSIONS
            try:  # each day on its own: one unreadable file never stops the others (self-review, blocking)
                if not self._final(day):
                    lines += self._check(day, on, lookup, last)
            except DataDisagrees as disagree:  # read and contradictory: final at once (judge 658.1 m1)
                lines += self._failed(day, on, True, str(disagree))
                ok = False
            except (InputFailed, NotSaved, RecordRefused) as failed:  # RecordRefused covers a damaged check file
                lines += self._failed(day, on, last, str(failed))
                ok = False
        return DayResult(tuple(lines) or (NOTHING.format(on=on),), ok)

    def _recorded_days(self, on: date) -> list[date]:
        """Every receipted recommendation up to `on`, however old (judge 658.1 S1): a missed evening never lets a day
        leave the window without its final check; a day already final is skipped by its latest check."""
        folder = self.ports.receipts / AREA_FOLDER
        names = (p.name.removesuffix(f".json{RECEIPT_SUFFIX}") for p in folder.rglob(f"*.json{RECEIPT_SUFFIX}"))
        return sorted(d for d in (_day_of(name) for name in names) if d is not None and d <= on)

    def _check(self, day: date, on: date, lookup: OutcomeLookup, last: bool) -> list[str]:
        data = self._read(record_path(day))
        record = decode(data)
        result = check(record, hashlib.sha256(data).hexdigest(), on, self.clock(), lookup, last)
        kept, stands = self._keep(result)
        if stands.verdict not in FINAL:
            return [f"recommender check {day}: {stands.verdict.value}, {stands.open_positions} position(s) still open"]
        line = _line(record, stands, kept)
        return [self.alerts.send(line), line]

    def _failed(self, day: date, on: date, last: bool, why: str) -> list[str]:
        """A failed check is alerted; a read error is tried again next evening, and at the last check, or for records
        that disagree, it is written final as well."""
        line = NOT_CHECKED.format(day=day, why=why)
        lines = [self.alerts.send(line), line]
        if last:
            try:
                self._keep(unreadable(day, on, self.clock(), why))
            except NotSaved as unsaved:
                lines += [self.alerts.send(NOT_CHECKED.format(day=day, why=unsaved))]
        return lines

    def _keep(self, result: CheckRecord):
        day, on = result.session, result.checked_on
        kept = self.keeper.keep(_check_path(day, on), result.to_bytes(), _vouch(day, on),
                                RECEIPT_MESSAGE.format(day=day, on=on))  # fmt: skip
        return kept, _check_record(kept.payload)

    def _final(self, day: date) -> bool:
        checks = sorted(self._folder(day).glob(f"{day.isoformat()}.check.*.json{RECEIPT_SUFFIX}"))
        if not checks:
            return False
        latest = checks[-1].relative_to(self.ports.receipts).as_posix().removesuffix(RECEIPT_SUFFIX)
        return _check_record(self._read(latest)).verdict in FINAL

    def _read(self, path: str) -> bytes:
        """A data-area file verified against its receipt; any failure to read it is an input failure of that day."""
        try:
            return self.ports.read(path)
        except (StaleSeal, OSError, ValueError, KeyError) as unreadable:
            raise InputFailed(f"{path}: {type(unreadable).__name__}") from None

    def _folder(self, day: date) -> Path:
        return self.ports.receipts / AREA_FOLDER / f"{day:%Y}" / f"{day:%m}"


def _day_of(name: str) -> date | None:
    """`2026-11-02` names a recommendation; a check's receipt (`<day>.check.<on>`) names none."""
    try:
        return date.fromisoformat(name)
    except ValueError:
        return None


def _check_record(data: bytes) -> CheckRecord:
    try:
        return CheckRecord.from_bytes(data)
    except RecordRefused:
        raise
    except (ValueError, KeyError, TypeError) as damaged:  # a damaged check file: that day's problem, never the run's
        raise RecordRefused(f"a check file does not read ({type(damaged).__name__})") from None


def _check_path(day: date, on: date) -> str:
    return f"{AREA_FOLDER}/{day:%Y}/{day:%m}/{CHECK_NAME.format(day=day.isoformat(), on=on.isoformat())}"


def _vouch(day: date, on: date):
    def vouch(held: bytes) -> None:
        try:
            stored = _check_record(held)
        except RecordRefused as refused:
            raise NotOurs(str(refused)) from None
        if (stored.session, stored.checked_on) != (day, on):
            raise NotOurs(f"a check of {stored.session} on {stored.checked_on}")

    return vouch


def _line(record, stands: CheckRecord, kept) -> str:
    return LINE.format(day=record.session, verdict=stands.verdict.value.replace("_", " "),
                       answer=answer_text(record, stands), trades=trades_text(stands), path=kept.path,
                       short=kept.sha256[:12])  # fmt: skip
