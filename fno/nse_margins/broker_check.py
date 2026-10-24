"""`python -m fno margins stress-broker-check` (story A14c part 2): every A14 row of the day against the broker's
read-only margin calculator, run by O1's daily routine (the only place Groww's key lives), never by GitHub Actions.

From 09:30 IST on a session day (before it Groww may still be on the previous day's file) until a hard stop: no broker
request starts at or after 14:50 IST, whatever time the run began, so the 14:55 capture is never crowded. Baskets not
asked by then are `error` "deadline". One request every `pace_seconds`, the NIFTY quote first.

Exit and lines (O1's rules, agreed 16 Oct 2026): a finding is not a failure, and a failure never alerts twice.
- 0: every basket `ok`, "nothing to check", "outside market hours", or "nothing written: <reason>" (O1: refused).
- 0 with its own #fno-desk line: a `mismatch` (the data landed; the line says to review the stress factor).
- 1, the reason last and no own alert (O1 sends the step's line): a broker failure, the deadline, a basket that is
  not its row, or a record that could not be read or written. O1 never retries the step (judge 634), so an `error`
  basket is asked again only by a by-hand run before 14:50 IST; the line says so, never "a rerun today retries"."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time

from ..alerts.sender import AlertSender
from .broker_basket import Basket, BasketBuilder, BasketProblem, todays_rows
from .broker_compare import ERROR, MISMATCH, Levels, compare
from .broker_port import BrokerMargins
from .broker_record import BrokerRecord, BrokerResult, RecordProblem
from .calculator import ExposureRule, MarginOutsideModel
from .span_file import read_span_file

OPENS, STOPS = time(9, 30), time(14, 50)
OUTSIDE = "margin check {day}: outside market hours"
NO_ROWS = "margin check {day}: nothing written: margins.csv has no A14 row for {day}"
NOTHING = "margin check {day}: nothing to check ({count} baskets already checked)"
CHECKED = "margin check {day}: {ok} ok, {mismatch} mismatch, {error} error; record {path}"
MISMATCHED = "; mismatch: {baskets}"
LOST = "today's broker figure is lost"  # O1 never retries the step (judge 634)
BY_HAND = LOST + " unless `python -m fno margins stress-broker-check` is run by hand before 14:50"
NOT_SAVED = "margin check {day}: {count} basket(s) checked but not saved ({reason}); " + BY_HAND
MISMATCH_LINE = "Omenix F&O margin check: Groww and A14 differ beyond tolerance for {baskets}: review the stress factor"
FAILED = "margin check {day}: {count} basket(s) not checked ({reason}); {then}"
DEADLINE, NO_FILE = "deadline", "the day's SPAN file is not in the archive"
LOT_DIFFERS = "lot {lot} differs from NSE's dated lot {dated} for {expiry}"
NO_LOT = "no dated NSE lot for {expiry} on {day} ({why})"
OWN_REFUSALS = (BasketProblem, RecordProblem, MarginOutsideModel)  # their text is this repository's own wording


@dataclass(frozen=True)
class BrokerCheckParts:
    rows: Callable[[], Sequence[Mapping[str, str]]]  # margins.csv's rows
    span_file: Callable[[date], tuple[str, bytes | None]]  # the day's first-archived SPAN file
    baskets: BasketBuilder
    broker: BrokerMargins
    exposure: ExposureRule
    dated_lot: Callable[[date, date], int | str]  # NSE's lot for (day, expiry) from A20a's file, or why there is none
    record: BrokerRecord


class BrokerMarginCheck:
    def __init__(self, parts: BrokerCheckParts, is_session: Callable[[date], bool], clock: Callable[[], datetime],
                 sleep: Callable[[float], None], alerts: AlertSender, pace_seconds: float = 2.0,
                 print_line=print):  # fmt: skip
        self.parts, self.is_session, self.clock, self.sleep = parts, is_session, clock, sleep
        self.alerts, self.pace_seconds, self.print_line = alerts, pace_seconds, print_line
        self._asked = False  # pacing: the first request of a run does not wait

    def run(self) -> int:
        started = self.clock()
        day = started.date()
        if not self.is_session(day) or started.time() < OPENS:
            return self._done(OUTSIDE.format(day=day))
        try:
            rows = todays_rows(self.parts.rows(), day)
            if not rows:
                return self._done(NO_ROWS.format(day=day))
            done = self.parts.record.done(day)
            due = [row for row in rows if _key(row) not in done]
        except Exception as exc:  # rows or earlier records unreadable: nothing asked; the class name only (Drive's
            return self._failed(day, 0, _named(exc))  # and google-auth's texts are not ours to print)
        if not due:
            return self._done(NOTHING.format(day=day, count=len(rows)))
        results = self._check(day, due)
        try:
            path = self.parts.record.write(day, started, results)
        except Exception as exc:  # the answers did not land: no finding is alerted
            self.print_line(NOT_SAVED.format(day=day, count=len(results), reason=_named(exc)))
            return 1
        return self._finish(day, results, path)

    @property
    def lot_size(self) -> int:
        return self.parts.baskets.lot_size  # the lot A14's rows were computed with: one source (judge 630)

    def _check(self, day: date, rows: Sequence[Mapping[str, str]]) -> list[BrokerResult]:
        baskets = self._baskets(day, rows)
        if all(isinstance(basket, str) for basket in baskets.values()):  # nothing to send: no Groww request at all
            return [self._error(day, row, baskets[_key(row)]) for row in rows]
        try:
            before = self._ask(self.parts.broker.index_level)
        except Exception as exc:  # a row whose basket already failed keeps its own reason
            why = _quote_failure(exc)
            return [self._error(day, row, b if isinstance(b := baskets[_key(row)], str) else why) for row in rows]
        answers = {key: self._answer(basket) for key, basket in baskets.items() if not isinstance(basket, str)}
        levels = self._second_level(before) if answers else Levels(before)
        results = []
        for row in rows:
            basket = baskets[_key(row)]
            results.append(self._error(day, row, basket) if isinstance(basket, str)
                           else self._result(day, basket, *answers[basket.key], levels))  # fmt: skip
        return results

    def _second_level(self, before: float) -> Levels:
        """NIFTY after the last basket, so a move during the run is inside the range compared (judge 630)."""
        try:
            return Levels(before, self._ask(self.parts.broker.index_level))
        except Exception as exc:
            return Levels(before, None, _quote_failure(exc))

    def _baskets(self, day: date, rows: Sequence[Mapping[str, str]]) -> dict[tuple[str, float], Basket | str]:
        """Each row's basket, or the reason it has none (kept as the row's `error` detail)."""
        keys = [_key(row) for row in rows]
        try:
            name, data = self.parts.span_file(day)
            if data is None:
                return dict.fromkeys(keys, NO_FILE)
            span = read_span_file(data, name, allow_short_option_minimum=True)
        except Exception as exc:  # Drive unreachable or a damaged file: no basket can be built
            return dict.fromkeys(keys, f"SPAN file: {type(exc).__name__}")
        found: dict[tuple[str, float], Basket | str] = {}
        for key, row in zip(keys, rows, strict=True):
            try:
                basket = self.parts.baskets.basket(row, span, data, day)
                found[key] = self._lot_problem(day, basket) or basket
            except Exception as exc:  # not the row's own basket (named), outside the margin model, or no lot file
                found[key] = _named(exc)
        return found

    def _lot_problem(self, day: date, basket: Basket) -> str | None:
        """Why the basket's one lot is not NSE's dated lot for its expiry (then it is never sent), or None."""
        dated = self.parts.dated_lot(day, basket.expiry)
        if isinstance(dated, str):
            return NO_LOT.format(expiry=basket.expiry, day=day, why=dated)
        return None if dated == self.lot_size else LOT_DIFFERS.format(lot=self.lot_size, dated=dated,
                                                                       expiry=basket.expiry)  # fmt: skip

    def _answer(self, basket: Basket) -> tuple[datetime, tuple[float, float] | str]:
        """When Groww answered and its (SPAN, exposure), or why it did not (the class name only: an exception's text
        could carry a credential)."""
        try:
            answer = self._ask(lambda: self.parts.broker.basket(basket.orders(self.lot_size)))
        except Exception as exc:
            answer = DEADLINE if isinstance(exc, PastDeadline) else f"Groww: {type(exc).__name__}"
        return self.clock(), answer

    def _result(self, day: date, basket: Basket, checked_at: datetime, answer: tuple[float, float] | str,
                levels: Levels) -> BrokerResult:  # fmt: skip
        if isinstance(answer, str):
            return BrokerResult(checked_at, day, basket.structure, basket.width, None, basket.span_expected, None,
                                None, ERROR, answer, levels)  # fmt: skip
        try:
            found = compare(basket, answer, levels, self.parts.exposure, self.lot_size, day)
        except Exception as exc:  # e.g. an expiry outside the exposure model: named, never a silent pass
            return BrokerResult(checked_at, day, basket.structure, basket.width, answer[0], basket.span_expected,
                                answer[1], None, ERROR, _named(exc), levels)  # fmt: skip
        return BrokerResult(checked_at, day, basket.structure, basket.width, found.span_broker, found.span_expected,
                            found.exposure_broker, found.exposure_expected, found.status, found.detail,
                            levels)  # fmt: skip

    def _ask(self, request: Callable[[], object]):
        """One broker request, paced, never started at or after the hard stop."""
        if self._asked:
            self.sleep(self.pace_seconds)
        if self.clock().time() >= STOPS:
            raise PastDeadline()
        self._asked = True
        return request()

    def _error(self, day: date, row: Mapping[str, str], why: str) -> BrokerResult:
        return BrokerResult(self.clock(), day, row["structure"], float(row["width"]), None, None, None, None, ERROR,
                            why)  # fmt: skip

    def _finish(self, day: date, results: Sequence[BrokerResult], path: str) -> int:
        counts = {status: sum(r.status == status for r in results) for status in ("ok", MISMATCH, ERROR)}
        mismatched = ", ".join(f"{r.structure} {r.width:g} ({r.detail})" for r in results if r.status == MISMATCH)
        if mismatched:
            self.print_line(self.alerts.send(MISMATCH_LINE.format(baskets=mismatched)))
        summary = CHECKED.format(day=day, ok=counts["ok"], mismatch=counts[MISMATCH], error=counts[ERROR], path=path)
        self.print_line(summary + (MISMATCHED.format(baskets=mismatched) if mismatched else ""))  # O1's reason
        errors = [r for r in results if r.status == ERROR]
        if errors:
            reasons = sorted({r.detail for r in errors})
            return self._failed(day, len(errors), "; ".join(reasons))
        return 0

    def _failed(self, day: date, count: int, reason: str) -> int:
        then = LOST if DEADLINE in reason.split("; ") else BY_HAND  # past 14:50 no run can ask again
        self.print_line(FAILED.format(day=day, count=count, reason=reason, then=then))
        return 1

    def _done(self, line: str) -> int:
        self.print_line(line)
        return 0


def _key(row: Mapping[str, str]) -> tuple[str, float]:
    return row["structure"], float(row["width"])


def _quote_failure(exc: Exception) -> str:
    return DEADLINE if isinstance(exc, PastDeadline) else f"NIFTY quote: {type(exc).__name__}"


def _named(exc: Exception) -> str:
    """A failure by its class name, and our own text only for our own refusals."""
    return f"{type(exc).__name__}: {exc}" if isinstance(exc, OWN_REFUSALS) else type(exc).__name__


class PastDeadline(RuntimeError):
    """A broker request would start at or after 14:50 IST."""
