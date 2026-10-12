"""Foreign investors' (FII/FPI) derivatives positioning from NSE's free daily participant-wise open interest file.

FIIs are often structurally short index futures (hedges against their stock holdings), so the level alone says little.
What matters is the change: their long share of index futures against its own recent average, and the tilt of their
index options book. Read once each morning for the previous sessions; never during the session.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, timedelta

PARTICIPANT_OI_URL = "https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{day:%d%m%Y}.csv"
FII_ROW = "FII"
CLIENT_TYPE = "Client Type"
FUT_LONG, FUT_SHORT = "Future Index Long", "Future Index Short"
CALL_LONG, PUT_LONG = "Option Index Call Long", "Option Index Put Long"
CALL_SHORT, PUT_SHORT = "Option Index Call Short", "Option Index Put Short"
MAX_CALENDAR_DAYS_BACK = 20  # enough to find 10 sessions across weekends and holidays


@dataclass(frozen=True)
class FiiDay:
    day: date
    futures_long_share: float  # FII index futures long / (long + short)
    options_tilt: float  # (calls long - calls short) - (puts long - puts short), as a share of their index options

    @classmethod
    def from_row(cls, day: date, row: dict[str, float]) -> FiiDay:
        futures = row[FUT_LONG] + row[FUT_SHORT]
        options = row[CALL_LONG] + row[CALL_SHORT] + row[PUT_LONG] + row[PUT_SHORT]
        tilt = ((row[CALL_LONG] - row[CALL_SHORT]) - (row[PUT_LONG] - row[PUT_SHORT])) / options if options else 0.0
        return cls(day, row[FUT_LONG] / futures if futures else 0.5, tilt)


def parse_participant_oi(text: str) -> dict[str, dict[str, float]]:
    """Rows by participant (Client, DII, FII, Pro, TOTAL); the first line is a title."""
    lines = text.strip().splitlines()
    reader = csv.DictReader(io.StringIO("\n".join(lines[1:])))
    rows = {}
    for raw in reader:
        clean = {(k or "").strip(): (v or "").strip() for k, v in raw.items()}
        name = clean.pop(CLIENT_TYPE, "")
        if name:
            rows[name] = {k: float(v) for k, v in clean.items() if v.replace(".", "", 1).isdigit()}
    return rows


@dataclass(frozen=True)
class FiiPositioning:
    """The last few sessions of FII index positioning, oldest first."""

    days: tuple[FiiDay, ...]

    @property
    def latest(self) -> FiiDay | None:
        return self.days[-1] if self.days else None

    def futures_shift(self) -> float | None:
        """Latest long share minus the average of the earlier sessions (+ = FIIs turning less bearish)."""
        if len(self.days) < 3:
            return None
        earlier = [d.futures_long_share for d in self.days[:-1]]
        return self.days[-1].futures_long_share - sum(earlier) / len(earlier)

    def options_shift(self) -> float | None:
        if len(self.days) < 3:
            return None
        earlier = [d.options_tilt for d in self.days[:-1]]
        return self.days[-1].options_tilt - sum(earlier) / len(earlier)


def load_fii_positioning(fetch_text, today: date, sessions: int = 10) -> FiiPositioning:
    """fetch_text(url) -> csv text or None (file missing: weekend, holiday, not yet published)."""
    found: list[FiiDay] = []
    for back in range(1, MAX_CALENDAR_DAYS_BACK + 1):
        day = today - timedelta(days=back)
        if day.weekday() >= 5:
            continue
        text = fetch_text(PARTICIPANT_OI_URL.format(day=day))
        rows = parse_participant_oi(text) if text else {}
        if FII_ROW in rows:
            found.append(FiiDay.from_row(day, rows[FII_ROW]))
        if len(found) >= sessions:
            break
    return FiiPositioning(tuple(sorted(found, key=lambda d: d.day)))
