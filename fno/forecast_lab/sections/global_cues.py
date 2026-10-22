"""Overnight cues from A17's tables (story FL1-1d-2), read only, through A17's own reader (agreed with the A17
builder, 22 Oct): never fetched here, never a second writer. A cue is shown only inside its as-of rule:
- the S&P 500, the Nasdaq-100 and the US 10-year: the last US session before the day's 09:15 IST open (A17's
  `current` or `ahead` at `OPEN`); a `behind` or older reading is not shown as current;
- the RBI's USD/INR reference rate: the same reading (its expected date is the previous session at 09:15);
- Brent: no calendar (EIA prints lag days); the latest print at most `BRENT_DAYS` old, shown with its own date.
The S&P 500 and the Nasdaq-100 are private cues (owner a927390): their values go to Slack and the Drive record only,
never to a repository file (owner bcbbc454)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from ..page.cues import AVAILABLE, CONTEXT, Cue, Section, SectionView, missing
from .spread import changes, size

BRENT_DAYS = 10  # a stated limit (story FL1-1d table), not evidence of the right number
USABLE = ("current", "ahead")
BEHIND = "behind"
NOT_SHOWN = "{label}: no reading inside its rule ({status})"


@dataclass(frozen=True)
class CueSpec:
    cue: str  # A17's table name
    label: str
    unit: str  # "%" for a level's change, "pts" for a yield's
    calendar: bool = True  # False: Brent, judged by its age only


SPECS = (
    CueSpec("sp500", "S&P 500", "%"),
    CueSpec("nasdaq100", "Nasdaq-100", "%"),
    CueSpec("us10y", "US 10-year yield", "pts"),
    CueSpec("usdinr_rbi", "USD/INR (RBI)", "%"),
    CueSpec("brent", "Brent", "%", calendar=False),
)


class GlobalCueSection(Section):
    def __init__(self, reader: Callable, spec: CueSpec, cutoff):
        """`reader`: makes A17's `CueReader` (once; it needs the Drive settings, so a missing one fails this Section's
        read, never the page); `cutoff`: A17's `OPEN` (09:15 IST), what was known before the open."""
        self.reader, self.spec, self.cutoff, self.name = reader, spec, cutoff, spec.label

    def _shown(self, reading) -> bool:
        if reading.row is None:
            return False
        if self.spec.calendar:
            return reading.status in USABLE
        return reading.status in (*USABLE, BEHIND) and reading.age_days is not None and reading.age_days <= BRENT_DAYS

    def read(self, day: date, edition: str) -> SectionView:
        reader = self.reader()
        reading = reader.read(self.spec.cue, day, self.cutoff, live_only=True)
        if not self._shown(reading):
            return missing(self.name, edition, NOT_SHOWN.format(label=self.name, status=reading.status))
        as_of = date.fromisoformat(reading.row["value_date"])
        rows = [r for r in reader.tables[self.spec.cue].rows() if date.fromisoformat(r["value_date"]) <= as_of]
        values = [float(r["value"]) for r in sorted(rows, key=lambda r: r["value_date"])]
        moves = changes(values, percent=self.spec.unit == "%")
        change = round(moves[-1], 3) if moves else None
        cue = Cue(self.name, values[-1], change, self.spec.unit, as_of, CONTEXT, size=size(change, moves[:-1]))
        return SectionView(self.name, AVAILABLE, as_of, (cue,))
