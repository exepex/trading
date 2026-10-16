"""Back-fill (section 4): every session in a range rebuilt from captured inputs, labelled `backfill_3pm` (A4's chains)
or `backfill_eod` (the panel), stopping before the first live day. One gzip file per run and underlying, named by the
method hash and the range; with no `made_at`, a rerun is byte-identical and the store's same-bytes rule makes it a
no-op. Never alerts and never fails for a missing day: missing days are counted by reason."""

from __future__ import annotations

import gzip
from collections import Counter
from collections.abc import Sequence
from datetime import date

from ..research_data.calendar import SessionCalendar
from .build import DayBuilder
from .chain import ChainSource
from .folders import backfill_path
from .recorder import NO_CHAIN, RECORDED_KINDS
from .records import encode
from .sources import ChainUnavailable

SCHEMA = "g13_backfill_v1"
STOPS_BEFORE_LIVE = "back-fill stops before the first live day {live_from}"
WRITTEN = "{underlying} {label}: {days} days written to {path}"
NONE_WRITTEN = "{underlying} {label}: no day to write"
SKIPPED = "{underlying} {label}: {count} days skipped: {reason}"


class Backfill:
    def __init__(self, source: ChainSource, builder: DayBuilder, store, calendar: SessionCalendar,
                 live_from: date | None):  # fmt: skip
        self.source, self.builder, self.store, self.calendar, self.live_from = (
            source,
            builder,
            store,
            calendar,
            live_from,
        )

    def run(self, label: str, underlyings: Sequence[str], first: date, last: date) -> list[str]:
        lines = []
        if self.live_from is not None and last >= self.live_from:
            last = min(last, self.calendar.previous_session(self.live_from))
            lines.append(STOPS_BEFORE_LIVE.format(live_from=self.live_from))
        days = [d for d in self.calendar.sessions(first, last) if self.calendar.session_kind(d) in RECORDED_KINDS]
        for underlying in underlyings:
            records, skipped = [], Counter()
            for day in days:
                try:
                    chain = self.source.chain(underlying, day)
                except ChainUnavailable as error:
                    skipped[str(error)] += 1
                    continue
                if chain is None:
                    skipped[NO_CHAIN] += 1
                    continue
                records.append(self.builder.build(chain, label, None))
            lines += [SKIPPED.format(underlying=underlying, label=label, count=n, reason=r) for r, n in skipped.items()]
            lines.append(self._write(label, underlying, first, last, records))
        return lines

    def _write(self, label: str, underlying: str, first: date, last: date, records: list[dict]) -> str:
        if not records:
            return NONE_WRITTEN.format(underlying=underlying, label=label)
        path = backfill_path(label, self.builder.method, underlying, first, last)
        payload = {"schema": SCHEMA, "label": label, "underlying": underlying, "method_sha256": self.builder.method,
                   "first": first.isoformat(), "last": last.isoformat(), "records": records}  # fmt: skip
        self.store.put(path, gzip.compress(encode(payload), mtime=0))
        return WRITTEN.format(underlying=underlying, label=label, days=len(records), path=path)
