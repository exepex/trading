"""Reads the F&O files in parallel, a batch of sessions at a time (bounded memory): session summaries (every session)
and option chains (only the stocks and sessions an event needs)."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from itertools import batched

from .bhav import Chain, DaySummary, option_legs, summarise

DayFile = Callable[[date], tuple[str, bytes] | None]  # a session's original file name and bytes, or None
BATCH_SESSIONS = 32


def _summary_job(job):
    day, filename, data, names = job
    return summarise(day, filename, data, names)


def _chains_job(job):
    day, filename, data, symbols, names = job
    return day, option_legs(day, filename, data, symbols, names)


class FileReader:
    """`workers` = 0 reads in this process (tests); more uses that many processes."""

    def __init__(self, names, workers: int = 0):
        self.names, self.workers = names, workers

    def _run(self, job, days: Iterable[date], read: DayFile, extra: Callable[[date], tuple]) -> Iterator:
        pool = ProcessPoolExecutor(self.workers) if self.workers else None
        try:
            for batch in batched(days, BATCH_SESSIONS):
                jobs = [(day, *found, *extra(day)) for day in batch if (found := read(day)) is not None]
                yield from (pool.map(job, jobs) if pool else map(job, jobs))
        finally:
            if pool:
                pool.shutdown()

    def summaries(self, days: Iterable[date], read: DayFile) -> dict[date, DaySummary]:
        return {s.day: s for s in self._run(_summary_job, days, read, lambda d: (self.names,))}

    def chains(self, needs: dict[date, set[str]], read: DayFile) -> Iterator[tuple[date, dict[str, dict[date, Chain]]]]:
        """(day, symbol -> expiry -> chain) for the stocks each day needs, one session at a time."""
        return self._run(_chains_job, sorted(needs), read, lambda d: (needs[d], self.names))
