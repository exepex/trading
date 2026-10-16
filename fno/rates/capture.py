"""One rates run (story A21): read RBI's home page, the press-release list and each new T-bill cut-off release; store
every page write-once in Drive (O9); add the new rows; run the checks. Every failure is one O10 row (its step and
kind), and the run posts at most one #fno-desk message, which also carries a repo-rate change as information."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from ..alerts.sender import AlertSender
from .checks import disagreement, stale_auction, stale_home
from .constants import POLICY_REPO, RAW_FOLDER, RBI_HOME, RBI_RELEASE, RBI_RELEASES
from .failures import FailureLog
from .fetch import PageFetcher, RateFetchError
from .history import HOME_FILE, UNREADABLE, RatesHistory
from .pages import CurrentRates, RatePageError, parse_current_rates, parse_tbill_release, tbill_release_ids
from .rows import RateRow, auction_rows, latest, recorded_prids, repo_row

ALERT = "Omenix F&O rates (story A21): {lines}"
REPO_CHANGED = "information: RBI's policy repo rate changed from {old}% to {new}% (first seen {at})"


@dataclass
class RatesRun:
    added: list[RateRow] = field(default_factory=list)
    problems: list[tuple[str, str, str]] = field(default_factory=list)  # (step, kind, message)
    notes: list[str] = field(default_factory=list)
    alert: str = ""


class RatesCapture:
    def __init__(self, pages: PageFetcher, store, table, history: RatesHistory, failures: FailureLog,
                 alerts: AlertSender, clock: Callable[[], datetime]):  # fmt: skip
        self.pages, self.store, self.table, self.history = pages, store, table, history
        self.failures, self.alerts, self.clock = failures, alerts, clock

    def run(self) -> RatesRun:
        result, started = RatesRun(), self.clock()
        known = self._known(result)
        if known is None:  # stopped loudly: nothing is fetched or written without the earlier rows
            return self._finish(result, started)
        current = self._step(result, "home", self._home)
        ids = self._step(result, "release list", lambda: self._read(RBI_RELEASES, "list", tbill_release_ids)[0])
        for prid in self._new_ids(ids or [], known):
            self._step(result, f"release {prid}", lambda prid=prid: result.added.extend(self._release(prid)))
        if current is not None:
            result.added += self._repo(current, known, result)
        self._write(result, started)
        self._checks(result, known + result.added, current, started)
        return self._finish(result, started)

    def _known(self, result: RatesRun) -> list[RateRow] | None:
        """The table so far; None stops the run's writes (a re-record would carry a later first-seen time)."""
        return self._step(result, "history", self.history.rows, kind="history_unreadable")

    def _step(self, result: RatesRun, step: str, action, kind: str | None = None):
        try:
            return action()
        except RateFetchError as error:
            result.problems.append((step, error.kind, str(error)))
        except RatePageError as error:
            result.problems.append((step, "layout", str(error)))
        except Exception as error:  # Drive and anything else: named by class, never its text
            result.problems.append((step, kind or "store_failed", f"{step}: {type(error).__name__}"))
        return None

    def _read(self, url: str, name: str, parse):
        """Fetch, note the arrival time (judge 355 addendum 1), parse, then store the page write-once: a page that does
        not parse is still stored, under `<name>_unreadable`, and its error is raised."""
        data = self.pages.get(url)
        seen = self.clock()
        try:
            parsed = parse(data.decode("utf-8", errors="replace"))
        except RatePageError:
            self.store.put(f"{RAW_FOLDER}/{seen:%Y/%m/%d/%H%M%S}_{name}{UNREADABLE}.html", data)
            raise
        self.store.put(f"{RAW_FOLDER}/{seen:%Y/%m/%d/%H%M%S}_{name}.html", data)
        return parsed, hashlib.sha256(data).hexdigest(), seen

    def _home(self) -> tuple[CurrentRates, str, datetime]:
        return self._read(RBI_HOME, HOME_FILE.removeprefix("_").removesuffix(".html"), parse_current_rates)

    @staticmethod
    def _new_ids(ids: list[int], known: list[RateRow]) -> list[int]:
        """Each listed release not recorded yet and newer than the first one recorded, so a release that failed once is
        retried; on the first run, only the newest (no back-fill)."""
        prids = recorded_prids(known)
        return [i for i in ids if i not in prids and i > min(prids)] if prids else ids[:1]

    def _release(self, prid: int) -> list[RateRow]:
        auction, sha, seen = self._read(RBI_RELEASE.format(prid=prid), f"release_{prid}",
                                        lambda page: parse_tbill_release(page, prid))  # fmt: skip
        return auction_rows(auction, sha, seen)

    @staticmethod
    def _repo(current, known: list[RateRow], result: RatesRun) -> list[RateRow]:
        rates, sha, seen = current
        before = latest(known, POLICY_REPO)
        if before is not None and abs(before.value - rates.policy_repo_pct) < 5e-5:
            return []
        if before is not None:
            result.notes.append(REPO_CHANGED.format(old=before.value_pct, new=f"{rates.policy_repo_pct:.2f}",
                                                    at=seen.isoformat()))  # fmt: skip
        return [repo_row(rates, sha, seen)]

    def _write(self, result: RatesRun, started: datetime) -> None:
        if result.added:
            rows = [row.as_dict() for row in result.added]
            if self._step(result, "table", lambda: self.table.write(started.date(), rows)) is None:
                result.added, result.notes = [], []  # nothing was recorded, so nothing is announced

    def _checks(self, result: RatesRun, rows: list[RateRow], current, now: datetime) -> None:
        found = [("checks", "stale", stale_auction(rows, now.date()))]
        if current is None:
            found.append(("checks", "stale", stale_home(self.history.last_home_read(), now)))
        else:
            found.append(("checks", "disagreement", disagreement(rows, current[0].tbill_91_pct, now)))
        result.problems += [(step, kind, message) for step, kind, message in found if message]

    def _finish(self, result: RatesRun, started: datetime) -> RatesRun:
        for step, kind, message in dict.fromkeys(result.problems):  # one O10 row per failure, in order
            self.failures.record(started.date(), step, kind, message)
        lines = [message for _, _, message in result.problems] + result.notes
        if lines:
            result.alert = self.alerts.send(ALERT.format(lines="; ".join(lines)))
        return result
